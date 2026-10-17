# Case 001 — irrelevance_162

## 原始任务

第 1 轮：

Who are the famous dancers of the 19th Century?

完整工具定义、初始状态及其他任务字段见 task.json。

## 七种方法的实际表现

### BF16：通过

指出工具未明确支持舞者查询，而且缺少博物馆名称，没有发起调用。

实际任务调用 0 次；[完整 CoT 和工具返回](BF16/cot_and_actions.txt)。

<details><summary>实际动作序列</summary>

```json
[]
```

</details>

### Ours：通过

识别到现有工具不适合回答该问题，没有调用任务工具。

实际任务调用 0 次；[完整 CoT 和工具返回](Ours/cot_and_actions.txt)。

<details><summary>实际动作序列</summary>

```json
[]
```

</details>

### GPTQ：未通过

承认查询舞者有些牵强，仍自行选定 Louvre Museum 和 France。

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
      "name": "mcp_tool_get_museum_artists",
      "arguments": {
        "museum_name": "Louvre Museum",
        "period": "19th Century",
        "country": "France"
      }
    }
  }
]
```

</details>

### EfficientQAT：未通过

假设艺术家结果可能包含舞者，实际调用只有 period 和 country，缺少 museum_name。

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
      "name": "mcp_tool_get_museum_artists",
      "arguments": {
        "period": "19th Century",
        "country": "France"
      }
    }
  }
]
```

</details>

### BitDistiller：未通过

自行选择 Louvre，希望结果包含舞者。

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
      "name": "mcp_tool_get_museum_artists",
      "arguments": {
        "museum_name": "Louvre",
        "period": "19th Century"
      }
    }
  }
]
```

</details>

### On-Policy QAD：未通过

把舞者扩大解释为工具里的艺术家，并自行选择 Metropolitan Museum of Art。

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
      "name": "mcp_tool_get_museum_artists",
      "arguments": {
        "museum_name": "Metropolitan Museum of Art",
        "period": "19th Century"
      }
    }
  }
]
```

</details>

### QeRL：未通过

承认工具未提到舞蹈，仍以只有这一个工具为理由强行调用。

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
      "name": "mcp_tool_get_museum_artists",
      "arguments": {
        "museum_name": "Metropolitan Museum of Art",
        "period": "19th Century"
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
      "name": "mcp_tool_get_museum_artists",
      "arguments": {
        "museum_name": "Louvre Museum",
        "period": "19th Century",
        "country": "France"
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
      "name": "mcp_tool_get_museum_artists",
      "arguments": {
        "period": "19th Century",
        "country": "France"
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
      "name": "mcp_tool_get_museum_artists",
      "arguments": {
        "museum_name": "Louvre",
        "period": "19th Century"
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
      "name": "mcp_tool_get_museum_artists",
      "arguments": {
        "museum_name": "Metropolitan Museum of Art",
        "period": "19th Century"
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
      "name": "mcp_tool_get_museum_artists",
      "arguments": {
        "museum_name": "Metropolitan Museum of Art",
        "period": "19th Century"
      }
    }
  }
]
```

## 失败原因

五个 baseline 的所选轨迹都尝试把博物馆艺术家查询工具套到舞者问题上。GPTQ、BitDistiller、On-Policy QAD 和 QeRL 自行选定卢浮宫或大都会博物馆；EfficientQAT 的实际调用甚至没有填写必填的 museum_name。它们的推理中出现了“也许艺术家包括舞者”“虽然牵强，但只有这个工具”的假设。BF16 和 Ours 则保留工具无法满足请求的判断，没有强行调用。可观察的分歧发生在看到工具列表后的第一条回复：从识别工具限制，转向用没有依据的假设为调用找理由。

### GPTQ

承认查询舞者有些牵强，仍自行选定 Louvre Museum 和 France。

评分指出的失败位置/原因：

```text
["Valid syntax. Successfully decode AST when it should not."]
```

### EfficientQAT

假设艺术家结果可能包含舞者，实际调用只有 period 和 country，缺少 museum_name。

评分指出的失败位置/原因：

```text
["Valid syntax. Successfully decode AST when it should not."]
```

### BitDistiller

自行选择 Louvre，希望结果包含舞者。

评分指出的失败位置/原因：

```text
["Valid syntax. Successfully decode AST when it should not."]
```

### On-Policy QAD

把舞者扩大解释为工具里的艺术家，并自行选择 Metropolitan Museum of Art。

评分指出的失败位置/原因：

```text
["Valid syntax. Successfully decode AST when it should not."]
```

### QeRL

承认工具未提到舞蹈，仍以只有这一个工具为理由强行调用。

评分指出的失败位置/原因：

```text
["Valid syntax. Successfully decode AST when it should not."]
```

