# 数据字典和时间语义

| 来源或输出 | 字段 | 单位与用途 |
|---|---|---|
| raw trade CSV | instrument_name, trade_id | 合约及唯一成交ID；去重不按timestamp |
| raw trade CSV | side, price, size | 主动buy/sell；USDT/BTC；spot size为BTC，swap size为张数 |
| raw trade CSV | created_time | Unix毫秒、exchange time；没有本机接收时间 |
| raw trade CSV | source | 原样统计0/1；官方当前REST文档1为RPI（旧ELP），档案对应语义待进一步确认 |
| raw book JSON | instId, action, ts | 合约、snapshot/update、Unix毫秒 |
| raw book JSON | bids/asks [price,size,count] | 价格、绝对数量、委托数量；本轮档案三列，不能当WebSocket四列 |
| raw book JSON | seqId/prevSeqId/checksum | 本轮全部缺失，未伪造；完整性未知 |
| metadata | ctVal,ctMult,ctValCcy | 张数×面值×乘数→BTC；当前0.01×1 BTC/张 |
| metadata | lotSz,minSz,tickSz | 下单单位、最小数量、价格步长；Decimal映射 |
| features.csv | ts | 本地模拟决策毫秒；只读取已收到行情 |
| features.csv | spot_mid,perp_mid | 当时观察到的mid，非成交价 |
| features.csv | basis_bps,excess_bps,momentum_60s_bps | 基点；excess参考严格过去窗口 |
| pressure.csv | available_exchange_ms | 该分钟结束时刻；用于信号还需额外接收延迟 |
| pressure.csv | spot_tp,perp_tp,relative_tp,relative_decay | 每市场主动成交额归一化；无量为缺失；当前含所有source，非OFI |
| orders.csv | send_ms,arrival_ms,report_ms | 分别为发送、到达交易所、收到成交回报 |
| fills.csv | quantity_btc,price,fee_usdt | 每档成交基础币数量、USDT/BTC、费用USDT |
| trades.csv | gross_fill_usdt,fees_usdt,funding_usdt,net_usdt | 同一公共账本现金流；empty CSV代表没有交易 |
| equity.csv | equity_usdt,residual_btc,state | 总配置资本+按mid估值PnL、spot+perp残余BTC、当前已知状态 |
| funding.json | fundingTime,realizedRate | 实际结算时刻和最终费率；不能作为过去入场信息 |

Book的valid在本轮只表示存在可重建快照和更新，以及没有已检测的格式/顺序错误；sequence_verified仍为false。策略每秒检查双腿非空、bid<ask、未过期（≤2秒）。质量报告不把“未发现异常”写成“原始数据没有缺口”。

压缩文件本地SHA256记录在downloads.json，证明本次代码使用哪份文件；不是交易所签发的校验和。原始数据不提交Git，处理文件/报告可重新生成。原始UTC全天已下载，但盘口只检查前两小时；成交统计也仅描述目标两小时。

source=1流动性是否可被普通API taker获得是另一个问题。pressure作为观察到的市场信息目前包含这类成交，不能据此给订单增加相同流动性；V0不使用pressure，不受该候选口径影响。
