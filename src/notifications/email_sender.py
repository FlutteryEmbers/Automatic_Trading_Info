"""
邮件发送模块
使用AWS SES发送分析报告邮件
"""
import boto3
import json
import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from typing import Dict, List, Optional
from datetime import datetime
import pandas as pd

logger = logging.getLogger(__name__)

class EmailSender:
    """邮件发送器"""
    
    def __init__(self, region_name: str = 'us-east-1'):
        """
        初始化邮件发送器
        
        Args:
            region_name: AWS区域
        """
        self.region_name = region_name
        self.ses_client = boto3.client('ses', region_name=region_name)
    
    def send_analysis_report(self, 
                           to_emails: List[str], 
                           from_email: str, 
                           subject: str,
                           momentum_results: Dict = None,
                           correlation_results: Dict = None,
                           stock_prices: Dict = None) -> bool:
        """
        发送分析报告邮件
        
        Args:
            to_emails: 收件人邮箱列表
            from_email: 发件人邮箱
            subject: 邮件主题
            momentum_results: 动量分析结果
            correlation_results: 相关性分析结果
            stock_prices: 股票价格数据
        
        Returns:
            发送成功返回True，失败返回False
        """
        try:
            # 创建邮件内容
            email_content = self._create_email_content(
                momentum_results, 
                correlation_results, 
                stock_prices
            )
            
            # 发送邮件
            response = self.ses_client.send_email(
                Source=from_email,
                Destination={
                    'ToAddresses': to_emails
                },
                Message={
                    'Subject': {
                        'Data': subject,
                        'Charset': 'UTF-8'
                    },
                    'Body': {
                        'Html': {
                            'Data': email_content,
                            'Charset': 'UTF-8'
                        }
                    }
                }
            )
            
            logger.info(f"Email sent successfully. MessageId: {response['MessageId']}")
            return True
            
        except Exception as e:
            logger.error(f"Error sending email: {str(e)}")
            return False
    
    def _create_email_content(self, 
                            momentum_results: Dict = None,
                            correlation_results: Dict = None,
                            stock_prices: Dict = None) -> str:
        """
        创建邮件HTML内容
        
        Args:
            momentum_results: 动量分析结果
            correlation_results: 相关性分析结果
            stock_prices: 股票价格数据
        
        Returns:
            HTML格式的邮件内容
        """
        try:
            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
                <title>股票分析报告</title>
                <style>
                    body {{
                        font-family: Arial, sans-serif;
                        line-height: 1.6;
                        color: #333;
                        max-width: 800px;
                        margin: 0 auto;
                        padding: 20px;
                    }}
                    .header {{
                        background-color: #2c3e50;
                        color: white;
                        padding: 20px;
                        text-align: center;
                        border-radius: 8px;
                        margin-bottom: 20px;
                    }}
                    .section {{
                        background-color: #f8f9fa;
                        padding: 15px;
                        margin-bottom: 20px;
                        border-radius: 8px;
                        border-left: 4px solid #3498db;
                    }}
                    .alert {{
                        padding: 12px;
                        margin-bottom: 15px;
                        border-radius: 4px;
                    }}
                    .alert-success {{
                        background-color: #d4edda;
                        border-color: #c3e6cb;
                        color: #155724;
                    }}
                    .alert-warning {{
                        background-color: #fff3cd;
                        border-color: #ffeaa7;
                        color: #856404;
                    }}
                    .alert-danger {{
                        background-color: #f8d7da;
                        border-color: #f5c6cb;
                        color: #721c24;
                    }}
                    table {{
                        width: 100%;
                        border-collapse: collapse;
                        margin-bottom: 20px;
                    }}
                    th, td {{
                        padding: 12px;
                        text-align: left;
                        border-bottom: 1px solid #ddd;
                    }}
                    th {{
                        background-color: #3498db;
                        color: white;
                    }}
                    .signal-buy {{
                        color: #27ae60;
                        font-weight: bold;
                    }}
                    .signal-sell {{
                        color: #e74c3c;
                        font-weight: bold;
                    }}
                    .signal-neutral {{
                        color: #95a5a6;
                        font-weight: bold;
                    }}
                    .footer {{
                        text-align: center;
                        color: #666;
                        font-size: 12px;
                        margin-top: 30px;
                        padding-top: 20px;
                        border-top: 1px solid #ddd;
                    }}
                </style>
            </head>
            <body>
                <div class="header">
                    <h1>📈 股票分析报告</h1>
                    <p>生成时间: {datetime.now().strftime('%Y年%m月%d日 %H:%M:%S')}</p>
                </div>
            """
            
            # 添加股票价格信息
            if stock_prices:
                html_content += self._create_price_section(stock_prices)
            
            # 添加动量分析结果
            if momentum_results:
                html_content += self._create_momentum_section(momentum_results)
            
            # 添加相关性分析结果
            if correlation_results:
                html_content += self._create_correlation_section(correlation_results)
            
            # 添加页脚
            html_content += """
                <div class="footer">
                    <p>本报告由AWS股票监控系统自动生成</p>
                    <p>⚠️ 投资有风险，决策需谨慎。本报告仅供参考，不构成投资建议。</p>
                </div>
            </body>
            </html>
            """
            
            return html_content
            
        except Exception as e:
            logger.error(f"Error creating email content: {str(e)}")
            return "<html><body><h1>报告生成失败</h1><p>请查看系统日志获取详细信息。</p></body></html>"
    
    def _create_price_section(self, stock_prices: Dict) -> str:
        """创建股票价格部分"""
        try:
            html = '<div class="section"><h2>💰 最新股票价格</h2><table>'
            html += '<tr><th>股票代码</th><th>最新价格</th><th>涨跌幅</th></tr>'
            
            for symbol, price_info in stock_prices.items():
                if isinstance(price_info, dict):
                    current_price = price_info.get('current_price', 0)
                    change_percent = price_info.get('change_percent', 0)
                    
                    # 根据涨跌设置颜色
                    change_class = 'signal-buy' if change_percent > 0 else 'signal-sell' if change_percent < 0 else 'signal-neutral'
                    change_symbol = '+' if change_percent > 0 else ''
                    
                    html += f'''
                    <tr>
                        <td><strong>{symbol}</strong></td>
                        <td>${current_price:.2f}</td>
                        <td class="{change_class}">{change_symbol}{change_percent:.2f}%</td>
                    </tr>
                    '''
                else:
                    html += f'''
                    <tr>
                        <td><strong>{symbol}</strong></td>
                        <td>${price_info:.2f}</td>
                        <td class="signal-neutral">N/A</td>
                    </tr>
                    '''
            
            html += '</table></div>'
            return html
            
        except Exception as e:
            logger.error(f"Error creating price section: {str(e)}")
            return '<div class="section"><h2>💰 价格信息</h2><p>价格数据加载失败</p></div>'
    
    def _create_momentum_section(self, momentum_results: Dict) -> str:
        """创建动量分析部分"""
        try:
            html = '<div class="section"><h2>📊 动量分析</h2>'
            
            for symbol, result in momentum_results.items():
                if 'signals' in result:
                    signals = result['signals']
                    indicators = result.get('indicators', {})
                    
                    # 总体信号
                    overall_signal = signals.get('overall_signal', 'NEUTRAL')
                    signal_class = f'signal-{overall_signal.lower()}'
                    
                    html += f'<h3>{symbol}</h3>'
                    html += f'<div class="alert alert-info">'
                    html += f'<strong>综合信号: <span class="{signal_class}">{overall_signal}</span></strong>'
                    html += f'</div>'
                    
                    # 技术指标表格
                    html += '<table>'
                    html += '<tr><th>指标</th><th>数值</th><th>信号</th></tr>'
                    
                    # RSI
                    rsi_value = indicators.get('rsi', 0)
                    rsi_signal = signals.get('rsi_signal', 'NEUTRAL')
                    rsi_signal_class = f'signal-{rsi_signal.lower()}'
                    html += f'<tr><td>RSI</td><td>{rsi_value:.2f}</td><td class="{rsi_signal_class}">{rsi_signal}</td></tr>'
                    
                    # MACD
                    macd_value = indicators.get('macd', 0)
                    macd_signal = signals.get('macd_signal', 'NEUTRAL')
                    macd_signal_class = f'signal-{macd_signal.lower()}'
                    html += f'<tr><td>MACD</td><td>{macd_value:.4f}</td><td class="{macd_signal_class}">{macd_signal}</td></tr>'
                    
                    # 移动平均
                    ma_signal = signals.get('ma_signal', 'NEUTRAL')
                    ma_signal_class = f'signal-{ma_signal.lower()}'
                    sma_short = indicators.get('sma_short', 0)
                    sma_long = indicators.get('sma_long', 0)
                    html += f'<tr><td>移动平均</td><td>短期: {sma_short:.2f} / 长期: {sma_long:.2f}</td><td class="{ma_signal_class}">{ma_signal}</td></tr>'
                    
                    html += '</table>'
            
            html += '</div>'
            return html
            
        except Exception as e:
            logger.error(f"Error creating momentum section: {str(e)}")
            return '<div class="section"><h2>📊 动量分析</h2><p>动量分析数据加载失败</p></div>'
    
    def _create_correlation_section(self, correlation_results: Dict) -> str:
        """创建相关性分析部分"""
        try:
            html = '<div class="section"><h2>🔗 相关性分析</h2>'
            
            # 高相关性股票对
            if 'highly_correlated_pairs' in correlation_results:
                html += '<h3>高相关性股票对</h3>'
                pairs = correlation_results['highly_correlated_pairs']
                
                if pairs:
                    html += '<table>'
                    html += '<tr><th>股票1</th><th>股票2</th><th>相关系数</th><th>强度</th></tr>'
                    
                    for pair in pairs[:5]:  # 显示前5对
                        corr_value = pair['correlation']
                        corr_class = 'signal-buy' if corr_value > 0.7 else 'signal-warning' if corr_value > 0.5 else 'signal-neutral'
                        
                        html += f'''
                        <tr>
                            <td>{pair['stock1']}</td>
                            <td>{pair['stock2']}</td>
                            <td class="{corr_class}">{corr_value:.3f}</td>
                            <td>{pair['strength']}</td>
                        </tr>
                        '''
                    
                    html += '</table>'
                else:
                    html += '<p>未发现显著的高相关性股票对</p>'
            
            # 投资组合分散化评分
            if 'diversification_score' in correlation_results:
                score = correlation_results['diversification_score']
                score_percent = score * 100
                
                if score > 0.7:
                    score_class = 'alert-success'
                    score_text = '良好'
                elif score > 0.4:
                    score_class = 'alert-warning'
                    score_text = '中等'
                else:
                    score_class = 'alert-danger'
                    score_text = '较差'
                
                html += f'''
                <div class="{score_class}">
                    <strong>投资组合分散化评分: {score_percent:.1f}% ({score_text})</strong>
                </div>
                '''
            
            # 分析总结
            if 'summary' in correlation_results:
                html += f'<p><strong>分析总结:</strong> {correlation_results["summary"]}</p>'
            
            html += '</div>'
            return html
            
        except Exception as e:
            logger.error(f"Error creating correlation section: {str(e)}")
            return '<div class="section"><h2>🔗 相关性分析</h2><p>相关性分析数据加载失败</p></div>'
    
    def verify_email_address(self, email: str) -> bool:
        """
        验证邮箱地址是否在SES中已验证
        
        Args:
            email: 邮箱地址
        
        Returns:
            验证状态
        """
        try:
            response = self.ses_client.get_identity_verification_attributes(
                Identities=[email]
            )
            
            verification_attributes = response.get('VerificationAttributes', {})
            email_status = verification_attributes.get(email, {})
            
            return email_status.get('VerificationStatus') == 'Success'
            
        except Exception as e:
            logger.error(f"Error verifying email address {email}: {str(e)}")
            return False
