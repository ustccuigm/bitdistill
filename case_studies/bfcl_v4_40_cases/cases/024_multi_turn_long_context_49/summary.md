# Case 024 — multi_turn_long_context_49

## 原始任务

第 1 轮：

Within the temp directory, could you list all the current files directly in the terminal including all the hidden files, ensuring we maintain the present directory structure intact and refrain from generating any additional directories or files?

第 2 轮：

Select the third file displayed in that directory and meticulously reorder its contents alphabetically. Proceed to display only the last 10 lines once you've done this.

第 3 轮：

For that same third file, could you determine the total number of lines it holds?

第 4 轮：

In your experience, could you perform a precise computation of 2 to determine the base 10 logarithm for the number of line?

完整工具定义、初始状态及其他任务字段见 task.json。

## 七种方法的实际表现

### BF16：通过

实际任务调用 6 次；[完整 CoT 和工具返回](BF16/cot_and_actions.txt)。

<details><summary>实际动作序列</summary>

```json
[
  {
    "user_turn": 1,
    "action_in_turn": 1,
    "message_index": 4,
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
    "message_index": 8,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_sort",
      "arguments": {
        "file_name": "file3.txt"
      }
    }
  },
  {
    "user_turn": 2,
    "action_in_turn": 2,
    "message_index": 10,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_tail",
      "arguments": {
        "file_name": "file3.txt",
        "lines": 10
      }
    }
  },
  {
    "user_turn": 3,
    "action_in_turn": 1,
    "message_index": 14,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_wc",
      "arguments": {
        "file_name": "file3.txt",
        "mode": "l"
      }
    }
  },
  {
    "user_turn": 4,
    "action_in_turn": 1,
    "message_index": 18,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_logarithm",
      "arguments": {
        "value": 20,
        "base": 10,
        "precision": 4
      }
    }
  },
  {
    "user_turn": 4,
    "action_in_turn": 2,
    "message_index": 20,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_logarithm",
      "arguments": {
        "value": 20,
        "base": 10,
        "precision": 2
      }
    }
  }
]
```

</details>

### Ours：通过

实际任务调用 7 次；[完整 CoT 和工具返回](Ours/cot_and_actions.txt)。

<details><summary>实际动作序列</summary>

```json
[
  {
    "user_turn": 1,
    "action_in_turn": 1,
    "message_index": 4,
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
    "message_index": 8,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_sort",
      "arguments": {
        "file_name": "file3.txt"
      }
    }
  },
  {
    "user_turn": 2,
    "action_in_turn": 2,
    "message_index": 10,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_tail",
      "arguments": {
        "file_name": "file3.txt",
        "lines": 10
      }
    }
  },
  {
    "user_turn": 3,
    "action_in_turn": 1,
    "message_index": 14,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_wc",
      "arguments": {
        "file_name": "file3.txt",
        "mode": "l"
      }
    }
  },
  {
    "user_turn": 4,
    "action_in_turn": 1,
    "message_index": 18,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_logarithm",
      "arguments": {
        "value": 20,
        "base": 10,
        "precision": 4
      }
    }
  },
  {
    "user_turn": 4,
    "action_in_turn": 2,
    "message_index": 20,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_logarithm",
      "arguments": {
        "value": 20,
        "base": 10,
        "precision": 4
      }
    }
  },
  {
    "user_turn": 4,
    "action_in_turn": 3,
    "message_index": 22,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_logarithm",
      "arguments": {
        "value": 20,
        "base": 10,
        "precision": 2
      }
    }
  }
]
```

</details>

### GPTQ：未通过

实际任务调用 5 次；[完整 CoT 和工具返回](GPTQ/cot_and_actions.txt)。

<details><summary>实际动作序列</summary>

```json
[
  {
    "user_turn": 1,
    "action_in_turn": 1,
    "message_index": 4,
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
    "message_index": 8,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_sort",
      "arguments": {
        "file_name": "file3.txt"
      }
    }
  },
  {
    "user_turn": 2,
    "action_in_turn": 2,
    "message_index": 10,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_tail",
      "arguments": {
        "file_name": "file3.txt",
        "lines": 10
      }
    }
  },
  {
    "user_turn": 3,
    "action_in_turn": 1,
    "message_index": 14,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_wc",
      "arguments": {
        "file_name": "file3.txt",
        "mode": "l"
      }
    }
  },
  {
    "user_turn": 4,
    "action_in_turn": 1,
    "message_index": 18,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_logarithm",
      "arguments": {
        "value": 20,
        "base": 10,
        "precision": 4
      }
    }
  }
]
```

