# Case 038 — parallel_multiple_75

## 任务

第 1 轮：

"Can you help me plan my day? I want to start from my home in New York and go to a chess club named 'Knight Gambit' located in Boston. I want to take the fastest route. After that, I want to go to another chess club named 'Rook Corner' in Philadelphia, again taking the fastest route. Finally, I want to return home, but this time I want to take the shortest route. Can you also provide me with the details of the events hosted by both chess clubs?"

完整工具定义、初始状态及其他任务字段见 task.json。

## 七种方法的实际表现

### BF16：通过

实际任务调用 5 次；[完整 CoT 和工具返回](BF16/cot_and_actions.txt)。

<details><summary>实际动作序列</summary>

```json
[
  {
    "user_turn": 1,
    "action_in_turn": 1,
    "message_index": 4,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_route_planner.calculate_route",
      "arguments": {
        "start": "New York",
        "destination": "Boston",
        "method": "fastest"
      }
    }
  },
  {
    "user_turn": 1,
    "action_in_turn": 2,
    "message_index": 6,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_chess_club_details.find",
      "arguments": {
        "name": "Knight Gambit",
        "city": "Boston"
      }
    }
  },
  {
    "user_turn": 1,
    "action_in_turn": 3,
    "message_index": 8,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_route_planner.calculate_route",
      "arguments": {
        "start": "Boston",
        "destination": "Philadelphia",
        "method": "fastest"
      }
    }
  },
  {
    "user_turn": 1,
    "action_in_turn": 4,
    "message_index": 10,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_chess_club_details.find",
      "arguments": {
        "name": "Rook Corner",
        "city": "Philadelphia"
      }
    }
  },
  {
    "user_turn": 1,
    "action_in_turn": 5,
    "message_index": 12,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_route_planner.calculate_route",
      "arguments": {
        "start": "Philadelphia",
        "destination": "New York",
        "method": "shortest"
      }
    }
  }
]
```

</details>

### Ours：通过

实际任务调用 5 次；[完整 CoT 和工具返回](Ours/cot_and_actions.txt)。

<details><summary>实际动作序列</summary>

```json
[
  {
    "user_turn": 1,
    "action_in_turn": 1,
    "message_index": 4,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_route_planner.calculate_route",
      "arguments": {
        "start": "New York",
        "destination": "Boston",
        "method": "fastest"
      }
    }
  },
  {
    "user_turn": 1,
    "action_in_turn": 2,
    "message_index": 6,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_route_planner.calculate_route",
      "arguments": {
        "start": "Boston",
        "destination": "Philadelphia",
        "method": "fastest"
      }
    }
  },
  {
    "user_turn": 1,
    "action_in_turn": 3,
    "message_index": 8,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_route_planner.calculate_route",
      "arguments": {
        "start": "Philadelphia",
        "destination": "New York",
        "method": "shortest"
      }
    }
  },
  {
    "user_turn": 1,
    "action_in_turn": 4,
    "message_index": 10,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_chess_club_details.find",
      "arguments": {
        "name": "Knight Gambit",
        "city": "Boston"
      }
    }
  },
  {
    "user_turn": 1,
    "action_in_turn": 5,
    "message_index": 12,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_chess_club_details.find",
      "arguments": {
        "name": "Rook Corner",
        "city": "Philadelphia"
      }
    }
  }
]
```

</details>

### GPTQ：未通过

实际任务调用 5 次；[完整 CoT 和工具返回](GPTQ/cot_and_actions.txt)。

<details><summary>实际动作序列</summary>

