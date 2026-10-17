# Case 009 — live_irrelevance_623-196-4

## 原始任务

第 1 轮：

I have a plan for a trip to Los Angeles for which I want to search for a round trip flight. I am comfortable with Economy seats in Delta Airlines flight. Find me the suitable one.

完整工具定义、初始状态及其他任务字段见 task.json。

## 七种方法的实际表现

### BF16：通过

没有在出发地缺失时发起查询。

实际任务调用 0 次；[完整 CoT 和工具返回](BF16/cot_and_actions.txt)。

<details><summary>实际动作序列</summary>

```json
[]
```

</details>

### Ours：通过

保留补充信息的分支，没有强行调用查询工具。

实际任务调用 0 次；[完整 CoT 和工具返回](Ours/cot_and_actions.txt)。

<details><summary>实际动作序列</summary>

```json
[]
```

</details>

### GPTQ：未通过

CoT 最后说应该请求缺失信息，实际却传入 origin_airport=<missing>。

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
        "origin_airport": "<missing>",
        "destination_airport": "Los Angeles",
        "departure_date": "<missing>",
        "return_date": "<missing>",
        "seating_class": "Economy",
        "airlines": "Delta Airlines"
      }
    }
  }
]
```

</details>

### EfficientQAT：未通过

明知出发地必填，仍传入空字符串，同时填入用户没有提供的日期。

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
        "origin_airport": "",
        "destination_airport": "Los Angeles",
        "departure_date": "2023-12-08",
        "return_date": "2023-12-16",
        "seating_class": "Economy",
        "airlines": "Delta Airlines"
      }
    }
  }
]
```

</details>

### BitDistiller：未通过

CoT 计划先询问出发地，实际调用的 origin_airport 仍为空。

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
        "origin_airport": "",
        "destination_airport": "Los Angeles",
        "departure_date": "",
        "return_date": "",
        "seating_class": "Economy",
        "airlines": "Delta Airlines"
      }
    }
  }
]
```

</details>

### On-Policy QAD：未通过

把 Los Angeles 同时填作出发地和目的地，改变了用户请求。

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
        "origin_airport": "Los Angeles",
        "destination_airport": "Los Angeles",
        "seating_class": "Economy",
        "airlines": "Delta Airlines"
      }
    }
  }
]
```

</details>

### QeRL：未通过

推理中反复讨论应先询问，最终仍用空出发地调用。

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
        "origin_airport": "",
        "destination_airport": "Los Angeles",
        "departure_date": "",
        "return_date": "",
        "seating_class": "Economy",
        "airlines": "Delta Airlines"
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
        "origin_airport": "<missing>",
        "destination_airport": "Los Angeles",
        "departure_date": "<missing>",
        "return_date": "<missing>",
        "seating_class": "Economy",
        "airlines": "Delta Airlines"
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
        "origin_airport": "",
        "destination_airport": "Los Angeles",
        "departure_date": "2023-12-08",
        "return_date": "2023-12-16",
        "seating_class": "Economy",
        "airlines": "Delta Airlines"
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
        "origin_airport": "",
        "destination_airport": "Los Angeles",
        "departure_date": "",
        "return_date": "",
        "seating_class": "Economy",
        "airlines": "Delta Airlines"
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
        "origin_airport": "Los Angeles",
        "destination_airport": "Los Angeles",
        "seating_class": "Economy",
        "airlines": "Delta Airlines"
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
        "origin_airport": "",
        "destination_airport": "Los Angeles",
        "departure_date": "",
        "return_date": "",
        "seating_class": "Economy",
        "airlines": "Delta Airlines"
      }
    }
  }
]
```

## 失败原因

问题不是选错了航班查询工具，而是缺少出发地时是否继续执行。五个 baseline 的所选轨迹都识别到需要补充信息，却仍生成调用：GPTQ 用 <missing> 占位，EfficientQAT、BitDistiller、QeRL 传入空字符串，On-Policy QAD 则把目的地洛杉矶同时当作出发地。BF16 和 Ours 没有调用查询工具，先要求补充信息。关键分歧位于看到工具列表后的第一条回复从“需要询问用户”的推理转向实际 tool_call 的地方。日期字段在此工具中可以省略，因此这里的确定性问题是缺失必填的出发地，不能把所有日期未填写都说成错误。

### GPTQ

CoT 最后说应该请求缺失信息，实际却传入 origin_airport=<missing>。

评分指出的失败位置/原因：

```text
["Valid syntax. Successfully decode AST when it should not."]
```

### EfficientQAT

明知出发地必填，仍传入空字符串，同时填入用户没有提供的日期。

评分指出的失败位置/原因：

```text
["Valid syntax. Successfully decode AST when it should not."]
```

### BitDistiller

CoT 计划先询问出发地，实际调用的 origin_airport 仍为空。

评分指出的失败位置/原因：

```text
["Valid syntax. Successfully decode AST when it should not."]
```

### On-Policy QAD

把 Los Angeles 同时填作出发地和目的地，改变了用户请求。

评分指出的失败位置/原因：

```text
["Valid syntax. Successfully decode AST when it should not."]
```

### QeRL

推理中反复讨论应先询问，最终仍用空出发地调用。

评分指出的失败位置/原因：

```text
["Valid syntax. Successfully decode AST when it should not."]
```

