# ETF 月末 200MA 动量择强量化研究项目

这是一个适合初学者阅读和运行的 Python 量化研究示例。项目使用 `yfinance` 下载 QQQ、SPY 与 TLT 数据，用 `pandas` 比较 QQQ 和 SPY 的 60 日动量，并结合 200 日均线在每月最后一个交易日生成调仓信号和策略资金曲线。

## 项目目录结构

```text
.
├── main.py              # 主流程控制：串联数据、策略、回测、绩效和输出
├── data.py              # 数据模块：下载价格数据、保存输出文件
├── strategy.py          # 策略模块：计算均线、识别月末交易日、生成调仓信号
├── backtest.py          # 回测模块：生成每日持仓、计算收益和资金曲线、绘图
├── metrics.py           # 绩效模块：计算年度收益、最大回撤和 Sharpe Ratio
├── report.py            # 报告模块：对比策略与 QQQ 买入持有
├── sensitivity.py       # 敏感性分析模块：评估波动率仓位参数稳定性
├── requirements.txt     # Python 依赖列表
├── README.md            # 项目说明文档
├── sample_data/         # 内置样例价格数据，供限流或离线时备用
│   └── prices.csv
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
    ├── rolling_sharpe.csv
    ├── rolling_sharpe.png
    ├── walk_forward.csv
    ├── walk_forward.txt
    ├── volatility_sensitivity.csv
    ├── volatility_sensitivity_sharpe.png
    ├── volatility_sensitivity_drawdown.png
    ├── integrated_report.html
    └── equity_curve.png
```

## 每个文件的作用

- `main.py`：只负责流程控制，按顺序调用各模块完成完整研究流程。
- `data.py`：负责使用 `yfinance` 下载 ETF 价格数据，并保存 CSV 输出文件。
- `strategy.py`：负责计算 200 日均线、60 日动量、识别月末交易日，并生成月末调仓信号。
- `backtest.py`：负责把月末信号转换为每日持仓，计算策略收益、资金曲线并绘图。
- `metrics.py`：负责计算每年收益率、最大回撤、Sharpe Ratio，并打印绩效摘要。
- `report.py`：负责对比策略与 QQQ 买入持有的年化收益率、最大回撤、Sharpe Ratio、月度胜率和盈亏比。
- `sensitivity.py`：负责生成波动率仓位参数敏感性 CSV 和热力图。
- `requirements.txt`：记录运行项目所需的第三方库，包括 `yfinance`、`pandas` 和 `matplotlib`。
- `README.md`：说明项目目标、目录结构、运行方式和输出结果。
- `sample_data/prices.csv`：内置包含 QQQ、SPY、TLT 的样例价格数据，供在线数据源失败时备用。
- `outputs/prices.csv`：保存 QQQ、SPY、TLT 的历史复权收盘价。
- `outputs/moving_average.csv`：保存 QQQ、SPY、TLT 的 200 日均线。
- `outputs/rebalance_signals.csv`：保存每月最后一个交易日生成的调仓信号。
- `outputs/signals.csv`：保存每日调仓信号和实际持仓，持仓可能是 `QQQ`、`SPY`、`TLT` 或 `CASH`。
- `outputs/strategy_result.csv`：保存每日持仓、策略收益和资金曲线。
- `outputs/annual_returns.csv`：保存每年收益率，并新增当年 `QQQ/SPY/TLT/CASH` 月度持仓分布。
- `outputs/performance_summary.csv`：保存最终资金、累计收益、最大回撤和 Sharpe Ratio。
- `outputs/report.csv`：保存策略与 QQQ 买入持有的对比指标。
- `outputs/report.txt`：保存适合阅读的纯文本对比报告。
- `outputs/rolling_sharpe.csv`：保存 252 日 rolling Sharpe Ratio。
- `outputs/rolling_sharpe.png`：保存 rolling Sharpe 图表。
- `outputs/walk_forward.csv`：保存按年份滚动推进的样本外测试结果。
- `outputs/walk_forward.txt`：保存 walk-forward 纯文本报告。
- `outputs/volatility_sensitivity.csv`：保存目标波动率和波动率回看期的敏感性分析明细。
- `outputs/volatility_sensitivity_sharpe.png`：保存 Sharpe Ratio 参数敏感性热力图。
- `outputs/volatility_sensitivity_drawdown.png`：保存最大回撤参数敏感性热力图。
- `outputs/integrated_report.html`：保存可直接用浏览器打开的整合 HTML 投资策略分析报告。
- `outputs/equity_curve.png`：保存策略与 QQQ 买入持有的资金曲线对比图。

## 策略逻辑

1. 下载 QQQ、SPY、TLT 的历史复权收盘价。
2. 计算每个 ETF 的 200 日均线，并计算 QQQ 与 SPY 的 60 日动量。
3. 只在每月最后一个交易日生成调仓信号。
4. 比较 QQQ 与 SPY 的 60 日动量，选择动量更强的一个作为权益候选。
5. 如果权益候选高于其 200 日均线，则持有该候选资产。
6. 如果权益候选低于 200 日均线，则检查 TLT；如果 TLT 高于 200 日均线，则持有 TLT。
7. 如果 TLT 也低于 200 日均线，则持有现金，信号为 `CASH`。
8. 月末收盘后得到的信号从下一个交易日开始执行，避免未来函数。

## 如何运行

```bash
python3 -m pip install -r requirements.txt
python3 main.py
```

运行后，终端会输出最新持仓信号、最终资金曲线值、累计收益率、最大回撤、Sharpe Ratio 和每年收益率，结果文件会保存到 `outputs/` 目录，并自动生成策略 vs QQQ 买入持有的对比报告和 `outputs/integrated_report.html` 整合 HTML 报告。

## 数据源容错

项目优先使用 Yahoo Finance 下载价格数据。如果 Yahoo Finance 因限流或网络问题返回空数据，程序会先尝试读取本地 `outputs/prices.csv` 缓存；如果缓存不存在，则使用仓库内置的 `sample_data/prices.csv` 样例数据继续运行。
