# Case 040 — simple_python_395

## 任务

第 1 轮：

Find the nearest parking lot within 2 miles of Central Park in New York.

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
      "name": "mcp_tool_parking_lot.find_nearest",
      "arguments": {
        "location": "Central Park, NY",
        "radius": 2
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
      "name": "mcp_tool_parking_lot.find_nearest",
      "arguments": {
        "location": "Central Park, NY",
        "radius": 2
      }
    }
  }
]
```

</details>

### GPTQ：未通过

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
      "name": "mcp_tool_parking_lot.find_nearest",
      "arguments": {
        "location": "Central Park, New York",
        "radius": 2
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
      "name": "mcp_tool_parking_lot.find_nearest",
      "arguments": {
        "location": "Central Park",
        "radius": 2
      }
    }
  }
]
```

</details>

### BitDistiller：未通过

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
      "name": "mcp_tool_parking_lot.find_nearest",
      "arguments": {
        "location": "Central Park, New York",
        "radius": 2,
        "type": "public"
      }
    }
  }
]
```

</details>

### On-Policy QAD：未通过

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
      "name": "mcp_tool_parking_lot.find_nearest",
      "arguments": {
        "location": "Central Park, New York",
        "radius": 2
      }
    }
  }
]
```

</details>

### QeRL：未通过

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
      "name": "mcp_tool_parking_lot.find_nearest",
      "arguments": {
        "location": "Central Park, New York",
        "radius": 2
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
    "reference": "Central Park, NY",
    "actual": "Central Park, New York"
  }
]
```

### EfficientQAT

最早动作差异：第 1 个用户轮，第 1 个任务动作；BF16 消息 4，本方法消息 4。

```json
[
  {
    "field": "$.arguments.location",
    "reference": "Central Park, NY",
    "actual": "Central Park"
  }
]
```

### BitDistiller

最早动作差异：第 1 个用户轮，第 1 个任务动作；BF16 消息 4，本方法消息 4。

```json
[
  {
    "field": "$.arguments.location",
    "reference": "Central Park, NY",
    "actual": "Central Park, New York"
  },
  {
    "field": "$.arguments.type",
    "reference": null,
    "actual": "public",
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
    "field": "$.arguments.location",
    "reference": "Central Park, NY",
    "actual": "Central Park, New York"
  }
]
```

### QeRL

最早动作差异：第 1 个用户轮，第 1 个任务动作；BF16 消息 4，本方法消息 4。

```json
[
  {
    "field": "$.arguments.location",
    "reference": "Central Park, NY",
    "actual": "Central Park, New York"
  }
]
```

## 失败原因

评分接受 Central Park, NY；多数 baseline 使用 Central Park, New York，EfficientQAT 使用 Central Park。主要是地点字符串匹配差异，不能声称多数方法找错了城市。

### GPTQ

评分指出的失败位置/原因：

```text
["Invalid value for parameter 'location': 'Central Park, New York'. Expected one of ['Central Park, NY']. Case insensitive."]
```

### EfficientQAT

评分指出的失败位置/原因：

```text
["Invalid value for parameter 'location': 'Central Park'. Expected one of ['Central Park, NY']. Case insensitive."]
```

### BitDistiller

评分指出的失败位置/原因：

```text
["Invalid value for parameter 'location': 'Central Park, New York'. Expected one of ['Central Park, NY']. Case insensitive."]
```

### On-Policy QAD

评分指出的失败位置/原因：

```text
["Invalid value for parameter 'location': 'Central Park, New York'. Expected one of ['Central Park, NY']. Case insensitive."]
```

### QeRL

评分指出的失败位置/原因：

```text
["Invalid value for parameter 'location': 'Central Park, New York'. Expected one of ['Central Park, NY']. Case insensitive."]
```
