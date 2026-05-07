# ETF Dual Momentum 量化研究项目

这是一个适合初学者阅读和运行的 Python 量化研究示例。项目使用 `yfinance` 下载 ETF 数据，用 `pandas` 计算 QQQ 与 TLT 的 60 日动量，并根据 Dual Momentum 思路每日生成持仓信号和策略资金曲线。

## 项目目录结构

```text
.
├── main.py              # 策略主程序：下载数据、计算动量、生成信号、回测并绘图
├── requirements.txt     # Python 依赖列表
├── README.md            # 项目说明文档
└── outputs/             # 运行 main.py 后自动生成，保存研究结果
    ├── prices.csv
    ├── momentum.csv
    ├── signals.csv
    ├── strategy_result.csv
    └── equity_curve.png
```

## 每个文件的作用

- `main.py`：项目核心代码，使用函数拆分量化研究流程，包含中文注释，便于逐步理解。
- `requirements.txt`：记录运行项目所需的第三方库，包括 `yfinance`、`pandas` 和 `matplotlib`。
- `README.md`：说明项目目标、目录结构、运行方式和输出结果。
- `outputs/prices.csv`：保存 QQQ 和 TLT 的历史复权收盘价。
- `outputs/momentum.csv`：保存 QQQ 和 TLT 的 60 日动量。
- `outputs/signals.csv`：保存每日持仓信号，信号可能是 `QQQ`、`TLT` 或 `CASH`。
- `outputs/strategy_result.csv`：保存每日持仓、策略收益和资金曲线。
- `outputs/equity_curve.png`：保存由 `matplotlib` 绘制的资金曲线图。

## 策略逻辑

1. 下载 QQQ 和 TLT 的历史复权收盘价。
2. 分别计算两个 ETF 的 60 日动量。
3. 每天选择 60 日动量更强的 ETF。
4. 如果两个 ETF 的动量都小于等于 0，则空仓，信号为 `CASH`。
5. 使用下一交易日收益计算策略资金曲线，避免未来函数。

## 如何运行

```bash
pip install -r requirements.txt
python main.py
```

运行后，终端会输出最新持仓信号、最终资金曲线值和累计收益率，结果文件会保存到 `outputs/` 目录。
