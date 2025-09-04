#!/usr/bin/env python3
"""
Enhanced Trading Bot - Explorateur de base de données SQLite
Version corrigée sans erreurs sur les valeurs NULL
"""

import sqlite3
import sys
import os
from datetime import datetime, timedelta
import argparse

class DatabaseExplorer:
    def __init__(self, db_path="../db/trading.db"):
        self.db_path = db_path
        if not os.path.exists(db_path):
            print(f"❌ Base de données non trouvée: {db_path}")
            sys.exit(1)
        
        print(f"📊 Connexion à: {db_path}")
    
    def get_connection(self):
        """Connexion à la base"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            return conn
        except Exception as e:
            print(f"❌ Erreur connexion: {e}")
            sys.exit(1)
    
    def safe_str(self, value, max_length=30):
        """Conversion sécurisée en string"""
        if value is None:
            return "NULL"
        
        str_value = str(value)
        if len(str_value) > max_length:
            return str_value[:max_length-3] + "..."
        return str_value
    
    def print_table(self, headers, rows, max_width=25):
        """Affichage sécurisé en tableau"""
        if not rows:
            print("📭 Aucune donnée")
            return
        
        # Calculer les largeurs de colonnes
        widths = []
        for i, header in enumerate(headers):
            width = len(str(header))
            for row in rows:
                if i < len(row):
                    cell_value = self.safe_str(row[i], max_width)
                    width = max(width, len(cell_value))
            widths.append(min(width, max_width))
        
        # Ligne de séparation
        separator = "+" + "+".join("-" * (w + 2) for w in widths) + "+"
        
        # Afficher les en-têtes
        print(separator)
        header_row = "|"
        for header, width in zip(headers, widths):
            header_str = str(header)[:width]
            header_row += f" {header_str:<{width}} |"
        print(header_row)
        print(separator)
        
        # Afficher les données
        for row in rows:
            data_row = "|"
            for i, width in enumerate(widths):
                if i < len(row):
                    cell_value = self.safe_str(row[i], width)
                else:
                    cell_value = ""
                data_row += f" {cell_value:<{width}} |"
            print(data_row)
        
        print(separator)
        print(f"📊 {len(rows)} ligne(s) affichée(s)")
    
    def print_vertical(self, headers, rows):
        """Affichage vertical pour tables avec beaucoup de colonnes"""
        if not rows:
            print("📭 Aucune donnée")
            return
        
        for i, row in enumerate(rows, 1):
            print(f"\n🔸 === ENREGISTREMENT {i} ===")
            for j, header in enumerate(headers):
                value = self.safe_str(row[j] if j < len(row) else None, 50)
                print(f"  {header:<20}: {value}")
            
            if i < len(rows):
                print("-" * 50)
        
        print(f"\n📊 {len(rows)} enregistrement(s) affiché(s)")
    
    def list_tables(self):
        """Liste toutes les tables"""
        print("\n🗂️  === TABLES DISPONIBLES ===")
        
        with self.get_connection() as conn:
            cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
            tables = [row[0] for row in cursor.fetchall()]
        
        if tables:
            print(f"📊 {len(tables)} table(s) trouvée(s):\n")
            for i, table in enumerate(tables, 1):
                try:
                    cursor = conn.execute(f"SELECT COUNT(*) FROM `{table}`")
                    count = cursor.fetchone()[0]
                    print(f"{i:2d}. {table:<20} ({count:>6} ligne(s))")
                except Exception as e:
                    print(f"{i:2d}. {table:<20} (erreur: {e})")
        else:
            print("❌ Aucune table trouvée")
        
        return tables
    
    def show_table_structure(self, table_name):
        """Affiche la structure d'une table"""
        print(f"\n📋 === STRUCTURE DE LA TABLE '{table_name}' ===")
        
        with self.get_connection() as conn:
            try:
                cursor = conn.execute(f"PRAGMA table_info(`{table_name}`)")
                columns = cursor.fetchall()
                
                if columns:
                    headers = ["#", "Colonne", "Type", "NULL", "Défaut", "Clé"]
                    rows = []
                    for col in columns:
                        rows.append([
                            col[0],  # cid
                            col[1],  # name
                            col[2],  # type
                            "✅" if col[3] == 0 else "❌",  # notnull (inversé)
                            self.safe_str(col[4]) if col[4] else "-",  # dflt_value
                            "🔑" if col[5] else "-"   # pk
                        ])
                    
                    self.print_table(headers, rows)
                    
                    # Informations supplémentaires
                    cursor = conn.execute(f"SELECT COUNT(*) FROM `{table_name}`")
                    count = cursor.fetchone()[0]
                    print(f"\n💡 Total des enregistrements: {count}")
                    
                else:
                    print("❌ Table non trouvée")
            except Exception as e:
                print(f"❌ Erreur: {e}")
    
    def show_table_data(self, table_name, limit=10, vertical=False):
        """Affiche les données d'une table"""
        print(f"\n📊 === DONNÉES DE LA TABLE '{table_name}' ===")
        
        query = f"SELECT * FROM `{table_name}`"
        
        # Ajouter ORDER BY si colonne id ou created_at existe
        if self._has_column(table_name, 'id'):
            query += " ORDER BY id DESC"
        elif self._has_column(table_name, 'created_at'):
            query += " ORDER BY created_at DESC"
        
        query += f" LIMIT {limit}"
        
        print(f"🔍 Requête: {query}")
        
        with self.get_connection() as conn:
            try:
                cursor = conn.execute(query)
                rows = cursor.fetchall()
                
                if rows:
                    headers = [description[0] for description in cursor.description]
                    data = [list(row) for row in rows]
                    
                    # Choisir le mode d'affichage selon le nombre de colonnes
                    if vertical or len(headers) > 6:
                        self.print_vertical(headers, data)
                    else:
                        self.print_table(headers, data)
                else:
                    print("📭 Aucune donnée trouvée")
                    
            except Exception as e:
                print(f"❌ Erreur requête: {e}")
    
    def _has_column(self, table_name, column_name):
        """Vérifie si une table a une colonne spécifique"""
        with self.get_connection() as conn:
            try:
                cursor = conn.execute(f"PRAGMA table_info(`{table_name}`)")
                columns = [row[1] for row in cursor.fetchall()]
                return column_name in columns
            except:
                return False
    
    def quick_stats(self):
        """Statistiques rapides"""
        print("\n📊 === STATISTIQUES RAPIDES ===")
        
        with self.get_connection() as conn:
            try:
                # Vérifier si les tables existent
                cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
                existing_tables = [row[0] for row in cursor.fetchall()]
                
                # Transactions
                if 'transactions' in existing_tables:
                    cursor = conn.execute("SELECT COUNT(*) FROM transactions")
                    total_transactions = cursor.fetchone()[0]
                    
                    cursor = conn.execute("SELECT COUNT(*) FROM transactions WHERE order_side = 'BUY'")
                    total_buys = cursor.fetchone()[0]
                    
                    cursor = conn.execute("SELECT COUNT(*) FROM transactions WHERE order_side = 'SELL'")
                    total_sells = cursor.fetchone()[0]
                    
                    print(f"💰 Transactions: {total_transactions} total ({total_buys} achats, {total_sells} ventes)")
                    
                    # Dernière transaction
                    cursor = conn.execute("SELECT MAX(created_at), symbol FROM transactions")
                    last_info = cursor.fetchone()
                    if last_info[0]:
                        print(f"🕐 Dernière transaction: {last_info[0]} ({last_info[1]})")
                    
                    # Volume par crypto (derniers 7 jours)
                    cursor = conn.execute("""
                        SELECT symbol, COUNT(*) as trades, 
                               ROUND(SUM(price * qty), 2) as volume_usdc
                        FROM transactions 
                        WHERE created_at >= date('now', '-7 days')
                        GROUP BY symbol 
                        ORDER BY volume_usdc DESC 
                        LIMIT 5
                    """)
                    volume_data = cursor.fetchall()
                    
                    if volume_data:
                        print(f"\n💹 Top 5 cryptos (volume 7 jours):")
                        for i, (symbol, trades, volume) in enumerate(volume_data, 1):
                            print(f"   {i}. {symbol}: {trades} trades, {volume} USDC")
                
                # OCO
                if 'oco_orders' in existing_tables:
                    cursor = conn.execute("SELECT COUNT(*) FROM oco_orders")
                    total_oco = cursor.fetchone()[0]
                    
                    cursor = conn.execute("SELECT COUNT(*) FROM oco_orders WHERE status = 'ACTIVE'")
                    active_oco = cursor.fetchone()[0]
                    
                    cursor = conn.execute("SELECT COUNT(*) FROM oco_orders WHERE status LIKE '%FILLED'")
                    executed_oco = cursor.fetchone()[0]
                    
                    print(f"\n🎯 Ordres OCO: {total_oco} total ({active_oco} actifs, {executed_oco} exécutés)")
                    
                    if active_oco > 0:
                        cursor = conn.execute("""
                            SELECT symbol, COUNT(*) as count
                            FROM oco_orders 
                            WHERE status = 'ACTIVE'
                            GROUP BY symbol 
                            ORDER BY count DESC
                        """)
                        active_by_symbol = cursor.fetchall()
                        
                        print("   📈 OCO actifs par crypto:")
                        for symbol, count in active_by_symbol:
                            print(f"      • {symbol}: {count}")
                
                # Résumé général
                total_tables = len(existing_tables)
                print(f"\n📊 Base de données: {total_tables} table(s)")
                
            except Exception as e:
                print(f"❌ Erreur statistiques: {e}")
    
    def search_by_symbol(self, symbol, days=7, limit=20):
        """Recherche par symbole crypto"""
        print(f"\n🔍 === RECHERCHE '{symbol.upper()}' ({days} derniers jours) ===")
        
        with self.get_connection() as conn:
            try:
                # Transactions
                query = """
                    SELECT created_at, order_side, price, qty, 
                           ROUND(price * qty, 2) as value_usdc, commission
                    FROM transactions 
                    WHERE symbol LIKE ? 
                    AND created_at >= date('now', '-{} days')
                    ORDER BY created_at DESC 
                    LIMIT ?
                """.format(days)
                
                cursor = conn.execute(query, (f"%{symbol.upper()}%", limit))
                rows = cursor.fetchall()
                
                if rows:
                    headers = ["Date", "Type", "Prix", "Qté", "Valeur USDC", "Commission"]
                    data = []
                    for row in rows:
                        data.append([
                            row[0][:16] if row[0] else "",  # Date courte
                            row[1],  # side
                            f"{row[2]:.6f}" if row[2] else "",  # price
                            f"{row[3]:.8f}" if row[3] else "",  # qty
                            f"{row[4]:.2f}" if row[4] else "",  # value
                            f"{row[5]:.4f}" if row[5] else ""   # commission
                        ])
                    
                    self.print_table(headers, data)
                    
                    # Statistiques
                    buy_count = len([r for r in rows if r[1] == 'BUY'])
                    sell_count = len([r for r in rows if r[1] == 'SELL'])
                    total_value = sum(float(r[4]) for r in rows if r[4])
                    
                    print(f"\n📊 Résumé: {buy_count} achats, {sell_count} ventes, {total_value:.2f} USDC total")
                    
                else:
                    print("📭 Aucune transaction trouvée")
                    
            except Exception as e:
                print(f"❌ Erreur recherche: {e}")
    
    def interactive_mode(self):
        """Mode interactif"""
        print("\n🎮 === MODE INTERACTIF ===")
        print("Commandes disponibles:")
        print("  list              - Lister les tables")
        print("  show <table> [n]  - Afficher n lignes d'une table")
        print("  showv <table> [n] - Afficher en mode vertical")
        print("  struct <table>    - Structure d'une table")
        print("  stats             - Statistiques rapides")
        print("  search <crypto>   - Rechercher par crypto")
        print("  sql <requête>     - Exécuter une requête SQL")
        print("  help              - Afficher l'aide")
        print("  quit              - Quitter")
        
        # Lister les tables au démarrage
        tables = self.list_tables()
        
        while True:
            try:
                command = input("\n🔍 db> ").strip()
                
                if not command:
                    continue
                
                parts = command.split()
                cmd = parts[0].lower()
                
                if cmd in ['quit', 'exit', 'q']:
                    print("👋 Au revoir !")
                    break
                    
                elif cmd == 'help':
                    print("\n📖 === AIDE ===")
                    print("  list                    - Lister toutes les tables")
                    print("  show transactions 20    - Afficher 20 transactions")
                    print("  showv oco_orders        - OCO en mode vertical")
                    print("  struct transactions     - Structure de la table")
                    print("  stats                   - Statistiques générales")
                    print("  search BTC              - Transactions BTC")
                    print("  sql SELECT COUNT(*)...  - Requête personnalisée")
                    print(f"\n💡 Tables: {', '.join(tables)}")
                    
                elif cmd == 'list':
                    tables = self.list_tables()
                    
                elif cmd == 'show' and len(parts) > 1:
                    table = parts[1]
                    limit = int(parts[2]) if len(parts) > 2 else 10
                    self.show_table_data(table, limit=limit, vertical=False)
                    
                elif cmd == 'showv' and len(parts) > 1:
                    table = parts[1]
                    limit = int(parts[2]) if len(parts) > 2 else 5
                    self.show_table_data(table, limit=limit, vertical=True)
                    
                elif cmd == 'struct' and len(parts) > 1:
                    self.show_table_structure(parts[1])
                    
                elif cmd == 'stats':
                    self.quick_stats()
                    
                elif cmd == 'search' and len(parts) > 1:
                    symbol = parts[1]
                    days = int(parts[2]) if len(parts) > 2 else 7
                    self.search_by_symbol(symbol, days=days)
                    
                elif cmd == 'sql' and len(parts) > 1:
                    sql_query = ' '.join(parts[1:])
                    self.execute_custom_query(sql_query)
                    
                else:
                    print("❌ Commande inconnue. Tapez 'help' pour l'aide.")
                    
            except KeyboardInterrupt:
                print("\n👋 Au revoir !")
                break
            except Exception as e:
                print(f"❌ Erreur: {e}")
    
    def execute_custom_query(self, query):
        """Exécute une requête SQL personnalisée"""
        print(f"\n🔍 Requête: {query}")
        
        with self.get_connection() as conn:
            try:
                cursor = conn.execute(query)
                
                if query.strip().upper().startswith('SELECT'):
                    rows = cursor.fetchall()
                    if rows:
                        headers = [description[0] for description in cursor.description]
                        data = [list(row) for row in rows]
                        
                        # Mode vertical si beaucoup de colonnes
                        if len(headers) > 6:
                            self.print_vertical(headers, data)
                        else:
                            self.print_table(headers, data)
                    else:
                        print("📭 Aucun résultat")
                else:
                    changes = cursor.rowcount
                    print(f"✅ Requête exécutée ({changes} ligne(s) affectée(s))")
                    
            except Exception as e:
                print(f"❌ Erreur SQL: {e}")

