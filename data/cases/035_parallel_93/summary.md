# Case 035 — parallel_93

## 原始任务

第 1 轮：

What would be the estimated travel time if I start my journey from New York, make stops at Philadelphia, Washington D.C., and Atlanta, and finally reach Miami? Also, what if I skip the stop at Atlanta and directly go to Miami from Washington D.C.? And lastly, what if I start from Philadelphia instead of New York, stop at Washington D.C., and then reach Miami?

完整工具定义、初始状态及其他任务字段见 task.json。

## 七种方法的实际表现

### BF16：通过

依次使用正确函数和字段提交三种路线。

实际任务调用 3 次；[完整 CoT 和工具返回](BF16/cot_and_actions.txt)。

<details><summary>实际动作序列</summary>

```json
[
  {
    "user_turn": 1,
    "action_in_turn": 1,
    "message_index": 4,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_route.estimate_time",
      "arguments": {
        "start_location": "New York",
        "end_location": "Miami",
        "stops": [
          "Philadelphia",
          "Washington D.C.",
          "Atlanta"
        ]
      }
    }
  },
  {
    "user_turn": 1,
    "action_in_turn": 2,
    "message_index": 6,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_route.estimate_time",
      "arguments": {
        "start_location": "New York",
        "end_location": "Miami",
        "stops": [
          "Philadelphia",
          "Washington D.C."
        ]
      }
    }
  },
  {
    "user_turn": 1,
    "action_in_turn": 3,
    "message_index": 8,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_route.estimate_time",
      "arguments": {
        "start_location": "Philadelphia",
        "end_location": "Miami",
        "stops": [
          "Washington D.C."
        ]
      }
    }
  }
]
```

</details>

### Ours：通过

三次调用都保持正确函数名、参数名和路线内容。

实际任务调用 3 次；[完整 CoT 和工具返回](Ours/cot_and_actions.txt)。

<details><summary>实际动作序列</summary>

```json
[
  {
    "user_turn": 1,
    "action_in_turn": 1,
    "message_index": 4,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_route.estimate_time",
      "arguments": {
        "start_location": "New York",
        "end_location": "Miami",
        "stops": [
          "Philadelphia",
          "Washington D.C.",
          "Atlanta"
        ]
      }
    }
  },
  {
    "user_turn": 1,
    "action_in_turn": 2,
    "message_index": 6,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_route.estimate_time",
      "arguments": {
        "start_location": "New York",
        "end_location": "Miami",
        "stops": [
          "Philadelphia",
          "Washington D.C."
        ]
      }
    }
  },
  {
    "user_turn": 1,
    "action_in_turn": 3,
    "message_index": 8,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_route.estimate_time",
      "arguments": {
        "start_location": "Philadelphia",
        "end_location": "Miami",
        "stops": [
          "Washington D.C."
        ]
      }
    }
  }
]
```

</details>

### GPTQ：未通过

第二次调用变成 route.estimated_time，第三次虽恢复函数名，却没有重做第二次。

实际任务调用 3 次；[完整 CoT 和工具返回](GPTQ/cot_and_actions.txt)。

<details><summary>实际动作序列</summary>

```json
[
  {
    "user_turn": 1,
    "action_in_turn": 1,
    "message_index": 4,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_route.estimate_time",
      "arguments": {
        "start_location": "New York",
        "end_location": "Miami",
        "stops": [
          "Philadelphia",
          "Washington D.C.",
          "Atlanta"
        ]
      }
    }
  },
  {
    "user_turn": 1,
    "action_in_turn": 2,
    "message_index": 6,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_route.estimated_time",
      "arguments": {
        "start_location": "New York",
        "end_location": "Miami",
        "stops": [
          "Philadelphia",
          "Washington D.C."
        ]
      }
    }
  },
  {
    "user_turn": 1,
    "action_in_turn": 3,
    "message_index": 8,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_route.estimate_time",
      "arguments": {
        "start_location": "Philadelphia",
        "end_location": "Miami",
        "stops": [
          "Washington D.C."
        ]
      }
    }
  }
]
```

</details>

### EfficientQAT：未通过

第二次提前提交费城出发路线，第三次又遗漏华盛顿经停，纽约出发的第二种方案没有正确查询。

实际任务调用 3 次；[完整 CoT 和工具返回](EfficientQAT/cot_and_actions.txt)。

<details><summary>实际动作序列</summary>

