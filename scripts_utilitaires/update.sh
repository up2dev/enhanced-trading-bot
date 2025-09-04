#!/bin/bash

# 🔄 Enhanced Trading Bot - Script de mise à jour v2.1.8
# Script déplacé dans scripts_utilitaires/ - Chemins corrigés

set -e

# Couleurs
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}🔄 === MISE À JOUR TRADING BOT ===${NC}"
echo ""

# 🔧 CORRECTION: Détection chemin racine du projet
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"  # Remonte d'un niveau
CURRENT_USER=$(whoami)

echo -e "${BLUE}📍 Script dans: ${SCRIPT_DIR}${NC}"
echo -e "${BLUE}📍 Projet dans: ${PROJECT_ROOT}${NC}"
echo ""

# Vérification que nous sommes dans le bon projet
if [ ! -f "${PROJECT_ROOT}/run_bot.py" ] || [ ! -d "${PROJECT_ROOT}/src" ]; then
    echo -e "${RED}❌ Erreur: Structure de projet non trouvée${NC}"
    echo -e "${RED}   run_bot.py et dossier src/ doivent être à la racine${NC}"
    exit 1
fi

# 🔧 CORRECTION: Toutes les opérations dans PROJECT_ROOT
cd "$PROJECT_ROOT"
echo -e "${GREEN}✅ Position corrigée vers racine du projet${NC}"

# Détection version actuelle
CURRENT_VERSION=""
if git describe --tags --exact-match 2>/dev/null; then
    CURRENT_VERSION=$(git describe --tags --exact-match)
    echo -e "${BLUE}📌 Version actuelle: ${CURRENT_VERSION}${NC}"
else
    echo -e "${YELLOW}📌 Version: commit $(git rev-parse --short HEAD)${NC}"
fi

# Vérification des changements locaux
if ! git diff-index --quiet HEAD --; then
    echo -e "${YELLOW}⚠️  Changements locaux détectés${NC}"
    git status --short
    echo ""
fi

# 💾 SAUVEGARDES ÉLARGIES (dans PROJECT_ROOT)
echo -e "${YELLOW}💾 Sauvegarde des données critiques...${NC}"

# Configuration principale
if [ -f "config/config.json" ]; then
    cp config/config.json "config/config.json.backup.$(date +%Y%m%d_%H%M)"
    echo "✅ config.json sauvegardé"
fi

# Configuration email Smart Monitor
if [ -f "config/email_config.json" ]; then
    cp config/email_config.json "config/email_config.json.backup.$(date +%Y%m%d_%H%M)"
    echo "✅ email_config.json sauvegardé"
fi

# Base de données
if [ -f "db/trading.db" ]; then
    BACKUP_DB="db/trading_backup_$(date +%Y%m%d_%H%M).db"
    cp db/trading.db "$BACKUP_DB"
    echo "✅ Base de données sauvegardée: $BACKUP_DB"
fi

# Logs importants (derniers 7 jours)
if [ -d "logs" ]; then
    BACKUP_LOGS="logs_backup_$(date +%Y%m%d_%H%M)"
    mkdir -p "$BACKUP_LOGS"
    find logs/ -name "*.log" -mtime -7 -exec cp {} "$BACKUP_LOGS/" \; 2>/dev/null || true
    if [ "$(ls -A "$BACKUP_LOGS" 2>/dev/null)" ]; then
        echo "✅ Logs récents sauvegardés: $BACKUP_LOGS"
    else
        rm -rf "$BACKUP_LOGS"
    fi
fi

# 📥 MISE À JOUR GIT
echo -e "${YELLOW}📥 Récupération des mises à jour...${NC}"

# Stash des changements locaux
if ! git diff-index --quiet HEAD --; then
    git stash push -m "Sauvegarde locale avant mise à jour $(date +%Y%m%d_%H%M)"
    echo "✅ Changements locaux mis de côté"
fi

# Récupération des tags
git fetch --tags

