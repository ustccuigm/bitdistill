# Case 036 — parallel_multiple_144

## 任务

第 1 轮：

"Can you tell me the name of the scientist who is credited for the discovery of the theory of relativity? Also, I would like to know the predicted forest growth in Amazon rainforest over the next 10 years, considering the impact of human activities. After that, could you also provide the forecast for the same location but this time without considering human impact? Lastly, I'm curious about the scientist who discovered the DNA double helix structure."

完整工具定义、初始状态及其他任务字段见 task.json。

## 七种方法的实际表现

### BF16：通过

四个子任务均有对应的正确工具调用。

实际任务调用 4 次；[完整 CoT 和工具返回](BF16/cot_and_actions.txt)。

<details><summary>实际动作序列</summary>

```json
[
  {
    "user_turn": 1,
    "action_in_turn": 1,
    "message_index": 4,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_get_scientist_for_discovery",
      "arguments": {
        "discovery": "theory of relativity"
      }
    }
  },
  {
    "user_turn": 1,
    "action_in_turn": 2,
    "message_index": 6,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_forest_growth_forecast",
      "arguments": {
        "location": "Amazon rainforest",
        "years": 10,
        "include_human_impact": true
      }
    }
  },
  {
    "user_turn": 1,
    "action_in_turn": 3,
    "message_index": 8,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_forest_growth_forecast",
      "arguments": {
        "location": "Amazon rainforest",
        "years": 10,
        "include_human_impact": false
      }
    }
  },
  {
    "user_turn": 1,
    "action_in_turn": 4,
    "message_index": 10,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_get_scientist_for_discovery",
      "arguments": {
        "discovery": "DNA double helix structure"
      }
    }
  }
]
```

</details>

### Ours：通过

完成两种森林预测；DNA 查询的外层工具名写错后，根据错误反馈修正，完成全部任务。

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
      "name": "mcp_tool_get_scientist_for_discovery",
      "arguments": {
        "discovery": "theory of relativity"
      }
    }
  },
  {
    "user_turn": 1,
    "action_in_turn": 2,
    "message_index": 6,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_forest_growth_forecast",
      "arguments": {
        "location": "Amazon rainforest",
        "years": 10,
        "include_human_impact": true
      }
    }
  },
  {
    "user_turn": 1,
    "action_in_turn": 3,
    "message_index": 8,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_forest_growth_forecast",
      "arguments": {
        "location": "Amazon rainforest",
        "years": 10,
        "include_human_impact": false
      }
    }
  },
  {
    "user_turn": 1,
    "action_in_turn": 4,
    "message_index": 10,
    "action": {
      "wrapper": "call/Tool",
      "name": "mcp_tool_get_scientist_for_discovery",
      "arguments": {
        "discovery": "DNA double helix structure"
      }
    }
  },
  {
    "user_turn": 1,
    "action_in_turn": 5,
    "message_index": 12,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_get_scientist_for_discovery",
      "arguments": {
        "discovery": "DNA double helix structure"
      }
    }
  }
]
```

</details>

### GPTQ：未通过

第一项查询后，只在文字中宣称将执行剩余三项，没有生成相应工具调用。

实际任务调用 1 次；[完整 CoT 和工具返回](GPTQ/cot_and_actions.txt)。

<details><summary>实际动作序列</summary>

```json
[
  {
    "user_turn": 1,
    "action_in_turn": 1,
    "message_index": 4,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_get_scientist_for_discovery",
      "arguments": {
        "discovery": "theory of relativity"
      }
    }
  }
]
```

</details>

### EfficientQAT：未通过

CoT 明确四项任务，实际只执行相对论科学家查询。

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
      "name": "mcp_tool_get_scientist_for_discovery",
      "arguments": {
        "discovery": "theory of relativity"
      }
    }
  }
]
```

</details>

### BitDistiller：未通过

推理列清两个森林预测及 DNA 查询，实际仅完成首项。

实际任务调用 1 次；[完整 CoT 和工具返回](BitDistiller/cot_and_actions.txt)。

<details><summary>实际动作序列</summary>

```json
[
  {
    "user_turn": 1,
    "action_in_turn": 1,
    "message_index": 4,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_get_scientist_for_discovery",
      "arguments": {
        "discovery": "theory of relativity"
      }
    }
  }
]
```

</details>

### On-Policy QAD：未通过

后续重复 DNA 查询，并生成不相关的 get_weather 请求，调用集合多出错误项。

实际任务调用 7 次；[完整 CoT 和工具返回](On-Policy%20QAD/cot_and_actions.txt)。

<details><summary>实际动作序列</summary>

```json
[
  {
    "user_turn": 1,
    "action_in_turn": 1,
    "message_index": 4,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_get_scientist_for_discovery",
      "arguments": {
        "discovery": "theory of relativity"
      }
    }
  },
  {
    "user_turn": 1,
    "action_in_turn": 2,
    "message_index": 6,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_forest_growth_forecast",
      "arguments": {
        "location": "Amazon rainforest",
        "years": 10,
        "include_human_impact": true
      }
    }
  },
  {
    "user_turn": 1,
    "action_in_turn": 3,
    "message_index": 8,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_forest_growth_forecast",
      "arguments": {
        "location": "Amazon rainforest",
        "years": 10,
        "include_human_impact": false
      }
    }
  },
  {
    "user_turn": 1,
    "action_in_turn": 4,
    "message_index": 10,
    "action": {
      "wrapper": "call/Tool",
      "name": "mcp_tool_get_scientist_for_discovery",
      "arguments": {
        "discovery": "DNA double helix structure"
      }
    }
  },
  {
    "user_turn": 1,
    "action_in_turn": 5,
    "message_index": 12,
    "action": {
      "wrapper": "call/Tool",
      "name": "mcp_tool_get_scientist_for_discovery",
      "arguments": {
        "discovery": "DNA double helix structure"
      }
    }
  },
  {
    "user_turn": 1,
    "action_in_turn": 6,
    "message_index": 14,
    "action": {
      "wrapper": "call_tool",
      "name": "get_weather",
      "arguments": "..."
    }
  },
  {
    "user_turn": 1,
    "action_in_turn": 7,
    "message_index": 16,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_get_scientist_for_discovery",
      "arguments": {
        "discovery": "DNA double helix structure"
      }
    }
  }
]
```

