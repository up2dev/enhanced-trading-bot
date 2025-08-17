#!/bin/bash

# Script wrapper pour le trading bot
SCRIPT_DIR="/home/yotsi/enhanced_trading_bot"
VENV_PATH="$SCRIPT_DIR/venv/bin/python"
LOG_FILE="$SCRIPT_DIR/logs/cron.log"

# Fonction de logging
log_message() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" >> "$LOG_FILE"
}

# Vérifications préalables
log_message "=== DÉBUT EXECUTION CRON ==="

# Vérifier que le dossier existe
if [ ! -d "$SCRIPT_DIR" ]; then
    log_message "❌ ERREUR: Dossier non trouvé: $SCRIPT_DIR"
    exit 1
fi

# Vérifier que l'environnement virtuel existe
if [ ! -f "$VENV_PATH" ]; then
    log_message "❌ ERREUR: Environnement virtuel non trouvé: $VENV_PATH"
    exit 1
fi

# Vérifier la connexion internet
if ! ping -c 1 8.8.8.8 &> /dev/null; then
    log_message "❌ ERREUR: Pas de connexion internet"
    exit 1
fi

# Aller dans le bon dossier
cd "$SCRIPT_DIR" || {
    log_message "❌ ERREUR: Impossible d'accéder au dossier $SCRIPT_DIR"
    exit 1
}

# Vérifier la température du CPU (optionnel)
if [ -f "/sys/class/thermal/thermal_zone0/temp" ]; then
    TEMP=$(cat /sys/class/thermal/thermal_zone0/temp | head -c 2)
    if [ "$TEMP" -gt 80 ]; then
        log_message "⚠️  ATTENTION: Température CPU élevée: ${TEMP}°C"
    fi
fi

# Exécuter le bot
log_message "🚀 Lancement du trading bot..."
START_TIME=$(date +%s)

"$VENV_PATH" run_bot.py >> "$LOG_FILE" 2>&1
EXIT_CODE=$?

END_TIME=$(date +%s)
DURATION=$((END_TIME - START_TIME))

if [ $EXIT_CODE -eq 0 ]; then
    log_message "✅ Bot terminé avec succès (${DURATION}s)"
else
    log_message "❌ Bot terminé avec erreur (code: $EXIT_CODE, durée: ${DURATION}s)"
fi

log_message "=== FIN EXECUTION CRON ==="
log_message ""