# Mise à jour
echo "🔄 Mise à jour du code..."
if git pull origin main; then
    echo -e "${GREEN}✅ Code mis à jour avec succès${NC}"
else
    echo -e "${RED}❌ Erreur lors de la mise à jour Git${NC}"
    exit 1
fi

# Affichage de la nouvelle version
NEW_VERSION=""
if git describe --tags --exact-match 2>/dev/null; then
    NEW_VERSION=$(git describe --tags --exact-match)
    echo -e "${GREEN}🆕 Nouvelle version: ${NEW_VERSION}${NC}"
else
    echo -e "${BLUE}🆕 Version: commit $(git rev-parse --short HEAD)${NC}"
fi

# 📦 MISE À JOUR DÉPENDANCES
echo -e "${YELLOW}📦 Mise à jour des dépendances Python...${NC}"

if [ ! -d "venv" ]; then
    echo -e "${YELLOW}🔧 Création de l'environnement virtuel manquant...${NC}"
    python3 -m venv venv
fi

source venv/bin/activate

if [ -f "requirements.txt" ]; then
    pip install --upgrade pip
    pip install --upgrade -r requirements.txt
    echo -e "${GREEN}✅ Dépendances mises à jour${NC}"
else
    echo -e "${RED}❌ requirements.txt non trouvé${NC}"
fi

# 🔧 RESTAURATION CONFIGURATIONS
echo -e "${YELLOW}🔧 Vérification des configurations...${NC}"

# Restaurer config principale si disparue
if [ ! -f "config/config.json" ]; then
    LATEST_BACKUP=$(ls -t config/config.json.backup.* 2>/dev/null | head -1 || echo "")
    if [ -n "$LATEST_BACKUP" ] && [ -f "$LATEST_BACKUP" ]; then
        cp "$LATEST_BACKUP" config/config.json
        echo -e "${GREEN}✅ Configuration principale restaurée depuis $LATEST_BACKUP${NC}"
    elif [ -f "config/config.template.json" ]; then
        cp config/config.template.json config/config.json
        echo -e "${YELLOW}⚠️  Configuration créée depuis template - CONFIGUREZ VOS CLÉS API${NC}"
    fi
fi

# Restaurer config email si disparue
if [ ! -f "config/email_config.json" ] && [ -f "config/email_config.template.json" ]; then
    cp config/email_config.template.json config/email_config.json
    echo -e "${YELLOW}📧 Configuration email créée depuis template${NC}"
fi

