# 写入订单前，要让折扣真正生效

For customer_account 'Joe's Auto Repair' (price_tier 'silver'), create a sales_order with a requested_ship_date of '2026-01-05' containing three order_lines: 10 units of part SKU 'OIL-FLTR-001', 4 units of 'BRK-TOY-001', and 2 units of 'BAT-12V-600CCA', letting the system apply the appropriate discount_rules and setting backorder_status to 'allow' for any lines that cannot be fully filled.

## 错误与修正

学生直接按标价写入订单行，discount_percent=0；没有应用 silver 客户适用的定价规则。

修正后的第一步改为 apply_pricing_rules_to_line，先取得折扣和单价，避免直接写入错误价格。

## 局部验收与后续执行

这个局部步骤是查询，不新增订单行；验收检查目标订单没有新增折扣或价格错误的首条明细。

撤掉指导后，学生根据定价返回写入订单行，并继续完成其余明细；最终三条订单的数量、折扣、单价和延期交付设置通过任务验收。

`before/` 保留固定干预状态下的错误响应及重放结果；`steering/` 保留实际 teacher 请求、响应和完整 prompt；`after/` 保留每次局部重试、续跑请求与状态快照。`unsteered_rollout/` 是原无指导续跑记录。`evidence.json` 给出展示的尝试编号及状态验收依据；`tools.json` 为工具定义。