</details>

### QeRL：未通过

只执行第一项，剩余任务停留在计划中。

实际任务调用 1 次；[完整 CoT 和工具返回](QeRL/cot_and_actions.txt)。

<details><summary>实际动作序列</summary>

```json
[
  {
    "user_turn": 1,
    "action_in_turn": 1,
    "message_index": 4,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_get_scientist_for_discovery",
      "arguments": {
        "discovery": "theory of relativity"
      }
    }
  }
]
```

</details>

## 分歧位置

消息编号从 0 开始，用户轮和动作编号从 1 开始。按同一用户轮的任务动作序号与 BF16 比较，忽略 list_tools。最早动作差异不一定就是失败起点：正确的工具顺序、补救步骤也可能不同；评分失败位置另见下一节。

### Ours

最早动作差异：第 1 个用户轮，第 4 个任务动作；BF16 消息 10，本方法消息 10。

```json
[
  {
    "field": "$.wrapper",
    "reference": "call_tool",
    "actual": "call/Tool"
  }
]
```

### GPTQ

最早动作差异：第 1 个用户轮，第 2 个任务动作；BF16 消息 6，本方法消息 None。

该位置没有对应任务调用；该轮 assistant 消息为 [2, 4, 6]。

```json
[
  {
    "field": "$",
    "reference": {
      "wrapper": "call_tool",
      "name": "mcp_tool_forest_growth_forecast",
      "arguments": {
        "location": "Amazon rainforest",
        "years": 10,
        "include_human_impact": true
      }
    },
    "actual": null
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
      "name": "mcp_tool_forest_growth_forecast",
      "arguments": {
        "location": "Amazon rainforest",
        "years": 10,
        "include_human_impact": true
      }
    },
    "actual": null
  }
]
```

### BitDistiller

最早动作差异：第 1 个用户轮，第 2 个任务动作；BF16 消息 6，本方法消息 None。

该位置没有对应任务调用；该轮 assistant 消息为 [2, 4, 6]。

```json
[
  {
    "field": "$",
    "reference": {
      "wrapper": "call_tool",
      "name": "mcp_tool_forest_growth_forecast",
      "arguments": {
        "location": "Amazon rainforest",
        "years": 10,
        "include_human_impact": true
      }
    },
    "actual": null
  }
]
```

### On-Policy QAD

最早动作差异：第 1 个用户轮，第 4 个任务动作；BF16 消息 10，本方法消息 10。

```json
[
  {
    "field": "$.wrapper",
    "reference": "call_tool",
    "actual": "call/Tool"
  }
]
```

### QeRL

最早动作差异：第 1 个用户轮，第 2 个任务动作；BF16 消息 6，本方法消息 None。

该位置没有对应任务调用；该轮 assistant 消息为 [2, 4, 6]。

```json
[
  {
    "field": "$",
    "reference": {
      "wrapper": "call_tool",
      "name": "mcp_tool_forest_growth_forecast",
      "arguments": {
        "location": "Amazon rainforest",
        "years": 10,
        "include_human_impact": true
      }
    },
    "actual": null
  }
]
```

## 失败原因

四个子任务及对应参数在各方法的初始推理中基本已经明确。GPTQ、EfficientQAT、BitDistiller 和 QeRL 的所选轨迹只执行了第一个科学家查询，之后用自然语言描述还要调用哪些工具，没有实际完成剩余调用。On-Policy QAD 虽然执行了所需查询，却在后面重复查询 DNA、调用无关的 get_weather，并进入对错误工具文本的重复纠正，导致调用集合错误。BF16 完成四项查询；Ours 在最后一项曾把外层 call_tool 写成 call/Tool，收到错误后改正，最终完成四项。这里体现的是计划到执行之间的断裂以及出错后的恢复差异，不能把我们的轨迹描述成从未出错，也不能把模拟工具响应当作真实科学数据。

### GPTQ

第一项查询后，只在文字中宣称将执行剩余三项，没有生成相应工具调用。

评分指出的失败位置/原因：

```text
["Wrong number of functions."]
```

### EfficientQAT

CoT 明确四项任务，实际只执行相对论科学家查询。

评分指出的失败位置/原因：

```text
["Wrong number of functions."]
```

### BitDistiller

推理列清两个森林预测及 DNA 查询，实际仅完成首项。

评分指出的失败位置/原因：

```text
["Wrong number of functions."]
```

### On-Policy QAD

后续重复 DNA 查询，并生成不相关的 get_weather 请求，调用集合多出错误项。

评分指出的失败位置/原因：

```text
["Wrong number of functions."]
```

### QeRL

只执行第一项，剩余任务停留在计划中。

评分指出的失败位置/原因：

```text
["Wrong number of functions."]
```
