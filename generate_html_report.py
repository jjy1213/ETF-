from __future__ import annotations

import base64
import csv
import html
import json
from pathlib import Path


TEXT_FILES = {
    "report.txt": "report.txt",
    "walk_forward.txt": "walk_forward.txt",
}

TABLE_FILES = {
    "performance_summary.xlsx": "performance_summary.csv",
    "annual_returns.xlsx": "annual_returns.csv",
    "strategy_result.xlsx": "strategy_result.csv",
    "rolling_sharpe.xlsx": "rolling_sharpe.csv",
    "volatility_sensitivity.xlsx": "volatility_sensitivity.csv",
    "signals.xlsx": "signals.csv",
    "rebalance_signals.xlsx": "rebalance_signals.csv",
    "moving_average.xlsx": "moving_average.csv",
    "prices.xlsx": "prices.csv",
    "walk_forward.xlsx": "walk_forward.csv",
}

IMAGE_FILES = {
    "equity_curve.png": "equity_curve.png",
    "rolling_sharpe.png": "rolling_sharpe.png",
    "volatility_sensitivity_drawdown.png": "volatility_sensitivity_drawdown.png",
    "volatility_sensitivity_sharpe.png": "volatility_sensitivity_sharpe.png",
}

REPORT_NAME = "integrated_report.html"


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    """读取 CSV 为字典列表。"""
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def to_float(value: str | None, default: float = 0.0) -> float:
    """安全地把字符串转为浮点数。"""
    try:
        return float(value) if value is not None else default
    except ValueError:
        return default


def format_percent(value: str | None) -> str:
    """把小数格式化为百分比。"""
    return f"{to_float(value) * 100:.2f}%"


def format_number(value: str | None) -> str:
    """把数值格式化为两位小数。"""
    return f"{to_float(value):.2f}"


def read_required_text(output_dir: Path) -> dict[str, str]:
    """读取报告需要的文本文件。"""
    return {
        display_name: (output_dir / file_name).read_text(encoding="utf-8")
        for display_name, file_name in TEXT_FILES.items()
    }


def read_required_tables(output_dir: Path) -> dict[str, str]:
    """读取表格源数据；浏览器端用 SheetJS 按工作簿数据源解析。"""
    return {
        display_name: (output_dir / file_name).read_text(encoding="utf-8")
        for display_name, file_name in TABLE_FILES.items()
    }


def read_required_images(output_dir: Path) -> dict[str, str]:
    """读取 PNG 并转为 base64 data URI。"""
    images: dict[str, str] = {}
    for display_name, file_name in IMAGE_FILES.items():
        image_bytes = (output_dir / file_name).read_bytes()
        encoded = base64.b64encode(image_bytes).decode("ascii")
        images[display_name] = f"data:image/png;base64,{encoded}"
    return images


def validate_sources(output_dir: Path) -> None:
    """确认 HTML 所需源文件已经由主流程生成。"""
    required_files = [
        *(output_dir / file_name for file_name in TEXT_FILES.values()),
        *(output_dir / file_name for file_name in TABLE_FILES.values()),
        *(output_dir / file_name for file_name in IMAGE_FILES.values()),
    ]
    missing_files = [str(path) for path in required_files if not path.exists()]
    if missing_files:
        missing_text = ", ".join(missing_files)
        raise FileNotFoundError(f"生成整合 HTML 报告缺少源文件: {missing_text}")


def build_metric_cards(output_dir: Path) -> list[dict[str, str]]:
    """构建顶部概览卡片。"""
    summary_rows = read_csv_rows(output_dir / "performance_summary.csv")
    summary = {row.get("", row.get("metric", "")): row.get("value", "") for row in summary_rows}
    report_rows = read_csv_rows(output_dir / "report.csv")
    strategy_report = next((row for row in report_rows if row.get("portfolio") == "strategy"), {})

    return [
        {"label": "总收益", "value": format_percent(summary.get("total_return")), "hint": "策略累计收益"},
        {
            "label": "年化收益",
            "value": format_percent(strategy_report.get("annualized_return")),
            "hint": "来自策略对比报告",
        },
        {"label": "最大回撤", "value": format_percent(summary.get("max_drawdown")), "hint": "越接近 0 越好"},
        {"label": "夏普比率", "value": format_number(summary.get("sharpe_ratio")), "hint": "风险调整后收益"},
    ]


