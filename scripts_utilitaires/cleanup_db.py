#!/usr/bin/env python3
"""
Enhanced Trading Bot - Nettoyage de base de données v2.1.8
Supporte OCO + LIMIT orders avec chemins corrigés depuis scripts_utilitaires/
"""

import sqlite3
import os
import sys
from datetime import datetime
import argparse

class DatabaseCleaner:
    def __init__(self, db_path="db/trading.db"):
        # 🔧 CORRECTION: Détection chemin depuis scripts_utilitaires/
        script_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(script_dir)
        
        # Si chemin relatif, le résoudre depuis project_root
        if not os.path.isabs(db_path):
            db_path = os.path.join(project_root, db_path)
        
        self.db_path = db_path
        
        if not os.path.exists(db_path):
            print(f"❌ Base de données non trouvée: {db_path}")
            sys.exit(1)
        
        # Créer une sauvegarde automatique dans le bon dossier
        db_dir = os.path.dirname(db_path)
        backup_path = os.path.join(db_dir, f"trading_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db")
        os.system(f"cp '{db_path}' '{backup_path}'")
        print(f"✅ Sauvegarde automatique: {backup_path}")
        
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
    
    def show_current_data(self):
        """Affiche les données actuelles - AVEC LIMIT ORDERS"""
        print("\n📊 === DONNÉES ACTUELLES ===")
        
        # 🆕 AJOUT: Table limit_orders
        tables = ['transactions', 'oco_orders', 'limit_orders']
        
        for table in tables:
            try:
                cursor = self.conn.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                print(f"📋 {table}: {count} enregistrement(s)")
                
                if count > 0:
                    # Afficher quelques exemples
                    cursor = self.conn.execute(f"SELECT * FROM {table} ORDER BY created_at DESC LIMIT 3")
                    rows = cursor.fetchall()
                    if rows:
                        print(f"   Derniers enregistrements:")
                        for row in rows:
                            if table == 'transactions':
                                print(f"   • {row['created_at']} - {row['symbol']} {row['order_side']} {row['qty']:.8f}")
                            elif table == 'oco_orders':
                                print(f"   • {row['created_at']} - {row['symbol']} {row['status']} (qty: {row.get('kept_quantity', 0):.8f})")
                            elif table == 'limit_orders':  # 🆕 AJOUT
                                print(f"   • {row['created_at']} - {row['symbol']} {row['status']} (qty: {row.get('kept_quantity', 0):.8f})")
                    print()
            except Exception as e:
                print(f"❌ Erreur lecture table {table}: {e}")
    
    def clear_all_data(self):
        """Supprime TOUTES les données - AVEC LIMIT ORDERS"""
        print("\n🗑️  === SUPPRESSION COMPLÈTE ===")
        
        confirmation = input("⚠️  ATTENTION: Supprimer TOUTES les données ? (oui/NON): ")
        
        if confirmation.lower() != 'oui':
            print("❌ Annulation")
            return False
        
        # 🆕 AJOUT: Table limit_orders
        tables = ['transactions', 'oco_orders', 'limit_orders']
        
        try:
            for table in tables:
                cursor = self.conn.execute(f"DELETE FROM {table}")
                deleted = cursor.rowcount
                print(f"🗑️  {table}: {deleted} enregistrement(s) supprimé(s)")
            
            # Reset des compteurs auto-increment
            for table in tables:
                self.conn.execute(f"DELETE FROM sqlite_sequence WHERE name='{table}'")
            
            self.conn.commit()
            print("✅ Suppression complète terminée")
            return True
            
        except Exception as e:
            print(f"❌ Erreur suppression: {e}")
            self.conn.rollback()
            return False
    
    def clear_transactions_only(self):
        """Supprime uniquement les transactions"""
        print("\n🗑️  === SUPPRESSION TRANSACTIONS SEULEMENT ===")
        
        cursor = self.conn.execute("SELECT COUNT(*) FROM transactions")
        count = cursor.fetchone()[0]
        
        confirmation = input(f"⚠️  Supprimer {count} transaction(s) ? (oui/NON): ")
        
        if confirmation.lower() != 'oui':
            print("❌ Annulation")
            return False
        
        try:
            cursor = self.conn.execute("DELETE FROM transactions")
            deleted = cursor.rowcount
            
            # Reset compteur
            self.conn.execute("DELETE FROM sqlite_sequence WHERE name='transactions'")
            
            self.conn.commit()
            print(f"✅ {deleted} transaction(s) supprimée(s)")
            return True
            
        except Exception as e:
            print(f"❌ Erreur: {e}")
            self.conn.rollback()
            return False
    
    def clear_oco_only(self):
        """Supprime uniquement les ordres OCO"""
        print("\n🗑️  === SUPPRESSION OCO SEULEMENT ===")
        
        cursor = self.conn.execute("SELECT COUNT(*) FROM oco_orders")
        count = cursor.fetchone()[0]
        
        confirmation = input(f"⚠️  Supprimer {count} ordre(s) OCO ? (oui/NON): ")
        
        if confirmation.lower() != 'oui':
            print("❌ Annulation")
            return False
        
        try:
            cursor = self.conn.execute("DELETE FROM oco_orders")
            deleted = cursor.rowcount
            
            # Reset compteur
            self.conn.execute("DELETE FROM sqlite_sequence WHERE name='oco_orders'")
            
            self.conn.commit()
            print(f"✅ {deleted} ordre(s) OCO supprimé(s)")
            return True
            
        except Exception as e:
            print(f"❌ Erreur: {e}")
            self.conn.rollback()
            return False
    
    def clear_limit_only(self):
        """🆕 NOUVEAU: Supprime uniquement les ordres LIMIT"""
        print("\n🗑️  === SUPPRESSION LIMIT ORDERS SEULEMENT ===")
        
        cursor = self.conn.execute("SELECT COUNT(*) FROM limit_orders")
        count = cursor.fetchone()[0]
        
        confirmation = input(f"⚠️  Supprimer {count} ordre(s) LIMIT ? (oui/NON): ")
        
        if confirmation.lower() != 'oui':
            print("❌ Annulation")
            return False
        
        try:
            cursor = self.conn.execute("DELETE FROM limit_orders")
            deleted = cursor.rowcount
            
            # Reset compteur
            self.conn.execute("DELETE FROM sqlite_sequence WHERE name='limit_orders'")
            
            self.conn.commit()
            print(f"✅ {deleted} ordre(s) LIMIT supprimé(s)")
            return True
            
        except Exception as e:
            print(f"❌ Erreur: {e}")
            self.conn.rollback()
            return False
    
    def clear_by_date(self, days_to_keep=7):
        """Supprime les données anciennes - AVEC LIMIT ORDERS"""
        print(f"\n🗑️  === SUPPRESSION DONNÉES > {days_to_keep} JOURS ===")
        
        try:
            # Compter ce qui sera supprimé
            cursor = self.conn.execute("""
                SELECT COUNT(*) FROM transactions 
                WHERE date(created_at) < date('now', '-{} days')
            """.format(days_to_keep))
            old_transactions = cursor.fetchone()[0]
            
            cursor = self.conn.execute("""
                SELECT COUNT(*) FROM oco_orders 
                WHERE date(created_at) < date('now', '-{} days')
            """.format(days_to_keep))
            old_oco = cursor.fetchone()[0]
            
            # 🆕 AJOUT: LIMIT orders
            cursor = self.conn.execute("""
                SELECT COUNT(*) FROM limit_orders 
                WHERE date(created_at) < date('now', '-{} days')
            """.format(days_to_keep))
            old_limits = cursor.fetchone()[0]
            
            print(f"📊 Transactions à supprimer: {old_transactions}")
            print(f"📊 Ordres OCO à supprimer: {old_oco}")
            print(f"📊 Ordres LIMIT à supprimer: {old_limits}")
            
            if old_transactions == 0 and old_oco == 0 and old_limits == 0:
                print("✅ Aucune donnée ancienne à supprimer")
                return True
            
            confirmation = input("⚠️  Continuer ? (oui/NON): ")
            if confirmation.lower() != 'oui':
                print("❌ Annulation")
                return False
            
            # Supprimer
            cursor = self.conn.execute("""
                DELETE FROM transactions 
                WHERE date(created_at) < date('now', '-{} days')
            """.format(days_to_keep))
            deleted_tx = cursor.rowcount
            
            cursor = self.conn.execute("""
                DELETE FROM oco_orders 
                WHERE date(created_at) < date('now', '-{} days')
            """.format(days_to_keep))
            deleted_oco = cursor.rowcount
            
            # 🆕 AJOUT: LIMIT orders
            cursor = self.conn.execute("""
                DELETE FROM limit_orders 
                WHERE date(created_at) < date('now', '-{} days')
            """.format(days_to_keep))
            deleted_limits = cursor.rowcount
            
            self.conn.commit()
            print(f"✅ Supprimé: {deleted_tx} transactions, {deleted_oco} OCO, {deleted_limits} LIMIT")
            return True
            
        except Exception as e:
            print(f"❌ Erreur: {e}")
            self.conn.rollback()
            return False
    
    def clear_orphaned_data(self):
        """Supprime les données orphelines - AVEC LIMIT ORDERS"""
        print("\n🧹 === NETTOYAGE DONNÉES ORPHELINES ===")
        
        try:
            # Trouver les transactions BUY sans OCO/LIMIT correspondants
            cursor = self.conn.execute("""
                SELECT t.id, t.symbol, t.created_at, t.order_side, t.qty
                FROM transactions t
                LEFT JOIN oco_orders o ON t.id = o.buy_transaction_id
                LEFT JOIN limit_orders l ON t.id = l.buy_transaction_id
                WHERE t.order_side = 'BUY' 
                AND o.id IS NULL AND l.id IS NULL
                ORDER BY t.created_at DESC
                LIMIT 20
            """)
            orphaned_buys = cursor.fetchall()
            
            # Trouver les OCO sans transaction d'achat correspondante
            cursor = self.conn.execute("""
                SELECT o.id, o.symbol, o.created_at, o.status
                FROM oco_orders o
                LEFT JOIN transactions t ON o.buy_transaction_id = t.id
                WHERE t.id IS NULL
                ORDER BY o.created_at DESC
                LIMIT 20
            """)
            orphaned_oco = cursor.fetchall()
            
            # 🆕 AJOUT: LIMIT sans transaction d'achat
            cursor = self.conn.execute("""
                SELECT l.id, l.symbol, l.created_at, l.status
                FROM limit_orders l
                LEFT JOIN transactions t ON l.buy_transaction_id = t.id
                WHERE t.id IS NULL
                ORDER BY l.created_at DESC
                LIMIT 20
            """)
            orphaned_limits = cursor.fetchall()
            
            print(f"📊 Transactions BUY sans OCO/LIMIT: {len(orphaned_buys)}")
            print(f"📊 OCO sans transaction d'achat: {len(orphaned_oco)}")
            print(f"📊 LIMIT sans transaction d'achat: {len(orphaned_limits)}")
            
            if orphaned_buys:
                print("\n🔍 Exemples de transactions BUY sans ordres:")
                for buy in orphaned_buys[:5]:
                    print(f"   • {buy['created_at']} - {buy['symbol']} BUY {buy['qty']:.8f}")
            
            if orphaned_oco:
                print("\n🔍 Exemples d'OCO sans transaction:")
                for oco in orphaned_oco[:5]:
                    print(f"   • {oco['created_at']} - {oco['symbol']} {oco['status']}")
            
            if orphaned_limits:
                print("\n🔍 Exemples de LIMIT sans transaction:")
                for limit in orphaned_limits[:5]:
                    print(f"   • {limit['created_at']} - {limit['symbol']} {limit['status']}")
            
            if len(orphaned_buys) == 0 and len(orphaned_oco) == 0 and len(orphaned_limits) == 0:
                print("✅ Aucune donnée orpheline trouvée")
                return True
            
            confirmation = input("⚠️  Supprimer ces données orphelines ? (oui/NON): ")
            if confirmation.lower() != 'oui':
                print("❌ Annulation")
                return False
            
            # Supprimer les données orphelines
            deleted_buys = 0
            deleted_oco = 0
            deleted_limits = 0
            
            if orphaned_buys:
                buy_ids = [str(buy['id']) for buy in orphaned_buys]
                cursor = self.conn.execute(f"""
                    DELETE FROM transactions 
                    WHERE id IN ({','.join(['?'] * len(buy_ids))})
                """, buy_ids)
                deleted_buys = cursor.rowcount
            
            if orphaned_oco:
                oco_ids = [str(oco['id']) for oco in orphaned_oco]
                cursor = self.conn.execute(f"""
                    DELETE FROM oco_orders 
                    WHERE id IN ({','.join(['?'] * len(oco_ids))})
                """, oco_ids)
                deleted_oco = cursor.rowcount
            
            # 🆕 AJOUT: Supprimer LIMIT orphelins
            if orphaned_limits:
                limit_ids = [str(limit['id']) for limit in orphaned_limits]
                cursor = self.conn.execute(f"""
                    DELETE FROM limit_orders 
                    WHERE id IN ({','.join(['?'] * len(limit_ids))})
                """, limit_ids)
                deleted_limits = cursor.rowcount
            
            self.conn.commit()
            print(f"✅ Supprimé: {deleted_buys} transactions, {deleted_oco} OCO, {deleted_limits} LIMIT orphelins")
            return True
            
        except Exception as e:
            print(f"❌ Erreur: {e}")
            self.conn.rollback()
            return False
    
    def interactive_cleanup(self):
        """Mode interactif pour le nettoyage - AVEC LIMIT ORDERS"""
        print("\n🧹 === NETTOYAGE INTERACTIF v2.1.8 ===")
        
        while True:
            print("\nOptions disponibles:")
            print("1. Voir les données actuelles")
            print("2. Supprimer TOUTES les données")
            print("3. Supprimer uniquement les transactions")
            print("4. Supprimer uniquement les OCO")
            print("5. 🆕 Supprimer uniquement les LIMIT")
            print("6. Supprimer les données anciennes")
            print("7. Nettoyer les données orphelines (recommandé)")
            print("8. Quitter")
            
            choice = input("\n🔍 Votre choix (1-8): ").strip()
            
            if choice == '1':
                self.show_current_data()
            elif choice == '2':
                if self.clear_all_data():
                    break
            elif choice == '3':
                self.clear_transactions_only()
            elif choice == '4':
                self.clear_oco_only()
            elif choice == '5':  # 🆕 NOUVEAU
                self.clear_limit_only()
            elif choice == '6':
                days = input("Nombre de jours à conserver (défaut: 7): ").strip()
                days = int(days) if days.isdigit() else 7
                self.clear_by_date(days)
            elif choice == '7':
                self.clear_orphaned_data()
            elif choice == '8':
                print("👋 Au revoir !")
                break
            else:
                print("❌ Choix invalide")
    
    def close(self):
        """Ferme la connexion"""
        self.conn.close()

