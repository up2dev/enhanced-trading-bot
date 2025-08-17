"""
Client Binance amélioré avec gestion d'erreurs et retry
Optimisé pour Raspberry Pi Zero W2
"""

import logging
import time
import hashlib
import hmac
from decimal import Decimal
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
import requests
from binance.client import Client
from binance.exceptions import BinanceAPIException, BinanceOrderException

class EnhancedBinanceClient:
    """Client Binance avec fonctionnalités avancées et robustesse"""
    
    def __init__(self, api_key: str, api_secret: str, testnet: bool = False):
        self.api_key = api_key
        self.api_secret = api_secret
        self.testnet = testnet
        self.logger = logging.getLogger(__name__)
        
        # Configuration client
        self.client = Client(
            api_key=api_key,
            api_secret=api_secret,
            testnet=testnet
        )
        
        # Configuration retry
        self.max_retries = 3
        self.retry_delay = 1.0
        self.rate_limit_delay = 0.5
        
        # Cache pour éviter les appels répétés
        self._symbol_info_cache = {}
        self._cache_duration = 300  # 5 minutes
        self._last_cache_update = 0
        
        # Synchronisation du timestamp
        self._sync_timestamp()
        
        self.logger.info("🔗 Client Binance initialisé")
        if testnet:
            self.logger.warning("⚠️  Mode TESTNET activé")
    
    def _sync_timestamp(self):
        """Synchronise le timestamp avec les serveurs Binance"""
        try:
            self.logger.info("🕐 Synchronisation du timestamp avec Binance...")
            
            server_time = self.client.get_server_time()
            local_time = int(time.time() * 1000)
            
            self.timestamp_offset = server_time['serverTime'] - local_time
            
            self.logger.info(f"✅ Timestamp synchronisé. Offset: {self.timestamp_offset}ms")
            
        except Exception as e:
            self.logger.warning(f"⚠️  Échec synchronisation timestamp: {e}")
            self.timestamp_offset = 0
    
    def _make_request_with_retry(self, func, *args, **kwargs):
        """Exécute une requête avec retry automatique"""
        last_exception = None
        
        for attempt in range(self.max_retries):
            try:
                # Délai pour éviter le rate limiting
                if attempt > 0:
                    delay = self.retry_delay * (2 ** (attempt - 1))  # Backoff exponentiel
                    self.logger.debug(f"⏳ Tentative {attempt + 1}/{self.max_retries} dans {delay:.1f}s...")
                    time.sleep(delay)
                
                # Ajouter un petit délai pour éviter les rate limits
                time.sleep(self.rate_limit_delay)
                
                # Exécuter la requête
                result = func(*args, **kwargs)
                
                if attempt > 0:
                    self.logger.info(f"✅ Requête réussie après {attempt + 1} tentative(s)")
                
                return result
                
            except BinanceAPIException as e:
                last_exception = e
                
                # Gestion spécifique des erreurs Binance
                if e.code == -1021:  # Timestamp out of sync
                    self.logger.warning("🕐 Resynchronisation du timestamp...")
                    self._sync_timestamp()
                    continue
                    
                elif e.code == -1003:  # Too many requests
                    self.logger.warning("⚠️  Rate limit atteint, pause plus longue...")
                    time.sleep(60)  # Pause 1 minute
                    continue
                    
                elif e.code in [-1000, -1001]:  # Server errors
                    self.logger.warning(f"🔄 Erreur serveur Binance: {e.message}")
                    continue
                    
                elif e.code == -2010:  # Insufficient funds
                    self.logger.error(f"💰 Fonds insuffisants: {e.message}")
                    break
                    
                else:
                    self.logger.error(f"❌ Erreur API Binance [{e.code}]: {e.message}")
                    if attempt == self.max_retries - 1:
                        break
                    continue
                    
            except requests.exceptions.RequestException as e:
                last_exception = e
                self.logger.warning(f"🌐 Erreur réseau (tentative {attempt + 1}/{self.max_retries}): {e}")
                
                if "timeout" in str(e).lower():
                    # Timeout - retry avec délai plus long
                    time.sleep(5)
                    continue
                elif "connection" in str(e).lower():
                    # Problème de connexion
                    time.sleep(10)
                    continue
                else:
                    if attempt == self.max_retries - 1:
                        break
                    continue
                    
            except Exception as e:
                last_exception = e
                self.logger.error(f"❌ Erreur inattendue: {e}")
                if attempt == self.max_retries - 1:
                    break
                continue
        
        # Toutes les tentatives ont échoué
        self.logger.error(f"❌ Échec après {self.max_retries} tentatives. Dernière erreur: {last_exception}")
        raise last_exception
    
    def test_connection(self) -> bool:
        """Test la connexion à l'API Binance"""
        try:
            self.logger.info("🔧 Test de connexion à l'API Binance...")
            
            # Test de l'API publique
            server_time = self._make_request_with_retry(self.client.get_server_time)
            self.logger.info("✅ Système Binance opérationnel")
            
            # Calcul de l'offset de temps
            local_time = int(time.time() * 1000)
            offset = abs(server_time['serverTime'] - local_time)
            self.logger.info(f"🕐 Offset timestamp: {offset}ms")
            
            if offset > 5000:  # > 5 secondes
                self.logger.warning("⚠️  Offset de temps important, resynchronisation...")
                self._sync_timestamp()
            
            # Test de l'API privée (compte)
            account_status = self._make_request_with_retry(self.client.get_account_status)
            self.logger.info(f"✅ Status compte: {account_status.get('data', 'Normal')}")
            
            # Vérification des permissions
            account_info = self._make_request_with_retry(self.client.get_account)
            permissions = account_info.get('permissions', [])
            
            can_trade = any(perm.startswith('TRD_GRP_') for perm in permissions)
            can_withdraw = 'WITHDRAWING' in permissions  # Existe toujours pour les retraits
            
            self.logger.info(f"🔑 Permissions - Trading: {can_trade}, Retrait: {can_withdraw}")
            
            if not can_trade:
                self.logger.error("❌ Permissions de trading insuffisantes!")
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Test de connexion échoué: {e}")
            return False
    
    def get_account_balance(self, asset: str) -> float:
        """Récupère le solde libre d'un asset"""
        try:
            balance_info = self._make_request_with_retry(
                self.client.get_asset_balance, 
                asset=asset
            )
            
            if balance_info:
                free_balance = float(balance_info['free'])
                self.logger.debug(f"💰 Solde {asset}: {free_balance:.8f}")
                return free_balance
            
            return 0.0
            
        except Exception as e:
            self.logger.error(f"❌ Erreur récupération solde {asset}: {e}")
            return 0.0
    
    def get_all_balances(self, min_value: float = 0.01) -> Dict[str, Dict[str, float]]:
        """Récupère tous les soldes significatifs"""
        try:
            self.logger.debug("📊 Récupération des informations du compte...")
            account_info = self._make_request_with_retry(self.client.get_account)
            
            balances = {}
            for balance in account_info.get('balances', []):
                asset = balance['asset']
                free = float(balance['free'])
                locked = float(balance['locked'])
                total = free + locked
                
                if total >= min_value:
                    balances[asset] = {
                        'free': free,
                        'locked': locked,
                        'total': total
                    }
            
            return balances
            
        except Exception as e:
            self.logger.error(f"❌ Erreur récupération soldes: {e}")
            return {}
    
    def get_total_portfolio_value(self) -> float:
        """Calcule la valeur totale du portefeuille en USDC"""
        try:
            self.logger.debug("💱 Récupération des prix...")
            
            # Récupérer tous les prix
            tickers = self._make_request_with_retry(self.client.get_all_tickers)
            price_map = {ticker['symbol']: float(ticker['price']) for ticker in tickers}
            
            # Récupérer les soldes
            balances = self.get_all_balances()
            
            total_value = 0.0
            significant_balances = []
            
            for asset, balance_info in balances.items():
                total_balance = balance_info['total']
                
                if asset == 'USDC':
                    asset_value = total_balance
                else:
                    # Chercher le prix en USDC
                    symbol = f"{asset}USDC"
                    if symbol in price_map:
                        asset_value = total_balance * price_map[symbol]
                    else:
                        # Essayer via BTC ou ETH si pas de paire directe USDC
                        btc_symbol = f"{asset}BTC"
                        if btc_symbol in price_map and 'BTCUSDC' in price_map:
                            btc_price = price_map[btc_symbol] * price_map['BTCUSDC']
                            asset_value = total_balance * btc_price
                        else:
                            asset_value = 0  # Impossible de calculer
                
                total_value += asset_value
                
                # Garder les soldes significatifs pour le log
                if asset_value >= 1.0:  # Au moins 1 USDC
                    significant_balances.append((asset, total_balance, asset_value))
            
            # Log des soldes significatifs
            if significant_balances:
                self.logger.info("💰 Soldes significatifs:")
                for asset, quantity, value in sorted(significant_balances, key=lambda x: x[2], reverse=True):
                    self.logger.info(f"   • {asset}: {quantity:.6f} ({value:.2f} USDC)")
            
            return total_value
            
        except Exception as e:
            self.logger.error(f"❌ Erreur calcul valeur portefeuille: {e}")
            return 0.0
    
    def get_symbol_info(self, symbol: str) -> Optional[Dict]:
        """Récupère les informations d'un symbole avec cache"""
        try:
            current_time = time.time()
            
            # Vérifier le cache
            if (symbol in self._symbol_info_cache and 
                current_time - self._last_cache_update < self._cache_duration):
                return self._symbol_info_cache[symbol]
            
            # Récupérer les infos d'exchange
            exchange_info = self._make_request_with_retry(self.client.get_exchange_info)
            
            # Mettre à jour le cache complet
            self._symbol_info_cache = {
                s['symbol']: s for s in exchange_info['symbols'] 
                if s['status'] == 'TRADING'
            }
            self._last_cache_update = current_time
            
            return self._symbol_info_cache.get(symbol)
            
        except Exception as e:
            self.logger.error(f"❌ Erreur récupération info symbole {symbol}: {e}")
            return None
    
    def get_current_price(self, symbol: str) -> float:
        """Récupère le prix actuel d'un symbole"""
        try:
            ticker = self._make_request_with_retry(
                self.client.get_symbol_ticker,
                symbol=symbol
            )
            return float(ticker['price'])
            
        except Exception as e:
            self.logger.error(f"❌ Erreur récupération prix {symbol}: {e}")
            return 0.0
    
    def place_market_buy_order(self, symbol: str, quantity: float) -> Optional[Dict]:
        """Place un ordre d'achat au marché"""
        try:
            self.logger.info(f"💰 Ordre d'achat marché: {symbol} - {quantity:.8f}")
            
            order = self._make_request_with_retry(
                self.client.order_market_buy,
                symbol=symbol,
                quantity=quantity
            )
            
            self.logger.info(f"✅ Ordre d'achat exécuté: {order['orderId']}")
            return order
            
        except Exception as e:
            self.logger.error(f"❌ Erreur ordre d'achat {symbol}: {e}")
            return None
    
    def place_limit_sell_order(self, symbol: str, quantity: float, price: float) -> Optional[Dict]:
        """Place un ordre de vente limite"""
        try:
            self.logger.info(f"📈 Ordre de vente limite: {symbol} - {quantity:.8f} à {price:.8f}")
            
            order = self._make_request_with_retry(
                self.client.order_limit_sell,
                symbol=symbol,
                quantity=quantity,
                price=f"{price:.8f}"
            )
            
            self.logger.info(f"✅ Ordre de vente placé: {order['orderId']}")
            return order
            
        except Exception as e:
            self.logger.error(f"❌ Erreur ordre de vente {symbol}: {e}")
            return None
    
    def place_oco_order(self, symbol: str, quantity: float, price: float, 
                       stop_price: float, stop_limit_price: float) -> Optional[Dict]:
        """Place un ordre OCO (One-Cancels-Other)"""
        try:
            self.logger.info(f"📊 Ordre OCO: {symbol} - {quantity:.8f}")
            self.logger.info(f"   🎯 Limite: {price:.8f}")
            self.logger.info(f"   🛡️  Stop: {stop_price:.8f} → {stop_limit_price:.8f}")
            
            oco_order = self._make_request_with_retry(
                self.client.create_oco_order,
                symbol=symbol,
                side='SELL',
                quantity=quantity,
                price=f"{price:.8f}",
                stopPrice=f"{stop_price:.8f}",
                stopLimitPrice=f"{stop_limit_price:.8f}"
            )
            
            self.logger.info(f"✅ Ordre OCO placé: {oco_order['orderListId']}")
            return oco_order
            
        except Exception as e:
            self.logger.error(f"❌ Erreur ordre OCO {symbol}: {e}")
            return None
    
    def get_open_orders(self, symbol: Optional[str] = None) -> List[Dict]:
        """Récupère les ordres ouverts"""
        try:
            if symbol:
                orders = self._make_request_with_retry(
                    self.client.get_open_orders,
                    symbol=symbol
                )
            else:
                orders = self._make_request_with_retry(self.client.get_open_orders)
            
            return orders if orders else []
            
        except Exception as e:
            self.logger.error(f"❌ Erreur récupération ordres ouverts: {e}")
            return []
    
    def cancel_order(self, symbol: str, order_id: str) -> bool:
        """Annule un ordre"""
        try:
            self.logger.info(f"🚫 Annulation ordre {order_id} pour {symbol}")
            
            result = self._make_request_with_retry(
                self.client.cancel_order,
                symbol=symbol,
                orderId=order_id
            )
            
            self.logger.info(f"✅ Ordre {order_id} annulé")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Erreur annulation ordre {order_id}: {e}")
            return False
    
    def get_recent_trades(self, symbol: str, limit: int = 50) -> List[Dict]:
        """Récupère les trades récents"""
        try:
            trades = self._make_request_with_retry(
                self.client.get_my_trades,
                symbol=symbol,
                limit=limit
            )
            
            return trades if trades else []
            
        except Exception as e:
            self.logger.error(f"❌ Erreur récupération trades {symbol}: {e}")
            return []
    
    def get_klines(self, symbol: str, interval: str, limit: int = 100) -> List[List]:
        """Récupère les données de chandelier"""
        try:
            klines = self._make_request_with_retry(
                self.client.get_klines,
                symbol=symbol,
                interval=interval,
                limit=limit
            )
            
            return klines if klines else []
            
        except Exception as e:
            self.logger.error(f"❌ Erreur récupération klines {symbol}: {e}")
            return []
    
    def format_quantity(self, symbol: str, quantity: float) -> float:
        """Formate une quantité selon les règles du symbole"""
        try:
            symbol_info = self.get_symbol_info(symbol)
            if not symbol_info:
                return round(quantity, 8)
            
            lot_size_filter = next(
                (f for f in symbol_info['filters'] if f['filterType'] == 'LOT_SIZE'),
                None
            )
            
            if lot_size_filter:
                step_size = float(lot_size_filter['stepSize'])
                min_qty = float(lot_size_filter['minQty'])
                
                # Ajuster selon le step_size
                adjusted_qty = quantity - (quantity % step_size)
                adjusted_qty = max(adjusted_qty, min_qty)
                
                # Précision basée sur step_size
                precision = len(str(step_size).split('.')[-1].rstrip('0'))
                return round(adjusted_qty, precision)
            
            return round(quantity, 8)
            
        except Exception as e:
            self.logger.error(f"❌ Erreur formatage quantité: {e}")
            return round(quantity, 8)
    
    def format_price(self, symbol: str, price: float) -> float:
        """Formate un prix selon les règles du symbole"""
        try:
            symbol_info = self.get_symbol_info(symbol)
            if not symbol_info:
                return round(price, 8)
            
            price_filter = next(
                (f for f in symbol_info['filters'] if f['filterType'] == 'PRICE_FILTER'),
                None
            )
            
            if price_filter:
                tick_size = float(price_filter['tickSize'])
                
                # Ajuster selon le tick_size
                adjusted_price = price - (price % tick_size)
                
                # Précision basée sur tick_size
                if tick_size >= 1:
                    precision = 0
                else:
                    precision = len(str(tick_size).split('.')[-1].rstrip('0'))
                
                return round(adjusted_price, precision)
            
            return round(price, 8)
            
        except Exception as e:
            self.logger.error(f"❌ Erreur formatage prix: {e}")
            return round(price, 8)
    
    def is_market_open(self, symbol: str) -> bool:
        """Vérifie si le marché est ouvert pour un symbole"""
        try:
            symbol_info = self.get_symbol_info(symbol)
            return symbol_info['status'] == 'TRADING' if symbol_info else False
            
        except Exception as e:
            self.logger.error(f"❌ Erreur vérification marché {symbol}: {e}")
            return False
    
    def get_24h_stats(self, symbol: str) -> Optional[Dict]:
        """Récupère les statistiques 24h d'un symbole"""
        try:
            stats = self._make_request_with_retry(
                self.client.get_24hr_ticker,
                symbol=symbol
            )
            
            if stats:
                return {
                    'price_change': float(stats['priceChange']),
                    'price_change_percent': float(stats['priceChangePercent']),
                    'high_price': float(stats['highPrice']),
                    'low_price': float(stats['lowPrice']),
                    'volume': float(stats['volume']),
                    'quote_volume': float(stats['quoteVolume'])
                }
            
            return None
            
        except Exception as e:
            self.logger.error(f"❌ Erreur statistiques 24h {symbol}: {e}")
            return None
