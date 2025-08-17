"""
Indicateurs techniques avancés pour le trading bot
Prêts à l'emploi pour stratégies évolutives
"""

import logging
import numpy as np
import pandas as pd
import pandas_ta as ta
from typing import Dict, List, Tuple, Optional
from datetime import datetime, timedelta

class AdvancedTechnicalIndicators:
    """Classe pour tous les indicateurs techniques"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def calculate_rsi(self, prices: List[float], period: int = 14) -> float:
        """Calcule le RSI (Relative Strength Index)"""
        try:
            if len(prices) < period + 1:
                return 50.0
            
            df = pd.DataFrame({'close': prices})
            df['RSI'] = ta.rsi(df['close'], length=period)
            
            return float(df['RSI'].dropna().iloc[-1])
            
        except Exception as e:
            self.logger.error(f"❌ Erreur calcul RSI: {e}")
            return 50.0
    
    def calculate_macd(self, prices: List[float], fast: int = 12, slow: int = 26, signal: int = 9) -> Dict:
        """Calcule le MACD (Moving Average Convergence Divergence)"""
        try:
            if len(prices) < max(fast, slow, signal) + 10:
                return {'macd': 0, 'signal': 0, 'histogram': 0, 'crossover': False}
            
            df = pd.DataFrame({'close': prices})
            macd_data = ta.macd(df['close'], fast=fast, slow=slow, signal=signal)
            
            if macd_data is None or macd_data.empty:
                return {'macd': 0, 'signal': 0, 'histogram': 0, 'crossover': False}
            
            # Dernières valeurs
            macd_line = float(macd_data.iloc[-1, 0]) if not pd.isna(macd_data.iloc[-1, 0]) else 0
            macd_signal = float(macd_data.iloc[-1, 2]) if not pd.isna(macd_data.iloc[-1, 2]) else 0
            macd_histogram = float(macd_data.iloc[-1, 1]) if not pd.isna(macd_data.iloc[-1, 1]) else 0
            
            # Détection de croisement (signal d'achat/vente)
            prev_histogram = float(macd_data.iloc[-2, 1]) if len(macd_data) > 1 and not pd.isna(macd_data.iloc[-2, 1]) else 0
            crossover = (prev_histogram <= 0 and macd_histogram > 0)  # Croisement haussier
            
            return {
                'macd': macd_line,
                'signal': macd_signal, 
                'histogram': macd_histogram,
                'crossover': crossover,
                'trend': 'bullish' if macd_histogram > 0 else 'bearish'
            }
            
        except Exception as e:
            self.logger.error(f"❌ Erreur calcul MACD: {e}")
            return {'macd': 0, 'signal': 0, 'histogram': 0, 'crossover': False}
    
    def calculate_bollinger_bands(self, prices: List[float], period: int = 20, std_dev: float = 2.0) -> Dict:
        """Calcule les Bandes de Bollinger"""
        try:
            if len(prices) < period + 5:
                return {'upper': 0, 'middle': 0, 'lower': 0, 'squeeze': False, 'position': 'middle'}
            
            df = pd.DataFrame({'close': prices})
            bb = ta.bbands(df['close'], length=period, std=std_dev)
            
            if bb is None or bb.empty:
                return {'upper': 0, 'middle': 0, 'lower': 0, 'squeeze': False, 'position': 'middle'}
            
            upper = float(bb.iloc[-1, 0])
            middle = float(bb.iloc[-1, 1]) 
            lower = float(bb.iloc[-1, 2])
            current_price = prices[-1]
            
            # Détection du squeeze (bandes serrées)
            band_width = (upper - lower) / middle
            prev_width = (float(bb.iloc[-2, 0]) - float(bb.iloc[-2, 2])) / float(bb.iloc[-2, 1]) if len(bb) > 1 else band_width
            squeeze = band_width < 0.1 and band_width < prev_width
            
            # Position du prix par rapport aux bandes
            if current_price >= upper:
                position = 'overbought'
            elif current_price <= lower:
                position = 'oversold'
            elif current_price > middle:
                position = 'upper_half'
            else:
                position = 'lower_half'
            
            return {
                'upper': upper,
                'middle': middle,
                'lower': lower,
                'width': band_width,
                'squeeze': squeeze,
                'position': position,
                'signal': 'buy' if position == 'oversold' else 'sell' if position == 'overbought' else 'hold'
            }
            
        except Exception as e:
            self.logger.error(f"❌ Erreur calcul Bollinger: {e}")
            return {'upper': 0, 'middle': 0, 'lower': 0, 'squeeze': False, 'position': 'middle'}
    
    def calculate_ema(self, prices: List[float], period: int = 21) -> float:
        """Calcule la Moyenne Mobile Exponentielle"""
        try:
            if len(prices) < period:
                return sum(prices) / len(prices) if prices else 0
            
            df = pd.DataFrame({'close': prices})
            ema = ta.ema(df['close'], length=period)
            
            return float(ema.iloc[-1]) if not pd.isna(ema.iloc[-1]) else prices[-1]
            
        except Exception as e:
            self.logger.error(f"❌ Erreur calcul EMA: {e}")
            return prices[-1] if prices else 0
    
    def calculate_stochastic(self, high_prices: List[float], low_prices: List[float], close_prices: List[float], k_period: int = 14, d_period: int = 3) -> Dict:
        """Calcule l'oscillateur Stochastique"""
        try:
            if len(close_prices) < k_period + d_period:
                return {'k': 50, 'd': 50, 'signal': 'hold'}
            
            df = pd.DataFrame({
                'high': high_prices,
                'low': low_prices, 
                'close': close_prices
            })
            
            stoch = ta.stoch(df['high'], df['low'], df['close'], k=k_period, d=d_period)
            
            if stoch is None or stoch.empty:
                return {'k': 50, 'd': 50, 'signal': 'hold'}
            
            k_value = float(stoch.iloc[-1, 0]) if not pd.isna(stoch.iloc[-1, 0]) else 50
            d_value = float(stoch.iloc[-1, 1]) if not pd.isna(stoch.iloc[-1, 1]) else 50
            
            # Signaux
            if k_value < 20 and d_value < 20:
                signal = 'oversold'
            elif k_value > 80 and d_value > 80:
                signal = 'overbought'
            elif k_value > d_value and k_value < 50:
                signal = 'bullish_divergence'
            else:
                signal = 'hold'
            
            return {
                'k': k_value,
                'd': d_value,
                'signal': signal
            }
            
        except Exception as e:
            self.logger.error(f"❌ Erreur calcul Stochastic: {e}")
            return {'k': 50, 'd': 50, 'signal': 'hold'}
    
    def calculate_adx(self, high_prices: List[float], low_prices: List[float], close_prices: List[float], period: int = 14) -> Dict:
        """Calcule l'Average Directional Index (force de la tendance)"""
        try:
            if len(close_prices) < period * 2:
                return {'adx': 25, 'plus_di': 25, 'minus_di': 25, 'trend_strength': 'weak'}
            
            df = pd.DataFrame({
                'high': high_prices,
                'low': low_prices,
                'close': close_prices
            })
            
            adx_data = ta.adx(df['high'], df['low'], df['close'], length=period)
            
            if adx_data is None or adx_data.empty:
                return {'adx': 25, 'plus_di': 25, 'minus_di': 25, 'trend_strength': 'weak'}
            
            adx = float(adx_data.iloc[-1, 0]) if not pd.isna(adx_data.iloc[-1, 0]) else 25
            plus_di = float(adx_data.iloc[-1, 1]) if not pd.isna(adx_data.iloc[-1, 1]) else 25
            minus_di = float(adx_data.iloc[-1, 2]) if not pd.isna(adx_data.iloc[-1, 2]) else 25
            
            # Force de la tendance
            if adx > 50:
                trend_strength = 'very_strong'
            elif adx > 25:
                trend_strength = 'strong'
            elif adx > 20:
                trend_strength = 'moderate'
            else:
                trend_strength = 'weak'
            
            # Direction de la tendance
            if plus_di > minus_di:
                trend_direction = 'bullish'
            else:
                trend_direction = 'bearish'
            
            return {
                'adx': adx,
                'plus_di': plus_di,
                'minus_di': minus_di,
                'trend_strength': trend_strength,
                'trend_direction': trend_direction
            }
            
        except Exception as e:
            self.logger.error(f"❌ Erreur calcul ADX: {e}")
            return {'adx': 25, 'plus_di': 25, 'minus_di': 25, 'trend_strength': 'weak'}
    
    def calculate_support_resistance(self, prices: List[float], window: int = 20) -> Dict:
        """Calcule les niveaux de support et résistance"""
        try:
            if len(prices) < window * 2:
                return {'support': min(prices) if prices else 0, 'resistance': max(prices) if prices else 0}
            
            df = pd.DataFrame({'close': prices})
            
            # Méthode des pivots locaux
            highs = df['close'].rolling(window=window, center=True).max()
            lows = df['close'].rolling(window=window, center=True).min()
            
            # Niveaux actuels
            recent_prices = prices[-window:]
            current_support = min(recent_prices)
            current_resistance = max(recent_prices)
            
            # Niveaux psychologiques (nombres ronds)
            current_price = prices[-1]
            psychological_levels = []
            
            # Générer des niveaux psychologiques proches
            if current_price > 1:
                base = 10 ** (len(str(int(current_price))) - 1)
                for i in range(1, 10):
                    level = base * i
                    if abs(level - current_price) / current_price < 0.1:  # Dans les 10%
                        psychological_levels.append(level)
            
            return {
                'support': current_support,
                'resistance': current_resistance,
                'psychological_levels': psychological_levels,
                'range_percent': ((current_resistance - current_support) / current_support) * 100 if current_support > 0 else 0
            }
            
        except Exception as e:
            self.logger.error(f"❌ Erreur calcul Support/Resistance: {e}")
            return {'support': 0, 'resistance': 0, 'psychological_levels': []}
    
    def calculate_volume_profile(self, prices: List[float], volumes: List[float], bins: int = 20) -> Dict:
        """Analyse du profil de volume"""
        try:
            if len(prices) != len(volumes) or len(prices) < bins:
                return {'vwap': prices[-1] if prices else 0, 'high_volume_zones': []}
            
            df = pd.DataFrame({'price': prices, 'volume': volumes})
            
            # Volume Weighted Average Price (VWAP)
            vwap = (df['price'] * df['volume']).sum() / df['volume'].sum() if df['volume'].sum() > 0 else df['price'].mean()
            
            # Zones de fort volume
            price_min, price_max = df['price'].min(), df['price'].max()
            price_bins = np.linspace(price_min, price_max, bins)
            df['price_bin'] = pd.cut(df['price'], bins=price_bins, include_lowest=True)
            
            volume_by_price = df.groupby('price_bin')['volume'].sum().sort_values(ascending=False)
            
            # Top 3 des zones de volume
            high_volume_zones = []
            for i, (price_range, volume) in enumerate(volume_by_price.head(3).items()):
                zone_price = (price_range.left + price_range.right) / 2
                high_volume_zones.append({
                    'price': zone_price,
                    'volume': volume,
                    'rank': i + 1
                })
            
            return {
                'vwap': vwap,
                'high_volume_zones': high_volume_zones,
                'current_vs_vwap': ((prices[-1] - vwap) / vwap) * 100 if vwap > 0 else 0
            }
            
        except Exception as e:
            self.logger.error(f"❌ Erreur calcul Volume Profile: {e}")
            return {'vwap': prices[-1] if prices else 0, 'high_volume_zones': []}
    
    def comprehensive_analysis(self, klines_data: List[List]) -> Dict:
        """Analyse technique complète à partir des données klines"""
        try:
            if not klines_data or len(klines_data) < 50:
                return {'error': 'Données insuffisantes'}
            
            # Extraction des données
            timestamps = [int(k[0]) for k in klines_data]
            opens = [float(k[1]) for k in klines_data]
            highs = [float(k[2]) for k in klines_data]
            lows = [float(k[3]) for k in klines_data]
            closes = [float(k[4]) for k in klines_data]
            volumes = [float(k[5]) for k in klines_data]
            
            # Calculs des indicateurs
            analysis = {
                'timestamp': datetime.now().isoformat(),
                'current_price': closes[-1],
                'price_change_24h': ((closes[-1] - closes[-24]) / closes[-24]) * 100 if len(closes) >= 24 else 0,
                
                # RSI
                'rsi': self.calculate_rsi(closes),
                
                # MACD
                'macd': self.calculate_macd(closes),
                
                # Bollinger Bands
                'bollinger': self.calculate_bollinger_bands(closes),
                
                # EMA
                'ema_21': self.calculate_ema(closes, 21),
                'ema_50': self.calculate_ema(closes, 50),
                
                # Stochastic
                'stochastic': self.calculate_stochastic(highs, lows, closes),
                
                # ADX
                'adx': self.calculate_adx(highs, lows, closes),
                
                # Support/Resistance
                'levels': self.calculate_support_resistance(closes),
                
                # Volume
                'volume_profile': self.calculate_volume_profile(closes, volumes)
            }
            
            # Score de signal global
            analysis['composite_signal'] = self._calculate_composite_signal(analysis)
            
            return analysis
            
        except Exception as e:
            self.logger.error(f"❌ Erreur analyse complète: {e}")
            return {'error': str(e)}
    
    def _calculate_composite_signal(self, analysis: Dict) -> Dict:
        """Calcule un signal composite basé sur tous les indicateurs"""
        try:
            signals = []
            scores = []
            
            # RSI (poids: 3)
            rsi = analysis.get('rsi', 50)
            if rsi < 30:
                signals.append('buy')
                scores.append(3)
            elif rsi > 70:
                signals.append('sell')
                scores.append(-3)
            else:
                signals.append('neutral')
                scores.append(0)
            
            # MACD (poids: 2)
            macd = analysis.get('macd', {})
            if macd.get('crossover', False):
                signals.append('buy')
                scores.append(2)
            elif macd.get('histogram', 0) < 0:
                signals.append('sell')
                scores.append(-1)
            else:
                signals.append('neutral')
                scores.append(0)
            
            # Bollinger (poids: 2)
            bollinger = analysis.get('bollinger', {})
            if bollinger.get('signal') == 'buy':
                signals.append('buy')
                scores.append(2)
            elif bollinger.get('signal') == 'sell':
                signals.append('sell')
                scores.append(-2)
            else:
                signals.append('neutral')
                scores.append(0)
            
            # Stochastic (poids: 1)
            stoch = analysis.get('stochastic', {})
            if stoch.get('signal') == 'oversold':
                signals.append('buy')
                scores.append(1)
            elif stoch.get('signal') == 'overbought':
                signals.append('sell')
                scores.append(-1)
            else:
                signals.append('neutral')
                scores.append(0)
            
            # Score final
            total_score = sum(scores)
            max_score = 8  # Score maximum possible
            
            if total_score >= 4:
                composite_signal = 'strong_buy'
            elif total_score >= 2:
                composite_signal = 'buy'
            elif total_score <= -4:
                composite_signal = 'strong_sell'
            elif total_score <= -2:
                composite_signal = 'sell'
            else:
                composite_signal = 'hold'
            
            return {
                'signal': composite_signal,
                'score': total_score,
                'max_score': max_score,
                'confidence': abs(total_score) / max_score,
                'individual_signals': signals
            }
            
        except Exception as e:
            self.logger.error(f"❌ Erreur calcul signal composite: {e}")
            return {'signal': 'hold', 'score': 0, 'confidence': 0}
    
    def detect_patterns(self, highs: List[float], lows: List[float], closes: List[float]) -> Dict:
        """Détection de patterns techniques simples"""
        try:
            if len(closes) < 10:
                return {'patterns': [], 'trend': 'unknown'}
            
            patterns = []
            
            # Double top/bottom (très simplifié)
            recent_highs = highs[-10:]
            recent_lows = lows[-10:]
            
            max_idx = recent_highs.index(max(recent_highs))
            min_idx = recent_lows.index(min(recent_lows))
            
            # Tendance générale (EMA court vs EMA long)
            ema_short = self.calculate_ema(closes, 10)
            ema_long = self.calculate_ema(closes, 30)
            
            if ema_short > ema_long * 1.02:
                trend = 'uptrend'
            elif ema_short < ema_long * 0.98:
                trend = 'downtrend'
            else:
                trend = 'sideways'
            
            # Volatilité récente
            recent_prices = closes[-10:]
            volatility = (max(recent_prices) - min(recent_prices)) / min(recent_prices) * 100
            
            if volatility > 10:
                patterns.append('high_volatility')
            elif volatility < 3:
                patterns.append('low_volatility')
            
            return {
                'patterns': patterns,
                'trend': trend,
                'volatility_percent': volatility
            }
            
        except Exception as e:
            self.logger.error(f"❌ Erreur détection patterns: {e}")
            return {'patterns': [], 'trend': 'unknown'}