```json
[
  {
    "user_turn": 1,
    "action_in_turn": 1,
    "message_index": 4,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_route_planner.calculate_route",
      "arguments": {
        "start": "Home in New York",
        "destination": "Knight Gambit, Boston",
        "method": "fastest"
      }
    }
  },
  {
    "user_turn": 1,
    "action_in_turn": 2,
    "message_index": 6,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_route_planner.calculate_route",
      "arguments": {
        "start": "Knight Gambit, Boston",
        "destination": "Rook Corner, Philadelphia",
        "method": "fastest"
      }
    }
  },
  {
    "user_turn": 1,
    "action_in_turn": 3,
    "message_index": 8,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_route_planner.calculate_route",
      "arguments": {
        "start": "Rook Corner, Philadelphia",
        "destination": "Home in New York",
        "method": "shortest"
      }
    }
  },
  {
    "user_turn": 1,
    "action_in_turn": 4,
    "message_index": 10,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_chess_club_details.find",
      "arguments": {
        "name": "Knight Gambit",
        "city": "Boston"
      }
    }
  },
  {
    "user_turn": 1,
    "action_in_turn": 5,
    "message_index": 12,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_chess_club_details.find",
      "arguments": {
        "name": "Rook Corner",
        "city": "Philadelphia"
      }
    }
  }
]
```

</details>

### EfficientQAT：未通过

实际任务调用 5 次；[完整 CoT 和工具返回](EfficientQAT/cot_and_actions.txt)。

<details><summary>实际动作序列</summary>

```json
[
  {
    "user_turn": 1,
    "action_in_turn": 1,
    "message_index": 4,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_route_planner.calculate_route",
      "arguments": {
        "start": "Home",
        "destination": "Knight Gambit Chess Club",
        "method": "fastest"
      }
    }
  },
  {
    "user_turn": 1,
    "action_in_turn": 2,
    "message_index": 6,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_chess_club_details.find",
      "arguments": {
        "name": "Knight Gambit",
        "city": "Boston"
      }
    }
  },
  {
    "user_turn": 1,
    "action_in_turn": 3,
    "message_index": 8,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_route_planner.calculate_route",
      "arguments": {
        "start": "Knight Gambit",
        "destination": "Rook Corner",
        "method": "fastest"
      }
    }
  },
  {
    "user_turn": 1,
    "action_in_turn": 4,
    "message_index": 10,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_chess_club_details.find",
      "arguments": {
        "name": "Rook Corner",
        "city": "Philadelphia"
      }
    }
  },
  {
    "user_turn": 1,
    "action_in_turn": 5,
    "message_index": 12,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_route_planner.calculate_route",
      "arguments": {
        "start": "Rook Corner",
        "destination": "Home",
        "method": "shortest"
      }
    }
  }
]
```

</details>

### BitDistiller：未通过

实际任务调用 5 次；[完整 CoT 和工具返回](BitDistiller/cot_and_actions.txt)。

<details><summary>实际动作序列</summary>

```json
[
  {
    "user_turn": 1,
    "action_in_turn": 1,
    "message_index": 4,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_chess_club_details.find",
      "arguments": {
        "name": "Knight Gambit",
        "city": "Boston"
      }
    }
  },
  {
    "user_turn": 1,
    "action_in_turn": 2,
    "message_index": 6,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_chess_club_details.find",
      "arguments": {
        "name": "Rook Corner",
        "city": "Philadelphia"
      }
    }
  },
  {
    "user_turn": 1,
    "action_in_turn": 3,
    "message_index": 8,
    "action": {
      "wrapper": "call_tool",
      "name": "m_c_p_tool_route_planner.calculate_route",
      "arguments": {
        "start": "New York",
        "destination": "Boston",
        "method": "fastest"
      }
    }
  },
  {
    "user_turn": 1,
    "action_in_turn": 4,
    "message_index": 10,
    "action": {
      "wrapper": "call_tool",
      "name": "m_c_p_tool_route_planner.calculate_route",
      "arguments": {
        "start": "Boston",
        "destination": "Philadelphia",
        "method": "fastest"
      }
    }
  },
  {
    "user_turn": 1,
    "action_in_turn": 5,
    "message_index": 12,
    "action": {
      "wrapper": "call_tool",
      "name": "m_c_p_tool_route_planner.calculate_route",
      "arguments": {
        "start": "Philadelphia",
        "destination": "New York",
        "method": "shortest"
      }
    }
  }
]
```

</details>

### On-Policy QAD：未通过

实际任务调用 5 次；[完整 CoT 和工具返回](On-Policy%20QAD/cot_and_actions.txt)。

<details><summary>实际动作序列</summary>

