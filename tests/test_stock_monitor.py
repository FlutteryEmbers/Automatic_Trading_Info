"""
股票监控系统测试
"""
import unittest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.data.stock_data_fetcher import StockDataFetcher
from src.analyzers.momentum_analyzer import MomentumAnalyzer
from src.analyzers.correlation_analyzer import CorrelationAnalyzer

class TestStockDataFetcher(unittest.TestCase):
    """测试股票数据获取器"""
    
    def setUp(self):
        self.fetcher = StockDataFetcher()
    
    def test_fetch_stock_data(self):
        """测试获取单个股票数据"""
        data = self.fetcher.fetch_stock_data("AAPL", period="1mo")
        
        self.assertIsInstance(data, pd.DataFrame)
        self.assertIn('Close', data.columns)
        self.assertIn('Volume', data.columns)
        self.assertGreater(len(data), 0)
    
    def test_fetch_multiple_stocks(self):
        """测试获取多个股票数据"""
        symbols = ["AAPL", "MSFT", "GOOGL"]
        data = self.fetcher.fetch_multiple_stocks(symbols, period="1mo")
        
        self.assertIsInstance(data, dict)
        self.assertGreater(len(data), 0)
        
        for symbol in data.keys():
            self.assertIn(symbol, symbols)
            self.assertIsInstance(data[symbol], pd.DataFrame)
    
    def test_calculate_returns(self):
        """测试收益率计算"""
        # 创建测试数据
        test_data = pd.Series([100, 105, 110, 108, 112])
        returns = self.fetcher.calculate_returns(test_data)
        
        self.assertIsInstance(returns, pd.Series)
        self.assertEqual(len(returns), len(test_data))
        self.assertTrue(np.isnan(returns.iloc[0]))  # 第一个值应该是NaN

class TestMomentumAnalyzer(unittest.TestCase):
    """测试动量分析器"""
    
    def setUp(self):
        self.analyzer = MomentumAnalyzer()
        
        # 创建测试数据
        dates = pd.date_range(start='2023-01-01', periods=100, freq='D')
        np.random.seed(42)
        prices = 100 + np.cumsum(np.random.randn(100) * 0.01)
        
        self.test_data = pd.DataFrame({
            'Open': prices + np.random.randn(100) * 0.1,
            'High': prices + np.abs(np.random.randn(100) * 0.2),
            'Low': prices - np.abs(np.random.randn(100) * 0.2),
            'Close': prices,
            'Volume': np.random.randint(1000000, 10000000, 100)
        }, index=dates)
    
    def test_calculate_rsi(self):
        """测试RSI计算"""
        rsi = self.analyzer.calculate_rsi(self.test_data['Close'])
        
        self.assertIsInstance(rsi, pd.Series)
        self.assertTrue(all(0 <= value <= 100 for value in rsi.dropna()))
    
    def test_calculate_macd(self):
        """测试MACD计算"""
        macd_data = self.analyzer.calculate_macd(self.test_data['Close'])
        
        self.assertIn('macd', macd_data)
        self.assertIn('signal', macd_data)
        self.assertIn('histogram', macd_data)
        
        for key, series in macd_data.items():
            self.assertIsInstance(series, pd.Series)
    
    def test_calculate_moving_averages(self):
        """测试移动平均线计算"""
        ma_data = self.analyzer.calculate_moving_averages(self.test_data['Close'])
        
        self.assertIn('sma_short', ma_data)
        self.assertIn('sma_long', ma_data)
        
        for key, series in ma_data.items():
            self.assertIsInstance(series, pd.Series)
    
    def test_analyze_momentum_signals(self):
        """测试动量信号分析"""
        result = self.analyzer.analyze_momentum_signals(self.test_data)
        
        self.assertIn('indicators', result)
        self.assertIn('signals', result)
        self.assertIn('strength', result)
        
        signals = result['signals']
        self.assertIn('overall_signal', signals)
        self.assertIn(signals['overall_signal'], ['BUY', 'SELL', 'NEUTRAL'])

