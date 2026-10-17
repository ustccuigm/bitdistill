# Case 008 — live_irrelevance_620-196-1

## 原始任务

第 1 轮：

Could you help me search for a roundtrip flight with three tickets? The return date is March 8th 2023, and I'm flexible with the departure date and other details.

完整工具定义、初始状态及其他任务字段见 task.json。

## 七种方法的实际表现

### BF16：通过

询问缺失行程信息。

实际任务调用 0 次；[完整 CoT 和工具返回](BF16/cot_and_actions.txt)。

<details><summary>实际动作序列</summary>

```json
[]
```

</details>

### Ours：通过

保留澄清分支，没有强行查票。

实际任务调用 0 次；[完整 CoT 和工具返回](Ours/cot_and_actions.txt)。

<details><summary>实际动作序列</summary>

```json
[]
```

</details>

### GPTQ：未通过

推理要求澄清，实际只传返程日期和人数。

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
      "name": "mcp_tool_Flights_4_SearchRoundtripFlights",
      "arguments": {
        "return_date": "2023-03-08",
        "number_of_tickets": 3
      }
    }
  }
]
```

</details>

### EfficientQAT：未通过

编造 NYC 到 SFO 的航线以及 2023-03-01 去程日期。

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
      "name": "mcp_tool_Flights_4_SearchRoundtripFlights",
      "arguments": {
        "origin_airport": "NYC",
        "destination_airport": "SFO",
        "departure_date": "2023-03-01",
        "return_date": "2023-03-08",
        "number_of_tickets": 3
      }
    }
  }
]
```

</details>

### BitDistiller：未通过

把可灵活安排扩展成省略机场，只传日期、人数和航空公司偏好。

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
      "name": "mcp_tool_Flights_4_SearchRoundtripFlights",
      "arguments": {
        "return_date": "2023-03-08",
        "number_of_tickets": 3,
        "airlines": "dontcare"
      }
    }
  }
]
```

</details>

### On-Policy QAD：未通过

识别缺少机场后仍发起查询。

实际任务调用 1 次；[完整 CoT 和工具返回](On-Policy%20QAD/cot_and_actions.txt)。

<details><summary>实际动作序列</summary>

```json
[
  {
    "user_turn": 1,
    "action_in_turn": 1,
    "message_index": 4,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_Flights_4_SearchRoundtripFlights",
      "arguments": {
        "return_date": "2023-03-08",
        "number_of_tickets": 3
      }
    }
  }
]
```

</details>

### QeRL：未通过

关注日期和人数，实际调用没有机场。

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
      "name": "mcp_tool_Flights_4_SearchRoundtripFlights",
      "arguments": {
        "return_date": "2023-03-08",
        "number_of_tickets": 3
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

最早动作差异：第 1 个用户轮，第 1 个任务动作；BF16 消息 None，本方法消息 4。

```json
[
  {
    "field": "$",
    "reference": null,
    "actual": {
      "wrapper": "call_tool",
      "name": "mcp_tool_Flights_4_SearchRoundtripFlights",
      "arguments": {
        "return_date": "2023-03-08",
        "number_of_tickets": 3
      }
    }
  }
]
```

### EfficientQAT

最早动作差异：第 1 个用户轮，第 1 个任务动作；BF16 消息 None，本方法消息 4。

```json
[
  {
    "field": "$",
    "reference": null,
    "actual": {
      "wrapper": "call_tool",
      "name": "mcp_tool_Flights_4_SearchRoundtripFlights",
      "arguments": {
        "origin_airport": "NYC",
        "destination_airport": "SFO",
        "departure_date": "2023-03-01",
        "return_date": "2023-03-08",
        "number_of_tickets": 3
      }
    }
  }
]
```

### BitDistiller

最早动作差异：第 1 个用户轮，第 1 个任务动作；BF16 消息 None，本方法消息 4。

```json
[
  {
    "field": "$",
    "reference": null,
    "actual": {
      "wrapper": "call_tool",
      "name": "mcp_tool_Flights_4_SearchRoundtripFlights",
      "arguments": {
        "return_date": "2023-03-08",
        "number_of_tickets": 3,
        "airlines": "dontcare"
      }
    }
  }
]
```

### On-Policy QAD

最早动作差异：第 1 个用户轮，第 1 个任务动作；BF16 消息 None，本方法消息 4。

```json
[
  {
    "field": "$",
    "reference": null,
    "actual": {
      "wrapper": "call_tool",
      "name": "mcp_tool_Flights_4_SearchRoundtripFlights",
      "arguments": {
        "return_date": "2023-03-08",
        "number_of_tickets": 3
      }
    }
  }
]
```

### QeRL

最早动作差异：第 1 个用户轮，第 1 个任务动作；BF16 消息 None，本方法消息 4。

```json
[
  {
    "field": "$",
    "reference": null,
    "actual": {
      "wrapper": "call_tool",
      "name": "mcp_tool_Flights_4_SearchRoundtripFlights",
      "arguments": {
        "return_date": "2023-03-08",
        "number_of_tickets": 3
      }
    }
  }
]
```

## 失败原因

关键不是去程日期能否灵活，而是航线的起终点缺失。GPTQ、BitDistiller、On-Policy QAD 和 QeRL 仍用返程日期及人数调用查询，省略必填机场；EfficientQAT 则自行编造 NYC 到 SFO 以及去程日期。GPTQ 和 On-Policy QAD 的 CoT 已经说应询问机场，动作仍进入查询分支。BF16 和 Ours 先澄清，不发起缺少航线的调用。

### GPTQ

推理要求澄清，实际只传返程日期和人数。

评分指出的失败位置/原因：

```text
["Valid syntax. Successfully decode AST when it should not."]
```

### EfficientQAT

编造 NYC 到 SFO 的航线以及 2023-03-01 去程日期。

评分指出的失败位置/原因：

```text
["Valid syntax. Successfully decode AST when it should not."]
```

### BitDistiller

把可灵活安排扩展成省略机场，只传日期、人数和航空公司偏好。

评分指出的失败位置/原因：

```text
["Valid syntax. Successfully decode AST when it should not."]
```

### On-Policy QAD

识别缺少机场后仍发起查询。

评分指出的失败位置/原因：

```text
["Valid syntax. Successfully decode AST when it should not."]
```

### QeRL

关注日期和人数，实际调用没有机场。

评分指出的失败位置/原因：

```text
["Valid syntax. Successfully decode AST when it should not."]
```

