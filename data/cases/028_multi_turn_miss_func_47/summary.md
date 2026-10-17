# Case 028 — multi_turn_miss_func_47

## 原始任务

第 1 轮：

I have a list of student record in this directory, could you find me where is it by telling me its name and using 'find'?

第 2 轮：

Look at the student_record.txt and tell me the average score.

第 3 轮：

第 4 轮：

What about the standard deviation?

完整工具定义、初始状态及其他任务字段见 task.json。

## 七种方法的实际表现

### BF16：通过

用 name=student 查询，成功匹配 student_record.txt。

实际任务调用 4 次；[完整 CoT 和工具返回](BF16/cot_and_actions.txt)。

<details><summary>实际动作序列</summary>

```json
[
  {
    "user_turn": 1,
    "action_in_turn": 1,
    "message_index": 4,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_find",
      "arguments": {
        "name": "student"
      }
    }
  },
  {
    "user_turn": 2,
    "action_in_turn": 1,
    "message_index": 8,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_cat",
      "arguments": {
        "file_name": "student_record.txt"
      }
    }
  },
  {
    "user_turn": 2,
    "action_in_turn": 2,
    "message_index": 10,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_mean",
      "arguments": {
        "numbers": [
          100,
          95,
          85,
          90,
          88,
          92
        ]
      }
    }
  },
  {
    "user_turn": 4,
    "action_in_turn": 1,
    "message_index": 16,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_standard_deviation",
      "arguments": {
        "numbers": [
          100,
          95,
          85,
          90,
          88,
          92
        ]
      }
    }
  }
]
```

</details>

### Ours：通过

不预设完整文件名，用空 name 检索得到目标文件，再完成后续统计任务。

实际任务调用 6 次；[完整 CoT 和工具返回](Ours/cot_and_actions.txt)。

<details><summary>实际动作序列</summary>

```json
[
  {
    "user_turn": 1,
    "action_in_turn": 1,
    "message_index": 4,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_find",
      "arguments": {
        "path": ".",
        "name": ""
      }
    }
  },
  {
    "user_turn": 2,
    "action_in_turn": 1,
    "message_index": 8,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_cat",
      "arguments": {
        "file_name": "student_record.txt"
      }
    }
  },
  {
    "user_turn": 2,
    "action_in_turn": 2,
    "message_index": 10,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_sum_values",
      "arguments": {
        "numbers": [
          100,
          95,
          85,
          90,
          88,
          92
        ]
      }
    }
  },
  {
    "user_turn": 2,
    "action_in_turn": 3,
    "message_index": 12,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_divide",
      "arguments": {
        "a": 550,
        "b": 6
      }
    }
  },
  {
    "user_turn": 3,
    "action_in_turn": 1,
    "message_index": 16,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_mean",
      "arguments": {
        "numbers": [
          100,
          95,
          85,
          90,
          88,
          92
        ]
      }
    }
  },
  {
    "user_turn": 4,
    "action_in_turn": 1,
    "message_index": 20,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_standard_deviation",
      "arguments": {
        "numbers": [
          100,
          95,
          85,
          90,
          88,
          92
        ]
      }
    }
  }
]
```

</details>

### GPTQ：未通过

先猜 student_records，随后仍未得到有效 find 匹配；通过 ls 看到了文件，但未在该轮修正 find 查询。

实际任务调用 6 次；[完整 CoT 和工具返回](GPTQ/cot_and_actions.txt)。

<details><summary>实际动作序列</summary>

```json
[
  {
    "user_turn": 1,
    "action_in_turn": 1,
    "message_index": 4,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_find",
      "arguments": {
        "path": ".",
        "name": "student_records"
      }
    }
  },
  {
    "user_turn": 1,
    "action_in_turn": 2,
    "message_index": 6,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_find",
      "arguments": "{\"path\": \".\", \"name\": \"*\")}"
    }
  },
  {
    "user_turn": 1,
    "action_in_turn": 3,
    "message_index": 8,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_ls",
      "arguments": {
        "a": false
      }
    }
  },
  {
    "user_turn": 2,
    "action_in_turn": 1,
    "message_index": 12,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_cat",
      "arguments": {
        "file_name": "student_record.txt"
      }
    }
  },
  {
    "user_turn": 3,
    "action_in_turn": 1,
    "message_index": 16,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_mean",
      "arguments": {
        "numbers": [
          100,
          95,
          85,
          90,
          88,
          92
        ]
      }
    }
  },
  {
    "user_turn": 4,
    "action_in_turn": 1,
    "message_index": 20,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_standard_deviation",
      "arguments": {
        "numbers": [
          100,
          95,
          85,
          90,
          88,
          92
        ]
      }
    }
  }
]
```

</details>

### EfficientQAT：未通过

student_records 返回空结果后改用 ls，没有补上成功的 find 定位。

实际任务调用 7 次；[完整 CoT 和工具返回](EfficientQAT/cot_and_actions.txt)。

