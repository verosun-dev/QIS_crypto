# QIS Spot–Perpetual 研究起步版

研究问题：同一资产永续异常正溢价时，买现货、空等量线性永续，之后的价差收敛能否覆盖成本？本项目目前没有盈利证据。

首轮已取得OKX真实免费样本，并完成**两小时工程调试**。2026-10-23 00:00–02:00 UTC的每秒basis全部为负，因此规定方向的V0没有开仓。零交易不是策略赚钱或亏钱的证据。原Project Guide的图和示例是合成教学材料，与本工程真实数据报告分开。

## 先从这里读

1. [项目易懂解读](docs/project_explained.md)：为什么两条价格都上涨还能赚价差；+2毛利润为何在示意费用下变成−1.017 USDT。
2. [19项阅读导览](docs/reading_map.md)：每项重点、能做什么和四组最短路线。
3. [四组执行指南](docs/team_workstreams.md)：数据怎么买/下载、L1/L2、模型、回测与成本工作接口。
4. [本轮结果](docs/first_run_results.md)、[真实运行摘要](outputs/okx_20261023_debug_v0/summary.json)、[基差图](outputs/okx_20261023_debug_v0/basis.png)。

## 最短运行命令

在本目录执行。核心仅用Python标准库，无需安装第三方包。本轮验证环境Python3.14.2；项目支持Python3.10以上，其他版本尚未逐一测试。

```bash
PYTHONPATH=src python3 -m unittest discover -s tests -v
PYTHONPATH=src python3 scripts/synthetic_demo.py
PYTHONPATH=src python3 -m qis_spot_perp.cli run --config configs/debug.json
```

最后一条重放真实样本，读取已下载的原始文件；每次运行会追加实验登记。outputs/synthetic_demo全部为**合成测试**，真实样本只在outputs/okx_20261023_debug_v0。

其他机器复现时先列清单、再有界下载：

```bash
python3 scripts/fetch_sample.py --date 2026-10-23
python3 scripts/fetch_sample.py --date 2026-10-23 --download --max-mb 700
python3 scripts/check_archives.py
PYTHONPATH=src python3 -m qis_spot_perp.cli manifest
PYTHONPATH=src python3 -m qis_spot_perp.cli run --config configs/debug.json
```

无需API密钥。下载仅支持这一对合约的单日研究请求；更长时间逐日运行前先保留对应日期manifest，当前固定名字会更新元数据。原始文件保留，已有文件不自动覆盖，下载失败保留.part供排查。若需要全24小时lookback，需要额外前一天，不可直接把debug改称正式评估。

可选静态图：`MPLCONFIGDIR=tmp/matplotlib python3 scripts/plot_debug.py`。可选依赖见requirements-optional.txt，核心计算不需要它们。

实时采集程序已准备，但本轮**未联网验证**。在确认当前地区适用的官方public WS URL后：

```bash
python3 scripts/collect_public.py --url 'wss://ws.okx.com:8443/ws/v5/public' --seconds 30 --max-mb 25 --output data/raw/live-public.jsonl
```

URL是待核验候选，不能用更换域名绕过访问限制。程序只订阅books/trades，默认30秒，最多300秒/100MB，文件不能覆盖，断线记录并停止。下一次须重新取得snapshot。没有常驻后台或交易权限。

## 工程入口

| 模块 | 作用 |
|---|---|
| src/qis_spot_perp/data.py | 流式档案、UTC边界、成交去重、pressure、SHA256 |
| book.py | Decimal L2绝对数量更新、序列/恢复、小额IOC深度撮合 |
| features.py | 因果滚动basis、momentum、TP和时间purge基础函数 |
| replay.py | exchange/observed/reported状态、订单延迟、部分成交恢复 |
| accounting.py | 实际fill现金流、库存、逐笔费和funding方向 |
| configs/debug.json | 所有调试参数和适用边界 |
| tests/test_research.py | 手算、时间、序列、延迟、部分成交和数据边界测试 |

详细规格见[baseline_spec](docs/baseline_spec.md)、[instrument_spec](docs/instrument_spec.md)、[data_dictionary](docs/data_dictionary.md)。下载来源、大小、SHA256在data/manifests/downloads.json；每次运行参数与代码指纹在outputs/experiment_register.jsonl。

## 当前不能说明什么

- 下载了全天盘口，但只解析前两小时，30分钟暖机是调试设置。没有最终样本外测试。
- 档案无seqId/prevSeqId或本机接收时间；流式解压成功不等于市场数据无漏包。
- 费用是教学情景，延迟是配置假设，历史账户费率/规则未完整核验。
- 资金费参考价格缺失，因此跨结算点交易受限。无保证金清算、maker排队或市场冲击反馈验证。
- 真实样本零交易，所以成本模型在本轮真实数据中尚未经历实际开平仓；合成测试只支持代码核对。

下一步优先扩展连续日期、补24小时暖机，并采集带接收时间和序列的原始消息，再评估是否存在足够多的正溢价episode。不要为制造交易去掉正basis条件、修改费率或事后挑日期。
