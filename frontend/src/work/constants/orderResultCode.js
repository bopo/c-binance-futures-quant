export const orderResultCodeObj ={
    "-1000":"处理请求时发生未知错误。",
    "-1001":"币安内部错误; 无法处理您的请求。 请再试一次.",
    "-1002":"币安认为您无权执行此请求.",
    "-1003":"请求过多",
    "-1004":"IP地址已经在白名单.",
    "-1005":"白名单上没有此IP地址.",
    "-1006":"从消息总线收到意外的响应。执行状态未知。.",
    "-1007":"等待后端服务器响应超时。 发送状态未知； 执行状态未知。.",
    "-1014":"不支持当前的下单参数组合.",
    "-1015":"新订单太多。",
    "-1016":"该服务不可用。",
    "-1020":"不支持此操作。.",
    "-1021":"请求的时间戳有问题.",
    "-1022":"请求签名无效.",
    "-1023":"参数里面的开始时间在结束时间之后.",
    "-1100":"在参数中发现非法字符.",

    "-1101":"为此端点发送的参数太多。",
    "-1102":"未发送强制性参数，该参数为空/空或格式错误。",
    "-1103":"发送了未知参数。",
    "-1104":"并非所有发送的参数都被读取。",
    "-1105":"参数为空。",
    "-1106":"发送了不需要的参数。",
    "-1111":"精度超过为此资产定义的最大值。",
    "-1112":"交易对没有挂单。",
    "-1114":"发送的TimeInForce参数不需要。",
    "-1115":"无效的timeInForce。",
    "-1116":"无效订单类型。",
    "-1117":"无效买卖方向。",
    "-1118":"新的客户订单ID为空。",
    "-1119":"客户自定义的订单ID为空。",
    "-1120":"无效时间间隔。",
    "-1121":"无效的交易对。",
    "-1125":"此listenKey不存在。",
    "-1127":"查询间隔太大。",
    "-1128":"可选参数组合无效.",
    "-1130":"发送的参数为无效数据。",
    "-1136":"无效的 newOrderRespType。",
    "-2010":"新订单被拒绝。",
    "-2011":"取消订单被拒绝。",
    "-2013":"订单不存在。",
    "-2014":"API-key 格式无效。",
    "-2015":"无效的API密钥，IP或操作权限。",
    "-2016":"找不到该交易对的交易窗口。 尝试改为24小时自动报价。",
    "-2018":"余额不足。",
    "-2019":"杠杆账户余额不足.",
    "-2020":"无法成交。",
    "-2021":"订单可能被立刻触发。",
    "-2022":"只减仓订单被拒绝。",
    "-2023":"用户正处于被强平模式。",
    "-2024":"持仓不足。",
    "-2025":"挂单量达到上限。",
    "-2026":"当前订单类型不支持仅减仓。",
    "-2027":"挂单或持仓超出当前初始杠杆下的最大值。",
    "-2028":"调整初始杠杆过低，导致可用余额不足。",
    "-4000":"订单状态不正确。",
    "-4001":"价格小于0。",
    "-4002":"价格超过最大值。",
    "-4003":"数量小于0。",
    "-4004":"数量小于最小值。",
    "-4005":"数量大于最大值。",
    "-4006":"触发价小于最小值。",
    "-4007":"触发价大于最大值。",
    "-4008":"价格精度小于0。",
    "-4009":"最大价格小于最小价格。",
    "-4010":"最大数量小于最小数量。",
    "-4011":"步进值小于0。",
    "-4012":"最大订单量小于0。",
    "-4013":"价格小于最小价格。",
    "-4014":"价格增量不是价格精度的倍数。",
    "-4015":"客户订单ID有误。",
    "-4016":"价格高于标记价格乘数上限。",
    "-4017":"价格上限小于0。",
    "-4018":"价格下限小于0。",
    "-4019":"Composite scale too large.。",
    "-4020":"目标策略值不适合订单状态, 只减仓",
    "-4021":"深度信息的limit值不正确。",
    "-4022":"发送的市场状态不正确。",
    "-4023":"数量的递增值不是步进值的倍数。",
    "-4024":"价格低于标记价格乘数下限。",
    "-4025":"乘数小于0。",
    "-4026":"收益值不正确。",
    "-4027":"账户类型不正确。",
    "-4028":"杠杆倍数不正确。",
    "-4029":"价格精度小数点位数不正确。",
    "-4030":"步进值小数点位数不正确。",
    "-4031":"不正确的参数类型。",
    "-4032":"超过可以取消的最大订单量。",
    "-4033":"风险保障基金账号没找到。",
    "-4044":"余额类型不正确。",
    "-4045":"达到止损单的上限。",
    "-4046":"不需要切换仓位模式。",
    "-4047":"如果有挂单，仓位模式不能切换。",
    "-4048":"如果有仓位，仓位模式不能切换。",
    "-4049":"Add margin only support for isolated position。",
    "-4050":"全仓余额不足。",
    "-4051":"逐仓余额不足。",
    "-4052":"No need to change auto add margin.",
    "-4053":"自动增加保证金只适用于逐仓。",
    "-4054":"不能增加逐仓保证金: 持仓为0",
    "-4055":"数量必须是正整数",
    "-4056":"API key的类型不正确",
    "-4057":"API key不正确",
    "-4058":"maxPrice和priceDecimal太大，请检查。",
    "-4059":"无需变更仓位方向。",
    "-4060":"仓位方向不正确。",
    "-4061":"订单的持仓方向和用户设置不一致。",
    "-4062":"仅减仓的设置不正确。",
    "-4063":"无效的期权请求类型。",
    "-4064":"无效的期权时间窗口。",
    "-4065":"无效的期权数量。",
    "-4066":"无效的期权事件类型。",
    "-4067":"如果有挂单，无法修改仓位方向。",
    "-4068":"如果有仓位, 无法修改仓位方向。",
    "-4069":"无效的期权费。",
    "-4070":"客户的期权ID不合法。",
    "-4071":"期权的方向无效。",
    "-4072":"期权费没有更新。",
    "-4073":"输入的期权费小于0。",
    "-4074":"Order amount is bigger than upper boundary or less than 0, reject order。",
    "-4075":"output premium fee is less than 0, reject order\n。",
    "-4076":"期权的费用比之前的费用高。",
    "-4077":"下单的数量达到上限。",
    "-4078":"期权内部系统错误。",
    "-4079":"期权ID无效。",
    "-4080":"用户找不到。",
    "-4081":"期权找不到。",
    "-4082":"批量下单的数量不正确。",
    "-4083":"无法批量下单。",
    "-4084":"方法不支持。",
    "-4085":"期权的有限系数不正确。",
    "-4086":"无效的价差阀值。",
    "-4087":"用户只能下仅减仓订单。",
    "-4088":"用户当前不能下单。",
    "-4104":"无效的合约类型。",
    "-4114":"clientTranId不正确。",
    "-4115":"clientTranId重复。",
    "-4118":"仅减仓订单失败。请检查现有的持仓和挂单。",
    "-4131":"交易对手的最高价格未达到PERCENT_PRICE过滤器限制。",
    "-4135":"无效的激活价格。",
    "-4137":"数量必须为0，当closePosition为true时",
    "-4138":"Reduce only 必须为true，当closePosition为true时",
    "-4139":"订单类型不能为市价单如果不能取消",
    "-4140":"无效的交易对状态",
    "-4141":"交易对已下架",
    "-4142":"拒绝：止盈止损单将立即被触发",
    "-4144":"无效的pair",
    "-4161":"逐仓仓位模式下无法降低杠杆",
    "-4164":"订单的名义价值不可以小于5，除了使用reduce only",
    "-4165":"无效的间隔",
    "-4183":"止盈止损订单价格不应高于触发价与报价乘数上限的乘积",
    "-4184":"止盈止损订单价格不应低于触发价与报价乘数下限的乘积",

}
