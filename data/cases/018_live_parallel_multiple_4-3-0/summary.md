# Case 018 — live_parallel_multiple_4-3-0

## 原始任务

第 1 轮：

Could you provide me with the latest news report for Paris, France, in English and also for Letterkenny, Ireland, focusing on technology news again in English?

完整工具定义、初始状态及其他任务字段见 task.json。

## 七种方法的实际表现

### BF16：通过

实际任务调用 2 次；[完整 CoT 和工具返回](BF16/cot_and_actions.txt)。

<details><summary>实际动作序列</summary>

```json
[
  {
    "user_turn": 1,
    "action_in_turn": 1,
    "message_index": 4,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_get_news_report",
      "arguments": {
        "location": "Paris, France",
        "category": "Technology",
        "language": "en"
      }
    }
  },
  {
    "user_turn": 1,
    "action_in_turn": 2,
    "message_index": 6,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_get_news_report",
      "arguments": {
        "location": "Letterkenny, Ireland",
        "category": "Technology",
        "language": "en"
      }
    }
  }
]
```

</details>

### Ours：通过

实际任务调用 2 次；[完整 CoT 和工具返回](Ours/cot_and_actions.txt)。

<details><summary>实际动作序列</summary>

```json
[
  {
    "user_turn": 1,
    "action_in_turn": 1,
    "message_index": 4,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_get_news_report",
      "arguments": {
        "location": "Paris, France",
        "category": "Technology",
        "language": "en"
      }
    }
  },
  {
    "user_turn": 1,
    "action_in_turn": 2,
    "message_index": 6,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_get_news_report",
      "arguments": {
        "location": "Letterkenny, Ireland",
        "category": "Technology",
        "language": "en"
      }
    }
  }
]
```

</details>

### GPTQ：未通过

实际任务调用 2 次；[完整 CoT 和工具返回](GPTQ/cot_and_actions.txt)。

<details><summary>实际动作序列</summary>

```json
[
  {
    "user_turn": 1,
    "action_in_turn": 1,
    "message_index": 4,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_get_news_report",
      "arguments": {
        "location": "Paris, FR",
        "category": "Technology",
        "language": "en"
      }
    }
  },
  {
    "user_turn": 1,
    "action_in_turn": 2,
    "message_index": 6,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_get_news_report",
      "arguments": {
        "location": "Letterkenny, IE",
        "category": "Technology",
        "language": "en"
      }
    }
  }
]
```

</details>

### EfficientQAT：未通过

实际任务调用 1 次；[完整 CoT 和工具返回](EfficientQAT/cot_and_actions.txt)。

<details><summary>实际动作序列</summary>

```json
[
  {
    "user_turn": 1,
    "action_in_turn": 1,
    "message_index": 4,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_get_news_report",
      "arguments": {
        "location": "Paris, France",
        "category": "Technology",
        "language": "en"
      }
    }
  }
]
```

</details>

### BitDistiller：未通过

实际任务调用 2 次；[完整 CoT 和工具返回](BitDistiller/cot_and_actions.txt)。

<details><summary>实际动作序列</summary>

```json
[
  {
    "user_turn": 1,
    "action_in_turn": 1,
    "message_index": 4,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_get_news_report",
      "arguments": {
        "location": "Paris, FR",
        "category": "Technology",
        "language": "en"
      }
    }
  },
  {
    "user_turn": 1,
    "action_in_turn": 2,
    "message_index": 6,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_get_news_report",
      "arguments": {
        "location": "Letterkenny, IE",
        "category": "Technology",
        "language": "en"
      }
    }
  }
]
```

</details>

### On-Policy QAD：未通过

实际任务调用 2 次；[完整 CoT 和工具返回](On-Policy%20QAD/cot_and_actions.txt)。

<details><summary>实际动作序列</summary>

```json
[
  {
    "user_turn": 1,
    "action_in_turn": 1,
    "message_index": 4,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_get_news_report",
      "arguments": {
        "location": "Paris, FR",
        "category": "Technology",
        "language": "en"
      }
    }
  },
  {
    "user_turn": 1,
    "action_in_turn": 2,
    "message_index": 6,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_get_news_report",
      "arguments": {
        "location": "Letterkenny, IE",
        "category": "Technology",
        "language": "en"
      }
    }
  }
]
```

</details>

### QeRL：未通过

实际任务调用 2 次；[完整 CoT 和工具返回](QeRL/cot_and_actions.txt)。

<details><summary>实际动作序列</summary>

