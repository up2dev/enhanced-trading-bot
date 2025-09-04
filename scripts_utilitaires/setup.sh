#!/bin/bash

# 🤖 Enhanced Trading Bot - Installation complète
# Script déplacé dans scripts_utilitaires/ - Chemins corrigés v2.1.8

set -e

# Couleurs pour l'affichage
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🤖 === ENHANCED TRADING BOT - INSTALLATION v2.1.8 ===${NC}"
echo -e "${GREEN}🍓 Optimisé pour Raspberry Pi Zero W2${NC}"
echo ""

# 🔧 CORRECTION: Détection chemin racine du projet
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"  # Remonte d'un niveau
CURRENT_USER=$(whoami)

echo -e "${BLUE}📍 Script dans: ${SCRIPT_DIR}${NC}"
echo -e "${BLUE}📍 Projet dans: ${PROJECT_ROOT}${NC}"
echo -e "${BLUE}👤 Utilisateur: ${CURRENT_USER}${NC}"
echo ""

# Vérification que nous sommes dans le bon projet
if [ ! -f "${PROJECT_ROOT}/run_bot.py" ] || [ ! -f "${PROJECT_ROOT}/smart_monitor.py" ]; then
    echo -e "${RED}❌ Erreur: Structure de projet non trouvée${NC}"
    echo -e "${RED}   run_bot.py et smart_monitor.py doivent être à la racine${NC}"
    exit 1
fi

# 🔧 CORRECTION: Toutes les opérations dans PROJECT_ROOT
cd "$PROJECT_ROOT"
echo -e "${GREEN}✅ Position corrigée vers racine du projet${NC}"

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
    
    # Création environnement virtuel (dans PROJECT_ROOT)
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
        echo -e "${RED}❌ requirements.txt non trouvé dans ${PROJECT_ROOT}!${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}✅ Environnement Python configuré${NC}"
}

# Fonction de configuration
setup_config() {
    echo -e "${YELLOW}⚙️ Configuration du bot...${NC}"
    
    # Création des répertoires (dans PROJECT_ROOT)
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
    
    # 🆕 Configuration email pour Smart Monitor v2.1.8
    if [ -f "config/email_config.template.json" ] && [ ! -f "config/email_config.json" ]; then
        cp config/email_config.template.json config/email_config.json
        echo -e "${GREEN}📧 Configuration email créée pour Smart Monitor${NC}"
    fi
    
    # Permissions (scripts racine + utilitaires)
    chmod +x *.py *.sh scripts_utilitaires/*.py scripts_utilitaires/*.sh 2>/dev/null || true
    chmod 755 logs db config
    
    echo -e "${GREEN}✅ Configuration terminée${NC}"
}

# Fonction logrotate (optionnel)
setup_logrotate() {
    echo -e "${YELLOW}📋 Configuration de la rotation des logs...${NC}"
    
    # 🔧 CORRECTION: Utiliser PROJECT_ROOT dans logrotate
    sudo tee /etc/logrotate.d/trading-bot > /dev/null <<EOF
${PROJECT_ROOT}/logs/*.log {
    daily
    rotate 15
    compress
    delaycompress
    missingok
    notifempty
    copytruncate
    olddir ${PROJECT_ROOT}/logs/archived
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
    
    # Test des modules principaux
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
        echo -e "${GREEN}✅ Modules principaux OK${NC}"
    else
        echo -e "${RED}❌ Test des modules échoué${NC}"
        exit 1
    fi
    
    # 🆕 Test du Smart Monitor v2.1.8
    echo "🧪 Test du Smart Monitor..."
    if python3 smart_monitor.py daily --help &>/dev/null || python3 -c "
import sys
try:
    exec(open('smart_monitor.py').read())
    print('✅ Smart Monitor OK')
except SystemExit:
    print('✅ Smart Monitor OK (exit normal)')
except Exception as e:
    print(f'⚠️  Smart Monitor: {e}')
"; then
        echo -e "${GREEN}✅ Smart Monitor v2.1.8 prêt${NC}"
    else
        echo -e "${YELLOW}⚠️  Smart Monitor nécessite configuration complète${NC}"
    fi
}

# Affichage des instructions finales
show_final_instructions() {
    echo ""
    echo -e "${GREEN}🎉 === INSTALLATION v2.1.8 TERMINÉE AVEC SUCCÈS ===${NC}"
    echo ""
    echo -e "${BLUE}📝 PROCHAINES ÉTAPES:${NC}"
    echo "1. 🔑 Éditez votre configuration:"
    echo "   nano config/config.json"
    echo "   (Ajoutez vos clés Binance + configuration Telegram)"
    echo ""
    echo "2. 📧 Configurez les emails pour Smart Monitor:"
    echo "   nano config/email_config.json"
    echo ""
    echo "3. 🧪 Testez le bot:"
    echo "   cd ${PROJECT_ROOT}"
    echo "   source venv/bin/activate"
    echo "   python3 run_bot.py --dry-run"
    echo ""
    echo "4. 📊 Testez le Smart Monitor v2.1.8:"
    echo "   python3 smart_monitor.py daily"
    echo ""
    echo "5. ⏰ Configurez l'automatisation (NOUVEAU cron v2.1.8):"
    echo "   crontab -e"
    echo "   # Ajoutez ces lignes:"
    echo "   */10 * * * * cd ${PROJECT_ROOT} && ${PROJECT_ROOT}/run_wrapper.sh"
    echo "   0 18 * * * cd ${PROJECT_ROOT} && python3 smart_monitor.py daily >> logs/monitor.log 2>&1"
    echo "   0 19 * * 0 cd ${PROJECT_ROOT} && python3 smart_monitor.py weekly >> logs/monitor.log 2>&1"
    echo ""
    echo -e "${BLUE}🆕 NOUVEAUTÉS v2.1.8:${NC}"
    echo -e "   📊 Smart Monitor hybride EMAIL + TELEGRAM"
    echo -e "   💎 Holdings vs Profits garantis"
    echo -e "   🔄 Timestamps adaptatifs"
    echo -e "   🚀 75% moins de code de monitoring"
    echo ""
    echo -e "${BLUE}📚 Documentation complète: README.md${NC}"
    echo -e "${BLUE}🐛 Support: GitHub Issues${NC}"
}

# MENU PRINCIPAL
echo "Choisissez le type d'installation:"
echo "1. 🚀 Installation complète v2.1.8 (recommandée)"
echo "2. 🔧 Installation basique (sans logrotate)"
echo "3. 📊 Système seulement (dépendances)"
echo "4. 🐍 Python seulement (environnement)"
echo ""
read -p "Votre choix (1-4): " choice

case $choice in
    1)
        echo -e "${GREEN}🚀 Installation complète v2.1.8 sélectionnée${NC}"
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
echo -e "${GREEN}🎯 Installation v2.1.8 terminée avec succès!${NC}"
echo -e "${BLUE}📊 Smart Monitor prêt pour rapports automatiques${NC}"
