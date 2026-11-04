# Training steering cases

Ten local steering examples. Each case includes the fixed context and environment snapshot, the teacher request and prompt, the revised student response, a local state check, and continuation without additional steering. Read-only repairs preserve the local database state; final task verification checks the subsequent writes.

- [面积和楼层都对，却漏了装修类型](b2b_saas_2_0/README.md) — `b2b_saas_2:0`
- [“低于 220”不能写成 220](booking_2_2/README.md) — `booking_2:2`
- [标记轮胎不合格，还要留下照片](asset_management_6_6/README.md) — `asset_management_6:6`
- [每千次调用的价格，被写成每次调用](billing_payments_3_5/README.md) — `billing_payments_3:5`
- [预约已建好，但不是“当日加号”](booking_and_scheduling_11_4/README.md) — `booking_and_scheduling_11:4`
- [核销 40 美元，被多写了一个零](b2b_payments_2_9/README.md) — `b2b_payments_2:9`
- [反复查询补卡记录，却没有发起补卡](banking_fintech_3_6/README.md) — `banking_fintech_3:6`
- [写入订单前，要让折扣真正生效](b2b_commerce_1_1/README.md) — `b2b_commerce_1:1`
- [反复思考如何找病历，却没有执行工具](booking_and_scheduling_4_6/README.md) — `booking_and_scheduling_4:6`
- [重复读取预约，没有走到处方写入](booking_and_scheduling_4_8/README.md) — `booking_and_scheduling_4:8`
