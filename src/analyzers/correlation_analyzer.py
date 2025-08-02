"""
相关性分析模块
分析股票间的相关性和协整关系
"""
import pandas as pd
import numpy as np
from scipy import stats
from typing import Dict, List, Tuple, Optional
import logging

logger = logging.getLogger(__name__)

class CorrelationAnalyzer:
    """相关性分析器"""
    
    def __init__(self, config: Dict = None):
        """
        初始化相关性分析器
        
        Args:
            config: 配置参数
        """
        self.config = config or {}
        self.default_params = {
            'lookback_period': 60,
            'min_correlation': 0.5,
            'rolling_window': 30
        }
    
    def get_param(self, key: str):
        """获取参数值"""
        return self.config.get(key, self.default_params.get(key))
    
    def calculate_correlation_matrix(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        计算相关性矩阵
        
        Args:
            data: 股票价格数据，列为股票代码
        
        Returns:
            相关性矩阵
        """
        try:
            # 计算收益率
            returns = data.pct_change().dropna()
            
            # 计算相关性矩阵
            correlation_matrix = returns.corr()
            
            return correlation_matrix
            
        except Exception as e:
            logger.error(f"Error calculating correlation matrix: {str(e)}")
            return pd.DataFrame()
    
    def calculate_rolling_correlation(self, 
                                    data1: pd.Series, 
                                    data2: pd.Series, 
                                    window: int = None) -> pd.Series:
        """
        计算滚动相关性
        
        Args:
            data1: 第一个时间序列
            data2: 第二个时间序列
            window: 滚动窗口大小
        
        Returns:
            滚动相关性序列
        """
        try:
            if window is None:
                window = self.get_param('rolling_window')
            
            # 计算收益率
            returns1 = data1.pct_change().dropna()
            returns2 = data2.pct_change().dropna()
            
            # 确保数据长度一致
            min_length = min(len(returns1), len(returns2))
            returns1 = returns1.iloc[-min_length:]
            returns2 = returns2.iloc[-min_length:]
            
            # 计算滚动相关性
            rolling_corr = returns1.rolling(window=window).corr(returns2)
            
            return rolling_corr
            
        except Exception as e:
            logger.error(f"Error calculating rolling correlation: {str(e)}")
            return pd.Series()
    
    def find_highly_correlated_pairs(self, 
                                   correlation_matrix: pd.DataFrame, 
                                   threshold: float = None) -> List[Tuple[str, str, float]]:
        """
        找出高相关性股票对
        
        Args:
            correlation_matrix: 相关性矩阵
            threshold: 相关性阈值
        
        Returns:
            高相关性股票对列表，格式为(股票1, 股票2, 相关系数)
        """
        try:
            if threshold is None:
                threshold = self.get_param('min_correlation')
            
            high_corr_pairs = []
            
            # 遍历相关性矩阵的上三角部分
            for i in range(len(correlation_matrix.columns)):
                for j in range(i + 1, len(correlation_matrix.columns)):
                    stock1 = correlation_matrix.columns[i]
                    stock2 = correlation_matrix.columns[j]
                    corr_value = correlation_matrix.loc[stock1, stock2]
                    
                    # 检查是否满足阈值条件
                    if abs(corr_value) >= threshold and not np.isnan(corr_value):
                        high_corr_pairs.append((stock1, stock2, corr_value))
            
            # 按相关性强度排序
            high_corr_pairs.sort(key=lambda x: abs(x[2]), reverse=True)
            
            return high_corr_pairs
            
        except Exception as e:
            logger.error(f"Error finding highly correlated pairs: {str(e)}")
            return []
    
    def calculate_beta(self, stock_returns: pd.Series, market_returns: pd.Series) -> float:
        """
        计算股票相对于市场的贝塔系数
        
        Args:
            stock_returns: 股票收益率
            market_returns: 市场收益率
        
        Returns:
            贝塔系数
        """
        try:
            # 确保数据长度一致
            min_length = min(len(stock_returns), len(market_returns))
            stock_returns = stock_returns.iloc[-min_length:].dropna()
            market_returns = market_returns.iloc[-min_length:].dropna()
            
            # 计算协方差和方差
            covariance = np.cov(stock_returns, market_returns)[0, 1]
            market_variance = np.var(market_returns)
            
            if market_variance == 0:
                return np.nan
            
            beta = covariance / market_variance
            
            return beta
            
        except Exception as e:
            logger.error(f"Error calculating beta: {str(e)}")
            return np.nan
    
    def calculate_portfolio_correlation(self, 
                                      portfolio_weights: Dict[str, float], 
                                      correlation_matrix: pd.DataFrame) -> float:
        """
        计算投资组合的平均相关性
        
        Args:
            portfolio_weights: 投资组合权重字典
            correlation_matrix: 相关性矩阵
        
        Returns:
            投资组合平均相关性
        """
        try:
            total_correlation = 0.0
            total_weight = 0.0
            
            stocks = list(portfolio_weights.keys())
            
            for i, stock1 in enumerate(stocks):
                for j, stock2 in enumerate(stocks):
                    if i != j and stock1 in correlation_matrix.columns and stock2 in correlation_matrix.columns:
                        weight1 = portfolio_weights[stock1]
                        weight2 = portfolio_weights[stock2]
                        corr = correlation_matrix.loc[stock1, stock2]
                        
                        if not np.isnan(corr):
                            total_correlation += weight1 * weight2 * corr
                            total_weight += weight1 * weight2
            
            if total_weight == 0:
                return np.nan
            
            return total_correlation / total_weight
            
        except Exception as e:
            logger.error(f"Error calculating portfolio correlation: {str(e)}")
            return np.nan
    
    def analyze_sector_correlation(self, 
                                 stock_data: Dict[str, pd.DataFrame], 
                                 sector_mapping: Dict[str, str]) -> Dict[str, Dict]:
        """
        分析行业相关性
        
        Args:
            stock_data: 股票数据字典
            sector_mapping: 股票到行业的映射
        
        Returns:
            行业相关性分析结果
        """
        try:
            # 按行业分组
            sector_groups = {}
            for stock, sector in sector_mapping.items():
                if stock in stock_data:
                    if sector not in sector_groups:
                        sector_groups[sector] = []
                    sector_groups[sector].append(stock)
            
            sector_analysis = {}
            
            for sector, stocks in sector_groups.items():
                if len(stocks) > 1:
                    # 创建该行业的数据
                    sector_data = pd.DataFrame()
                    for stock in stocks:
                        if stock in stock_data and 'Close' in stock_data[stock].columns:
                            sector_data[stock] = stock_data[stock]['Close']
                    
                    if not sector_data.empty:
                        # 计算行业内相关性矩阵
                        sector_corr = self.calculate_correlation_matrix(sector_data)
                        
                        # 计算平均相关性
                        upper_triangle = np.triu(sector_corr.values, k=1)
                        non_zero_values = upper_triangle[upper_triangle != 0]
                        avg_correlation = np.mean(non_zero_values) if len(non_zero_values) > 0 else 0
                        
                        sector_analysis[sector] = {
                            'stocks': stocks,
                            'correlation_matrix': sector_corr,
                            'average_correlation': avg_correlation,
                            'stock_count': len(stocks)
                        }
            
            return sector_analysis
            
        except Exception as e:
            logger.error(f"Error in sector correlation analysis: {str(e)}")
            return {}
    
    def detect_correlation_breakdowns(self, 
                                    data1: pd.Series, 
                                    data2: pd.Series, 
                                    window: int = None, 
                                    threshold_change: float = 0.3) -> List[Dict]:
        """
        检测相关性破裂点
        
        Args:
            data1: 第一个时间序列
            data2: 第二个时间序列
            window: 滚动窗口大小
            threshold_change: 相关性变化阈值
        
        Returns:
            相关性破裂点列表
        """
        try:
            if window is None:
                window = self.get_param('rolling_window')
            
            # 计算滚动相关性
            rolling_corr = self.calculate_rolling_correlation(data1, data2, window)
            
            # 计算相关性变化
            corr_change = rolling_corr.diff().abs()
            
            # 找出破裂点
            breakdowns = []
            for date, change in corr_change.items():
                if change > threshold_change and not np.isnan(change):
                    breakdowns.append({
                        'date': date,
                        'correlation_change': change,
                        'new_correlation': rolling_corr.loc[date] if date in rolling_corr.index else np.nan
                    })
            
            return breakdowns
            
        except Exception as e:
            logger.error(f"Error detecting correlation breakdowns: {str(e)}")
            return []
    
    def generate_correlation_report(self, 
                                  stock_data: Dict[str, pd.DataFrame], 
                                  stock_list: List[str] = None) -> Dict:
        """
        生成综合相关性分析报告
        
        Args:
            stock_data: 股票数据字典
            stock_list: 要分析的股票列表
        
        Returns:
            相关性分析报告
        """
        try:
            if stock_list is None:
                stock_list = list(stock_data.keys())
            
            # 创建价格数据框
            price_data = pd.DataFrame()
            for stock in stock_list:
                if stock in stock_data and 'Close' in stock_data[stock].columns:
                    price_data[stock] = stock_data[stock]['Close']
            
            if price_data.empty:
                return {'error': 'No valid price data found'}
            
            # 计算相关性矩阵
            correlation_matrix = self.calculate_correlation_matrix(price_data)
            
            # 找出高相关性股票对
            high_corr_pairs = self.find_highly_correlated_pairs(correlation_matrix)
            
            # 计算投资组合相关性（等权重）
            equal_weights = {stock: 1.0/len(stock_list) for stock in stock_list}
            portfolio_corr = self.calculate_portfolio_correlation(equal_weights, correlation_matrix)
            
            # 生成报告
            report = {
                'analysis_date': pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S'),
                'stocks_analyzed': stock_list,
                'correlation_matrix': correlation_matrix.round(3),
                'highly_correlated_pairs': [
                    {
                        'stock1': pair[0],
                        'stock2': pair[1],
                        'correlation': round(pair[2], 3),
                        'strength': 'Strong' if abs(pair[2]) > 0.8 else 'Moderate'
                    } for pair in high_corr_pairs[:10]  # 取前10对
                ],
                'portfolio_average_correlation': round(portfolio_corr, 3) if not np.isnan(portfolio_corr) else None,
                'diversification_score': self._calculate_diversification_score(correlation_matrix),
                'summary': self._generate_correlation_summary(correlation_matrix, high_corr_pairs)
            }
            
            return report
            
        except Exception as e:
            logger.error(f"Error generating correlation report: {str(e)}")
            return {'error': str(e)}
    
    def _calculate_diversification_score(self, correlation_matrix: pd.DataFrame) -> float:
        """计算分散化评分"""
        try:
            # 获取上三角矩阵的相关系数
            upper_triangle = np.triu(correlation_matrix.values, k=1)
            correlations = upper_triangle[upper_triangle != 0]
            correlations = correlations[~np.isnan(correlations)]
            
            if len(correlations) == 0:
                return 0.0
            
            # 分散化评分 = 1 - 平均相关性的绝对值
            avg_abs_corr = np.mean(np.abs(correlations))
            diversification_score = max(0.0, 1.0 - avg_abs_corr)
            
            return round(diversification_score, 3)
            
        except Exception as e:
            logger.error(f"Error calculating diversification score: {str(e)}")
            return 0.0
    
    def _generate_correlation_summary(self, 
                                    correlation_matrix: pd.DataFrame, 
                                    high_corr_pairs: List[Tuple]) -> str:
        """生成相关性分析总结"""
        try:
            total_pairs = len(correlation_matrix.columns) * (len(correlation_matrix.columns) - 1) // 2
            high_corr_count = len(high_corr_pairs)
            
            summary = f"共分析了{len(correlation_matrix.columns)}只股票，"
            summary += f"总计{total_pairs}个股票对。"
            
            if high_corr_count > 0:
                summary += f"发现{high_corr_count}对高相关性股票对，"
                summary += f"占比{high_corr_count/total_pairs*100:.1f}%。"
                
                max_corr = max([abs(pair[2]) for pair in high_corr_pairs])
                summary += f"最高相关系数为{max_corr:.3f}。"
            else:
                summary += "未发现显著的高相关性股票对。"
            
            return summary
            
        except Exception as e:
            logger.error(f"Error generating correlation summary: {str(e)}")
            return "无法生成分析总结"
