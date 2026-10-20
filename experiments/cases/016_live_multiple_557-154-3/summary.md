# Case 016 — live_multiple_557-154-3

## 任务

第 1 轮：

I need to rent a car in Los Angeles. Find what's available from April 18th 2023 at 10am until April 24th?

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
      "name": "mcp_tool_RentalCars_3_GetCarsAvailable",
      "arguments": {
        "city": "Los Angeles, CA",
        "start_date": "2023-04-18",
        "pickup_time": "10:00",
        "end_date": "2023-04-24",
        "car_type": "dontcare"
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
      "name": "mcp_tool_RentalCars_3_GetCarsAvailable",
      "arguments": {
        "city": "Los Angeles, CA",
        "start_date": "2023-04-18",
        "pickup_time": "10:00",
        "end_date": "2023-04-24",
        "car_type": "dontcare"
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
      "name": "mcp_tool_RentalCars_3_GetCarsAvailable",
      "arguments": {
        "city": "Los Angeles, CA",
        "start_date": "2023-04-18",
        "pickup_time": "10:00",
        "end_date": "2023-04-24",
        "car_type": "dontcare"
      }
    }
  },
  {
    "user_turn": 1,
    "action_in_turn": 2,
    "message_index": 6,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_RentalCars_3_ReserveCar",
      "arguments": {
        "pickup_location": "Los Angeles, CA",
        "start_date": "04/18/2023",
        "pickup_time": "10:00 AM",
        "end_date": "04/24/2023",
        "car_type": "Sedan",
        "add_insurance": false
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
      "name": "mcp_tool_RentalCars_3_GetCarsAvailable",
      "arguments": {
        "city": "Los Angeles, CA",
        "start_date": "2023-04-18",
        "pickup_time": "10:00 AM",
        "end_date": "2023-04-24",
        "car_type": "dontcare"
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
      "name": "mcp_tool_RentalCars_3_GetCarsAvailable",
      "arguments": {
        "city": "Los Angeles, CA",
        "start_date": "2023-04-18",
        "pickup_time": "10:00 AM",
        "end_date": "2023-04-24"
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
      "name": "mcp_tool_RentalCars_3_GetCarsAvailable",
      "arguments": {
        "city": "Los Angeles, CA",
        "start_date": "2023-04-18",
        "pickup_time": "10:00 AM",
        "end_date": "2023-04-24",
        "car_type": "dontcare"
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
      "name": "mcp_tool_RentalCars_3_GetCarsAvailable",
      "arguments": {
        "city": "Los Angeles, CA",
        "start_date": "2023-04-18",
        "pickup_time": "10:00 AM",
        "end_date": "2023-04-24",
        "car_type": "dontcare"
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

最早动作差异：第 1 个用户轮，第 2 个任务动作；BF16 消息 None，本方法消息 6。

```json
[
  {
    "field": "$",
    "reference": null,
    "actual": {
      "wrapper": "call_tool",
      "name": "mcp_tool_RentalCars_3_ReserveCar",
      "arguments": {
        "pickup_location": "Los Angeles, CA",
        "start_date": "04/18/2023",
        "pickup_time": "10:00 AM",
        "end_date": "04/24/2023",
        "car_type": "Sedan",
        "add_insurance": false
      }
    }
  }
]
```

### EfficientQAT

最早动作差异：第 1 个用户轮，第 1 个任务动作；BF16 消息 4，本方法消息 4。

```json
[
  {
    "field": "$.arguments.pickup_time",
    "reference": "10:00",
    "actual": "10:00 AM"
  }
]
```

### BitDistiller

最早动作差异：第 1 个用户轮，第 1 个任务动作；BF16 消息 4，本方法消息 4。

```json
[
  {
    "field": "$.arguments.car_type",
    "reference": "dontcare",
    "actual": null,
    "reference_present": true,
    "actual_present": false
  },
  {
    "field": "$.arguments.pickup_time",
    "reference": "10:00",
    "actual": "10:00 AM"
  }
]
```

### On-Policy QAD

最早动作差异：第 1 个用户轮，第 1 个任务动作；BF16 消息 4，本方法消息 4。

```json
[
  {
    "field": "$.arguments.pickup_time",
    "reference": "10:00",
    "actual": "10:00 AM"
  }
]
```

### QeRL

最早动作差异：第 1 个用户轮，第 1 个任务动作；BF16 消息 4，本方法消息 4。

```json
[
  {
    "field": "$.arguments.pickup_time",
    "reference": "10:00",
    "actual": "10:00 AM"
  }
]
```

## 失败原因

GPTQ 的调用数量不匹配；其余四种方法写 10:00 AM，评分要求 10:00。时间含义相同，失败来自格式匹配。

### GPTQ

评分指出的失败位置/原因：

```text
["Wrong number of functions."]
```

### EfficientQAT

评分指出的失败位置/原因：

```text
["Invalid value for parameter 'pickup_time': '10:00 AM'. Expected one of ['10:00']. Case insensitive."]
```

### BitDistiller

评分指出的失败位置/原因：

```text
["Invalid value for parameter 'pickup_time': '10:00 AM'. Expected one of ['10:00']. Case insensitive."]
```

### On-Policy QAD

评分指出的失败位置/原因：

```text
["Invalid value for parameter 'pickup_time': '10:00 AM'. Expected one of ['10:00']. Case insensitive."]
```

### QeRL

评分指出的失败位置/原因：

```text
["Invalid value for parameter 'pickup_time': '10:00 AM'. Expected one of ['10:00']. Case insensitive."]
```