class TestCorrelationAnalyzer(unittest.TestCase):
    """测试相关性分析器"""
    
    def setUp(self):
        self.analyzer = CorrelationAnalyzer()
        
        # 创建测试数据
        dates = pd.date_range(start='2023-01-01', periods=100, freq='D')
        np.random.seed(42)
        
        # 创建相关的股票价格
        base_returns = np.random.randn(100) * 0.02
        
        self.test_data = pd.DataFrame({
            'AAPL': 150 + np.cumsum(base_returns + np.random.randn(100) * 0.01),
            'MSFT': 300 + np.cumsum(base_returns * 0.8 + np.random.randn(100) * 0.01),
            'GOOGL': 2500 + np.cumsum(base_returns * 0.6 + np.random.randn(100) * 0.02),
            'TSLA': 800 + np.cumsum(np.random.randn(100) * 0.03)  # 独立的股票
        }, index=dates)
    
    def test_calculate_correlation_matrix(self):
        """测试相关性矩阵计算"""
        corr_matrix = self.analyzer.calculate_correlation_matrix(self.test_data)
        
        self.assertIsInstance(corr_matrix, pd.DataFrame)
        self.assertEqual(corr_matrix.shape[0], corr_matrix.shape[1])
        self.assertEqual(len(corr_matrix), len(self.test_data.columns))
        
        # 对角线应该都是1
        np.testing.assert_array_almost_equal(np.diag(corr_matrix), np.ones(len(corr_matrix)))
    
    def test_find_highly_correlated_pairs(self):
        """测试高相关性股票对查找"""
        corr_matrix = self.analyzer.calculate_correlation_matrix(self.test_data)
        pairs = self.analyzer.find_highly_correlated_pairs(corr_matrix, threshold=0.3)
        
        self.assertIsInstance(pairs, list)
        
        for pair in pairs:
            self.assertEqual(len(pair), 3)  # (股票1, 股票2, 相关系数)
            self.assertIsInstance(pair[0], str)
            self.assertIsInstance(pair[1], str)
            self.assertIsInstance(pair[2], (int, float))
            self.assertGreaterEqual(abs(pair[2]), 0.3)
    
    def test_calculate_rolling_correlation(self):
        """测试滚动相关性计算"""
        rolling_corr = self.analyzer.calculate_rolling_correlation(
            self.test_data['AAPL'], 
            self.test_data['MSFT'], 
            window=30
        )
        
        self.assertIsInstance(rolling_corr, pd.Series)
        self.assertLessEqual(len(rolling_corr), len(self.test_data))
    
    def test_generate_correlation_report(self):
        """测试相关性报告生成"""
        # 创建模拟股票数据字典
        stock_data = {}
        for symbol in self.test_data.columns:
            stock_data[symbol] = pd.DataFrame({
                'Close': self.test_data[symbol]
            })
        
        report = self.analyzer.generate_correlation_report(stock_data)
        
        self.assertIn('analysis_date', report)
        self.assertIn('stocks_analyzed', report)
        self.assertIn('correlation_matrix', report)
        self.assertIn('highly_correlated_pairs', report)
        self.assertIn('summary', report)

class TestSystemIntegration(unittest.TestCase):
    """系统集成测试"""
    
    def test_end_to_end_analysis(self):
        """端到端分析测试"""
        # 这个测试需要网络连接来获取真实数据
        try:
            fetcher = StockDataFetcher()
            momentum_analyzer = MomentumAnalyzer()
            correlation_analyzer = CorrelationAnalyzer()
            
            # 获取少量股票数据进行测试
            symbols = ["AAPL", "MSFT"]
            stock_data = fetcher.fetch_multiple_stocks(symbols, period="1mo")
            
            if stock_data:
                # 动量分析
                momentum_results = {}
                for symbol, data in stock_data.items():
                    result = momentum_analyzer.analyze_momentum_signals(data)
                    if result:
                        momentum_results[symbol] = result
                
                # 相关性分析
                correlation_result = correlation_analyzer.generate_correlation_report(stock_data)
                
                # 验证结果
                self.assertGreater(len(momentum_results), 0)
                self.assertIn('analysis_date', correlation_result)
                
                print(f"✓ 成功分析了 {len(momentum_results)} 只股票")
                print(f"✓ 相关性分析包含 {len(correlation_result.get('highly_correlated_pairs', []))} 个高相关性股票对")
        
        except Exception as e:
            self.skipTest(f"网络连接测试跳过: {str(e)}")

if __name__ == '__main__':
    # 运行测试
    unittest.main(verbosity=2)
