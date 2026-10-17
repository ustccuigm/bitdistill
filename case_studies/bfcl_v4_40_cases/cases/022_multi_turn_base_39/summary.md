# Case 022 — multi_turn_base_39

## 原始任务

第 1 轮：

I need you to set up a fresh folder named 'WebDevProjects' wherever you're currently working.

第 2 轮：

Enter the folder and populate the 'WebDevProjects' folder with 3 files:, 'styles.css',  'index.html', and 'script.js' with content 'Hello World!','Hi World!', 'Halo World!' in each.

第 3 轮：

What's the second file name by system order? Don't list out hidden files.

第 4 轮：

Can you display the content of the first file by system order?

完整工具定义、初始状态及其他任务字段见 task.json。

## 七种方法的实际表现

### BF16：通过

根据文件不存在的反馈，创建文件后补写，之后 ls 并读取 styles.css。

实际任务调用 13 次；[完整 CoT 和工具返回](BF16/cot_and_actions.txt)。

<details><summary>实际动作序列</summary>

```json
[
  {
    "user_turn": 1,
    "action_in_turn": 1,
    "message_index": 4,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_mkdir",
      "arguments": {
        "dir_name": "WebDevProjects"
      }
    }
  },
  {
    "user_turn": 2,
    "action_in_turn": 1,
    "message_index": 8,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_cd",
      "arguments": {
        "folder": "WebDevProjects"
      }
    }
  },
  {
    "user_turn": 2,
    "action_in_turn": 2,
    "message_index": 10,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_echo",
      "arguments": {
        "content": "Hello World!",
        "file_name": "styles.css"
      }
    }
  },
  {
    "user_turn": 2,
    "action_in_turn": 3,
    "message_index": 12,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_touch",
      "arguments": {
        "file_name": "styles.css"
      }
    }
  },
  {
    "user_turn": 2,
    "action_in_turn": 4,
    "message_index": 14,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_echo",
      "arguments": {
        "content": "Hello World!",
        "file_name": "styles.css"
      }
    }
  },
  {
    "user_turn": 2,
    "action_in_turn": 5,
    "message_index": 16,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_echo",
      "arguments": {
        "content": "Hi World!",
        "file_name": "index.html"
      }
    }
  },
  {
    "user_turn": 2,
    "action_in_turn": 6,
    "message_index": 18,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_touch",
      "arguments": {
        "file_name": "index.html"
      }
    }
  },
  {
    "user_turn": 2,
    "action_in_turn": 7,
    "message_index": 20,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_echo",
      "arguments": {
        "content": "Hi World!",
        "file_name": "index.html"
      }
    }
  },
  {
    "user_turn": 2,
    "action_in_turn": 8,
    "message_index": 22,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_echo",
      "arguments": {
        "content": "Halo World!",
        "file_name": "script.js"
      }
    }
  },
  {
    "user_turn": 2,
    "action_in_turn": 9,
    "message_index": 24,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_touch",
      "arguments": {
        "file_name": "script.js"
      }
    }
  },
  {
    "user_turn": 2,
    "action_in_turn": 10,
    "message_index": 26,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_echo",
      "arguments": {
        "content": "Halo World!",
        "file_name": "script.js"
      }
    }
  },
  {
    "user_turn": 3,
    "action_in_turn": 1,
    "message_index": 30,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_ls",
      "arguments": {
        "a": false
      }
    }
  },
  {
    "user_turn": 4,
    "action_in_turn": 1,
    "message_index": 34,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_cat",
      "arguments": {
        "file_name": "styles.css"
      }
    }
  }
]
```

</details>

### Ours：通过

补齐每次创建后的写入，并执行 ls 与正确的首文件读取。

实际任务调用 11 次；[完整 CoT 和工具返回](Ours/cot_and_actions.txt)。

<details><summary>实际动作序列</summary>