```json
[
  {
    "user_turn": 1,
    "action_in_turn": 1,
    "message_index": 4,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_route_planner.calculate_route",
      "arguments": {
        "start": "New York",
        "destination": "Knight Gambit",
        "method": "fastest"
      }
    }
  },
  {
    "user_turn": 1,
    "action_in_turn": 2,
    "message_index": 6,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_route_planner.calculate_route",
      "arguments": {
        "start": "Boston",
        "destination": "Rook Corner",
        "method": "fastest"
      }
    }
  },
  {
    "user_turn": 1,
    "action_in_turn": 3,
    "message_index": 8,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_route_planner.calculate_route",
      "arguments": {
        "start": "Philadelphia",
        "destination": "New York",
        "method": "shortest"
      }
    }
  },
  {
    "user_turn": 1,
    "action_in_turn": 4,
    "message_index": 10,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_chess_club_details.find",
      "arguments": {
        "name": "Knight Gambit",
        "city": "Boston"
      }
    }
  },
  {
    "user_turn": 1,
    "action_in_turn": 5,
    "message_index": 12,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_chess_club_details.find",
      "arguments": {
        "name": "Rook Corner",
        "city": "Philadelphia"
      }
    }
  }
]
```

</details>

### QeRL：未通过

实际任务调用 7 次；[完整 CoT 和工具返回](QeRL/cot_and_actions.txt)。

<details><summary>实际动作序列</summary>

```json
[
  {
    "user_turn": 1,
    "action_in_turn": 1,
    "message_index": 4,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_chess_club_details.find",
      "arguments": {
        "name": "Knight Gambit",
        "city": "Boston"
      }
    }
  },
  {
    "user_turn": 1,
    "action_in_turn": 2,
    "message_index": 6,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_route_planner.calculate_route",
      "arguments": {
        "start": "New York",
        "destination": "Boston",
        "method": "fastest"
      }
    }
  },
  {
    "user_turn": 1,
    "action_in_turn": 3,
    "message_index": 8,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_chess_club_details.find",
      "arguments": {
        "name": "Rook Corner",
        "city": "Philadelphia"
      }
    }
  },
  {
    "user_turn": 1,
    "action_in_turn": 4,
    "message_index": 10,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_route_planner.calculate_route",
      "arguments": {
        "start": "Boston",
        "destination": "Philadelphia",
        "method": "fastest"
      }
    }
  },
  {
    "user_turn": 1,
    "action_in_turn": 5,
    "message_index": 12,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_route_planner.calculate_route",
      "arguments": {
        "start": "Philadelphia",
        "destination": "New York",
        "method": "shortest"
      }
    }
  },
  {
    "user_turn": 1,
    "action_in_turn": 6,
    "message_index": 14,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_chess_club_details.find",
      "arguments": {
        "name": "Knight Gambit",
        "city": "Boston",
        "event": "events"
      }
    }
  },
  {
    "user_turn": 1,
    "action_in_turn": 7,
    "message_index": 16,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_chess_club_details.find",
      "arguments": {
        "name": "Rook Corner",
        "city": "Philadelphia",
        "event": "events"
      }
    }
  }
]
```

</details>

## 分歧位置

消息编号从 0 开始，用户轮和动作编号从 1 开始。按同一用户轮的任务动作序号与 BF16 比较，忽略 list_tools。最早动作差异不一定就是失败起点：正确的工具顺序、补救步骤也可能不同；评分失败位置另见下一节。

### Ours

最早动作差异：第 1 个用户轮，第 2 个任务动作；BF16 消息 6，本方法消息 6。

```json
[
  {
    "field": "$.arguments.city",
    "reference": "Boston",
    "actual": null,
    "reference_present": true,
    "actual_present": false
  },
  {
    "field": "$.arguments.destination",
    "reference": null,
    "actual": "Philadelphia",
    "reference_present": false,
    "actual_present": true
  },
  {
    "field": "$.arguments.method",
    "reference": null,
    "actual": "fastest",
    "reference_present": false,
    "actual_present": true
  },
  {
    "field": "$.arguments.name",
    "reference": "Knight Gambit",
    "actual": null,
    "reference_present": true,
    "actual_present": false
  },
  {
    "field": "$.arguments.start",
    "reference": null,
    "actual": "Boston",
    "reference_present": false,
    "actual_present": true
  },
  {
    "field": "$.name",
    "reference": "mcp_tool_chess_club_details.find",
    "actual": "mcp_tool_route_planner.calculate_route"
  }
]
```

