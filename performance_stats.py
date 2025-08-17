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
    
    def get_trading_performance(self, days=30, symbol=None):
        """Analyse complète des performances de trading - VERSION SÉCURISÉE"""
        print(f"\n📊 === ANALYSE DE PERFORMANCE ({days} derniers jours) ===")
        
        # Conditions de filtre
        date_filter = datetime.now() - timedelta(days=days)
        where_conditions = ["created_at >= ?"]
        params = [date_filter.strftime('%Y-%m-%d')]
        
        if symbol:
            where_conditions.append("symbol LIKE ?")
            params.append(f"%{symbol.upper()}%")
        
        where_clause = " AND ".join(where_conditions)
        
        # 1. STATISTIQUES GÉNÉRALES AVEC PROTECTION NULL
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
        
        # Calculs de base avec protection
        total_transactions = self._safe_int(stats['total_transactions'])
        total_buys = self._safe_int(stats['total_buys'])
        total_sells = self._safe_int(stats['total_sells'])
        total_invested = self._safe_float(stats['total_invested'])
        total_sold = self._safe_float(stats['total_sold'])
        total_fees = self._safe_float(stats['total_fees'])
        unique_symbols = self._safe_int(stats['unique_symbols'])
        
        net_profit = total_sold - total_invested - total_fees
        roi_percent = (net_profit / total_invested * 100) if total_invested > 0 else 0
        
        print(f"💰 Investissement total: {total_invested:.2f} USDC")
        print(f"💵 Ventes totales: {total_sold:.2f} USDC")
        print(f"💸 Frais totaux: {total_fees:.6f} USDC")
        print(f"📈 Profit net: {net_profit:+.2f} USDC")
        print(f"🎯 ROI: {roi_percent:+.2f}%")
        print(f"🔄 {total_buys} achats, {total_sells} ventes")
        print(f"🪙 {unique_symbols} cryptos différentes")
        
        # Message si pas de données
        if total_transactions == 0:
            print("\n⚠️  AUCUNE TRANSACTION TROUVÉE")
            print("💡 Vérifiez que votre bot a des transactions enregistrées")
            print("💡 Utilisez: python3 db_query.py pour explorer la base")
        
        return {
            'invested': total_invested,
            'sold': total_sold,
            'fees': total_fees,
            'net_profit': net_profit,
            'roi_percent': roi_percent,
            'buys': total_buys,
            'sells': total_sells,
            'symbols': unique_symbols,
            'total_transactions': total_transactions
        }
    
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
                    crypto['symbol'] or 'N/A',
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
        """Performance des ordres OCO - VERSION SÉCURISÉE"""
        print(f"\n🎯 === PERFORMANCE ORDRES OCO ===")
        
        cursor = self.conn.execute("""
            SELECT 
                COALESCE(status, 'UNKNOWN') as status,
                COUNT(*) as count,
                AVG(execution_price) as avg_price,
                SUM(execution_qty) as total_qty,
                AVG(profit_target) as avg_profit_target
            FROM oco_orders 
            WHERE status != 'ACTIVE' AND status IS NOT NULL
            GROUP BY status
            ORDER BY count DESC
        """)
        
        oco_stats = cursor.fetchall()
        
        if oco_stats:
            headers = ["Statut", "Nombre", "Prix moy.", "Qty totale", "Profit cible %"]
            rows = []
            
            for stat in oco_stats:
                avg_price = self._safe_float(stat['avg_price'])
                total_qty = self._safe_float(stat['total_qty'])
                avg_target = self._safe_float(stat['avg_profit_target'])
                
                rows.append([
                    stat['status'] or 'UNKNOWN',
                    self._safe_int(stat['count']),
                    f"{avg_price:.6f}" if avg_price > 0 else "N/A",
                    f"{total_qty:.8f}" if total_qty > 0 else "N/A",
                    f"{avg_target:.1f}%" if avg_target > 0 else "N/A"
                ])
            
            print(tabulate(rows, headers=headers, tablefmt="grid"))
        else:
            print("📭 Aucun ordre OCO exécuté trouvé")
        
        # OCO actifs
        cursor = self.conn.execute("SELECT COUNT(*) FROM oco_orders WHERE status = 'ACTIVE'")
        active_oco = self._safe_int(cursor.fetchone()[0])
        print(f"\n🔄 Ordres OCO actifs: {active_oco}")
    
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
                created_at = sell['created_at'] or 'N/A'
                
                rows.append([
                    sell['symbol'] or 'N/A',
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
    
    def export_performance_report(self, filename=None):
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
            
            self.get_trading_performance(30)
            self.get_crypto_breakdown(30)
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
            analyzer.export_performance_report(args.export)
        elif args.full:
            analyzer.get_trading_performance(args.days, args.symbol)
            analyzer.get_crypto_breakdown(args.days)
            analyzer.get_monthly_performance()
            analyzer.get_oco_performance()
            analyzer.get_best_worst_trades()
            analyzer.get_trading_frequency()
        else:
            # Rapport par défaut
            analyzer.get_trading_performance(args.days, args.symbol)
    
    except Exception as e:
        print(f"❌ Erreur analyse: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        analyzer.close()

if __name__ == "__main__":
    main()
