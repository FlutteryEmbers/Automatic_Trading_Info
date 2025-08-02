# AWS 股票监控系统

一个部署在AWS上的股票分析监控系统，提供动量分析和相关性分析功能，并定时发送分析报告。

## 功能特性

- 📈 股票动量分析（RSI, MACD, 移动平均线等）
- 🔗 股票相关性分析
- ⏰ 定时分析和报告
- 📧 邮件通知功能
- ☁️ AWS Lambda无服务器部署
- 📊 支持多种技术指标

## 项目结构

```
stock_monitors/
├── src/
│   ├── analyzers/
│   │   ├── momentum_analyzer.py
│   │   └── correlation_analyzer.py
│   ├── data/
│   │   └── stock_data_fetcher.py
│   ├── notifications/
│   │   ├── email_sender.py
│   │   └── sns_sender.py
│   └── lambda_function.py
├── infrastructure/
│   ├── cloudformation.yaml
│   └── terraform/
├── config/
│   ├── config.yaml
│   └── stocks_watchlist.yaml
├── tests/
├── requirements.txt
├── serverless.yml
└── deploy.sh
```

## 部署方法

### 方法1: Serverless Framework
```bash
npm install -g serverless
pip install -r requirements.txt
serverless deploy
```

### 方法2: AWS CLI + CloudFormation
```bash
./deploy.sh
```

## 配置

在 `config/config.yaml` 中配置：
- 股票代码列表
- 分析参数
- 通知设置
- AWS资源配置

## 依赖服务

- AWS Lambda
- AWS CloudWatch Events
- AWS SES (邮件发送)
- AWS SNS (消息通知)
- AWS Systems Manager (参数存储)
