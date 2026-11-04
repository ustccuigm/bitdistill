# 每千次调用的价格，被写成每次调用

Define a metered pricing_plan for product 'API Usage Add-on' with billing_interval 'month', unit_price 0.02 USD per 1,000 API calls, usage_type 'metered', and no trial_period_days, then create it via the API.

## 错误与修正

学生写入 unit_price=0.02，却没有 billing_unit_quantity。接口默认计费单位为 1，变成每次调用 0.02 美元，而不是每 1,000 次。

补上 billing_unit_quantity=1000，并显式设置 trial_period_days=0；月度计费、USD 和 metered 均保持一致。

## 局部验收与后续执行

验收读取 pricing_plans 中新建记录的计费单位与价格，不以接口成功返回作为完成依据。

通过局部验收后撤掉指导，学生给出新套餐的确认；最终状态满足每千次 0.02 美元的任务要求。

`before/` 保留固定干预状态下的错误响应及重放结果；`steering/` 保留实际 teacher 请求、响应和完整 prompt；`after/` 保留每次局部重试、续跑请求与状态快照。`unsteered_rollout/` 是原无指导续跑记录。`evidence.json` 给出展示的尝试编号及状态验收依据；`tools.json` 为工具定义。