</details>

### EfficientQAT：未通过

实际任务调用 4 次；[完整 CoT 和工具返回](EfficientQAT/cot_and_actions.txt)。

<details><summary>实际动作序列</summary>

```json
[
  {
    "user_turn": 1,
    "action_in_turn": 1,
    "message_index": 4,
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
    "message_index": 8,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_sort",
      "arguments": {
        "file_name": "file3.txt"
      }
    }
  },
  {
    "user_turn": 3,
    "action_in_turn": 1,
    "message_index": 12,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_wc",
      "arguments": {
        "file_name": "file3.txt",
        "mode": "l"
      }
    }
  },
  {
    "user_turn": 4,
    "action_in_turn": 1,
    "message_index": 16,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_logarithm",
      "arguments": {
        "value": 20,
        "base": 10,
        "precision": 4
      }
    }
  }
]
```

</details>

### BitDistiller：未通过

实际任务调用 4 次；[完整 CoT 和工具返回](BitDistiller/cot_and_actions.txt)。

<details><summary>实际动作序列</summary>

```json
[
  {
    "user_turn": 1,
    "action_in_turn": 1,
    "message_index": 4,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_cd",
      "arguments": {
        "folder": "temp"
      }
    }
  },
  {
    "user_turn": 4,
    "action_in_turn": 1,
    "message_index": 12,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_logarithm",
      "arguments": {
        "value": 2,
        "base": 10,
        "precision": 5
      }
    }
  },
  {
    "user_turn": 4,
    "action_in_turn": 2,
    "message_index": 14,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_logarithm",
      "arguments": {
        "value": 2,
        "base": 10,
        "precision": "5"
      }
    }
  },
  {
    "user_turn": 4,
    "action_in_turn": 3,
    "message_index": 16,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_logarithm",
      "arguments": {
        "value": 2,
        "base": 10,
        "precision": 5
      }
    }
  }
]
```

</details>

### On-Policy QAD：未通过

实际任务调用 7 次；[完整 CoT 和工具返回](On-Policy%20QAD/cot_and_actions.txt)。

<details><summary>实际动作序列</summary>

```json
[
  {
    "user_turn": 1,
    "action_in_turn": 1,
    "message_index": 4,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_cd",
      "arguments": {
        "folder": "temp"
      }
    }
  },
  {
    "user_turn": 2,
    "action_in_turn": 1,
    "message_index": 8,
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
    "action_in_turn": 2,
    "message_index": 10,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_sort",
      "arguments": {
        "file_name": "file3.txt"
      }
    }
  },
  {
    "user_turn": 2,
    "action_in_turn": 3,
    "message_index": 12,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_tail",
      "arguments": {
        "file_name": "file3.txt",
        "lines": 10
      }
    }
  },
  {
    "user_turn": 3,
    "action_in_turn": 1,
    "message_index": 16,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_wc",
      "arguments": {
        "file_name": "file3.txt",
        "mode": "l"
      }
    }
  },
  {
    "user_turn": 4,
    "action_in_turn": 1,
    "message_index": 20,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_logarithm",
      "arguments": {
        "value": 20,
        "base": 10,
        "precision": 4
      }
    }
  },
  {
    "user_turn": 4,
    "action_in_turn": 2,
    "message_index": 22,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_logarithm",
      "arguments": {
        "value": 20,
        "base": 10,
        "precision": 2
      }
    }
  }
]
```

</details>

### QeRL：未通过

实际任务调用 4 次；[完整 CoT 和工具返回](QeRL/cot_and_actions.txt)。

<details><summary>实际动作序列</summary>

```json
[
  {
    "user_turn": 1,
    "action_in_turn": 1,
    "message_index": 4,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_cd",
      "arguments": {
        "folder": "temp"
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
        "name": "temp"
      }
    }
  },
  {
    "user_turn": 2,
    "action_in_turn": 2,
    "message_index": 10,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_find",
      "arguments": {
        "path": ".",
        "name": "tmp"
      }
    }
  },
  {
    "user_turn": 4,
    "action_in_turn": 1,
    "message_index": 16,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_logarithm",
      "arguments": {
        "value": 2,
        "base": 10,
        "precision": 1e-06
      }
    }
  }
]
```