```json
[
  {
    "user_turn": 1,
    "action_in_turn": 1,
    "message_index": 4,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_route.estimate_time",
      "arguments": {
        "start_location": "New York",
        "end_location": "Miami",
        "stops": [
          "Philadelphia",
          "Washington D.C.",
          "Atlanta"
        ]
      }
    }
  },
  {
    "user_turn": 1,
    "action_in_turn": 2,
    "message_index": 6,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_route.estimate_time",
      "arguments": {
        "start_location": "Philadelphia",
        "end_location": "Miami",
        "stops": [
          "Washington D.C."
        ]
      }
    }
  },
  {
    "user_turn": 1,
    "action_in_turn": 3,
    "message_index": 8,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_route.estimate_time",
      "arguments": {
        "start_location": "Philadelphia",
        "end_location": "Miami",
        "stops": []
      }
    }
  }
]
```

</details>

### BitDistiller：未通过

第二条路线把 end_location 写成 end；后来发现错误，仅在第三条使用正确字段。

实际任务调用 3 次；[完整 CoT 和工具返回](BitDistiller/cot_and_actions.txt)。

<details><summary>实际动作序列</summary>

```json
[
  {
    "user_turn": 1,
    "action_in_turn": 1,
    "message_index": 4,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_route.estimate_time",
      "arguments": {
        "start_location": "New York",
        "end_location": "Miami",
        "stops": [
          "Philadelphia",
          "Washington D.C.",
          "Atlanta"
        ]
      }
    }
  },
  {
    "user_turn": 1,
    "action_in_turn": 2,
    "message_index": 6,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_route.estimate_time",
      "arguments": {
        "start_location": "New York",
        "end": "Miami",
        "stops": [
          "Philadelphia",
          "Washington D.C."
        ]
      }
    }
  },
  {
    "user_turn": 1,
    "action_in_turn": 3,
    "message_index": 8,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_route.estimate_time",
      "arguments": {
        "start_location": "Philadelphia",
        "end_location": "Miami",
        "stops": [
          "Washington D.C."
        ]
      }
    }
  }
]
```

</details>

### On-Policy QAD：未通过

第二条使用 end，随后受模拟成功响应影响，第三条继续使用 end。

实际任务调用 3 次；[完整 CoT 和工具返回](On-Policy%20QAD/cot_and_actions.txt)。

<details><summary>实际动作序列</summary>

```json
[
  {
    "user_turn": 1,
    "action_in_turn": 1,
    "message_index": 4,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_route.estimate_time",
      "arguments": {
        "start_location": "New York",
        "end_location": "Miami",
        "stops": [
          "Philadelphia",
          "Washington D.C.",
          "Atlanta"
        ]
      }
    }
  },
  {
    "user_turn": 1,
    "action_in_turn": 2,
    "message_index": 6,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_route.estimate_time",
      "arguments": {
        "start_location": "New York",
        "end": "Miami",
        "stops": [
          "Philadelphia",
          "Washington D.C."
        ]
      }
    }
  },
  {
    "user_turn": 1,
    "action_in_turn": 3,
    "message_index": 8,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_route.estimate_time",
      "arguments": {
        "start_location": "Philadelphia",
        "end": "Miami",
        "stops": [
          "Washington D.C."
        ]
      }
    }
  }
]
```

</details>

### QeRL：未通过

第二条使用 end，第三条恢复 end_location，但没有补交第二条。

实际任务调用 3 次；[完整 CoT 和工具返回](QeRL/cot_and_actions.txt)。

<details><summary>实际动作序列</summary>

```json
[
  {
    "user_turn": 1,
    "action_in_turn": 1,
    "message_index": 4,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_route.estimate_time",
      "arguments": {
        "start_location": "New York",
        "end_location": "Miami",
        "stops": [
          "Philadelphia",
          "Washington D.C.",
          "Atlanta"
        ]
      }
    }
  },
  {
    "user_turn": 1,
    "action_in_turn": 2,
    "message_index": 6,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_route.estimate_time",
      "arguments": {
        "start_location": "New York",
        "end": "Miami",
        "stops": [
          "Philadelphia",
          "Washington D.C."
        ]
      }
    }
  },
  {
    "user_turn": 1,
    "action_in_turn": 3,
    "message_index": 8,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_route.estimate_time",
      "arguments": {
        "start_location": "Philadelphia",
        "end_location": "Miami",
        "stops": [
          "Washington D.C."
        ]
      }
    }
  }
]
```