### GPTQ

最早动作差异：第 1 个用户轮，第 1 个任务动作；BF16 消息 4，本方法消息 4。

```json
[
  {
    "field": "$.arguments.destination",
    "reference": "Boston",
    "actual": "Knight Gambit, Boston"
  },
  {
    "field": "$.arguments.start",
    "reference": "New York",
    "actual": "Home in New York"
  }
]
```

### EfficientQAT

最早动作差异：第 1 个用户轮，第 1 个任务动作；BF16 消息 4，本方法消息 4。

```json
[
  {
    "field": "$.arguments.destination",
    "reference": "Boston",
    "actual": "Knight Gambit Chess Club"
  },
  {
    "field": "$.arguments.start",
    "reference": "New York",
    "actual": "Home"
  }
]
```

### BitDistiller

最早动作差异：第 1 个用户轮，第 1 个任务动作；BF16 消息 4，本方法消息 4。

```json
[
  {
    "field": "$.arguments.city",
    "reference": null,
    "actual": "Boston",
    "reference_present": false,
    "actual_present": true
  },
  {
    "field": "$.arguments.destination",
    "reference": "Boston",
    "actual": null,
    "reference_present": true,
    "actual_present": false
  },
  {
    "field": "$.arguments.method",
    "reference": "fastest",
    "actual": null,
    "reference_present": true,
    "actual_present": false
  },
  {
    "field": "$.arguments.name",
    "reference": null,
    "actual": "Knight Gambit",
    "reference_present": false,
    "actual_present": true
  },
  {
    "field": "$.arguments.start",
    "reference": "New York",
    "actual": null,
    "reference_present": true,
    "actual_present": false
  },
  {
    "field": "$.name",
    "reference": "mcp_tool_route_planner.calculate_route",
    "actual": "mcp_tool_chess_club_details.find"
  }
]
```

### On-Policy QAD

最早动作差异：第 1 个用户轮，第 1 个任务动作；BF16 消息 4，本方法消息 4。

```json
[
  {
    "field": "$.arguments.destination",
    "reference": "Boston",
    "actual": "Knight Gambit"
  }
]
```

### QeRL

最早动作差异：第 1 个用户轮，第 1 个任务动作；BF16 消息 4，本方法消息 4。

```json
[
  {
    "field": "$.arguments.city",
    "reference": null,
    "actual": "Boston",
    "reference_present": false,
    "actual_present": true
  },
  {
    "field": "$.arguments.destination",
    "reference": "Boston",
    "actual": null,
    "reference_present": true,
    "actual_present": false
  },
  {
    "field": "$.arguments.method",
    "reference": "fastest",
    "actual": null,
    "reference_present": true,
    "actual_present": false
  },
  {
    "field": "$.arguments.name",
    "reference": null,
    "actual": "Knight Gambit",
    "reference_present": false,
    "actual_present": true
  },
  {
    "field": "$.arguments.start",
    "reference": "New York",
    "actual": null,
    "reference_present": true,
    "actual_present": false
  },
  {
    "field": "$.name",
    "reference": "mcp_tool_route_planner.calculate_route",
    "actual": "mcp_tool_chess_club_details.find"
  }
]
```

## 失败原因

涉及路线地点写法、函数名和调用数量差异。城市与俱乐部名称的匹配问题需按具体参数解读，不能把所有排列匹配失败都看作路线顺序错误。

### GPTQ

评分指出的失败位置/原因：

