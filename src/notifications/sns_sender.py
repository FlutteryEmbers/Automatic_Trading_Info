"""
SNS消息发送模块
使用AWS SNS发送通知消息
"""
import boto3
import json
import logging
from typing import Dict, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class SNSSender:
    """SNS消息发送器"""
    
    def __init__(self, region_name: str = 'us-east-1'):
        """
        初始化SNS发送器
        
        Args:
            region_name: AWS区域
        """
        self.region_name = region_name
        self.sns_client = boto3.client('sns', region_name=region_name)
    
    def send_alert_message(self, 
                          topic_arn: str, 
                          subject: str, 
                          message: str, 
                          message_attributes: Dict = None) -> bool:
        """
        发送警报消息
        
        Args:
            topic_arn: SNS主题ARN
            subject: 消息主题
            message: 消息内容
            message_attributes: 消息属性
        
        Returns:
            发送成功返回True，失败返回False
        """
        try:
            publish_params = {
                'TopicArn': topic_arn,
                'Subject': subject,
                'Message': message
            }
            
            if message_attributes:
                publish_params['MessageAttributes'] = message_attributes
            
            response = self.sns_client.publish(**publish_params)
            
            logger.info(f"SNS message sent successfully. MessageId: {response['MessageId']}")
            return True
            
        except Exception as e:
            logger.error(f"Error sending SNS message: {str(e)}")
            return False
    
    def send_momentum_alert(self, 
                           topic_arn: str, 
                           symbol: str, 
                           signal: str, 
                           indicators: Dict) -> bool:
        """
        发送动量信号警报
        
        Args:
            topic_arn: SNS主题ARN
            symbol: 股票代码
            signal: 信号类型
            indicators: 技术指标数据
        
        Returns:
            发送成功返回True，失败返回False
        """
        try:
            # 创建消息内容
            message = self._create_momentum_message(symbol, signal, indicators)
            subject = f"[股票警报] {symbol} - {signal}信号"
            
            # 添加消息属性
            message_attributes = {
                'symbol': {
                    'DataType': 'String',
                    'StringValue': symbol
                },
                'signal': {
                    'DataType': 'String',
                    'StringValue': signal
                },
                'alert_type': {
                    'DataType': 'String',
                    'StringValue': 'momentum'
                }
            }
            
            return self.send_alert_message(topic_arn, subject, message, message_attributes)
            
        except Exception as e:
            logger.error(f"Error sending momentum alert: {str(e)}")
            return False
    
    def send_correlation_alert(self, 
                              topic_arn: str, 
                              correlated_pairs: List[Dict], 
                              threshold: float) -> bool:
        """
        发送相关性警报
        
        Args:
            topic_arn: SNS主题ARN
            correlated_pairs: 高相关性股票对
            threshold: 相关性阈值
        
        Returns:
            发送成功返回True，失败返回False
        """
        try:
            # 创建消息内容
            message = self._create_correlation_message(correlated_pairs, threshold)
            subject = "[股票警报] 发现高相关性股票对"
            
            # 添加消息属性
            message_attributes = {
                'alert_type': {
                    'DataType': 'String',
                    'StringValue': 'correlation'
                },
                'pairs_count': {
                    'DataType': 'Number',
                    'StringValue': str(len(correlated_pairs))
                }
            }
            
            return self.send_alert_message(topic_arn, subject, message, message_attributes)
            
        except Exception as e:
            logger.error(f"Error sending correlation alert: {str(e)}")
            return False
    
    def send_daily_summary(self, 
                          topic_arn: str, 
                          summary_data: Dict) -> bool:
        """
        发送每日总结
        
        Args:
            topic_arn: SNS主题ARN
            summary_data: 总结数据
        
        Returns:
            发送成功返回True，失败返回False
        """
        try:
            # 创建消息内容
            message = self._create_summary_message(summary_data)
            subject = f"[每日总结] {datetime.now().strftime('%Y-%m-%d')} 股票分析报告"
            
            # 添加消息属性
            message_attributes = {
                'alert_type': {
                    'DataType': 'String',
                    'StringValue': 'daily_summary'
                },
                'date': {
                    'DataType': 'String',
                    'StringValue': datetime.now().strftime('%Y-%m-%d')
                }
            }
            
            return self.send_alert_message(topic_arn, subject, message, message_attributes)
            
        except Exception as e:
            logger.error(f"Error sending daily summary: {str(e)}")
            return False
    
    def _create_momentum_message(self, symbol: str, signal: str, indicators: Dict) -> str:
        """创建动量信号消息"""
        try:
            message = f"股票 {symbol} 触发 {signal} 信号！\n\n"
            message += "技术指标:\n"
            
            if 'rsi' in indicators:
                rsi = indicators['rsi']
                message += f"• RSI: {rsi:.2f}\n"
                if rsi > 70:
                    message += "  (超买区域)\n"
                elif rsi < 30:
                    message += "  (超卖区域)\n"
            
            if 'macd' in indicators:
                macd = indicators['macd']
                message += f"• MACD: {macd:.4f}\n"
            
            if 'sma_short' in indicators and 'sma_long' in indicators:
                sma_short = indicators['sma_short']
                sma_long = indicators['sma_long']
                message += f"• 短期移动平均: {sma_short:.2f}\n"
                message += f"• 长期移动平均: {sma_long:.2f}\n"
            
            message += f"\n生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            message += "\n\n⚠️ 投资有风险，决策需谨慎。"
            
            return message
            
        except Exception as e:
            logger.error(f"Error creating momentum message: {str(e)}")
            return f"股票 {symbol} 触发 {signal} 信号"
    
    def _create_correlation_message(self, correlated_pairs: List[Dict], threshold: float) -> str:
        """创建相关性消息"""
        try:
            message = f"发现 {len(correlated_pairs)} 对高相关性股票（阈值: {threshold}）:\n\n"
            
            for i, pair in enumerate(correlated_pairs[:5], 1):  # 只显示前5对
                stock1 = pair.get('stock1', 'N/A')
                stock2 = pair.get('stock2', 'N/A')
                correlation = pair.get('correlation', 0)
                
                message += f"{i}. {stock1} ↔ {stock2}: {correlation:.3f}\n"
            
            if len(correlated_pairs) > 5:
                message += f"\n... 还有 {len(correlated_pairs) - 5} 对\n"
            
            message += f"\n生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            message += "\n\n高相关性可能表明投资组合缺乏分散化。"
            
            return message
            
        except Exception as e:
            logger.error(f"Error creating correlation message: {str(e)}")
            return f"发现 {len(correlated_pairs)} 对高相关性股票"
    
    def _create_summary_message(self, summary_data: Dict) -> str:
        """创建总结消息"""
        try:
            message = "📈 每日股票分析总结\n\n"
            
            # 股票数量
            stocks_count = summary_data.get('stocks_analyzed', 0)
            message += f"分析股票数量: {stocks_count}\n"
            
            # 动量信号统计
            momentum_summary = summary_data.get('momentum_summary', {})
            buy_signals = momentum_summary.get('buy_signals', 0)
            sell_signals = momentum_summary.get('sell_signals', 0)
            neutral_signals = momentum_summary.get('neutral_signals', 0)
            
            message += f"\n动量信号统计:\n"
            message += f"• 买入信号: {buy_signals}\n"
            message += f"• 卖出信号: {sell_signals}\n"
            message += f"• 中性信号: {neutral_signals}\n"
            
            # 相关性统计
            correlation_summary = summary_data.get('correlation_summary', {})
            high_corr_pairs = correlation_summary.get('high_correlation_pairs', 0)
            avg_correlation = correlation_summary.get('average_correlation', 0)
            
            message += f"\n相关性统计:\n"
            message += f"• 高相关性股票对: {high_corr_pairs}\n"
            message += f"• 平均相关系数: {avg_correlation:.3f}\n"
            
            # 市场情况
            market_sentiment = summary_data.get('market_sentiment', 'NEUTRAL')
            message += f"\n市场情绪: {market_sentiment}\n"
            
            message += f"\n生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            
            return message
            
        except Exception as e:
            logger.error(f"Error creating summary message: {str(e)}")
            return "每日股票分析总结生成失败"
    
    def create_topic(self, topic_name: str) -> Optional[str]:
        """
        创建SNS主题
        
        Args:
            topic_name: 主题名称
        
        Returns:
            主题ARN，失败返回None
        """
        try:
            response = self.sns_client.create_topic(Name=topic_name)
            topic_arn = response['TopicArn']
            
            logger.info(f"Created SNS topic: {topic_arn}")
            return topic_arn
            
        except Exception as e:
            logger.error(f"Error creating SNS topic: {str(e)}")
            return None
    
    def subscribe_email(self, topic_arn: str, email: str) -> bool:
        """
        订阅邮箱到SNS主题
        
        Args:
            topic_arn: 主题ARN
            email: 邮箱地址
        
        Returns:
            订阅成功返回True，失败返回False
        """
        try:
            response = self.sns_client.subscribe(
                TopicArn=topic_arn,
                Protocol='email',
                Endpoint=email
            )
            
            logger.info(f"Subscribed {email} to topic {topic_arn}")
            return True
            
        except Exception as e:
            logger.error(f"Error subscribing email to SNS: {str(e)}")
            return False
    
    def list_subscriptions(self, topic_arn: str) -> List[Dict]:
        """
        列出主题的所有订阅
        
        Args:
            topic_arn: 主题ARN
        
        Returns:
            订阅列表
        """
        try:
            response = self.sns_client.list_subscriptions_by_topic(TopicArn=topic_arn)
            return response.get('Subscriptions', [])
            
        except Exception as e:
            logger.error(f"Error listing subscriptions: {str(e)}")
            return []
