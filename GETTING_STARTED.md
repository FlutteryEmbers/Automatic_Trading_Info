# AWS 股票监控系统快速上手指南

## 🎯 项目简介

这是一个完整的AWS云端股票监控解决方案，提供：
- **动量分析**: RSI、MACD、移动平均线等技术指标分析
- **相关性分析**: 股票间相关性和投资组合风险评估
- **定时报告**: 自动化分析并通过邮件发送报告
- **AWS部署**: 基于Lambda的无服务器架构，成本低廉

## 🚀 三分钟快速开始

### 1. 环境准备
```powershell
# 确保已安装 Python 3.9+ 和 AWS CLI
python --version
aws --version

# 配置 AWS 凭证
aws configure
```

### 2. 安装依赖
```powershell
# 克隆项目到本地
git clone <your-repo-url>
cd stock_monitors

# 安装Python依赖
pip install -r requirements.txt
```

### 3. 本地测试
```powershell
# 运行本地测试，验证功能
python run_local_test.py
```

### 4. 部署到AWS
```powershell
# 一键部署（会提示输入邮箱地址）
.\deploy.ps1

# 或指定参数
.\deploy.ps1 -Environment prod -Region us-west-2
```

## 📊 功能展示

### 动量分析报告示例
```
📈 AAPL 动量分析
• RSI: 65.2 (正常区间)
• MACD: 0.0052 (金叉信号)
• 移动平均: 短期线上穿长期线
• 综合信号: BUY ✅
```

### 相关性分析示例
```
🔗 投资组合相关性分析
• AAPL ↔ MSFT: 0.78 (强相关)
• GOOGL ↔ AMZN: 0.65 (中等相关)
• 分散化评分: 0.67 (良好)
```

## ⚙️ 自定义配置

### 修改监控股票列表
编辑 `config/stocks_watchlist.yaml`:
```yaml
stocks:
  my_portfolio:
    - symbol: "NVDA"
      name: "NVIDIA Corporation"
      weight: 0.3
    - symbol: "AMD"
      name: "Advanced Micro Devices"
      weight: 0.2
```

### 调整分析参数
编辑 `config/config.yaml`:
```yaml
analysis:
  momentum:
    rsi_period: 21      # 改为21天RSI
    sma_short: 10       # 短期均线改为10天
  correlation:
    min_correlation: 0.6 # 提高相关性阈值
```

### 修改发送频率
在部署时修改定时表达式：
```yaml
# 每天上午9点发送
schedule_expression: "cron(0 9 * * *)"

# 每周一上午9点发送  
schedule_expression: "cron(0 9 * * MON)"
```

## 📧 邮件报告样式

系统会发送包含以下内容的HTML邮件：

1. **股票价格概览** - 最新价格和涨跌幅
2. **动量分析结果** - 各种技术指标和交易信号
3. **相关性分析** - 股票间的相关性矩阵和风险评估
4. **投资建议总结** - 基于分析结果的综合建议

## 💰 成本控制

### 预期费用（每月）
- **Lambda**: ~$0.01 (60次执行)
- **SES**: ~$0.01 (100封邮件)
- **CloudWatch**: ~$0.50 (日志和监控)
- **总计**: **约$0.52/月**

### 节省成本的建议
1. 减少运行频率（如每日一次改为每周一次）
2. 监控更少的股票
3. 使用更短的数据历史周期

## 🔧 故障排除

### 常见问题及解决方案

**问题**: 邮件发送失败
```
解决: 检查SES邮箱验证状态
aws ses get-identity-verification-attributes --identities your-email@example.com
```

**问题**: Lambda函数超时
```
解决: 增加超时时间或减少监控股票数量
aws lambda update-function-configuration --function-name stock-monitor-dev --timeout 300
```

**问题**: 股票数据获取失败
```
解决: 检查网络连接，可能是Yahoo Finance API限制
```

## 📈 高级功能

### 1. 添加自定义技术指标
在 `src/analyzers/momentum_analyzer.py` 中添加新的指标计算方法：

```python
def calculate_custom_indicator(self, data: pd.Series) -> pd.Series:
    # 实现你的自定义指标
    pass
```

### 2. 集成其他数据源
修改 `src/data/stock_data_fetcher.py` 支持其他API：

```python
def fetch_from_alpha_vantage(self, symbol: str):
    # 集成Alpha Vantage API
    pass
```

### 3. 添加Slack通知
创建新的通知模块支持Slack Webhook。

### 4. 实现实时监控
修改为WebSocket连接实现实时数据流监控。

## 📚 学习资源

### 技术指标学习
- [RSI指标详解](https://www.investopedia.com/terms/r/rsi.asp)
- [MACD指标使用](https://www.investopedia.com/terms/m/macd.asp)
- [相关性分析原理](https://www.investopedia.com/terms/c/correlation.asp)

### AWS服务文档
- [AWS Lambda开发指南](https://docs.aws.amazon.com/lambda/)
- [Amazon SES用户指南](https://docs.aws.amazon.com/ses/)
- [CloudWatch Events规则](https://docs.aws.amazon.com/cloudwatch/latest/events/)

## 🤝 社区和支持

### 获取帮助
1. 查看 [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) 获取详细部署说明
2. 运行 `python tests/test_stock_monitor.py` 执行单元测试
3. 检查CloudWatch日志获取运行时错误信息

### 贡献代码
我们欢迎各种形式的贡献：
- 🐛 报告Bug
- 💡 提出新功能建议  
- 📝 改进文档
- 🔧 提交代码修复

### 路线图
- [ ] 支持加密货币监控
- [ ] 添加机器学习预测模型
- [ ] 实现移动端APP
- [ ] 集成更多第三方数据源

## ⚠️ 重要提醒

1. **投资风险**: 本系统仅供学习参考，不构成投资建议
2. **数据准确性**: 请验证数据源的准确性和时效性
3. **成本控制**: 定期检查AWS账单，避免意外费用
4. **安全性**: 妥善保管AWS访问密钥，不要提交到代码仓库

---

**开始您的智能投资分析之旅！** 🚀📊

如有任何问题，欢迎创建GitHub Issue或联系维护者。
