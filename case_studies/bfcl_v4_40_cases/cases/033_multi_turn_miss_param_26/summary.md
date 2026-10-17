# Case 033 — multi_turn_miss_param_26

## 原始任务

第 1 轮：

Could you kindly navigate to the temporary directory and list all the files available there right in the terminal for me? I would like to quickly skim through them and all the hidden files.

第 2 轮：

What's inside of a file?

第 3 轮：

It is the last file displayed.

第 4 轮：

Create a docx file with the same name as the previosu file but changing the format, they should also have the same content.

完整工具定义、初始状态及其他任务字段见 task.json。

## 七种方法的实际表现

### BF16：通过

实际任务调用 10 次；[完整 CoT 和工具返回](BF16/cot_and_actions.txt)。

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
        "folder": "/tmp"
      }
    }
  },
  {
    "user_turn": 1,
    "action_in_turn": 2,
    "message_index": 6,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_cd",
      "arguments": {
        "folder": "temp"
      }
    }
  },
  {
    "user_turn": 1,
    "action_in_turn": 3,
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
    "user_turn": 1,
    "action_in_turn": 4,
    "message_index": 10,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_ls",
      "arguments": {
        "a": true
      }
    }
  },
  {
    "user_turn": 1,
    "action_in_turn": 5,
    "message_index": 12,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_cd",
      "arguments": {
        "folder": "tmp"
      }
    }
  },
  {
    "user_turn": 1,
    "action_in_turn": 6,
    "message_index": 14,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_ls",
      "arguments": {
        "a": true
      }
    }
  },
  {
    "user_turn": 3,
    "action_in_turn": 1,
    "message_index": 20,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_cat",
      "arguments": {
        "file_name": "file3.txt"
      }
    }
  },
  {
    "user_turn": 4,
    "action_in_turn": 1,
    "message_index": 24,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_echo",
      "arguments": {
        "content": "Nothing important here. Yet another line.",
        "file_name": "file3.docx"
      }
    }
  },
  {
    "user_turn": 4,
    "action_in_turn": 2,
    "message_index": 26,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_touch",
      "arguments": {
        "file_name": "file3.docx"
      }
    }
  },
  {
    "user_turn": 4,
    "action_in_turn": 3,
    "message_index": 28,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_echo",
      "arguments": {
        "content": "Nothing important here. Yet another line.",
        "file_name": "file3.docx"
      }
    }
  }
]
```

</details>

### Ours：通过

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
      "name": "mcp_tool_cd",
      "arguments": {
        "folder": "tmp"
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
    "user_turn": 3,
    "action_in_turn": 1,
    "message_index": 12,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_cat",
      "arguments": {
        "file_name": "file3.txt"
      }
    }
  },
  {
    "user_turn": 4,
    "action_in_turn": 1,
    "message_index": 16,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_echo",
      "arguments": {
        "content": "Nothing important here. Yet another line.",
        "file_name": "file3.docx"
      }
    }
  },
  {
    "user_turn": 4,
    "action_in_turn": 2,
    "message_index": 18,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_touch",
      "arguments": {
        "file_name": "file3.docx"
      }
    }
  },
  {
    "user_turn": 4,
    "action_in_turn": 3,
    "message_index": 20,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_echo",
      "arguments": {
        "content": "Nothing important here. Yet another line.",
        "file_name": "file3.docx"
      }
    }
  }
]
```

</details>

