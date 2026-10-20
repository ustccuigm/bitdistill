# Case 007 — live_irrelevance_593-188-0

## 任务

第 1 轮：

I would like to listen to a song

完整工具定义、初始状态及其他任务字段见 task.json。

## 七种方法的实际表现

### BF16：通过

实际任务调用 0 次；[完整 CoT 和工具返回](BF16/cot_and_actions.txt)。

<details><summary>实际动作序列</summary>

```json
[]
```

</details>

### Ours：通过

实际任务调用 0 次；[完整 CoT 和工具返回](Ours/cot_and_actions.txt)。

<details><summary>实际动作序列</summary>

```json
[]
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
      "name": "mcp_tool_Music_3_LookupMusic",
      "arguments": {
        "artist": "dontcare",
        "album": "dontcare",
        "genre": "dontcare",
        "year": "dontcare"
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
      "name": "mcp_tool_Music_3_LookupMusic",
      "arguments": {
        "artist": "dontcare",
        "album": "dontcare",
        "genre": "dontcare",
        "year": "dontcare"
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
      "name": "mcp_tool_Music_3_LookupMusic",
      "arguments": {
        "artist": "dontcare",
        "album": "dontcare",
        "genre": "dontcare",
        "year": "dontcare"
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
      "name": "mcp_tool_Music_3_LookupMusic",
      "arguments": {
        "artist": "dontcare",
        "album": "dontcare",
        "genre": "dontcare",
        "year": "dontcare"
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
      "name": "mcp_tool_Music_3_LookupMusic",
      "arguments": {
        "artist": "dontcare",
        "album": "dontcare",
        "genre": "dontcare",
        "year": "dontcare"
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

最早动作差异：第 1 个用户轮，第 1 个任务动作；BF16 消息 None，本方法消息 4。

```json
[
  {
    "field": "$",
    "reference": null,
    "actual": {
      "wrapper": "call_tool",
      "name": "mcp_tool_Music_3_LookupMusic",
      "arguments": {
        "artist": "dontcare",
        "album": "dontcare",
        "genre": "dontcare",
        "year": "dontcare"
      }
    }
  }
]
```

### EfficientQAT

最早动作差异：第 1 个用户轮，第 1 个任务动作；BF16 消息 None，本方法消息 4。

```json
[
  {
    "field": "$",
    "reference": null,
    "actual": {
      "wrapper": "call_tool",
      "name": "mcp_tool_Music_3_LookupMusic",
      "arguments": {
        "artist": "dontcare",
        "album": "dontcare",
        "genre": "dontcare",
        "year": "dontcare"
      }
    }
  }
]
```

### BitDistiller

最早动作差异：第 1 个用户轮，第 1 个任务动作；BF16 消息 None，本方法消息 4。

```json
[
  {
    "field": "$",
    "reference": null,
    "actual": {
      "wrapper": "call_tool",
      "name": "mcp_tool_Music_3_LookupMusic",
      "arguments": {
        "artist": "dontcare",
        "album": "dontcare",
        "genre": "dontcare",
        "year": "dontcare"
      }
    }
  }
]
```

### On-Policy QAD

最早动作差异：第 1 个用户轮，第 1 个任务动作；BF16 消息 None，本方法消息 4。

```json
[
  {
    "field": "$",
    "reference": null,
    "actual": {
      "wrapper": "call_tool",
      "name": "mcp_tool_Music_3_LookupMusic",
      "arguments": {
        "artist": "dontcare",
        "album": "dontcare",
        "genre": "dontcare",
        "year": "dontcare"
      }
    }
  }
]
```

### QeRL

最早动作差异：第 1 个用户轮，第 1 个任务动作；BF16 消息 None，本方法消息 4。

```json
[
  {
    "field": "$",
    "reference": null,
    "actual": {
      "wrapper": "call_tool",
      "name": "mcp_tool_Music_3_LookupMusic",
      "arguments": {
        "artist": "dontcare",
        "album": "dontcare",
        "genre": "dontcare",
        "year": "dontcare"
      }
    }
  }
]
```

## 失败原因

用户只说想听歌，没有指定歌曲或明确筛选条件。该题参考答案要求先澄清，baseline 选择了调用分支；这反映该题的澄清规则，不意味着所有推荐歌曲的调用都普遍错误。

### GPTQ

评分指出的失败位置/原因：

```text
["Valid syntax. Successfully decode AST when it should not."]
```

### EfficientQAT

评分指出的失败位置/原因：

```text
["Valid syntax. Successfully decode AST when it should not."]
```

### BitDistiller

评分指出的失败位置/原因：

```text
["Valid syntax. Successfully decode AST when it should not."]
```

### On-Policy QAD

评分指出的失败位置/原因：

```text
["Valid syntax. Successfully decode AST when it should not."]
```

### QeRL

评分指出的失败位置/原因：

```text
["Valid syntax. Successfully decode AST when it should not."]
```