```json
[
  {
    "user_turn": 1,
    "action_in_turn": 1,
    "message_index": 4,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_mkdir",
      "arguments": {
        "dir_name": "WebDevProjects"
      }
    }
  },
  {
    "user_turn": 2,
    "action_in_turn": 1,
    "message_index": 8,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_cd",
      "arguments": {
        "folder": "WebDevProjects"
      }
    }
  },
  {
    "user_turn": 2,
    "action_in_turn": 2,
    "message_index": 10,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_echo",
      "arguments": {
        "content": "Hello World!",
        "file_name": "styles.css"
      }
    }
  },
  {
    "user_turn": 2,
    "action_in_turn": 3,
    "message_index": 12,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_touch",
      "arguments": {
        "file_name": "styles.css"
      }
    }
  },
  {
    "user_turn": 2,
    "action_in_turn": 4,
    "message_index": 14,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_echo",
      "arguments": {
        "content": "Hello World!",
        "file_name": "styles.css"
      }
    }
  },
  {
    "user_turn": 2,
    "action_in_turn": 5,
    "message_index": 16,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_touch",
      "arguments": {
        "file_name": "index.html"
      }
    }
  },
  {
    "user_turn": 2,
    "action_in_turn": 6,
    "message_index": 18,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_echo",
      "arguments": {
        "content": "Hi World!",
        "file_name": "index.html"
      }
    }
  },
  {
    "user_turn": 2,
    "action_in_turn": 7,
    "message_index": 20,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_touch",
      "arguments": {
        "file_name": "script.js"
      }
    }
  },
  {
    "user_turn": 2,
    "action_in_turn": 8,
    "message_index": 22,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_echo",
      "arguments": {
        "content": "Halo World!",
        "file_name": "script.js"
      }
    }
  },
  {
    "user_turn": 3,
    "action_in_turn": 1,
    "message_index": 26,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_ls",
      "arguments": {}
    }
  },
  {
    "user_turn": 4,
    "action_in_turn": 1,
    "message_index": 30,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_cat",
      "arguments": {
        "file_name": "styles.css"
      }
    }
  }
]
```

</details>

### GPTQ：未通过

首次写入便把 styles.css 内容设成 Hi World!，随后把 Hello World! 写入 index.html。

实际任务调用 11 次；[完整 CoT 和工具返回](GPTQ/cot_and_actions.txt)。

<details><summary>实际动作序列</summary>

```json
[
  {
    "user_turn": 1,
    "action_in_turn": 1,
    "message_index": 4,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_mkdir",
      "arguments": {
        "dir_name": "WebDevProjects"
      }
    }
  },
  {
    "user_turn": 2,
    "action_in_turn": 1,
    "message_index": 8,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_cd",
      "arguments": {
        "folder": "WebDevProjects"
      }
    }
  },
  {
    "user_turn": 2,
    "action_in_turn": 2,
    "message_index": 10,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_echo",
      "arguments": {
        "content": "Hi World!",
        "file_name": "styles.css"
      }
    }
  },
  {
    "user_turn": 2,
    "action_in_turn": 3,
    "message_index": 12,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_touch",
      "arguments": {
        "file_name": "styles.css"
      }
    }
  },
  {
    "user_turn": 2,
    "action_in_turn": 4,
    "message_index": 14,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_echo",
      "arguments": {
        "content": "Hi World!",
        "file_name": "styles.css"
      }
    }
  },
  {
    "user_turn": 2,
    "action_in_turn": 5,
    "message_index": 16,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_touch",
      "arguments": {
        "file_name": "index.html"
      }
    }
  },
  {
    "user_turn": 2,
    "action_in_turn": 6,
    "message_index": 18,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_echo",
      "arguments": {
        "content": "Hello World!",
        "file_name": "index.html"
      }
    }
  },
  {
    "user_turn": 2,
    "action_in_turn": 7,
    "message_index": 20,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_touch",
      "arguments": {
        "file_name": "script.js"
      }
    }
  },
  {
    "user_turn": 2,
    "action_in_turn": 8,
    "message_index": 22,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_echo",
      "arguments": {
        "content": "Halo World!",
        "file_name": "script.js"
      }
    }
  },
  {
    "user_turn": 3,
    "action_in_turn": 1,
    "message_index": 26,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_ls",
      "arguments": {
        "a": false
      }
    }
  },
  {
    "user_turn": 4,
    "action_in_turn": 1,
    "message_index": 30,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_cat",
      "arguments": {
        "file_name": "styles.css"
      }
    }
  }
]
```

