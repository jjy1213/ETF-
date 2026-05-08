# ETF 月末 200MA 多资产轮动量化研究项目

这是一个适合初学者阅读和运行的 Python 量化研究示例。项目使用 `yfinance` 下载 ETF 数据，用 `pandas` 计算多 ETF 的 200 日均线和 126 日动量，并在每月最后一个交易日生成轮动权重和策略资金曲线。

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
- `strategy.py`：负责计算 200 日均线、动量、识别月末交易日，并生成月末轮动权重。
- `backtest.py`：负责把月末权重转换为每日持仓，扣除交易成本，计算策略收益、资金曲线并绘图。
- `metrics.py`：负责计算每年收益率、最大回撤、Sharpe Ratio，并打印绩效摘要。
- `report.py`：负责对比策略与 QQQ 买入持有的年化收益率、最大回撤、Sharpe Ratio、月度胜率和盈亏比。
- `sensitivity.py`：负责生成波动率仓位参数敏感性 CSV 和热力图。
- `requirements.txt`：记录运行项目所需的第三方库，包括 `yfinance`、`pandas` 和 `matplotlib`。
- `README.md`：说明项目目标、目录结构、运行方式和输出结果。
- `sample_data/prices.csv`：内置 SPY、QQQ、IWM、EFA、EEM、TLT、GLD 样例价格数据，供在线数据源失败时备用。
- `outputs/prices.csv`：保存 ETF 池的历史复权收盘价。
- `outputs/moving_average.csv`：保存 ETF 池的 200 日均线。
- `outputs/rebalance_signals.csv`：保存每月最后一个交易日生成的目标轮动权重。
- `outputs/signals.csv`：保存每日持仓、总仓位、换手率、交易成本和 ETF 权重。
- `outputs/strategy_result.csv`：保存每日持仓、策略收益和资金曲线。
- `outputs/annual_returns.csv`：保存每年收益率。
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

1. 下载 SPY、QQQ、IWM、EFA、EEM、TLT、GLD 的历史复权收盘价。
2. 计算每个 ETF 的 200 日均线和 126 日动量。
3. 只在每月最后一个交易日生成轮动目标权重。
4. 只考虑站上 200 日均线且 126 日动量为正的 ETF。
5. 在候选 ETF 中按动量排序，最多持有前 3 个，并等权配置。
6. 用 20 日历史波动率把组合缩放到 10% 年化目标波动率，最大总仓位 100%，不使用杠杆。
7. 月末收盘后得到的权重从下一个交易日开始执行，并按换手率扣除 5 bps 交易成本。
8. 输出 rolling Sharpe、walk-forward 分年样本外结果、参数敏感性分析和 QQQ buy&hold 对比。
9. 为防止过度拟合，主策略使用固定整数参数；敏感性分析和 walk-forward 只做诊断，不用于全样本反向挑选最优参数。

## 如何运行

```bash
python3 -m pip install -r requirements.txt
python3 main.py
```

运行后，终端会输出最新持仓信号、最终资金曲线值、累计收益率、最大回撤、Sharpe Ratio 和每年收益率，结果文件会保存到 `outputs/` 目录，并自动生成策略 vs QQQ 买入持有的对比报告和 `outputs/integrated_report.html` 整合 HTML 报告。

## 数据源容错

项目优先使用 Yahoo Finance 下载价格数据。如果 Yahoo Finance 因限流或网络问题返回空数据，程序会先尝试读取本地 `outputs/prices.csv` 缓存；如果缓存不存在，则使用仓库内置的 `sample_data/prices.csv` 样例数据继续运行。