<details><summary>实际动作序列</summary>

```json
[
  {
    "user_turn": 1,
    "action_in_turn": 1,
    "message_index": 4,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_find",
      "arguments": {
        "path": ".",
        "name": "student_records"
      }
    }
  },
  {
    "user_turn": 1,
    "action_in_turn": 2,
    "message_index": 6,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_ls",
      "arguments": {
        "a": true
      }
    }
  },
  {
    "user_turn": 2,
    "action_in_turn": 1,
    "message_index": 10,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_cat",
      "arguments": {
        "file_name": "student_record.txt"
      }
    }
  },
  {
    "user_turn": 2,
    "action_in_turn": 2,
    "message_index": 12,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_sum_values",
      "arguments": {
        "numbers": [
          100,
          95,
          85,
          90,
          88,
          92
        ]
      }
    }
  },
  {
    "user_turn": 2,
    "action_in_turn": 3,
    "message_index": 14,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_divide",
      "arguments": {
        "a": 550,
        "b": 6
      }
    }
  },
  {
    "user_turn": 3,
    "action_in_turn": 1,
    "message_index": 18,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_mean",
      "arguments": {
        "numbers": [
          100,
          95,
          85,
          90,
          88,
          92
        ]
      }
    }
  },
  {
    "user_turn": 4,
    "action_in_turn": 1,
    "message_index": 22,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_standard_deviation",
      "arguments": {
        "numbers": [
          100,
          95,
          85,
          90,
          88,
          92
        ]
      }
    }
  }
]
```

</details>

### BitDistiller：未通过

第一轮仅查询 student_records；下一轮用户给出明确文件名后才改用正确名称。

实际任务调用 5 次；[完整 CoT 和工具返回](BitDistiller/cot_and_actions.txt)。

<details><summary>实际动作序列</summary>

```json
[
  {
    "user_turn": 1,
    "action_in_turn": 1,
    "message_index": 4,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_find",
      "arguments": {
        "path": ".",
        "name": "student_records"
      }
    }
  },
  {
    "user_turn": 2,
    "action_in_turn": 1,
    "message_index": 8,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_find",
      "arguments": {
        "path": ".",
        "name": "student_record.txt"
      }
    }
  },
  {
    "user_turn": 2,
    "action_in_turn": 2,
    "message_index": 10,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_cat",
      "arguments": {
        "file_name": "student_record.txt"
      }
    }
  },
  {
    "user_turn": 3,
    "action_in_turn": 1,
    "message_index": 14,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_mean",
      "arguments": {
        "numbers": [
          100,
          95,
          85,
          90,
          88,
          92
        ]
      }
    }
  },
  {
    "user_turn": 4,
    "action_in_turn": 1,
    "message_index": 18,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_standard_deviation",
      "arguments": {
        "numbers": [
          100,
          95,
          85,
          90,
          88,
          92
        ]
      }
    }
  }
]
```

</details>

### On-Policy QAD：未通过

先猜 student_records，随后查看目录，但未在当前轮修正 find 的 name。

实际任务调用 5 次；[完整 CoT 和工具返回](On-Policy%20QAD/cot_and_actions.txt)。

<details><summary>实际动作序列</summary>

```json
[
  {
    "user_turn": 1,
    "action_in_turn": 1,
    "message_index": 4,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_find",
      "arguments": {
        "name": "student_records"
      }
    }
  },
  {
    "user_turn": 1,
    "action_in_turn": 2,
    "message_index": 6,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_ls",
      "arguments": {}
    }
  },
  {
    "user_turn": 2,
    "action_in_turn": 1,
    "message_index": 10,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_cat",
      "arguments": {
        "file_name": "student_record.txt"
      }
    }
  },
  {
    "user_turn": 2,
    "action_in_turn": 2,
    "message_index": 12,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_mean",
      "arguments": {
        "numbers": [
          100,
          95,
          85,
          90,
          88,
          92
        ]
      }
    }
  },
  {
    "user_turn": 4,
    "action_in_turn": 1,
    "message_index": 18,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_standard_deviation",
      "arguments": {
        "numbers": [
          100,
          95,
          85,
          90,
          88,
          92
        ]
      }
    }
  }
]
```

</details>

### QeRL：未通过

第一轮以 student_records 查询后停止；下一轮得到文件名提示才重新 find。

实际任务调用 9 次；[完整 CoT 和工具返回](QeRL/cot_and_actions.txt)。

<details><summary>实际动作序列</summary>

