# AWS 股票监控系统部署指南

## 系统概述

这是一个部署在AWS上的股票监控系统，具备以下功能：

- 📈 **动量分析**: RSI、MACD、移动平均线、布林带等技术指标
- 🔗 **相关性分析**: 股票间相关性分析和投资组合分散化评估  
- ⏰ **定时执行**: 使用CloudWatch Events自动触发分析
- 📧 **智能通知**: 通过SES邮件和SNS消息发送分析报告
- ☁️ **无服务器架构**: 基于AWS Lambda，按需付费

## 架构图

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   CloudWatch    │───▶│   AWS Lambda     │───▶│   股票数据API    │
│   Events        │    │  (分析引擎)       │    │  (Yahoo Finance) │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                │
                                ▼
                       ┌──────────────────┐
                       │   通知服务        │
                       │  ┌─────────────┐  │
                       │  │ AWS SES     │  │
                       │  │ (邮件发送)   │  │
                       │  └─────────────┘  │
                       │  ┌─────────────┐  │
                       │  │ AWS SNS     │  │
                       │  │ (消息通知)   │  │
                       │  └─────────────┘  │
                       └──────────────────┘
```

## 快速开始

### 前置要求

1. **AWS账户**: 确保有权限使用Lambda、SES、SNS、CloudWatch
2. **AWS CLI**: 安装并配置AWS CLI
3. **Python 3.9+**: 本地开发环境
4. **Git**: 代码版本控制

### 一键部署

#### Windows用户:
```powershell
# 克隆项目
git clone <your-repo-url>
cd stock_monitors

# 运行部署脚本
.\deploy.ps1 -Environment dev -Region us-east-1
```

#### Linux/Mac用户:
```bash
# 克隆项目
git clone <your-repo-url>
cd stock_monitors

# 给脚本执行权限
chmod +x deploy.sh

# 运行部署脚本
./deploy.sh --environment dev --region us-east-1
```

### 手动部署步骤

#### 1. 准备环境
```bash
# 创建虚拟环境
python -m venv venv

# 激活虚拟环境 (Windows)
venv\Scripts\activate
# 或 Linux/Mac
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt
```

#### 2. 配置AWS凭证
```bash
aws configure
# 输入你的Access Key ID, Secret Access Key, Region
```

#### 3. 部署CloudFormation堆栈
```bash
aws cloudformation deploy \
  --template-file infrastructure/cloudformation.yaml \
  --stack-name stock-monitor-dev \
  --parameter-overrides \
    Environment=dev \
    FromEmail=your-email@example.com \
    ToEmail=recipient@example.com \
  --capabilities CAPABILITY_NAMED_IAM \
  --region us-east-1
```

#### 4. 打包并上传Lambda代码
```bash
# 创建部署包
mkdir deployment-package
cp -r src deployment-package/
cp -r config deployment-package/
pip install -r requirements.txt -t deployment-package/

# 打包
cd deployment-package
zip -r ../lambda-deployment-package.zip .
cd ..

# 更新Lambda函数
aws lambda update-function-code \
  --function-name stock-monitor-dev \
  --zip-file fileb://lambda-deployment-package.zip \
  --region us-east-1
```

## 配置说明

### 1. 股票监控列表 (`config/stocks_watchlist.yaml`)

```yaml
stocks:
  tech:
    - symbol: "AAPL"
      name: "Apple Inc."
      weight: 0.2
    - symbol: "MSFT" 
      name: "Microsoft Corporation"
      weight: 0.2
  
portfolios:
  - name: "科技组合"
    description: "科技股动量分析"
    stocks: ["AAPL", "MSFT", "GOOGL"]
```

### 2. 分析参数 (`config/config.yaml`)

```yaml
analysis:
  momentum:
    rsi_period: 14        # RSI周期
    macd_fast: 12         # MACD快线
    macd_slow: 26         # MACD慢线
    sma_short: 20         # 短期移动平均
    sma_long: 50          # 长期移动平均
  
  correlation:
    lookback_period: 60   # 相关性分析回看期
    min_correlation: 0.5  # 最小相关性阈值

notifications:
  email:
    enabled: true
    subject_prefix: "[股票分析]"
