# Case 023 — multi_turn_long_context_39

## 任务

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
      "name": "mcp_tool_pwd",
      "arguments": {}
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
        "file_name": "styles.css"
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
        "file_name": "styles.css"
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
        "content": "Hi World!",
        "file_name": "index.html"
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

### GPTQ：未通过

实际任务调用 13 次；[完整 CoT 和工具返回](GPTQ/cot_and_actions.txt)。

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
      "name": "mcp_tool_echo",
      "arguments": {
        "content": "Hello World!",
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
      "name": "mcp_tool_touch",
      "arguments": {
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
        "content": "Halo World!",
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
      "name": "m/core/tool/touch",
      "arguments": {
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

### EfficientQAT：未通过

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
    "user_turn": 4,
    "action_in_turn": 1,
    "message_index": 28,
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
    "action_in_turn": 2,
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
      "name": "mcp_tool_echo",
      "arguments": {
        "content": "Hello World!",
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
      "name": "mcp_tool_touch",
      "arguments": {
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
        "content": "Hello World!",
        "file_name": "styles.css"
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
      "name": "mcp_tool_touch",
      "arguments": {
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

实际任务调用 10 次；[完整 CoT 和工具返回](On-Policy%20QAD/cot_and_actions.txt)。

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
        "file_name": "styles.css"
      }
    }
  }
]
```

</details>

### QeRL：未通过

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

最早动作差异：第 2 个用户轮，第 3 个任务动作；BF16 消息 12，本方法消息 12。

```json
[
  {
    "field": "$.arguments.file_name",
    "reference": null,
    "actual": "styles.css",
    "reference_present": false,
    "actual_present": true
  },
  {
    "field": "$.name",
    "reference": "mcp_tool_pwd",
    "actual": "mcp_tool_touch"
  }
]
```

### GPTQ

最早动作差异：第 2 个用户轮，第 3 个任务动作；BF16 消息 12，本方法消息 12。

```json
[
  {
    "field": "$.arguments.content",
    "reference": null,
    "actual": "Hello World!",
    "reference_present": false,
    "actual_present": true
  },
  {
    "field": "$.arguments.file_name",
    "reference": null,
    "actual": "styles.css",
    "reference_present": false,
    "actual_present": true
  },
  {
    "field": "$.name",
    "reference": "mcp_tool_pwd",
    "actual": "mcp_tool_echo"
  }
]
```

### EfficientQAT

最早动作差异：第 2 个用户轮，第 3 个任务动作；BF16 消息 12，本方法消息 12。

```json
[
  {
    "field": "$.arguments.file_name",
    "reference": null,
    "actual": "styles.css",
    "reference_present": false,
    "actual_present": true
  },
  {
    "field": "$.name",
    "reference": "mcp_tool_pwd",
    "actual": "mcp_tool_touch"
  }
]
```

### BitDistiller

最早动作差异：第 2 个用户轮，第 3 个任务动作；BF16 消息 12，本方法消息 12。

```json
[
  {
    "field": "$.arguments.content",
    "reference": null,
    "actual": "Hello World!",
    "reference_present": false,
    "actual_present": true
  },
  {
    "field": "$.arguments.file_name",
    "reference": null,
    "actual": "styles.css",
    "reference_present": false,
    "actual_present": true
  },
  {
    "field": "$.name",
    "reference": "mcp_tool_pwd",
    "actual": "mcp_tool_echo"
  }
]
```

### On-Policy QAD

最早动作差异：第 2 个用户轮，第 3 个任务动作；BF16 消息 12，本方法消息 12。

```json
[
  {
    "field": "$.arguments.file_name",
    "reference": null,
    "actual": "styles.css",
    "reference_present": false,
    "actual_present": true
  },
  {
    "field": "$.name",
    "reference": "mcp_tool_pwd",
    "actual": "mcp_tool_touch"
  }
]
```

### QeRL

最早动作差异：第 2 个用户轮，第 3 个任务动作；BF16 消息 12，本方法消息 12。

```json
[
  {
    "field": "$.arguments.file_name",
    "reference": null,
    "actual": "styles.css",
    "reference_present": false,
    "actual_present": true
  },
  {
    "field": "$.name",
    "reference": "mcp_tool_pwd",
    "actual": "mcp_tool_touch"
  }
]
```

## 失败原因

GPTQ 和 EfficientQAT 的文件系统状态不符合要求；其他三种 baseline 在后续用户轮缺少任务调用。具体文件内容和轮次见各自评分证据。

### GPTQ

评分指出的失败位置/原因：

```text
"Model instance for GorillaFileSystem does not match the state with ground truth instance."
```

- 状态字段 `root`：实际 "<Directory: current_working_directory, Parent: None, Contents: {'image_344822349461074042.jpg': <<File: image_344822349461074042.jpg, Content: >>, 'image_8219547643081662353.jpg': <<File: image_8219547643081662353.jpg, Content: >>, 'image_5421509146842474663.jpg': <<File: image_5421509146842474663.jpg, Content: >>, 'image_185391401034246046.jpg': <<File: image_185391401034246046.jpg, Content: >>, 'image_6824007961180780019.jpg': <<File: image_6824007961180780019.jpg, Content: >>, 'image_2994974694593273051.jpg': <<File: image_2994974694593273051.jpg, Content: >>, 'image_2537728455072851196.jpg': <<File: image_2537728455072851196.jpg, Content: >>, 'image_2164918946836800275.jpg': <<File: image_2164918946836800275.jpg, Content: >>, 'image_17 ...（完整值见 score.json / analysis.json）；参考 "<Directory: current_working_directory, Parent: None, Contents: {'image_344822349461074042.jpg': <<File: image_344822349461074042.jpg, Content: >>, 'image_8219547643081662353.jpg': <<File: image_8219547643081662353.jpg, Content: >>, 'image_5421509146842474663.jpg': <<File: image_5421509146842474663.jpg, Content: >>, 'image_185391401034246046.jpg': <<File: image_185391401034246046.jpg, Content: >>, 'image_6824007961180780019.jpg': <<File: image_6824007961180780019.jpg, Content: >>, 'image_2994974694593273051.jpg': <<File: image_2994974694593273051.jpg, Content: >>, 'image_2537728455072851196.jpg': <<File: image_2537728455072851196.jpg, Content: >>, 'image_2164918946836800275.jpg': <<File: image_2164918946836800275.jpg, Content: >>, 'image_17 ...（完整值见 score.json / analysis.json）。
### EfficientQAT

评分指出的失败位置/原因：

```text
"Model instance for GorillaFileSystem does not match the state with ground truth instance."
```

- 状态字段 `root`：实际 "<Directory: current_working_directory, Parent: None, Contents: {'image_344822349461074042.jpg': <<File: image_344822349461074042.jpg, Content: >>, 'image_8219547643081662353.jpg': <<File: image_8219547643081662353.jpg, Content: >>, 'image_5421509146842474663.jpg': <<File: image_5421509146842474663.jpg, Content: >>, 'image_185391401034246046.jpg': <<File: image_185391401034246046.jpg, Content: >>, 'image_6824007961180780019.jpg': <<File: image_6824007961180780019.jpg, Content: >>, 'image_2994974694593273051.jpg': <<File: image_2994974694593273051.jpg, Content: >>, 'image_2537728455072851196.jpg': <<File: image_2537728455072851196.jpg, Content: >>, 'image_2164918946836800275.jpg': <<File: image_2164918946836800275.jpg, Content: >>, 'image_17 ...（完整值见 score.json / analysis.json）；参考 "<Directory: current_working_directory, Parent: None, Contents: {'image_344822349461074042.jpg': <<File: image_344822349461074042.jpg, Content: >>, 'image_8219547643081662353.jpg': <<File: image_8219547643081662353.jpg, Content: >>, 'image_5421509146842474663.jpg': <<File: image_5421509146842474663.jpg, Content: >>, 'image_185391401034246046.jpg': <<File: image_185391401034246046.jpg, Content: >>, 'image_6824007961180780019.jpg': <<File: image_6824007961180780019.jpg, Content: >>, 'image_2994974694593273051.jpg': <<File: image_2994974694593273051.jpg, Content: >>, 'image_2537728455072851196.jpg': <<File: image_2537728455072851196.jpg, Content: >>, 'image_2164918946836800275.jpg': <<File: image_2164918946836800275.jpg, Content: >>, 'image_17 ...（完整值见 score.json / analysis.json）。
### BitDistiller

评分指出的失败位置/原因：

```text
"Model response list is empty for turn 2"
```

### On-Policy QAD

评分指出的失败位置/原因：

```text
"Model response list is empty for turn 2"
```

### QeRL

评分指出的失败位置/原因：

```text
"Model response list is empty for turn 2"
```
