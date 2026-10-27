# Parent-menu retrieval

## 任务

Publish a new version of the 'Ghost Kitchen Late Night' menu for the 'Midtown Cloud Kitchen' location that adds the 'Loaded Kimchi Fries' menu_item, unpublishes the 'Classic Nachos' item, and records an audit note 'Shifted to Korean-inspired snacks based on sales data'.

## 前后表现

原list_menu_items调用合法，返回空列表；修正后的list_menus调用合法，找到id=4的Ghost Kitchen Late Night。两次查询都不改变数据库。

## 分歧位置与原因

具体调用、assistant轮次和当时的判断见[case.json](case.json)。该文件保留生成时的分析，不把其中的“expected”自动当成实际成功结果。当前执行结果以[execution/execution_comparison.json](execution/execution_comparison.json)为准。

## 执行与验收范围

可展示steer改变查询方向并取得菜单ID，但现有结果不能证明原查询非法，也不能证明该位置是state-only定位下的状态分歧。

本次从环境提供的数据重建隔离数据库，按已记录上下文重放前序调用，再分别从同一pre-state执行前后候选动作。保存HTTP返回、数据库变化和前后数据库。不是从旧运行缺失的快照恢复，也不是新生成的一整轮steering训练。

## 数据

- [before/trajectory.json](before/trajectory.json)：指导前完整记录。
- [after/trajectory.json](after/trajectory.json)：已保存的指导后候选调用及上下文，不含未执行的后续轨迹。
- [steering/analysis.json](steering/analysis.json)：分析记录。
- [steering/raw_steering_prompt.txt](steering/raw_steering_prompt.txt)：实际保存的steering输入。
- [execution/tool_schema.json](execution/tool_schema.json)：执行环境接口定义。
- [execution/prefix_replay.json](execution/prefix_replay.json)：前序调用执行返回。
- [execution/before_execution.json](execution/before_execution.json)、[execution/after_execution.json](execution/after_execution.json)：前后候选执行结果。
