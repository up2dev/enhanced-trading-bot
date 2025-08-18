#!/bin/bash

# 🤖 Enhanced Trading Bot - Installation complète
# Raspberry Pi optimisé avec options avancées

set -e

# Couleurs pour l'affichage
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🤖 === ENHANCED TRADING BOT - INSTALLATION ===${NC}"
echo -e "${GREEN}🍓 Optimisé pour Raspberry Pi Zero W2${NC}"
echo ""

# Détection utilisateur et chemin
CURRENT_USER=$(whoami)
INSTALL_PATH=$(pwd)

echo -e "${BLUE}📍 Installation dans: ${INSTALL_PATH}${NC}"
echo -e "${BLUE}👤 Utilisateur: ${CURRENT_USER}${NC}"
echo ""

# Fonction d'installation système
install_system_deps() {
    echo -e "${YELLOW}🔍 Vérification des dépendances système...${NC}"
    
    # Mise à jour système
    echo "📦 Mise à jour du système..."
    sudo apt update && sudo apt upgrade -y
    
    # Installation paquets nécessaires
    echo "📦 Installation des dépendances..."
    sudo apt install python3-full python3-pip python3-venv git sqlite3 curl -y
    
    echo -e "${GREEN}✅ Dépendances système installées${NC}"
}

# Fonction d'installation Python
install_python_deps() {
    echo -e "${YELLOW}🐍 Configuration de l'environnement Python...${NC}"
    
    # Création environnement virtuel
    if [ ! -d "venv" ]; then
        echo "🔧 Création de l'environnement virtuel..."
        python3 -m venv venv
    fi
    
    # Activation et installation
    echo "📦 Installation des dépendances Python..."
    source venv/bin/activate
    pip install --upgrade pip
    
    if [ -f "requirements.txt" ]; then
        pip install -r requirements.txt
    else
        echo -e "${RED}❌ requirements.txt non trouvé!${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}✅ Environnement Python configuré${NC}"
}

# Fonction de configuration
setup_config() {
    echo -e "${YELLOW}⚙️ Configuration du bot...${NC}"
    
    # Création des répertoires
    mkdir -p logs db config
    
    # Configuration depuis template
    if [ ! -f "config/config.json" ]; then
        if [ -f "config/config.template.json" ]; then
            cp config/config.template.json config/config.json
            echo -e "${GREEN}📋 Configuration créée depuis template${NC}"
            echo -e "${YELLOW}⚠️  IMPORTANT: Éditez config/config.json avec vos clés API${NC}"
        else
            echo -e "${RED}❌ Template de configuration manquant!${NC}"
            exit 1
        fi
    fi
    
    # Configuration email si template existe
    if [ -f "config/email_config.template.json" ] && [ ! -f "config/email_config.json" ]; then
        cp config/email_config.template.json config/email_config.json
        echo -e "${GREEN}📧 Configuration email créée${NC}"
    fi
    
    # Permissions
    chmod +x *.py *.sh
    chmod 755 logs db config
    
    echo -e "${GREEN}✅ Configuration terminée${NC}"
}

# Fonction logrotate (optionnel)
setup_logrotate() {
    echo -e "${YELLOW}📋 Configuration de la rotation des logs...${NC}"
    
    sudo tee /etc/logrotate.d/trading-bot > /dev/null <<EOF
${INSTALL_PATH}/logs/*.log {
    daily
    rotate 15
    compress
    delaycompress
    missingok
    notifempty
    copytruncate
    olddir ${INSTALL_PATH}/logs/archived
}
EOF
    
    # Créer le répertoire archived
    mkdir -p logs/archived
    
    echo -e "${GREEN}✅ Logrotate configuré${NC}"
}

# Test de l'installation
test_installation() {
    echo -e "${YELLOW}🧪 Test de l'installation...${NC}"
    
    source venv/bin/activate
    
    if python3 -c "
import sys
sys.path.insert(0, '.')
try:
    from src.portfolio_manager import EnhancedPortfolioManager
    from src.binance_client import EnhancedBinanceClient
    print('✅ Modules principaux OK')
except ImportError as e:
    print(f'❌ Erreur import: {e}')
    sys.exit(1)
except Exception as e:
    print(f'❌ Erreur: {e}')
    sys.exit(1)
"; then
        echo -e "${GREEN}✅ Test d'installation réussi!${NC}"
    else
        echo -e "${RED}❌ Test d'installation échoué${NC}"
        exit 1
    fi
}

# Affichage des instructions finales
show_final_instructions() {
    echo ""
    echo -e "${GREEN}🎉 === INSTALLATION TERMINÉE AVEC SUCCÈS ===${NC}"
    echo ""
    echo -e "${BLUE}📝 PROCHAINES ÉTAPES:${NC}"
    echo "1. 🔑 Éditez votre configuration:"
    echo "   nano config/config.json"
    echo ""
    echo "2. 📧 Configurez les emails (optionnel):"
    echo "   nano config/email_config.json"
    echo ""
    echo "3. 🔒 Configurez les permissions API Binance:"
    echo "   ✅ Enable Trading"
    echo "   ✅ Enable Reading" 
    echo "   ❌ Disable Withdrawals"
    echo ""
    echo "4. 🧪 Testez le bot:"
    echo "   source venv/bin/activate"
    echo "   python3 run_bot.py --dry-run"
    echo ""
    echo "5. ⏰ Configurez l'automatisation (cron):"
    echo "   crontab -e"
    echo "   # Ajoutez:"
    echo "   */10 * * * * cd ${INSTALL_PATH} && ${INSTALL_PATH}/run_wrapper.sh"
    echo "   0 23 * * * cd ${INSTALL_PATH} && ${INSTALL_PATH}/monitor.sh"
    echo ""
    echo -e "${BLUE}📚 Documentation complète: README.md${NC}"
    echo -e "${BLUE}🐛 Support: GitHub Issues${NC}"
}

# MENU PRINCIPAL
echo "Choisissez le type d'installation:"
echo "1. 🚀 Installation complète (recommandée)"
echo "2. 🔧 Installation basique (sans logrotate)"
echo "3. 📊 Système seulement (dépendances)"
echo "4. 🐍 Python seulement (environnement)"
echo ""
read -p "Votre choix (1-4): " choice

case $choice in
    1)
        echo -e "${GREEN}🚀 Installation complète sélectionnée${NC}"
        install_system_deps
        install_python_deps
        setup_config
        setup_logrotate
        test_installation
        show_final_instructions
        ;;
    2)
        echo -e "${GREEN}🔧 Installation basique sélectionnée${NC}"
        install_system_deps
        install_python_deps
        setup_config
        test_installation
        show_final_instructions
        ;;
    3)
        echo -e "${GREEN}📊 Installation système seulement${NC}"
        install_system_deps
        ;;
    4)
        echo -e "${GREEN}🐍 Installation Python seulement${NC}"
        install_python_deps
        setup_config
        test_installation
        ;;
    *)
        echo -e "${RED}❌ Choix invalide${NC}"
        exit 1
        ;;
esac

echo ""
echo -e "${GREEN}🎯 Installation terminée avec succès!${NC}"