from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

from .performance import annual_returns, direction_performance


def write_report(
    output: str | Path,
    result: pd.DataFrame,
    trades: pd.DataFrame,
    performance: pd.DataFrame,
    turning: pd.DataFrame,
    rankings: pd.DataFrame | None = None,
) -> None:
    out = Path(output)
    out.mkdir(parents=True, exist_ok=True)

    result.to_csv(out / "backtest_result.csv", encoding="utf-8-sig")
    trades.to_csv(out / "holdings_history.csv", index=False, encoding="utf-8-sig")
    performance.to_csv(out / "performance_summary.csv", index=False, encoding="utf-8-sig")
    result.resample("ME").last().pct_change().to_csv(
        out / "monthly_returns.csv",
        encoding="utf-8-sig",
    )
    annual_returns(result).to_csv(out / "annual_returns.csv", encoding="utf-8-sig")
    direction_performance(result, trades).to_csv(
        out / "direction_performance.csv",
        index=False,
        encoding="utf-8-sig",
    )
    turning.to_csv(out / "turning_index.csv", encoding="utf-8-sig")
    if rankings is not None:
        rankings.to_csv(out / "theme_rankings.csv", encoding="utf-8-sig")

    plt.figure(figsize=(11, 5))
    plt.plot(result.index, result.portfolio_value)
    plt.title("ETF Rotation Net Value")
    plt.grid(alpha=0.3)
    plt.tight_layout()
    plt.savefig(out / "net_value.png", dpi=160)
    plt.close()

    plt.figure(figsize=(11, 4))
    plt.fill_between(result.index, result.drawdown, 0, alpha=0.5)
    plt.title("Drawdown")
    plt.grid(alpha=0.3)
    plt.tight_layout()
    plt.savefig(out / "drawdown.png", dpi=160)
    plt.close()

    plt.figure(figsize=(11, 4))
    plt.plot(turning.index, turning.turning_index)
    plt.title("Turning Index")
    plt.grid(alpha=0.3)
    plt.tight_layout()
    plt.savefig(out / "turning_index.png", dpi=160)
    plt.close()

    html = (
        "<html><meta charset='utf-8'>"
        "<h1>ETF Rotation Backtest Report</h1>"
        f"{performance.to_html(index=False)}"
        "<h2>Net Value</h2><img src='net_value.png' width='900'>"
        "<h2>Drawdown</h2><img src='drawdown.png' width='900'>"
        "</html>"
    )
    (out / "research_report.html").write_text(html, encoding="utf-8")
