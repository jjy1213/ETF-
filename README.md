# ETF 月末 200MA 风险过滤量化研究项目

这是一个适合初学者阅读和运行的 Python 量化研究示例。项目使用 `yfinance` 下载 ETF 数据，用 `pandas` 计算 QQQ 与 TLT 的 200 日均线，并在每月最后一个交易日生成调仓信号和策略资金曲线。

## 项目目录结构

```text
.
├── main.py              # 主流程控制：串联数据、策略、回测、绩效和输出
├── data.py              # 数据模块：下载价格数据、保存输出文件
├── strategy.py          # 策略模块：计算均线、识别月末交易日、生成调仓信号
├── backtest.py          # 回测模块：生成每日持仓、计算收益和资金曲线、绘图
├── metrics.py           # 绩效模块：计算年度收益、最大回撤和 Sharpe Ratio
├── report.py            # 报告模块：对比策略与 QQQ 买入持有
├── requirements.txt     # Python 依赖列表
├── README.md            # 项目说明文档
└── outputs/             # 运行 main.py 后自动生成，保存研究结果
    ├── prices.csv
    ├── moving_average.csv
    ├── rebalance_signals.csv
    ├── signals.csv
    ├── strategy_result.csv
    ├── annual_returns.csv
    ├── performance_summary.csv
    ├── report.csv
    ├── report.txt
    └── equity_curve.png
```

## 每个文件的作用

- `main.py`：只负责流程控制，按顺序调用各模块完成完整研究流程。
- `data.py`：负责使用 `yfinance` 下载 ETF 价格数据，并保存 CSV 输出文件。
- `strategy.py`：负责计算 200 日均线、识别月末交易日，并生成月末调仓信号。
- `backtest.py`：负责把月末信号转换为每日持仓，计算策略收益、资金曲线并绘图。
- `metrics.py`：负责计算每年收益率、最大回撤、Sharpe Ratio，并打印绩效摘要。
- `report.py`：负责对比策略与 QQQ 买入持有的年化收益率、最大回撤、Sharpe Ratio、月度胜率和盈亏比。
- `requirements.txt`：记录运行项目所需的第三方库，包括 `yfinance`、`pandas` 和 `matplotlib`。
- `README.md`：说明项目目标、目录结构、运行方式和输出结果。
- `outputs/prices.csv`：保存 QQQ 和 TLT 的历史复权收盘价。
- `outputs/moving_average.csv`：保存 QQQ 和 TLT 的 200 日均线。
- `outputs/rebalance_signals.csv`：保存每月最后一个交易日生成的调仓信号。
- `outputs/signals.csv`：保存每日调仓信号和实际持仓，持仓可能是 `QQQ`、`TLT` 或 `CASH`。
- `outputs/strategy_result.csv`：保存每日持仓、策略收益和资金曲线。
- `outputs/annual_returns.csv`：保存每年收益率。
- `outputs/performance_summary.csv`：保存最终资金、累计收益、最大回撤和 Sharpe Ratio。
- `outputs/report.csv`：保存策略与 QQQ 买入持有的对比指标。
- `outputs/report.txt`：保存适合阅读的纯文本对比报告。
- `outputs/equity_curve.png`：保存由 `matplotlib` 绘制的资金曲线图。

## 策略逻辑

1. 下载 QQQ 和 TLT 的历史复权收盘价。
2. 分别计算两个 ETF 的 200 日均线。
3. 只在每月最后一个交易日生成调仓信号。
4. 如果 QQQ 高于或等于 200 日均线，则持有 QQQ。
5. 如果 QQQ 低于 200 日均线，则检查 TLT；如果 TLT 高于或等于 200 日均线，则持有 TLT。
6. 如果 TLT 也低于 200 日均线，则持有现金，信号为 `CASH`。
7. 月末收盘后得到的信号从下一个交易日开始执行，避免未来函数。

## 如何运行

```bash
python3 -m pip install -r requirements.txt
python3 main.py
```

运行后，终端会输出最新持仓信号、最终资金曲线值、累计收益率、最大回撤、Sharpe Ratio 和每年收益率，结果文件会保存到 `outputs/` 目录，并自动生成策略 vs QQQ 买入持有的对比报告。
