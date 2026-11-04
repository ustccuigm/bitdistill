# 预约已建好，但不是“当日加号”

Create 15-minute overbooked appointment_slots for provider ID 'PROV-3344' at 'Downtown Clinic' between 08:00 and 09:00 on 2026-02-03 by increasing capacity_per_slot from 2 to 3 and then add a same-day sick visit booking for patient 'Maria Lopez' (DOB 2012-09-03) with status 'scheduled'.

## 错误与修正

学生选择了正确的患者、医生和时段，却漏掉 is_same_day_booking，接口默认将该预约记为普通预约。

保留原来的预约对象，增加 is_same_day_booking=1，将这次挂号明确标记为当日加号。

## 局部验收与后续执行

检查新预约的患者、医生、时段、scheduled 状态和当日标记，避免被已有预约记录掩盖。

学生在没有新增指导的情况下完成确认；原有时段扩容和新预约一起通过任务验收。

`before/` 保留固定干预状态下的错误响应及重放结果；`steering/` 保留实际 teacher 请求、响应和完整 prompt；`after/` 保留每次局部重试、续跑请求与状态快照。`unsteered_rollout/` 是原无指导续跑记录。`evidence.json` 给出展示的尝试编号及状态验收依据；`tools.json` 为工具定义。
