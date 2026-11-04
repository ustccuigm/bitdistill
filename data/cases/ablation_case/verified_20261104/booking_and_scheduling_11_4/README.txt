先扩充时段容量，再完成当天预约
任务：Create 15-minute overbooked appointment_slots for provider ID 'PROV-3344' at 'Downtown Clinic' between 08:00 and 09:00 on 2026-02-03 by increasing capacity_per_slot from 2 to 3 and then add a same-day sick visit booking for patient 'Maria Lopez' (DOB 2012-09-03) with status 'scheduled'.

五分支使用相同保存状态与学生模型，均实际执行且工具请求全部 HTTP 200。
原生验收：teacher_structured 成功，其余四分支失败。
自由文本教师、学生结构化指导和无指导分支的预约 is_same_day_booking=0；外部指导分支重复创建已有 08:00 时段，最终为五个时段，原生验收要求恰好四个。
保留完整指导、请求、响应、轨迹、初末数据库及验收代码；页面仅摘录关键动作。
这是筛选出的单次案例，不表示整体成功率。
来源：/mnt/genming/case-rerun-20261103/expanded-history/point-3855af42427414/cases/booking_and_scheduling_11_4