</details>

### EfficientQAT：未通过

前两个文件的 echo 失败后只创建空文件，没有重新写入。

实际任务调用 11 次；[完整 CoT 和工具返回](EfficientQAT/cot_and_actions.txt)。

<details><summary>实际动作序列</summary>

```json
[
  {
    "user_turn": 1,
    "action_in_turn": 1,
    "message_index": 4,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_mkdir",
      "arguments": {
        "dir_name": "WebDevProjects"
      }
    }
  },
  {
    "user_turn": 2,
    "action_in_turn": 1,
    "message_index": 8,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_cd",
      "arguments": {
        "folder": "WebDevProjects"
      }
    }
  },
  {
    "user_turn": 2,
    "action_in_turn": 2,
    "message_index": 10,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_echo",
      "arguments": {
        "content": "Hello World!",
        "file_name": "styles.css"
      }
    }
  },
  {
    "user_turn": 2,
    "action_in_turn": 3,
    "message_index": 12,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_touch",
      "arguments": {
        "file_name": "styles.css"
      }
    }
  },
  {
    "user_turn": 2,
    "action_in_turn": 4,
    "message_index": 14,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_echo",
      "arguments": {
        "content": "Hi World!",
        "file_name": "index.html"
      }
    }
  },
  {
    "user_turn": 2,
    "action_in_turn": 5,
    "message_index": 16,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_touch",
      "arguments": {
        "file_name": "index.html"
      }
    }
  },
  {
    "user_turn": 2,
    "action_in_turn": 6,
    "message_index": 18,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_echo",
      "arguments": {
        "content": "Halo World!",
        "file_name": "script.js"
      }
    }
  },
  {
    "user_turn": 2,
    "action_in_turn": 7,
    "message_index": 20,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_touch",
      "arguments": {
        "file_name": "script.js"
      }
    }
  },
  {
    "user_turn": 2,
    "action_in_turn": 8,
    "message_index": 22,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_echo",
      "arguments": {
        "content": "Halo World!",
        "file_name": "script.js"
      }
    }
  },
  {
    "user_turn": 3,
    "action_in_turn": 1,
    "message_index": 26,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_ls",
      "arguments": {
        "a": false
      }
    }
  },
  {
    "user_turn": 4,
    "action_in_turn": 1,
    "message_index": 30,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_cat",
      "arguments": {
        "file_name": "styles.css"
      }
    }
  }
]
```

</details>

### BitDistiller：未通过

touch index.html 后直接处理 script.js，漏掉中间的内容写入。

实际任务调用 11 次；[完整 CoT 和工具返回](BitDistiller/cot_and_actions.txt)。

<details><summary>实际动作序列</summary>

```json
[
  {
    "user_turn": 1,
    "action_in_turn": 1,
    "message_index": 4,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_mkdir",
      "arguments": {
        "dir_name": "WebDevProjects"
      }
    }
  },
  {
    "user_turn": 2,
    "action_in_turn": 1,
    "message_index": 8,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_cd",
      "arguments": {
        "folder": "WebDevProjects"
      }
    }
  },
  {
    "user_turn": 2,
    "action_in_turn": 2,
    "message_index": 10,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_echo",
      "arguments": {
        "content": "Hello World!",
        "file_name": "styles.css"
      }
    }
  },
  {
    "user_turn": 2,
    "action_in_turn": 3,
    "message_index": 12,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_touch",
      "arguments": {
        "file_name": "styles.css"
      }
    }
  },
  {
    "user_turn": 2,
    "action_in_turn": 4,
    "message_index": 14,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_echo",
      "arguments": {
        "content": "Hello World!",
        "file_name": "styles.css"
      }
    }
  },
  {
    "user_turn": 2,
    "action_in_turn": 5,
    "message_index": 16,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_touch",
      "arguments": {
        "file_name": "index.html"
      }
    }
  },
  {
    "user_turn": 2,
    "action_in_turn": 6,
    "message_index": 18,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_echo",
      "arguments": {
        "content": "Halo World!",
        "file_name": "script.js"
      }
    }
  },
  {
    "user_turn": 2,
    "action_in_turn": 7,
    "message_index": 20,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_touch",
      "arguments": {
        "file_name": "script.js"
      }
    }
  },
  {
    "user_turn": 2,
    "action_in_turn": 8,
    "message_index": 22,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_echo",
      "arguments": {
        "content": "Halo World!",
        "file_name": "script.js"
      }
    }
  },
  {
    "user_turn": 3,
    "action_in_turn": 1,
    "message_index": 26,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_ls",
      "arguments": {
        "a": false
      }
    }
  },
  {
    "user_turn": 4,
    "action_in_turn": 1,
    "message_index": 30,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_cat",
      "arguments": {
        "file_name": "styles.css"
      }
    }
  }
]
```

