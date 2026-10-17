# Case 017 — live_multiple_853-180-1

## 原始任务

第 1 轮：

Can you help me purchase two bus tickets from San Francisco to Los Angeles for the 7th of March? I would like the departure time to be around 14:00.

完整工具定义、初始状态及其他任务字段见 task.json。

## 七种方法的实际表现

### BF16：通过

实际任务调用 1 次；[完整 CoT 和工具返回](BF16/cot_and_actions.txt)。

<details><summary>实际动作序列</summary>

```json
[
  {
    "user_turn": 1,
    "action_in_turn": 1,
    "message_index": 4,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_Buses_3_BuyBusTicket",
      "arguments": {
        "from_city": "San Francisco, CA",
        "to_city": "Los Angeles, CA",
        "departure_date": "2023-03-07",
        "departure_time": "14:00",
        "num_passengers": 2
      }
    }
  }
]
```

</details>

### Ours：通过

实际任务调用 1 次；[完整 CoT 和工具返回](Ours/cot_and_actions.txt)。

<details><summary>实际动作序列</summary>

```json
[
  {
    "user_turn": 1,
    "action_in_turn": 1,
    "message_index": 4,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_Buses_3_BuyBusTicket",
      "arguments": {
        "from_city": "San Francisco, CA",
        "to_city": "Los Angeles, CA",
        "departure_date": "2023-03-07",
        "departure_time": "14:00",
        "num_passengers": 2
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
      "name": "mcp_tool_Buses_3_FindBus",
      "arguments": {
        "from_city": "San Francisco, CA",
        "to_city": "Los Angeles, CA",
        "departure_date": "03/07/2023",
        "num_passengers": 2
      }
    }
  },
  {
    "user_turn": 1,
    "action_in_turn": 2,
    "message_index": 6,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_Buses_3_BuyBusTicket",
      "arguments": {
        "from_city": "San Francisco, CA",
        "to_city": "Los Angeles, CA",
        "departure_date": "2023-03-07",
        "departure_time": "14:00",
        "num_passengers": 2
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
      "name": "mcp_tool_Buses_3_BuyBusTicket",
      "arguments": {
        "from_city": "San Francisco, CA",
        "to_city": "Los Angeles, CA",
        "departure_date": "2024-03-07",
        "departure_time": "14:00",
        "num_passengers": 2
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
      "name": "mcp_tool_Buses_3_FindBus",
      "arguments": {
        "from_city": "San Francisco, CA",
        "to_city": "Los Angeles, CA",
        "departure_date": "03/07/2023",
        "num_passengers": 2
      }
    }
  },
  {
    "user_turn": 1,
    "action_in_turn": 2,
    "message_index": 6,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_Buses_3_BuyBusTicket",
      "arguments": {
        "from_city": "San Francisco, CA",
        "to_city": "Los Angeles, CA",
        "departure_date": "2023-03-07",
        "departure_time": "14:00",
        "num_passengers": 2
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
      "name": "mcp_tool_Buses_3_FindBus",
      "arguments": {
        "from_city": "San Francisco, CA",
        "to_city": "Los Angeles, CA",
        "departure_date": "03/07/2023",
        "num_passengers": 2
      }
    }
  },
  {
    "user_turn": 1,
    "action_in_turn": 2,
    "message_index": 6,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_Buses_3_BuyBusTicket",
      "arguments": {
        "from_city": "San Francisco, CA",
        "to_city": "Los Angeles, CA",
        "departure_date": "2023-03-07",
        "departure_time": "14:00",
        "num_passengers": 2
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
      "name": "mcp_tool_Buses_3_FindBus",
      "arguments": {
        "from_city": "San Francisco, CA",
        "to_city": "Los Angeles, CA",
        "departure_date": "03/07/2024",
        "num_passengers": 2
      }
    }
  },
  {
    "user_turn": 1,
    "action_in_turn": 2,
    "message_index": 6,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_Buses_3_BuyBusTicket",
      "arguments": {
        "from_city": "San Francisco, CA",
        "to_city": "Los Angeles, CA",
        "departure_date": "2024-03-07",
        "departure_time": "14:30",
        "num_passengers": 2
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
    "field": "$.arguments.departure_date",
    "reference": "2023-03-07",
    "actual": "03/07/2023"
  },
  {
    "field": "$.arguments.departure_time",
    "reference": "14:00",
    "actual": null,
    "reference_present": true,
    "actual_present": false
  },
  {
    "field": "$.name",
    "reference": "mcp_tool_Buses_3_BuyBusTicket",
    "actual": "mcp_tool_Buses_3_FindBus"
  }
]
```

### EfficientQAT

最早动作差异：第 1 个用户轮，第 1 个任务动作；BF16 消息 4，本方法消息 4。

```json
[
  {
    "field": "$.arguments.departure_date",
    "reference": "2023-03-07",
    "actual": "2024-03-07"
  }
]
```

### BitDistiller

最早动作差异：第 1 个用户轮，第 1 个任务动作；BF16 消息 4，本方法消息 4。

```json
[
  {
    "field": "$.arguments.departure_date",
    "reference": "2023-03-07",
    "actual": "03/07/2023"
  },
  {
    "field": "$.arguments.departure_time",
    "reference": "14:00",
    "actual": null,
    "reference_present": true,
    "actual_present": false
  },
  {
    "field": "$.name",
    "reference": "mcp_tool_Buses_3_BuyBusTicket",
    "actual": "mcp_tool_Buses_3_FindBus"
  }
]
```

### On-Policy QAD

最早动作差异：第 1 个用户轮，第 1 个任务动作；BF16 消息 4，本方法消息 4。

```json
[
  {
    "field": "$.arguments.departure_date",
    "reference": "2023-03-07",
    "actual": "03/07/2023"
  },
  {
    "field": "$.arguments.departure_time",
    "reference": "14:00",
    "actual": null,
    "reference_present": true,
    "actual_present": false
  },
  {
    "field": "$.name",
    "reference": "mcp_tool_Buses_3_BuyBusTicket",
    "actual": "mcp_tool_Buses_3_FindBus"
  }
]
```

### QeRL

最早动作差异：第 1 个用户轮，第 1 个任务动作；BF16 消息 4，本方法消息 4。

```json
[
  {
    "field": "$.arguments.departure_date",
    "reference": "2023-03-07",
    "actual": "03/07/2024"
  },
  {
    "field": "$.arguments.departure_time",
    "reference": "14:00",
    "actual": null,
    "reference_present": true,
    "actual_present": false
  },
  {
    "field": "$.name",
    "reference": "mcp_tool_Buses_3_BuyBusTicket",
    "actual": "mcp_tool_Buses_3_FindBus"
  }
]
```

## 失败原因

四种方法的调用数量不匹配；EfficientQAT 使用 2024-03-07，而参考答案为 2023-03-07。原问题没有给出年份，因此年份差异本身不能证明理解错误。

### GPTQ

评分指出的失败位置/原因：

```text
["Wrong number of functions."]
```

### EfficientQAT

评分指出的失败位置/原因：

```text
["Invalid value for parameter 'departure_date': '2024-03-07'. Expected one of ['2023-03-07']. Case insensitive."]
```

### BitDistiller

评分指出的失败位置/原因：

```text
["Wrong number of functions."]
```

### On-Policy QAD

评分指出的失败位置/原因：

```text
["Wrong number of functions."]
```

### QeRL

评分指出的失败位置/原因：

```text
["Wrong number of functions."]
```

