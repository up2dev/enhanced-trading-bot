"""
Base de données SQLite simplifiée pour le trading bot
Version allégée et utilisée à 100%
"""

import sqlite3
import logging
import os
import threading
from typing import Optional, List, Dict
from datetime import datetime, timedelta
from contextlib import contextmanager

class DatabaseManager:
    """Gestionnaire DB minimaliste et efficace"""
    
    def __init__(self, db_path: str = "db/trading.db"):
        self.db_path = db_path
        self.logger = logging.getLogger(__name__)
        self._lock = threading.Lock()
        
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self._init_database()
        
        self.logger.info(f"📊 Base de données initialisée: {db_path}")
    
    def _init_database(self):
        """Crée seulement les tables VRAIMENT utilisées"""
        try:
            with self.get_connection() as conn:
                # Table des transactions (ESSENTIELLE)
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS transactions (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        symbol TEXT NOT NULL,
                        order_id TEXT NOT NULL UNIQUE,
                        transact_time TEXT NOT NULL,
                        order_type TEXT NOT NULL,
                        order_side TEXT NOT NULL,
                        price REAL NOT NULL,
                        qty REAL NOT NULL,
                        commission REAL DEFAULT 0,
                        commission_asset TEXT DEFAULT 'USDC',
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Index ESSENTIELS pour les requêtes utilisées
                conn.execute("CREATE INDEX IF NOT EXISTS idx_symbol_side_time ON transactions(symbol, order_side, transact_time)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_order_side_time ON transactions(order_side, transact_time)")
                
                # Table OCO (ESSENTIELLE pour monitoring)
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS oco_orders (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        symbol TEXT NOT NULL,
                        oco_order_id TEXT NOT NULL UNIQUE,
                        profit_order_id TEXT,
                        stop_order_id TEXT,
                        buy_transaction_id INTEGER,
                        status TEXT DEFAULT 'ACTIVE',
                        profit_target REAL,
                        stop_loss_price REAL,
                        quantity REAL,
                        kept_quantity REAL DEFAULT 0,
                        execution_price REAL,
                        execution_qty REAL,
                        execution_type TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        executed_at TIMESTAMP
                    )
                """)
                
                # Index OCO pour monitoring
                conn.execute("CREATE INDEX IF NOT EXISTS idx_oco_status ON oco_orders(status)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_oco_symbol ON oco_orders(symbol)")
                
                conn.commit()
                self.logger.info("✅ Tables essentielles créées")
                
        except Exception as e:
            self.logger.error(f"❌ Erreur initialisation base: {e}")
            raise
    
    @contextmanager
    def get_connection(self):
        """Context manager thread-safe optimisé Pi"""
        conn = None
        try:
            with self._lock:
                conn = sqlite3.connect(self.db_path, timeout=10.0, check_same_thread=False)
                conn.row_factory = sqlite3.Row
                
                # Optimisations Pi seulement
                conn.execute("PRAGMA journal_mode=WAL")
                conn.execute("PRAGMA synchronous=NORMAL")
                
                yield conn
                
        except Exception as e:
            if conn:
                conn.rollback()
            raise
        finally:
            if conn:
                conn.close()
    
    def insert_transaction(self, symbol: str, order_id: str, transact_time: str, 
                         order_type: str, order_side: str, price: float, 
                         qty: float, commission: float = 0, 
                         commission_asset: str = 'USDC') -> int:
        """Insère une transaction (UTILISÉE)"""
        try:
            with self.get_connection() as conn:
                cursor = conn.execute("""
                    INSERT OR REPLACE INTO transactions 
                    (symbol, order_id, transact_time, order_type, order_side, 
                     price, qty, commission, commission_asset)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (symbol, order_id, transact_time, order_type, order_side, 
                      price, qty, commission, commission_asset))
                
                transaction_id = cursor.lastrowid
                conn.commit()
                
                self.logger.debug(f"💾 Transaction: {symbol} {order_side} {qty:.6f}")
                return transaction_id
                
        except Exception as e:
            self.logger.error(f"❌ Erreur transaction: {e}")
            return 0
    
    def insert_oco_order(self, symbol: str, oco_order_id: str, profit_order_id: str,
                        stop_order_id: str, buy_transaction_id: int, profit_target: float,
                        stop_loss_price: float, quantity: float, kept_quantity: float = 0) -> int:
        """Insère un ordre OCO (UTILISÉE)"""
        try:
            with self.get_connection() as conn:
                cursor = conn.execute("""
                    INSERT INTO oco_orders 
                    (symbol, oco_order_id, profit_order_id, stop_order_id, 
                     buy_transaction_id, profit_target, stop_loss_price, quantity, kept_quantity)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (symbol, oco_order_id, profit_order_id, stop_order_id,
                      buy_transaction_id, profit_target, stop_loss_price, quantity, kept_quantity))
                
                oco_id = cursor.lastrowid
                conn.commit()
                
                self.logger.info(f"📊 OCO enregistré: {symbol} - {oco_order_id}")
                return oco_id
                
        except Exception as e:
            self.logger.error(f"❌ Erreur OCO: {e}")
            return 0
    
    def get_active_oco_orders(self) -> List[Dict]:
        """Récupère les ordres OCO actifs (UTILISÉE pour monitoring)"""
        try:
            with self.get_connection() as conn:
                cursor = conn.execute("""
                    SELECT * FROM oco_orders 
                    WHERE status = 'ACTIVE'
                    ORDER BY created_at DESC
                """)
                
                orders = [dict(row) for row in cursor.fetchall()]
                
                if orders:
                    self.logger.debug(f"🔍 {len(orders)} ordre(s) OCO actifs trouvés")
                
                return orders
                
        except Exception as e:
            self.logger.error(f"❌ Erreur récupération OCO actifs: {e}")
            return []

    def update_oco_execution(self, oco_order_id: str, status: str, 
                           execution_price: float, execution_qty: float, 
                           execution_type: str):
        """Met à jour un OCO exécuté (UTILISÉE pour monitoring)"""
        try:
            with self.get_connection() as conn:
                conn.execute("""
                    UPDATE oco_orders 
                    SET status = ?, execution_price = ?, execution_qty = ?, 
                        execution_type = ?, executed_at = CURRENT_TIMESTAMP
                    WHERE oco_order_id = ?
                """, (status, execution_price, execution_qty, execution_type, oco_order_id))
                
                if conn.total_changes > 0:
                    conn.commit()
                    self.logger.info(f"🔄 OCO mis à jour: {oco_order_id} -> {status}")
                else:
                    self.logger.warning(f"⚠️  OCO {oco_order_id} non trouvé pour mise à jour")
                
        except Exception as e:
            self.logger.error(f"❌ Erreur update OCO: {e}")
    
    def get_daily_buy_count(self, date: Optional[str] = None) -> int:
        """Compte les achats du jour (UTILISÉE pour cooldown)"""
        try:
            if not date:
                date = datetime.now().strftime('%Y-%m-%d')
            
            date_start = int(datetime.strptime(date, '%Y-%m-%d').timestamp())
            date_end = date_start + 86400
            
            with self.get_connection() as conn:
                cursor = conn.execute("""
                    SELECT COUNT(*) FROM transactions 
                    WHERE order_side = 'BUY'
                    AND CAST(transact_time AS INTEGER) >= ?
                    AND CAST(transact_time AS INTEGER) < ?
                """, (date_start, date_end))
                
                return cursor.fetchone()[0]
                
        except Exception as e:
            self.logger.error(f"❌ Erreur comptage achats: {e}")
            return 0
    
    def get_last_buy_time(self, symbol: str) -> Optional[float]:
        """Dernière transaction d'achat pour cooldown (UTILISÉE)"""
        try:
            with self.get_connection() as conn:
                cursor = conn.execute("""
                    SELECT MAX(CAST(transact_time AS INTEGER)) as last_time
                    FROM transactions 
                    WHERE symbol = ? AND order_side = 'BUY'
                """, (symbol,))
                
                result = cursor.fetchone()
                if result and result[0]:
                    timestamp = result[0]
                    return timestamp / 1000.0 if timestamp > 2000000000 else timestamp
                
                return None
                
        except Exception as e:
            self.logger.error(f"❌ Erreur dernière transaction {symbol}: {e}")
            return None
    
    def get_quick_stats(self) -> Dict:
        """Stats rapides pour les logs (UTILISÉE)"""
        try:
            today = datetime.now().strftime('%Y-%m-%d')
            today_start = int(datetime.strptime(today, '%Y-%m-%d').timestamp())
            today_end = today_start + 86400
            
            with self.get_connection() as conn:
                # Achats du jour
                cursor = conn.execute("""
                    SELECT COUNT(*) FROM transactions 
                    WHERE order_side = 'BUY'
                    AND CAST(transact_time AS INTEGER) >= ?
                    AND CAST(transact_time AS INTEGER) < ?
                """, (today_start, today_end))
                daily_buys = cursor.fetchone()[0]
                
                # OCO actifs
                cursor = conn.execute("SELECT COUNT(*) FROM oco_orders WHERE status = 'ACTIVE'")
                active_oco = cursor.fetchone()[0]
                
                # Total transactions
                cursor = conn.execute("SELECT COUNT(*) FROM transactions")
                total_transactions = cursor.fetchone()[0]
                
                return {
                    'daily_buys': daily_buys,
                    'active_oco': active_oco,
                    'total_transactions': total_transactions
                }
                
        except Exception as e:
            self.logger.error(f"❌ Erreur stats: {e}")
            return {'daily_buys': 0, 'active_oco': 0, 'total_transactions': 0}
    
    def cleanup_old_transactions(self, days_to_keep: int = 30):
        """Nettoyage léger (OPTIONNELLE)"""
        try:
            cutoff_timestamp = int((datetime.now() - timedelta(days=days_to_keep)).timestamp())
            
            with self.get_connection() as conn:
                cursor = conn.execute("""
                    DELETE FROM transactions 
                    WHERE CAST(transact_time AS INTEGER) < ?
                """, (cutoff_timestamp,))
                
                deleted = cursor.rowcount
                conn.commit()
                
                if deleted > 0:
                    self.logger.info(f"🧹 {deleted} anciennes transactions supprimées")
                
        except Exception as e:
            self.logger.error(f"❌ Erreur nettoyage: {e}")
