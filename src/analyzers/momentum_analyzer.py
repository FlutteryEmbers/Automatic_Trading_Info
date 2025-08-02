"""
动量分析模块
实现各种技术指标和动量分析
"""
import pandas as pd
import numpy as np
import ta
from typing import Dict, List, Tuple, Optional
import logging

logger = logging.getLogger(__name__)

class MomentumAnalyzer:
    """动量分析器"""
    
    def __init__(self, config: Dict = None):
        """
        初始化动量分析器
        
        Args:
            config: 配置参数
        """
        self.config = config or {}
        self.default_params = {
            'rsi_period': 14,
            'macd_fast': 12,
            'macd_slow': 26,
            'macd_signal': 9,
            'sma_short': 20,
            'sma_long': 50,
            'bb_period': 20,
            'bb_std': 2
        }
    
    def get_param(self, key: str) -> int:
        """获取参数值"""
        return self.config.get(key, self.default_params.get(key))
    
    def calculate_rsi(self, data: pd.Series, period: int = None) -> pd.Series:
        """
        计算RSI相对强弱指数
        
        Args:
            data: 价格数据
            period: 计算周期
        
        Returns:
            RSI值
        """
        try:
            if period is None:
                period = self.get_param('rsi_period')
            
            return ta.momentum.RSIIndicator(data, window=period).rsi()
            
        except Exception as e:
            logger.error(f"Error calculating RSI: {str(e)}")
            return pd.Series()
    
    def calculate_macd(self, data: pd.Series, 
                      fast: int = None, 
                      slow: int = None, 
                      signal: int = None) -> Dict[str, pd.Series]:
        """
        计算MACD指标
        
        Args:
            data: 价格数据
            fast: 快线周期
            slow: 慢线周期
            signal: 信号线周期
        
        Returns:
            包含MACD线、信号线和柱状图的字典
        """
        try:
            if fast is None:
                fast = self.get_param('macd_fast')
            if slow is None:
                slow = self.get_param('macd_slow')
            if signal is None:
                signal = self.get_param('macd_signal')
            
            macd_indicator = ta.trend.MACD(data, window_slow=slow, window_fast=fast, window_sign=signal)
            
            return {
                'macd': macd_indicator.macd(),
                'signal': macd_indicator.macd_signal(),
                'histogram': macd_indicator.macd_diff()
            }
            
        except Exception as e:
            logger.error(f"Error calculating MACD: {str(e)}")
            return {}
    
    def calculate_moving_averages(self, data: pd.Series, 
                                short_period: int = None, 
                                long_period: int = None) -> Dict[str, pd.Series]:
        """
        计算移动平均线
        
        Args:
            data: 价格数据
            short_period: 短期移动平均周期
            long_period: 长期移动平均周期
        
        Returns:
            包含短期和长期移动平均线的字典
        """
        try:
            if short_period is None:
                short_period = self.get_param('sma_short')
            if long_period is None:
                long_period = self.get_param('sma_long')
            
            return {
                'sma_short': ta.trend.SMAIndicator(data, window=short_period).sma_indicator(),
                'sma_long': ta.trend.SMAIndicator(data, window=long_period).sma_indicator()
            }
            
        except Exception as e:
            logger.error(f"Error calculating moving averages: {str(e)}")
            return {}
    
    def calculate_bollinger_bands(self, data: pd.Series, 
                                period: int = None, 
                                std_dev: float = None) -> Dict[str, pd.Series]:
        """
        计算布林带
        
        Args:
            data: 价格数据
            period: 计算周期
            std_dev: 标准差倍数
        
        Returns:
            包含上轨、中轨、下轨的字典
        """
        try:
            if period is None:
                period = self.get_param('bb_period')
            if std_dev is None:
                std_dev = self.get_param('bb_std')
            
            bb_indicator = ta.volatility.BollingerBands(data, window=period, window_dev=std_dev)
            
            return {
                'upper': bb_indicator.bollinger_hband(),
                'middle': bb_indicator.bollinger_mavg(),
                'lower': bb_indicator.bollinger_lband()
            }
            
        except Exception as e:
            logger.error(f"Error calculating Bollinger Bands: {str(e)}")
            return {}
    
    def calculate_stochastic(self, high: pd.Series, 
                           low: pd.Series, 
                           close: pd.Series, 
                           k_period: int = 14, 
                           d_period: int = 3) -> Dict[str, pd.Series]:
        """
        计算随机指标
        
        Args:
            high: 最高价
            low: 最低价
            close: 收盘价
            k_period: K线周期
            d_period: D线周期
        
        Returns:
            包含%K和%D的字典
        """
        try:
            stoch_indicator = ta.momentum.StochasticOscillator(
                high=high, 
                low=low, 
                close=close, 
                window=k_period, 
                smooth_window=d_period
            )
            
            return {
                'k_percent': stoch_indicator.stoch(),
                'd_percent': stoch_indicator.stoch_signal()
            }
            
        except Exception as e:
            logger.error(f"Error calculating Stochastic: {str(e)}")
            return {}
    
    def calculate_williams_r(self, high: pd.Series, 
                           low: pd.Series, 
                           close: pd.Series, 
                           period: int = 14) -> pd.Series:
        """
        计算威廉指标
        
        Args:
            high: 最高价
            low: 最低价
            close: 收盘价
            period: 计算周期
        
        Returns:
            威廉指标值
        """
        try:
            return ta.momentum.WilliamsRIndicator(high, low, close, lbp=period).williams_r()
            
        except Exception as e:
            logger.error(f"Error calculating Williams %R: {str(e)}")
            return pd.Series()
    
    def analyze_momentum_signals(self, data: pd.DataFrame) -> Dict[str, Dict]:
        """
        综合动量信号分析
        
        Args:
            data: OHLCV数据
        
        Returns:
            动量分析结果
        """
        try:
            results = {}
            
            # 计算各种指标
            rsi = self.calculate_rsi(data['Close'])
            macd_data = self.calculate_macd(data['Close'])
            ma_data = self.calculate_moving_averages(data['Close'])
            bb_data = self.calculate_bollinger_bands(data['Close'])
            stoch_data = self.calculate_stochastic(data['High'], data['Low'], data['Close'])
            williams_r = self.calculate_williams_r(data['High'], data['Low'], data['Close'])
            
            # 获取最新值
            latest_rsi = rsi.iloc[-1] if not rsi.empty else np.nan
            latest_macd = macd_data['macd'].iloc[-1] if 'macd' in macd_data else np.nan
            latest_signal = macd_data['signal'].iloc[-1] if 'signal' in macd_data else np.nan
            latest_price = data['Close'].iloc[-1]
            latest_sma_short = ma_data['sma_short'].iloc[-1] if 'sma_short' in ma_data else np.nan
            latest_sma_long = ma_data['sma_long'].iloc[-1] if 'sma_long' in ma_data else np.nan
            
            # 分析信号
            signals = {
                'rsi_signal': self._analyze_rsi_signal(latest_rsi),
                'macd_signal': self._analyze_macd_signal(latest_macd, latest_signal),
                'ma_signal': self._analyze_ma_signal(latest_price, latest_sma_short, latest_sma_long),
                'bb_signal': self._analyze_bb_signal(data['Close'], bb_data),
                'overall_signal': 'NEUTRAL'
            }
            
            # 综合信号判断
            bull_signals = sum([1 for signal in signals.values() if signal == 'BUY'])
            bear_signals = sum([1 for signal in signals.values() if signal == 'SELL'])
            
            if bull_signals > bear_signals:
                signals['overall_signal'] = 'BUY'
            elif bear_signals > bull_signals:
                signals['overall_signal'] = 'SELL'
            
            results = {
                'indicators': {
                    'rsi': latest_rsi,
                    'macd': latest_macd,
                    'macd_signal': latest_signal,
                    'sma_short': latest_sma_short,
                    'sma_long': latest_sma_long,
                    'williams_r': williams_r.iloc[-1] if not williams_r.empty else np.nan
                },
                'signals': signals,
                'strength': abs(bull_signals - bear_signals) / max(len(signals) - 1, 1)  # 排除overall_signal
            }
            
            return results
            
        except Exception as e:
            logger.error(f"Error in momentum analysis: {str(e)}")
            return {}
    
    def _analyze_rsi_signal(self, rsi: float) -> str:
        """分析RSI信号"""
        if np.isnan(rsi):
            return 'NEUTRAL'
        
        if rsi > 70:
            return 'SELL'  # 超买
        elif rsi < 30:
            return 'BUY'   # 超卖
        else:
            return 'NEUTRAL'
    
    def _analyze_macd_signal(self, macd: float, signal: float) -> str:
        """分析MACD信号"""
        if np.isnan(macd) or np.isnan(signal):
            return 'NEUTRAL'
        
        if macd > signal:
            return 'BUY'
        elif macd < signal:
            return 'SELL'
        else:
            return 'NEUTRAL'
    
    def _analyze_ma_signal(self, price: float, sma_short: float, sma_long: float) -> str:
        """分析移动平均线信号"""
        if np.isnan(price) or np.isnan(sma_short) or np.isnan(sma_long):
            return 'NEUTRAL'
        
        if price > sma_short > sma_long:
            return 'BUY'
        elif price < sma_short < sma_long:
            return 'SELL'
        else:
            return 'NEUTRAL'
    
    def _analyze_bb_signal(self, prices: pd.Series, bb_data: Dict) -> str:
        """分析布林带信号"""
        if not bb_data or prices.empty:
            return 'NEUTRAL'
        
        latest_price = prices.iloc[-1]
        latest_upper = bb_data['upper'].iloc[-1] if not bb_data['upper'].empty else np.nan
        latest_lower = bb_data['lower'].iloc[-1] if not bb_data['lower'].empty else np.nan
        
        if np.isnan(latest_upper) or np.isnan(latest_lower):
            return 'NEUTRAL'
        
        if latest_price > latest_upper:
            return 'SELL'  # 突破上轨
        elif latest_price < latest_lower:
            return 'BUY'   # 跌破下轨
        else:
            return 'NEUTRAL'