</details>

## 分歧位置

消息编号从 0 开始，用户轮和动作编号从 1 开始。按同一用户轮的任务动作序号与 BF16 比较，忽略 list_tools。最早动作差异不一定就是失败起点：正确的工具顺序、补救步骤也可能不同；评分失败位置另见下一节。

- Ours：按用户轮和动作序号比较，任务动作序列与 BF16 相同。

### GPTQ

最早动作差异：第 1 个用户轮，第 2 个任务动作；BF16 消息 6，本方法消息 6。

```json
[
  {
    "field": "$.name",
    "reference": "mcp_tool_route.estimate_time",
    "actual": "mcp_tool_route.estimated_time"
  }
]
```

### EfficientQAT

最早动作差异：第 1 个用户轮，第 2 个任务动作；BF16 消息 6，本方法消息 6。

```json
[
  {
    "field": "$.arguments.start_location",
    "reference": "New York",
    "actual": "Philadelphia"
  },
  {
    "field": "$.arguments.stops[0]",
    "reference": "Philadelphia",
    "actual": "Washington D.C."
  },
  {
    "field": "$.arguments.stops[1]",
    "reference": "Washington D.C.",
    "actual": null
  }
]
```

### BitDistiller

最早动作差异：第 1 个用户轮，第 2 个任务动作；BF16 消息 6，本方法消息 6。

```json
[
  {
    "field": "$.arguments.end",
    "reference": null,
    "actual": "Miami",
    "reference_present": false,
    "actual_present": true
  },
  {
    "field": "$.arguments.end_location",
    "reference": "Miami",
    "actual": null,
    "reference_present": true,
    "actual_present": false
  }
]
```

### On-Policy QAD

最早动作差异：第 1 个用户轮，第 2 个任务动作；BF16 消息 6，本方法消息 6。

```json
[
  {
    "field": "$.arguments.end",
    "reference": null,
    "actual": "Miami",
    "reference_present": false,
    "actual_present": true
  },
  {
    "field": "$.arguments.end_location",
    "reference": "Miami",
    "actual": null,
    "reference_present": true,
    "actual_present": false
  }
]
```

### QeRL

最早动作差异：第 1 个用户轮，第 2 个任务动作；BF16 消息 6，本方法消息 6。

```json
[
  {
    "field": "$.arguments.end",
    "reference": null,
    "actual": "Miami",
    "reference_present": false,
    "actual_present": true
  },
  {
    "field": "$.arguments.end_location",
    "reference": "Miami",
    "actual": null,
    "reference_present": true,
    "actual_present": false
  }
]
```

## 失败原因

七种方法的第一次调用都正确。分歧从第二次调用开始：GPTQ 把 estimate_time 写成不存在的 estimated_time；BitDistiller、On-Policy QAD 和 QeRL 把必填字段 end_location 改成 end；EfficientQAT 跳过第二条纽约出发的路线，并把第三次调用的经停站清空。BF16 和 Ours 完整保留三条路线及工具接口。部分 baseline 注意到字段名错误，但只在下一条路线改正，没有重新提交已经出错的第二条路线。非多轮 BFCL 这里返回模拟成功消息，因此本例说明不能把模拟返回成功当作接口正确的证据；它不是一次真实出行服务的运行结果。

### GPTQ

第二次调用变成 route.estimated_time，第三次虽恢复函数名，却没有重做第二次。

评分指出的失败位置/原因：

