发货之后，还要关联订单明细

原始轨迹：before/trajectory.json、after/trajectory.json。
教师指导：steering/。干预前状态与原任务验收器：state/。
各轮 request.json/response.json 保留实际请求与生成。
这是同状态指导重试的训练素材，不是训练后无指导性能评测。
创建运单 → 关联明细 → 更新预计送达日期。
