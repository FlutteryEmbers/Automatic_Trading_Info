"""
股票数据获取模块
使用yfinance获取股票数据
"""
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import logging

logger = logging.getLogger(__name__)

class StockDataFetcher:
    """股票数据获取器"""
    
    def __init__(self):
        self.cache = {}
    
    def fetch_stock_data(self, 
                        symbol: str, 
                        period: str = "6mo", 
                        interval: str = "1d") -> Optional[pd.DataFrame]:
        """
        获取单个股票数据
        
        Args:
            symbol: 股票代码
            period: 数据周期 (1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max)
            interval: 数据间隔 (1m, 2m, 5m, 15m, 30m, 60m, 90m, 1h, 1d, 5d, 1wk, 1mo, 3mo)
        
        Returns:
            DataFrame with OHLCV data
        """
        try:
            cache_key = f"{symbol}_{period}_{interval}"
            
            # 检查缓存
            if cache_key in self.cache:
                cached_data, cached_time = self.cache[cache_key]
                if datetime.now() - cached_time < timedelta(minutes=30):
                    logger.info(f"Using cached data for {symbol}")
                    return cached_data
            
            logger.info(f"Fetching data for {symbol} with period {period}")
            ticker = yf.Ticker(symbol)
            data = ticker.history(period=period, interval=interval)
            
            if data.empty:
                logger.warning(f"No data found for {symbol}")
                return None
            
            # 缓存数据
            self.cache[cache_key] = (data, datetime.now())
            
            return data
            
        except Exception as e:
            logger.error(f"Error fetching data for {symbol}: {str(e)}")
            return None
    
    def fetch_multiple_stocks(self, 
                             symbols: List[str], 
                             period: str = "6mo", 
                             interval: str = "1d") -> Dict[str, pd.DataFrame]:
        """
        获取多个股票数据
        
        Args:
            symbols: 股票代码列表
            period: 数据周期
            interval: 数据间隔
        
        Returns:
            字典，键为股票代码，值为DataFrame
        """
        results = {}
        
        for symbol in symbols:
            data = self.fetch_stock_data(symbol, period, interval)
            if data is not None:
                results[symbol] = data
            else:
                logger.warning(f"Failed to fetch data for {symbol}")
        
        return results
    
    def get_stock_info(self, symbol: str) -> Optional[Dict]:
        """
        获取股票基本信息
        
        Args:
            symbol: 股票代码
        
        Returns:
            股票信息字典
        """
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            
            # 提取关键信息
            key_info = {
                'symbol': symbol,
                'shortName': info.get('shortName', ''),
                'longName': info.get('longName', ''),
                'sector': info.get('sector', ''),
                'industry': info.get('industry', ''),
                'marketCap': info.get('marketCap', 0),
                'currentPrice': info.get('currentPrice', 0),
                'previousClose': info.get('previousClose', 0),
                'dayLow': info.get('dayLow', 0),
                'dayHigh': info.get('dayHigh', 0),
                'volume': info.get('volume', 0),
                'averageVolume': info.get('averageVolume', 0),
            }
            
            return key_info
            
        except Exception as e:
            logger.error(f"Error fetching info for {symbol}: {str(e)}")
            return None
    
    def create_combined_dataframe(self, 
                                 stock_data: Dict[str, pd.DataFrame], 
                                 price_type: str = 'Close') -> pd.DataFrame:
        """
        将多个股票数据合并为一个DataFrame
        
        Args:
            stock_data: 股票数据字典
            price_type: 价格类型 (Open, High, Low, Close, Volume)
        
        Returns:
            合并后的DataFrame，列为股票代码
        """
        try:
            combined_data = pd.DataFrame()
            
            for symbol, data in stock_data.items():
                if price_type in data.columns:
                    combined_data[symbol] = data[price_type]
            
            # 删除包含NaN的行
            combined_data = combined_data.dropna()
            
            return combined_data
            
        except Exception as e:
            logger.error(f"Error creating combined dataframe: {str(e)}")
            return pd.DataFrame()
    
    def calculate_returns(self, data: pd.DataFrame, periods: int = 1) -> pd.DataFrame:
        """
        计算收益率
        
        Args:
            data: 价格数据
            periods: 计算周期
        
        Returns:
            收益率DataFrame
        """
        try:
            if isinstance(data, pd.Series):
                return data.pct_change(periods=periods)
            else:
                return data.pct_change(periods=periods)
                
        except Exception as e:
            logger.error(f"Error calculating returns: {str(e)}")
            return pd.DataFrame()
    
    def get_latest_prices(self, symbols: List[str]) -> Dict[str, float]:
        """
        获取最新价格
        
        Args:
            symbols: 股票代码列表
        
        Returns:
            最新价格字典
        """
        latest_prices = {}
        
        for symbol in symbols:
            try:
                ticker = yf.Ticker(symbol)
                hist = ticker.history(period="1d")
                if not hist.empty:
                    latest_prices[symbol] = hist['Close'].iloc[-1]
                else:
                    logger.warning(f"No recent data for {symbol}")
                    
            except Exception as e:
                logger.error(f"Error getting latest price for {symbol}: {str(e)}")
        
        return latest_prices
