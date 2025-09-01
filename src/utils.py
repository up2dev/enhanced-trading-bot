"""
Utilitaires pour le trading bot
"""

import os
import json
import logging
import logging.handlers
import requests
from pathlib import Path
from typing import Dict, Any
from datetime import datetime

def ensure_directories():
    """Crée les répertoires nécessaires"""
    directories = ['logs', 'logs/archived', 'db', 'config']
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        
        # Permissions pour Raspberry Pi
        os.chmod(directory, 0o755)

def setup_logging(level: str = "INFO", log_dir: str = None):
    """Configuration avancée du logging avec rotation"""
    
    # Niveau de logging
    numeric_level = getattr(logging, level.upper(), None)
    if not isinstance(numeric_level, int):
        raise ValueError(f'Invalid log level: {level}')
    
    # Configuration du logger racine
    logger = logging.getLogger()
    logger.setLevel(numeric_level)
    
    # Nettoyer les handlers existants
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # Format détaillé des logs
    detailed_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Format simple pour la console
    console_formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%H:%M:%S'
    )
    
    # Handler console (toujours actif)
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(console_formatter)
    console_handler.setLevel(logging.INFO)
    logger.addHandler(console_handler)
    
    if log_dir:
        log_path = Path(log_dir)
        log_path.mkdir(parents=True, exist_ok=True)
        
        # 1. Log principal avec rotation quotidienne
        main_log_file = log_path / 'trading_bot.log'
        main_handler = logging.handlers.TimedRotatingFileHandler(
            main_log_file,
            when='midnight',
            interval=1,
            backupCount=15,  # 15 jours
            encoding='utf-8'
        )
        main_handler.setFormatter(detailed_formatter)
        main_handler.setLevel(logging.DEBUG)
        logger.addHandler(main_handler)
        
        # 2. Log des erreurs seulement
        error_log_file = log_path / 'errors.log'
        error_handler = logging.handlers.TimedRotatingFileHandler(
            error_log_file,
            when='midnight',
            interval=1,
            backupCount=15,
            encoding='utf-8'
        )
        error_handler.setFormatter(detailed_formatter)
        error_handler.setLevel(logging.ERROR)
        logger.addHandler(error_handler)
        
        # 3. Log de debug détaillé (si niveau DEBUG)
        if numeric_level <= logging.DEBUG:
            debug_log_file = log_path / 'debug.log'
            debug_handler = logging.handlers.TimedRotatingFileHandler(
                debug_log_file,
                when='midnight',
                interval=1,
                backupCount=7,  # 7 jours pour debug
                encoding='utf-8'
            )
            debug_handler.setFormatter(logging.Formatter(
                '%(asctime)s - %(name)s:%(lineno)d - %(levelname)s - %(funcName)s() - %(message)s'
            ))
            debug_handler.setLevel(logging.DEBUG)
            logger.addHandler(debug_handler)
    
    # Log initial
    logging.getLogger(__name__).info(f"📝 Logging configuré - Niveau: {level}")
    if log_dir:
        logging.getLogger(__name__).info(f"📁 Logs sauvés dans: {log_path.absolute()}")

def load_json_config(config_path: str) -> Dict[str, Any]:
    """Charge un fichier JSON avec gestion d'erreur"""
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        return config
    except FileNotFoundError:
        raise FileNotFoundError(f"Fichier de configuration non trouvé: {config_path}")
    except json.JSONDecodeError as e:
        raise ValueError(f"Erreur dans le fichier JSON {config_path}: {e}")
    except Exception as e:
        raise Exception(f"Erreur lors du chargement de {config_path}: {e}")