```

### 3. 环境变量

在AWS Lambda中设置以下环境变量：

- `FROM_EMAIL`: 发件人邮箱地址
- `TO_EMAIL`: 收件人邮箱地址  
- `SES_REGION`: SES服务区域
- `STAGE`: 环境标识(dev/staging/prod)

## SES邮箱验证

在使用邮件功能前，需要在AWS SES中验证邮箱地址：

1. 登录AWS控制台
2. 进入Simple Email Service (SES)
3. 在"Verified identities"中添加发件人邮箱
4. 检查邮箱并点击验证链接
5. 如果在沙盒模式，也需要验证收件人邮箱

## 监控和调试

### CloudWatch日志
```bash
# 查看Lambda函数日志
aws logs describe-log-groups --log-group-name-prefix "/aws/lambda/stock-monitor"

# 获取最新日志流
aws logs describe-log-streams \
  --log-group-name "/aws/lambda/stock-monitor-dev" \
  --order-by LastEventTime \
  --descending
```

### 手动触发测试
```bash
# 手动调用Lambda函数
aws lambda invoke \
  --function-name stock-monitor-dev \
  --payload '{"source": "manual-test"}' \
  output.json

# 查看结果
cat output.json
```

### 本地测试
```bash
# 运行单元测试
python -m pytest tests/ -v

# 运行本地调试
python src/lambda_function.py
```

## 成本估算

基于典型使用场景的AWS成本估算：

| 服务 | 使用量 | 月费用(USD) |
|------|--------|-------------|
| Lambda | 60次调用/月, 512MB, 30秒 | $0.01 |
| SES | 100封邮件/月 | $0.01 |
| CloudWatch | 日志存储和Events | $0.50 |
| SNS | 可选，基于使用量 | $0.50 |
| **总计** | | **~$1.02/月** |

## 故障排除

### 常见问题

**Q: Lambda函数超时**
```
A: 增加超时时间或优化代码
aws lambda update-function-configuration \
  --function-name stock-monitor-dev \
  --timeout 300
```

**Q: 邮件发送失败**
```
A: 检查SES邮箱验证状态和发送限制
aws ses get-identity-verification-attributes \
  --identities your-email@example.com
```

**Q: 股票数据获取失败**  
```
A: 检查网络连接和API限制，可能需要添加重试逻辑
```

**Q: 权限错误**
```
A: 检查Lambda执行角色权限，确保包含必要的IAM策略
```

### 日志分析

查看具体错误信息：
```bash
# 获取最新错误日志
aws logs filter-log-events \
  --log-group-name "/aws/lambda/stock-monitor-dev" \
  --filter-pattern "ERROR" \
  --start-time $(date -d "1 hour ago" +%s)000
```

## 高级配置

### 1. 自定义调度
修改CloudFormation模板中的`ScheduleExpression`：
```yaml
ScheduleExpression: 'cron(0 9,15 * * MON-FRI)'  # 工作日9点和15点
```

### 2. 多环境部署
```bash
# 部署到生产环境
./deploy.ps1 -Environment prod -Region us-west-2
```

### 3. 自定义分析指标
在`src/analyzers/`目录下添加新的分析器类。

### 4. 集成其他数据源
修改`src/data/stock_data_fetcher.py`添加其他API支持。

## API集成

### Webhook支持
可以通过API Gateway添加HTTP触发器：

```bash
# 创建API Gateway集成
aws apigateway create-rest-api --name stock-monitor-api
```

### 第三方集成
- **Slack**: 修改通知模块添加Slack Webhook
- **Discord**: 添加Discord Bot集成  
- **Telegram**: 集成Telegram Bot API

## 贡献指南

1. Fork 项目
2. 创建功能分支 (`git checkout -b feature/new-indicator`)
3. 提交更改 (`git commit -am 'Add new technical indicator'`)
4. 推送到分支 (`git push origin feature/new-indicator`)
5. 创建Pull Request

## 许可证

MIT License - 详见[LICENSE](LICENSE)文件

## 支持

如有问题或建议，请：
1. 查看[常见问题](#故障排除)
2. 创建GitHub Issue
3. 查看AWS官方文档

---

**⚠️ 免责声明**: 本系统仅供学习和参考使用，不构成投资建议。投资有风险，决策需谨慎。
