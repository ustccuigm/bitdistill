# “低于 220”不能写成 220

Create a new trip in draft status for traveler 'Maria Gonzalez' with purpose 'Client meeting at Seattle HQ' and cost center 'SALES-NW', including a flight segment from 'SFO' to 'SEA' on '2025-02-10' departing after 8:00 and returning from 'SEA' to 'SFO' on '2025-02-12' after 17:00 in Economy, plus a hotel booking in downtown Seattle from '2025-02-10' to '2025-02-12' at a mid-range property under 220 USD per night.

## 错误与修正

用户要求酒店每晚低于 220 美元，学生却提交 nightly_rate=220。接口接受了这个数值，但它不满足任务的严格上界。

同一行程下重新生成酒店动作，将每晚价格改为 210，入住和退房日期不变。

## 局部验收与后续执行

只检查本次新建行程的酒店：210 < 220，日期为 2 月 10 日至 12 日。

已有去返程航段保持不变，学生不再接收 steering，给出包含酒店和航班的行程确认。

`before/` 保留固定干预状态下的错误响应及重放结果；`steering/` 保留实际 teacher 请求、响应和完整 prompt；`after/` 保留每次局部重试、续跑请求与状态快照。`unsteered_rollout/` 是原无指导续跑记录。`evidence.json` 给出展示的尝试编号及状态验收依据；`tools.json` 为工具定义。