# 🔑 PERMISSIONS (PROJECT_ROOT + scripts_utilitaires)
echo -e "${YELLOW}🔑 Mise à jour des permissions...${NC}"
chmod +x *.py *.sh scripts_utilitaires/*.py scripts_utilitaires/*.sh 2>/dev/null || true
chmod 755 logs db config 2>/dev/null || true

# 🧪 TESTS POST-MISE À JOUR
echo -e "${YELLOW}🧪 Tests de validation...${NC}"

# Test modules principaux
if python3 -c "
import sys
sys.path.insert(0, '.')
try:
    from src.bot import EnhancedTradingBot
    from src.binance_client import EnhancedBinanceClient
    print('✅ Modules principaux OK')
except Exception as e:
    print(f'❌ Erreur modules: {e}')
    sys.exit(1)
" 2>/dev/null; then
    echo -e "${GREEN}✅ Modules principaux validés${NC}"
else
    echo -e "${RED}❌ Erreur validation modules${NC}"
fi

# Test Smart Monitor v2.1.8
if [ -f "smart_monitor.py" ]; then
    if python3 -c "
try:
    exec(open('smart_monitor.py').read())
    print('✅ Smart Monitor OK')
except SystemExit:
    print('✅ Smart Monitor OK (exit normal)')
except Exception as e:
    print(f'⚠️  Smart Monitor: {e}')
" 2>/dev/null; then
        echo -e "${GREEN}✅ Smart Monitor v2.1.8 validé${NC}"
    else
        echo -e "${YELLOW}⚠️  Smart Monitor nécessite configuration${NC}"
    fi
else
    echo -e "${YELLOW}⚠️  Smart Monitor non trouvé (version < 2.1.8 ?)${NC}"
fi

# 📋 MIGRATION v2.1.8
echo -e "${YELLOW}🔄 Vérification migration v2.1.8...${NC}"

# Détecter anciens scripts de monitoring obsolètes
OBSOLETE_SCRIPTS=()
[ -f "monitor.sh" ] && OBSOLETE_SCRIPTS+=("monitor.sh")
[ -f "email_sender.py" ] && OBSOLETE_SCRIPTS+=("email_sender.py")  
[ -f "performance_stats.py" ] && OBSOLETE_SCRIPTS+=("performance_stats.py")

if [ ${#OBSOLETE_SCRIPTS[@]} -gt 0 ]; then
    echo -e "${YELLOW}📦 Scripts obsolètes détectés (remplacés par Smart Monitor):${NC}"
    for script in "${OBSOLETE_SCRIPTS[@]}"; do
        echo "   - $script"
    done
    
    read -p "Voulez-vous les sauvegarder et les supprimer ? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        OBSOLETE_BACKUP="backup_obsolete_scripts_$(date +%Y%m%d_%H%M)"
        mkdir -p "$OBSOLETE_BACKUP"
        
        for script in "${OBSOLETE_SCRIPTS[@]}"; do
            mv "$script" "$OBSOLETE_BACKUP/"
            echo "✅ $script → $OBSOLETE_BACKUP/"
        done
        
        echo -e "${GREEN}✅ Scripts obsolètes sauvegardés dans $OBSOLETE_BACKUP${NC}"
        echo -e "${BLUE}📊 Utilisez maintenant: python3 smart_monitor.py daily|weekly${NC}"
    fi
fi

# 📊 RÉSUMÉ FINAL
echo ""
echo -e "${GREEN}🎉 === MISE À JOUR TERMINÉE AVEC SUCCÈS ===${NC}"
echo ""

if [ -n "$CURRENT_VERSION" ] && [ -n "$NEW_VERSION" ] && [ "$CURRENT_VERSION" != "$NEW_VERSION" ]; then
    echo -e "${BLUE}📌 $CURRENT_VERSION → $NEW_VERSION${NC}"
    echo ""
fi

echo -e "${BLUE}🧪 TESTS RECOMMANDÉS:${NC}"
echo "1. Test configuration:"
echo "   cd ${PROJECT_ROOT}"
echo "   source venv/bin/activate"
echo "   python3 run_bot.py --dry-run"
echo ""
echo "2. Test Smart Monitor v2.1.8:"
echo "   python3 smart_monitor.py daily"
echo ""
echo "3. Vérifier base de données:"
echo "   python3 db_query.py --stats"
echo ""

if [ -f "smart_monitor.py" ]; then
    echo -e "${BLUE}📊 NOUVEAU CRONTAB RECOMMANDÉ (v2.1.8):${NC}"
    echo "   crontab -e"
    echo "   # Remplacer par:"
    echo "   */10 * * * * cd ${PROJECT_ROOT} && ${PROJECT_ROOT}/run_wrapper.sh"
    echo "   0 18 * * * cd ${PROJECT_ROOT} && python3 smart_monitor.py daily >> logs/monitor.log 2>&1"
    echo "   0 19 * * 0 cd ${PROJECT_ROOT} && python3 smart_monitor.py weekly >> logs/monitor.log 2>&1"
    echo ""
fi

echo -e "${BLUE}💾 Sauvegardes disponibles:${NC}"
ls -la config/*.backup.* db/trading_backup_* logs_backup_* 2>/dev/null | tail -5 || echo "   (aucune sauvegarde ancienne)"

echo ""
echo -e "${GREEN}🚀 Bot prêt à être relancé !${NC}"
echo -e "${BLUE}📍 Exécuté depuis: ${SCRIPT_DIR}${NC}"
echo -e "${BLUE}📍 Projet mis à jour: ${PROJECT_ROOT}${NC}"

deactivate 2>/dev/null || true
