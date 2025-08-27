#!/bin/bash
# Script de gestion du dashboard Enhanced Trading Bot

DASHBOARD_SCRIPT="dashboard_server.py"
DASHBOARD_PID_FILE="dashboard.pid"
LOG_FILE="logs/dashboard.log"

# Créer le dossier logs si nécessaire
mkdir -p logs

case "$1" in
    start)
        if [ -f "$DASHBOARD_PID_FILE" ] && kill -0 $(cat "$DASHBOARD_PID_FILE") 2>/dev/null; then
            echo "⚠️  Dashboard déjà en cours (PID: $(cat $DASHBOARD_PID_FILE))"
        else
            echo "🚀 Démarrage du dashboard..."
            source venv/bin/activate
            nohup python3 $DASHBOARD_SCRIPT > $LOG_FILE 2>&1 &
            PID=$!
            echo $PID > $DASHBOARD_PID_FILE
            sleep 2
            if kill -0 $PID 2>/dev/null; then
                echo "✅ Dashboard démarré (PID: $PID)"
                echo "🔗 Accessible sur: http://localhost:5000"
                echo "📋 Logs: tail -f $LOG_FILE"
            else
                echo "❌ Échec démarrage dashboard"
                rm -f $DASHBOARD_PID_FILE
            fi
        fi
        ;;
    stop)
        if [ -f "$DASHBOARD_PID_FILE" ]; then
            PID=$(cat $DASHBOARD_PID_FILE)
            echo "🛑 Arrêt du dashboard (PID: $PID)..."
            kill $PID 2>/dev/null
            rm -f $DASHBOARD_PID_FILE
            sleep 2
            if kill -0 $PID 2>/dev/null; then
                echo "⚠️  Arrêt forcé..."
                kill -9 $PID 2>/dev/null
            fi
            echo "✅ Dashboard arrêté"
        else
            echo "ℹ️  Dashboard déjà arrêté"
        fi
        ;;
    restart)
        $0 stop
        sleep 2
        $0 start
        ;;
    status)
        if [ -f "$DASHBOARD_PID_FILE" ] && kill -0 $(cat "$DASHBOARD_PID_FILE") 2>/dev/null; then
            PID=$(cat $DASHBOARD_PID_FILE)
            echo "✅ Dashboard en cours (PID: $PID)"
            echo "🔗 URL: http://localhost:5000"
            echo "📋 Logs: tail -f $LOG_FILE"
        else
            echo "❌ Dashboard arrêté"
            rm -f $DASHBOARD_PID_FILE 2>/dev/null
        fi
        ;;
    logs)
        if [ -f "$LOG_FILE" ]; then
            echo "📋 Logs du dashboard (Ctrl+C pour quitter):"
            tail -f $LOG_FILE
        else
            echo "❌ Fichier de logs non trouvé: $LOG_FILE"
        fi
        ;;
    *)
        echo "Usage: $0 {start|stop|restart|status|logs}"
        echo ""
        echo "Commandes:"
        echo "  start   - Démarre le dashboard en arrière-plan"
        echo "  stop    - Arrête le dashboard"
        echo "  restart - Redémarre le dashboard"
        echo "  status  - Affiche le statut du dashboard"
        echo "  logs    - Affiche les logs en temps réel"
        exit 1
        ;;
esac
