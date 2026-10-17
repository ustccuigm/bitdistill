# Case 013 — live_multiple_142-55-0

## 原始任务

第 1 轮：

Could you provide the current weather data for London in the UK, including the temperature, wind speed, and precipitation levels?

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
      "name": "mcp_tool_weather.get_weather_data",
      "arguments": {
        "city": "London",
        "country": "GB"
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
      "name": "mcp_tool_weather.get_weather_data",
      "arguments": {
        "city": "London",
        "country": "GB",
        "units": "metric"
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
      "name": "mcp_tool_weather.get_weather_data",
      "arguments": {
        "city": "London",
        "country": "UK"
      }
    }
  },
  {
    "user_turn": 1,
    "action_in_turn": 2,
    "message_index": 6,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_weather.get_weather_data",
      "arguments": {
        "city": "London",
        "country": "UK"
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
      "name": "mcp_tool_weather.get_weather_data",
      "arguments": {
        "city": "London",
        "country": "UK"
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
      "name": "mcp_tool_weather.get_weather_data",
      "arguments": {
        "city": "London",
        "country": "UK",
        "units": "metric"
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
      "name": "mcp_tool_weather.get_weather_data",
      "arguments": {
        "city": "London",
        "country": "UK"
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
      "name": "mcp_tool_weather.get_weather_data",
      "arguments": {
        "city": "London",
        "country": "UK"
      }
    }
  }
]
```

</details>

## 分歧位置

消息编号从 0 开始，用户轮和动作编号从 1 开始。按同一用户轮的任务动作序号与 BF16 比较，忽略 list_tools。最早动作差异不一定就是失败起点：正确的工具顺序、补救步骤也可能不同；评分失败位置另见下一节。

### Ours

最早动作差异：第 1 个用户轮，第 1 个任务动作；BF16 消息 4，本方法消息 4。

```json
[
  {
    "field": "$.arguments.units",
    "reference": null,
    "actual": "metric",
    "reference_present": false,
    "actual_present": true
  }
]
```

### GPTQ

最早动作差异：第 1 个用户轮，第 1 个任务动作；BF16 消息 4，本方法消息 4。

```json
[
  {
    "field": "$.arguments.country",
    "reference": "GB",
    "actual": "UK"
  }
]
```

### EfficientQAT

最早动作差异：第 1 个用户轮，第 1 个任务动作；BF16 消息 4，本方法消息 4。

```json
[
  {
    "field": "$.arguments.country",
    "reference": "GB",
    "actual": "UK"
  }
]
```

### BitDistiller

最早动作差异：第 1 个用户轮，第 1 个任务动作；BF16 消息 4，本方法消息 4。

```json
[
  {
    "field": "$.arguments.country",
    "reference": "GB",
    "actual": "UK"
  },
  {
    "field": "$.arguments.units",
    "reference": null,
    "actual": "metric",
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
    "field": "$.arguments.country",
    "reference": "GB",
    "actual": "UK"
  }
]
```

### QeRL

最早动作差异：第 1 个用户轮，第 1 个任务动作；BF16 消息 4，本方法消息 4。

```json
[
  {
    "field": "$.arguments.country",
    "reference": "GB",
    "actual": "UK"
  }
]
```

## 失败原因

GPTQ 的调用数量不匹配；其余四种方法将国家写为 UK，参考答案接受 GB。这是国家代码的匹配差异，不能据此说它们查询了不同城市。

### GPTQ

评分指出的失败位置/原因：

```text
["Wrong number of functions."]
```

### EfficientQAT

评分指出的失败位置/原因：

```text
["Invalid value for parameter 'country': 'UK'. Expected one of ['GB']. Case insensitive."]
```

### BitDistiller

评分指出的失败位置/原因：

```text
["Invalid value for parameter 'country': 'UK'. Expected one of ['GB']. Case insensitive."]
```

### On-Policy QAD

评分指出的失败位置/原因：

```text
["Invalid value for parameter 'country': 'UK'. Expected one of ['GB']. Case insensitive."]
```

### QeRL

评分指出的失败位置/原因：

```text
["Invalid value for parameter 'country': 'UK'. Expected one of ['GB']. Case insensitive."]
```