</details>

### On-Policy QAD：未通过

创建 index.html 和 script.js 后又写 styles.css，遗漏另外两次写入。

实际任务调用 9 次；[完整 CoT 和工具返回](On-Policy%20QAD/cot_and_actions.txt)。

<details><summary>实际动作序列</summary>

```json
[
  {
    "user_turn": 1,
    "action_in_turn": 1,
    "message_index": 4,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_mkdir",
      "arguments": {
        "dir_name": "WebDevProjects"
      }
    }
  },
  {
    "user_turn": 2,
    "action_in_turn": 1,
    "message_index": 8,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_cd",
      "arguments": {
        "folder": "WebDevProjects"
      }
    }
  },
  {
    "user_turn": 2,
    "action_in_turn": 2,
    "message_index": 10,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_echo",
      "arguments": {
        "content": "Hello World!",
        "file_name": "styles.css"
      }
    }
  },
  {
    "user_turn": 2,
    "action_in_turn": 3,
    "message_index": 12,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_touch",
      "arguments": {
        "file_name": "styles.css"
      }
    }
  },
  {
    "user_turn": 2,
    "action_in_turn": 4,
    "message_index": 14,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_echo",
      "arguments": {
        "content": "Hello World!",
        "file_name": "styles.css"
      }
    }
  },
  {
    "user_turn": 2,
    "action_in_turn": 5,
    "message_index": 16,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_touch",
      "arguments": {
        "file_name": "index.html"
      }
    }
  },
  {
    "user_turn": 2,
    "action_in_turn": 6,
    "message_index": 18,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_touch",
      "arguments": {
        "file_name": "script.js"
      }
    }
  },
  {
    "user_turn": 2,
    "action_in_turn": 7,
    "message_index": 20,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_echo",
      "arguments": {
        "content": "Hello World!",
        "file_name": "styles.css"
      }
    }
  },
  {
    "user_turn": 4,
    "action_in_turn": 1,
    "message_index": 26,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_cat",
      "arguments": {
        "file_name": "index.html"
      }
    }
  }
]
```

</details>

### QeRL：未通过

创建内容正确，后续没有 ls，读取的首个文件又选成 index.html。

实际任务调用 10 次；[完整 CoT 和工具返回](QeRL/cot_and_actions.txt)。

<details><summary>实际动作序列</summary>

```json
[
  {
    "user_turn": 1,
    "action_in_turn": 1,
    "message_index": 4,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_mkdir",
      "arguments": {
        "dir_name": "WebDevProjects"
      }
    }
  },
  {
    "user_turn": 2,
    "action_in_turn": 1,
    "message_index": 8,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_cd",
      "arguments": {
        "folder": "WebDevProjects"
      }
    }
  },
  {
    "user_turn": 2,
    "action_in_turn": 2,
    "message_index": 10,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_echo",
      "arguments": {
        "content": "Hello World!",
        "file_name": "styles.css"
      }
    }
  },
  {
    "user_turn": 2,
    "action_in_turn": 3,
    "message_index": 12,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_touch",
      "arguments": {
        "file_name": "styles.css"
      }
    }
  },
  {
    "user_turn": 2,
    "action_in_turn": 4,
    "message_index": 14,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_echo",
      "arguments": {
        "content": "Hello World!",
        "file_name": "styles.css"
      }
    }
  },
  {
    "user_turn": 2,
    "action_in_turn": 5,
    "message_index": 16,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_touch",
      "arguments": {
        "file_name": "index.html"
      }
    }
  },
  {
    "user_turn": 2,
    "action_in_turn": 6,
    "message_index": 18,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_echo",
      "arguments": {
        "content": "Hi World!",
        "file_name": "index.html"
      }
    }
  },
  {
    "user_turn": 2,
    "action_in_turn": 7,
    "message_index": 20,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_touch",
      "arguments": {
        "file_name": "script.js"
      }
    }
  },
  {
    "user_turn": 2,
    "action_in_turn": 8,
    "message_index": 22,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_echo",
      "arguments": {
        "content": "Halo World!",
        "file_name": "script.js"
      }
    }
  },
  {
    "user_turn": 4,
    "action_in_turn": 1,
    "message_index": 28,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_cat",
      "arguments": {
        "file_name": "index.html"
      }
    }
  }
]
```