def main():
    parser = argparse.ArgumentParser(
        description="Explorateur de base de données Trading Bot",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemples d'utilisation:
  python3 db_query.py                    # Vue d'ensemble
  python3 db_query.py --stats            # Statistiques rapides
  python3 db_query.py --table transactions --limit 20
  python3 db_query.py --interactive      # Mode interactif (recommandé)
        """
    )
    
    parser.add_argument("--db", default="db/trading.db", help="Chemin vers la base de données")
    parser.add_argument("--table", help="Afficher une table spécifique")
    parser.add_argument("--limit", type=int, default=10, help="Nombre de lignes à afficher")
    parser.add_argument("--stats", action="store_true", help="Afficher les statistiques")
    parser.add_argument("--interactive", "-i", action="store_true", help="Mode interactif")
    parser.add_argument("--vertical", "-v", action="store_true", help="Affichage vertical")
    
    args = parser.parse_args()
    
    explorer = DatabaseExplorer(args.db)
    
    if args.interactive:
        explorer.interactive_mode()
    elif args.stats:
        explorer.quick_stats()
    elif args.table:
        explorer.show_table_structure(args.table)
        explorer.show_table_data(args.table, limit=args.limit, vertical=args.vertical)
    else:
        # Mode par défaut
        explorer.list_tables()
        explorer.quick_stats()
        print("\n💡 Utilisez --interactive pour le mode interactif complet")

if __name__ == "__main__":
    main()
