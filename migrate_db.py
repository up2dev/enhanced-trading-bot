#!/usr/bin/env python3
import sqlite3
import shutil
from datetime import datetime

def migrate_database():
    db_path = "db/trading.db"
    backup_path = f"db/trading_backup_{datetime.now().strftime('%Y%m%d_%H%M')}.db"
    
    print(f"🔄 Migration de la base avec préservation des données...")
    
    # 1. SAUVEGARDE
    print(f"💾 Sauvegarde: {backup_path}")
    shutil.copy2(db_path, backup_path)
    
    # 2. CONNEXION
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 3. VÉRIFICATION DES DONNÉES
    cursor.execute("SELECT COUNT(*) FROM transactions")
    transactions_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM oco_orders")  
    oco_count = cursor.fetchone()[0]
    
    print(f"📊 Préservation de {transactions_count} transactions et {oco_count} ordre OCO")
    
    # 4. CRÉER NOUVELLES TABLES
    print("🔄 Création des nouvelles tables...")
    
    # Table transactions optimisée
    cursor.execute("""
        CREATE TABLE transactions_new (
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
    
    # Table OCO optimisée avec nouvelles colonnes
    cursor.execute("""
        CREATE TABLE oco_orders_new (
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
    
    # 5. MIGRATION DES DONNÉES
    print("📦 Migration des transactions...")
    cursor.execute("""
        INSERT INTO transactions_new 
        (id, symbol, order_id, transact_time, order_type, order_side, price, qty, commission, commission_asset, created_at)
        SELECT id, symbol, order_id, transact_time, order_type, order_side, price, qty, 
               COALESCE(commission, 0), COALESCE(commission_asset, 'USDC'), created_at
        FROM transactions
    """)
    
    print("📦 Migration des ordres OCO...")
    cursor.execute("""
        INSERT INTO oco_orders_new 
        (id, symbol, oco_order_id, profit_order_id, stop_order_id, buy_transaction_id, 
         status, profit_target, stop_loss_price, quantity, kept_quantity, created_at)
        SELECT id, symbol, oco_order_id, profit_order_id, stop_order_id, 
               COALESCE(buy_transaction_id, 0), COALESCE(status, 'ACTIVE'),
               profit_target, stop_loss_price, quantity, COALESCE(kept_quantity, 0), created_at
        FROM oco_orders
    """)
    
    # 6. REMPLACEMENT DES TABLES
    print("🔄 Remplacement des tables...")
    
    # Supprimer toutes les anciennes tables
    cursor.execute("DROP TABLE IF EXISTS alerts")
    cursor.execute("DROP TABLE IF EXISTS daily_stats") 
    cursor.execute("DROP TABLE IF EXISTS cooldown_cache")
    cursor.execute("DROP TABLE transactions")
    cursor.execute("DROP TABLE oco_orders")
    
    # Renommer les nouvelles
    cursor.execute("ALTER TABLE transactions_new RENAME TO transactions")
    cursor.execute("ALTER TABLE oco_orders_new RENAME TO oco_orders")
    
    # 7. CRÉER LES INDEX OPTIMISÉS
    print("📊 Création des index optimisés...")
    cursor.execute("CREATE INDEX idx_symbol_side_time ON transactions(symbol, order_side, transact_time)")
    cursor.execute("CREATE INDEX idx_order_side_time ON transactions(order_side, transact_time)")
    cursor.execute("CREATE INDEX idx_oco_status ON oco_orders(status)")
    cursor.execute("CREATE INDEX idx_oco_symbol ON oco_orders(symbol)")
    
    conn.commit()
    conn.close()
    
    print("✅ Migration terminée avec succès!")
    
    # 8. VÉRIFICATION
    print("🔍 Vérification...")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM transactions")
    new_transactions = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM oco_orders")
    new_oco = cursor.fetchone()[0]
    
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [row[0] for row in cursor.fetchall()]
    
    print(f"📊 Résultat:")
    print(f"   • Transactions préservées: {new_transactions}")
    print(f"   • Ordres OCO préservés: {new_oco}")
    print(f"   • Tables restantes: {', '.join(sorted(tables))}")
    
    conn.close()
    
    print(f"💾 Sauvegarde disponible: {backup_path}")

if __name__ == "__main__":
    migrate_database()
