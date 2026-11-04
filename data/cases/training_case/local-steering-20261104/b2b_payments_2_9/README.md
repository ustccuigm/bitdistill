# 核销 40 美元，被多写了一个零

For payment_id 'PMT-2025-00077', create a remittance_advice that allocates 8,000.00 USD to invoice 'INV-2024-1190' with a 160.00 early_payment_discount, 4,300.00 USD to invoice 'INV-2024-1215' with a 40.00 write_off, marks both invoices as fully paid, and then update the payment's reconciliation_status to 'reconciled'.

## 错误与修正

任务要求给第二张发票分配 4,300 美元、核销 40 美元；学生把 write_off_amount 写成 400。

同一付款和发票下，保留 allocated_amount=4300，将 write_off_amount 改回 40。

## 局部验收与后续执行

读取新建汇款通知的实际金额，确认核销是 40 而不是 400。

撤掉指导后，学生继续把两张发票标为已付，并将付款 reconciliation_status 更新为 reconciled。

`before/` 保留固定干预状态下的错误响应及重放结果；`steering/` 保留实际 teacher 请求、响应和完整 prompt；`after/` 保留每次局部重试、续跑请求与状态快照。`unsteered_rollout/` 是原无指导续跑记录。`evidence.json` 给出展示的尝试编号及状态验收依据；`tools.json` 为工具定义。