</details>

## 分歧位置

消息编号从 0 开始，用户轮和动作编号从 1 开始。按同一用户轮的任务动作序号与 BF16 比较，忽略 list_tools。最早动作差异不一定就是失败起点：正确的工具顺序、补救步骤也可能不同；评分失败位置另见下一节。

### Ours

最早动作差异：第 2 个用户轮，第 5 个任务动作；BF16 消息 16，本方法消息 16。

```json
[
  {
    "field": "$.arguments.content",
    "reference": "Hi World!",
    "actual": null,
    "reference_present": true,
    "actual_present": false
  },
  {
    "field": "$.name",
    "reference": "mcp_tool_echo",
    "actual": "mcp_tool_touch"
  }
]
```

### GPTQ

最早动作差异：第 2 个用户轮，第 2 个任务动作；BF16 消息 10，本方法消息 10。

```json
[
  {
    "field": "$.arguments.content",
    "reference": "Hello World!",
    "actual": "Hi World!"
  }
]
```

### EfficientQAT

最早动作差异：第 2 个用户轮，第 4 个任务动作；BF16 消息 14，本方法消息 14。

```json
[
  {
    "field": "$.arguments.content",
    "reference": "Hello World!",
    "actual": "Hi World!"
  },
  {
    "field": "$.arguments.file_name",
    "reference": "styles.css",
    "actual": "index.html"
  }
]
```

### BitDistiller

最早动作差异：第 2 个用户轮，第 5 个任务动作；BF16 消息 16，本方法消息 16。

```json
[
  {
    "field": "$.arguments.content",
    "reference": "Hi World!",
    "actual": null,
    "reference_present": true,
    "actual_present": false
  },
  {
    "field": "$.name",
    "reference": "mcp_tool_echo",
    "actual": "mcp_tool_touch"
  }
]
```

### On-Policy QAD

最早动作差异：第 2 个用户轮，第 5 个任务动作；BF16 消息 16，本方法消息 16。

```json
[
  {
    "field": "$.arguments.content",
    "reference": "Hi World!",
    "actual": null,
    "reference_present": true,
    "actual_present": false
  },
  {
    "field": "$.name",
    "reference": "mcp_tool_echo",
    "actual": "mcp_tool_touch"
  }
]
```

### QeRL

最早动作差异：第 2 个用户轮，第 5 个任务动作；BF16 消息 16，本方法消息 16。

```json
[
  {
    "field": "$.arguments.content",
    "reference": "Hi World!",
    "actual": null,
    "reference_present": true,
    "actual_present": false
  },
  {
    "field": "$.name",
    "reference": "mcp_tool_echo",
    "actual": "mcp_tool_touch"
  }
]
```

## 失败原因

GPTQ 把 styles.css 和 index.html 的两段内容交换；EfficientQAT 在 echo 失败后只 touch 创建了前两个文件，没有补写内容；BitDistiller 漏写 index.html；On-Policy QAD 创建后只反复写 styles.css，另外两个文件仍为空。QeRL 的文件创建是正确的，但在用户要求按系统顺序查第二个文件时没有执行查询，且随后读取 index.html 而非该环境顺序中的首个 styles.css。BF16 和 Ours 均能在首次 echo 报文件不存在后补 touch、重做写入，完成全部文件和后续查询。不同 baseline 的首处分歧不全在同一轮，不能把 QeRL 描述成创建文件失败。

