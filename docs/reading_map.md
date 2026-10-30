# Reading Guide 导览与最短阅读路线

已核对原 DOCX 的19项索引。下面是阅读任务，不代表已经精读或复现全部论文。附件中的 Project Guide 全文已核对；论文主要核对标题、版本、摘要和相关主题。没有提供的书籍全文不作为开始编码的前提，也未购买。

## 每项读完应该带回什么

| 编号与材料 | 讲什么及与本项目的关系 | 优先看哪里 | 可以实现的产物 | 不能直接推断 |
|---|---|---|---|---|
| 01 Fundamentals of Perpetual Futures，He 等 | funding、无到期日的定价和摩擦边界；解释永续贵不等于错价 | 摘要、合约设定、含交易成本的价格界限；附件是2026年9月稿，109页，证明可后读 | 一页现货/永续/funding/保证金现金流 | 理论套利收益不是我们可成交收益 |
| 02 Crypto Carry，Schmeling 等 | 杠杆需求和套利资本约束；解释溢价为什么持续 | 附件 BIS WP1087，2023年版本；3.1 positioning、3.3 capital、2.4 decomposition，按标题核对 | 融资、保证金、资金占用和市场状态清单 | 有到期期货的到期收敛不能当作永续30分钟收敛 |
| 03 Trading and Arbitrage，Makarov/Schoar | 跨平台与跨国市场分割 | 套利操作、资金流约束与价差持续；56页附件为2019-02-17稿 | 说明第一版同平台的理由，画未来跨平台资金位置 | 现货跨平台证据不是 spot–perp 收益证据 |
| 04 Algorithmic Trading，Chan | 从均值回归假设变成可回测规则 | 2013版1–3章；第5章按需；Kalman后置 | 变量、形成窗口、交易窗口、规则与成本规格 | 书中参数不能直接移植 |
| 05 Pairs Trading，Gatev 等 | 配对形成期和交易期分离 | formation/trading、收益定义、成本与稳健性；working paper与期刊版章节可能不同 | 时间切分和无未来泄漏对照 | 不需用全样本挑“最好看”的BTC组合 |
| 06 Statistical Arbitrage in US Equities，Avellaneda/Lee | 共同因子与剩余偏离 | 2.3、3、4/4.1；PCA后置 | 检查匹配后P&L是否仍暴露BTC方向 | 不能为了漂亮残差随意拟合对冲比率 |
| 07 Hyperliquid官方文档 | funding、oracle/mark、合约与可见行情 | Funding、WebSocket、Info/Perpetuals | 字段含义、known-at、单位和规则版本表 | HL的小时结算等规则不能移植到OKX |
| 08 Binance本地订单簿 | 初始快照与增量正确衔接 | snapshot、缓存、序列、数量零删除、断线重建 | 可手工逐条检查的盘口测试 | Binance spot/futures/OKX不是同一序列规则 |
| 09 Tardis历史数据说明 | 历史数据覆盖、供应商接收时间、采集空洞 | 日期/通道覆盖、local timestamp、disconnect | 缺失区间和可用性表；先看样本再决定是否付费 | 有接口不等于指定日期齐全；供应商接收时间不是本机时间 |
| 10 Price Impact of Order Book Events，Cont等 | 盘口事件OFI与同期价格影响 | 附件2011年稿；2.1变量、实证深度、与成交量失衡对比 | 按最优报价变化实现OFI，和TP分开比较 | 同期解释力不是未来预测；股票样本不是BTC交易验证 |
| 11 Queue Imbalance，Gould/Bonart | 买一卖一队列对下一跳方向的预测 | 5、6.2、6.3，以章节主题定位 | QI=(bid size−ask size)/(两者之和)，校准下一跳概率 | 下一tick不等于30分钟基差回归 |
| 12 Fragmentation Price Formation and Cross-Impact，Albers等 | BTC跨市场特征、领先滞后和交易实现 | 2数据、3.1特征、3.3期限、6 maker | 两腿压力与价格特征的单独对照；期限衰减图 | 亚秒级历史收益和费率不能直接复制 |
| 13 Cross-Impact of OFI，Cont等 | 自身与其他市场的订单流信息 | 2.1定义、3同期、4.1–4.3预测 | basis-only / 加perp压力 / 加双腿压力的消融 | 跨市场相关不是因果；不必建大因子系统 |
| 14 Periodicity，Hansen等 | 波动和流动性的时段规律 | 3、5、5.2及A.1–A.4图 | 按UTC小时、星期和距funding分组的成本表 | 活跃时段不是自动买卖信号 |
| 15 Trading and Exchanges，Harris | 做市商、流动性、立即成交成本 | 原DOCX推荐13、19、21章；prompt另补14章spread，实际版本目录再核对 | mid→bid/ask→深度/延迟/费用的分解 | 已含在fill中的价差不能二次扣费 |
| 16 Limit Order Strategic Placement，Lehalle/Mounjid | maker逆向选择、排队和延迟 | 2、4.1.1、4.1.4、4.2 | 成交概率、等待时间、fill后价格变化与裸露风险 | 碰到挂单价不代表排到我们 |
| 17 HftBacktest文档 | fill/queue/latency的回放假设 | fill models、queue、feed/order/response latency | 模拟器假设及测试清单；可借鉴而不立即引库 | 库能跑不代表有真实市场反馈或精确队列 |
| 18 Probability of Backtest Overfitting，Bailey等 | 多次挑选规则导致选择偏差 | 2.1、3.1、3.2；CSCV后置 | 所有尝试的登记、按时间切分、episode块不确定性 | 一次holdout不能修复未来泄漏和错误成交 |
| 19 Optimal Mean Reversion Trading，Leung/Li | OU下成本和止损对边界的影响 | 附件arXiv v3 2015-05-15；模型设定与数值例子 | 在固定持有期之后比较目标退出和止损规则 | 假设均值回归不能作为均值回归存在的证据 |

## 四组最短路线

- 全员先读 Project Guide 和01的机制部分，独立手算 docs/project_explained 的 +2 与 −1.017 USDT。
- A数据组：08→09→实际使用的OKX官方文档。第一份产物是两腿同一UTC区间的数据字典、单位映射、缺失清单和序列恢复测试。
- B信号组：04→12→10。第一份产物是 excess、relative pressure decay、momentum 三个可用过去数据计算的变量；11和13留后续。
- C回测组：04→18→17，05补充。第一份产物是可以逐笔核对的状态机、账本和按时间切分方案。
- D执行组：15→17，之后16。第一份产物是四次交易的费率/币种、深度成本、延迟、单腿失败和保证金约束。

02帮助解释经济来源；03为跨平台扩展；06为更广义统计套利；14解释分时段差异；19用于后续退出。每次读完带回一张表、一个公式或一项测试，不以“读完多少篇”作为交付。

## 附件差异记录

`Trading and Arbitrage in Cryptocurrency Markets.pdf` 是两页作者文章介绍，`trading-and-arbitrage-in-crypto-markets.pdf` 才是56页论文，二者不是两项不同研究。`Fundamental of Perpetuals.pdf`实际标题是复数 Fundamentals，版本为2026年9月。章节号码以附件和当次使用版本为准。

原Project Guide先介绍Binance作为方便来源，交接prompt进一步优先OKX；本轮采用实际取得的OKX同平台两腿。原Guide的V2称成本过滤，prompt的V2指单独momentum、V3指成本过滤；本工程遵循prompt命名，当前只运行V0。

论文链接及原有19项目录保留于用户交接文件；本表根据所附 Reading Guide 导览编写，没有将未精读论文描述成已复现结果。