```text
["Could not find a matching function among index [1, 2] of model output for index 1 of possible answers.", {"Model Result Index 1": {"sub_error": ["Function name 'route.estimate_time' not found in model output."], "sub_error_type": "simple_function_checker:wrong_func_name", "model_output_item": {"route.estimated_time": {"start_location": "New York", "end_location": "Miami", "stops": ["Philadelphia", "Washington D.C."]}}, "possible_answer_item": {"route.estimate_time": {"start_location": ["New York", "New York, NY", "NYC"], "end_location": ["Miami"], "stops": [["Washington D.C."], ["Philadelphia", "Washington D.C."], ["Philadelphia", "Washington D.C.", "New York"], ["Philadelphia", "Washington D.C.", "NYC"], ["Washington D.C.", "Philadelphia"], ["Washington D.C.", "Philadelphia", "New York"], ["Washington D.C.", "Philadelphia", "NYC"]]}}}}, {"Model Result Index 2": {"sub_error": ["Invalid value for parameter 'start_location': 'Philadelphia'. Expected one of ['New York', 'New York, NY', 'NYC']. Case insensitive."], "sub_error_type": "value_error:string", "model_output_item": {"route.estimate_time": {"start_location": "Philadelphia", "end_location": "Miami", "stops": ["Washington D.C."]}}, "possible_answer_item": {"route.estimate_time": {"start_location": ["New York", "New York, NY", "NYC"], "end_location": ["Miami"], "stops": [["Washington D.C."], ["Philadelphia", "Washington D.C."], ["Philadelphia", "Washington D.C.", "New York"], ["Philadelphia", "Washington D.C.", "NYC"], ["Washington D.C.", "Philadelphia"], ["Washington D.C.", "Philadelphia", "New York"], ["Washington D.C.", "Philadelphia", "NYC"]]}}}}]
```

### EfficientQAT

第二次提前提交费城出发路线，第三次又遗漏华盛顿经停，纽约出发的第二种方案没有正确查询。

评分指出的失败位置/原因：

```text
["Could not find a matching function among index [1, 2] of model output for index 1 of possible answers.", {"Model Result Index 1": {"sub_error": ["Invalid value for parameter 'start_location': 'Philadelphia'. Expected one of ['New York', 'New York, NY', 'NYC']. Case insensitive."], "sub_error_type": "value_error:string", "model_output_item": {"route.estimate_time": {"start_location": "Philadelphia", "end_location": "Miami", "stops": ["Washington D.C."]}}, "possible_answer_item": {"route.estimate_time": {"start_location": ["New York", "New York, NY", "NYC"], "end_location": ["Miami"], "stops": [["Washington D.C."], ["Philadelphia", "Washington D.C."], ["Philadelphia", "Washington D.C.", "New York"], ["Philadelphia", "Washington D.C.", "NYC"], ["Washington D.C.", "Philadelphia"], ["Washington D.C.", "Philadelphia", "New York"], ["Washington D.C.", "Philadelphia", "NYC"]]}}}}, {"Model Result Index 2": {"sub_error": ["Invalid value for parameter 'start_location': 'Philadelphia'. Expected one of ['New York', 'New York, NY', 'NYC']. Case insensitive."], "sub_error_type": "value_error:string", "model_output_item": {"route.estimate_time": {"start_location": "Philadelphia", "end_location": "Miami", "stops": []}}, "possible_answer_item": {"route.estimate_time": {"start_location": ["New York", "New York, NY", "NYC"], "end_location": ["Miami"], "stops": [["Washington D.C."], ["Philadelphia", "Washington D.C."], ["Philadelphia", "Washington D.C.", "New York"], ["Philadelphia", "Washington D.C.", "NYC"], ["Washington D.C.", "Philadelphia"], ["Washington D.C.", "Philadelphia", "New York"], ["Washington D.C.", "Philadelphia", "NYC"]]}}}}]
```

### BitDistiller

第二条路线把 end_location 写成 end；后来发现错误，仅在第三条使用正确字段。

评分指出的失败位置/原因：

```text
["Could not find a matching function among index [1, 2] of model output for index 1 of possible answers.", {"Model Result Index 1": {"sub_error": ["Missing required parameter: 'end_location'."], "sub_error_type": "simple_function_checker:missing_required", "model_output_item": {"route.estimate_time": {"start_location": "New York", "end": "Miami", "stops": ["Philadelphia", "Washington D.C."]}}, "possible_answer_item": {"route.estimate_time": {"start_location": ["New York", "New York, NY", "NYC"], "end_location": ["Miami"], "stops": [["Washington D.C."], ["Philadelphia", "Washington D.C."], ["Philadelphia", "Washington D.C.", "New York"], ["Philadelphia", "Washington D.C.", "NYC"], ["Washington D.C.", "Philadelphia"], ["Washington D.C.", "Philadelphia", "New York"], ["Washington D.C.", "Philadelphia", "NYC"]]}}}}, {"Model Result Index 2": {"sub_error": ["Invalid value for parameter 'start_location': 'Philadelphia'. Expected one of ['New York', 'New York, NY', 'NYC']. Case insensitive."], "sub_error_type": "value_error:string", "model_output_item": {"route.estimate_time": {"start_location": "Philadelphia", "end_location": "Miami", "stops": ["Washington D.C."]}}, "possible_answer_item": {"route.estimate_time": {"start_location": ["New York", "New York, NY", "NYC"], "end_location": ["Miami"], "stops": [["Washington D.C."], ["Philadelphia", "Washington D.C."], ["Philadelphia", "Washington D.C.", "New York"], ["Philadelphia", "Washington D.C.", "NYC"], ["Washington D.C.", "Philadelphia"], ["Washington D.C.", "Philadelphia", "New York"], ["Washington D.C.", "Philadelphia", "NYC"]]}}}}]
```

