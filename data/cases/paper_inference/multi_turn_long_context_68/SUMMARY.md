# multi_turn_long_context_68

原始任务和工具定义见 task.json；标准答案见 ground_truth.json。完整推理、调用、工具返回、调用消息位置和正式评分位于各方法目录。

对应论文图 14。Ours 消息 4 使用 display_car_status，环境报未知方法；消息 6 改为 displayCarStatus，消息 8 加 35 加仑，环境确认达到 50。BF16 在加油阶段成功，但整题评分未通过；局部恢复与整题成功不能混为一谈。

| 方法 | 整题评分 |
| --- | --- |
| BF16 | 未通过 |
| Ours | 通过 |