</details>

## 分歧位置

消息编号从 0 开始，用户轮和动作编号从 1 开始。按同一用户轮的任务动作序号与 BF16 比较，忽略 list_tools。最早动作差异不一定就是失败起点：正确的工具顺序、补救步骤也可能不同；评分失败位置另见下一节。

### Ours

最早动作差异：第 4 个用户轮，第 2 个任务动作；BF16 消息 20，本方法消息 20。

```json
[
  {
    "field": "$.arguments.precision",
    "reference": 2,
    "actual": 4
  }
]
```

### GPTQ

最早动作差异：第 4 个用户轮，第 2 个任务动作；BF16 消息 20，本方法消息 None。

该位置没有对应任务调用；该轮 assistant 消息为 [18, 20]。

```json
[
  {
    "field": "$",
    "reference": {
      "wrapper": "call_tool",
      "name": "mcp_tool_logarithm",
      "arguments": {
        "value": 20,
        "base": 10,
        "precision": 2
      }
    },
    "actual": null
  }
]
```

### EfficientQAT

最早动作差异：第 2 个用户轮，第 2 个任务动作；BF16 消息 10，本方法消息 None。

该位置没有对应任务调用；该轮 assistant 消息为 [8, 10]。

```json
[
  {
    "field": "$",
    "reference": {
      "wrapper": "call_tool",
      "name": "mcp_tool_tail",
      "arguments": {
        "file_name": "file3.txt",
        "lines": 10
      }
    },
    "actual": null
  }
]
```

### BitDistiller

最早动作差异：第 1 个用户轮，第 1 个任务动作；BF16 消息 4，本方法消息 4。

```json
[
  {
    "field": "$.arguments.a",
    "reference": true,
    "actual": null,
    "reference_present": true,
    "actual_present": false
  },
  {
    "field": "$.arguments.folder",
    "reference": null,
    "actual": "temp",
    "reference_present": false,
    "actual_present": true
  },
  {
    "field": "$.name",
    "reference": "mcp_tool_ls",
    "actual": "mcp_tool_cd"
  }
]
```

### On-Policy QAD

最早动作差异：第 1 个用户轮，第 1 个任务动作；BF16 消息 4，本方法消息 4。

```json
[
  {
    "field": "$.arguments.a",
    "reference": true,
    "actual": null,
    "reference_present": true,
    "actual_present": false
  },
  {
    "field": "$.arguments.folder",
    "reference": null,
    "actual": "temp",
    "reference_present": false,
    "actual_present": true
  },
  {
    "field": "$.name",
    "reference": "mcp_tool_ls",
    "actual": "mcp_tool_cd"
  }
]
```

### QeRL

最早动作差异：第 1 个用户轮，第 1 个任务动作；BF16 消息 4，本方法消息 4。

```json
[
  {
    "field": "$.arguments.a",
    "reference": true,
    "actual": null,
    "reference_present": true,
    "actual_present": false
  },
  {
    "field": "$.arguments.folder",
    "reference": null,
    "actual": "temp",
    "reference_present": false,
    "actual_present": true
  },
  {
    "field": "$.name",
    "reference": "mcp_tool_ls",
    "actual": "mcp_tool_cd"
  }
]
```

## 失败原因

不同 baseline 分别缺少目录列表、文件末尾内容或最后的计算结果；评分按轮检查执行返回，不能将它们归为同一个数学错误。

### GPTQ

评分指出的失败位置/原因：

```text
"Model response execution results so far does not contain all the ground truth response execution results for turn 3."
```


缺少的执行返回：

```text
["{'result': mpf('1.3027')}"]
```

### EfficientQAT

评分指出的失败位置/原因：

```text
"Model response execution results so far does not contain all the ground truth response execution results for turn 1."
```


缺少的执行返回：

```text
["{\"last_lines\": \"Kiwi\\nPlum\\nPear\\nFig\\nDate\\nCoconut\\nPineapple\\nPapaya\\nGuava\\nLychee\"}"]
```

### BitDistiller

评分指出的失败位置/原因：

```text
"Model response execution results so far does not contain all the ground truth response execution results for turn 0."
```


缺少的执行返回：