def main():
    parser = argparse.ArgumentParser(description="Nettoyeur de base de données Trading Bot v2.1.8")
    parser.add_argument("--db", default="db/trading.db", help="Chemin vers la base")
    parser.add_argument("--clear-all", action="store_true", help="Supprimer toutes les données")
    parser.add_argument("--clear-transactions", action="store_true", help="Supprimer les transactions")
    parser.add_argument("--clear-oco", action="store_true", help="Supprimer les OCO")
    parser.add_argument("--clear-limits", action="store_true", help="🆕 Supprimer les LIMIT")
    parser.add_argument("--clear-orphaned", action="store_true", help="Nettoyer les données orphelines")
    parser.add_argument("--days-keep", type=int, help="Garder les N derniers jours")
    parser.add_argument("--interactive", "-i", action="store_true", help="Mode interactif")
    
    args = parser.parse_args()
    
    cleaner = DatabaseCleaner(args.db)
    
    try:
        if args.interactive:
            cleaner.interactive_cleanup()
        elif args.clear_all:
            cleaner.clear_all_data()
        elif args.clear_transactions:
            cleaner.clear_transactions_only()
        elif args.clear_oco:
            cleaner.clear_oco_only()
        elif args.clear_limits:  # 🆕 NOUVEAU
            cleaner.clear_limit_only()
        elif args.clear_orphaned:
            cleaner.clear_orphaned_data()
        elif args.days_keep:
            cleaner.clear_by_date(args.days_keep)
        else:
            cleaner.show_current_data()
            print("\n💡 Utilisez --interactive pour le mode interactif")
            print("💡 Ou --clear-orphaned pour nettoyer les données orphelines")
    
    finally:
        cleaner.close()

if __name__ == "__main__":
    main()