### GPTQ

首次写入便把 styles.css 内容设成 Hi World!，随后把 Hello World! 写入 index.html。

评分指出的失败位置/原因：

```text
"Model instance for GorillaFileSystem does not match the state with ground truth instance."
```

- 状态字段 `root`：实际 "<Directory: current_working_directory, Parent: None, Contents: {'WebDevProjects': <Directory: WebDevProjects, Parent: current_working_directory, Contents: {'styles.css': <<File: styles.css, Content: Hi World!>>, 'index.html': <<File: index.html, Content: Hello World!>>, 'script.js': <<File: script.js, Content: Halo World!>>}>}>"；参考 "<Directory: current_working_directory, Parent: None, Contents: {'WebDevProjects': <Directory: WebDevProjects, Parent: current_working_directory, Contents: {'styles.css': <<File: styles.css, Content: Hello World!>>, 'index.html': <<File: index.html, Content: Hi World!>>, 'script.js': <<File: script.js, Content: Halo World!>>}>}>"。
### EfficientQAT

前两个文件的 echo 失败后只创建空文件，没有重新写入。

评分指出的失败位置/原因：

```text
"Model instance for GorillaFileSystem does not match the state with ground truth instance."
```

- 状态字段 `root`：实际 "<Directory: current_working_directory, Parent: None, Contents: {'WebDevProjects': <Directory: WebDevProjects, Parent: current_working_directory, Contents: {'styles.css': <<File: styles.css, Content: >>, 'index.html': <<File: index.html, Content: >>, 'script.js': <<File: script.js, Content: Halo World!>>}>}>"；参考 "<Directory: current_working_directory, Parent: None, Contents: {'WebDevProjects': <Directory: WebDevProjects, Parent: current_working_directory, Contents: {'styles.css': <<File: styles.css, Content: Hello World!>>, 'index.html': <<File: index.html, Content: Hi World!>>, 'script.js': <<File: script.js, Content: Halo World!>>}>}>"。
### BitDistiller

touch index.html 后直接处理 script.js，漏掉中间的内容写入。

评分指出的失败位置/原因：

```text
"Model instance for GorillaFileSystem does not match the state with ground truth instance."
```

- 状态字段 `root`：实际 "<Directory: current_working_directory, Parent: None, Contents: {'WebDevProjects': <Directory: WebDevProjects, Parent: current_working_directory, Contents: {'styles.css': <<File: styles.css, Content: Hello World!>>, 'index.html': <<File: index.html, Content: >>, 'script.js': <<File: script.js, Content: Halo World!>>}>}>"；参考 "<Directory: current_working_directory, Parent: None, Contents: {'WebDevProjects': <Directory: WebDevProjects, Parent: current_working_directory, Contents: {'styles.css': <<File: styles.css, Content: Hello World!>>, 'index.html': <<File: index.html, Content: Hi World!>>, 'script.js': <<File: script.js, Content: Halo World!>>}>}>"。
### On-Policy QAD

创建 index.html 和 script.js 后又写 styles.css，遗漏另外两次写入。

评分指出的失败位置/原因：

```text
"Model instance for GorillaFileSystem does not match the state with ground truth instance."
```

- 状态字段 `root`：实际 "<Directory: current_working_directory, Parent: None, Contents: {'WebDevProjects': <Directory: WebDevProjects, Parent: current_working_directory, Contents: {'styles.css': <<File: styles.css, Content: Hello World!>>, 'index.html': <<File: index.html, Content: >>, 'script.js': <<File: script.js, Content: >>}>}>"；参考 "<Directory: current_working_directory, Parent: None, Contents: {'WebDevProjects': <Directory: WebDevProjects, Parent: current_working_directory, Contents: {'styles.css': <<File: styles.css, Content: Hello World!>>, 'index.html': <<File: index.html, Content: Hi World!>>, 'script.js': <<File: script.js, Content: Halo World!>>}>}>"。
### QeRL

创建内容正确，后续没有 ls，读取的首个文件又选成 index.html。

评分指出的失败位置/原因：

```text
"Model response list is empty for turn 2"
```

