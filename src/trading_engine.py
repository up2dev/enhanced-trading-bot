import logging
import time
from typing import Dict, List, Tuple, Optional
from decimal import Decimal, ROUND_DOWN
import numpy as np
import pandas as pd
import pandas_ta as ta
from datetime import datetime, timedelta

from .binance_client import EnhancedBinanceClient
from .database import DatabaseManager

class TradingEngine:
    def __init__(self, binance_client: EnhancedBinanceClient, database: DatabaseManager, config: Dict, dry_run: bool = False):
        self.binance_client = binance_client
        self.database = database
        self.config = config
        self.dry_run = dry_run
        self.logger = logging.getLogger(__name__)
        
        # Configuration trading
        self.trading_config = config.get('trading', {})
        self.risk_config = config.get('risk_management', {})
        self.advanced_config = config.get('advanced_strategy', {})
        
        # Cache des données avec timestamps pour éviter les recalculs
        self._rsi_cache = {}
        self._cache_duration = 60  # Cache RSI pendant 60 secondes
        
        # SÉCURITÉS COHÉRENTES
        self.max_positions_per_crypto = self.risk_config.get('max_positions_per_crypto', 10)
        
        # Cooldown entre ordres (configuration depuis le fichier)
        cooldown_minutes = self.risk_config.get('cooldown_minutes', 30)
        self.min_time_between_orders = cooldown_minutes * 60
        
        # Limite d'achats par jour
        self.max_daily_buys_global = self.risk_config.get('max_daily_trades', 50)
        
        # Log des paramètres de sécurité
        mode_text = "🧪 SIMULATION" if self.dry_run else "🔥 RÉEL"
        self.logger.info(f"⚙️  TradingEngine initialisé en mode {mode_text}")
        self.logger.info(f"🛡️  Sécurités: {self.max_positions_per_crypto} positions/crypto, {cooldown_minutes}min cooldown, {self.max_daily_buys_global} achats/jour max")

    def find_digit_position(self, num: float, digit: str = '1') -> int:
        """Trouve la position d'un chiffre dans la partie décimale (logique legacy)"""
        try:
            num_str = f"{num:.16f}".rstrip('0')
            fractional_part = num_str.split('.')[1] if '.' in num_str else num_str
            position = fractional_part.index(digit) + 1
            return position
        except (ValueError, IndexError):
            return 8

    def calculate_sell_price_limit(self, buy_price: float, profit_percentage: float) -> float:
        """Calcule le prix de vente avec la logique legacy exacte"""
        buy_price = Decimal(str(buy_price))
        buy_price *= Decimal('100000000')
        
        sell_ratio = (100 - profit_percentage) / 100
        buy_price = buy_price / Decimal(str(sell_ratio))
        buy_price = buy_price.to_integral_value(rounding=ROUND_DOWN)
        buy_price = buy_price * Decimal('0.00000001')
        
        return float(buy_price)
        
    def calculate_rsi(self, symbol: str, period: int = 14, timeframe: str = '1h') -> float:
        """Calcule le RSI avec pandas-ta"""
        try:
            cache_key = f"{symbol}_{period}_{timeframe}"
            current_time = time.time()
            
            if cache_key in self._rsi_cache:
                cached_time, cached_rsi = self._rsi_cache[cache_key]
                if current_time - cached_time < self._cache_duration:
                    self.logger.debug(f"📊 RSI {symbol} (cache): {cached_rsi:.2f}")
                    return cached_rsi
            
            limit = max(period * 3, 100)
            
            klines = self.binance_client._make_request_with_retry(
                self.binance_client.client.get_klines,
                symbol=symbol,
                interval=timeframe,
                limit=limit
            )
            
            if not klines or len(klines) < period + 1:
                self.logger.warning(f"⚠️  Pas assez de données pour calculer RSI de {symbol}")
                return 50.0
            
            df = pd.DataFrame(klines, columns=[
                'timestamp', 'open', 'high', 'low', 'close', 'volume',
                'close_time', 'quote_asset_volume', 'number_of_trades',
                'taker_buy_base_asset_volume', 'taker_buy_quote_asset_volume', 'ignore'
            ])
            
            df['close'] = pd.to_numeric(df['close'])
            df['RSI'] = ta.rsi(df['close'], length=period)
            df['RSI'] = pd.to_numeric(df['RSI'])
            
            rsi_values = df['RSI'].dropna()
            
            if len(rsi_values) == 0:
                self.logger.warning(f"⚠️  Aucune valeur RSI calculée pour {symbol}")
                return 50.0
            
            current_rsi = float(rsi_values.iloc[-1])
            
            if pd.isna(current_rsi) or current_rsi < 0 or current_rsi > 100:
                self.logger.warning(f"⚠️  Valeur RSI invalide pour {symbol}: {current_rsi}")
                return 50.0
            
            self._rsi_cache[cache_key] = (current_time, current_rsi)
            
            self.logger.debug(f"📊 RSI {symbol} (période {period}): {current_rsi:.2f}")
            return current_rsi
            
        except Exception as e:
            self.logger.error(f"❌ Erreur calcul RSI pour {symbol}: {e}")
            return 50.0
    
    def should_buy(self, symbol: str, current_price: float) -> Tuple[bool, str]:
        """Détermine s'il faut acheter une crypto"""
        try:
            rsi_period = self.trading_config.get('rsi_period', 14)
            timeframe = self.trading_config.get('timeframe', '1h')
            rsi = self.calculate_rsi(symbol, rsi_period, timeframe)
            
            first_rsi_rate = self.trading_config.get('first_rsi_rate', 35)
            second_rsi_rate = self.trading_config.get('second_rsi_rate', 30)
            rsi_oversold = self.trading_config.get('rsi_oversold', 30)
            
            reentry_rsi = second_rsi_rate if second_rsi_rate else rsi_oversold
            
            security_check, security_msg = self._check_trading_security(symbol)
            if not security_check:
                return False, security_msg
            
            position_count = self._count_active_positions(symbol)
            
            if position_count == 0:
                if rsi <= first_rsi_rate:
                    return True, f"🥇 Premier achat - RSI favorable ({rsi:.2f} <= {first_rsi_rate})"
                else:
                    return False, f"RSI trop élevé pour premier achat ({rsi:.2f} > {first_rsi_rate})"
                    
            elif position_count < self.max_positions_per_crypto:
                if rsi <= reentry_rsi:
                    return True, f"🔄 Rachat #{position_count + 1} - RSI très bas ({rsi:.2f} <= {reentry_rsi})"
                else:
                    return False, f"Position #{position_count} active, RSI pas assez bas pour racheter ({rsi:.2f} > {reentry_rsi})"
            else:
                return False, f"🛑 Maximum {self.max_positions_per_crypto} positions atteint pour {symbol}"
            
        except Exception as e:
            self.logger.error(f"❌ Erreur analyse achat {symbol}: {e}")
            return False, f"Erreur d'analyse: {e}"
    
    def _check_trading_security(self, symbol: str) -> Tuple[bool, str]:
        """Vérifications de sécurité avec PERSISTANCE EN BASE"""
        try:
            # 1. COOLDOWN depuis la base de données (PERSISTANT entre exécutions)
            last_order_time = self._get_last_order_time_from_db(symbol)
            current_time = time.time()
            
            if last_order_time and (current_time - last_order_time) < self.min_time_between_orders:
                remaining = int(self.min_time_between_orders - (current_time - last_order_time))
                self.logger.debug(f"⏰ Dernier ordre {symbol}: {datetime.fromtimestamp(last_order_time).strftime('%H:%M:%S')}")
                return False, f"⏰ Cooldown {symbol} (reste {remaining // 60}min {remaining % 60}s)"
            
            # 2. LIMITE GLOBALE d'achats par jour
            daily_buys_global = self._get_daily_buys_count_global()
            
            if daily_buys_global >= self.max_daily_buys_global:
                return False, f"🚫 Limite journalière globale atteinte ({daily_buys_global}/{self.max_daily_buys_global} achats)"
            
            # 3. ALERTE si approche limite
            if daily_buys_global >= self.max_daily_buys_global * 0.8:
                remaining = self.max_daily_buys_global - daily_buys_global
                self.logger.warning(f"⚠️  Limite journalière globale: {daily_buys_global}/{self.max_daily_buys_global} ({remaining} restants)")
            
            return True, "Sécurité OK"
            
        except Exception as e:
            return False, f"Erreur sécurité: {e}"
    
    def _get_last_order_time_from_db(self, symbol: str) -> Optional[float]:
        """Récupère le timestamp du dernier ordre depuis la DB (PERSISTANT)"""
        try:
            last_time = self.database.get_last_buy_time(symbol)
            if last_time:
                self.logger.debug(f"🔍 Dernier achat {symbol}: {datetime.fromtimestamp(last_time).strftime('%Y-%m-%d %H:%M:%S')}")
            return last_time
        except Exception as e:
            self.logger.error(f"❌ Erreur récupération dernier ordre {symbol}: {e}")
            return None
    
    def _count_active_positions(self, symbol: str) -> int:
        """Compte le nombre de POSITIONS logiques (basé sur orderListId)"""
        try:
            open_orders = self.binance_client._make_request_with_retry(
                self.binance_client.client.get_open_orders,
                symbol=symbol
            )
        
            sell_orders = [order for order in open_orders if order['side'] == 'SELL']
        
            if not sell_orders:
                return 0
        
            # 🎯 LOGIQUE CORRECTE basée sur orderListId
            oco_orders = set()  # Utiliser set pour éviter doublons
            limit_simple_orders = 0
        
            for order in sell_orders:
                order_list_id = order.get('orderListId', -1)
            
                if order_list_id != -1:
                    # C'est un ordre OCO (orderListId positif)
                    oco_orders.add(order_list_id)  # Set évite les doublons automatiquement
                else:
                    # C'est un ordre LIMIT simple (orderListId = -1)
                    limit_simple_orders += 1
        
            total_positions = len(oco_orders) + limit_simple_orders
        
            if total_positions > 0:
                self.logger.debug(f"📊 {symbol}: {total_positions} position(s) logiques ({len(oco_orders)} OCO + {limit_simple_orders} LIMIT)")
        
            return total_positions
        
        except Exception as e:
            self.logger.error(f"❌ Erreur comptage positions {symbol}: {e}")
            return len(sell_orders)  # Fallback sécuritaire

    def _get_daily_buys_count_global(self) -> int:
        """Compte TOUS les achats du jour"""
        return self.database.get_daily_buy_count()
    
    def log_trading_stats(self):
        """Log les statistiques de trading avec OCO"""
        try:
            # Stats rapides depuis la DB
            stats = self.database.get_quick_stats()
            daily_buys = stats.get('daily_buys', 0)
            active_oco = stats.get('active_oco', 0)
            
            self.logger.info("📊 === STATISTIQUES DE TRADING ===")
            self.logger.info(f"🌍 Achats aujourd'hui: {daily_buys}/{self.max_daily_buys_global} ({self.max_daily_buys_global - daily_buys} restants)")
            self.logger.info(f"🎯 Ordres OCO actifs: {active_oco}")
            
            # Positions par crypto via Binance API
            active_cryptos = self.config.get('cryptos', {})
            total_positions = 0
            
            for name, crypto_config in active_cryptos.items():
                if not crypto_config.get('active', False):
                    continue
                
                symbol = crypto_config.get('symbol')
                if symbol:
                    positions = self._count_active_positions(symbol)
                    if positions > 0:
                        self.logger.info(f"📈 {symbol}: {positions}/{self.max_positions_per_crypto} positions actives")
                        total_positions += positions
            
            if total_positions == 0:
                self.logger.info("✅ Aucune position active actuellement")
            else:
                self.logger.info(f"📊 Total positions API: {total_positions}")
                
            self.logger.info("=" * 40)
            
        except Exception as e:
            self.logger.error(f"❌ Erreur log statistiques: {e}")
    
    def execute_buy_order(self, symbol: str, usdc_amount: float) -> Dict:
        """Exécute un ordre d'achat avec gestion COMPLÈTE des fills multiples"""
        try:
            ticker = self.binance_client._make_request_with_retry(
                self.binance_client.client.get_symbol_ticker,
                symbol=symbol
            )
            current_price = float(ticker['price'])
            quantity = usdc_amount / current_price
        
            # Timestamp pour le cooldown
            order_timestamp = int(time.time() * 1000)  # Timestamp en millisecondes pour cohérence
        
            if self.dry_run:
                self.logger.info(f"🧪 SIMULATION ACHAT {symbol}: {quantity:.8f} à {current_price:.6f} USDC")
            
                # Enregistrer en simulation pour tester le cooldown
                self.database.insert_transaction(
                    symbol=symbol,
                    order_id=f'SIMULATION_{order_timestamp}',
                    transact_time=str(order_timestamp),
                    order_type='MARKET',
                    order_side='BUY',
                    price=current_price,
                    qty=quantity,
                    commission=0.0,
                    commission_asset='USDC'
                )
            
                return {
                    'success': True,
                    'order': {'orderId': f'SIMULATION_{order_timestamp}', 'executedQty': str(quantity)},
                    'price': current_price,
                    'quantity': quantity,
                    'simulation': True
                }
        
            # ACHAT RÉEL avec validation des filtres
            symbol_info = self.binance_client._make_request_with_retry(
                self.binance_client.client.get_symbol_info,
                symbol=symbol
            )
        
            lot_size_filter = next(f for f in symbol_info['filters'] if f['filterType'] == 'LOT_SIZE')
            min_qty = float(lot_size_filter['minQty'])
            max_qty = float(lot_size_filter['maxQty'])
            step_size = float(lot_size_filter['stepSize'])
        
            quantity = min(max(quantity, min_qty), max_qty)
            quantity -= quantity % step_size
            quantity = round(quantity, 8)
        
            self.logger.info(f"💰 ACHAT RÉEL {symbol}: {quantity:.8f} à ~{current_price:.6f} USDC")
        
            order = self.binance_client._make_request_with_retry(
                self.binance_client.client.order_market_buy,
                symbol=symbol,
                quantity=quantity
            )
        
            # 🔥 GESTION COMPLÈTE DES FILLS MULTIPLES (CORRECTION MAJEURE!)
            total_quantity = 0.0
            total_value = 0.0
            total_commission = 0.0
            commission_asset = 'USDC'  # Par défaut
            fills_count = 0
        
            if 'fills' in order and order['fills']:
                fills = order['fills']
                fills_count = len(fills)
            
                self.logger.info(f"📊 Ordre exécuté en {fills_count} fill(s):")
            
                for i, fill in enumerate(fills):
                    fill_price = float(fill.get('price', 0))
                    fill_qty = float(fill.get('qty', 0))
                    fill_commission = float(fill.get('commission', 0))
                    fill_commission_asset = fill.get('commissionAsset', 'USDC')
                
                    # Accumuler
                    total_quantity += fill_qty
                    total_value += fill_price * fill_qty
                
                    # Commission (garder l'asset de la première commission non-nulle)
                    if fill_commission > 0:
                        if total_commission == 0:  # Premier commission
                            commission_asset = fill_commission_asset
                    
                        # Si même asset, additionner
                        if fill_commission_asset == commission_asset:
                            total_commission += fill_commission
                        else:
                            # Assets différents : garder la plus importante ou convertir
                            self.logger.warning(f"⚠️  Commissions en assets différents: {fill_commission_asset} vs {commission_asset}")
                            # Pour simplifier, on garde la première
                            if total_commission == 0:
                                total_commission = fill_commission
                                commission_asset = fill_commission_asset
                
                    # Log détaillé des fills (max 5 pour pas spam)
                    if i < 5:
                        self.logger.info(f"   Fill {i+1}: {fill_qty:.8f} @ {fill_price:.6f} (comm: {fill_commission:.8f} {fill_commission_asset})")
                    elif i == 5:
                        self.logger.info(f"   ... et {fills_count - 5} autres fills")
            
                # Calculer le prix moyen pondéré
                average_price = total_value / total_quantity if total_quantity > 0 else current_price
            
                # Logs récapitulatifs
                self.logger.info(f"✅ RÉCAPITULATIF {symbol}:")
                self.logger.info(f"   📊 {fills_count} fills = {total_quantity:.8f} {symbol.replace('USDC', '')}")
                self.logger.info(f"   💰 Prix moyen: {average_price:.6f} USDC")
                self.logger.info(f"   💸 Commission totale: {total_commission:.8f} {commission_asset}")
                self.logger.info(f"   💵 Valeur totale: {total_value:.2f} USDC")
            
            else:
                # Fallback si pas de fills (ne devrait pas arriver)
                total_quantity = quantity
                total_value = current_price * quantity
                average_price = current_price
                self.logger.warning(f"⚠️  Aucun fill détecté, utilisation des valeurs estimées")
        
            # 🔥 CONVERSION COMMISSION BNB (si nécessaire)
            if commission_asset == 'BNB' and total_commission > 0:
                try:
                    bnb_ticker = self.binance_client._make_request_with_retry(
                        self.binance_client.client.get_symbol_ticker,
                        symbol='BNBUSDC'
                    )
                    bnb_price = float(bnb_ticker['price'])
                    commission_usdc_value = total_commission * bnb_price
                
                    self.logger.info(f"💰 Commission BNB: {total_commission:.8f} BNB = ~{commission_usdc_value:.6f} USDC")
                
                except Exception as e:
                    self.logger.warning(f"⚠️  Erreur conversion BNB: {e}")
        
            # 🔥 ENREGISTRER AVEC LES VRAIES DONNÉES TOTALES
            self.database.insert_transaction(
                symbol=symbol,
                order_id=str(order['orderId']),
                transact_time=str(order.get('transactTime', order_timestamp)),
                order_type=order['type'],
                order_side=order['side'],
                price=average_price,        # ✅ Prix moyen pondéré de TOUS les fills
                qty=total_quantity,         # ✅ Quantité totale de TOUS les fills  
                commission=total_commission, # ✅ Commission totale de TOUS les fills
                commission_asset=commission_asset
            )
        
            return {
                'success': True,
                'order': order,
                'price': average_price,     # Prix moyen pondéré
                'quantity': total_quantity, # Quantité totale réelle
                'commission': total_commission,
                'commission_asset': commission_asset,
                'fills_count': fills_count,
                'total_value': total_value,
                'simulation': False
            }
        
        except Exception as e:
            self.logger.error(f"❌ Erreur ordre d'achat {symbol}: {e}")
            import traceback
            self.logger.debug(traceback.format_exc())
            return {'success': False, 'error': str(e)}

    def execute_sell_order_with_stop_loss(self, symbol: str, bought_quantity: float, buy_price: float, profit_target: float, buy_transaction_id: int = None) -> Dict:
        """Exécute un ordre OCO avec profit + stop-loss + INSERTION EN BASE"""
        try:
            # Configuration des ordres
            future_transfer_enabled = self.advanced_config.get('future_transfer_enabled', True)
            use_oco_orders = self.risk_config.get('use_oco_orders', True)
            stop_loss_percentage = self.risk_config.get('stop_loss_percentage', -8.0)
            
            # 🔥 CORRECTION COMPLÈTE: Logique "récupérer investissement initial"
            if future_transfer_enabled:
                # Prix de vente cible
                target_price = self.calculate_sell_price_limit(buy_price, profit_target)

                # 🔍 RÉCUPÉRER LES FILTRES DYNAMIQUES DEPUIS BINANCE
                try:
                    symbol_info = self.binance_client._make_request_with_retry(
                        self.binance_client.client.get_symbol_info,
                        symbol=symbol
                    )

                    # Extraire les filtres importants
                    notional_filter = None
                    lot_size_filter = None

                    for f in symbol_info['filters']:
                        if f['filterType'] == 'NOTIONAL':
                            notional_filter = f
                        elif f['filterType'] == 'LOT_SIZE':
                            lot_size_filter = f

                    # Valeurs par défaut si filtres non trouvés
                    min_notional = float(notional_filter.get('minNotional', 5.0)) if notional_filter else 5.0
                    step_size = float(lot_size_filter.get('stepSize', 0.00000001)) if lot_size_filter else 0.00000001

                    self.logger.debug(f"🔍 Filtres {symbol}:")
                    self.logger.debug(f"   NOTIONAL min: {min_notional} USDC")
                    self.logger.debug(f"   LOT_SIZE step: {step_size}")

                except Exception as filter_error:
                    self.logger.warning(f"⚠️  Erreur récupération filtres {symbol}: {filter_error}")
                    # Valeurs de sécurité
                    min_notional = 10.0  # Sécurité plus haute
                    step_size = 0.00000001

                # STRATÉGIE: Récupérer l'investissement initial en USDC
                initial_investment_usdc = bought_quantity * buy_price

                # Calculer combien vendre pour récupérer l'investissement
                sell_quantity_for_investment = initial_investment_usdc / target_price

                # Vérifier que ça respecte NOTIONAL minimum
                min_sell_quantity_notional = min_notional / target_price

                # Prendre le maximum pour respecter NOTIONAL
                sell_quantity_raw = max(sell_quantity_for_investment, min_sell_quantity_notional)

                # Arrondir selon LOT_SIZE step_size
                qty_precision = max(0, -int(np.log10(step_size)))
                sell_quantity = round(sell_quantity_raw / step_size) * step_size
                sell_quantity = round(sell_quantity, qty_precision)

                # S'assurer qu'on ne vend pas plus que ce qu'on a
                sell_quantity = min(sell_quantity, bought_quantity * 0.99)  # Max 99%

                # Le reste = profit pur en crypto
                kept_quantity = bought_quantity - sell_quantity

                # Vérification finale
                final_notional = sell_quantity * target_price
                recovered_usdc = final_notional
                profit_crypto = kept_quantity
                profit_usdc_equivalent = profit_crypto * target_price

                self.logger.info(f"🎯 STRATÉGIE: Récupérer investissement initial")
                self.logger.info(f"   💰 Investissement initial: {initial_investment_usdc:.2f} USDC")
                self.logger.info(f"   📈 Prix vente: {target_price:.6f} USDC")
                self.logger.info(f"   📊 Quantité théorique: {sell_quantity_for_investment:.8f}")
                self.logger.info(f"   📏 Quantité NOTIONAL-safe: {sell_quantity:.{qty_precision}f}")
                self.logger.info(f"   💵 Valeur finale: {final_notional:.2f} USDC ({final_notional/min_notional:.1f}x NOTIONAL min)")
                self.logger.info(f"   🏪 À vendre: {sell_quantity:.{qty_precision}f} → récupère {recovered_usdc:.2f} USDC")
                self.logger.info(f"   💎 À garder: {kept_quantity:.8f} → profit {profit_usdc_equivalent:.2f} USDC équivalent")

                # Alertes de sécurité
                if final_notional < min_notional:
                    self.logger.error(f"❌ NOTIONAL encore insuffisant: {final_notional:.2f} < {min_notional:.2f}")
                    return {'success': False, 'error': f'Impossible de respecter NOTIONAL minimum {min_notional} USDC'}

                if sell_quantity >= bought_quantity * 0.95:
                    self.logger.warning(f"⚠️  Vente élevée: {(sell_quantity/bought_quantity)*100:.1f}% (accumulation faible)")

            else:
                # Mode classique : vendre tout
                sell_quantity = bought_quantity
                kept_quantity = 0
                target_price = buy_price * (1 + profit_target / 100)
            
            # Prix stop-loss
            stop_price = buy_price * (1 + stop_loss_percentage / 100)
            stop_limit_buffer = self.risk_config.get('stop_limit_buffer', 0.001)
            stop_limit_price = stop_price * (1 - stop_limit_buffer)
            
            # Informations du symbole pour formatage
            symbol_info = self.binance_client._make_request_with_retry(
                self.binance_client.client.get_symbol_info,
                symbol=symbol
            )
            
            tick_size = float(next(f for f in symbol_info['filters'] if f['filterType'] == 'PRICE_FILTER')['tickSize'])
            step_size = float(next(f for f in symbol_info['filters'] if f['filterType'] == 'LOT_SIZE')['stepSize'])
            
            # Formatage précis avec gestion complète des précisions
            price_precision = max(0, -int(np.log10(tick_size)))
            qty_precision = max(0, -int(np.log10(step_size)))

            # Prix formatés
            target_price = round(target_price / tick_size) * tick_size
            stop_price = round(stop_price / tick_size) * tick_size
            stop_limit_price = round(stop_limit_price / tick_size) * tick_size

            # 🔧 CORRECTION: Quantité formatée avec précision exacte
            sell_quantity = round(sell_quantity / step_size) * step_size
            sell_quantity = round(sell_quantity, qty_precision)

            # Debug pour vérification
            self.logger.debug(f"🔧 Formatage {symbol}:")
            self.logger.debug(f"   Tick size: {tick_size} -> Prix précision: {price_precision}")
            self.logger.debug(f"   Step size: {step_size} -> Qty précision: {qty_precision}")
            self.logger.debug(f"   Quantité finale: {sell_quantity:.{qty_precision}f}")
            
            self.logger.info(f"🔄 Future transfer: {'Activé' if future_transfer_enabled else 'Désactivé'}")
            if future_transfer_enabled:
                self.logger.info(f"   📦 Quantité achetée: {bought_quantity:.8f}")
                self.logger.info(f"   🏪 Quantité à vendre: {sell_quantity:.8f} ({(sell_quantity/bought_quantity)*100:.1f}%)")
                self.logger.info(f"   💎 Quantité gardée: {kept_quantity:.8f} ({(kept_quantity/bought_quantity)*100:.1f}%)")
            
            self.logger.info(f"📊 ORDRE OCO {symbol}:")
            self.logger.info(f"   🎯 Profit: {target_price:.{price_precision}f} (+{profit_target}%)")
            self.logger.info(f"   🛡️  Stop-Loss: {stop_price:.{price_precision}f} ({stop_loss_percentage}%)")
            self.logger.info(f"   🛡️  Stop-Limit: {stop_limit_price:.{price_precision}f}")
            
            if self.dry_run:
                return {
                    'success': True,
                    'order_type': 'OCO_SIMULATION',
                    'target_price': target_price,
                    'stop_price': stop_price,
                    'quantity': sell_quantity,
                    'kept_quantity': kept_quantity,
                    'simulation': True
                }
            
            # ORDRE OCO RÉEL avec insertion en base
            if use_oco_orders:
                try:
                    oco_order = self.binance_client._make_request_with_retry(
                        self.binance_client.client.create_oco_order,
                        symbol=symbol,
                        side='SELL',
                        quantity=sell_quantity,
                        price=f"{target_price:.{price_precision}f}",
                        stopPrice=f"{stop_price:.{price_precision}f}",
                        stopLimitPrice=f"{stop_limit_price:.{price_precision}f}",
                        stopLimitTimeInForce='GTC'
                    )
                    
                    self.logger.info(f"✅ ORDRE OCO PLACÉ {symbol}")
                    
                    # 🔥 EXTRACTION AMÉLIORÉE DES IDs D'ORDRES
                    profit_order_id = None
                    stop_order_id = None
                    oco_order_list_id = oco_order.get('orderListId', '')
                    
                    self.logger.debug(f"🔍 OCO Response: orderListId={oco_order_list_id}")
                    
                    orders = oco_order.get('orders', [])
                    self.logger.debug(f"🔍 Orders in OCO: {len(orders)}")
                    
                    for i, order in enumerate(orders):
                        order_id = order.get('orderId')
                        order_type = order.get('type')
                        order_side = order.get('side', '')
                        
                        self.logger.debug(f"   Order {i+1}: ID={order_id}, Type={order_type}, Side={order_side}")
                        
                        if order_type == 'LIMIT_MAKER':
                            profit_order_id = order_id
                            self.logger.info(f"   📈 Limite profit: {profit_order_id}")
                        elif order_type == 'STOP_LOSS_LIMIT':
                            stop_order_id = order_id 
                            self.logger.info(f"   🛡️  Stop-loss: {stop_order_id}")
                        else:
                            self.logger.warning(f"   ❓ Type d'ordre inattendu: {order_type}")
                    
                    # Vérification finale
                    if not profit_order_id:
                        self.logger.warning(f"⚠️  PROFIT_ORDER_ID non trouvé dans la réponse OCO !")
                    if not stop_order_id:
                        self.logger.warning(f"⚠️  STOP_ORDER_ID non trouvé dans la réponse OCO !")
                    
                    # 🔥 INSERTION EN BASE (PARTIE CRUCIALE!)
                    try:
                        oco_db_id = self.database.insert_oco_order(
                            symbol=symbol,
                            oco_order_id=str(oco_order_list_id),
                            profit_order_id=str(profit_order_id) if profit_order_id else '',
                            stop_order_id=str(stop_order_id) if stop_order_id else '',
                            buy_transaction_id=buy_transaction_id or 0,
                            profit_target=profit_target,
                            stop_loss_price=stop_price,
                            quantity=sell_quantity,
                            kept_quantity=kept_quantity
                        )
                        
                        self.logger.info(f"💾 Ordre OCO enregistré en base (DB ID: {oco_db_id})")
                        
                    except Exception as db_error:
                        # L'ordre est placé sur Binance mais pas en base - log l'erreur
                        self.logger.error(f"❌ Erreur insertion OCO en base: {db_error}")
                        oco_db_id = None
                    
                    return {
                        'success': True,
                        'order_type': 'OCO',
                        'oco_order': oco_order,
                        'target_price': target_price,
                        'stop_price': stop_price,
                        'quantity': sell_quantity,
                        'kept_quantity': kept_quantity,
                        'oco_db_id': oco_db_id,
                        'profit_order_id': profit_order_id,
                        'stop_order_id': stop_order_id,
                        'simulation': False
                    }
                    
                except Exception as oco_error:
                    self.logger.warning(f"⚠️  Échec ordre OCO, fallback vers ordre limite: {oco_error}")
                    use_oco_orders = False
            
            if not use_oco_orders:
                # Ordre limite classique (fallback)
                limit_order = self.binance_client._make_request_with_retry(
                    self.binance_client.client.order_limit_sell,
                    symbol=symbol,
                    quantity=sell_quantity,
                    price=f"{target_price:.{price_precision}f}",
                    timeInForce='GTC'
                )
                
                self.logger.info(f"✅ ORDRE LIMITE PLACÉ {symbol}")
                self.logger.info(f"   📈 ID: {limit_order['orderId']}")
                self.logger.warning(f"⚠️  Pas de protection stop-loss (ordre limite simple)")
                
                return {
                    'success': True,
                    'order_type': 'LIMIT',
                    'order': limit_order,
                    'target_price': target_price,
                    'quantity': sell_quantity,
                    'kept_quantity': kept_quantity,
                    'simulation': False
                }
            
        except Exception as e:
            self.logger.error(f"❌ Erreur ordre {symbol}: {e}")
            import traceback
            self.logger.debug(traceback.format_exc())
            return {'success': False, 'error': str(e)}
    
    def monitor_oco_orders(self):
        """Surveillance des ordres OCO AMÉLIORÉE avec vérification robuste"""
        try:
            # Récupérer les ordres OCO actifs depuis la DB
            active_oco_orders = self.database.get_active_oco_orders()
            
            if not active_oco_orders:
                self.logger.debug("🔍 Aucun ordre OCO à surveiller")
                return
            
            self.logger.info(f"🔍 Surveillance de {len(active_oco_orders)} ordre(s) OCO actifs")
            
            updated_count = 0
            
            for oco_order in active_oco_orders:
                try:
                    # Vérification DOUBLE pour plus de fiabilité
                    was_updated = self._check_oco_status_enhanced(oco_order)
                    if was_updated:
                        updated_count += 1
                        
                except Exception as e:
                    self.logger.debug(f"Erreur vérification OCO {oco_order.get('oco_order_id', 'UNKNOWN')}: {e}")
            
            if updated_count > 0:
                self.logger.info(f"📝 {updated_count} ordre(s) OCO mis à jour")
                    
        except Exception as e:
            self.logger.error(f"❌ Erreur surveillance OCO: {e}")

    def _check_oco_status_enhanced(self, oco_order: Dict) -> bool:
        """Version améliorée de vérification OCO avec double vérification"""
        try:
            symbol = oco_order['symbol']
            profit_order_id = oco_order.get('profit_order_id')
            stop_order_id = oco_order.get('stop_order_id')
            
            # VÉRIFICATION DIRECTE des ordres individuels (plus fiable)
            for order_id, order_type in [(profit_order_id, 'PROFIT'), (stop_order_id, 'STOP')]:
                if not order_id:
                    continue
                    
                try:
                    order = self.binance_client._make_request_with_retry(
                        self.binance_client.client.get_order,
                        symbol=symbol,
                        orderId=int(order_id)
                    )
                    
                    if order['status'] == 'FILLED':
                        # Ordre exécuté ! Traiter immédiatement
                        self._handle_oco_execution_direct(oco_order, order, order_type)
                        return True
                        
                except Exception as order_error:
                    self.logger.debug(f"Erreur vérification {order_type} order {order_id}: {order_error}")
            
            return False
            
        except Exception as e:
            self.logger.error(f"❌ Erreur vérification OCO enhanced: {e}")
            return False

    def _handle_oco_execution_direct(self, oco_order: Dict, executed_order: Dict, execution_type: str):
        """🔥 VERSION CORRIGÉE - Traite l'exécution OCO avec création transaction BULLETPROOF"""
        try:
            symbol = oco_order['symbol']
            oco_order_id = oco_order['oco_order_id']
            
            exec_price = float(executed_order['price'])
            exec_qty = float(executed_order['executedQty'])
            order_id = str(executed_order['orderId'])
            
            # Déterminer le nouveau statut
            new_status = 'PROFIT_FILLED' if execution_type == 'PROFIT' else 'STOP_FILLED'
            
            # Log approprié
            if execution_type == 'PROFIT':
                self.logger.info(f"🎯 PROFIT RÉALISÉ {symbol}! Prix: {exec_price:.6f}, Qty: {exec_qty:.8f}")
                kept_qty = oco_order.get('kept_quantity', 0)
                if kept_qty > 0:
                    self.logger.info(f"   💎 Crypto gardée: {kept_qty:.8f} {symbol.replace('USDC', '')}")
            else:
                self.logger.warning(f"🛡️ STOP-LOSS DÉCLENCHÉ {symbol}! Prix: {exec_price:.6f}, Qty: {exec_qty:.8f}")
                kept_qty = oco_order.get('kept_quantity', 0)
                if kept_qty > 0:
                    self.logger.warning(f"   💎 Crypto gardée: {kept_qty:.8f} {symbol.replace('USDC', '')}")
            
            # 1. Mettre à jour la table oco_orders
            self.database.update_oco_execution(
                oco_order_id,
                new_status,
                exec_price,
                exec_qty,
                execution_type
            )
            
            # 2. 🔥 CRÉER LA TRANSACTION DE VENTE (MÉTHODE BULLETPROOF)
            try:
                # Vérifier si la transaction existe déjà - MÉTHODE SQL DIRECTE
                cursor = self.database.conn.execute(
                    "SELECT id FROM transactions WHERE order_id = ? AND order_side = 'SELL'",
                    (order_id,)
                )
                existing_tx = cursor.fetchone()
                
                if existing_tx:
                    self.logger.debug(f"   ✅ Transaction vente déjà existante (ID: {existing_tx[0]})")
                else:
                    # Créer la transaction de vente
                    self.database.insert_transaction(
                        symbol=symbol,
                        order_id=order_id,
                        transact_time=str(executed_order.get('time', int(time.time() * 1000))),
                        order_type=executed_order.get('type', 'LIMIT'),
                        order_side='SELL',  # 🎯 CRUCIAL : C'est une VENTE !
                        price=exec_price,
                        qty=exec_qty,
                        commission=float(executed_order.get('commission', 0.0)),
                        commission_asset=executed_order.get('commissionAsset', 'USDC')
                    )
                    self.logger.info(f"   📝 Transaction VENTE créée: {exec_qty:.8f} @ {exec_price:.6f}")
                    
            except Exception as tx_error:
                self.logger.error(f"❌ Erreur gestion transaction vente: {tx_error}")
                # Continuer quand même, l'OCO est mis à jour
                
            self.logger.info(f"💾 Exécution OCO {execution_type} COMPLÈTEMENT enregistrée")
            
        except Exception as e:
            self.logger.error(f"❌ Erreur traitement exécution directe: {e}")
            import traceback
            self.logger.debug(traceback.format_exc())

    def _check_oco_status(self, oco_order: Dict):
        """Vérifie le statut d'un ordre OCO sur Binance avec méthode robuste - VERSION LEGACY"""
        try:
            symbol = oco_order['symbol']
            oco_order_id = oco_order['oco_order_id']
            profit_order_id = oco_order.get('profit_order_id')
            stop_order_id = oco_order.get('stop_order_id')
            
            # 🔥 MÉTHODE 1: Vérifier via les ordres ouverts (plus fiable)
            try:
                open_orders = self.binance_client._make_request_with_retry(
                    self.binance_client.client.get_open_orders,
                    symbol=symbol
                )
                
                # Chercher nos ordres dans la liste
                profit_found = False
                stop_found = False
                oco_found = False
                
                for order in open_orders:
                    order_list_id = str(order.get('orderListId', -1))
                    order_id = str(order.get('orderId'))
                    
                    # Vérifier si c'est notre OCO
                    if order_list_id == str(oco_order_id):
                        oco_found = True
                        
                    # Vérifier les ordres individuels aussi (backup)
                    if profit_order_id and order_id == str(profit_order_id):
                        profit_found = True
                    if stop_order_id and order_id == str(stop_order_id):
                        stop_found = True
                
                if oco_found or profit_found or stop_found:
                    # OCO encore actif
                    self.logger.debug(f"📊 OCO {symbol} toujours actif (oco:{oco_found}, profit:{profit_found}, stop:{stop_found})")
                    return
                
                # OCO plus dans les ordres ouverts = exécuté !
                self.logger.info(f"🎯 OCO {symbol} n'est plus actif → Recherche dans l'historique")
                
            except Exception as open_orders_error:
                self.logger.warning(f"⚠️  Erreur vérification ordres ouverts: {open_orders_error}")
            
            # 🔥 MÉTHODE 2: Vérifier dans l'historique récent
            try:
                # Historique des dernières 24h
                yesterday = datetime.now() - timedelta(hours=24)
                start_time = int(yesterday.timestamp() * 1000)
                
                all_orders = self.binance_client._make_request_with_retry(
                    self.binance_client.client.get_all_orders,
                    symbol=symbol,
                    startTime=start_time,
                    limit=100
                )
                
                # Chercher les ordres de notre OCO
                executed_orders = []
                for order in all_orders:
                    order_list_id = str(order.get('orderListId', -1))
                    
                    if order_list_id == str(oco_order_id):
                        executed_orders.append(order)
                
                if executed_orders:
                    self.logger.info(f"📜 Trouvé {len(executed_orders)} ordres dans l'historique pour OCO {oco_order_id}")
                    
                    # Analyser les ordres exécutés
                    for order in executed_orders:
                        status = order.get('status')
                        order_type = order.get('type')
                        
                        self.logger.info(f"   - Status: {status}, Type: {order_type}")
                        
                        if status == 'FILLED':
                            # Ordre exécuté ! Traiter l'exécution
                            self._handle_oco_execution_from_history(oco_order, executed_orders)
                            return
                    
                    # Si aucun FILLED mais ordres trouvés = probablement annulés
                    self.logger.warning(f"⚠️  OCO {oco_order_id} trouvé dans l'historique mais aucun ordre FILLED")
                    self.database.update_oco_execution(oco_order_id, 'EXPIRED_OR_CANCELED', 0, 0, 'UNKNOWN')
                    
                else:
                    self.logger.warning(f"❓ OCO {oco_order_id} non trouvé dans l'historique récent")
                    
            except Exception as history_error:
                self.logger.error(f"❌ Erreur vérification historique: {history_error}")
                
        except Exception as e:
            self.logger.error(f"❌ Erreur vérification OCO {oco_order.get('symbol', 'UNKNOWN')}: {e}")

    def _handle_oco_execution(self, oco_order: Dict, binance_status: Dict):
        """Traite l'exécution d'un ordre OCO avec commissions réelles - VERSION LEGACY"""
        try:
            symbol = oco_order['symbol']
            oco_order_id = oco_order['oco_order_id']
            
            # Déterminer quel ordre s'est exécuté
            executed_order = None
            execution_type = None
            
            for order in binance_status.get('orders', []):
                if order['status'] == 'FILLED':
                    executed_order = order
                    if str(order['orderId']) == str(oco_order.get('profit_order_id', '')):
                        execution_type = 'PROFIT'
                    elif str(order['orderId']) == str(oco_order.get('stop_order_id', '')):
                        execution_type = 'STOP_LOSS'
                    break
            
            if executed_order and execution_type:
                # Prix et quantité d'exécution
                exec_price = float(executed_order['price'])
                exec_qty = float(executed_order['executedQty'])
                
                # Commission réelle (si disponible)
                commission = float(executed_order.get('commission', 0.0))
                commission_asset = executed_order.get('commissionAsset', 'USDC')
                
                # Log de l'événement
                if execution_type == 'PROFIT':
                    self.logger.info(f"🎯 PROFIT RÉALISÉ {symbol}!")
                    self.logger.info(f"   📈 Prix: {exec_price:.6f} USDC")
                    self.logger.info(f"   📦 Quantité: {exec_qty:.8f}")
                    self.logger.info(f"   💎 Crypto gardée: {oco_order.get('kept_quantity', 0):.8f} {symbol.replace('USDC', '')}")
                    if commission > 0:
                        self.logger.info(f"   💰 Commission: {commission:.8f} {commission_asset}")
                    new_status = 'PROFIT_FILLED'
                    
                elif execution_type == 'STOP_LOSS':
                    self.logger.warning(f"🛡️  STOP-LOSS DÉCLENCHÉ {symbol}")
                    self.logger.warning(f"   📉 Prix: {exec_price:.6f} USDC") 
                    self.logger.warning(f"   📦 Quantité: {exec_qty:.8f}")
                    self.logger.warning(f"   💎 Crypto gardée: {oco_order.get('kept_quantity', 0):.8f} {symbol.replace('USDC', '')}")
                    if commission > 0:
                        self.logger.warning(f"   💰 Commission: {commission:.8f} {commission_asset}")
                    new_status = 'STOP_FILLED'
                
                # Mettre à jour la DB
                self.database.update_oco_execution(
                    oco_order_id, 
                    new_status, 
                    exec_price, 
                    exec_qty, 
                    execution_type
                )
                
                # 🔥 AUSSI CRÉER LA TRANSACTION DE VENTE (AJOUT CRUCIAL)
                try:
                    # Vérifier si elle existe déjà
                    cursor = self.database.conn.execute(
                        "SELECT id FROM transactions WHERE order_id = ? AND order_side = 'SELL'",
                        (str(executed_order['orderId']),)
                    )
                    existing_tx = cursor.fetchone()
                    
                    if not existing_tx:
                        # Enregistrer la transaction de vente avec commission réelle
                        self.database.insert_transaction(
                            symbol=symbol,
                            order_id=str(executed_order['orderId']),
                            transact_time=str(executed_order.get('time', int(time.time() * 1000))),
                            order_type=executed_order.get('type', 'LIMIT'),
                            order_side='SELL',  # 🎯 VENTE
                            price=exec_price,
                            qty=exec_qty,
                            commission=commission,           # ✅ Commission réelle
                            commission_asset=commission_asset  # ✅ Asset de commission réel
                        )
                        self.logger.info(f"   📝 Transaction VENTE créée")
                        
                except Exception as tx_error:
                    self.logger.warning(f"⚠️ Erreur création transaction: {tx_error}")
                
                self.logger.info(f"💾 Exécution OCO {execution_type} enregistrée en base")
                
            else:
                self.logger.warning(f"⚠️  OCO {oco_order_id} terminé mais aucun ordre FILLED trouvé")
                # Marquer comme terminé quand même
                self.database.update_oco_execution(oco_order_id, 'COMPLETED_UNKNOWN', 0, 0, 'UNKNOWN')
                        
        except Exception as e:
            self.logger.error(f"❌ Erreur traitement exécution OCO: {e}")
            import traceback
            self.logger.debug(traceback.format_exc())

    def _handle_oco_execution_from_history(self, oco_order: Dict, executed_orders: List[Dict]):
        """🔥 VERSION CORRIGÉE - Traite l'exécution OCO depuis l'historique avec transaction"""
        try:
            symbol = oco_order['symbol']
            oco_order_id = oco_order['oco_order_id']
            
            # Trouver l'ordre FILLED
            filled_order = None
            execution_type = None
            
            for order in executed_orders:
                if order['status'] == 'FILLED':
                    filled_order = order
                    
                    # Déterminer le type d'exécution
                    order_type = order.get('type')
                    if order_type == 'LIMIT_MAKER':
                        execution_type = 'PROFIT'
                    elif order_type in ['STOP_LOSS_LIMIT', 'STOP_LOSS']:
                        execution_type = 'STOP_LOSS'
                    break
            
            if filled_order and execution_type:
                exec_price = float(filled_order['price'])
                exec_qty = float(filled_order['executedQty'])
                order_id = str(filled_order['orderId'])
                
                if execution_type == 'PROFIT':
                    self.logger.info(f"🎯 PROFIT HISTORIQUE DÉTECTÉ {symbol}!")
                    new_status = 'PROFIT_FILLED'
                else:
                    self.logger.warning(f"🛡️  STOP-LOSS HISTORIQUE DÉTECTÉ {symbol}")
                    new_status = 'STOP_FILLED'
                
                # Mettre à jour la DB
                self.database.update_oco_execution(
                    oco_order_id, 
                    new_status, 
                    exec_price, 
                    exec_qty, 
                    execution_type
                )
                
                # 🔥 CRÉER LA TRANSACTION DE VENTE (AJOUT CRUCIAL)
                try:
                    # Vérifier si elle existe déjà
                    cursor = self.database.conn.execute(
                        "SELECT id FROM transactions WHERE order_id = ? AND order_side = 'SELL'",
                        (order_id,)
                    )
                    existing_tx = cursor.fetchone()
                    
                    if not existing_tx:
                        # Enregistrer la transaction de vente
                        self.database.insert_transaction(
                            symbol=symbol,
                            order_id=order_id,
                            transact_time=str(filled_order.get('updateTime', int(time.time() * 1000))),
                            order_type=filled_order.get('type', 'LIMIT'),
                            order_side='SELL',  # 🎯 VENTE
                            price=exec_price,
                            qty=exec_qty,
                            commission=0.0,  # Historique : commission pas toujours disponible
                            commission_asset='USDC'
                        )
                        self.logger.info(f"   📝 Transaction VENTE historique créée")
                        
                except Exception as tx_error:
                    self.logger.warning(f"⚠️ Erreur création transaction historique: {tx_error}")
                
                self.logger.info(f"💾 Exécution OCO historique enregistrée")
                
        except Exception as e:
            self.logger.error(f"❌ Erreur traitement exécution historique: {e}")