```json
[
  {
    "user_turn": 1,
    "action_in_turn": 1,
    "message_index": 4,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_get_news_report",
      "arguments": {
        "location": "Paris, FR",
        "category": "Technology",
        "language": "en"
      }
    }
  },
  {
    "user_turn": 1,
    "action_in_turn": 2,
    "message_index": 6,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_get_news_report",
      "arguments": {
        "location": "Letterkenny, IE",
        "category": "Technology",
        "language": "en"
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

最早动作差异：第 1 个用户轮，第 1 个任务动作；BF16 消息 4，本方法消息 4。

```json
[
  {
    "field": "$.arguments.location",
    "reference": "Paris, France",
    "actual": "Paris, FR"
  }
]
```

### EfficientQAT

最早动作差异：第 1 个用户轮，第 2 个任务动作；BF16 消息 6，本方法消息 None。

该位置没有对应任务调用；该轮 assistant 消息为 [2, 4, 6]。

```json
[
  {
    "field": "$",
    "reference": {
      "wrapper": "call_tool",
      "name": "mcp_tool_get_news_report",
      "arguments": {
        "location": "Letterkenny, Ireland",
        "category": "Technology",
        "language": "en"
      }
    },
    "actual": null
  }
]
```

### BitDistiller

最早动作差异：第 1 个用户轮，第 1 个任务动作；BF16 消息 4，本方法消息 4。

```json
[
  {
    "field": "$.arguments.location",
    "reference": "Paris, France",
    "actual": "Paris, FR"
  }
]
```

### On-Policy QAD

最早动作差异：第 1 个用户轮，第 1 个任务动作；BF16 消息 4，本方法消息 4。

```json
[
  {
    "field": "$.arguments.location",
    "reference": "Paris, France",
    "actual": "Paris, FR"
  }
]
```

### QeRL

最早动作差异：第 1 个用户轮，第 1 个任务动作；BF16 消息 4，本方法消息 4。

```json
[
  {
    "field": "$.arguments.location",
    "reference": "Paris, France",
    "actual": "Paris, FR"
  }
]
```

## 失败原因

EfficientQAT 的调用数量不匹配；其他方法使用 Paris, FR 等地点写法，参考答案接受完整国家名称。应区分字符串匹配失败与真实查询对象错误。

### GPTQ

评分指出的失败位置/原因：

```text
["Could not find a matching function among index [0, 1] of model output for index 0 of possible answers.", {"Model Result Index 0": {"sub_error": ["Invalid value for parameter 'location': 'Paris, FR'. Expected one of ['Paris, France']. Case insensitive."], "sub_error_type": "value_error:string", "model_output_item": {"get_news_report": {"location": "Paris, FR", "category": "Technology", "language": "en"}}, "possible_answer_item": {"get_news_report": {"location": ["Paris, France"], "category": ["Technology"], "language": ["en", ""]}}}}, {"Model Result Index 1": {"sub_error": ["Invalid value for parameter 'location': 'Letterkenny, IE'. Expected one of ['Paris, France']. Case insensitive."], "sub_error_type": "value_error:string", "model_output_item": {"get_news_report": {"location": "Letterkenny, IE", "category": "Technology", "language": "en"}}, "possible_answer_item": {"get_news_report": {"location": ["Paris, France"], "category": ["Technology"], "language": ["en", ""]}}}}]
```

### EfficientQAT

评分指出的失败位置/原因：

```text
["Wrong number of functions."]
```

### BitDistiller

评分指出的失败位置/原因：

```text
["Could not find a matching function among index [0, 1] of model output for index 0 of possible answers.", {"Model Result Index 0": {"sub_error": ["Invalid value for parameter 'location': 'Paris, FR'. Expected one of ['Paris, France']. Case insensitive."], "sub_error_type": "value_error:string", "model_output_item": {"get_news_report": {"location": "Paris, FR", "category": "Technology", "language": "en"}}, "possible_answer_item": {"get_news_report": {"location": ["Paris, France"], "category": ["Technology"], "language": ["en", ""]}}}}, {"Model Result Index 1": {"sub_error": ["Invalid value for parameter 'location': 'Letterkenny, IE'. Expected one of ['Paris, France']. Case insensitive."], "sub_error_type": "value_error:string", "model_output_item": {"get_news_report": {"location": "Letterkenny, IE", "category": "Technology", "language": "en"}}, "possible_answer_item": {"get_news_report": {"location": ["Paris, France"], "category": ["Technology"], "language": ["en", ""]}}}}]
```

### On-Policy QAD

评分指出的失败位置/原因：

```text
["Could not find a matching function among index [0, 1] of model output for index 0 of possible answers.", {"Model Result Index 0": {"sub_error": ["Invalid value for parameter 'location': 'Paris, FR'. Expected one of ['Paris, France']. Case insensitive."], "sub_error_type": "value_error:string", "model_output_item": {"get_news_report": {"location": "Paris, FR", "category": "Technology", "language": "en"}}, "possible_answer_item": {"get_news_report": {"location": ["Paris, France"], "category": ["Technology"], "language": ["en", ""]}}}}, {"Model Result Index 1": {"sub_error": ["Invalid value for parameter 'location': 'Letterkenny, IE'. Expected one of ['Paris, France']. Case insensitive."], "sub_error_type": "value_error:string", "model_output_item": {"get_news_report": {"location": "Letterkenny, IE", "category": "Technology", "language": "en"}}, "possible_answer_item": {"get_news_report": {"location": ["Paris, France"], "category": ["Technology"], "language": ["en", ""]}}}}]
```

### QeRL

评分指出的失败位置/原因：

```text
["Could not find a matching function among index [0, 1] of model output for index 0 of possible answers.", {"Model Result Index 0": {"sub_error": ["Invalid value for parameter 'location': 'Paris, FR'. Expected one of ['Paris, France']. Case insensitive."], "sub_error_type": "value_error:string", "model_output_item": {"get_news_report": {"location": "Paris, FR", "category": "Technology", "language": "en"}}, "possible_answer_item": {"get_news_report": {"location": ["Paris, France"], "category": ["Technology"], "language": ["en", ""]}}}}, {"Model Result Index 1": {"sub_error": ["Invalid value for parameter 'location': 'Letterkenny, IE'. Expected one of ['Paris, France']. Case insensitive."], "sub_error_type": "value_error:string", "model_output_item": {"get_news_report": {"location": "Letterkenny, IE", "category": "Technology", "language": "en"}}, "possible_answer_item": {"get_news_report": {"location": ["Paris, France"], "category": ["Technology"], "language": ["en", ""]}}}}]
```