### GPTQ：未通过

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
      "name": "mcp_tool_cd",
      "arguments": {
        "folder": "/tmp"
      }
    }
  },
  {
    "user_turn": 1,
    "action_in_turn": 2,
    "message_index": 6,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_pwd",
      "arguments": {}
    }
  },
  {
    "user_turn": 1,
    "action_in_turn": 3,
    "message_index": 8,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_cd",
      "arguments": {
        "folder": "tmp"
      }
    }
  },
  {
    "user_turn": 1,
    "action_in_turn": 4,
    "message_index": 10,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_ls",
      "arguments": {
        "a": true
      }
    }
  },
  {
    "user_turn": 3,
    "action_in_turn": 1,
    "message_index": 16,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_cat",
      "arguments": {
        "file_name": "file3.txt"
      }
    }
  },
  {
    "user_turn": 4,
    "action_in_turn": 1,
    "message_index": 20,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_cp",
      "arguments": {
        "source": "file3.txt",
        "destination": "file3.docx"
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
      "name": "mcp_tool_cd",
      "arguments": {
        "folder": "temp"
      }
    }
  },
  {
    "user_turn": 1,
    "action_in_turn": 2,
    "message_index": 6,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_mkdir",
      "arguments": {
        "dir_name": "temp"
      }
    }
  },
  {
    "user_turn": 1,
    "action_in_turn": 3,
    "message_index": 8,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_cd",
      "arguments": {
        "folder": "temp"
      }
    }
  },
  {
    "user_turn": 1,
    "action_in_turn": 4,
    "message_index": 10,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_ls",
      "arguments": {
        "a": true
      }
    }
  }
]
```

</details>

### BitDistiller：未通过

实际任务调用 6 次；[完整 CoT 和工具返回](BitDistiller/cot_and_actions.txt)。

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
        "folder": "tmp"
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
    "user_turn": 3,
    "action_in_turn": 1,
    "message_index": 12,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_cat",
      "arguments": {
        "file_name": "file3.txt"
      }
    }
  },
  {
    "user_turn": 4,
    "action_in_turn": 1,
    "message_index": 16,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_echo",
      "arguments": {
        "content": "Nothing important here.\nYet another line.",
        "file_name": "file3.docx"
      }
    }
  },
  {
    "user_turn": 4,
    "action_in_turn": 2,
    "message_index": 18,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_touch",
      "arguments": {
        "file_name": "file3.docx"
      }
    }
  },
  {
    "user_turn": 4,
    "action_in_turn": 3,
    "message_index": 20,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_echo",
      "arguments": {
        "content": "Nothing important here.\nYet another line.",
        "file_name": "file3.docx"
      }
    }
  }
]
```

</details>