```json
[
  {
    "user_turn": 1,
    "action_in_turn": 1,
    "message_index": 4,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_find",
      "arguments": {
        "path": ".",
        "name": "student_records"
      }
    }
  },
  {
    "user_turn": 2,
    "action_in_turn": 1,
    "message_index": 8,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_find",
      "arguments": {
        "path": ".",
        "name": "student_record.txt"
      }
    }
  },
  {
    "user_turn": 2,
    "action_in_turn": 2,
    "message_index": 10,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_cat",
      "arguments": {
        "file_name": "student_record.txt"
      }
    }
  },
  {
    "user_turn": 2,
    "action_in_turn": 3,
    "message_index": 12,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_split",
      "arguments": {
        "input": "100 95 85 90 88 92",
        "delimiter": " "
      }
    }
  },
  {
    "user_turn": 2,
    "action_in_turn": 4,
    "message_index": 14,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_grep",
      "arguments": "{\"file_name\": \"student_record.txt\", \"pattern\": \"\\d+\"}"
    }
  },
  {
    "user_turn": 2,
    "action_in_turn": 5,
    "message_index": 16,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_sum_values",
      "arguments": {
        "numbers": [
          100,
          95,
          85,
          90,
          88,
          92
        ]
      }
    }
  },
  {
    "user_turn": 2,
    "action_in_turn": 6,
    "message_index": 18,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_divide",
      "arguments": {
        "a": 550,
        "b": 6
      }
    }
  },
  {
    "user_turn": 3,
    "action_in_turn": 1,
    "message_index": 22,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_mean",
      "arguments": {
        "numbers": [
          100,
          95,
          85,
          90,
          88,
          92
        ]
      }
    }
  },
  {
    "user_turn": 4,
    "action_in_turn": 1,
    "message_index": 26,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_standard_deviation",
      "arguments": {
        "numbers": [
          100,
          95,
          85,
          90,
          88,
          92
        ]
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
    "field": "$.arguments.name",
    "reference": "student",
    "actual": ""
  },
  {
    "field": "$.arguments.path",
    "reference": null,
    "actual": ".",
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
    "field": "$.arguments.name",
    "reference": "student",
    "actual": "student_records"
  },
  {
    "field": "$.arguments.path",
    "reference": null,
    "actual": ".",
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
    "field": "$.arguments.name",
    "reference": "student",
    "actual": "student_records"
  },
  {
    "field": "$.arguments.path",
    "reference": null,
    "actual": ".",
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
    "field": "$.arguments.name",
    "reference": "student",
    "actual": "student_records"
  },
  {
    "field": "$.arguments.path",
    "reference": null,
    "actual": ".",
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
    "field": "$.arguments.name",
    "reference": "student",
    "actual": "student_records"
  }
]
```

### QeRL

最早动作差异：第 1 个用户轮，第 1 个任务动作；BF16 消息 4，本方法消息 4。

```json
[
  {
    "field": "$.arguments.name",
    "reference": "student",
    "actual": "student_records"
  },
  {
    "field": "$.arguments.path",
    "reference": null,
    "actual": ".",
    "reference_present": false,
    "actual_present": true
  }
]
```

## 失败原因

五个 baseline 的所选轨迹在第一轮都猜测文件名为 student_records，find 返回空结果。它们没有在该轮改用更宽的关键词或正确文件名重新完成 find 定位。BF16 用 student 做部分匹配，Ours 用空名称检索当前目录，均得到目标文件。这里的共同分歧在首次 find 的 name 参数，后续问题是空结果没有促成当前任务内的有效修正。部分 baseline 后来通过 ls 看到了文件，或在下一轮用户明确给出文件名后成功读取；所以该案例说明第一轮定位要求失败，不能说它们此后始终找不到文件或数学计算全部错误。

### GPTQ

先猜 student_records，随后仍未得到有效 find 匹配；通过 ls 看到了文件，但未在该轮修正 find 查询。

评分指出的失败位置/原因：

```text
"Model response execution results so far does not contain all the ground truth response execution results for turn 0."
```


缺少的执行返回：

```text
["{\"matches\": [\"./student_record.txt\"]}"]
```

### EfficientQAT

student_records 返回空结果后改用 ls，没有补上成功的 find 定位。

评分指出的失败位置/原因：

```text
"Model response execution results so far does not contain all the ground truth response execution results for turn 0."
```


缺少的执行返回：

```text
["{\"matches\": [\"./student_record.txt\"]}"]
```

### BitDistiller

第一轮仅查询 student_records；下一轮用户给出明确文件名后才改用正确名称。

评分指出的失败位置/原因：

```text
"Model response execution results so far does not contain all the ground truth response execution results for turn 0."
```


缺少的执行返回：

```text
["{\"matches\": [\"./student_record.txt\"]}"]
```

### On-Policy QAD

先猜 student_records，随后查看目录，但未在当前轮修正 find 的 name。

评分指出的失败位置/原因：

```text
"Model response execution results so far does not contain all the ground truth response execution results for turn 0."
```


缺少的执行返回：

```text
["{\"matches\": [\"./student_record.txt\"]}"]
```

### QeRL

第一轮以 student_records 查询后停止；下一轮得到文件名提示才重新 find。

评分指出的失败位置/原因：

```text
"Model response execution results so far does not contain all the ground truth response execution results for turn 0."
```


缺少的执行返回：

```text
["{\"matches\": [\"./student_record.txt\"]}"]
```

