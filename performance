import numpy as np
import pandas as pd


def calculate_performance(
    result: pd.DataFrame,
    trades: pd.DataFrame | None = None,
    initial_cash: float | None = None,
    risk_free_rate: float = 0.0,
) -> pd.DataFrame:
    if result.empty:
        raise ValueError("回测结果为空，无法计算绩效。")

    equity = result["portfolio_value"].astype(float)
    initial_value = (
        float(initial_cash)
        if initial_cash is not None
        else float(equity.iloc[0])
    )

    returns = result["return"].astype(float).fillna(0).copy()

    # 回测首日如果发生交易，纳入首次建仓成本。
    if initial_cash is not None:
        returns.iloc[0] = equity.iloc[0] / initial_value - 1

    years = max(
        (result.index[-1] - result.index[0]).days / 365.25,
        1 / 365.25,
    )

    cumulative_return = equity.iloc[-1] / initial_value - 1
    annual_return = (
        equity.iloc[-1] / initial_value
    ) ** (1 / years) - 1

    daily_std = returns.std(ddof=1)
    annual_volatility = daily_std * np.sqrt(252)

    daily_risk_free = (
        (1 + risk_free_rate) ** (1 / 252) - 1
    )
    excess_returns = returns - daily_risk_free

    sharpe = (
        excess_returns.mean() / daily_std * np.sqrt(252)
        if daily_std > 0
        else np.nan
    )

    running_peak = equity.cummax()
    if initial_cash is not None:
        running_peak = running_peak.clip(lower=initial_value)

    drawdown = equity / running_peak - 1
    max_drawdown = drawdown.min()

    row = {
        "累计收益率": cumulative_return,
        "年化收益率": annual_return,
        "年化波动率": annual_volatility,
        "Sharpe": sharpe,
        "最大回撤": max_drawdown,
        "Calmar": (
            annual_return / abs(max_drawdown)
            if max_drawdown < 0
            else np.nan
        ),
        "日胜率": (returns > 0).mean(),
        "调仓次数": 0,
        "平均换手率": 0,
        "交易成本": 0,
    }

    if trades is not None and not trades.empty:
        row.update({
            "调仓次数": len(trades),
            "平均换手率": trades["turnover"].mean(),
            "交易成本": trades["cost"].sum(),
        })

    return pd.DataFrame([row])

def monthly_returns(result: pd.DataFrame) -> pd.DataFrame:
    return result.portfolio_value.resample("ME").last().pct_change().rename("monthly_return").to_frame()


def annual_returns(result: pd.DataFrame) -> pd.DataFrame:
    values = result.portfolio_value.resample("YE").last()
    return values.pct_change().rename("annual_return").to_frame()


def direction_performance(result: pd.DataFrame, trades: pd.DataFrame) -> pd.DataFrame:
    if trades.empty:
        return pd.DataFrame(columns=["direction", "trades", "mean_trade_return"])
    t = trades.copy()
    t["trade_return"] = t["portfolio_value"].pct_change()
    return t.groupby("direction", dropna=False).agg(
        trades=("direction", "size"), mean_trade_return=("trade_return", "mean")
    ).reset_index()


def equal_weight_benchmark(prices: pd.DataFrame, initial_cash: float = 1_000_000) -> pd.Series:
    returns = prices.pct_change(fill_method=None).mean(axis=1, skipna=True).fillna(0)
    return initial_cash * (1 + returns).cumprod().rename("benchmark_value")
