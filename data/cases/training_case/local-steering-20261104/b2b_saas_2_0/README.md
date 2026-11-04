# 面积和楼层都对，却漏了装修类型

Create a new office property at '120 Market Street, Sydney NSW 2000' with key_features ['A-grade office tower', 'On-site parking', 'End-of-trip facilities'], then add three units (Unit 501: floor_area 750 sqm, floor_number 5, fitout_type 'open plan', occupancy_status 'vacant'; Unit 502: floor_area 600 sqm, floor_number 5, fitout_type 'spec fitout', occupancy_status 'occupied'; Unit 601: floor_area 800 sqm, floor_number 6, fitout_type 'shell', occupancy_status 'vacant').

## 错误与修正

Unit 501 的面积、楼层、空置状态都写对了，但调用没有 fitout_type，落库后装修类型为空，未满足用户明确要求的 open plan。

在同一位置重新创建 Unit 501，补上 fitout_type="open plan"；其余房间属性保持任务要求。

## 局部验收与后续执行

检查新建物业下的 Unit 501，而不是数据库中另一个同名房间。

撤掉指导后继续建立 Unit 502 和 Unit 601；三间房的面积、楼层、装修类型和入住状态全部齐全。

`before/` 保留固定干预状态下的错误响应及重放结果；`steering/` 保留实际 teacher 请求、响应和完整 prompt；`after/` 保留每次局部重试、续跑请求与状态快照。`unsteered_rollout/` 是原无指导续跑记录。`evidence.json` 给出展示的尝试编号及状态验收依据；`tools.json` 为工具定义。