### On-Policy QAD

第二条使用 end，随后受模拟成功响应影响，第三条继续使用 end。

评分指出的失败位置/原因：

```text
["Could not find a matching function among index [1, 2] of model output for index 1 of possible answers.", {"Model Result Index 1": {"sub_error": ["Missing required parameter: 'end_location'."], "sub_error_type": "simple_function_checker:missing_required", "model_output_item": {"route.estimate_time": {"start_location": "New York", "end": "Miami", "stops": ["Philadelphia", "Washington D.C."]}}, "possible_answer_item": {"route.estimate_time": {"start_location": ["New York", "New York, NY", "NYC"], "end_location": ["Miami"], "stops": [["Washington D.C."], ["Philadelphia", "Washington D.C."], ["Philadelphia", "Washington D.C.", "New York"], ["Philadelphia", "Washington D.C.", "NYC"], ["Washington D.C.", "Philadelphia"], ["Washington D.C.", "Philadelphia", "New York"], ["Washington D.C.", "Philadelphia", "NYC"]]}}}}, {"Model Result Index 2": {"sub_error": ["Missing required parameter: 'end_location'."], "sub_error_type": "simple_function_checker:missing_required", "model_output_item": {"route.estimate_time": {"start_location": "Philadelphia", "end": "Miami", "stops": ["Washington D.C."]}}, "possible_answer_item": {"route.estimate_time": {"start_location": ["New York", "New York, NY", "NYC"], "end_location": ["Miami"], "stops": [["Washington D.C."], ["Philadelphia", "Washington D.C."], ["Philadelphia", "Washington D.C.", "New York"], ["Philadelphia", "Washington D.C.", "NYC"], ["Washington D.C.", "Philadelphia"], ["Washington D.C.", "Philadelphia", "New York"], ["Washington D.C.", "Philadelphia", "NYC"]]}}}}]
```

### QeRL

第二条使用 end，第三条恢复 end_location，但没有补交第二条。

评分指出的失败位置/原因：

```text
["Could not find a matching function among index [1, 2] of model output for index 1 of possible answers.", {"Model Result Index 1": {"sub_error": ["Missing required parameter: 'end_location'."], "sub_error_type": "simple_function_checker:missing_required", "model_output_item": {"route.estimate_time": {"start_location": "New York", "end": "Miami", "stops": ["Philadelphia", "Washington D.C."]}}, "possible_answer_item": {"route.estimate_time": {"start_location": ["New York", "New York, NY", "NYC"], "end_location": ["Miami"], "stops": [["Washington D.C."], ["Philadelphia", "Washington D.C."], ["Philadelphia", "Washington D.C.", "New York"], ["Philadelphia", "Washington D.C.", "NYC"], ["Washington D.C.", "Philadelphia"], ["Washington D.C.", "Philadelphia", "New York"], ["Washington D.C.", "Philadelphia", "NYC"]]}}}}, {"Model Result Index 2": {"sub_error": ["Invalid value for parameter 'start_location': 'Philadelphia'. Expected one of ['New York', 'New York, NY', 'NYC']. Case insensitive."], "sub_error_type": "value_error:string", "model_output_item": {"route.estimate_time": {"start_location": "Philadelphia", "end_location": "Miami", "stops": ["Washington D.C."]}}, "possible_answer_item": {"route.estimate_time": {"start_location": ["New York", "New York, NY", "NYC"], "end_location": ["Miami"], "stops": [["Washington D.C."], ["Philadelphia", "Washington D.C."], ["Philadelphia", "Washington D.C.", "New York"], ["Philadelphia", "Washington D.C.", "NYC"], ["Washington D.C.", "Philadelphia"], ["Washington D.C.", "Philadelphia", "New York"], ["Washington D.C.", "Philadelphia", "NYC"]]}}}}]
```