```text
["Could not find a matching function among index [0, 1, 2, 3, 4] of model output for index 0 of possible answers.", {"Model Result Index 0": {"sub_error": ["Invalid value for parameter 'start': 'Home in New York'. Expected one of ['New York']. Case insensitive."], "sub_error_type": "value_error:string", "model_output_item": {"route_planner.calculate_route": {"start": "Home in New York", "destination": "Knight Gambit, Boston", "method": "fastest"}}, "possible_answer_item": {"route_planner.calculate_route": {"start": ["New York"], "destination": ["Boston"], "method": ["fastest", ""]}}}}, {"Model Result Index 1": {"sub_error": ["Invalid value for parameter 'start': 'Knight Gambit, Boston'. Expected one of ['New York']. Case insensitive."], "sub_error_type": "value_error:string", "model_output_item": {"route_planner.calculate_route": {"start": "Knight Gambit, Boston", "destination": "Rook Corner, Philadelphia", "method": "fastest"}}, "possible_answer_item": {"route_planner.calculate_route": {"start": ["New York"], "destination": ["Boston"], "method": ["fastest", ""]}}}}, {"Model Result Index 2": {"sub_error": ["Invalid value for parameter 'start': 'Rook Corner, Philadelphia'. Expected one of ['New York']. Case insensitive."], "sub_error_type": "value_error:string", "model_output_item": {"route_planner.calculate_route": {"start": "Rook Corner, Philadelphia", "destination": "Home in New York", "method": "shortest"}}, "possible_answer_item": {"route_planner.calculate_route": {"start": ["New York"], "destination": ["Boston"], "method": ["fastest", ""]}}}}, {"Model Result Index 3": {"sub_error": ["Function name 'route_planner.calculate_route' not found in model output."], "sub_error_type": "simple_function_checker:wrong_func_name", "model_output_item": {"chess_club_details.find": {"name": "Knight Gambit", "city": "Boston"}}, "possible_answer_item": {"route_planner.calculate_route": {"start": ["New York"], "destination": ["Boston"], "method": ["fastest", ""]}}}}, {"Model Resu ...（完整值见 score.json / analysis.json）
```

### EfficientQAT

评分指出的失败位置/原因：

```text
["Could not find a matching function among index [0, 1, 2, 3, 4] of model output for index 0 of possible answers.", {"Model Result Index 0": {"sub_error": ["Invalid value for parameter 'start': 'Home'. Expected one of ['New York']. Case insensitive."], "sub_error_type": "value_error:string", "model_output_item": {"route_planner.calculate_route": {"start": "Home", "destination": "Knight Gambit Chess Club", "method": "fastest"}}, "possible_answer_item": {"route_planner.calculate_route": {"start": ["New York"], "destination": ["Boston"], "method": ["fastest", ""]}}}}, {"Model Result Index 1": {"sub_error": ["Function name 'route_planner.calculate_route' not found in model output."], "sub_error_type": "simple_function_checker:wrong_func_name", "model_output_item": {"chess_club_details.find": {"name": "Knight Gambit", "city": "Boston"}}, "possible_answer_item": {"route_planner.calculate_route": {"start": ["New York"], "destination": ["Boston"], "method": ["fastest", ""]}}}}, {"Model Result Index 2": {"sub_error": ["Invalid value for parameter 'start': 'Knight Gambit'. Expected one of ['New York']. Case insensitive."], "sub_error_type": "value_error:string", "model_output_item": {"route_planner.calculate_route": {"start": "Knight Gambit", "destination": "Rook Corner", "method": "fastest"}}, "possible_answer_item": {"route_planner.calculate_route": {"start": ["New York"], "destination": ["Boston"], "method": ["fastest", ""]}}}}, {"Model Result Index 3": {"sub_error": ["Function name 'route_planner.calculate_route' not found in model output."], "sub_error_type": "simple_function_checker:wrong_func_name", "model_output_item": {"chess_club_details.find": {"name": "Rook Corner", "city": "Philadelphia"}}, "possible_answer_item": {"route_planner.calculate_route": {"start": ["New York"], "destination": ["Boston"], "method": ["fastest", ""]}}}}, {"Model Result Index 4": {"sub_error": ["Invalid value for parameter 'start': 'Rook Corner'. Expected one of ['New York']. Case insensiti ...（完整值见 score.json / analysis.json）
```

### BitDistiller

评分指出的失败位置/原因：

