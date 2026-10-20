# Case 039 — simple_python_130

## 任务

第 1 轮：

What's the NPV (Net Present Value) of a series of cash flows: [-50000, 10000, 15000, 20000, 25000, 30000] discounted at 8% annually?

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
      "name": "mcp_tool_finance_calculator.npv",
      "arguments": {
        "cash_flows": [
          -50000,
          10000,
          15000,
          20000,
          25000,
          30000
        ],
        "discount_rate": 0.08
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
      "name": "mcp_tool_finance_calculator.npv",
      "arguments": {
        "cash_flows": [
          -50000,
          10000,
          15000,
          20000,
          25000,
          30000
        ],
        "discount_rate": 0.08
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
      "name": "mcp_tool_finance_calculator.npv",
      "arguments": {
        "cash_flows": [
          "-50000",
          "10000",
          "15000",
          "20000",
          "25000",
          "30000"
        ],
        "discount_rate": 0.08
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
      "name": "mcp_tool_finance_calculator.npv",
      "arguments": {
        "cash_flows": [
          -50000,
          10000,
          15000,
          20000,
          25000,
          30000
        ],
        "discount_rate": 0.08,
        "years": [
          0,
          1,
          2,
          3,
          4,
          5
        ]
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
      "name": "mcp_tool_finance_calculator.npv",
      "arguments": {
        "cash_flows": [
          -50000,
          10000,
          15000,
          20000,
          25000,
          30000
        ],
        "discount_rate": 0.08,
        "years": [
          0,
          1,
          2,
          3,
          4,
          5
        ]
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
      "name": "mcp_tool_finance_calculator.npv",
      "arguments": {
        "cash_flows": [
          -50000,
          10000,
          15000,
          20000,
          25000,
          30000
        ],
        "discount_rate": 0.08,
        "years": [
          0,
          1,
          2,
          3,
          4,
          5
        ]
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
      "name": "mcp_tool_finance_calculator.npv",
      "arguments": {
        "cash_flows": [
          -50000,
          10000,
          15000,
          20000,
          25000,
          30000
        ],
        "discount_rate": 0.08,
        "years": [
          0,
          1,
          2,
          3,
          4,
          5
        ]
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
    "field": "$.arguments.cash_flows[0]",
    "reference": -50000,
    "actual": "-50000"
  },
  {
    "field": "$.arguments.cash_flows[1]",
    "reference": 10000,
    "actual": "10000"
  },
  {
    "field": "$.arguments.cash_flows[2]",
    "reference": 15000,
    "actual": "15000"
  },
  {
    "field": "$.arguments.cash_flows[3]",
    "reference": 20000,
    "actual": "20000"
  },
  {
    "field": "$.arguments.cash_flows[4]",
    "reference": 25000,
    "actual": "25000"
  },
  {
    "field": "$.arguments.cash_flows[5]",
    "reference": 30000,
    "actual": "30000"
  }
]
```

### EfficientQAT

最早动作差异：第 1 个用户轮，第 1 个任务动作；BF16 消息 4，本方法消息 4。

```json
[
  {
    "field": "$.arguments.years",
    "reference": null,
    "actual": [
      0,
      1,
      2,
      3,
      4,
      5
    ],
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
    "field": "$.arguments.years",
    "reference": null,
    "actual": [
      0,
      1,
      2,
      3,
      4,
      5
    ],
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
    "field": "$.arguments.years",
    "reference": null,
    "actual": [
      0,
      1,
      2,
      3,
      4,
      5
    ],
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
    "field": "$.arguments.years",
    "reference": null,
    "actual": [
      0,
      1,
      2,
      3,
      4,
      5
    ],
    "reference_present": false,
    "actual_present": true
  }
]
```

## 失败原因

GPTQ 将现金流数字写成字符串，违反参数类型；其余四种方法增加 years=[0,1,2,3,4,5]，参考答案要求省略或空列表。后者不等同于已证明 NPV 数值算错。

### GPTQ

评分指出的失败位置/原因：

```text
["Nested type checking failed for parameter 'cash_flows'. Expected outer type array with inner type <class 'int'>. Parameter value: ['-50000', '10000', '15000', '20000', '25000', '30000']."]
```

### EfficientQAT

评分指出的失败位置/原因：

```text
["Invalid value for parameter 'years': [0, 1, 2, 3, 4, 5]. Expected one of ['', []]."]
```

### BitDistiller

评分指出的失败位置/原因：

```text
["Invalid value for parameter 'years': [0, 1, 2, 3, 4, 5]. Expected one of ['', []]."]
```

### On-Policy QAD

评分指出的失败位置/原因：

```text
["Invalid value for parameter 'years': [0, 1, 2, 3, 4, 5]. Expected one of ['', []]."]
```

### QeRL

评分指出的失败位置/原因：

```text
["Invalid value for parameter 'years': [0, 1, 2, 3, 4, 5]. Expected one of ['', []]."]
```
