#!/bin/bash

# Enhanced Trading Bot - Monitoring et rapport quotidien
# Version finale sans erreur octal pour Raspberry Pi

cd /home/yotsi/enhanced_trading_bot

REPORT_FILE="logs/daily_report.log"
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')
TODAY=$(date '+%Y-%m-%d')

# Fonction pour nettoyer et valider les nombres
clean_number() {
    local input="$1"
    local cleaned=$(echo "$input" | grep -o '[0-9]*' | head -1)
    
    # Si vide ou invalide, retourner 0
    if [ -z "$cleaned" ] || [ "$cleaned" = "" ]; then
        echo "0"
    else
        echo "$cleaned"
    fi
}

# Fonction pour sécuriser les calculs arithmétiques
safe_calc() {
    local expr="$1"
    local result
    
    # Utiliser bc si disponible, sinon bash
    if command -v bc >/dev/null 2>&1; then
        result=$(echo "$expr" | bc 2>/dev/null)
    else
        # Fallback avec bash (attention aux nombres octaux)
        result=$((expr)) 2>/dev/null || result=0
    fi
    
    echo "${result:-0}"
}

# Fonction pour formater l'heure sans printf (éviter erreur octal)
format_time() {
    local hour="$1"
    local minute="$2"
    
    # S'assurer que les nombres sont en base 10
    local hour_num=$((10#$hour))
    local min_num=$((10#$minute))
    
    # Format manuel
    local hour_str minute_str
    if [ "$hour_num" -lt 10 ]; then
        hour_str="0${hour_num}"
    else
        hour_str="$hour_num"
    fi
    
    if [ "$min_num" -lt 10 ]; then
        minute_str="0${min_num}"
    else
        minute_str="$min_num"
    fi
    
    echo "${hour_str}:${minute_str}"
}

# Fonction pour générer le rapport
generate_report() {
    echo "📊 Génération du rapport quotidien..."
    
    cat > "$REPORT_FILE" << 'EOF'
🤖 === ENHANCED TRADING BOT - RAPPORT QUOTIDIEN ===
📅 Généré le: TIMESTAMP_PLACEHOLDER
🍓 Raspberry Pi Zero W2

📊 === STATISTIQUES D'EXÉCUTION ===
EOF

    # Remplacer le timestamp
    sed -i "s/TIMESTAMP_PLACEHOLDER/$TIMESTAMP/" "$REPORT_FILE"

    # STATISTIQUES COHÉRENTES - Version corrigée
    if [ -f "logs/cron.log" ]; then
        # Compter les débuts d'exécution (plus fiable)
        EXECUTIONS_RAW=$(grep "$TODAY" logs/cron.log 2>/dev/null | grep -c "=== DÉBUT EXECUTION CRON ===" || echo "0")
        EXECUTIONS_TODAY=$(clean_number "$EXECUTIONS_RAW")
        
        # Compter les fins d'exécution réussies
        SUCCESS_RAW=$(grep "$TODAY" logs/cron.log 2>/dev/null | grep -c "=== FIN EXECUTION CRON ===" || echo "0")
        SUCCESS_TODAY=$(clean_number "$SUCCESS_RAW")
        
        # Les erreurs = exécutions commencées mais pas terminées
        ERRORS_TODAY=$(safe_calc "$EXECUTIONS_TODAY - $SUCCESS_TODAY")
        
        # S'assurer que les erreurs ne sont jamais négatives
        if [ "$ERRORS_TODAY" -lt 0 ] 2>/dev/null; then
            ERRORS_TODAY=0
        fi
        
        # Ajouter les erreurs loggées séparément
        LOGGED_ERRORS_RAW=$(grep "$TODAY" logs/errors.log 2>/dev/null | wc -l || echo "0")
        LOGGED_ERRORS=$(clean_number "$LOGGED_ERRORS_RAW")
        TOTAL_ERRORS=$(safe_calc "$ERRORS_TODAY + $LOGGED_ERRORS")
        
        echo "   📈 Exécutions aujourd'hui: $EXECUTIONS_TODAY" >> "$REPORT_FILE"
        echo "   ✅ Succès: $SUCCESS_TODAY" >> "$REPORT_FILE"
        echo "   ❌ Erreurs: $TOTAL_ERRORS" >> "$REPORT_FILE"
        
        # Taux de succès mathématiquement correct
        if [ "$EXECUTIONS_TODAY" -gt 0 ] 2>/dev/null; then
            SUCCESS_RATE=$(safe_calc "$SUCCESS_TODAY * 100 / $EXECUTIONS_TODAY")
            # Cap à 100% pour éviter les erreurs d'arrondi
            if [ "$SUCCESS_RATE" -gt 100 ] 2>/dev/null; then
                SUCCESS_RATE=100
            fi
            echo "   📊 Taux de succès: ${SUCCESS_RATE}%" >> "$REPORT_FILE"
        else
            echo "   📊 Taux de succès: N/A" >> "$REPORT_FILE"
        fi
        
        # Dernière exécution
        LAST_EXEC=$(grep "$TODAY" logs/cron.log 2>/dev/null | grep "=== DÉBUT EXECUTION CRON ===" | tail -1 | grep -o '\[.*\]' | tr -d '[]' | head -1)
        if [ -n "$LAST_EXEC" ] && [ "$LAST_EXEC" != "" ]; then
            echo "   🕐 Dernière exécution: $LAST_EXEC" >> "$REPORT_FILE"
        else
            echo "   🕐 Dernière exécution: Aucune trouvée aujourd'hui" >> "$REPORT_FILE"
        fi
        
        # Durée moyenne des exécutions (bonus)
        AVG_DURATION=$(grep "$TODAY" logs/cron.log 2>/dev/null | grep "✅ Bot terminé avec succès" | grep -o '([0-9]*s)' | tr -d '()s' | awk '{sum+=$1; n++} END {if(n>0) printf "%.0f", sum/n; else print "0"}')
        if [ "$AVG_DURATION" -gt 0 ] 2>/dev/null; then
            echo "   ⏱️  Durée moyenne: ${AVG_DURATION}s" >> "$REPORT_FILE"
        fi
        
    else
        echo "   ⚠️  Aucun log cron.log trouvé" >> "$REPORT_FILE"
    fi

    echo "" >> "$REPORT_FILE"
    echo "📋 === ACTIVITÉ DE TRADING ===" >> "$REPORT_FILE"
    
    # Analyser l'activité de trading - patterns corrigés
    ACHATS_TODAY=0
    OCO_TODAY=0
    VENTES_TODAY=0
    
    # Chercher dans tous les fichiers de logs
    for log_file in logs/trading_bot.log logs/cron.log logs/debug.log; do
        if [ -f "$log_file" ]; then
            # Compter les achats (patterns multiples)
            ACHATS_FILE=$(grep "$TODAY" "$log_file" 2>/dev/null | grep -cE "💰 ACHAT RÉEL|🧪 SIMULATION ACHAT|✅.*Achat.*exécuté" || echo "0")
            ACHATS_TODAY=$(safe_calc "$ACHATS_TODAY + $(clean_number "$ACHATS_FILE")")
            
            # Compter les OCO
            OCO_FILE=$(grep "$TODAY" "$log_file" 2>/dev/null | grep -cE "✅ ORDRE OCO PLACÉ|🧪 Ordre OCO simulé" || echo "0")
            OCO_TODAY=$(safe_calc "$OCO_TODAY + $(clean_number "$OCO_FILE")")
            
            # Compter les ordres de vente
            VENTES_FILE=$(grep "$TODAY" "$log_file" 2>/dev/null | grep -cE "✅ Ordre.*placé|✅.*ORDRE.*PLACÉ" || echo "0")
            VENTES_TODAY=$(safe_calc "$VENTES_TODAY + $(clean_number "$VENTES_FILE")")
        fi
    done
    
    echo "   💰 Achats exécutés: $ACHATS_TODAY" >> "$REPORT_FILE"
    echo "   📈 Ordres de vente placés: $VENTES_TODAY" >> "$REPORT_FILE"
    echo "   🎯 Ordres OCO (avec stop-loss): $OCO_TODAY" >> "$REPORT_FILE"
    
    # Cryptos tradées - version sécurisée
    if [ "$ACHATS_TODAY" -gt 0 ] 2>/dev/null; then
        echo "   🪙 Cryptos tradées:" >> "$REPORT_FILE"
        
        # Extraire les symboles depuis les logs (multiple sources)
        CRYPTO_LIST=""
        for log_file in logs/trading_bot.log logs/cron.log logs/debug.log; do
            if [ -f "$log_file" ]; then
                FILE_CRYPTOS=$(grep "$TODAY" "$log_file" 2>/dev/null | grep -E "💰 ACHAT RÉEL|🧪 SIMULATION ACHAT|=== ANALYSE" | grep -oE '[A-Z]{2,6}USDC|[A-Z]{2,6} \(' | sed -E 's/USDC|[[:space:]]*\(//g' | sort | uniq)
                if [ -n "$FILE_CRYPTOS" ]; then
                    CRYPTO_LIST="${CRYPTO_LIST}${FILE_CRYPTOS}"$'\n'
                fi
            fi
        done
        
        if [ -n "$CRYPTO_LIST" ]; then
            echo "$CRYPTO_LIST" | sort | uniq | while read -r crypto; do
                if [ -n "$crypto" ] && [ "$crypto" != "" ]; then
                    echo "   • $crypto" >> "$REPORT_FILE"
                fi
            done
        else
            echo "   • $ACHATS_TODAY achat(s) détecté(s)" >> "$REPORT_FILE"
        fi
    fi
    
    # Erreurs de trading
    TRADING_ERRORS=0
    for log_file in logs/trading_bot.log logs/cron.log logs/errors.log; do
        if [ -f "$log_file" ]; then
            ERRORS_FILE=$(grep "$TODAY" "$log_file" 2>/dev/null | grep -cE "❌.*Erreur|ERROR.*trading|Échec.*achat|❌.*Échec" || echo "0")
            TRADING_ERRORS=$(safe_calc "$TRADING_ERRORS + $(clean_number "$ERRORS_FILE")")
        fi
    done
    
    if [ "$TRADING_ERRORS" -gt 0 ] 2>/dev/null; then
        echo "   ⚠️  Erreurs de trading: $TRADING_ERRORS" >> "$REPORT_FILE"
    fi
    
    # Positions actives (estimation depuis les logs)
    POSITIONS_MENTIONS=$(grep "$TODAY" logs/cron.log 2>/dev/null | grep -c "positions.*actives\|📊 Total.*positions" | tail -1)
    if [ "$POSITIONS_MENTIONS" -gt 0 ] 2>/dev/null; then
        LAST_POSITIONS=$(grep "$TODAY" logs/cron.log 2>/dev/null | grep "📊 Total.*positions" | tail -1 | grep -o '[0-9]* positions' | head -1)
        if [ -n "$LAST_POSITIONS" ]; then
            echo "   📊 Positions actives: $LAST_POSITIONS (dernière mesure)" >> "$REPORT_FILE"
        fi
    fi

    echo "" >> "$REPORT_FILE"
    echo "🚨 === ERREURS RÉCENTES ===" >> "$REPORT_FILE"
    
    if [ -f "logs/errors.log" ] && [ -s "logs/errors.log" ]; then
        echo "   📋 5 dernières erreurs:" >> "$REPORT_FILE"
        tail -5 logs/errors.log 2>/dev/null | while IFS= read -r line; do
            if [ -n "$line" ]; then
                # Raccourcir les lignes trop longues
                if [ ${#line} -gt 120 ]; then
                    short_line="${line:0:117}..."
                else
                    short_line="$line"
                fi
                echo "   • $short_line" >> "$REPORT_FILE"
            fi
        done
    else
        echo "   ✅ Aucune erreur récente dans errors.log" >> "$REPORT_FILE"
    fi

    echo "" >> "$REPORT_FILE"
    echo "🍓 === SYSTÈME RASPBERRY PI ===" >> "$REPORT_FILE"
    
    # Température CPU - gestion sécurisée
    if [ -f "/sys/class/thermal/thermal_zone0/temp" ]; then
        TEMP_RAW=$(cat /sys/class/thermal/thermal_zone0/temp 2>/dev/null || echo "50000")
        TEMP=$(clean_number "$TEMP_RAW")
        TEMP_C=$(safe_calc "$TEMP / 1000")
        echo "   🌡️  Température CPU: ${TEMP_C}°C" >> "$REPORT_FILE"
        
        if [ "$TEMP_C" -gt 75 ] 2>/dev/null; then
            echo "   ⚠️  ATTENTION: Température élevée!" >> "$REPORT_FILE"
        elif [ "$TEMP_C" -gt 65 ] 2>/dev/null; then
            echo "   ⚠️  Température surveillée (>65°C)" >> "$REPORT_FILE"
        fi
    else
        echo "   🌡️  Température CPU: Non disponible" >> "$REPORT_FILE"
    fi
    
    # Charge système
    if [ -f "/proc/loadavg" ]; then
        LOAD=$(cat /proc/loadavg 2>/dev/null | cut -d' ' -f1-3 || echo "0.00 0.00 0.00")
        echo "   📊 Charge système: $LOAD" >> "$REPORT_FILE"
        
        # Alerte si charge élevée
        LOAD_1MIN=$(echo "$LOAD" | cut -d' ' -f1)
        if [ "$(echo "$LOAD_1MIN > 1.5" | bc -l 2>/dev/null || echo 0)" = "1" ]; then
            echo "   ⚠️  ATTENTION: Charge système élevée!" >> "$REPORT_FILE"
        fi
    fi
    
    # Espace disque - éviter les nombres octaux
    DISK_USAGE_RAW=$(df -h / 2>/dev/null | awk 'NR==2 {print $5}' | tr -d '%' || echo "0")
    DISK_USAGE=$(clean_number "$DISK_USAGE_RAW")
    echo "   💾 Utilisation disque: ${DISK_USAGE}%" >> "$REPORT_FILE"
    
    if [ "$DISK_USAGE" -gt 90 ] 2>/dev/null; then
        echo "   🚨 CRITIQUE: Espace disque très faible!" >> "$REPORT_FILE"
    elif [ "$DISK_USAGE" -gt 85 ] 2>/dev/null; then
        echo "   ⚠️  ATTENTION: Espace disque faible!" >> "$REPORT_FILE"
    fi
    
    # Mémoire - calcul sécurisé
    if [ -f "/proc/meminfo" ]; then
        TOTAL_MEM_RAW=$(grep MemTotal /proc/meminfo 2>/dev/null | awk '{print $2}' || echo "1000000")
        TOTAL_MEM=$(clean_number "$TOTAL_MEM_RAW")
        
        AVAIL_MEM_RAW=$(grep MemAvailable /proc/meminfo 2>/dev/null | awk '{print $2}' || echo "700000")
        AVAIL_MEM=$(clean_number "$AVAIL_MEM_RAW")
        
        if [ "$TOTAL_MEM" -gt 0 ] 2>/dev/null; then
            MEM_USAGE=$(safe_calc "100 - ($AVAIL_MEM * 100 / $TOTAL_MEM)")
        else
            MEM_USAGE=0
        fi
        echo "   🧠 Utilisation mémoire: ${MEM_USAGE}%" >> "$REPORT_FILE"
        
        if [ "$MEM_USAGE" -gt 90 ] 2>/dev/null; then
            echo "   ⚠️  ATTENTION: Mémoire faible!" >> "$REPORT_FILE"
        fi
    fi
    
    # Uptime
    UPTIME=$(uptime -p 2>/dev/null | sed 's/up //' || echo "Non disponible")
    echo "   ⏰ Uptime système: $UPTIME" >> "$REPORT_FILE"

    echo "" >> "$REPORT_FILE"
    echo "⏰ === PLANIFICATION CRON ===" >> "$REPORT_FILE"
    
    # Vérifier cron - version détaillée
    if command -v crontab >/dev/null 2>&1; then
        BOT_CRON_RAW=$(crontab -l 2>/dev/null | grep -c "run_wrapper.sh" || echo "0")
        BOT_CRON=$(clean_number "$BOT_CRON_RAW")
        
        MONITOR_CRON_RAW=$(crontab -l 2>/dev/null | grep -c "monitor.sh" || echo "0")
        MONITOR_CRON=$(clean_number "$MONITOR_CRON_RAW")
        
        if [ "$BOT_CRON" -gt 0 ] 2>/dev/null; then
            echo "   ✅ Cron trading actif: $BOT_CRON tâche(s)" >> "$REPORT_FILE"
            
            # Extraire la fréquence
            FREQUENCY=$(crontab -l 2>/dev/null | grep "run_wrapper.sh" | head -1 | cut -d' ' -f1-2)
            if [ "$FREQUENCY" = "*/10 *" ]; then
                echo "   🔄 Fréquence: Toutes les 10 minutes" >> "$REPORT_FILE"
            else
                echo "   🔄 Fréquence: $FREQUENCY" >> "$REPORT_FILE"
            fi
        else
            echo "   ❌ ATTENTION: Cron trading non configuré!" >> "$REPORT_FILE"
        fi
        
        if [ "$MONITOR_CRON" -gt 0 ] 2>/dev/null; then
            echo "   📊 Cron monitoring actif: $MONITOR_CRON tâche(s)" >> "$REPORT_FILE"
        else
            echo "   ⚠️  Cron monitoring non configuré" >> "$REPORT_FILE"
        fi
        
        # Prochaine exécution - SANS printf pour éviter erreur octal
        CURRENT_HOUR=$(date +"%H")
        CURRENT_MINUTE=$(date +"%M")
        
        # Convertir en base 10 pour éviter erreur octal
        CURRENT_HOUR_NUM=$((10#$CURRENT_HOUR))
        CURRENT_MINUTE_NUM=$((10#$CURRENT_MINUTE))
        
        # Calcul de la prochaine exécution (multiple de 10 minutes)
        NEXT_EXEC_MIN=$(safe_calc "($CURRENT_MINUTE_NUM / 10 + 1) * 10")
        NEXT_HOUR_NUM=$CURRENT_HOUR_NUM
        
        if [ "$NEXT_EXEC_MIN" -ge 60 ] 2>/dev/null; then
            NEXT_EXEC_MIN=0
            NEXT_HOUR_NUM=$(safe_calc "$CURRENT_HOUR_NUM + 1")
            if [ "$NEXT_HOUR_NUM" -ge 24 ] 2>/dev/null; then
                NEXT_HOUR_NUM=0
            fi
        fi
        
        # Format avec fonction personnalisée (pas de printf)
        NEXT_TIME=$(format_time "$NEXT_HOUR_NUM" "$NEXT_EXEC_MIN")
        echo "   🎯 Prochaine exécution estimée: $NEXT_TIME" >> "$REPORT_FILE"
    else
        echo "   ❌ CRITIQUE: Cron non disponible!" >> "$REPORT_FILE"
    fi

    echo "" >> "$REPORT_FILE"
    echo "🔧 === DIAGNOSTIC RAPIDE ===" >> "$REPORT_FILE"
    
    # Vérifications de base avec détails
    if [ -f "run_bot.py" ]; then
        BOT_SIZE=$(ls -lh run_bot.py 2>/dev/null | awk '{print $5}' || echo "?")
        echo "   ✅ Script principal: OK ($BOT_SIZE)" >> "$REPORT_FILE"
    else
        echo "   ❌ Script principal: MANQUANT" >> "$REPORT_FILE"
    fi
    
    if [ -f "config/config.json" ]; then
        CONFIG_SIZE=$(ls -lh config/config.json 2>/dev/null | awk '{print $5}' || echo "?")
        echo "   ✅ Configuration: OK ($CONFIG_SIZE)" >> "$REPORT_FILE"
    else
        echo "   ❌ Configuration: MANQUANTE" >> "$REPORT_FILE"
    fi
    
    if [ -d "venv" ]; then
        VENV_COUNT=$(find venv -name "*.py" 2>/dev/null | wc -l || echo "0")
        echo "   ✅ Environnement virtuel: OK ($VENV_COUNT fichiers Python)" >> "$REPORT_FILE"
    else
        echo "   ❌ Environnement virtuel: MANQUANT" >> "$REPORT_FILE"
    fi
    
    # Test de base très rapide
    if [ -f "config/config.json" ] && [ -d "venv" ]; then
        echo "   🧪 Test rapide..." >> "$REPORT_FILE"
        
        # Test JSON et modules critiques
        TEST_RESULT=$(timeout 10 bash -c '
            source venv/bin/activate 2>/dev/null
            python3 -c "
import json, sys
try:
    with open(\"config/config.json\") as f:
        config = json.load(f)
    cryptos = len([k for k,v in config.get(\"cryptos\", {}).items() if v.get(\"active\", False)])
    print(f\"Config OK - {cryptos} cryptos actives\")
except Exception as e:
    print(f\"Erreur: {e}\")
    sys.exit(1)
" 2>/dev/null
        ' 2>/dev/null)
        
        if [ $? -eq 0 ] && [ -n "$TEST_RESULT" ]; then
            echo "   ✅ Test: $TEST_RESULT" >> "$REPORT_FILE"
        else
            echo "   ⚠️  Test: Problème détecté (timeout ou erreur)" >> "$REPORT_FILE"
        fi
    fi
    
    # Statistique des fichiers de log
    LOG_COUNT=$(find logs/ -name "*.log" -type f 2>/dev/null | wc -l || echo "0")
    LOG_SIZE=$(du -sh logs/ 2>/dev/null | cut -f1 || echo "?")
    echo "   📁 Logs: $LOG_COUNT fichiers ($LOG_SIZE total)" >> "$REPORT_FILE"

    echo "" >> "$REPORT_FILE"
    echo "=== FIN DU RAPPORT ===" >> "$REPORT_FILE"
    
    echo "✅ Rapport généré avec succès dans $REPORT_FILE"
}

# === EXÉCUTION PRINCIPALE ===

# Créer le répertoire logs si inexistant
mkdir -p logs

# Créer errors.log s'il n'existe pas
touch logs/errors.log

# Générer le rapport
generate_report

# Logger l'événement dans cron.log
echo "[$(date '+%Y-%m-%d %H:%M:%S')] 📊 Rapport quotidien généré - Taille: $(ls -lh "$REPORT_FILE" 2>/dev/null | awk '{print $5}' || echo '?')" >> logs/cron.log

# Rotation des logs - nettoyage sécurisé
DELETED_FILES=$(find logs/ -name "*.log" -type f -mtime +15 2>/dev/null | wc -l)
find logs/ -name "*.log" -type f -mtime +15 -delete 2>/dev/null || true

if [ "$DELETED_FILES" -gt 0 ] 2>/dev/null; then
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] 🧹 Rotation logs: $DELETED_FILES fichiers supprimés" >> logs/cron.log
fi

# Message final avec statistique
echo "📊 Rapport quotidien sauvegardé dans $REPORT_FILE ($(ls -lh "$REPORT_FILE" 2>/dev/null | awk '{print $5}' || echo '? octets'))"