def build_source_inventory(output_dir: Path) -> list[dict[str, str | float]]:
    """构建报告内的数据源清单。"""
    inventory: list[dict[str, str | float]] = []
    all_sources = {**TEXT_FILES, **TABLE_FILES, **IMAGE_FILES}
    for display_name, file_name in all_sources.items():
        path = output_dir / file_name
        inventory.append(
            {
                "name": display_name,
                "actual_file": file_name,
                "size_kb": round(path.stat().st_size / 1024, 1),
            }
        )
    return inventory


def build_html(
    texts: dict[str, str],
    tables: dict[str, str],
    images: dict[str, str],
    cards: list[dict[str, str]],
    source_inventory: list[dict[str, str | float]],
) -> str:
    """生成完整 HTML 文本。"""
    card_html = "".join(
        (
            '<div class="card">'
            f'<div class="label">{html.escape(card["label"])}</div>'
            f'<div class="value">{html.escape(card["value"])}</div>'
            f'<div class="hint">{html.escape(card["hint"])}</div>'
            "</div>"
        )
        for card in cards
    )

    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>多 ETF 200MA 轮动策略分析报告</title>
  <script src="https://cdn.jsdelivr.net/npm/echarts@5/dist/echarts.min.js"></script>
  <script src="https://cdn.jsdelivr.net/npm/xlsx@0.18.5/dist/xlsx.full.min.js"></script>
  <style>
    :root {{
      --bg: #08111f;
      --panel: #101b2e;
      --text: #e6edf7;
      --muted: #8ea0b8;
      --accent: #46d9ff;
      --green: #6ee7b7;
      --red: #fb7185;
      --line: rgba(148, 163, 184, 0.22);
      --shadow: 0 24px 70px rgba(0, 0, 0, 0.35);
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      font-family: Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", "Microsoft YaHei", sans-serif;
      background: radial-gradient(circle at top left, rgba(70, 217, 255, .16), transparent 28%), var(--bg);
      color: var(--text);
      line-height: 1.6;
    }}
    .page {{ max-width: 1280px; margin: 0 auto; padding: 32px 22px 72px; }}
    .hero {{
      padding: 32px;
      border: 1px solid var(--line);
      border-radius: 28px;
      background: linear-gradient(135deg, rgba(20,35,58,.96), rgba(8,17,31,.92));
      box-shadow: var(--shadow);
      margin-bottom: 24px;
    }}
    .eyebrow {{ color: var(--accent); letter-spacing: .16em; text-transform: uppercase; font-size: 12px; font-weight: 700; }}
    h1 {{ margin: 10px 0 8px; font-size: clamp(30px, 4vw, 52px); line-height: 1.1; }}
    .subtitle {{ color: var(--muted); max-width: 880px; margin: 0; }}
    .cards {{ display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 16px; margin-top: 26px; }}
    .card {{ background: rgba(16,27,46,.9); border: 1px solid var(--line); border-radius: 20px; padding: 18px; }}
    .card .label {{ color: var(--muted); font-size: 13px; }}
    .card .value {{ font-size: 30px; font-weight: 800; margin: 6px 0 2px; }}
    .card .hint {{ color: var(--muted); font-size: 12px; }}
    .grid {{ display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 20px; }}
    section {{ margin-top: 22px; padding: 24px; border: 1px solid var(--line); border-radius: 24px; background: rgba(16,27,46,.84); box-shadow: 0 14px 45px rgba(0,0,0,.22); }}
    section h2 {{ margin: 0 0 16px; font-size: 22px; }}
    .full {{ grid-column: 1 / -1; }}
    pre {{ white-space: pre-wrap; word-break: break-word; margin: 0; color: #dce7f7; background: rgba(8,17,31,.65); border: 1px solid var(--line); border-radius: 16px; padding: 18px; }}
    .chart {{ width: 100%; height: 430px; }}
    .image {{ width: 100%; border-radius: 18px; border: 1px solid var(--line); background: #fff; display: block; }}
    .side-by-side {{ display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 16px; }}
    .table-wrap {{ overflow: auto; border: 1px solid var(--line); border-radius: 16px; max-height: 520px; }}
    table {{ width: 100%; border-collapse: collapse; font-size: 13px; min-width: 680px; }}
    th, td {{ padding: 10px 12px; border-bottom: 1px solid var(--line); text-align: right; white-space: nowrap; }}
    th:first-child, td:first-child {{ text-align: left; }}
    th {{ position: sticky; top: 0; background: #17263d; color: var(--accent); z-index: 1; }}
    tr:hover td {{ background: rgba(70, 217, 255, 0.06); }}
    .note {{ color: var(--muted); font-size: 13px; margin-top: 10px; }}
    @media (max-width: 900px) {{
      .cards, .grid, .side-by-side {{ grid-template-columns: 1fr; }}
      .hero {{ padding: 24px; }}
    }}
  </style>
</head>
<body>
  <div class="page">
    <header class="hero">
      <div class="eyebrow">Investment Strategy Report</div>
      <h1>多 ETF 200MA 轮动策略分析报告</h1>
      <p class="subtitle">整合 outputs 中的回测结果、策略报告、步进测试、滚动夏普、敏感性分析和图表。PNG 以 base64 内嵌，表格数据由 SheetJS 在浏览器端解析。</p>
      <div class="cards">{card_html}</div>
    </header>

    <div class="grid">
      <section class="full">
        <h2>1. 策略文字说明</h2>
        <pre>{html.escape(texts["report.txt"])}</pre>
      </section>

      <section class="full">
        <h2>2. 净值曲线图</h2>
        <img class="image" src="{images["equity_curve.png"]}" alt="净值曲线图" />
      </section>

      <section class="full">
        <h2>3. 年度收益柱状图</h2>
        <div id="annualReturnsChart" class="chart"></div>
        <p class="note">数据来源：annual_returns.xlsx（本项目实际输出为 annual_returns.csv，HTML 中按同名工作簿数据源嵌入并用 SheetJS 解析）。</p>
      </section>

      <section class="full">
        <h2>4. 滚动夏普图</h2>
        <img class="image" src="{images["rolling_sharpe.png"]}" alt="滚动夏普图" />
      </section>

      <section class="full">
        <h2>5. 波动率敏感性分析</h2>
        <div class="side-by-side">
          <img class="image" src="{images["volatility_sensitivity_sharpe.png"]}" alt="波动率敏感性夏普图" />
          <img class="image" src="{images["volatility_sensitivity_drawdown.png"]}" alt="波动率敏感性回撤图" />
        </div>
      </section>

      <section class="full">
        <h2>6. 步进测试结果</h2>
        <pre>{html.escape(texts["walk_forward.txt"])}</pre>
        <div id="walkForwardTable" class="table-wrap" style="margin-top:16px"></div>
      </section>

      <section class="full">
        <h2>7. 详细绩效汇总表</h2>
        <div id="performanceTable" class="table-wrap"></div>
      </section>

      <section class="full">
        <h2>8. 数据源清单</h2>
        <div id="sourceInventoryTable" class="table-wrap"></div>
        <p class="note">用户清单中的 xlsx 在当前代码中对应 csv 输出；HTML 仍按 xlsx 名称组织数据源，并通过 SheetJS 读取嵌入数据。</p>
      </section>
    </div>
  </div>

  <script>
    const embeddedCsv = {json.dumps(tables, ensure_ascii=False)};
    const sourceInventory = {json.dumps(source_inventory, ensure_ascii=False)};

    function workbookRows(sourceName) {{
      const workbook = XLSX.read(embeddedCsv[sourceName], {{ type: 'string' }});
      const sheet = workbook.Sheets[workbook.SheetNames[0]];
      return XLSX.utils.sheet_to_json(sheet, {{ defval: '' }});
    }}

    function fmt(value) {{
      if (typeof value === 'number') {{
        return Number.isInteger(value) ? String(value) : value.toFixed(4);
      }}
      const numberValue = Number(value);
      if (value !== '' && Number.isFinite(numberValue)) {{
        return Math.abs(numberValue) < 1 && value !== '0'
          ? (numberValue * 100).toFixed(2) + '%'
          : numberValue.toFixed(4);
      }}
      return value ?? '';
    }}

    function renderTable(containerId, rows, maxRows = 50) {{
      const container = document.getElementById(containerId);
      if (!rows || rows.length === 0) {{
        container.innerHTML = '<div class="note">暂无数据</div>';
        return;
      }}
      const columns = Object.keys(rows[0]);
      const limitedRows = rows.slice(0, maxRows);
      let table = '<table><thead><tr>' + columns.map(col => `<th>${{col}}</th>`).join('') + '</tr></thead><tbody>';
      table += limitedRows.map(row => '<tr>' + columns.map(col => `<td>${{fmt(row[col])}}</td>`).join('') + '</tr>').join('');
      table += '</tbody></table>';
      const suffix = rows.length > maxRows ? `<div class="note" style="padding:10px 12px">仅展示前 ${{maxRows}} 行，共 ${{rows.length}} 行。</div>` : '';
      container.innerHTML = table + suffix;
    }}

    function renderAnnualReturns() {{
      const rows = workbookRows('annual_returns.xlsx');
      const years = rows.map(row => String(row.year));
      const returns = rows.map(row => Number(row.annual_return) * 100);
      const chart = echarts.init(document.getElementById('annualReturnsChart'));
      chart.setOption({{
        backgroundColor: 'transparent',
        tooltip: {{ trigger: 'axis', valueFormatter: value => value.toFixed(2) + '%' }},
        grid: {{ left: 58, right: 24, top: 35, bottom: 45 }},
        xAxis: {{ type: 'category', data: years, axisLabel: {{ color: '#8ea0b8' }}, axisLine: {{ lineStyle: {{ color: '#334155' }} }} }},
        yAxis: {{ type: 'value', axisLabel: {{ color: '#8ea0b8', formatter: '{{value}}%' }}, splitLine: {{ lineStyle: {{ color: 'rgba(148,163,184,.18)' }} }} }},
        series: [{{
          name: '年度收益',
          type: 'bar',
          data: returns,
          itemStyle: {{ color: params => params.value >= 0 ? '#6ee7b7' : '#fb7185', borderRadius: [6, 6, 0, 0] }}
        }}]
      }});
      window.addEventListener('resize', () => chart.resize());
    }}

    document.addEventListener('DOMContentLoaded', () => {{
      renderAnnualReturns();
      renderTable('walkForwardTable', workbookRows('walk_forward.xlsx'), 30);
      renderTable('performanceTable', workbookRows('performance_summary.xlsx'), 20);
      renderTable('sourceInventoryTable', sourceInventory, 100);
    }});
  </script>
</body>
</html>
"""


def generate_integrated_report(output_dir: Path) -> Path:
    """生成可直接浏览器打开的整合 HTML 投资策略报告。"""
    validate_sources(output_dir)
    texts = read_required_text(output_dir)
    tables = read_required_tables(output_dir)
    images = read_required_images(output_dir)
    cards = build_metric_cards(output_dir)
    source_inventory = build_source_inventory(output_dir)
    html_text = build_html(texts, tables, images, cards, source_inventory)

    output_path = output_dir / REPORT_NAME
    output_path.write_text(html_text, encoding="utf-8")
    return output_path


def main() -> None:
    """命令行入口：基于当前 outputs 目录生成 HTML 报告。"""
    output_path = generate_integrated_report(Path("outputs"))
    print(f"整合 HTML 报告已生成: {output_path.resolve()}")


if __name__ == "__main__":
    main()
