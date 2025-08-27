#!/usr/bin/env python3
"""
Enhanced Trading Bot - Dashboard Server
Point d'entrée simple pour lancer le dashboard web
"""

import sys
import os
from pathlib import Path

# Ajouter le dossier dashboard au path
dashboard_path = Path(__file__).parent / "dashboard"
sys.path.insert(0, str(dashboard_path))

# Ajouter le dossier racine pour accès aux modules src
sys.path.insert(0, str(Path(__file__).parent))

if __name__ == "__main__":
    try:
        from dashboard.app import create_app
        
        print("🌐 === ENHANCED TRADING BOT DASHBOARD ===")
        print("📊 Démarrage du serveur web...")
        
        app = create_app()
        
        print("✅ Dashboard disponible sur:")
        print("   🏠 Local: http://localhost:5000")
        print("   📱 Réseau: http://192.168.1.XXX:5000")
        print("   🛑 Ctrl+C pour arrêter")
        
        app.run(
            host='0.0.0.0',
            port=5000,
            debug=False,
            use_reloader=False
        )
        
    except ImportError as e:
        print(f"❌ Erreur import dashboard: {e}")
        print("💡 Installez les dépendances: pip install flask")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Erreur démarrage: {e}")
        sys.exit(1)