def validate_config(config: Dict[str, Any]):
    """Valide la configuration"""
    
    required_sections = ['binance', 'trading', 'cryptos']
    for section in required_sections:
        if section not in config:
            raise ValueError(f"Section manquante dans la configuration: {section}")
    
    # Validation Binance
    binance_config = config['binance']
    if not binance_config.get('api_key'):
        raise ValueError("Clé API Binance manquante")
    if not binance_config.get('api_secret'):
        raise ValueError("Clé secrète API Binance manquante")
    
    # Validation trading
    trading_config = config['trading']
    required_trading = ['base_currency', 'timeframe', 'rsi_period']
    for param in required_trading:
        if param not in trading_config:
            raise ValueError(f"Paramètre trading manquant: {param}")
    
    # Validation cryptos
    cryptos = config['cryptos']
    if not cryptos:
        raise ValueError("Aucune crypto configurée")
    
    active_cryptos = [name for name, cfg in cryptos.items() if cfg.get('active', False)]
    if not active_cryptos:
        raise ValueError("Aucune crypto active")
    
    logging.getLogger(__name__).info(f"✅ Configuration validée: {len(active_cryptos)} cryptos actives")

def format_number(number: float, decimals: int = 2) -> str:
    """Formate un nombre avec séparateurs"""
    return f"{number:,.{decimals}f}".replace(',', ' ')

def format_percentage(value: float, decimals: int = 2) -> str:
    """Formate un pourcentage"""
    return f"{value:+.{decimals}f}%"

def format_crypto_amount(amount: float, symbol: str) -> str:
    """Formate un montant de crypto selon le symbole"""
    if symbol in ['BTC']:
        return f"{amount:.8f}"
    elif symbol in ['ETH', 'BNB', 'SOL', 'DOT']:
        return f"{amount:.6f}"
    elif symbol in ['USDC', 'USDT']:
        return f"{amount:.2f}"
    else:
        return f"{amount:.8f}"

def get_system_info() -> Dict[str, Any]:
    """Informations système pour Raspberry Pi"""
    info = {
        'platform': 'Raspberry Pi',
        'timestamp': datetime.now().isoformat(),
    }
    
    try:
        # Température CPU
        with open('/sys/class/thermal/thermal_zone0/temp', 'r') as f:
            info['cpu_temp'] = round(int(f.read()) / 1000.0, 1)
    except:
        pass
    
    try:
        # Charge système
        with open('/proc/loadavg', 'r') as f:
            load = f.read().strip().split()
            info['load_avg'] = float(load[0])
    except:
        pass
    
    try:
        # Mémoire
        with open('/proc/meminfo', 'r') as f:
            meminfo = f.read()
            for line in meminfo.split('\n'):
                if 'MemAvailable:' in line:
                    info['mem_available_mb'] = int(line.split()[1]) // 1024
                    break
    except:
        pass
    
    return info

def send_telegram_message(bot_token: str, chat_id: str, message: str) -> bool:
    """Envoie un eessage Telegram (utilitaire global)"""
    try:
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": message,
            "parse_mode": "HTML"
        }
        response = requests.post(url, json=payload, timeout=5)
        if response.status_code == 200:
            logging.getLogger(__name__).debug("Message Telegram envoyé")
            return True
        else:
            logging.getLogger(__name__).warning(f"Erreur envoi Telegram: {response.text}")
            return False
    except Exception as e:
        logging.getLogger(__name__).warning(f" Exception Telegram: {e}")


class RaspberryPiOptimizer:
    """Optimisations spécifiques Raspberry Pi"""
    
    @staticmethod
    def reduce_memory_usage():
        """Réduit l'utilisation mémoire"""
        import gc
        gc.collect()
    
    @staticmethod
    def check_network() -> bool:
        """Vérifie la connectivité réseau"""
        try:
            import socket
            socket.create_connection(("8.8.8.8", 53), timeout=3)
            return True
        except:
            return False
    
    @staticmethod
    def optimize_for_pi():
        """Optimisations générales pour Pi"""
        # Réduction du cache pandas
        try:
            import pandas as pd
            pd.set_option('compute.use_bottleneck', False)
            pd.set_option('compute.use_numexpr', False)
        except:
            pass
