#!/bin/bash

# 🤖 Enhanced Trading Bot - Script d'installation
# Raspberry Pi optimisé

set -e

echo "🤖 === ENHANCED TRADING BOT - INSTALLATION ==="
echo "🍓 Optimisé pour Raspberry Pi Zero W2"

# Vérifications préalables
echo "🔍 Vérification du système..."
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 non trouvé. Installation..."
    sudo apt update
    sudo apt install python3-full python3-pip python3-venv -y
fi

# Création environnement virtuel
echo "🐍 Création de l'environnement virtuel..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi

# Activation et installation dépendances
echo "📦 Installation des dépendances..."
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# Configuration
echo "⚙️ Configuration..."
if [ ! -f "config/config.json" ]; then
    if [ -f "config/config.template.json" ]; then
        echo "📋 Copie du template de configuration..."
        cp config/config.template.json config/config.json
        echo "⚠️  IMPORTANT: Éditez config/config.json avec vos clés API Binance"
        echo "   Chemin: $(pwd)/config/config.json"
    else
        echo "❌ Template de configuration non trouvé!"
        exit 1
    fi
fi

# Création des répertoires
echo "📁 Création des répertoires..."
mkdir -p logs db

# Permissions
echo "🔧 Configuration des permissions..."
chmod +x *.py
chmod +x *.sh

# Test d'installation
echo "🧪 Test de l'installation..."
if python3 -c "
import sys
sys.path.insert(0, '.')
try:
    from src.portfolio_manager import EnhancedPortfolioManager
    print('✅ Modules Python OK')
except Exception as e:
    print(f'❌ Erreur modules: {e}')
    sys.exit(1)
"; then
    echo "✅ Installation réussie!"
else
    echo "❌ Problème d'installation détecté"
    exit 1
fi

echo ""
echo "🎉 === INSTALLATION TERMINÉE ==="
echo ""
echo "📝 PROCHAINES ÉTAPES:"
echo "1. Éditez config/config.json avec vos clés API Binance"
echo "2. Configurez les permissions API sur Binance:"
echo "   ✅ Enable Trading"
echo "   ✅ Enable Reading"
echo "   ❌ Disable Withdrawals"
echo "3. Testez avec: python3 run_bot.py --dry-run"
echo "4. Configurez le cron: crontab -e"
echo ""
echo "📚 Lisez README.md pour plus d'informations"
