"""
本地测试运行器
用于在本地环境测试股票监控系统
"""
import os
import sys
import json
import yaml
import logging
from datetime import datetime

# 添加src目录到Python路径
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def load_config():
    """加载配置文件"""
    try:
        with open('config/config.yaml', 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        with open('config/stocks_watchlist.yaml', 'r', encoding='utf-8') as f:
            stocks = yaml.safe_load(f)
        return config, stocks
    except Exception as e:
        print(f"Error loading config: {e}")
        return None, None

def run_local_test():
    """运行本地测试"""
    print("🚀 启动本地股票监控系统测试...")
    print("=" * 50)
    
    # 加载配置
    config, stocks_config = load_config()
    if not config or not stocks_config:
        print("❌ 配置文件加载失败")
        return
    
    # 导入模块
    try:
        from data.stock_data_fetcher import StockDataFetcher
        from analyzers.momentum_analyzer import MomentumAnalyzer
        from analyzers.correlation_analyzer import CorrelationAnalyzer
    except ImportError as e:
        print(f"❌ 模块导入失败: {e}")
        print("请确保已安装所有依赖: pip install -r requirements.txt")
        return
    
    # 初始化组件
    data_fetcher = StockDataFetcher()
    momentum_analyzer = MomentumAnalyzer(config.get('analysis', {}).get('momentum', {}))
    correlation_analyzer = CorrelationAnalyzer(config.get('analysis', {}).get('correlation', {}))
    
    # 获取测试股票列表
    test_symbols = []
    stocks = stocks_config.get('stocks', {})
    for category, stock_list in stocks.items():
        for stock in stock_list[:2]:  # 每个类别取前2只股票进行测试
            test_symbols.append(stock['symbol'])
    
    print(f"📊 测试股票: {test_symbols}")
    print("⏰ 开始获取股票数据...")
    
    # 获取股票数据
    analysis_config = config.get('analysis', {})
    data_config = analysis_config.get('data', {})
    
    stock_data = data_fetcher.fetch_multiple_stocks(
        test_symbols,
        period=data_config.get('period', '3mo'),  # 使用较短周期进行测试
        interval=data_config.get('interval', '1d')
    )
    
    if not stock_data:
        print("❌ 无法获取股票数据，请检查网络连接")
        return
    
    print(f"✅ 成功获取 {len(stock_data)} 只股票的数据")
    
    # 运行动量分析
    print("\n📈 运行动量分析...")
    momentum_results = {}
    
    for symbol, data in stock_data.items():
        try:
            result = momentum_analyzer.analyze_momentum_signals(data)
            if result:
                momentum_results[symbol] = result
                signals = result.get('signals', {})
                overall_signal = signals.get('overall_signal', 'UNKNOWN')
                print(f"  {symbol}: {overall_signal} (强度: {result.get('strength', 0):.2f})")
        except Exception as e:
            print(f"  {symbol}: ❌ 分析失败 - {e}")
    
    # 运行相关性分析
    print("\n🔗 运行相关性分析...")
    try:
        correlation_result = correlation_analyzer.generate_correlation_report(stock_data)
        
        if 'highly_correlated_pairs' in correlation_result:
            pairs = correlation_result['highly_correlated_pairs']
            print(f"  发现 {len(pairs)} 对高相关性股票")
            
            for i, pair in enumerate(pairs[:3], 1):  # 显示前3对
                print(f"    {i}. {pair['stock1']} ↔ {pair['stock2']}: {pair['correlation']:.3f}")
        
        if 'diversification_score' in correlation_result:
            score = correlation_result['diversification_score']
            print(f"  投资组合分散化评分: {score:.2f}")
            
    except Exception as e:
        print(f"  ❌ 相关性分析失败 - {e}")
        correlation_result = {}
    
    # 生成测试报告
    print("\n📄 生成测试报告...")
    
    # 统计信号
    buy_signals = sum(1 for result in momentum_results.values() 
                     if result.get('signals', {}).get('overall_signal') == 'BUY')
    sell_signals = sum(1 for result in momentum_results.values() 
                      if result.get('signals', {}).get('overall_signal') == 'SELL')
    neutral_signals = sum(1 for result in momentum_results.values() 
                         if result.get('signals', {}).get('overall_signal') == 'NEUTRAL')
    
    print(f"\n📊 分析总结:")
    print(f"  分析股票数量: {len(momentum_results)}")
    print(f"  买入信号: {buy_signals}")
    print(f"  卖出信号: {sell_signals}")
    print(f"  中性信号: {neutral_signals}")
    
    if correlation_result:
        high_corr_pairs = len(correlation_result.get('highly_correlated_pairs', []))
        print(f"  高相关性股票对: {high_corr_pairs}")
    
    # 市场情绪
    if buy_signals > sell_signals:
        market_sentiment = "看涨 📈"
    elif sell_signals > buy_signals:
        market_sentiment = "看跌 📉"
    else:
        market_sentiment = "中性 ➡️"
    
    print(f"  市场情绪: {market_sentiment}")
    
    # 保存测试结果
    test_results = {
        'timestamp': datetime.now().isoformat(),
        'test_mode': True,
        'stocks_analyzed': len(momentum_results),
        'momentum_results': momentum_results,
        'correlation_results': correlation_result,
        'summary': {
            'buy_signals': buy_signals,
            'sell_signals': sell_signals,
            'neutral_signals': neutral_signals,
            'market_sentiment': market_sentiment.split()[0]  # 只取文字部分
        }
    }
    
    # 保存为JSON文件
    try:
        with open('test_results.json', 'w', encoding='utf-8') as f:
            json.dump(test_results, f, indent=2, default=str, ensure_ascii=False)
        print(f"\n💾 测试结果已保存到 test_results.json")
    except Exception as e:
        print(f"\n❌ 保存测试结果失败: {e}")
    
    print("\n✅ 本地测试完成！")
    print("=" * 50)
    print("💡 提示:")
    print("  - 查看 test_results.json 获取详细结果")
    print("  - 运行 python tests/test_stock_monitor.py 执行单元测试")
    print("  - 准备好后可以运行 deploy.ps1 部署到AWS")

if __name__ == "__main__":
    run_local_test()
