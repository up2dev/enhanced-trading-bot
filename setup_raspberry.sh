#!/bin/bash
echo "🚀 Installation Enhanced Trading Bot sur Raspberry Pi"

# Mise à jour système
sudo apt update && sudo apt upgrade -y

# Installation Python et dépendances système
sudo apt install python3 python3-pip python3-venv git sqlite3 -y

# Création de l'environnement virtuel
python3 -m venv venv
source venv/bin/activate

# Installation dépendances Python
pip install --upgrade pip
pip install -r requirements.txt

# Création des répertoires
mkdir -p logs/archived db config

# Configuration des permissions
chmod +x run_bot.py
chmod 755 logs db config

# Configuration logrotate
sudo tee /etc/logrotate.d/trading-bot > /dev/null <<EOF
/home/pi/enhanced_trading_bot/logs/*.log {
    daily
    rotate 15
    compress
    delaycompress
    missingok
    notifempty
    copytruncate
    olddir /home/pi/enhanced_trading_bot/logs/archived
}
EOF

echo "✅ Installation terminée !"
echo "📋 Éditez config/config.json avec vos clés API"
echo "🧪 Test: python3 run_bot.py --dry-run"
echo "⏰ Cron: */30 * * * * cd /home/pi/enhanced_trading_bot && /home/pi/enhanced_trading_bot/venv/bin/python run_bot.py >> logs/cron.log 2>&1"
