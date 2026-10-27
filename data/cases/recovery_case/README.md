# Recovery case

整理的数据包含论文中的两个自主纠错案例，方法名为BF16和Ours。

| 案例 | 任务 | 恢复过程 |
|---|---|---|
| [Fuel-capacity recovery](multi_turn_miss_func_68/SUMMARY.md) | multi_turn_miss_func_68 | 加油超过容量被拒绝，查明已有15加仑后补35 |
| [Tool-name recovery](multi_turn_long_context_68/SUMMARY.md) | multi_turn_long_context_68 | 错误接口被拒绝，修正工具名后查询油量并补35 |

每个案例包含任务、初始状态、标准答案、方法总结、完整轨迹、推理与动作、工具返回、评分及带消息序号的恢复节选。`catalog.json`提供索引，`checksums.json`用于核对文件完整性。

两例的Ours均通过整题评分。第二例BF16完成所展示的加油阶段，但整题评分未通过；阶段结果与整题结果分别列出。轨迹中的工具反馈来自BFCL基准环境，不代表真实车辆执行。
