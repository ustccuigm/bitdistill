# Case 034 — parallel_191

## 任务

第 1 轮：

Can you help me find public libraries in New York, NY that have a Reading Room and Fiction section, and then in Los Angeles, CA that offer Wi-Fi and have a Children Section, and finally in Chicago, IL that have a Cafe and a Reading Room?

完整工具定义、初始状态及其他任务字段见 task.json。

## 七种方法的实际表现

### BF16：通过

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
      "name": "mcp_tool_public_library.find_nearby",
      "arguments": {
        "location": "New York, NY",
        "facilities": [
          "Reading Room",
          "Fiction"
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
      "name": "mcp_tool_public_library.find_nearby",
      "arguments": {
        "location": "Los Angeles, CA",
        "facilities": [
          "Wi-Fi",
          "Children Section"
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
      "name": "mcp_tool_public_library.find_nearby",
      "arguments": {
        "location": "Chicago, IL",
        "facilities": [
          "Cafe",
          "Reading Room"
        ]
      }
    }
  }
]
```

</details>

### Ours：通过

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
      "name": "mcp_tool_public_library.find_nearby",
      "arguments": {
        "location": "New York, NY",
        "facilities": [
          "Reading Room",
          "Fiction"
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
      "name": "mcp_tool_public_library.find_nearby",
      "arguments": {
        "location": "Los Angeles, CA",
        "facilities": [
          "Wi-Fi",
          "Children Section"
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
      "name": "mcp_tool_public_library.find_nearby",
      "arguments": {
        "location": "Chicago, IL",
        "facilities": [
          "Cafe",
          "Reading Room"
        ]
      }
    }
  }
]
```

</details>

### GPTQ：未通过

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
      "name": "mcp_tool_public_library.find_nearby",
      "arguments": {
        "location": "New York, NY",
        "facilities": [
          "Reading Room",
          "Fiction"
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
      "name": "mcp_tool_public_library.find_nearby",
      "arguments": {
        "location": "Los Angeles, CA",
        "facilities": [
          "Wi-Fi",
          "Children Section"
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
      "name": "mikipedia_tool_public_library.find_nearby",
      "arguments": {
        "location": "Chicago, IL",
        "facilities": [
          "Cafe",
          "Reading Room"
        ]
      }
    }
  }
]
```

</details>

### EfficientQAT：未通过

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
      "name": "mcp_tool_public_library.find_nearby",
      "arguments": {
        "location": "New York, NY",
        "facilities": [
          "Reading Room",
          "Fiction section"
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
      "name": "mcp_tool_public_library.find_nearby",
      "arguments": {
        "location": "Los Angeles, CA",
        "facilities": [
          "Wi-Fi",
          "Children Section"
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
      "name": "mcp_tool_public_library.find_nearby",
      "arguments": {
        "location": "Chicago, IL",
        "facilities": [
          "Cafe",
          "Reading Room"
        ]
      }
    }
  }
]
```

</details>

### BitDistiller：未通过

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
      "name": "mcp_tool_public_library.find_nearby",
      "arguments": {
        "location": "New York, NY",
        "facilities": [
          "Reading Room",
          "Fiction"
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
      "name": "mcp_tool_public_library.find_nearby",
      "arguments": {
        "location": "Los Angeles, CA",
        "facilities": [
          "Wi-Fi",
          "Children Section"
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
      "name": "m_c_p_tool_public_library.find_nearby",
      "arguments": {
        "location": "Chicago, IL",
        "facilities": [
          "Cafe",
          "Reading Room"
        ]
      }
    }
  }
]
```

</details>

### On-Policy QAD：未通过

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
      "name": "mcp_tool_public_library.find_nearby",
      "arguments": {
        "location": "New York, NY",
        "facilities": [
          "Reading Room",
          "Fiction"
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
      "name": "mcp_tool_public_library.find_nearby",
      "arguments": {
        "location": "Los Angeles, CA",
        "facilities": [
          "Wi-Fi",
          "Children Section"
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
      "name": "mcp_tool_public_library.find_nearby",
      "arguments": {
        "location": "Chicago, IL",
        "facilities": [
          "Cafe",
          "Reading"
        ]
      }
    }
  }
]
```

</details>

### QeRL：未通过

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
      "name": "mcp_tool_public_library.find_nearby",
      "arguments": {
        "location": "New York, NY",
        "facilities": [
          "Reading Room",
          "Fiction"
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
      "name": "mcp_tool_public_library.find_nearby",
      "arguments": {
        "location": "Los Angeles, CA",
        "facilities": [
          "Wi-Fi",
          "Children Section"
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
      "name": "mcp_tool_public_library.find_nearby",
      "arguments": "{\"location\": \"Chicago, IL\", \"facilities\": [\"Cafe\", \"Reading\nRoom\"]}"
    }
  }
]
```

</details>

## 分歧位置

消息编号从 0 开始，用户轮和动作编号从 1 开始。按同一用户轮的任务动作序号与 BF16 比较，忽略 list_tools。最早动作差异不一定就是失败起点：正确的工具顺序、补救步骤也可能不同；评分失败位置另见下一节。

- Ours：按用户轮和动作序号比较，任务动作序列与 BF16 相同。

### GPTQ

最早动作差异：第 1 个用户轮，第 3 个任务动作；BF16 消息 8，本方法消息 8。

```json
[
  {
    "field": "$.name",
    "reference": "mcp_tool_public_library.find_nearby",
    "actual": "mikipedia_tool_public_library.find_nearby"
  }
]
```

### EfficientQAT

最早动作差异：第 1 个用户轮，第 1 个任务动作；BF16 消息 4，本方法消息 4。

```json
[
  {
    "field": "$.arguments.facilities[1]",
    "reference": "Fiction",
    "actual": "Fiction section"
  }
]
```

### BitDistiller

最早动作差异：第 1 个用户轮，第 3 个任务动作；BF16 消息 8，本方法消息 8。

```json
[
  {
    "field": "$.name",
    "reference": "mcp_tool_public_library.find_nearby",
    "actual": "m_c_p_tool_public_library.find_nearby"
  }
]
```

### On-Policy QAD

最早动作差异：第 1 个用户轮，第 3 个任务动作；BF16 消息 8，本方法消息 8。

```json
[
  {
    "field": "$.arguments.facilities[1]",
    "reference": "Reading Room",
    "actual": "Reading"
  }
]
```

### QeRL

最早动作差异：第 1 个用户轮，第 3 个任务动作；BF16 消息 8，本方法消息 8。

```json
[
  {
    "field": "$.arguments",
    "reference": {
      "location": "Chicago, IL",
      "facilities": [
        "Cafe",
        "Reading Room"
      ]
    },
    "actual": "{\"location\": \"Chicago, IL\", \"facilities\": [\"Cafe\", \"Reading\nRoom\"]}"
  }
]
```

## 失败原因

后续相似调用出现工具名或 facilities 字段漂移；其中换行、Fiction section 等匹配差异不应一概解释成真实设施查询错误。

### GPTQ

评分指出的失败位置/原因：

```text
["Could not find a matching function among index [2] of model output for index 2 of possible answers.", {"Model Result Index 2": {"sub_error": ["Function name 'public_library.find_nearby' not found in model output."], "sub_error_type": "simple_function_checker:wrong_func_name", "model_output_item": {"mikipedia_tool_public_library.find_nearby": {"location": "Chicago, IL", "facilities": ["Cafe", "Reading Room"]}}, "possible_answer_item": {"public_library.find_nearby": {"location": ["Chicago, IL", "Chi"], "facilities": [["Cafe", "Reading Room"]]}}}}]
```

### EfficientQAT

评分指出的失败位置/原因：

```text
["Could not find a matching function among index [0, 1, 2] of model output for index 0 of possible answers.", {"Model Result Index 0": {"sub_error": ["Invalid value for parameter 'facilities': ['Reading Room', 'Fiction section']. Expected one of [['Reading Room', 'Fiction']]."], "sub_error_type": "value_error:list/tuple", "model_output_item": {"public_library.find_nearby": {"location": "New York, NY", "facilities": ["Reading Room", "Fiction section"]}}, "possible_answer_item": {"public_library.find_nearby": {"location": ["New York, NY", "NY"], "facilities": [["Reading Room", "Fiction"]]}}}}, {"Model Result Index 1": {"sub_error": ["Invalid value for parameter 'location': 'Los Angeles, CA'. Expected one of ['New York, NY', 'NY']. Case insensitive."], "sub_error_type": "value_error:string", "model_output_item": {"public_library.find_nearby": {"location": "Los Angeles, CA", "facilities": ["Wi-Fi", "Children Section"]}}, "possible_answer_item": {"public_library.find_nearby": {"location": ["New York, NY", "NY"], "facilities": [["Reading Room", "Fiction"]]}}}}, {"Model Result Index 2": {"sub_error": ["Invalid value for parameter 'location': 'Chicago, IL'. Expected one of ['New York, NY', 'NY']. Case insensitive."], "sub_error_type": "value_error:string", "model_output_item": {"public_library.find_nearby": {"location": "Chicago, IL", "facilities": ["Cafe", "Reading Room"]}}, "possible_answer_item": {"public_library.find_nearby": {"location": ["New York, NY", "NY"], "facilities": [["Reading Room", "Fiction"]]}}}}]
```

### BitDistiller

评分指出的失败位置/原因：

```text
["Could not find a matching function among index [2] of model output for index 2 of possible answers.", {"Model Result Index 2": {"sub_error": ["Function name 'public_library.find_nearby' not found in model output."], "sub_error_type": "simple_function_checker:wrong_func_name", "model_output_item": {"m_c_p_tool_public_library.find_nearby": {"location": "Chicago, IL", "facilities": ["Cafe", "Reading Room"]}}, "possible_answer_item": {"public_library.find_nearby": {"location": ["Chicago, IL", "Chi"], "facilities": [["Cafe", "Reading Room"]]}}}}]
```

### On-Policy QAD

评分指出的失败位置/原因：

```text
["Could not find a matching function among index [2] of model output for index 2 of possible answers.", {"Model Result Index 2": {"sub_error": ["Invalid value for parameter 'facilities': ['Cafe', 'Reading']. Expected one of [['Cafe', 'Reading Room']]."], "sub_error_type": "value_error:list/tuple", "model_output_item": {"public_library.find_nearby": {"location": "Chicago, IL", "facilities": ["Cafe", "Reading"]}}, "possible_answer_item": {"public_library.find_nearby": {"location": ["Chicago, IL", "Chi"], "facilities": [["Cafe", "Reading Room"]]}}}}]
```

### QeRL

评分指出的失败位置/原因：

```text
["Could not find a matching function among index [2] of model output for index 2 of possible answers.", {"Model Result Index 2": {"sub_error": ["Invalid value for parameter 'facilities': ['Cafe', 'Reading\\nRoom']. Expected one of [['Cafe', 'Reading Room']]."], "sub_error_type": "value_error:list/tuple", "model_output_item": {"public_library.find_nearby": {"location": "Chicago, IL", "facilities": ["Cafe", "Reading\nRoom"]}}, "possible_answer_item": {"public_library.find_nearby": {"location": ["Chicago, IL", "Chi"], "facilities": [["Cafe", "Reading Room"]]}}}}]
```
