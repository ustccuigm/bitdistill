# Case 011 — live_irrelevance_876-361-0

## 原始任务

第 1 轮：

I'm planning to travel on the 8th of march 2023 and need to reserve train tickets. Could you book them for me? I'm not particular about the fare class.

完整工具定义、初始状态及其他任务字段见 task.json。

## 七种方法的实际表现

### BF16：通过

没有在行程城市缺失时调用订票或查票工具。

实际任务调用 0 次；[完整 CoT 和工具返回](BF16/cot_and_actions.txt)。

<details><summary>实际动作序列</summary>

```json
[]
```

</details>

### Ours：通过

先补充询问行程信息，没有强行查票。

实际任务调用 0 次；[完整 CoT 和工具返回](Ours/cot_and_actions.txt)。

<details><summary>实际动作序列</summary>

```json
[]
```

</details>

### GPTQ：未通过

CoT 说需要询问城市，动作却使用 San Francisco, CA 和 Los Angeles, CA。

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
      "name": "mcp_tool_Trains_1_FindTrains",
      "arguments": {
        "_from": "San Francisco, CA",
        "to": "Los Angeles, CA",
        "date_of_journey": "03/08/2023"
      }
    }
  }
]
```

</details>

### EfficientQAT：未通过

只传日期，省略必填的 _from 和 to。

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
      "name": "mcp_tool_Trains_1_FindTrains",
      "arguments": {
        "date_of_journey": "03/08/2023"
      }
    }
  }
]
```

</details>

### BitDistiller：未通过

只传日期和 dontcare 舱位，未提供必填的出发地和目的地。

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
      "name": "mcp_tool_Trains_1_FindTrains",
      "arguments": {
        "date_of_journey": "03/08/2023",
        "_class": "dontcare"
      }
    }
  },
  {
    "user_turn": 1,
    "action_in_turn": 2,
    "message_index": 6,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_Trains_1_GetTrainTickets",
      "arguments": {
        "_from": "Boston, MA",
        "to": "New York, NY",
        "date_of_journey": "03/08/2023",
        "journey_start_time": "08:00",
        "number_of_adults": 1,
        "trip_protection": false,
        "_class": "Value"
      }
    }
  }
]
```

</details>

### On-Policy QAD：未通过

CoT 说城市未知，动作却自行设为 Boston, MA 到 New York, NY。

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
      "name": "mcp_tool_Trains_1_FindTrains",
      "arguments": {
        "_from": "Boston, MA",
        "to": "New York, NY",
        "date_of_journey": "03/08/2023"
      }
    }
  },
  {
    "user_turn": 1,
    "action_in_turn": 2,
    "message_index": 6,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_Trains_1_GetTrainTickets",
      "arguments": {
        "_from": "Boston, MA",
        "to": "New York, NY",
        "date_of_journey": "03/08/2023",
        "number_of_adults": 1,
        "trip_protection": false,
        "_class": "Value"
      }
    }
  }
]
```

</details>

### QeRL：未通过

出发地和目的地传空字符串，还自行设定一名成人。

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
      "name": "mcp_tool_Trains_1_FindTrains",
      "arguments": {
        "_from": "",
        "to": "",
        "date_of_journey": "03/08/2023",
        "_class": "dontcare",
        "number_of_adults": 1
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
      "name": "mcp_tool_Trains_1_FindTrains",
      "arguments": {
        "_from": "San Francisco, CA",
        "to": "Los Angeles, CA",
        "date_of_journey": "03/08/2023"
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
      "name": "mcp_tool_Trains_1_FindTrains",
      "arguments": {
        "date_of_journey": "03/08/2023"
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
      "name": "mcp_tool_Trains_1_FindTrains",
      "arguments": {
        "date_of_journey": "03/08/2023",
        "_class": "dontcare"
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
      "name": "mcp_tool_Trains_1_FindTrains",
      "arguments": {
        "_from": "Boston, MA",
        "to": "New York, NY",
        "date_of_journey": "03/08/2023"
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
      "name": "mcp_tool_Trains_1_FindTrains",
      "arguments": {
        "_from": "",
        "to": "",
        "date_of_journey": "03/08/2023",
        "_class": "dontcare",
        "number_of_adults": 1
      }
    }
  }
]
```

## 失败原因

五种 baseline 的所选轨迹在推理中都发现缺少出发地和目的地，最终却发起 FindTrains 调用。GPTQ 自行选择旧金山到洛杉矶，On-Policy QAD 自行选择波士顿到纽约；EfficientQAT 和 BitDistiller 省略必填城市，QeRL 把城市设为空字符串。BF16 和 Ours 先询问缺失信息。共同分歧发生在看到工具列表后的第一条回复：推理中的澄清结论没有约束实际动作。这不是因为用户没有指定舱位，舱位本来就可以不填。

### GPTQ

CoT 说需要询问城市，动作却使用 San Francisco, CA 和 Los Angeles, CA。

评分指出的失败位置/原因：

```text
["Valid syntax. Successfully decode AST when it should not."]
```

### EfficientQAT

只传日期，省略必填的 _from 和 to。

评分指出的失败位置/原因：

```text
["Valid syntax. Successfully decode AST when it should not."]
```

### BitDistiller

只传日期和 dontcare 舱位，未提供必填的出发地和目的地。

评分指出的失败位置/原因：

```text
["Valid syntax. Successfully decode AST when it should not."]
```

### On-Policy QAD

CoT 说城市未知，动作却自行设为 Boston, MA 到 New York, NY。

评分指出的失败位置/原因：

```text
["Valid syntax. Successfully decode AST when it should not."]
```

### QeRL

出发地和目的地传空字符串，还自行设定一名成人。

评分指出的失败位置/原因：

```text
["Valid syntax. Successfully decode AST when it should not."]
```