```text
["{\"current_directory_content\": [\"file1.txt\", \"file2.txt\", \"file3.txt\", \"image_344822349461074042.jpg\", \"image_8219547643081662353.jpg\", \"image_5421509146842474663.jpg\", \"image_185391401034246046.jpg\", \"image_6824007961180780019.jpg\", \"image_2994974694593273051.jpg\", \"image_2537728455072851196.jpg\", \"image_2164918946836800275.jpg\", \"image_1745133864906284051.jpg\", \"image_7707563551789432679.jpg\", \"image_8190489168166590809.jpg\", \"image_2385660725381355820.jpg\", \"image_4771211633166048374.jpg\", \"image_3443718094055823214.jpg\", \"image_6838087561356843690.jpg\", \"image_605952633285970710.jpg\", \"image_6341510244180179744.jpg\", \"image_4119241148692325954.jpg\", \"image_5651066601163181955.jpg\", \"image_3747091333751395055.jpg\", \"image_4623743619379194431.jpg\", \"image_5072742684386583099.jpg\", \"image_1978458056362464778.jpg\", \"image_3090346927968358019.jpg\", \"image_7193806748674265039.jpg\", \"image_7169516574395086720.jpg\", \"image_8618240224293913315.jpg\", \"image_5514683852355062444.jpg\", \"image_8749630317332649147.jpg\", \"image_1912245706439755759.jpg\"]}"]
```

### On-Policy QAD

评分指出的失败位置/原因：

```text
"Model response execution results so far does not contain all the ground truth response execution results for turn 0."
```


缺少的执行返回：

```text
["{\"current_directory_content\": [\"file1.txt\", \"file2.txt\", \"file3.txt\", \"image_344822349461074042.jpg\", \"image_8219547643081662353.jpg\", \"image_5421509146842474663.jpg\", \"image_185391401034246046.jpg\", \"image_6824007961180780019.jpg\", \"image_2994974694593273051.jpg\", \"image_2537728455072851196.jpg\", \"image_2164918946836800275.jpg\", \"image_1745133864906284051.jpg\", \"image_7707563551789432679.jpg\", \"image_8190489168166590809.jpg\", \"image_2385660725381355820.jpg\", \"image_4771211633166048374.jpg\", \"image_3443718094055823214.jpg\", \"image_6838087561356843690.jpg\", \"image_605952633285970710.jpg\", \"image_6341510244180179744.jpg\", \"image_4119241148692325954.jpg\", \"image_5651066601163181955.jpg\", \"image_3747091333751395055.jpg\", \"image_4623743619379194431.jpg\", \"image_5072742684386583099.jpg\", \"image_1978458056362464778.jpg\", \"image_3090346927968358019.jpg\", \"image_7193806748674265039.jpg\", \"image_7169516574395086720.jpg\", \"image_8618240224293913315.jpg\", \"image_5514683852355062444.jpg\", \"image_8749630317332649147.jpg\", \"image_1912245706439755759.jpg\"]}"]
```

### QeRL

评分指出的失败位置/原因：

```text
"Model response execution results so far does not contain all the ground truth response execution results for turn 0."
```


缺少的执行返回：

```text
["{\"current_directory_content\": [\"file1.txt\", \"file2.txt\", \"file3.txt\", \"image_344822349461074042.jpg\", \"image_8219547643081662353.jpg\", \"image_5421509146842474663.jpg\", \"image_185391401034246046.jpg\", \"image_6824007961180780019.jpg\", \"image_2994974694593273051.jpg\", \"image_2537728455072851196.jpg\", \"image_2164918946836800275.jpg\", \"image_1745133864906284051.jpg\", \"image_7707563551789432679.jpg\", \"image_8190489168166590809.jpg\", \"image_2385660725381355820.jpg\", \"image_4771211633166048374.jpg\", \"image_3443718094055823214.jpg\", \"image_6838087561356843690.jpg\", \"image_605952633285970710.jpg\", \"image_6341510244180179744.jpg\", \"image_4119241148692325954.jpg\", \"image_5651066601163181955.jpg\", \"image_3747091333751395055.jpg\", \"image_4623743619379194431.jpg\", \"image_5072742684386583099.jpg\", \"image_1978458056362464778.jpg\", \"image_3090346927968358019.jpg\", \"image_7193806748674265039.jpg\", \"image_7169516574395086720.jpg\", \"image_8618240224293913315.jpg\", \"image_5514683852355062444.jpg\", \"image_8749630317332649147.jpg\", \"image_1912245706439755759.jpg\"]}"]
```

