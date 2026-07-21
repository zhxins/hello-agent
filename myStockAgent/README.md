# 智能投资助手Agent

基于hello-agents库实现的A股投资分析助手，输入股票名称或代码，自动完成实时行情查询、均线分析、MACD指标、量价关系判断和止损位计算，给出综合买卖建议。

## 📝 项目简介

- 输入股票名称或代码（如"贵州茅台"或"600519"），一键获取完整技术分析报告
- 整合行情、均线、MACD、成交量、止损位五大维度，避免单一指标误判
- 适用于A股散户日常选股、买卖点判断和风险控制


## ✨ 核心功能

- **实时行情查询**: 当前价/涨跌幅/成交量/市盈率/总市值
- **均线分析**: MA5/MA10/MA20 金叉死叉信号 + 多空排列判断
- **MACD指标**: DIF/DEA 金叉死叉 + 零轴位置 + 红绿柱趋势
- **量价分析**: 量比 + 放量缩量 + 量价配合判断
- **止损位计算**: MA20支撑 / 近10日低点 / -7%固定比例 三重参考
- **综合买卖建议**: 多信号共振判断，给出"逢低买入/观望/减仓"建议


##  🛠️ 技术栈

基于HelloAgentsLearn项目中的ReAct框架实现:

- **ReAct Agent**: 推理-行动循环框架（Thought → Action → Observation）
- **HelloAgentsLLM**: 统一LLM调用接口（DeepSeek API）
- **腾讯财经API**: 实时行情(qt.gtimg.cn) + 日K线(web.ifzq.gtimg.cn) 数据源
- **Tool Registry**: 工具注册和管理


## 工具实现

1. **stock_query**: 查询A股实时行情（腾讯API，自动识别沪深交易所）
2. **ma_analysis**: MA5/MA10/MA20 均线分析 + 金叉死叉判断
3. **analyze_macd**: MACD指标计算（DIF/DEA/柱状图）
4. **analyze_volume**: 成交量分析（量比、量价配合）
5. **calc_stop_loss**: 止损位计算（MA20/近10日低点/-7%三重参考）
6. **stock_analysis**: 综合工具（默认调用），一次返回以上全部分析


## 🚀 快速开始
### 环境要求

- Python 3.10+ (推荐 conda py310 环境)

### 安装依赖

```bash
pip install -r requirements.txt
```

### 配置API密钥

编辑 `agent/.env` 文件，配置以下参数:

### LLM配置
- `API_KEY`: DeepSeek API密钥
- `BASE_URL`: API服务地址，如 `https://api.deepseek.com`
- `LLM_MODEL_ID`: 模型ID，如 `deepseek-chat`


### 运行项目

#### 运行主程序:

```bash
cd agent
python run_stock_agent.py
```

#### 查询示例

- "贵州茅台现在能买吗？"
- "帮我分析一下平安银行"
- "对比一下茅台和五粮液的均线"
- "中国黄金现在的止损位设多少合适？"


## 📂 项目结构

```
myStockAgent/
├── agent/
│   ├── .env                  # LLM API配置
│   ├── __init__.py
│   └── run_stock_agent.py    # ReAct主循环 + 工具注册
├── tools/
│   ├── __init__.py
│   ├── my_stock_tool.py      # 实时行情查询
│   ├── my_ma_tool.py         # 均线分析
│   └── my_indicator_tool.py  # MACD + 量价 + 止损
├── requirements.txt
└── README.md
```


## 🔮 未来计划

- 增加 KDJ、布林带(BOLL) 等技术指标
- 增加北向资金、板块资金流向监控
- 增加自选股批量监控和信号汇总
- 增加多周期共振分析（日线+周线）
- 增加财报基本面数据（PE/PB历史分位、ROE）
- 接入 plan_solve 智能体做投资组合分析


## 🤝 贡献指南

欢迎提出Issue和Pull Request！

## 📄 许可证

MIT License

## 👤 作者

- GitHub: [@mattow](https://github.com/zhxins/)

## 🙏 致谢

感谢Datawhale社区和Hello-Agents项目！
感谢腾讯财经提供的免费行情数据接口！
