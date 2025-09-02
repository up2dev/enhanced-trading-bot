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
from .utils import send_telegram_message, load_json_config

class DatabaseManager:
    """Gestionnaire DB minimaliste et efficace"""
    
    def __init__(self, db_path: str = "db/trading.db"):
        self.db_path = db_path
        self.logger = logging.getLogger(__name__)
        self._lock = threading.Lock()

        #Charger la config Telegram si disponible
        try:
            config = load_json_config("config/config.json")
            self.telegram_cfg = config.get("telegram", {})
        except Exception:
            self.telegram_cfg = {}

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
                
                # 🆕 NOUVELLE TABLE LIMIT ORDERS
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS limit_orders (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        symbol TEXT NOT NULL,
                        order_id TEXT NOT NULL UNIQUE,
                        buy_transaction_id INTEGER,
                        status TEXT DEFAULT 'ACTIVE',
                        profit_target REAL,
                        target_price REAL,
                        quantity REAL,
                        kept_quantity REAL DEFAULT 0,
                        execution_price REAL,
                        execution_qty REAL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        executed_at TIMESTAMP,
                        FOREIGN KEY (buy_transaction_id) REFERENCES transactions(id)
                    )
                """)
                
                # Index OCO pour monitoring
                conn.execute("CREATE INDEX IF NOT EXISTS idx_oco_status ON oco_orders(status)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_oco_symbol ON oco_orders(symbol)")
                
                # 🆕 Index LIMIT ORDERS
                conn.execute("CREATE INDEX IF NOT EXISTS idx_limit_status ON limit_orders(status)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_limit_symbol ON limit_orders(symbol)")
                
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
                #Notification Telegram si activée
                if getattr(self, 'telegram_cfg', {}).get('enabled', False):
                    bot_token = self.telegram_cfg.get('bot_token')
                    chat_id = self.telegram_cfg.get('chat_id')
                    msg = f"<b>Nouvelle transaction</b>\n<b>Type:</b> {order_side}\n<b>Symbole:</> {symbol}\n<b>Quantité:</b> {qty:.6f}\n<b>Prix:</b> {price:.4f} USDC"
                    send_telegram_message(bot_token, chat_id, msg)
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
        """Compte les achats du jour - VERSION CORRIGÉE pour timestamps Binance"""
        try:
            if not date:
                date = datetime.now().strftime('%Y-%m-%d')
            
            # 🔧 CORRECTION: Timestamps Binance sont en millisecondes !
            date_start = int(datetime.strptime(date, '%Y-%m-%d').timestamp() * 1000)  # x1000 !
            date_end = date_start + (86400 * 1000)  # +24h en millisecondes
            
            with self.get_connection() as conn:
                cursor = conn.execute("""
                    SELECT COUNT(*) FROM transactions 
                    WHERE order_side = 'BUY'
                    AND CAST(transact_time AS INTEGER) >= ?
                    AND CAST(transact_time AS INTEGER) < ?
                """, (date_start, date_end))
                
                count = cursor.fetchone()[0]
                
                # Debug pour vérification
                self.logger.debug(f"🔍 Comptage achats {date}: {count} (range: {date_start} - {date_end})")
                
                return count
                
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
        """Stats rapides avec LIMIT orders"""
        try:
            today = datetime.now().strftime('%Y-%m-%d')
            today_start = int(datetime.strptime(today, '%Y-%m-%d').timestamp() * 1000)
            today_end = today_start + (86400 * 1000)
            
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
                
                # 🆕 LIMIT actifs
                cursor = conn.execute("SELECT COUNT(*) FROM limit_orders WHERE status = 'ACTIVE'")
                active_limits = cursor.fetchone()[0]
                
                return {
                    'daily_buys': daily_buys,
                    'active_oco': active_oco,
                    'active_limits': active_limits,
                    'total_active_sells': active_oco + active_limits
                }
                
        except Exception as e:
            self.logger.error(f"❌ Erreur stats: {e}")
            return {'daily_buys': 0, 'active_oco': 0, 'active_limits': 0, 'total_active_sells': 0}

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

    def insert_limit_order(self, symbol: str, order_id: str, buy_transaction_id: int,
                        profit_target: float, target_price: float, quantity: float,
                        kept_quantity: float = 0) -> int:
        """Insère un ordre LIMIT simple (fallback OCO)"""
        try:
            with self.get_connection() as conn:
                cursor = conn.execute("""
                    INSERT INTO limit_orders 
                    (symbol, order_id, buy_transaction_id, profit_target, 
                    target_price, quantity, kept_quantity)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (symbol, order_id, buy_transaction_id, profit_target,
                    target_price, quantity, kept_quantity))
                
                limit_id = cursor.lastrowid
                conn.commit()
                
                self.logger.info(f"📈 LIMIT enregistré: {symbol} - {order_id}")
                return limit_id
                
        except Exception as e:
            self.logger.error(f"❌ Erreur LIMIT: {e}")
            return 0

    def get_active_limit_orders(self) -> List[Dict]:
        """Récupère les ordres LIMIT actifs pour monitoring"""
        try:
            with self.get_connection() as conn:
                cursor = conn.execute("""
                    SELECT * FROM limit_orders 
                    WHERE status = 'ACTIVE'
                    ORDER BY created_at DESC
                """)
                
                orders = [dict(row) for row in cursor.fetchall()]
                
                if orders:
                    self.logger.debug(f"🔍 {len(orders)} ordre(s) LIMIT actifs trouvés")
                
                return orders
                
        except Exception as e:
            self.logger.error(f"❌ Erreur récupération LIMIT actifs: {e}")
            return []

    def update_limit_execution(self, order_id: str, execution_price: float, 
                            execution_qty: float):
        """Met à jour un ordre LIMIT exécuté"""
        try:
            with self.get_connection() as conn:
                conn.execute("""
                    UPDATE limit_orders 
                    SET status = 'FILLED', execution_price = ?, execution_qty = ?,
                        executed_at = CURRENT_TIMESTAMP
                    WHERE order_id = ?
                """, (execution_price, execution_qty, order_id))
                
                if conn.total_changes > 0:
                    conn.commit()
                    self.logger.info(f"🔄 LIMIT mis à jour: {order_id} -> FILLED")
                else:
                    self.logger.warning(f"⚠️  LIMIT {order_id} non trouvé pour mise à jour")
                
        except Exception as e:
            self.logger.error(f"❌ Erreur update LIMIT: {e}")

    def get_order_commissions_from_binance(self, binance_client, symbol: str, order_id: str) -> tuple:
        """Récupère les commissions réelles depuis Binance - VERSION CORRIGÉE"""
        try:
            # 1. ESSAYER D'ABORD get_order (pour les ordres récents)
            try:
                order_details = binance_client._make_request_with_retry(
                    binance_client.client.get_order,
                    symbol=symbol,
                    orderId=int(order_id)
                )
                
                if 'fills' in order_details and order_details['fills']:
                    total_commission = 0.0
                    commission_asset = 'USDC'
                    
                    for fill in order_details['fills']:
                        fill_commission = float(fill.get('commission', 0.0))
                        fill_asset = fill.get('commissionAsset', 'USDC')
                        
                        # Simple : garder la commission dans son asset original
                        total_commission += fill_commission
                        commission_asset = fill_asset
                    
                    if total_commission > 0:
                        self.logger.debug(f"✅ Commissions via get_order: {total_commission} {commission_asset}")
                        return total_commission, commission_asset
                    else:
                        self.logger.debug(f"⚠️ get_order: fills présents mais commissions = 0")
                else:
                    self.logger.debug(f"⚠️ get_order: pas de fills, essai get_my_trades")
            
            except Exception as order_error:
                self.logger.debug(f"⚠️ get_order échoué: {order_error}")
            
            # 2. 🔥 FALLBACK: get_my_trades (pour ordres anciens ou sans fills)
            try:
                trades = binance_client._make_request_with_retry(
                    binance_client.client.get_my_trades,
                    symbol=symbol,
                    orderId=int(order_id)
                )
                
                if trades:
                    total_commission = 0.0
                    commission_asset = 'USDC'
                    
                    for trade in trades:
                        trade_commission = float(trade.get('commission', 0.0))
                        trade_asset = trade.get('commissionAsset', 'USDC')
                        
                        total_commission += trade_commission
                        commission_asset = trade_asset  # Garde le dernier
                    
                    self.logger.debug(f"✅ Commissions via get_my_trades: {total_commission} {commission_asset}")
                    return total_commission, commission_asset
                else:
                    self.logger.warning(f"⚠️ Aucun trade trouvé pour ordre {order_id}")
            
            except Exception as trades_error:
                self.logger.warning(f"⚠️ get_my_trades échoué: {trades_error}")
            
            # 3. FALLBACK FINAL: Estimation
            self.logger.warning(f"⚠️ Impossible de récupérer commissions, utilisation estimation")
            return 0.0, 'USDC'
            
        except Exception as e:
            self.logger.error(f"❌ Erreur récupération commissions: {e}")
            return 0.0, 'USDC'
