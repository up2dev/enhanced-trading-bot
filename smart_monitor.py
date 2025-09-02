#!/usr/bin/env python3
"""
📊 SMART TRADING MONITOR v2.2.2 - EMAIL + TELEGRAM
- Méthode hybrid pour les timestamps (created_at + transact_time fallback)
- Holdings vs Profits garantis (calculs réalistes)
- Adapté à la config email existante dans config/
- Auto-détection des logs
"""

import sqlite3
from datetime import datetime, timedelta
import json
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import subprocess
import re
import requests
import sys
import os

class SmartMonitor:
    def __init__(self):
        self.db_path = 'db/trading.db'
        self.db = None
        self._connect_db()
        self.telegram_config = self._load_telegram_config()
        
    def _connect_db(self):
        """Connexion sécurisée à la DB"""
        try:
            if not os.path.exists(self.db_path):
                print(f"❌ Base de données non trouvée: {self.db_path}")
                sys.exit(1)
            
            self.db = sqlite3.connect(self.db_path, timeout=10)
            self.db.row_factory = sqlite3.Row
            print("✅ Connexion DB OK")
            
        except Exception as e:
            print(f"❌ Erreur connexion DB: {e}")
            sys.exit(1)
            
    def _load_telegram_config(self):
        """Charge la config Telegram existante"""
        try:
            with open('config.json') as f:
                config = json.load(f)
                telegram = config.get('telegram', {})
                
                if telegram.get('enabled') and telegram.get('bot_token') and telegram.get('chat_id'):
                    print("✅ Config Telegram chargée")
                    return {
                        'token': telegram['bot_token'],
                        'chat_id': telegram['chat_id'],
                        'enabled': True
                    }
                else:
                    print("⚠️  Telegram désactivé ou mal configuré")
                    return {'enabled': False}
                    
        except Exception as e:
            print(f"⚠️  Erreur config Telegram: {e}")
            return {'enabled': False}
    
    def get_daily_transactions(self):
        """📊 Transactions du jour - MÉTHODE HYBRID FIABLE"""
        today = datetime.now().strftime('%Y-%m-%d')
        
        try:
            # 🎯 MÉTHODE 1: Essayer avec created_at (fonctionne)
            cursor = self.db.execute("""
                SELECT 
                    COUNT(*) as total_trades,
                    COUNT(CASE WHEN order_side = 'BUY' THEN 1 END) as buys,
                    COUNT(CASE WHEN order_side = 'SELL' THEN 1 END) as sells,
                    ROUND(SUM(CASE WHEN order_side = 'BUY' THEN price*qty ELSE 0 END), 2) as invested_today,
                    ROUND(SUM(CASE WHEN order_side = 'SELL' THEN price*qty ELSE 0 END), 2) as sold_today,
                    ROUND(SUM(commission), 6) as fees_today,
                    COUNT(DISTINCT symbol) as cryptos_traded
                FROM transactions 
                WHERE date(created_at) = ?
            """, [today])
            
            stats = cursor.fetchone()
            
            # Vérifier si on a des résultats
            if stats and (stats['total_trades'] or 0) > 0:
                invested = float(stats['invested_today']) if stats['invested_today'] else 0.0
                sold = float(stats['sold_today']) if stats['sold_today'] else 0.0
                fees = float(stats['fees_today']) if stats['fees_today'] else 0.0
                profit_today = sold - invested - fees
                
                print(f"✅ Méthode created_at: {stats['total_trades']} transactions trouvées")
                
                return {
                    'total': int(stats['total_trades']) if stats['total_trades'] else 0,
                    'buys': int(stats['buys']) if stats['buys'] else 0, 
                    'sells': int(stats['sells']) if stats['sells'] else 0,
                    'invested': invested,
                    'sold': sold,
                    'fees': fees,
                    'profit': profit_today,
                    'cryptos': int(stats['cryptos_traded']) if stats['cryptos_traded'] else 0
                }
            
            print("⚠️ Méthode created_at: aucune transaction, essai transact_time...")
            
            # 🔄 MÉTHODE 2: Fallback avec transact_time en millisecondes
            today_start = int(datetime.strptime(today, '%Y-%m-%d').timestamp() * 1000)
            today_end = today_start + (86400 * 1000)
            
            cursor = self.db.execute("""
                SELECT 
                    COUNT(*) as total_trades,
                    COUNT(CASE WHEN order_side = 'BUY' THEN 1 END) as buys,
                    COUNT(CASE WHEN order_side = 'SELL' THEN 1 END) as sells,
                    ROUND(SUM(CASE WHEN order_side = 'BUY' THEN price*qty ELSE 0 END), 2) as invested_today,
                    ROUND(SUM(CASE WHEN order_side = 'SELL' THEN price*qty ELSE 0 END), 2) as sold_today,
                    ROUND(SUM(commission), 6) as fees_today,
                    COUNT(DISTINCT symbol) as cryptos_traded
                FROM transactions 
                WHERE CAST(transact_time AS INTEGER) >= ? 
                AND CAST(transact_time AS INTEGER) < ?
            """, [today_start, today_end])
            
            stats = cursor.fetchone()
            
            invested = float(stats['invested_today']) if stats['invested_today'] else 0.0
            sold = float(stats['sold_today']) if stats['sold_today'] else 0.0
            fees = float(stats['fees_today']) if stats['fees_today'] else 0.0
            profit_today = sold - invested - fees
            
            print(f"✅ Méthode transact_time: {stats['total_trades']} transactions trouvées")
            
            return {
                'total': int(stats['total_trades']) if stats['total_trades'] else 0,
                'buys': int(stats['buys']) if stats['buys'] else 0, 
                'sells': int(stats['sells']) if stats['sells'] else 0,
                'invested': invested,
                'sold': sold,
                'fees': fees,
                'profit': profit_today,
                'cryptos': int(stats['cryptos_traded']) if stats['cryptos_traded'] else 0
            }
            
        except Exception as e:
            print(f"❌ Erreur récupération transactions: {e}")
            return {'total': 0, 'buys': 0, 'sells': 0, 'invested': 0, 'sold': 0, 'fees': 0, 'profit': 0, 'cryptos': 0}
    
    def get_active_positions(self):
        """🎯 Positions actives - ADAPTÉ À TA VRAIE DB STRUCTURE"""
        try:
            # 1. ORDRES ACTIFS
            cursor = self.db.execute("SELECT COUNT(*) FROM oco_orders WHERE status = 'ACTIVE'")
            active_oco = cursor.fetchone()[0] or 0
            
            cursor = self.db.execute("SELECT COUNT(*) FROM limit_orders WHERE status = 'ACTIVE'")
            active_limits = cursor.fetchone()[0] or 0
            
            # 2. HOLDINGS OCO (kept_quantity > 0) - Valeur NON RÉALISÉE
            cursor = self.db.execute("""
                SELECT 
                    COUNT(*) as orders_with_holdings,
                    ROUND(SUM(
                        o.kept_quantity * COALESCE(
                            (SELECT t.price FROM transactions t 
                             WHERE t.symbol = o.symbol 
                             ORDER BY t.created_at DESC LIMIT 1), 0
                        )
                    ), 2) as holdings_value
                FROM oco_orders o 
                WHERE o.status = 'ACTIVE' AND o.kept_quantity > 0
            """)
            
            oco_holdings = cursor.fetchone()
            oco_holdings_count = int(oco_holdings[0]) if oco_holdings[0] else 0
            oco_holdings_value = float(oco_holdings[1]) if oco_holdings[1] else 0.0
            
            # 3. HOLDINGS LIMIT (kept_quantity > 0)
            cursor = self.db.execute("""
                SELECT 
                    COUNT(*) as orders_with_holdings,
                    ROUND(SUM(
                        l.kept_quantity * COALESCE(
                            (SELECT t.price FROM transactions t 
                             WHERE t.symbol = l.symbol 
                             ORDER BY t.created_at DESC LIMIT 1), 0
                        )
                    ), 2) as holdings_value
                FROM limit_orders l 
                WHERE l.status = 'ACTIVE' AND l.kept_quantity > 0
            """)
            
            limit_holdings = cursor.fetchone()
            limit_holdings_count = int(limit_holdings[0]) if limit_holdings[0] else 0
            limit_holdings_value = float(limit_holdings[1]) if limit_holdings[1] else 0.0
            
            # 4. PROFIT GARANTI OCO (kept_quantity = 0) 
            # 🔧 CORRIGÉ : Utiliser le prix de la transaction d'achat
            cursor = self.db.execute("""
                SELECT 
                    COUNT(*) as orders_full_sell,
                    ROUND(SUM(
                        CASE 
                            WHEN o.profit_target IS NOT NULL AND t.price IS NOT NULL AND o.quantity IS NOT NULL
                            THEN t.price * o.quantity * (o.profit_target / 100.0)
                            ELSE 0
                        END
                    ), 2) as guaranteed_profit
                FROM oco_orders o
                LEFT JOIN transactions t ON t.id = o.buy_transaction_id
                WHERE o.status = 'ACTIVE' 
                AND (o.kept_quantity = 0 OR o.kept_quantity IS NULL)
                AND o.profit_target IS NOT NULL
            """)
            
            oco_profit = cursor.fetchone()
            oco_profit_count = int(oco_profit[0]) if oco_profit[0] else 0
            oco_guaranteed_profit = float(oco_profit[1]) if oco_profit[1] else 0.0
            
            # 5. PROFIT GARANTI LIMIT (logique similaire)
            cursor = self.db.execute("""
                SELECT 
                    COUNT(*) as orders_full_sell,
                    ROUND(SUM(
                        CASE 
                            WHEN l.profit_target IS NOT NULL AND t.price IS NOT NULL AND l.quantity IS NOT NULL
                            THEN t.price * l.quantity * (l.profit_target / 100.0)
                            ELSE 0
                        END
                    ), 2) as guaranteed_profit
                FROM limit_orders l
                LEFT JOIN transactions t ON t.id = l.buy_transaction_id
                WHERE l.status = 'ACTIVE' 
                AND (l.kept_quantity = 0 OR l.kept_quantity IS NULL)
                AND l.profit_target IS NOT NULL
            """)
            
            limit_profit = cursor.fetchone()
            limit_profit_count = int(limit_profit[0]) if limit_profit[0] else 0
            limit_guaranteed_profit = float(limit_profit[1]) if limit_profit[1] else 0.0
            
            return {
                'oco_count': int(active_oco),
                'limit_count': int(active_limits),
                'total_active': int(active_oco) + int(active_limits),
                
                # 💎 HOLDINGS (non réalisés)
                'oco_holdings_count': oco_holdings_count,
                'oco_holdings_value': oco_holdings_value,
                'limit_holdings_count': limit_holdings_count,
                'limit_holdings_value': limit_holdings_value,
                'total_holdings_value': oco_holdings_value + limit_holdings_value,
                'total_holdings_count': oco_holdings_count + limit_holdings_count,
                
                # 💰 PROFITS GARANTIS (estimés)
                'oco_profit_count': oco_profit_count,
                'oco_guaranteed_profit': oco_guaranteed_profit,
                'limit_profit_count': limit_profit_count,
                'limit_guaranteed_profit': limit_guaranteed_profit,
                'total_guaranteed_profit': oco_guaranteed_profit + limit_guaranteed_profit,
                'total_profit_count': oco_profit_count + limit_profit_count,
                
                # 📊 RÉSUMÉS
                'has_holdings': (oco_holdings_count + limit_holdings_count) > 0,
                'has_guaranteed_profits': (oco_profit_count + limit_profit_count) > 0
            }
            
        except Exception as e:
            print(f"❌ Erreur récupération positions: {e}")
            return {
                'oco_count': 0, 'limit_count': 0, 'total_active': 0,
                'total_holdings_value': 0, 'total_holdings_count': 0,
                'total_guaranteed_profit': 0, 'total_profit_count': 0,
                'has_holdings': False, 'has_guaranteed_profits': False
            }
    
    def get_critical_errors(self):
        """🚨 Erreurs critiques uniquement - AUTO-DÉTECTION LOG"""
        try:
            # Auto-détection du fichier de log
            possible_logs = [
                'logs/bot.log',
                'logs/trading_bot.log', 
                'logs/enhanced_trading_bot.log',
                'logs/main.log',
                'logs/application.log'
            ]
            
            log_file = None
            for log_path in possible_logs:
                if os.path.exists(log_path):
                    log_file = log_path
                    break
            
            if not log_file:
                return []  # Pas d'erreur si pas de logs
            
            result = subprocess.run(['tail', '-100', log_file], 
                                  capture_output=True, text=True, timeout=5)
            
            if result.returncode != 0:
                return []
            
            lines = result.stdout.split('\n')
            
            # Patterns d'erreurs critiques
            critical_patterns = [
                r'ERROR.*Binance.*API',
                r'ERROR.*Database.*lock',
                r'ERROR.*Trading.*failed',
                r'CRITICAL',
                r'ERROR.*Connection.*timeout',
                r'ERROR.*Échec création transaction',
                r'ERROR.*getAttr.*not defined'
            ]
            
            errors = []
            today = datetime.now().strftime('%Y-%m-%d')
            
            for line in lines:
                if today in line:
                    for pattern in critical_patterns:
                        if re.search(pattern, line, re.IGNORECASE):
                            if ' - ERROR - ' in line:
                                parts = line.split(' - ERROR - ')
                                if len(parts) >= 2:
                                    error_part = parts[-1].strip()
                                    time_part = line[:19] if len(line) >= 19 else line[:10]
                                    error_msg = f"{time_part[-8:]}: {error_part[:50]}"
                                    if error_msg not in errors:
                                        errors.append(error_msg)
                            break
            
            return errors[-5:] if errors else []
            
        except Exception as e:
            return []
    
    def get_system_health(self):
        """🖥️ Santé machine - INFO UTILE"""
        try:
            # Température CPU
            temp_file = '/sys/class/thermal/thermal_zone0/temp'
            temp = float(open(temp_file).read().strip()) / 1000 if os.path.exists(temp_file) else 0
            
            # Charge système  
            load = float(open('/proc/loadavg').read().split()[0]) if os.path.exists('/proc/loadavg') else 0
            
            # Mémoire
            mem_usage = 0
            if os.path.exists('/proc/meminfo'):
                with open('/proc/meminfo') as f:
                    mem_info = f.read()
                    mem_total_match = re.search(r'MemTotal:\s+(\d+)', mem_info)
                    mem_avail_match = re.search(r'MemAvailable:\s+(\d+)', mem_info)
                    
                    if mem_total_match and mem_avail_match:
                        mem_total = int(mem_total_match.group(1))
                        mem_avail = int(mem_avail_match.group(1))
                        mem_usage = round((1 - mem_avail/mem_total) * 100)
            
            # Espace disque
            disk_usage = "?%"
            try:
                disk_result = subprocess.run(['df', '-h', '.'], capture_output=True, text=True, timeout=5)
                if disk_result.returncode == 0:
                    lines = disk_result.stdout.split('\n')
                    if len(lines) >= 2:
                        columns = lines[1].split()
                        if len(columns) >= 5:
                            disk_usage = columns[4]
            except:
                pass
            
            return {
                'temp': temp,
                'load': load,
                'mem_usage': mem_usage,
                'disk_usage': disk_usage,
                'status': '🔥' if temp > 70 else '⚠️' if temp > 60 else '✅'
            }
            
        except Exception as e:
            return {'temp': 0, 'load': 0, 'mem_usage': 0, 'disk_usage': '?%', 'status': '❌'}
    
    def get_weekly_roi(self):
        """📈 ROI Hebdomadaire - MÉTHODE HYBRID"""
        try:
            week_ago = datetime.now() - timedelta(days=7)
            
            # 🎯 MÉTHODE 1: Essayer avec created_at
            cursor = self.db.execute("""
                SELECT 
                    ROUND(SUM(CASE WHEN order_side = 'BUY' THEN price*qty ELSE 0 END), 2) as invested_week,
                    ROUND(SUM(CASE WHEN order_side = 'SELL' THEN price*qty ELSE 0 END), 2) as sold_week,
                    ROUND(SUM(commission), 6) as fees_week,
                    COUNT(CASE WHEN order_side = 'BUY' THEN 1 END) as buys_week,
                    COUNT(CASE WHEN order_side = 'SELL' THEN 1 END) as sells_week
                FROM transactions 
                WHERE created_at >= ?
            """, [week_ago.isoformat()])
            
            stats = cursor.fetchone()
            
            # Vérifier si on a des résultats significatifs
            if stats and (stats['buys_week'] or 0) + (stats['sells_week'] or 0) > 0:
                print("✅ ROI weekly: méthode created_at utilisée")
            else:
                print("⚠️ ROI weekly: fallback transact_time...")
                # Fallback avec transact_time en millisecondes
                week_ago_ms = int(week_ago.timestamp() * 1000)
                
                cursor = self.db.execute("""
                    SELECT 
                        ROUND(SUM(CASE WHEN order_side = 'BUY' THEN price*qty ELSE 0 END), 2) as invested_week,
                        ROUND(SUM(CASE WHEN order_side = 'SELL' THEN price*qty ELSE 0 END), 2) as sold_week,
                        ROUND(SUM(commission), 6) as fees_week,
                        COUNT(CASE WHEN order_side = 'BUY' THEN 1 END) as buys_week,
                        COUNT(CASE WHEN order_side = 'SELL' THEN 1 END) as sells_week
                    FROM transactions 
                    WHERE CAST(transact_time AS INTEGER) >= ?
                """, [week_ago_ms])
                
                stats = cursor.fetchone()
            
            invested = float(stats['invested_week']) if stats['invested_week'] else 0.0
            sold = float(stats['sold_week']) if stats['sold_week'] else 0.0
            fees = float(stats['fees_week']) if stats['fees_week'] else 0.0
            
            realized_profit = sold - invested - fees
            positions = self.get_active_positions()
            
            # ROI = (Profit réalisé + Holdings + Profits garantis) / Investi * 100
            total_value = realized_profit + positions['total_holdings_value'] + positions['total_guaranteed_profit']
            roi = (total_value / invested * 100) if invested > 0 else 0
            
            return {
                'invested': invested,
                'sold': sold,
                'fees': fees,
                'realized_profit': realized_profit,
                'holdings_value': positions['total_holdings_value'],
                'guaranteed_profit': positions['total_guaranteed_profit'],
                'total_value': total_value,
                'roi': roi,
                'buys': int(stats['buys_week']) if stats['buys_week'] else 0,
                'sells': int(stats['sells_week']) if stats['sells_week'] else 0
            }
            
        except Exception as e:
            print(f"❌ Erreur calcul ROI: {e}")
            return {'invested': 0, 'sold': 0, 'fees': 0, 'realized_profit': 0, 'holdings_value': 0, 'guaranteed_profit': 0, 'total_value': 0, 'roi': 0, 'buys': 0, 'sells': 0}
    
    def generate_daily_report(self):
        """📊 RAPPORT QUOTIDIEN - HOLDINGS vs PROFITS GARANTIS"""
        transactions = self.get_daily_transactions()
        positions = self.get_active_positions()
        system = self.get_system_health()
        errors = self.get_critical_errors()
        
        report = f"""🤖 TRADING BOT - Rapport Quotidien
📅 {datetime.now().strftime('%d/%m/%Y %H:%M')}

💰 TRANSACTIONS AUJOURD'HUI
├─ {transactions['buys']} achats, {transactions['sells']} ventes
├─ Investi: {transactions['invested']:.2f} USDC
├─ Vendu: {transactions['sold']:.2f} USDC  
├─ Profit brut: {transactions['profit']:+.2f} USDC
└─ {transactions['cryptos']} cryptos tradées

🎯 POSITIONS ACTIVES ({positions['total_active']} ordres)
├─ {positions['oco_count']} ordres OCO
├─ {positions['limit_count']} ordres LIMIT"""

        # Section dynamique selon les types de positions
        if positions['has_holdings'] and positions['has_guaranteed_profits']:
            report += f"""
├─ 💎 Holdings: {positions['total_holdings_value']:.2f} USDC ({positions['total_holdings_count']} ordres)
└─ 💰 Profits garantis: +{positions['total_guaranteed_profit']:.2f} USDC ({positions['total_profit_count']} ordres)"""
        
        elif positions['has_holdings']:
            report += f"""
└─ 💎 Holdings: {positions['total_holdings_value']:.2f} USDC (non réalisé)"""
        
        elif positions['has_guaranteed_profits']:
            report += f"""
└─ 💰 Profits garantis: +{positions['total_guaranteed_profit']:.2f} USDC (vente au prix cible)"""
        
        else:
            report += f"""
└─ ⏳ En attente de déclenchement"""

        report += f"""

{system['status']} SYSTÈME RASPBERRY PI
├─ CPU: {system['temp']:.0f}°C
├─ Charge: {system['load']:.2f}
├─ RAM: {system['mem_usage']}%
└─ Disque: {system['disk_usage']}"""

        if errors:
            report += f"\n\n🚨 ERREURS CRITIQUES ({len(errors)})"
            for error in errors:
                report += f"\n├─ {error}"
        else:
            report += f"\n\n✅ Aucune erreur critique"
        
        return report
    
    def generate_weekly_report(self):
        """📈 RAPPORT HEBDOMADAIRE - AVEC ROI COMPLET"""
        roi_data = self.get_weekly_roi()
        daily_data = self.get_daily_transactions()
        system = self.get_system_health()
        
        report = f"""🤖 TRADING BOT - Rapport Hebdomadaire  
📅 {datetime.now().strftime('%d/%m/%Y %H:%M')} (7 derniers jours)

📈 PERFORMANCE HEBDOMADAIRE
├─ Investi: {roi_data['invested']:.2f} USDC
├─ Vendu: {roi_data['sold']:.2f} USDC
├─ Profit réalisé: {roi_data['realized_profit']:+.2f} USDC
├─ Holdings actuels: {roi_data['holdings_value']:.2f} USDC
├─ Profits garantis: +{roi_data['guaranteed_profit']:.2f} USDC
├─ Valeur totale: {roi_data['total_value']:+.2f} USDC
└─ 🎯 ROI: {roi_data['roi']:+.2f}%

📊 ACTIVITÉ
├─ {roi_data['buys']} achats, {roi_data['sells']} ventes
└─ Frais: {roi_data['fees']:.6f} USDC

💰 AUJOURD'HUI
└─ Profit: {daily_data['profit']:+.2f} USDC ({daily_data['total']} trades)

{system['status']} SYSTÈME
└─ {system['temp']:.0f}°C, RAM {system['mem_usage']}%, Disque {system['disk_usage']}"""
        
        return report
    
    def generate_telegram_daily(self):
        """📱 TELEGRAM QUOTIDIEN - HOLDINGS + PROFITS"""
        transactions = self.get_daily_transactions()
        positions = self.get_active_positions()
        system = self.get_system_health()
        errors = self.get_critical_errors()
        
        profit_emoji = "💚" if transactions['profit'] > 0 else "🔴" if transactions['profit'] < 0 else "⚪"
        temp_emoji = "🔥" if system['temp'] > 70 else "⚠️" if system['temp'] > 60 else "✅"
        
        message = f"""🤖 *TRADING BOT* - {datetime.now().strftime('%d/%m %H:%M')}

{profit_emoji} *{transactions['buys']}B/{transactions['sells']}S* → {transactions['profit']:+.2f} USDC
🎯 *{positions['total_active']} ordres*"""

        # Position details - intelligent
        if positions['has_holdings'] and positions['has_guaranteed_profits']:
            message += f" (💎{positions['total_holdings_value']:.0f} + 💰{positions['total_guaranteed_profit']:+.0f})"
        elif positions['has_holdings']:
            message += f" (💎{positions['total_holdings_value']:.0f} holdings)"
        elif positions['has_guaranteed_profits']:
            message += f" (💰{positions['total_guaranteed_profit']:+.0f} garantis)"
        
        message += f"""
{temp_emoji} *{system['temp']:.0f}°C* RAM {system['mem_usage']}%"""

        if errors:
            message += f"\n🚨 *{len(errors)} ERREUR(S)*"
            if errors:
                latest_error = errors[-1][:40] + "..." if len(errors[-1]) > 40 else errors[-1]
                message += f"\n`{latest_error}`"
        
        return message
    
    def generate_telegram_weekly(self):
        """📱 TELEGRAM HEBDOMADAIRE - ROI FOCUS"""  
        roi_data = self.get_weekly_roi()
        system = self.get_system_health()
        
        roi_emoji = "🚀" if roi_data['roi'] > 5 else "📈" if roi_data['roi'] > 0 else "📉"
        
        message = f"""🤖 *TRADING BOT* - Semaine {datetime.now().strftime('%d/%m')}

{roi_emoji} *ROI: {roi_data['roi']:+.1f}%*
💰 Investi: {roi_data['invested']:.0f} USDC
💵 Réalisé: {roi_data['realized_profit']:+.0f} USDC  
💎 Holdings: {roi_data['holdings_value']:.0f} USDC
🎯 Garantis: +{roi_data['guaranteed_profit']:.0f} USDC
🔄 {roi_data['buys']}B/{roi_data['sells']}S cette semaine

✅ Système: {system['temp']:.0f}°C"""
        
        return message
    
    def send_email(self, subject, content, is_weekly=False):
        """📧 Envoi email avec TA CONFIG EXISTANTE"""
        try:
            # Charger TA config email
            with open('config/email_config.json') as f:
                config = json.load(f)
            
            smtp_config = config['smtp']
            sender_config = config['sender']
            
            # Choisir les destinataires selon le type
            if is_weekly:
                recipients = config['recipients']['weekly']
            else:
                recipients = config['recipients']['daily']
            
            msg = MIMEMultipart()
            msg['Subject'] = f"🤖 {subject}"
            msg['From'] = f"{sender_config['name']} <{sender_config['email']}>"
            msg['To'] = ', '.join(recipients)
            
            msg.attach(MIMEText(content, 'plain', 'utf-8'))
            
            # Connexion SMTP avec TLS (port 587)
            with smtplib.SMTP(smtp_config['server'], smtp_config['port']) as server:
                if smtp_config.get('use_tls', True):
                    server.starttls()
                server.login(smtp_config['username'], smtp_config['password'])
                server.send_message(msg)
                
            print(f"✅ Email '{subject}' envoyé à {len(recipients)} destinataire(s)")
            return True
            
        except Exception as e:
            print(f"❌ Erreur envoi email: {e}")
            return False
    
    def send_telegram(self, message, silent=False):
        """📱 Envoi Telegram avec markdown"""
        if not self.telegram_config.get('enabled'):
            print("📱 Telegram désactivé dans la configuration")
            return False
            
        try:
            url = f"https://api.telegram.org/bot{self.telegram_config['token']}/sendMessage"
            
            data = {
                'chat_id': self.telegram_config['chat_id'],
                'text': message,
                'parse_mode': 'Markdown',
                'disable_notification': silent
            }
            
            response = requests.post(url, json=data, timeout=10)
            response.raise_for_status()
            
            print("✅ Message Telegram envoyé avec succès")
            return True
                
        except Exception as e:
            print(f"❌ Erreur envoi Telegram: {e}")
            return False
    
    def send_reports(self, mode='daily'):
        """🚀 ENVOI COMBINÉ - EMAIL + TELEGRAM"""
        success = {'email': False, 'telegram': False}
        
        try:
            print(f"\n🚀 Génération des rapports {mode}...")
            
            is_weekly = (mode == 'weekly')
            
            if is_weekly:
                email_report = self.generate_weekly_report()
                telegram_msg = self.generate_telegram_weekly()
                subject = "Rapport Hebdomadaire"
            else:
                email_report = self.generate_daily_report()
                telegram_msg = self.generate_telegram_daily()  
                subject = "Rapport Quotidien"
            
            print(f"\n📧 PRÉVISUALISATION EMAIL:\n{email_report}")
            print(f"\n📱 PRÉVISUALISATION TELEGRAM:\n{telegram_msg}")
            
            # Envoi EMAIL avec le bon paramètre
            print(f"\n📧 Envoi de l'email...")
            success['email'] = self.send_email(subject, email_report, is_weekly)
            
            # Envoi TELEGRAM
            if self.telegram_config.get('enabled'):
                print(f"\n📱 Envoi Telegram dans 3 secondes...")
                import time
                time.sleep(3)
                success['telegram'] = self.send_telegram(telegram_msg)
            else:
                print(f"\n📱 Telegram désactivé - pas d'envoi")
            
            return success
            
        except Exception as e:
            print(f"❌ Erreur globale envoi rapports: {e}")
            import traceback
            traceback.print_exc()
            return success
    
    def close(self):
        """Fermeture propre de la connexion DB"""
        if self.db:
            try:
                self.db.close()
                print("✅ Connexion DB fermée")
            except:
                pass

def main():
    """Point d'entrée principal"""
    print("🤖 === SMART TRADING MONITOR v2.2.2 ===")
    
    monitor = None
    
    try:
        monitor = SmartMonitor()
        mode = sys.argv[1] if len(sys.argv) > 1 else 'daily'
        
        if mode not in ['daily', 'weekly']:
            print(f"❌ Mode '{mode}' non reconnu. Utilisez: daily ou weekly")
            sys.exit(1)
        
        print(f"📊 Mode: {mode}")
        
        results = monitor.send_reports(mode)
        
        print(f"\n📊 === RÉSULTATS ENVOI ===")
        print(f"📧 Email: {'✅ Succès' if results['email'] else '❌ Échec'}")
        print(f"📱 Telegram: {'✅ Succès' if results['telegram'] else '❌ Échec ou désactivé'}")
        
        sys.exit(0 if results['email'] else 1)
        
    except KeyboardInterrupt:
        print("\n⚠️ Arrêt demandé par l'utilisateur")
        sys.exit(130)
        
    except Exception as e:
        print(f"\n❌ Erreur fatale: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    finally:
        if monitor:
            monitor.close()

if __name__ == "__main__":
    main()
