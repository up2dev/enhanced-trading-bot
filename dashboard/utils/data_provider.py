"""
Enhanced Trading Bot Dashboard - Fournisseur de données
Interface entre le dashboard et le bot de trading
"""

import sys
import sqlite3
import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional

# Import des modules bot
try:
    from src.database import DatabaseManager
    from src.portfolio_manager import EnhancedPortfolioManager
    from src.binance_client import EnhancedBinanceClient
except ImportError as e:
    print(f"⚠️  Erreur import modules bot: {e}")

class BotDataProvider:
    """Fournisseur de données pour le dashboard"""
    
    def __init__(self, config_path: str = "config/config.json"):
        self.config_path = config_path
        self.db = DatabaseManager()
        self.portfolio_manager = EnhancedPortfolioManager(config_path)
        
        # Initialiser le client Binance
        binance_config = self.portfolio_manager.get_binance_config()
        self.binance_client = EnhancedBinanceClient(
            binance_config['api_key'], 
            binance_config['api_secret']
        )
    
    def _get_current_timestamp(self):
        """Timestamp actuel"""
        return datetime.now().isoformat()
    
    def _period_to_start(self, period: str) -> Optional[str]:
        """Convertit une période logique en timestamp SQLite ("YYYY-MM-DD HH:MM:SS")."""
        try:
            period = (period or '').lower()
            now = datetime.now()
            if period in ('today', 'jour', 'day'):
                start = now.replace(hour=0, minute=0, second=0, microsecond=0)
            elif period in ('week', '7d', '7days'):
                start = now - timedelta(days=7)
            elif period in ('month', '30d', '30days'):
                start = now - timedelta(days=30)
            elif period in ('all', '', None):
                return None
            else:
                start = now - timedelta(days=30)
            # Important: utiliser un format compatible avec les comparaisons SQLite
            return start.strftime('%Y-%m-%d %H:%M:%S')
        except Exception:
            return None
    
    def get_quick_stats(self) -> Dict:
        """Statistiques rapides pour l'en-tête"""
        try:
            if not self.db:
                return {'error': 'Database non disponible'}
            
            stats = self.db.get_quick_stats()
            
            # Ajouter des infos supplémentaires
            stats.update({
                'timestamp': self._get_current_timestamp(),
                'bot_status': self._get_bot_status(),
                'last_update': self._get_last_activity()
            })
            
            return stats
            
        except Exception as e:
            return {'error': str(e)}
    
    def get_portfolio_summary(self) -> Dict:
        """Résumé du portefeuille avec données réelles Binance"""
        try:
            # Récupérer balances compte
            account_info = self.binance_client._make_request_with_retry(
                self.binance_client.client.get_account
            )
            balances = account_info.get('balances', [])
            
            # Configuration des cryptos
            active_cryptos = self.portfolio_manager.get_active_cryptos()
            
            # Enrichir les cryptos avec balances et prix
            total_value_usdc = 0
            enriched_cryptos = []
            
            for crypto in active_cryptos:
                name = crypto.get('name')
                symbol = crypto.get('symbol')
                
                # Recherche flexible de la balance
                balance_info = None
                for balance in balances:
                    if (
                        balance['asset'] == name or  
                        balance['asset'] == symbol.replace('USDC', '')
                    ):
                        balance_info = balance
                        break
                
                if balance_info:
                    total_balance = float(balance_info['free']) + float(balance_info['locked'])
                    
                    # Récupérer prix actuel
                    try:
                        ticker = self.binance_client._make_request_with_retry(
                            self.binance_client.client.get_symbol_ticker,
                            symbol=symbol
                        )
                        current_price = float(ticker['price'])
                        value_usdc = total_balance * current_price
                        
                        # Données enrichies
                        crypto_data = {
                            **crypto,
                            'balance': total_balance,
                            'free_balance': float(balance_info['free']),
                            'locked_balance': float(balance_info['locked']),
                            'current_price': current_price,
                            'value_usdc': value_usdc
                        }
                        
                        total_value_usdc += value_usdc
                        enriched_cryptos.append(crypto_data)
                    
                    except Exception as price_error:
                        print(f"⚠️ Erreur prix {symbol}: {price_error}")
            
            # Calculer allocations
            for crypto in enriched_cryptos:
                crypto['current_allocation'] = crypto['value_usdc'] / total_value_usdc if total_value_usdc > 0 else 0
            
            return {
                'active_cryptos': len(enriched_cryptos),
                'cryptos': enriched_cryptos,
                'total_value': total_value_usdc,
                'free_usdc': next((float(b['free']) for b in balances if b['asset'] == 'USDC'), 0),
                'last_update': self._get_current_timestamp()
            }
        
        except Exception as e:
            print(f"❌ Erreur portfolio summary: {e}")
            return {'error': str(e)}
    
    def get_portfolio_performance(self) -> Dict:
        """Calcule des performances (aujourd'hui, 7j, 30j, total) basées sur la DB."""
        try:
            if not self.db:
                return {'today': 0, '7d': 0, '30d': 0, 'total': 0}
            
            def compute_period_perf(days: int) -> float:
                with self.db.get_connection() as conn:
                    if days == 0:
                        # Aujourd'hui
                        start = datetime.now().strftime('%Y-%m-%d 00:00:00')
                    elif days < 0:
                        # Total
                        start = None
                    else:
                        start = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d %H:%M:%S')
                    
                    if start:
                        where = "WHERE created_at >= ?"
                        params = (start,)
                    else:
                        where = ""
                        params = ()
                    
                    q = f"""
                        SELECT 
                            COALESCE(SUM(CASE WHEN order_side = 'BUY' THEN price*qty ELSE 0 END), 0) as invested,
                            COALESCE(SUM(CASE WHEN order_side = 'SELL' THEN price*qty ELSE 0 END), 0) as sold,
                            COALESCE(SUM(commission), 0) as fees
                        FROM transactions
                        {where}
                    """
                    cur = conn.execute(q, params)
                    row = cur.fetchone()
                    invested = float(row[0]) if row and row[0] is not None else 0.0
                    sold = float(row[1]) if row and row[1] is not None else 0.0
                    fees = float(row[2]) if row and row[2] is not None else 0.0
                    profit = sold - invested - fees
                    return (profit / invested * 100.0) if invested > 0 else 0.0
            
            return {
                'today': round(compute_period_perf(0), 2),
                '7d': round(compute_period_perf(7), 2),
                '30d': round(compute_period_perf(30), 2),
                'total': round(compute_period_perf(-1), 2)
            }
        except Exception as e:
            print(f"Erreur performance: {e}")
            return {'today': 0, '7d': 0, '30d': 0, 'total': 0}
    
    def get_active_orders(self) -> List[Dict]:
        """Ordres OCO actifs enrichis (id, buy_price)"""
        try:
            if not self.db:
                return []
            
            with self.db.get_connection() as conn:
                cursor = conn.execute("""
                    SELECT id, symbol, quantity, kept_quantity, profit_target,
                           stop_loss_price, created_at, status, buy_transaction_id
                    FROM oco_orders 
                    WHERE status = 'ACTIVE'
                    ORDER BY created_at DESC
                """)
                
                orders = []
                for row in cursor.fetchall():
                    order_id = row[0]
                    symbol = row[1]
                    qty = float(row[2])
                    kept_qty = float(row[3])
                    profit_target = float(row[4]) if row[4] is not None else None
                    stop_loss_price = float(row[5]) if row[5] is not None else None
                    created_at = row[6]
                    status = row[7]
                    buy_tx_id = row[8]
                    
                    buy_price = None
                    if buy_tx_id:
                        try:
                            c2 = conn.execute(
                                "SELECT price FROM transactions WHERE id = ? LIMIT 1",
                                (buy_tx_id,)
                            )
                            r2 = c2.fetchone()
                            if r2 and r2[0] is not None:
                                buy_price = float(r2[0])
                        except Exception:
                            pass
                    
                    orders.append({
                        'id': order_id,
                        'symbol': symbol,
                        'quantity': qty,
                        'kept_quantity': kept_qty,
                        'profit_target': profit_target,
                        'stop_loss_price': stop_loss_price,
                        'buy_price': buy_price,
                        'created_at': created_at,
                        'status': status
                    })
                
                return orders
                
        except Exception as e:
            print(f"Erreur get_active_orders: {e}")
            return [{'error': str(e)}]
    
    def get_orders_history(self, limit: int = 50) -> List[Dict]:
        """Historique des OCO exécutés/terminés"""
        try:
            if not self.db:
                return []
            
            with self.db.get_connection() as conn:
                cursor = conn.execute("""
                    SELECT oco_order_id, symbol, quantity, kept_quantity,
                           profit_target, stop_loss_price,
                           status, execution_price, execution_qty, execution_type,
                           created_at, executed_at
                    FROM oco_orders
                    WHERE status != 'ACTIVE' AND status IS NOT NULL
                    ORDER BY COALESCE(executed_at, created_at) DESC
                    LIMIT ?
                """, (limit,))
                
                history = []
                for row in cursor.fetchall():
                    history.append({
                        'oco_order_id': row[0],
                        'symbol': row[1],
                        'quantity': float(row[2]) if row[2] is not None else 0,
                        'kept_quantity': float(row[3]) if row[3] is not None else 0,
                        'profit_target': float(row[4]) if row[4] is not None else None,
                        'stop_loss_price': float(row[5]) if row[5] is not None else None,
                        'status': row[6],
                        'execution_price': float(row[7]) if row[7] is not None else None,
                        'execution_qty': float(row[8]) if row[8] is not None else None,
                        'execution_type': row[9],
                        'created_at': row[10],
                        'executed_at': row[11]
                    })
                return history
        except Exception as e:
            print(f"Erreur get_orders_history: {e}")
            return [{'error': str(e)}]
    
    def get_recent_transactions(self, limit: int = 10, period: Optional[str] = None) -> List[Dict]:
        """Transactions récentes avec filtrage de période et order_id"""
        try:
            if not self.db:
                return []
            
            start_str = self._period_to_start(period)
            
            with self.db.get_connection() as conn:
                if start_str:
                    cursor = conn.execute("""
                        SELECT order_id, symbol, order_side, price, qty,
                               created_at, ROUND(price * qty, 2) as value
                        FROM transactions 
                        WHERE created_at >= ?
                        ORDER BY created_at DESC 
                        LIMIT ?
                    """, (start_str, limit))
                else:
                    cursor = conn.execute("""
                        SELECT order_id, symbol, order_side, price, qty,
                               created_at, ROUND(price * qty, 2) as value
                        FROM transactions 
                        ORDER BY created_at DESC 
                        LIMIT ?
                    """, (limit,))
                
                transactions = []
                for row in cursor.fetchall():
                    transactions.append({
                        'order_id': row[0],
                        'symbol': row[1],
                        'side': row[2],
                        'price': float(row[3]) if row[3] is not None else 0,
                        'quantity': float(row[4]) if row[4] is not None else 0,
                        'created_at': row[5],
                        'value': float(row[6]) if row[6] is not None else 0
                    })
                
                return transactions
                
        except Exception as e:
            print(f"Erreur get_recent_transactions: {e}")
            return [{'error': str(e)}]
    
    def _get_bot_status(self) -> str:
        """Status du bot (approximatif)"""
        try:
            # Vérifier activité récente (dernières 15 min)
            if not self.db:
                return 'unknown'
            
            cutoff = datetime.now() - timedelta(minutes=15)
            
            with self.db.get_connection() as conn:
                cursor = conn.execute("""
                    SELECT COUNT(*) FROM transactions 
                    WHERE created_at >= ?
                """, (cutoff.strftime('%Y-%m-%d %H:%M:%S'),))
                
                recent_activity = cursor.fetchone()[0]
                
                if recent_activity > 0:
                    return 'active'
                else:
                    return 'idle'
                    
        except:
            return 'unknown'
    
    def _get_last_activity(self) -> Optional[str]:
        """Dernière activité"""
        try:
            if not self.db:
                return None
            
            with self.db.get_connection() as conn:
                cursor = conn.execute("""
                    SELECT MAX(created_at) FROM transactions
                """)
                
                last_activity = cursor.fetchone()[0]
                return last_activity
                
        except:
            return None

# Instance globale pour le dashboard
data_provider = BotDataProvider()