### On-Policy QAD：未通过

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
      "name": "mcp_tool_cd",
      "arguments": {
        "folder": "/tmp"
      }
    }
  },
  {
    "user_turn": 1,
    "action_in_turn": 2,
    "message_index": 6,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_cd",
      "arguments": {
        "folder": "temp"
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
        "folder": "./tmp"
      }
    }
  },
  {
    "user_turn": 1,
    "action_in_turn": 2,
    "message_index": 6,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_cd",
      "arguments": {
        "folder": "/tmp"
      }
    }
  },
  {
    "user_turn": 3,
    "action_in_turn": 1,
    "message_index": 12,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_ls",
      "arguments": {
        "a": true
      }
    }
  },
  {
    "user_turn": 4,
    "action_in_turn": 1,
    "message_index": 16,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_cat",
      "arguments": {
        "file_name": "tmp"
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
    "field": "$.arguments.folder",
    "reference": "/tmp",
    "actual": "tmp"
  }
]
```

### GPTQ

最早动作差异：第 1 个用户轮，第 2 个任务动作；BF16 消息 6，本方法消息 6。

```json
[
  {
    "field": "$.arguments.folder",
    "reference": "temp",
    "actual": null,
    "reference_present": true,
    "actual_present": false
  },
  {
    "field": "$.name",
    "reference": "mcp_tool_cd",
    "actual": "mcp_tool_pwd"
  }
]
```

### EfficientQAT

最早动作差异：第 1 个用户轮，第 1 个任务动作；BF16 消息 4，本方法消息 4。

```json
[
  {
    "field": "$.arguments.folder",
    "reference": "/tmp",
    "actual": "temp"
  }
]
```

### BitDistiller

最早动作差异：第 1 个用户轮，第 1 个任务动作；BF16 消息 4，本方法消息 4。

```json
[
  {
    "field": "$.arguments.folder",
    "reference": "/tmp",
    "actual": "tmp"
  }
]
```

### On-Policy QAD

最早动作差异：第 1 个用户轮，第 3 个任务动作；BF16 消息 8，本方法消息 None。

该位置没有对应任务调用；该轮 assistant 消息为 [2, 4, 6, 8]。

```json
[
  {
    "field": "$",
    "reference": {
      "wrapper": "call_tool",
      "name": "mcp_tool_find",
      "arguments": {
        "path": ".",
        "name": "temp"
      }
    },
    "actual": null
  }
]
```

### QeRL

最早动作差异：第 1 个用户轮，第 1 个任务动作；BF16 消息 4，本方法消息 4。

```json
[
  {
    "field": "$.arguments.folder",
    "reference": "/tmp",
    "actual": "./tmp"
  }
]
```

## 失败原因

部分方法未能进入 tmp 并完成列表查询；另一些已完成前面步骤，但新建同内容 docx 的执行结果或文件状态不符。

### GPTQ

评分指出的失败位置/原因：

```text
"Model response execution results so far does not contain all the ground truth response execution results for turn 3."
```


缺少的执行返回：

```text
["None", "None"]
```

### EfficientQAT

评分指出的失败位置/原因：

```text
"Model instance for GorillaFileSystem does not match the state with ground truth instance."
```

- 状态字段 `root`：实际 "<Directory: alex, Parent: None, Contents: {'tmp': <Directory: tmp, Parent: alex, Contents: {'file1.txt': <<File: file1.txt, Content: This is some important data. Another line of text.>>, 'file2.txt': <<File: file2.txt, Content: Just some random text. More important data here.>>, 'file3.txt': <<File: file3.txt, Content: Nothing important here. Yet another line.>>}>, 'temp': <Directory: temp, Parent: alex, Contents: {}>}>"；参考 "<Directory: alex, Parent: None, Contents: {'tmp': <Directory: tmp, Parent: alex, Contents: {'file1.txt': <<File: file1.txt, Content: This is some important data. Another line of text.>>, 'file2.txt': <<File: file2.txt, Content: Just some random text. More important data here.>>, 'file3.txt': <<File: file3.txt, Content: Nothing important here. Yet another line.>>}>}>"。
### BitDistiller

评分指出的失败位置/原因：

```text
"Model instance for GorillaFileSystem does not match the state with ground truth instance."
```

- 状态字段 `root`：实际 "<Directory: alex, Parent: None, Contents: {'tmp': <Directory: tmp, Parent: alex, Contents: {'file1.txt': <<File: file1.txt, Content: This is some important data. Another line of text.>>, 'file2.txt': <<File: file2.txt, Content: Just some random text. More important data here.>>, 'file3.txt': <<File: file3.txt, Content: Nothing important here. Yet another line.>>, 'file3.docx': <<File: file3.docx, Content: Nothing important here.\nYet another line.>>}>}>"；参考 "<Directory: alex, Parent: None, Contents: {'tmp': <Directory: tmp, Parent: alex, Contents: {'file1.txt': <<File: file1.txt, Content: This is some important data. Another line of text.>>, 'file2.txt': <<File: file2.txt, Content: Just some random text. More important data here.>>, 'file3.txt': <<File: file3.txt, Content: Nothing important here. Yet another line.>>, 'file3.docx': <<File: file3.docx, Content: Nothing important here. Yet another line.>>}>}>"。
### On-Policy QAD

评分指出的失败位置/原因：

```text
"Model response execution results so far does not contain all the ground truth response execution results for turn 0."
```


缺少的执行返回：

```text
["{\"current_working_directory\": \"tmp\"}", "{\"current_directory_content\": [\"file1.txt\", \"file2.txt\", \"file3.txt\"]}"]
```

### QeRL

评分指出的失败位置/原因：

```text
"Model response execution results so far does not contain all the ground truth response execution results for turn 0."
```


缺少的执行返回：

```text
["{\"current_working_directory\": \"tmp\"}", "{\"current_directory_content\": [\"file1.txt\", \"file2.txt\", \"file3.txt\"]}"]
```

