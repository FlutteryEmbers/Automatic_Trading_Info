"""
AWS Lambda主函数
股票监控系统的核心处理逻辑
"""
import json
import logging
import os
import yaml
from typing import Dict, List, Optional
from datetime import datetime, timedelta

# 导入自定义模块
from src.data.stock_data_fetcher import StockDataFetcher
from src.analyzers.momentum_analyzer import MomentumAnalyzer
from src.analyzers.correlation_analyzer import CorrelationAnalyzer
from src.notifications.email_sender import EmailSender
from src.notifications.sns_sender import SNSSender

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class StockMonitoringService:
    """股票监控服务主类"""
    
    def __init__(self):
        """初始化服务"""
        self.config = self._load_config()
        self.stock_list = self._load_stock_list()
        
        # 初始化组件
        self.data_fetcher = StockDataFetcher()
        self.momentum_analyzer = MomentumAnalyzer(self.config.get('analysis', {}).get('momentum', {}))
        self.correlation_analyzer = CorrelationAnalyzer(self.config.get('analysis', {}).get('correlation', {}))
        
        # 初始化通知服务
        aws_config = self.config.get('aws', {})
        self.email_sender = EmailSender(aws_config.get('ses_region', 'us-east-1'))
        self.sns_sender = SNSSender(aws_config.get('region', 'us-east-1'))
    
    def _load_config(self) -> Dict:
        """加载配置文件"""
        try:
            config_path = '/opt/config/config.yaml'
            if not os.path.exists(config_path):
                config_path = 'config/config.yaml'
            
            with open(config_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except Exception as e:
            logger.error(f"Error loading config: {str(e)}")
            return {}
    
    def _load_stock_list(self) -> Dict:
        """加载股票列表"""
        try:
            stocks_path = '/opt/config/stocks_watchlist.yaml'
            if not os.path.exists(stocks_path):
                stocks_path = 'config/stocks_watchlist.yaml'
            
            with open(stocks_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except Exception as e:
            logger.error(f"Error loading stock list: {str(e)}")
            return {'stocks': {}}
    
    def get_all_symbols(self) -> List[str]:
        """获取所有股票代码"""
        symbols = []
        stocks = self.stock_list.get('stocks', {})
        
        for category, stock_list in stocks.items():
            for stock in stock_list:
                symbols.append(stock['symbol'])
        
        return list(set(symbols))  # 去重
    
    def run_analysis(self) -> Dict:
        """运行完整分析"""
        try:
            logger.info("Starting stock analysis...")
            
            # 获取股票数据
            symbols = self.get_all_symbols()
            logger.info(f"Analyzing {len(symbols)} stocks: {symbols}")
            
            analysis_config = self.config.get('analysis', {})
            data_config = analysis_config.get('data', {})
            
            stock_data = self.data_fetcher.fetch_multiple_stocks(
                symbols,
                period=data_config.get('period', '6mo'),
                interval=data_config.get('interval', '1d')
            )
            
            if not stock_data:
                logger.error("No stock data retrieved")
                return {'error': 'No stock data available'}
            
            logger.info(f"Retrieved data for {len(stock_data)} stocks")
            
            # 动量分析
            momentum_results = self._run_momentum_analysis(stock_data)
            
            # 相关性分析
            correlation_results = self._run_correlation_analysis(stock_data)
            
            # 获取最新价格
            latest_prices = self.data_fetcher.get_latest_prices(symbols)
            
            # 生成报告
            analysis_results = {
                'timestamp': datetime.now().isoformat(),
                'stocks_analyzed': len(stock_data),
                'momentum_results': momentum_results,
                'correlation_results': correlation_results,
                'latest_prices': latest_prices,
                'summary': self._generate_summary(momentum_results, correlation_results)
            }
            
            # 发送通知
            self._send_notifications(analysis_results)
            
            logger.info("Analysis completed successfully")
            return analysis_results
            
        except Exception as e:
            logger.error(f"Error in analysis: {str(e)}")
            return {'error': str(e)}
    
    def _run_momentum_analysis(self, stock_data: Dict) -> Dict:
        """运行动量分析"""
        try:
            logger.info("Running momentum analysis...")
            momentum_results = {}
            
            for symbol, data in stock_data.items():
                try:
                    result = self.momentum_analyzer.analyze_momentum_signals(data)
                    if result:
                        momentum_results[symbol] = result
                        logger.info(f"Momentum analysis completed for {symbol}: {result.get('signals', {}).get('overall_signal', 'UNKNOWN')}")
                except Exception as e:
                    logger.error(f"Error in momentum analysis for {symbol}: {str(e)}")
            
            return momentum_results
            
        except Exception as e:
            logger.error(f"Error in momentum analysis: {str(e)}")
            return {}
    
    def _run_correlation_analysis(self, stock_data: Dict) -> Dict:
        """运行相关性分析"""
        try:
            logger.info("Running correlation analysis...")
            
            symbols = list(stock_data.keys())
            correlation_result = self.correlation_analyzer.generate_correlation_report(stock_data, symbols)
            
            logger.info(f"Correlation analysis completed for {len(symbols)} stocks")
            return correlation_result
            
        except Exception as e:
            logger.error(f"Error in correlation analysis: {str(e)}")
            return {}
    
    def _generate_summary(self, momentum_results: Dict, correlation_results: Dict) -> Dict:
        """生成分析总结"""
        try:
            summary = {
                'total_stocks': len(momentum_results),
                'analysis_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
            # 动量信号统计
            buy_signals = sum(1 for result in momentum_results.values() 
                            if result.get('signals', {}).get('overall_signal') == 'BUY')
            sell_signals = sum(1 for result in momentum_results.values() 
                             if result.get('signals', {}).get('overall_signal') == 'SELL')
            neutral_signals = sum(1 for result in momentum_results.values() 
                                if result.get('signals', {}).get('overall_signal') == 'NEUTRAL')
            
            summary['momentum_summary'] = {
                'buy_signals': buy_signals,
                'sell_signals': sell_signals,
                'neutral_signals': neutral_signals
            }
            
            # 相关性统计
            if correlation_results and 'highly_correlated_pairs' in correlation_results:
                high_corr_pairs = len(correlation_results['highly_correlated_pairs'])
                avg_correlation = correlation_results.get('portfolio_average_correlation', 0)
                
                summary['correlation_summary'] = {
                    'high_correlation_pairs': high_corr_pairs,
                    'average_correlation': avg_correlation
                }
            
            # 市场情绪判断
            if buy_signals > sell_signals:
                summary['market_sentiment'] = 'BULLISH'
            elif sell_signals > buy_signals:
                summary['market_sentiment'] = 'BEARISH'
            else:
                summary['market_sentiment'] = 'NEUTRAL'
            
            return summary
            
        except Exception as e:
            logger.error(f"Error generating summary: {str(e)}")
            return {}
    
    def _send_notifications(self, analysis_results: Dict):
        """发送通知"""
        try:
            notification_config = self.config.get('notifications', {})
            
            # 发送邮件通知
            if notification_config.get('email', {}).get('enabled', False):
                self._send_email_notification(analysis_results, notification_config['email'])
            
            # 发送SNS通知
            if notification_config.get('sns', {}).get('enabled', False):
                self._send_sns_notification(analysis_results, notification_config['sns'])
                
        except Exception as e:
            logger.error(f"Error sending notifications: {str(e)}")
    
    def _send_email_notification(self, analysis_results: Dict, email_config: Dict):
        """发送邮件通知"""
        try:
            from_email = os.environ.get('FROM_EMAIL')
            to_email = os.environ.get('TO_EMAIL')
            
            if not from_email or not to_email:
                logger.warning("Email addresses not configured")
                return
            
            subject_prefix = email_config.get('subject_prefix', '[股票分析]')
            subject = f"{subject_prefix} {datetime.now().strftime('%Y-%m-%d')} 分析报告"
            
            success = self.email_sender.send_analysis_report(
                to_emails=[to_email],
                from_email=from_email,
                subject=subject,
                momentum_results=analysis_results.get('momentum_results', {}),
                correlation_results=analysis_results.get('correlation_results', {}),
                stock_prices=analysis_results.get('latest_prices', {})
            )
            
            if success:
                logger.info("Email notification sent successfully")
            else:
                logger.error("Failed to send email notification")
                
        except Exception as e:
            logger.error(f"Error sending email notification: {str(e)}")
    
    def _send_sns_notification(self, analysis_results: Dict, sns_config: Dict):
        """发送SNS通知"""
        try:
            topic_arn = sns_config.get('topic_arn')
            if not topic_arn:
                logger.warning("SNS topic ARN not configured")
                return
            
            summary = analysis_results.get('summary', {})
            
            success = self.sns_sender.send_daily_summary(topic_arn, summary)
            
            if success:
                logger.info("SNS notification sent successfully")
            else:
                logger.error("Failed to send SNS notification")
                
        except Exception as e:
            logger.error(f"Error sending SNS notification: {str(e)}")

def lambda_handler(event, context):
    """
    AWS Lambda入口函数
    
    Args:
        event: Lambda事件对象
        context: Lambda上下文对象
    
    Returns:
        执行结果
    """
    try:
        logger.info(f"Lambda function started with event: {json.dumps(event)}")
        
        # 初始化服务
        service = StockMonitoringService()
        
        # 运行分析
        results = service.run_analysis()
        
        # 构造响应
        response = {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Stock analysis completed successfully',
                'results': {
                    'timestamp': results.get('timestamp'),
                    'stocks_analyzed': results.get('stocks_analyzed', 0),
                    'summary': results.get('summary', {}),
                    'error': results.get('error')
                }
            }, default=str),
            'headers': {
                'Content-Type': 'application/json'
            }
        }
        
        logger.info("Lambda function completed successfully")
        return response
        
    except Exception as e:
        logger.error(f"Lambda function error: {str(e)}")
        
        return {
            'statusCode': 500,
            'body': json.dumps({
                'message': 'Internal server error',
                'error': str(e)
            }),
            'headers': {
                'Content-Type': 'application/json'
            }
        }

# 用于本地测试
if __name__ == "__main__":
    # 模拟Lambda事件
    test_event = {
        "source": "aws.events",
        "detail-type": "Scheduled Event"
    }
    
    test_context = type('Context', (), {
        'function_name': 'stock-monitor-test',
        'function_version': '$LATEST',
        'invoked_function_arn': 'arn:aws:lambda:us-east-1:123456789012:function:stock-monitor-test',
        'memory_limit_in_mb': '512',
        'remaining_time_in_millis': lambda: 30000
    })()
    
    # 运行测试
    result = lambda_handler(test_event, test_context)
    print(json.dumps(result, indent=2, default=str))