```text
["Could not find a matching function among index [0, 1, 2, 3, 4] of model output for index 0 of possible answers.", {"Model Result Index 0": {"sub_error": ["Function name 'route_planner.calculate_route' not found in model output."], "sub_error_type": "simple_function_checker:wrong_func_name", "model_output_item": {"chess_club_details.find": {"name": "Knight Gambit", "city": "Boston"}}, "possible_answer_item": {"route_planner.calculate_route": {"start": ["New York"], "destination": ["Boston"], "method": ["fastest", ""]}}}}, {"Model Result Index 1": {"sub_error": ["Function name 'route_planner.calculate_route' not found in model output."], "sub_error_type": "simple_function_checker:wrong_func_name", "model_output_item": {"chess_club_details.find": {"name": "Rook Corner", "city": "Philadelphia"}}, "possible_answer_item": {"route_planner.calculate_route": {"start": ["New York"], "destination": ["Boston"], "method": ["fastest", ""]}}}}, {"Model Result Index 2": {"sub_error": ["Function name 'route_planner.calculate_route' not found in model output."], "sub_error_type": "simple_function_checker:wrong_func_name", "model_output_item": {"m_c_p_tool_route_planner.calculate_route": {"start": "New York", "destination": "Boston", "method": "fastest"}}, "possible_answer_item": {"route_planner.calculate_route": {"start": ["New York"], "destination": ["Boston"], "method": ["fastest", ""]}}}}, {"Model Result Index 3": {"sub_error": ["Function name 'route_planner.calculate_route' not found in model output."], "sub_error_type": "simple_function_checker:wrong_func_name", "model_output_item": {"m_c_p_tool_route_planner.calculate_route": {"start": "Boston", "destination": "Philadelphia", "method": "fastest"}}, "possible_answer_item": {"route_planner.calculate_route": {"start": ["New York"], "destination": ["Boston"], "method": ["fastest", ""]}}}}, {"Model Result Index 4": {"sub_error": ["Function name 'route_planner.calculate_route' not found in model output."], "sub_error_type": "simple ...（完整值见 score.json / analysis.json）
```

### On-Policy QAD

评分指出的失败位置/原因：

```text
["Could not find a matching function among index [0, 1, 2, 3, 4] of model output for index 0 of possible answers.", {"Model Result Index 0": {"sub_error": ["Invalid value for parameter 'destination': 'Knight Gambit'. Expected one of ['Boston']. Case insensitive."], "sub_error_type": "value_error:string", "model_output_item": {"route_planner.calculate_route": {"start": "New York", "destination": "Knight Gambit", "method": "fastest"}}, "possible_answer_item": {"route_planner.calculate_route": {"start": ["New York"], "destination": ["Boston"], "method": ["fastest", ""]}}}}, {"Model Result Index 1": {"sub_error": ["Invalid value for parameter 'start': 'Boston'. Expected one of ['New York']. Case insensitive."], "sub_error_type": "value_error:string", "model_output_item": {"route_planner.calculate_route": {"start": "Boston", "destination": "Rook Corner", "method": "fastest"}}, "possible_answer_item": {"route_planner.calculate_route": {"start": ["New York"], "destination": ["Boston"], "method": ["fastest", ""]}}}}, {"Model Result Index 2": {"sub_error": ["Invalid value for parameter 'start': 'Philadelphia'. Expected one of ['New York']. Case insensitive."], "sub_error_type": "value_error:string", "model_output_item": {"route_planner.calculate_route": {"start": "Philadelphia", "destination": "New York", "method": "shortest"}}, "possible_answer_item": {"route_planner.calculate_route": {"start": ["New York"], "destination": ["Boston"], "method": ["fastest", ""]}}}}, {"Model Result Index 3": {"sub_error": ["Function name 'route_planner.calculate_route' not found in model output."], "sub_error_type": "simple_function_checker:wrong_func_name", "model_output_item": {"chess_club_details.find": {"name": "Knight Gambit", "city": "Boston"}}, "possible_answer_item": {"route_planner.calculate_route": {"start": ["New York"], "destination": ["Boston"], "method": ["fastest", ""]}}}}, {"Model Result Index 4": {"sub_error": ["Function name 'route_planner.calculate_route' not found in model ...（完整值见 score.json / analysis.json）
```

### QeRL

评分指出的失败位置/原因：

```text
["Wrong number of functions."]
```
