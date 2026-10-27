# Recovery case 2: Tool-name recovery

## 任务

I'm about to embark on a road trip adventure and I want my car to be in peak condition. Could you make sure to increase the current fuel level to ensure that my tank is full, so I don't have to keep stopping to refuel along the way?

用户要求把油箱加满；初始油量15加仑，容量50加仑，需要添加35加仑。这里展示整题第一个用户轮次的加油阶段；整题后续还包括启动、轮胎、导航和发帖，完整任务及初始状态见 [task.json](task.json)。

## 方法表现

| 方法 | 加油阶段 | 整题评分 |
|---|---|---|
| BF16 | 先查询15，再补35，返回50 | 未通过 |
| Ours | 首次动作被拒绝，随后自主修正并返回50 | 通过 |

BF16在本段完成加油，但后续导航传入`456 Oakwood Avenue, Rivermist, ID`，参考记录为`456 Oakwood Avenue, Rivermist, 83214`；整题评分未通过，不能把本段完成写成整题成功。完整判分见 [BF16/score.json](BF16/score.json)。

## 分歧与恢复位置

消息序号从0开始，对应各方法`trajectory.json`中的`trajectory`数组。

| Ours消息 | 行为或反馈 |
|---|---|
| 4 | **首次错误动作**：`{"name": "mcp_tool_display_car_status", "arguments": {"option": "fuel"}}` |
| 5 | **工具拒绝**：`Unknown method 'display_car_status'` |
| 6 | **开始修正**：调用`displayCarStatus(option="fuel")` |
| 7 | 工具返回当前油量15 |
| 8 | 根据50−15计算，调用`fillFuelTank(fuelAmount=35)` |
| 9 | **恢复完成**：工具返回`fuelLevel: 50.0` |

BF16对应消息4先查询油量，消息6补充35，消息7返回50。恢复区间没有新增用户或teacher指导消息，只有学生响应与工具反馈。

## 错误原因与恢复依据

**首次错误原因：** 计划先查询油量，但调用时将工具名displayCarStatus写成了display_car_status。

**为什么修正有效：** 工具的错误返回提供了可操作的反馈。Ours随后查询到当前油量，再按剩余容量补充35；成功依据是工具返回50，而不只是模型口头声称完成。

**推理对应位置：** 消息6包含对错误反馈的重新分析；消息8明确计算50−15=35。完整推理、动作和返回见 [Ours/cot_and_actions.md](Ours/cot_and_actions.md)，关键原文见 [Ours/recovery_excerpt.json](Ours/recovery_excerpt.json)。
