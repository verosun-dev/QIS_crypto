# 合约与来源核验

检查日期为2026-10-30。原始公开API响应保存在data/manifests；它们是取得时规格，不自动证明2026-10-23规则相同。

| 项目 | Spot | Perpetual |
|---|---|---|
| 场所与代码 | OKX BTC-USDT | OKX BTC-USDT-SWAP |
| 标的与结算 | BTC / USDT | linear，ctValCcy BTC，settleCcy USDT |
| 数量单位 | BTC | 张；每张0.01 BTC，ctMult=1 |
| 价格步长 | 0.1 USDT/BTC | 0.1 USDT/BTC |
| lotSz | 0.00000001 BTC | 0.01张 |
| minSz | 0.00001 BTC | 0.01张 |
| 本轮q | 0.01 BTC | 1张，即0.01 BTC |
| 手续费 | 情景10 bps/次 | 情景5 bps/次 |
| 费用币种 | 模型假定USDT；真实规则未核验 | 模型假定USDT；账户档位未核验 |

费用情景不表示标准费率、VIP优惠或可用返佣。最小名义限制、历史有效期、保证金梯度、费币和账户资格尚未完整核验；真实下单不在范围内。

实际取得的该日资金费结算时刻为00:00、08:00、16:00 UTC，realizedRate分别约0.0000668879、0.0000753334、0.0000685722。这是实际费率，不是之前已知的预测值。接口不包含本次需要的结算参考价格，跨点交易暂不运行；不能统一用八小时线性摊算。

本轮实际下载：23日两腿400档盘口；23和24日两腿成交，满足UTC全天需要的相邻UTC+8文件。全部压缩文件606,258,642字节，约606.3十进制MB或578.2MiB。只有前两小时盘口被逐条解析，余下内容未宣称质量通过。

官方文档核验：历史接口module1/4、日界和发布延迟仍与prompt主要描述一致；当前额外有module11借贷费率。普通books的checksum已标为deprecated、固定0，序列应检查seqId/prevSeqId。**本次历史档案没有这些字段**，不能用实时协议说明替它补出证据。档案三列价位与WebSocket格式也不同。

当前官方REST trade source=1说明是RPI（旧ELP）。本次成交档案确有source=1，保留并统计；pressure含全部source，尚未把该字段的档案可访问性映射验证完毕。盘口撮合不借成交记录补充流动性。

核验入口：[历史数据](https://www.okx.com/historical-data)、[API文档](https://www.okx.com/docs-v5/en/)、[变更记录](https://www.okx.com/docs-v5/log_en/)。档案清单与合约响应是实际访问证据，而非仅引用入口。未创建API密钥，未购买或使用真实订单接口。
