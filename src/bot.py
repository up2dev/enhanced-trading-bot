"""
Enhanced Trading Bot - Classe principale
Version optimisée Raspberry Pi avec OCO et stop-loss
OPTIMISÉE pour performance maximum + Logs indicateurs
"""

import logging
import time
from typing import List, Dict, Any, Tuple
from datetime import datetime

from .binance_client import EnhancedBinanceClient
from .indicators import AdvancedTechnicalIndicators
from .portfolio_manager import EnhancedPortfolioManager
from .database import DatabaseManager
from .trading_engine import TradingEngine
from .utils import RaspberryPiOptimizer, get_system_info

class EnhancedTradingBot:
    """Bot de trading principal avec gestion avancée et performance optimisée"""
    
    def __init__(self, config_path: str, dry_run: bool = False):
        self.config_path = config_path
        self.dry_run = dry_run
        self.logger = logging.getLogger(__name__)
        
        # Initialisation des composants
        self._initialize_components()
        
        # Optimisations Raspberry Pi
        RaspberryPiOptimizer.optimize_for_pi()
        
        # État interne
        self.active_positions = {}
        self.cycle_count = 0
        
        # Log de l'initialisation
        mode_text = "🧪 SIMULATION" if self.dry_run else "🔥 RÉEL"
        self.logger.info(f"🤖 EnhancedTradingBot initialisé en mode {mode_text}")
        
        # Informations système
        system_info = get_system_info()
        if 'cpu_temp' in system_info:
            self.logger.info(f"🌡️  Température CPU: {system_info['cpu_temp']}°C")
        
    def _initialize_components(self):
        """Initialise tous les composants du bot"""
        try:
            # Portfolio Manager (configuration centrale)
            self.logger.debug("📋 Initialisation du portfolio manager...")
            self.portfolio_manager = EnhancedPortfolioManager(self.config_path)
            
            # Client Binance
            self.logger.debug("🔗 Initialisation du client Binance...")
            binance_config = self.portfolio_manager.get_binance_config()
            self.binance_client = EnhancedBinanceClient(
                binance_config['api_key'],
                binance_config['api_secret'],
                binance_config.get('testnet', False)
            )
            
            # Base de données
            self.logger.debug("💾 Initialisation de la base de données...")
            self.database = DatabaseManager()
            
            # Configuration complète pour le trading engine
            full_config = {
                'trading': self.portfolio_manager.get_trading_config(),
                'risk_management': self.portfolio_manager.get_risk_config(),
                'advanced_strategy': self.portfolio_manager.get_advanced_strategy_config(),
                'cryptos': self.portfolio_manager.config.get('cryptos', {})
            }
            
            # Trading Engine
            self.logger.debug("⚙️  Initialisation du trading engine...")
            self.trading_engine = TradingEngine(
                self.binance_client, 
                self.database, 
                full_config, 
                dry_run=self.dry_run
            )
            
            # Indicateurs techniques (optionnel)
            self.indicators = AdvancedTechnicalIndicators()
            
            self.logger.debug("✅ Tous les composants initialisés")
            
        except Exception as e:
            self.logger.error(f"❌ Erreur initialisation composants: {e}")
            raise
    
    def run_trading_cycle(self):
        """Exécute un cycle de trading complet avec surveillance OCO"""
        start_time = time.time()
        self.cycle_count += 1
        
        try:
            mode_text = "🧪 MODE SIMULATION" if self.dry_run else "🔥 MODE TRADING RÉEL"
            self.logger.info(f"🚀 === DÉBUT DU CYCLE #{self.cycle_count} - {mode_text} ===")
            
            # Vérifications préalables
            if not self._pre_cycle_checks():
                return
            
            # Informations du portefeuille (version simple)
            self._log_portfolio_info_simple()
            
            # 🔍 SURVEILLANCE DES ORDRES OCO (AVANT le trading)
            if not self.dry_run:  # Pas en simulation
                self.trading_engine.monitor_oco_orders()
            
            # Vérification des positions existantes
            self._check_existing_positions()
            
            # Statistiques de trading
            self.trading_engine.log_trading_stats()
            
            # Trading pour chaque crypto active (OPTIMISÉ)
            self._execute_trading_strategies()
            
            # Post-cycle cleanup
            self._post_cycle_cleanup()
            
            # Statistiques du cycle
            cycle_time = time.time() - start_time
            self.logger.info(f"✅ Cycle #{self.cycle_count} terminé en {cycle_time:.2f}s")
            self.logger.info("🏁 === FIN DU CYCLE DE TRADING ===")
            
        except Exception as e:
            self.logger.error(f"❌ Erreur critique dans le cycle #{self.cycle_count}: {e}")
            import traceback
            self.logger.error(traceback.format_exc())
            raise
    
    def _pre_cycle_checks(self) -> bool:
        """Vérifications avant le cycle de trading"""
        try:
            # Test de connexion Binance
            self.logger.debug("🔧 Test de connexion à l'API Binance...")
            if not self.binance_client.test_connection():
                self.logger.error("❌ Impossible de se connecter à l'API Binance")
                return False
            
            # Vérification réseau
            if not RaspberryPiOptimizer.check_network():
                self.logger.error("❌ Pas de connectivité réseau")
                return False
            
            # Vérifications système
            system_info = get_system_info()
            
            # Température CPU
            if 'cpu_temp' in system_info and system_info['cpu_temp'] > 80:
                self.logger.warning(f"⚠️  Température CPU élevée: {system_info['cpu_temp']}°C")
            
            # Charge système
            if 'load_avg' in system_info and system_info['load_avg'] > 2:
                self.logger.warning(f"⚠️  Charge système élevée: {system_info['load_avg']}")
            
            # Mémoire disponible
            if 'mem_available_mb' in system_info and system_info['mem_available_mb'] < 100:
                self.logger.warning(f"⚠️  Mémoire faible: {system_info['mem_available_mb']} MB")
                RaspberryPiOptimizer.reduce_memory_usage()
            
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Erreur vérifications pré-cycle: {e}")
            return False
    
    def _log_portfolio_info_simple(self):
        """Version simplifiée du log portfolio pour éviter double calcul"""
        try:
            self.logger.debug("📊 Récupération informations portefeuille (simple)...")
            
            # On récupère juste l'USDC libre pour les calculs rapides
            usdc_balance = self.binance_client.get_account_balance('USDC')
            self._current_usdc_balance = usdc_balance
            
            self.logger.info(f"💳 Solde libre USDC: {usdc_balance:.2f}")
            
        except Exception as e:
            self.logger.error(f"❌ Erreur informations portefeuille: {e}")
            self._current_usdc_balance = 0
    
    def _check_existing_positions(self):
        """Vérifie et gère les positions existantes (version corrigée)"""
        try:
            self.logger.info("🔍 Vérification des positions existantes...")
        
            open_orders = self.binance_client._make_request_with_retry(
                self.binance_client.client.get_open_orders
            )
        
            if not open_orders:
                self.logger.info("✅ Aucun ordre en cours")
                return
        
            # Grouper par symbole avec analyse OCO/LIMIT
            orders_by_symbol = {}
            for order in open_orders:
                symbol = order['symbol']
                if symbol not in orders_by_symbol:
                    orders_by_symbol[symbol] = {
                        'oco_ids': set(), 
                        'limit_count': 0, 
                        'all_sell': []
                    }
            
                if order['side'] == 'SELL':
                    orders_by_symbol[symbol]['all_sell'].append(order)
                
                    order_list_id = order.get('orderListId', -1)
                    if order_list_id != -1:
                        # Ordre OCO
                        orders_by_symbol[symbol]['oco_ids'].add(order_list_id)
                    else:
                        # Ordre LIMIT simple
                        orders_by_symbol[symbol]['limit_count'] += 1
        
            self.logger.info(f"📋 {len(open_orders)} ordre(s) Binance total:")
        
            total_value = 0
            total_positions_logical = 0
        
            for symbol, orders_data in orders_by_symbol.items():
                oco_count = len(orders_data['oco_ids'])
                limit_count = orders_data['limit_count']
                logical_positions = oco_count + limit_count
            
                if logical_positions > 0:
                    total_positions_logical += logical_positions
                
                    # Calculer la valeur
                    symbol_value = sum(float(o['origQty']) * float(o['price']) for o in orders_data['all_sell'])
                    total_value += symbol_value
                
                    # Log détaillé
                    position_detail = []
                    if oco_count > 0:
                        position_detail.append(f"{oco_count} OCO")
                    if limit_count > 0:
                        position_detail.append(f"{limit_count} LIMIT")
                
                    detail_str = " + ".join(position_detail)
                    self.logger.info(f"   📈 {symbol}: {logical_positions} positions ({detail_str}) ~{symbol_value:.2f} USDC")
        
            if total_value > 0:
                self.logger.info(f"💰 Total: {total_positions_logical} positions logiques = {total_value:.2f} USDC")
        
        except Exception as e:
            self.logger.error(f"❌ Erreur vérification positions: {e}")
    
    def _execute_trading_strategies(self):
        """Exécute les stratégies - VERSION ULTRA OPTIMISÉE"""
        try:
            start_time = time.time()
            
            # 📊 CALCULER UNE SEULE FOIS LE PORTFOLIO COMPLET
            self.logger.debug("📊 Calcul portfolio global (optimisé)...")
            account, portfolio_data = self._calculate_portfolio_once()
            
            if not account or not portfolio_data:
                self.logger.error("❌ Impossible de calculer le portfolio")
                return
            
            calc_time = time.time() - start_time
            self.logger.debug(f"⚡ Portfolio calculé en {calc_time:.2f}s")
            
            active_cryptos = portfolio_data['active_cryptos']  # Déjà chargé
            self.logger.info(f"🪙 Cryptos actives: {len(active_cryptos)}")
            
            # Trading pour chaque crypto avec données pré-calculées
            successful_trades = 0
            for i, crypto_config in enumerate(active_cryptos):
                try:
                    crypto_start = time.time()
                    
                    if self._process_crypto_trading_optimized(crypto_config, account, portfolio_data):
                        successful_trades += 1
                    
                    crypto_time = time.time() - crypto_start
                    self.logger.debug(f"⚡ {crypto_config['name']} traité en {crypto_time:.2f}s")
                        
                    # Pause réduite seulement entre cryptos
                    if i < len(active_cryptos) - 1:  # Pas de pause après la dernière
                        time.sleep(0.1)
                        
                except Exception as e:
                    self.logger.error(f"❌ Erreur trading {crypto_config.get('name', 'UNKNOWN')}: {e}")
                    continue
            
            total_time = time.time() - start_time
            self.logger.info(f"📊 Résultat cycle: {successful_trades}/{len(active_cryptos)} cryptos traitées avec succès")
            self.logger.debug(f"⚡ Stratégies exécutées en {total_time:.2f}s")
            
        except Exception as e:
            self.logger.error(f"❌ Erreur stratégies de trading: {e}")

    def _calculate_portfolio_once(self) -> Tuple[Dict, Dict]:
        """Calcule le portfolio complet UNE SEULE FOIS - VERSION ULTRA OPTIMISÉE"""
        try:
            # 1. Récupérer le compte complet UNE FOIS
            account = self.binance_client._make_request_with_retry(
                self.binance_client.client.get_account
            )
            
            # 2. Cryptos actives UNE FOIS
            active_cryptos = self.portfolio_manager.get_active_cryptos()
            
            # 3. Batch de TOUS les prix UNE FOIS (plus rapide que ticker individuels)
            all_prices = self.binance_client._make_request_with_retry(
                self.binance_client.client.get_all_tickers
            )
            
            # Créer un dict pour accès O(1)
            price_dict = {ticker['symbol']: float(ticker['price']) for ticker in all_prices}
            
            # 4. Calculer portfolio total
            total_portfolio_value = 0.0
            crypto_balances = {}
            crypto_prices = {}
            
            # USDC
            usdc_free = 0.0
            for balance in account['balances']:
                if balance['asset'] == 'USDC':
                    usdc_free = float(balance['free'])
                    usdc_locked = float(balance['locked'])
                    total_usdc = usdc_free + usdc_locked
                    total_portfolio_value += total_usdc
                    break
            
            self._current_usdc_balance = usdc_free
            
            # 5. Toutes les cryptos en une passe
            for crypto in active_cryptos:
                crypto_name = crypto['name']
                crypto_symbol = crypto['symbol']
                
                # Balance depuis account (déjà récupéré)
                crypto_balance = 0.0
                for balance in account['balances']:
                    if balance['asset'] == crypto_name:
                        crypto_balance = float(balance['free']) + float(balance['locked'])
                        break
                
                crypto_balances[crypto_name] = crypto_balance
                
                # Prix depuis le batch
                crypto_price = price_dict.get(crypto_symbol, 0.0)
                crypto_prices[crypto_symbol] = crypto_price
                
                if crypto_balance > 0 and crypto_price > 0:
                    crypto_value = crypto_balance * crypto_price
                    total_portfolio_value += crypto_value
            
            self._current_portfolio_value = total_portfolio_value
            
            portfolio_data = {
                'total_value': total_portfolio_value,
                'crypto_balances': crypto_balances,
                'crypto_prices': crypto_prices,
                'active_cryptos': active_cryptos,  # Stocké pour éviter les recharges
                'usdc_free': usdc_free
            }
            
            # Log uniquement les cryptos avec valeur significative
            significant_holdings = []
            for crypto in active_cryptos:
                name = crypto['name']
                balance = crypto_balances.get(name, 0)
                price = crypto_prices.get(crypto['symbol'], 0)
                value = balance * price
                if value > 1.0:  # Plus de 1 USDC
                    significant_holdings.append(f"{name}: {balance:.8f} ({value:.2f} USDC)")
            
            if significant_holdings:
                self.logger.info(f"💰 Holdings significatifs: {', '.join(significant_holdings[:5])}...")  # Max 5
            
            self.logger.info(f"💰 Valeur portefeuille: {total_portfolio_value:.2f} USDC")
            
            return account, portfolio_data
            
        except Exception as e:
            self.logger.error(f"❌ Erreur calcul portfolio global: {e}")
            import traceback
            self.logger.debug(traceback.format_exc())
            return None, None

    def _process_crypto_trading_optimized(self, crypto_config: Dict[str, Any], account: Dict, portfolio_data: Dict) -> bool:
        """Version ultra-optimisée - utilise les données pré-calculées (PAS d'API calls)"""
        try:
            symbol = crypto_config['symbol']
            name = crypto_config['name']
            profit_target = crypto_config.get('profit_percentage', 3.0)
            max_allocation = crypto_config.get('max_allocation', 0.1)
            
            self.logger.info(f"🎯 === ANALYSE {name} ({symbol}) ===")
            
            # 1. DONNÉES DÉJÀ CALCULÉES (0 API calls!)
            current_crypto_balance = portfolio_data['crypto_balances'].get(name, 0.0)
            current_crypto_price = portfolio_data['crypto_prices'].get(symbol, 0.0)
            total_portfolio_value = portfolio_data['total_value']
            
            if current_crypto_price == 0:
                self.logger.warning(f"⚠️  Prix non trouvé pour {symbol}")
                return False
            
            current_crypto_value_usdc = current_crypto_balance * current_crypto_price
            
            # 2. ALLOCATION (calculs simples, pas d'API)
            target_allocation_usdc = total_portfolio_value * max_allocation
            missing_allocation_usdc = max(0, target_allocation_usdc - current_crypto_value_usdc)
            
            self.logger.info(f"📊 Allocation {name}:")
            self.logger.info(f"   💰 Valeur actuelle: {current_crypto_value_usdc:.2f} USDC ({current_crypto_balance:.8f} {name})")
            self.logger.info(f"   🎯 Allocation cible: {target_allocation_usdc:.2f} USDC ({max_allocation*100:.1f}%)")
            self.logger.info(f"   📈 Manquant: {missing_allocation_usdc:.2f} USDC")
            
            # 3. VÉRIFICATION RAPIDE
            if missing_allocation_usdc < 10:
                self.logger.info(f"✅ {name} : Allocation suffisante ({current_crypto_value_usdc:.0f}/{target_allocation_usdc:.0f} USDC)")
                return False
            
            # 4. CALCUL INVESTISSEMENT (rapide)
            trading_config = self.portfolio_manager.get_trading_config()
            max_investment = min(
                trading_config.get('max_trade_amount', 165),
                self._current_usdc_balance * 0.25,
                missing_allocation_usdc,
                self._current_usdc_balance - trading_config.get('min_balance_reserve', 21)
            )
            
            if max_investment < 10:
                if self._current_usdc_balance < trading_config.get('min_balance_reserve', 21):
                    self.logger.info(f"⚠️  Solde insuffisant pour {name}")
                else:
                    self.logger.info(f"⚠️  Montant d'achat trop faible: {max_investment:.2f} USDC")
                return False
            
            self.logger.info(f"💵 Montant d'investissement: {max_investment:.2f} USDC (manquant: {missing_allocation_usdc:.0f})")
            
            # 5. SIGNAL TRADING RSI (seul signal de décision)
            should_buy, buy_reason = self.trading_engine.should_buy(symbol, current_crypto_price)
            
            # 📊 LOGS INFORMATIFS DES AUTRES INDICATEURS (pas de décision)
            self._log_technical_indicators_info(symbol, name, current_crypto_price)
            
            if should_buy:
                self.logger.info(f"🛒 Signal d'achat RSI: {buy_reason}")
                return self._execute_buy_and_sell_logic(symbol, name, max_investment, profit_target)
            else:
                self.logger.info(f"⏸️  Pas d'achat pour {name}: {buy_reason}")
                return False
            
        except Exception as e:
            self.logger.error(f"❌ Erreur traitement optimisé {crypto_config.get('name', 'UNKNOWN')}: {e}")
            return False
    
    def _log_technical_indicators_info(self, symbol: str, name: str, current_price: float):
        """Log les indicateurs techniques à titre informatif (pas de décision)"""
        try:
            # Récupérer les données pour analyse (rapide - déjà optimisé)
            klines = self.binance_client._make_request_with_retry(
                self.binance_client.client.get_klines,
                symbol=symbol,
                interval='1h',
                limit=100
            )
            
            if not klines or len(klines) < 50:
                self.logger.debug(f"📊 {name}: Données insuffisantes pour indicateurs avancés")
                return
            
            # Analyse complète (utilise les indicateurs existants)
            analysis = self.indicators.comprehensive_analysis(klines)
            
            if 'error' in analysis:
                self.logger.debug(f"📊 {name}: Erreur calcul indicateurs - {analysis['error']}")
                return
            
            # RSI (déjà calculé mais on l'affiche)
            rsi = analysis.get('rsi', 0)
            
            # MACD
            macd = analysis.get('macd', {})
            macd_signal = macd.get('signal', 'hold')
            macd_crossover = "🎯 CROISEMENT!" if macd.get('crossover', False) else ""
            
            # Bollinger
            bollinger = analysis.get('bollinger', {})
            bb_position = bollinger.get('position', 'middle')
            bb_squeeze = "🎯 SQUEEZE!" if bollinger.get('squeeze', False) else ""
            
            # Stochastic
            stoch = analysis.get('stochastic', {})
            stoch_signal = stoch.get('signal', 'hold')
            
            # Signal composite
            composite = analysis.get('composite_signal', {})
            composite_signal = composite.get('signal', 'hold')
            confidence = composite.get('confidence', 0) * 100
            
            # 📊 LOG COMPACT DES INDICATEURS
            self.logger.info(f"📊 Indicateurs {name}:")
            self.logger.info(f"   📈 RSI: {rsi:.1f} | MACD: {macd_signal} {macd_crossover}")
            self.logger.info(f"   📊 Bollinger: {bb_position} {bb_squeeze} | Stoch: {stoch_signal}")
            self.logger.info(f"   🎯 Composite: {composite_signal} ({confidence:.0f}% conf)")
            
            # 🔍 SIGNAUX REMARQUABLES
            remarkable_signals = []
            if macd.get('crossover', False):
                remarkable_signals.append("MACD croisement haussier")
            if bollinger.get('squeeze', False):
                remarkable_signals.append("Bollinger squeeze (volatilité à venir)")
            if stoch_signal == 'oversold':
                remarkable_signals.append("Stochastic survente")
            if confidence > 80:
                remarkable_signals.append(f"Signal composite très fort ({confidence:.0f}%)")
            
            if remarkable_signals:
                self.logger.info(f"   ⭐ Signaux notables: {' | '.join(remarkable_signals)}")
                
        except Exception as e:
            self.logger.debug(f"❌ Erreur log indicateurs {name}: {e}")
    
    def _execute_buy_and_sell_logic(self, symbol: str, name: str, max_investment: float, profit_target: float) -> bool:
        """Exécute la logique d'achat et de vente avec liaison OCO"""
        try:
            self.logger.info(f"🛒 Signal d'achat détecté pour {name}")
            self.logger.info(f"💵 Montant d'investissement: {max_investment:.2f} USDC")
            
            # Exécuter l'achat
            buy_result = self.trading_engine.execute_buy_order(symbol, max_investment)
            
            if not buy_result['success']:
                self.logger.error(f"❌ Échec {'simulation' if self.dry_run else 'achat'}: {buy_result.get('error')}")
                return False
            
            buy_price = buy_result['price']
            quantity = buy_result['quantity']
            
            # 🔗 RÉCUPÉRER L'ID DE TRANSACTION D'ACHAT (si mode réel)
            buy_transaction_id = None
            if not self.dry_run and 'order' in buy_result:
                try:
                    # Petite pause pour s'assurer que la transaction est en base
                    time.sleep(0.3)  # Réduit de 0.5 à 0.3s
                    
                    with self.trading_engine.database.get_connection() as conn:
                        cursor = conn.execute("""
                            SELECT id FROM transactions 
                            WHERE order_id = ? AND order_side = 'BUY' 
                            ORDER BY created_at DESC LIMIT 1
                        """, (buy_result['order']['orderId'],))
                        result = cursor.fetchone()
                        if result:
                            buy_transaction_id = result[0]
                            self.logger.debug(f"🔗 ID transaction d'achat récupéré: {buy_transaction_id}")
                except Exception as e:
                    self.logger.debug(f"Impossible de récupérer l'ID transaction achat: {e}")
            
            self.logger.info(f"✅ {'Simulation' if self.dry_run else 'Achat'} réussi, placement ordre OCO (+{profit_target}%)")
            
            # Placement de l'ordre OCO/limite avec liaison
            sell_result = self.trading_engine.execute_sell_order_with_stop_loss(
                symbol, 
                quantity, 
                buy_price, 
                profit_target,
                buy_transaction_id=buy_transaction_id  # 🔗 LIAISON !
            )
            
            if not sell_result['success']:
                self.logger.error(f"❌ Échec placement ordre: {sell_result.get('error')}")
                return False
            
            # Log des résultats
            self._log_sell_order_results(sell_result, name)
            
            # Mise à jour du solde USDC pour les prochains calculs
            self._current_usdc_balance -= max_investment
            
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Erreur logique achat/vente {symbol}: {e}")
            return False
    
    def _log_sell_order_results(self, sell_result: Dict, name: str):
        """Log les résultats de l'ordre de vente"""
        try:
            if 'kept_quantity' in sell_result and sell_result['kept_quantity'] > 0:
                self.logger.info(f"💎 Cryptos gardées: {sell_result['kept_quantity']:.8f} {name}")
            
            order_type = sell_result.get('order_type', 'UNKNOWN')
            
            if order_type == 'OCO':
                self.logger.info(f"✅ Ordre OCO {'simulé' if self.dry_run else 'placé'}")
                self.logger.info(f"   🎯 Profit: {sell_result['target_price']:.6f} USDC")
                self.logger.info(f"   🛡️  Stop: {sell_result['stop_price']:.6f} USDC")
                
            elif order_type == 'LIMIT':
                self.logger.info(f"✅ Ordre limite {'simulé' if self.dry_run else 'placé'} à {sell_result['target_price']:.6f} USDC")
                
            elif order_type == 'OCO_SIMULATION':
                self.logger.info(f"🧪 Ordre OCO simulé")
                
            else:
                self.logger.info(f"✅ Ordre {'simulé' if self.dry_run else 'placé'}")
                
        except Exception as e:
            self.logger.debug(f"❌ Erreur log résultats: {e}")
    
    def _post_cycle_cleanup(self):
        """Nettoyage post-cycle"""
        try:
            # Réduction de l'usage mémoire
            RaspberryPiOptimizer.reduce_memory_usage()
            
            # Nettoyage périodique de la base (tous les 10 cycles)
            if self.cycle_count % 10 == 0:
                self.logger.debug("🧹 Nettoyage périodique de la base de données...")
                self.database.cleanup_old_transactions()
            
            # Log des statistiques système (tous les 5 cycles)
            if self.cycle_count % 5 == 0:
                system_info = get_system_info()
                self.logger.debug(f"🍓 Statistiques système: {system_info}")
                
        except Exception as e:
            self.logger.debug(f"❌ Erreur nettoyage post-cycle: {e}")
    
    def get_trading_summary(self) -> Dict[str, Any]:
        """Retourne un résumé des activités de trading"""
        try:
            return {
                'cycles_executed': self.cycle_count,
                'mode': 'simulation' if self.dry_run else 'real',
                'portfolio_value': getattr(self, '_current_portfolio_value', 0),
                'usdc_balance': getattr(self, '_current_usdc_balance', 0),
                'active_positions': len(getattr(self, 'active_positions', {})),
                'last_run': datetime.now().isoformat(),
                'statistics': self.database.get_quick_stats()
            }
        except Exception as e:
            return {'error': str(e)}
    
    def shutdown_gracefully(self):
        """Arrêt propre du bot"""
        try:
            self.logger.info("🛑 Arrêt propre du bot en cours...")
            
            # Enregistrer les statistiques finales
            summary = self.get_trading_summary()
            
            self.logger.info(f"✅ Bot arrêté proprement - {summary.get('cycles_executed', 0)} cycles exécutés")
            
        except Exception as e:
            self.logger.error(f"❌ Erreur arrêt: {e}")

