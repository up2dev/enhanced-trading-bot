#!/bin/bash

# 🔄 Enhanced Trading Bot - Script de mise à jour

echo "🔄 === MISE À JOUR DU TRADING BOT ==="

# Sauvegardes
echo "💾 Sauvegarde de la configuration..."
if [ -f "config/config.json" ]; then
    cp config/config.json config/config.json.backup
    echo "✅ Configuration sauvegardée"
fi

if [ -f "db/trading.db" ]; then
    cp db/trading.db db/trading_backup_$(date +%Y%m%d_%H%M).db
    echo "✅ Base de données sauvegardée"
fi

# Mise à jour Git
echo "📥 Récupération des mises à jour..."
git stash push -m "Sauvegarde locale avant mise à jour"
git pull origin main

# Mise à jour dépendances
echo "📦 Mise à jour des dépendances..."
source venv/bin/activate
pip install --upgrade -r requirements.txt

# Restaurer config si nécessaire
if [ -f "config/config.json.backup" ] && [ ! -f "config/config.json" ]; then
    cp config/config.json.backup config/config.json
    echo "✅ Configuration restaurée"
fi

# Permissions
chmod +x *.py *.sh

echo "✅ Mise à jour terminée!"
echo "🧪 Testez avec: python3 run_bot.py --dry-run"
