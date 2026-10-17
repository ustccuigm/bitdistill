# Case 015 — live_multiple_500-148-10

## 原始任务

第 1 轮：

I'm looking to catch a music concert today in San Francisco. Find some cultural events for me?

完整工具定义、初始状态及其他任务字段见 task.json。

## 七种方法的实际表现

### BF16：通过

CoT 明确说明 date 可省略并默认查询当天，最终调用省略 date。

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
      "name": "mcp_tool_Events_3_FindEvents",
      "arguments": {
        "event_type": "Music",
        "city": "San Francisco, CA"
      }
    }
  }
]
```

</details>

### Ours：通过

明确决定不填写 date，使用工具默认的今天。

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
      "name": "mcp_tool_Events_3_FindEvents",
      "arguments": {
        "event_type": "Music",
        "city": "San Francisco, CA"
      }
    }
  }
]
```

</details>

### GPTQ：未通过

CoT 读到了默认查询当天的规则，最终仍填入 date=2023-10-05。

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
      "name": "mcp_tool_Events_3_FindEvents",
      "arguments": {
        "event_type": "Music",
        "city": "San Francisco, CA",
        "date": "2023-10-05"
      }
    }
  }
]
```

</details>

### EfficientQAT：未通过

在推理中直接断言今天是 2026-10-05，并把它写进参数。

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
      "name": "mcp_tool_Events_3_FindEvents",
      "arguments": {
        "event_type": "Music",
        "city": "San Francisco, CA",
        "date": "2026-10-05"
      }
    }
  }
]
```

</details>

### BitDistiller：未通过

先说默认当前日期可用，随后假设今天是 2023-10-05，并实际传入该日期。

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
      "name": "mcp_tool_Events_3_FindEvents",
      "arguments": {
        "event_type": "Music",
        "city": "San Francisco, CA",
        "date": "2023-10-05"
      }
    }
  }
]
```

</details>

### On-Policy QAD：未通过

用没有来源的 2023-10-05 代表今天，覆盖了正确默认值。

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
      "name": "mcp_tool_Events_3_FindEvents",
      "arguments": {
        "event_type": "Music",
        "city": "San Francisco, CA",
        "date": "2023-10-05"
      }
    }
  }
]
```

</details>

### QeRL：未通过

把用户说“今天”理解成必须显式填写日期，随后编造 2023-10-05。

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
      "name": "mcp_tool_Events_3_FindEvents",
      "arguments": {
        "event_type": "Music",
        "city": "San Francisco, CA",
        "date": "2023-10-05"
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
    "field": "$.arguments.date",
    "reference": null,
    "actual": "2023-10-05",
    "reference_present": false,
    "actual_present": true
  }
]
```

### EfficientQAT

最早动作差异：第 1 个用户轮，第 1 个任务动作；BF16 消息 4，本方法消息 4。

```json
[
  {
    "field": "$.arguments.date",
    "reference": null,
    "actual": "2026-10-05",
    "reference_present": false,
    "actual_present": true
  }
]
```

### BitDistiller

最早动作差异：第 1 个用户轮，第 1 个任务动作；BF16 消息 4，本方法消息 4。

```json
[
  {
    "field": "$.arguments.date",
    "reference": null,
    "actual": "2023-10-05",
    "reference_present": false,
    "actual_present": true
  }
]
```

### On-Policy QAD

最早动作差异：第 1 个用户轮，第 1 个任务动作；BF16 消息 4，本方法消息 4。

```json
[
  {
    "field": "$.arguments.date",
    "reference": null,
    "actual": "2023-10-05",
    "reference_present": false,
    "actual_present": true
  }
]
```

### QeRL

最早动作差异：第 1 个用户轮，第 1 个任务动作；BF16 消息 4，本方法消息 4。

```json
[
  {
    "field": "$.arguments.date",
    "reference": null,
    "actual": "2023-10-05",
    "reference_present": false,
    "actual_present": true
  }
]
```

## 失败原因

七种方法都选中了正确的活动查询工具，区别出在是否填写日期。五个 baseline 的所选轨迹把“今天”写成了上下文没有提供的具体日期，其中四个写成 2023-10-05，EfficientQAT 写成 2026-10-05。BF16 和 Ours 保留工具的默认日期，因此通过。可观察的分歧在看到工具列表后的第一条回复生成 date 参数的位置；它不是工具名选错或 JSON 解析失败，而是已经读到默认规则，仍增加了没有依据的限制。该案例没有测量 token 概率，不能仅据此断定量化误差的具体数值或排除采样影响。

### GPTQ

CoT 读到了默认查询当天的规则，最终仍填入 date=2023-10-05。

评分指出的失败位置/原因：

```text
["Invalid value for parameter 'date': '2023-10-05'. Expected one of ['', 'null']. Case insensitive."]
```

### EfficientQAT

在推理中直接断言今天是 2026-10-05，并把它写进参数。

评分指出的失败位置/原因：

```text
["Invalid value for parameter 'date': '2026-10-05'. Expected one of ['', 'null']. Case insensitive."]
```

### BitDistiller

先说默认当前日期可用，随后假设今天是 2023-10-05，并实际传入该日期。

评分指出的失败位置/原因：

```text
["Invalid value for parameter 'date': '2023-10-05'. Expected one of ['', 'null']. Case insensitive."]
```

### On-Policy QAD

用没有来源的 2023-10-05 代表今天，覆盖了正确默认值。

评分指出的失败位置/原因：

```text
["Invalid value for parameter 'date': '2023-10-05'. Expected one of ['', 'null']. Case insensitive."]
```

### QeRL

把用户说“今天”理解成必须显式填写日期，随后编造 2023-10-05。

评分指出的失败位置/原因：

```text
["Invalid value for parameter 'date': '2023-10-05'. Expected one of ['', 'null']. Case insensitive."]
```

