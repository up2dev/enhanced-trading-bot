#!/usr/bin/env python3
"""
Enhanced Trading Bot - Version Raspberry Pi
Exécution optimisée pour Raspberry Pi Zero W2
"""

import sys
import os
import argparse
import signal
import logging
from pathlib import Path
from datetime import datetime, timedelta
import time

# Configuration du path
sys.path.insert(0, str(Path(__file__).parent))

from src.bot import EnhancedTradingBot
from src.utils import setup_logging, validate_config, load_json_config, ensure_directories

# Variables globales pour l'arrêt propre
graceful_shutdown = False
bot_instance = None

def signal_handler(signum, frame):
    """Gestionnaire de signal pour arrêt propre"""
    global graceful_shutdown
    logging.getLogger(__name__).info(f"🛑 Signal {signum} reçu, arrêt en cours...")
    graceful_shutdown = True

def parse_arguments():
    """Parse les arguments de ligne de commande"""
    parser = argparse.ArgumentParser(description='Enhanced Trading Bot')
    parser.add_argument('--dry-run', action='store_true', 
                       help='Mode simulation - aucun ordre réel ne sera passé')
    parser.add_argument('--log-level', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'], 
                       default='INFO', help='Niveau de logging')
    parser.add_argument('--config', type=str, default='config/config.json',
                       help='Chemin vers le fichier de configuration')
    return parser.parse_args()

def check_system_resources():
    """Vérifie les ressources système pour Raspberry Pi"""
    try:
        # Vérifier l'espace disque
        import shutil
        total, used, free = shutil.disk_usage('/')
        free_gb = free // (1024**3)
        
        if free_gb < 1:
            logging.getLogger(__name__).warning(f"⚠️  Espace disque faible: {free_gb} GB libre")
        
        # Vérifier la mémoire si psutil disponible
        try:
            import psutil
            memory = psutil.virtual_memory()
            if memory.percent > 85:
                logging.getLogger(__name__).warning(f"⚠️  Mémoire élevée: {memory.percent:.1f}%")
        except ImportError:
            pass
            
        # Température si disponible
        try:
            with open('/sys/class/thermal/thermal_zone0/temp', 'r') as f:
                temp = int(f.read()) / 1000.0
                if temp > 70:
                    logging.getLogger(__name__).warning(f"⚠️  Température élevée: {temp:.1f}°C")
        except:
            pass
            
    except Exception as e:
        logging.getLogger(__name__).debug(f"Vérification ressources échouée: {e}")

def cleanup_old_logs():
    """Nettoyage automatique des anciens logs"""
    try:
        log_dir = Path("logs")
        if not log_dir.exists():
            return
            
        # Supprimer les logs de plus de 15 jours
        cutoff = datetime.now() - timedelta(days=15)
        
        for log_file in log_dir.glob("*.log.*"):
            try:
                if log_file.stat().st_mtime < cutoff.timestamp():
                    log_file.unlink()
                    logging.getLogger(__name__).info(f"🗑️  Log supprimé: {log_file.name}")
            except Exception:
                pass
                
    except Exception as e:
        logging.getLogger(__name__).debug(f"Nettoyage logs échoué: {e}")

def main():
    """Fonction principale optimisée Raspberry Pi"""
    global graceful_shutdown, bot_instance
    
    try:
        # Parse des arguments
        args = parse_arguments()
        
        # Configuration des signaux
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        # Assurance que les répertoires existent
        ensure_directories()
        
        # Configuration du logging avec rotation
        setup_logging(args.log_level, "logs")
        
        logger = logging.getLogger(__name__)
        
        # Bannière de démarrage
        mode_indicator = "🧪 SIMULATION" if args.dry_run else "🔥 RÉEL"
        
        logger.info("=" * 60)
        logger.info(f"🤖 ENHANCED TRADING BOT - {mode_indicator}")
        logger.info(f"🍓 Raspberry Pi Zero W2 Edition")
        logger.info(f"🕐 Démarrage: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info("=" * 60)
        
        if args.dry_run:
            logger.warning("⚠️  MODE DRY-RUN ACTIVÉ - Aucun ordre réel ne sera passé")
        else:
            logger.warning("🚨 MODE TRADING RÉEL - Les ordres seront exécutés sur Binance !")
        
        # Vérifications système
        check_system_resources()
        cleanup_old_logs()
        
        # Chargement de la configuration
        config_path = Path(args.config)
        logger.info(f"📋 Chargement configuration: {config_path}")
        
        if not config_path.exists():
            logger.error(f"❌ Fichier config introuvable: {config_path}")
            logger.info("💡 Copiez config.template.json vers config.json et configurez vos clés API")
            sys.exit(1)
        
        config = load_json_config(str(config_path))
        validate_config(config)
        
        logger.info("✅ Configuration validée")
        
        # Initialisation du bot
        logger.info("🚀 Initialisation du bot...")
        
        start_init = time.time()
        bot_instance = EnhancedTradingBot(str(config_path), dry_run=args.dry_run)
        init_time = time.time() - start_init
        
        logger.info(f"✅ Bot initialisé en {init_time:.2f}s")
        
        # Exécution du cycle de trading
        logger.info("📊 Démarrage du cycle de trading...")
        
        start_cycle = time.time()
        bot_instance.run_trading_cycle()
        cycle_time = time.time() - start_cycle
        
        logger.info(f"✅ Cycle terminé en {cycle_time:.2f}s")
        
        # Statistiques finales
        total_time = init_time + cycle_time
        logger.info(f"⏱️  Temps total d'exécution: {total_time:.2f}s")
        
        logger.info("🏁 Bot arrêté proprement")
        
    except KeyboardInterrupt:
        logging.getLogger(__name__).info("🛑 Interruption clavier détectée")
    except Exception as e:
        logging.getLogger(__name__).error(f"❌ ERREUR CRITIQUE: {e}")
        import traceback
        logging.getLogger(__name__).error(traceback.format_exc())
        sys.exit(1)
    finally:
        if bot_instance:
            logging.getLogger(__name__).info("🧹 Nettoyage en cours...")

if __name__ == "__main__":
    main()
