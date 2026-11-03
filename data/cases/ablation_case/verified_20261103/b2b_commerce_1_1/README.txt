销售订单：完整五分支复测
任务：For customer_account 'Joe's Auto Repair' (price_tier 'silver'), create a sales_order with a requested_ship_date of '2026-01-05' containing three order_lines: 10 units of part SKU 'OIL-FLTR-001', 4 units of 'BRK-TOY-001', and 2 units of 'BAT-12V-600CCA', letting the system apply the appropriate discount_rules and setting backorder_status to 'allow' for any lines that cannot be fully filled.

五个分支使用同一保存状态和学生模型。teacher_structured 通过原生验收，其余四个分支未通过；均无 HTTP 500。
每个分支保留原始指导、模型请求与响应、执行轨迹、初末数据库和验收结果。
来源：/mnt/genming/case-rerun-20261103/ablation-only/cases/b2b_commerce_1_1
