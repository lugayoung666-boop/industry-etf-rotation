# 基于“变盘指数”的行业主题 ETF 动量-反转轮动策略

本项目是一个行业/主题 ETF 轮动策略 MVP。当前版本重点是跑通数据、信号、组合、交易和绩效统计链路，不预设策略一定取得正收益，也不把 demo 结果视为真实策略表现。

## 当前实现状态

- 默认主策略为 `regime_switch`，保留 `momentum` 和 `reversal` 作为对照模式。
- 变盘指数按 20 日滚动月度收益、每日横截面排名、220 日排名变化、220 日滚动标准差、20 日平滑和一阶差分构造。
- 当 `delta_breakpoint < 0` 使用动量信号；当 `delta_breakpoint > 0` 使用反转信号；等于 0 时沿用上一期状态。
- 动量因子为过去 240 个交易日累计收益率；反转因子为过去 60 个交易日累计收益率的相反数。
- 组合构建采用五组分层，持有因子得分最高的第 5 组，组内等权。
- 月末收盘后形成信号，下一交易日执行调仓；有开盘价时，执行日收益使用 `close/open`。
- 价格异常不做静默平滑，超过阈值的跳点会写入 `price_anomaly_log.csv` 并从该日期起排除。
- `--demo` 使用离线模拟数据，属于简化实现：ETF-like 价格同时作为信号层和交易层。

## 快速运行

```powershell
pip install -r requirements.txt
python run_backtest.py --demo --output output_demo
```

输出文件包括：

- `nav.csv`：策略与行业等权基准净值；
- `performance.csv`：累计收益、年化收益、年化波动、夏普比率和最大回撤；
- `regime_states.csv`：每期变盘指数、差分和状态；
- `group_detail.csv`：每期行业因子排序与五组分层；
- `target_weights_signal_date.csv`：信号日目标权重；
- `execution_audit.csv`：信号日与下一交易日执行日；
- `daily_weights.csv`、`daily_returns.csv`：日度持仓、收益、换手和成本；
- `rank_ic.csv`：因子与下一持有期收益的 RankIC；
- `price_anomaly_log.csv`：价格异常审计日志；
- `run_notes.txt`：本次运行口径说明。

## 本地真实数据格式

`--source local` 默认读取：

```text
data/cache/industry_prices.csv
data/cache/etf_prices.csv
```

两个文件均采用长表格式：

```csv
date,symbol,open,close
2020-01-02,ETF_CODE,1.000,1.010
```

其中行业指数文件至少需要 `date,symbol,close`，ETF 文件至少需要 `date,symbol,close`；如果 ETF 文件包含 `open`，回测会用下一交易日开盘执行口径。

如果本地缓存不存在，程序会提示先准备数据或使用 `--demo`，不会静默缩短样本区间。

## 配置

主要配置文件：

- `config/strategy.yaml`：策略模式、变盘指数窗口、动量/反转窗口、分组、成本和异常价格阈值；
- `config/universe.yaml`：行业、ETF、上市日期和跟踪指数映射。

核心默认参数：

```yaml
signal_mode: regime_switch
regime:
  rank_return_window: 20
  rank_compare_window: 220
  volatility_window: 220
  smoothing_window: 20
signals:
  momentum_window: 240
  reversal_window: 60
portfolio:
  n_groups: 5
  long_group: 5
```

## 后续待扩展

- 接入 AkShare/Tushare 下载器，并明确复权口径和交易日历；
- 使用行业指数作为信号层、ETF 作为交易层，而不是 demo 的简化单层价格；
- 增加样本内/样本外或滚动走步检验；
- 完善真实 ETF 流动性、上市时间、停牌、公司行动和重复暴露筛选；
- 扩展参数对比，但不得用全样本优化结果直接选择最终策略。

本项目仅用于研究和实习成果展示，不构成投资建议。
