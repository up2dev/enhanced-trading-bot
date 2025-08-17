"""
Gestionnaire de portefeuille et configuration
Charge et valide la configuration depuis config.json
"""

import json
import logging
import os
from typing import Dict, List, Any, Optional
from pathlib import Path

class EnhancedPortfolioManager:
    """Gestionnaire de portefeuille avec configuration avancée"""
    
    def __init__(self, config_path: str):
        self.config_path = config_path
        self.logger = logging.getLogger(__name__)
        
        # Configuration chargée
        self.config = {}
        
        # Chargement de la configuration
        self._load_config()
        self._inject_env_variables()
        self._validate_config()
        
        self.logger.info("📋 PortfolioManager initialisé avec succès")
    
    def _load_config(self):
        """Charge la configuration depuis le fichier JSON"""
        try:
            self.logger.info(f"📋 Chargement config depuis: {self.config_path}")
            
            config_file = Path(self.config_path)
            if not config_file.exists():
                raise FileNotFoundError(f"Fichier de configuration non trouvé: {self.config_path}")
            
            with open(config_file, 'r', encoding='utf-8') as f:
                self.config = json.load(f)
            
            self.logger.debug(f"✅ Configuration chargée: {len(self.config)} sections")
            
        except json.JSONDecodeError as e:
            self.logger.error(f"❌ Erreur format JSON: {e}")
            raise ValueError(f"Format JSON invalide dans {self.config_path}: {e}")
        except Exception as e:
            self.logger.error(f"❌ Erreur chargement config: {e}")
            raise
    
    def _inject_env_variables(self):
        """Injecte les variables d'environnement dans la configuration"""
        try:
            # API Keys depuis l'environnement (plus sécurisé)
            api_key = os.getenv('BINANCE_API_KEY')
            api_secret = os.getenv('BINANCE_API_SECRET')
            
            if api_key and api_secret:
                self.logger.info("✅ API Key injectée depuis l'environnement")
                self.config['binance']['api_key'] = api_key
                self.config['binance']['api_secret'] = api_secret
            elif not self.config.get('binance', {}).get('api_key'):
                self.logger.warning("⚠️  Aucune API Key trouvée (env ou config)")
            else:
                self.logger.info("✅ API Key chargée depuis la configuration")
            
        except Exception as e:
            self.logger.error(f"❌ Erreur injection variables env: {e}")
    
    def _validate_config(self):
        """Valide la configuration"""
        try:
            # Sections obligatoires
            required_sections = ['binance', 'trading', 'cryptos']
            for section in required_sections:
                if section not in self.config:
                    raise ValueError(f"Section manquante: {section}")
            
            # Validation Binance
            binance_config = self.config['binance']
            if not binance_config.get('api_key'):
                raise ValueError("API Key Binance manquante")
            if not binance_config.get('api_secret'):
                raise ValueError("API Secret Binance manquante")
            
            # Validation trading
            trading_config = self.config['trading']
            required_params = ['base_currency', 'timeframe', 'rsi_period']
            for param in required_params:
                if param not in trading_config:
                    raise ValueError(f"Paramètre trading manquant: {param}")
            
            # Validation cryptos
            cryptos = self.config.get('cryptos', {})
            if not cryptos:
                raise ValueError("Aucune crypto configurée")
            
            active_count = sum(1 for cfg in cryptos.values() if cfg.get('active', False))
            if active_count == 0:
                self.logger.warning("⚠️  Aucune crypto active")
            
            # Validation des pourcentages d'allocation
            total_allocation = sum(
                cfg.get('max_allocation', 0) 
                for cfg in cryptos.values() 
                if cfg.get('active', False)
            )
            
            if total_allocation > 1.0:
                self.logger.warning(f"⚠️  Allocation totale > 100%: {total_allocation*100:.1f}%")
            
            self.logger.info("✅ Configuration validée")
            
        except Exception as e:
            self.logger.error(f"❌ Configuration invalide: {e}")
            raise
    
    def get_binance_config(self) -> Dict[str, Any]:
        """Retourne la configuration Binance"""
        return self.config.get('binance', {})
    
    def get_trading_config(self) -> Dict[str, Any]:
        """Retourne la configuration de trading"""
        return self.config.get('trading', {})
    
    def get_risk_config(self) -> Dict[str, Any]:
        """Retourne la configuration de gestion des risques"""
        return self.config.get('risk_management', {})
    
    def get_advanced_strategy_config(self) -> Dict[str, Any]:
        """Retourne la configuration de stratégie avancée"""
        return self.config.get('advanced_strategy', {})
    
    def get_monitoring_config(self) -> Dict[str, Any]:
        """Retourne la configuration de monitoring"""
        return self.config.get('monitoring', {})
    
    def get_raspberry_pi_config(self) -> Dict[str, Any]:
        """Retourne la configuration spécifique Raspberry Pi"""
        return self.config.get('raspberry_pi', {})
    
    def get_active_cryptos(self) -> List[Dict[str, Any]]:
        """Retourne la liste des cryptos actives"""
        active_cryptos = []
        
        cryptos_config = self.config.get('cryptos', {})
        for name, config in cryptos_config.items():
            if config.get('active', False):
                crypto_info = {
                    'name': name,
                    'symbol': config.get('symbol', f"{name}USDC"),
                    'profit_percentage': config.get('profit_percentage', 3.0),
                    'max_allocation': config.get('max_allocation', 0.1)
                }
                active_cryptos.append(crypto_info)
                self.logger.debug(f"✅ Crypto configurée: {name} - Allocation: {crypto_info['max_allocation']*100}%")
        
        self.logger.info(f"📊 {len(active_cryptos)} cryptos actives chargées")
        return active_cryptos
    
    def get_crypto_config(self, crypto_name: str) -> Optional[Dict[str, Any]]:
        """Retourne la configuration d'une crypto spécifique"""
        return self.config.get('cryptos', {}).get(crypto_name)
    
    def is_crypto_active(self, crypto_name: str) -> bool:
        """Vérifie si une crypto est active"""
        crypto_config = self.get_crypto_config(crypto_name)
        return crypto_config.get('active', False) if crypto_config else False
    
    def get_profit_target(self, symbol: str) -> float:
        """Retourne l'objectif de profit pour un symbole"""
        # Extraire le nom de la crypto du symbole
        crypto_name = symbol.replace('USDC', '').replace('USDT', '')
        
        crypto_config = self.get_crypto_config(crypto_name)
        if crypto_config:
            return crypto_config.get('profit_percentage', 3.0)
        
        # Valeur par défaut
        return self.config.get('trading', {}).get('default_profit_percentage', 3.0)
    
    def get_max_allocation(self, symbol: str) -> float:
        """Retourne l'allocation maximale pour un symbole"""
        crypto_name = symbol.replace('USDC', '').replace('USDT', '')
        
        crypto_config = self.get_crypto_config(crypto_name)
        if crypto_config:
            return crypto_config.get('max_allocation', 0.1)
        
        return 0.05  # 5% par défaut
    
    def update_crypto_status(self, crypto_name: str, active: bool):
        """Met à jour le statut actif d'une crypto"""
        try:
            if crypto_name in self.config.get('cryptos', {}):
                self.config['cryptos'][crypto_name]['active'] = active
                self.logger.info(f"{'✅ Activée' if active else '❌ Désactivée'}: {crypto_name}")
            else:
                self.logger.error(f"❌ Crypto inconnue: {crypto_name}")
                
        except Exception as e:
            self.logger.error(f"❌ Erreur mise à jour statut {crypto_name}: {e}")
    
    def save_config(self):
        """Sauvegarde la configuration actuelle"""
        try:
            # Créer une copie sans les clés sensibles pour la sauvegarde
            safe_config = self.config.copy()
            
            # Masquer les clés API pour la sauvegarde
            if 'binance' in safe_config:
                safe_config['binance'] = safe_config['binance'].copy()
                if 'api_key' in safe_config['binance']:
                    safe_config['binance']['api_key'] = "***HIDDEN***"
                if 'api_secret' in safe_config['binance']:
                    safe_config['binance']['api_secret'] = "***HIDDEN***"
            
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=4, ensure_ascii=False)
            
            self.logger.info(f"💾 Configuration sauvegardée: {self.config_path}")
            
        except Exception as e:
            self.logger.error(f"❌ Erreur sauvegarde config: {e}")
    
    def get_portfolio_summary(self) -> Dict[str, Any]:
        """Retourne un résumé de la configuration du portefeuille"""
        try:
            active_cryptos = self.get_active_cryptos()
            
            total_allocation = sum(crypto['max_allocation'] for crypto in active_cryptos)
            
            summary = {
                'total_cryptos': len(self.config.get('cryptos', {})),
                'active_cryptos': len(active_cryptos),
                'total_allocation': total_allocation,
                'allocation_percentage': total_allocation * 100,
                'base_currency': self.config.get('trading', {}).get('base_currency', 'USDC'),
                'trading_mode': 'testnet' if self.config.get('binance', {}).get('testnet', False) else 'live',
                'active_symbols': [crypto['symbol'] for crypto in active_cryptos],
                'risk_settings': {
                    'stop_loss': self.config.get('risk_management', {}).get('stop_loss_percentage', -8.0),
                    'max_daily_trades': self.config.get('risk_management', {}).get('max_daily_trades', 50),
                    'cooldown_minutes': self.config.get('risk_management', {}).get('cooldown_minutes', 30)
                }
            }
            
            return summary
            
        except Exception as e:
            self.logger.error(f"❌ Erreur résumé portefeuille: {e}")
            return {'error': str(e)}
    
    def validate_symbol_config(self, symbol: str) -> bool:
        """Valide la configuration d'un symbole"""
        try:
            crypto_name = symbol.replace('USDC', '').replace('USDT', '')
            crypto_config = self.get_crypto_config(crypto_name)
            
            if not crypto_config:
                self.logger.warning(f"⚠️  Configuration manquante pour {crypto_name}")
                return False
            
            # Vérifications
            required_fields = ['active', 'symbol', 'profit_percentage', 'max_allocation']
            for field in required_fields:
                if field not in crypto_config:
                    self.logger.error(f"❌ Champ manquant pour {crypto_name}: {field}")
                    return False
            
            # Validation des valeurs
            if crypto_config['profit_percentage'] <= 0:
                self.logger.error(f"❌ Profit percentage invalide pour {crypto_name}")
                return False
            
            if crypto_config['max_allocation'] <= 0 or crypto_config['max_allocation'] > 1:
                self.logger.error(f"❌ Allocation invalide pour {crypto_name}")
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Erreur validation {symbol}: {e}")
            return False
    
    def get_config_version(self) -> str:
        """Retourne la version de la configuration"""
        return self.config.get('version', '1.0.0')
    
    def reload_config(self):
        """Recharge la configuration depuis le fichier"""
        try:
            self.logger.info("🔄 Rechargement de la configuration...")
            self._load_config()
            self._inject_env_variables()
            self._validate_config()
            self.logger.info("✅ Configuration rechargée")
        except Exception as e:
            self.logger.error(f"❌ Erreur rechargement config: {e}")
            raise
