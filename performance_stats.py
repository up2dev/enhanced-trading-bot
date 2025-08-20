#!/usr/bin/env python3
"""
Enhanced Trading Bot - Analyseur de performance complet (VERSION CORRIGÉE)
Calcule ROI, profits/pertes, statistiques détaillées avec protection NULL
"""

import sqlite3
import sys
import os
from datetime import datetime, timedelta
import argparse

# Gestion de tabulate avec fallback
try:
    from tabulate import tabulate
    HAS_TABULATE = True
except ImportError:
    HAS_TABULATE = False
    def tabulate(data, headers=None, tablefmt="grid", floatfmt=".2f"):
        """Fallback simple si tabulate non disponible"""
        if not data:
            return "Aucune donnée"
        
        # Format simple en texte
        result = []
        if headers:
            result.append(" | ".join(str(h) for h in headers))
            result.append("-" * (len(" | ".join(headers)) + 10))
        
        for row in data:
            result.append(" | ".join(str(cell) for cell in row))
        
        return "\n".join(result)

class PerformanceAnalyzer:
    def __init__(self, db_path="db/trading.db"):
        self.db_path = db_path
        if not os.path.exists(db_path):
            print(f"❌ Base de données non trouvée: {db_path}")
            sys.exit(1)
        
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
        
        # Vérifier si tabulate est disponible
        if not HAS_TABULATE:
            print("⚠️  Module 'tabulate' non disponible, utilisation du format simple")
    
    def _safe_float(self, value, default=0.0):
        """Convertit en float avec valeur par défaut"""
        if value is None:
            return default
        try:
            return float(value)
        except (TypeError, ValueError):
            return default
    
    def _safe_int(self, value, default=0):
        """Convertit en int avec valeur par défaut"""
        if value is None:
            return default
        try:
            return int(value)
        except (TypeError, ValueError):
            return default

    def self.safe_row_access(self, row, key, default=None):
        """Accès sécurisé aux Row SQLite"""
        try:
            return row[key]
        except (KeyError, IndexError, TypeError):
            return default
    
    def get_trading_performance_with_holdings(self, days=30, symbol=None):
        """Analyse complète AVEC CRYPTO MISE DE CÔTÉ"""
        print(f"\n📊 === ANALYSE DE PERFORMANCE COMPLÈTE ({days} derniers jours) ===")
        
        # Conditions de filtre
        date_filter = datetime.now() - timedelta(days=days)
        where_conditions = ["created_at >= ?"]
        params = [date_filter.strftime('%Y-%m-%d')]
        
        if symbol:
            where_conditions.append("symbol LIKE ?")
            params.append(f"%{symbol.upper()}%")
        
        where_clause = " AND ".join(where_conditions)
        
        # 1. STATISTIQUES DE BASE
        cursor = self.conn.execute(f"""
            SELECT 
                COUNT(*) as total_transactions,
                COALESCE(SUM(CASE WHEN order_side = 'BUY' THEN 1 ELSE 0 END), 0) as total_buys,
                COALESCE(SUM(CASE WHEN order_side = 'SELL' THEN 1 ELSE 0 END), 0) as total_sells,
                COALESCE(SUM(CASE WHEN order_side = 'BUY' THEN price * qty ELSE 0 END), 0) as total_invested,
                COALESCE(SUM(CASE WHEN order_side = 'SELL' THEN price * qty ELSE 0 END), 0) as total_sold,
                COALESCE(SUM(commission), 0) as total_fees,
                COUNT(DISTINCT symbol) as unique_symbols
            FROM transactions 
            WHERE {where_clause}
        """, params)
        
        stats = cursor.fetchone()
        
        # Calculs de base SÉCURISÉS
        try:
            total_transactions = self._safe_int(stats['total_transactions'])
        except (KeyError, IndexError, TypeError):
            total_transactions = 0
            
        try:
            total_buys = self._safe_int(stats['total_buys'])
        except (KeyError, IndexError, TypeError):
            total_buys = 0
            
        try:
            total_sells = self._safe_int(stats['total_sells'])
        except (KeyError, IndexError, TypeError):
            total_sells = 0
            
        try:
            total_invested = self._safe_float(stats['total_invested'])
        except (KeyError, IndexError, TypeError):
            total_invested = 0.0
            
        try:
            total_sold = self._safe_float(stats['total_sold'])
        except (KeyError, IndexError, TypeError):
            total_sold = 0.0
            
        try:
            total_fees = self._safe_float(stats['total_fees'])
        except (KeyError, IndexError, TypeError):
            total_fees = 0.0
            
        try:
            unique_symbols = self._safe_int(stats['unique_symbols'])
        except (KeyError, IndexError, TypeError):
            unique_symbols = 0
        
        # 2. CALCULER LA VALEUR DES CRYPTOS MISES DE CÔTÉ
        print("🔍 Calcul de la valeur des cryptos mises de côté...")
        
        # Récupérer les cryptos avec balance > 0 depuis les OCO
        cursor = self.conn.execute("""
            SELECT 
                symbol,
                COALESCE(SUM(kept_quantity), 0) as total_kept
            FROM oco_orders 
            WHERE kept_quantity > 0 
            AND created_at >= ?
            GROUP BY symbol
        """, [date_filter.strftime('%Y-%m-%d')])
        
        kept_cryptos = cursor.fetchall()
        total_holdings_value = 0.0
        
        if kept_cryptos:
            print("\n💎 Cryptos mises de côté:")
            
            for crypto in kept_cryptos:
                try:
                    symbol = self.safe_row_access(crypto['symbol'])
                    kept_qty = self._safe_float(self.safe_row_access(crypto['total_kept']))
                except (KeyError, IndexError, TypeError):
                    continue
                
                if kept_qty > 0:
                    # Récupérer le dernier prix connu
                    cursor = self.conn.execute("""
                        SELECT price FROM transactions 
                        WHERE symbol = ? 
                        ORDER BY created_at DESC 
                        LIMIT 1
                    """, [symbol])
                    
                    last_price_row = cursor.fetchone()
                    last_price = self._safe_float(last_price_row[0] if last_price_row and len(last_price_row) > 0 else 0) if last_price_row else 0
                    
                    holding_value = kept_qty * last_price
                    total_holdings_value += holding_value
                    
                    print(f"   {symbol}: {kept_qty:.8f} @ {last_price:.6f} = {holding_value:.2f} USDC")
        
        # 3. CALCUL CORRIGÉ DU PROFIT
        net_profit_basic = total_sold - total_invested - total_fees
        net_profit_with_holdings = net_profit_basic + total_holdings_value
        
        roi_basic = (net_profit_basic / total_invested * 100) if total_invested > 0 else 0
        roi_with_holdings = (net_profit_with_holdings / total_invested * 100) if total_invested > 0 else 0
        
        # 4. AFFICHAGE DÉTAILLÉ
        print(f"\n💰 === RÉSULTATS FINANCIERS ===")
        print(f"💰 Investissement total: {total_invested:.2f} USDC")
        print(f"💵 Ventes totales: {total_sold:.2f} USDC")
        print(f"💎 Valeur cryptos gardées: {total_holdings_value:.2f} USDC")
        print(f"💸 Frais totaux: {total_fees:.6f} USDC")
        print(f"")
        print(f"📈 Profit (ventes seules): {net_profit_basic:+.2f} USDC")
        print(f"📈 Profit (avec holdings): {net_profit_with_holdings:+.2f} USDC")
        print(f"")
        print(f"🎯 ROI (ventes seules): {roi_basic:+.2f}%")
        print(f"🎯 ROI (réel avec holdings): {roi_with_holdings:+.2f}%")
        
        if total_holdings_value > 0:
            print(f"\n💡 Différence due aux holdings: +{total_holdings_value:.2f} USDC ({(total_holdings_value/total_invested*100):+.2f}%)")
        
        print(f"\n🔄 {total_buys} achats, {total_sells} ventes")
        print(f"🪙 {unique_symbols} cryptos différentes")
        
        return {
            'invested': total_invested,
            'sold': total_sold,
            'holdings_value': total_holdings_value,
            'fees': total_fees,
            'net_profit_basic': net_profit_basic,
            'net_profit_with_holdings': net_profit_with_holdings,
            'roi_basic': roi_basic,
            'roi_with_holdings': roi_with_holdings,
            'buys': total_buys,
            'sells': total_sells,
            'symbols': unique_symbols,  # Variable locale sécurisée
            'total_transactions': total_transactions
        }

    def get_current_holdings_from_binance(self):
        """BONUS: Récupérer les vraies balances depuis Binance"""
        try:
            # Vous pouvez intégrer ici votre client Binance
            # pour récupérer les vraies balances actuelles
            
            print("\n🔗 Récupération balances Binance...")
            print("💡 Fonctionnalité à intégrer avec votre BinanceClient")
            
            # Exemple d'intégration:
            # from src.binance_client import EnhancedBinanceClient
            # client = EnhancedBinanceClient(api_key, api_secret)
            # account = client.client.get_account()
            # ... calculer la vraie valeur actuelle
            
            return 0.0  # Placeholder
            
        except Exception as e:
            print(f"⚠️ Impossible de récupérer les balances Binance: {e}")
            return 0.0

    def get_crypto_breakdown(self, days=30):
        """Performance par crypto - VERSION SÉCURISÉE"""
        print(f"\n🪙 === PERFORMANCE PAR CRYPTO ===")
        
        date_filter = datetime.now() - timedelta(days=days)
        
        cursor = self.conn.execute("""
            SELECT 
                symbol,
                COUNT(*) as transactions,
                COALESCE(SUM(CASE WHEN order_side = 'BUY' THEN 1 ELSE 0 END), 0) as buys,
                COALESCE(SUM(CASE WHEN order_side = 'SELL' THEN 1 ELSE 0 END), 0) as sells,
                COALESCE(SUM(CASE WHEN order_side = 'BUY' THEN price * qty ELSE 0 END), 0) as invested,
                COALESCE(SUM(CASE WHEN order_side = 'SELL' THEN price * qty ELSE 0 END), 0) as sold,
                COALESCE(SUM(commission), 0) as fees,
                AVG(CASE WHEN order_side = 'BUY' THEN price ELSE NULL END) as avg_buy_price,
                AVG(CASE WHEN order_side = 'SELL' THEN price ELSE NULL END) as avg_sell_price
            FROM transactions 
            WHERE created_at >= ?
            GROUP BY symbol 
            ORDER BY invested DESC
        """, [date_filter.strftime('%Y-%m-%d')])
        
        crypto_stats = cursor.fetchall()
        
        if crypto_stats:
            headers = ["Crypto", "Txs", "Achats", "Ventes", "Investi", "Vendu", "Profit", "ROI%", "Fees"]
            rows = []
            
            for crypto in crypto_stats:
                invested = self._safe_float(crypto['invested'])
                sold = self._safe_float(crypto['sold'])
                fees = self._safe_float(crypto['fees'])
                profit = sold - invested - fees
                roi = (profit / invested * 100) if invested > 0 else 0
                
                rows.append([
                    self.safe_row_access(crypto['symbol']) or 'N/A',
                    self._safe_int(crypto['transactions']),
                    self._safe_int(crypto['buys']),
                    self._safe_int(crypto['sells']),
                    f"{invested:.2f}",
                    f"{sold:.2f}",
                    f"{profit:+.2f}",
                    f"{roi:+.2f}%",
                    f"{fees:.6f}"
                ])
            
            print(tabulate(rows, headers=headers, tablefmt="grid"))
        else:
            print("📭 Aucune donnée crypto trouvée pour cette période")
    
    def get_monthly_performance(self):
        """Performance mensuelle - VERSION SÉCURISÉE"""
        print(f"\n📅 === PERFORMANCE MENSUELLE ===")
        
        cursor = self.conn.execute("""
            SELECT 
                strftime('%Y-%m', created_at) as month,
                COUNT(*) as transactions,
                COALESCE(SUM(CASE WHEN order_side = 'BUY' THEN price * qty ELSE 0 END), 0) as invested,
                COALESCE(SUM(CASE WHEN order_side = 'SELL' THEN price * qty ELSE 0 END), 0) as sold,
                COALESCE(SUM(commission), 0) as fees
            FROM transactions 
            WHERE created_at >= date('now', '-12 months')
            GROUP BY strftime('%Y-%m', created_at)
            ORDER BY month DESC
        """)
        
        monthly_stats = cursor.fetchall()
        
        if monthly_stats:
            headers = ["Mois", "Transactions", "Investi", "Vendu", "Profit", "ROI%"]
            rows = []
            
            for month in monthly_stats:
                invested = self._safe_float(month['invested'])
                sold = self._safe_float(month['sold'])
                fees = self._safe_float(month['fees'])
                profit = sold - invested - fees
                roi = (profit / invested * 100) if invested > 0 else 0
                
                rows.append([
                    month['month'] or 'N/A',
                    self._safe_int(month['transactions']),
                    f"{invested:.2f}",
                    f"{sold:.2f}",
                    f"{profit:+.2f}",
                    f"{roi:+.2f}%"
                ])
            
            print(tabulate(rows, headers=headers, tablefmt="grid"))
        else:
            print("📭 Aucune donnée mensuelle trouvée")
    
    def get_oco_performance(self):
        """Performance des ordres OCO AVEC CRYPTO GARDÉE"""
        print(f"\n🎯 === PERFORMANCE ORDRES OCO (COMPLÈTE) ===")
        
        # 1. STATISTIQUES DE BASE par statut
        cursor = self.conn.execute("""
            SELECT 
                COALESCE(status, 'UNKNOWN') as status,
                COUNT(*) as count,
                COALESCE(AVG(execution_price), 0) as avg_execution_price,
                COALESCE(SUM(execution_qty), 0) as total_execution_qty,
                COALESCE(AVG(profit_target), 0) as avg_profit_target,
                COALESCE(SUM(kept_quantity), 0) as total_kept_qty
            FROM oco_orders 
            WHERE status != 'ACTIVE' AND status IS NOT NULL
            GROUP BY status
            ORDER BY count DESC
        """)
        
        oco_stats = cursor.fetchall()
        
        if oco_stats:
            headers = ["Statut", "Nombre", "Prix moy.", "Qty exécutée", "Qty gardée", "Profit cible %"]
            rows = []
            
            for stat in oco_stats:
                avg_price = self._safe_float(stat['avg_execution_price'])
                exec_qty = self._safe_float(stat['total_execution_qty'])
                kept_qty = self._safe_float(stat['total_kept_qty'])
                avg_target = self._safe_float(stat['avg_profit_target'])
                
                rows.append([
                    stat['status'] or 'UNKNOWN',
                    self._safe_int(stat['count']),
                    f"{avg_price:.6f}" if avg_price > 0 else "N/A",
                    f"{exec_qty:.8f}" if exec_qty > 0 else "N/A",
                    f"{kept_qty:.8f}" if kept_qty > 0 else "N/A",
                    f"{avg_target:.1f}%" if avg_target > 0 else "N/A"
                ])
            
            print(tabulate(rows, headers=headers, tablefmt="grid"))
        
        # 2. CALCUL DÉTAILLÉ DU PROFIT OCO RÉEL
        print(f"\n💰 === ANALYSE FINANCIÈRE OCO ===")
        
        # Récupérer tous les OCO avec leurs données complètes
        cursor = self.conn.execute("""
            SELECT 
                symbol,
                quantity as initial_qty,
                COALESCE(execution_price, 0) as execution_price,
                COALESCE(execution_qty, 0) as execution_qty,
                COALESCE(kept_quantity, 0) as kept_qty,
                profit_target,
                stop_loss_price,
                status,
                created_at
            FROM oco_orders 
            WHERE status IN ('PROFIT_FILLED', 'STOP_FILLED')
            ORDER BY created_at DESC
        """)
        
        executed_ocos = cursor.fetchall()
        
        if executed_ocos:
            total_profit_realized = 0.0
            total_holdings_value = 0.0
            total_initial_investment = 0.0
            
            profits_detail = []
            losses_detail = []
            
            print(f"📊 Analyse détaillée de {len(executed_ocos)} ordres OCO exécutés:")
            
            for oco in executed_ocos:
                symbol = self.safe_row_access(oco['symbol'])
                initial_qty = self._safe_float(oco['initial_qty'])
                execution_price = self._safe_float(oco['execution_price'])
                execution_qty = self._safe_float(oco['execution_qty'])
                kept_qty = self._safe_float(oco['kept_qty'])
                status = oco['status']
                
                # Récupérer le prix d'achat initial depuis les transactions
                cursor_buy = self.conn.execute("""
                    SELECT AVG(price) as avg_buy_price, SUM(price * qty) / SUM(qty) as weighted_avg
                    FROM transactions 
                    WHERE symbol = ? AND order_side = 'BUY' 
                    AND created_at <= ?
                    ORDER BY created_at DESC
                    LIMIT 5
                """, [symbol, self.safe_row_access(oco['created_at'])])
                
                buy_data = cursor_buy.fetchone()
                avg_buy_price = self._safe_float(buy_data[1] if buy_data and len(buy_data) > 1 else 0) if buy_data else execution_price * 0.97  # Estimation
                
                # Calculs financiers
                initial_investment = initial_qty * avg_buy_price
                realized_value = execution_qty * execution_price
                realized_profit = realized_value - (execution_qty * avg_buy_price)
                
                # Valeur actuelle de la crypto gardée
                cursor_current = self.conn.execute("""
                    SELECT price FROM transactions 
                    WHERE symbol = ? 
                    ORDER BY created_at DESC 
                    LIMIT 1
                """, [symbol])
                
                current_price_row = cursor_current.fetchone()
                current_price = self._safe_float(current_price_row[0] if current_price_row and len(current_price_row) > 0 else 0) if current_price_row else execution_price
                
                holdings_value = kept_qty * current_price
                holdings_profit = holdings_value - (kept_qty * avg_buy_price)
                
                total_profit = realized_profit + holdings_profit
                total_investment_for_this = initial_investment
                roi = (total_profit / total_investment_for_this * 100) if total_investment_for_this > 0 else 0
                
                # Accumuler les totaux
                total_profit_realized += realized_profit
                total_holdings_value += holdings_value
                total_initial_investment += initial_investment
                
                # Catégoriser
                if status == 'PROFIT_FILLED':
                    profits_detail.append({
                        'symbol': symbol,
                        'profit': total_profit,
                        'roi': roi,
                        'holdings_value': holdings_value
                    })
                else:
                    losses_detail.append({
                        'symbol': symbol,
                        'loss': total_profit,  # Sera négatif
                        'roi': roi,
                        'holdings_value': holdings_value
                    })
            
            # 3. RÉSUMÉ GLOBAL
            total_holdings_profit = total_holdings_value - sum(self._safe_float(oco['kept_quantity']) * avg_buy_price for oco in executed_ocos if (kept_qty := self._safe_float(oco['kept_quantity'])) > 0)
            global_profit = total_profit_realized + total_holdings_profit
            global_roi = (global_profit / total_initial_investment * 100) if total_initial_investment > 0 else 0
            
            print(f"\n💰 RÉSUMÉ FINANCIER OCO:")
            print(f"💵 Profit réalisé (ventes): {total_profit_realized:+.2f} USDC")
            print(f"💎 Valeur actuelle gardée: {total_holdings_value:.2f} USDC")
            print(f"📈 Profit total OCO: {global_profit:+.2f} USDC")
            print(f"🎯 ROI global OCO: {global_roi:+.2f}%")
            
            # 4. TOP/FLOP OCO
            if profits_detail:
                best_oco = max(profits_detail, key=lambda x: x['profit'])
                print(f"\n🏆 Meilleur OCO: {best_self.safe_row_access(oco['symbol'])} → +{best_oco['profit']:.2f} USDC ({best_oco['roi']:+.1f}%)")
            
            if losses_detail:
                worst_oco = min(losses_detail, key=lambda x: x['loss'])
                print(f"💀 Pire OCO: {worst_self.safe_row_access(oco['symbol'])} → {worst_oco['loss']:.2f} USDC ({worst_oco['roi']:+.1f}%)")
            
            # 5. STATISTIQUES DÉTAILLÉES
            profit_orders = len(profits_detail)
            loss_orders = len(losses_detail)
            success_rate = (profit_orders / (profit_orders + loss_orders) * 100) if (profit_orders + loss_orders) > 0 else 0
            
            print(f"\n📊 STATISTIQUES OCO:")
            print(f"✅ Ordres profitables: {profit_orders}")
            print(f"❌ Ordres en perte: {loss_orders}")
            print(f"🎯 Taux de réussite: {success_rate:.1f}%")
            
        else:
            print("📭 Aucun ordre OCO exécuté trouvé")
        
        # OCO actifs
        cursor = self.conn.execute("SELECT COUNT(*) FROM oco_orders WHERE status = 'ACTIVE'")
        active_oco = self._safe_int(cursor.fetchone()[0])
        print(f"\n🔄 Ordres OCO actifs: {active_oco}")
        
        # 6. DÉTAIL DES OCO ACTIFS AVEC VALEUR ACTUELLE
        if active_oco > 0:
            print(f"\n📋 === DÉTAIL OCO ACTIFS ===")
            
            cursor = self.conn.execute("""
                SELECT symbol, quantity, kept_quantity, profit_target, 
                    stop_loss_price, created_at
                FROM oco_orders 
                WHERE status = 'ACTIVE'
                ORDER BY created_at DESC
            """)
            
            active_orders = cursor.fetchall()
            
            headers = ["Crypto", "Qty totale", "Qty gardée", "Profit %", "Stop-loss", "Âge (jours)"]
            rows = []
            
            for order in active_orders:
                age_days = (datetime.now() - datetime.fromisoformat(self.safe_row_access(order['created_at']))).days
                qty_total = self._safe_float(order['quantity'])
                qty_kept = self._safe_float(order['kept_quantity'])
                profit_target = self._safe_float(order['profit_target'])
                stop_loss = self._safe_float(order['stop_loss_price'])
                
                rows.append([
                    self.safe_row_access(order['symbol']).replace('USDC', ''),
                    f"{qty_total:.8f}",
                    f"{qty_kept:.8f}",
                    f"+{profit_target:.1f}%",
                    f"{stop_loss:.6f}",
                    f"{age_days}j"
                ])
            
            print(tabulate(rows, headers=headers, tablefmt="grid"))

    def get_best_worst_trades(self, limit=10):
        """Meilleurs et pires trades - VERSION SÉCURISÉE"""
        print(f"\n🏆 === TOP {limit} TRADES RÉCENTS ===")
        
        cursor = self.conn.execute(f"""
            SELECT 
                symbol,
                created_at,
                order_side,
                price,
                qty,
                price * qty as value,
                commission
            FROM transactions 
            WHERE order_side = 'SELL'
            ORDER BY created_at DESC
            LIMIT {limit}
        """)
        
        recent_sells = cursor.fetchall()
        
        if recent_sells:
            headers = ["Crypto", "Date", "Prix vente", "Quantité", "Valeur", "Commission"]
            rows = []
            
            for sell in recent_sells:
                price = self._safe_float(sell['price'])
                qty = self._safe_float(sell['qty'])
                value = self._safe_float(sell['value'])
                commission = self._safe_float(sell['commission'])
                created_at = self.safe_row_access(sell['created_at']) or 'N/A'
                
                rows.append([
                    self.safe_row_access(sell['symbol']) or 'N/A',
                    created_at[:16] if len(created_at) > 16 else created_at,
                    f"{price:.6f}",
                    f"{qty:.8f}",
                    f"{value:.2f}",
                    f"{commission:.6f}"
                ])
            
            print(tabulate(rows, headers=headers, tablefmt="grid"))
        else:
            print("📭 Aucune vente récente trouvée")
    
    def get_trading_frequency(self):
        """Analyse de la fréquence de trading - VERSION CORRIGÉE"""
        print(f"\n⏰ === FRÉQUENCE DE TRADING ===")
        
        # Transactions par jour des 30 derniers jours
        cursor = self.conn.execute("""
            SELECT 
                date(created_at) as trading_date,
                COUNT(*) as transactions,
                COALESCE(SUM(CASE WHEN order_side = 'BUY' THEN 1 ELSE 0 END), 0) as buys,
                COALESCE(SUM(CASE WHEN order_side = 'SELL' THEN 1 ELSE 0 END), 0) as sells
            FROM transactions 
            WHERE created_at >= date('now', '-30 days')
            GROUP BY date(created_at)
            ORDER BY trading_date DESC
            LIMIT 10
        """)
        
        daily_stats = cursor.fetchall()
        
        if daily_stats:
            headers = ["Date", "Transactions", "Achats", "Ventes"]
            rows = []
            
            for day in daily_stats:
                rows.append([
                    day['trading_date'] or 'N/A',
                    self._safe_int(day['transactions']),
                    self._safe_int(day['buys']),
                    self._safe_int(day['sells'])
                ])
            
            print(tabulate(rows, headers=headers, tablefmt="grid"))
            
            # Moyennes - VERSION CORRIGÉE AVEC PROTECTION NULL
            cursor = self.conn.execute("""
                SELECT 
                    AVG(CAST(daily_count AS REAL)) as avg_daily,
                    MAX(daily_count) as max_daily,
                    COUNT(*) as active_days
                FROM (
                    SELECT COUNT(*) as daily_count
                    FROM transactions 
                    WHERE created_at >= date('now', '-30 days')
                    GROUP BY date(created_at)
                )
            """)
            
            avg_stats = cursor.fetchone()
            
            # Protection contre les NULL
            avg_daily = self._safe_float(avg_stats['avg_daily']) if avg_stats else 0.0
            max_daily = self._safe_int(avg_stats['max_daily']) if avg_stats else 0
            active_days = self._safe_int(avg_stats['active_days']) if avg_stats else 0
            
            print(f"\n📊 Moyenne quotidienne: {avg_daily:.1f} transactions")
            print(f"📊 Maximum quotidien: {max_daily} transactions")
            print(f"📊 Jours actifs: {active_days}/30")
            
        else:
            print("📭 Aucune activité de trading dans les 30 derniers jours")
            print("\n📊 Moyenne quotidienne: 0.0 transactions")
            print("📊 Maximum quotidien: 0 transactions")
            print("📊 Jours actifs: 0/30")
    
    def export_performance_report(self, filename=None, days=30):
        """Exporte un rapport complet"""
        if not filename:
            filename = f"performance_report_{datetime.now().strftime('%Y%m%d_%H%M')}.txt"
        
        print(f"\n📄 === EXPORT RAPPORT ===")
        print(f"Génération du rapport: {filename}")
        
        # Rediriger la sortie vers un fichier
        from io import StringIO
        
        old_stdout = sys.stdout
        sys.stdout = StringIO()
        
        try:
            # Générer tous les rapports
            print(f"🤖 RAPPORT DE PERFORMANCE TRADING BOT")
            print(f"📅 Généré le: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print("=" * 60)
            
            self.get_trading_performance_with_holdings(days)
            self.get_crypto_breakdown(days)
            self.get_monthly_performance()
            self.get_oco_performance()
            self.get_best_worst_trades()
            self.get_trading_frequency()
            
            # Récupérer le contenu
            report_content = sys.stdout.getvalue()
            
        except Exception as e:
            report_content = f"Erreur génération rapport: {e}"
        
        finally:
            sys.stdout = old_stdout
        
        # Sauvegarder le fichier
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(report_content)
            print(f"✅ Rapport sauvegardé: {filename}")
            return filename
        except Exception as e:
            print(f"❌ Erreur sauvegarde: {e}")
            return None
    
    def close(self):
        """Ferme la connexion"""
        if self.conn:
            self.conn.close()

def main():
    parser = argparse.ArgumentParser(description="Analyseur de performance Trading Bot (Version corrigée)")
    parser.add_argument("--db", default="db/trading.db", help="Chemin vers la base")
    parser.add_argument("--days", type=int, default=30, help="Période d'analyse en jours")
    parser.add_argument("--symbol", help="Analyser une crypto spécifique")
    parser.add_argument("--export", help="Exporter vers un fichier")
    parser.add_argument("--full", action="store_true", help="Rapport complet")
    
    args = parser.parse_args()
    
    analyzer = PerformanceAnalyzer(args.db)
    
    try:
        if args.export:
            analyzer.export_performance_report(args.export, args.days)
        elif args.full:
            analyzer.get_trading_performance_with_holdings(args.days, args.symbol)
            analyzer.get_crypto_breakdown(args.days)
            analyzer.get_monthly_performance()
            analyzer.get_oco_performance()
            analyzer.get_best_worst_trades()
            analyzer.get_trading_frequency()
        else:
            # Rapport par défaut
            analyzer.get_trading_performance_with_holdings(args.days, args.symbol)
    
    except Exception as e:
        print(f"❌ Erreur analyse: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        analyzer.close()

if __name__ == "__main__":
    main()