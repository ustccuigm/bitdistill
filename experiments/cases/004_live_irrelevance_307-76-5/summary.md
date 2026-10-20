# Case 004 — live_irrelevance_307-76-5

## 任务

第 1 轮：

lebron James is

完整工具定义、初始状态及其他任务字段见 task.json。

## 七种方法的实际表现

### BF16：通过

识别到句子不完整，要求用户说明想了解什么。

实际任务调用 0 次；[完整 CoT 和工具返回](BF16/cot_and_actions.txt)。

<details><summary>实际动作序列</summary>

```json
[]
```

</details>

### Ours：通过

指出原句缺少明确问题，没有根据猜测发起 GET。

实际任务调用 0 次；[完整 CoT 和工具返回](Ours/cot_and_actions.txt)。

<details><summary>实际动作序列</summary>

```json
[]
```

</details>

### GPTQ：未通过

先承认请求不完整，随后自行决定查询 Wikipedia，并添加 JSON 请求头和格式参数。

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
      "name": "mcp_tool_requests.get",
      "arguments": {
        "url": "https://en.wikipedia.org/wiki/Lebron_James",
        "headers": {
          "Accept": "application/json",
          "Content-Type": "application/json"
        },
        "format": "jsonv2"
      }
    }
  }
]
```

</details>

### EfficientQAT：未通过

自行构造 NBA 积分榜接口和 2023-24 赛季参数，偏离尚未明确的人物问题。

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
      "name": "mcp_tool_requests.get",
      "arguments": {
        "url": "https://data.nba.com/data/v4/standings.json",
        "params": {
          "leagueId": "00",
          "season": "2023-24"
        }
      }
    }
  }
]
```

</details>

### BitDistiller：未通过

直接把不完整请求解释成读取 Wikipedia 人物页面。

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
      "name": "mcp_tool_requests.get",
      "arguments": {
        "url": "https://en.wikipedia.org/wiki/LeBron_James"
      }
    }
  }
]
```

</details>

### On-Policy QAD：未通过

生成 Sportsdata 接口地址，还填入占位的 Authorization 请求头。

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
      "name": "mcp_tool_requests.get",
      "arguments": {
        "url": "https://api.sportsdata.io/v3/nba/stats",
        "params": {
          "playerName": "LeBron James"
        },
        "headers": {
          "Authorization": "Bearer YOUR_API_KEY_HERE"
        }
      }
    }
  }
]
```

</details>

### QeRL：未通过

自行选择人物页面和格式参数，URL 中还出现 LeBron_Jamess。

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
      "name": "mcp_tool_requests.get",
      "arguments": {
        "url": "https://en.wikipedia.org/wiki/LeBron_Jamess",
        "params": {
          "format": "json"
        }
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
      "name": "mcp_tool_requests.get",
      "arguments": {
        "url": "https://en.wikipedia.org/wiki/Lebron_James",
        "headers": {
          "Accept": "application/json",
          "Content-Type": "application/json"
        },
        "format": "jsonv2"
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
      "name": "mcp_tool_requests.get",
      "arguments": {
        "url": "https://data.nba.com/data/v4/standings.json",
        "params": {
          "leagueId": "00",
          "season": "2023-24"
        }
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
      "name": "mcp_tool_requests.get",
      "arguments": {
        "url": "https://en.wikipedia.org/wiki/LeBron_James"
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
      "name": "mcp_tool_requests.get",
      "arguments": {
        "url": "https://api.sportsdata.io/v3/nba/stats",
        "params": {
          "playerName": "LeBron James"
        },
        "headers": {
          "Authorization": "Bearer YOUR_API_KEY_HERE"
        }
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
      "name": "mcp_tool_requests.get",
      "arguments": {
        "url": "https://en.wikipedia.org/wiki/LeBron_Jamess",
        "params": {
          "format": "json"
        }
      }
    }
  }
]
```

## 失败原因

五个 baseline 的所选轨迹都把半句话扩展成了查询詹姆斯资料的任务，并生成了不同的 URL、请求参数或请求头。BF16 和 Ours 没有发起请求，先要求澄清意图。这个 case 展示的是面对不完整请求时，是否过早替用户确定目标；评分失败依据是该任务要求澄清，而非 HTTP GET 在一般情况下不能检索人物资料。

### GPTQ

先承认请求不完整，随后自行决定查询 Wikipedia，并添加 JSON 请求头和格式参数。

评分指出的失败位置/原因：

```text
["Valid syntax. Successfully decode AST when it should not."]
```

### EfficientQAT

自行构造 NBA 积分榜接口和 2023-24 赛季参数，偏离尚未明确的人物问题。

评分指出的失败位置/原因：

```text
["Valid syntax. Successfully decode AST when it should not."]
```

### BitDistiller

直接把不完整请求解释成读取 Wikipedia 人物页面。

评分指出的失败位置/原因：

```text
["Valid syntax. Successfully decode AST when it should not."]
```

### On-Policy QAD

生成 Sportsdata 接口地址，还填入占位的 Authorization 请求头。

评分指出的失败位置/原因：

```text
["Valid syntax. Successfully decode AST when it should not."]
```

### QeRL

自行选择人物页面和格式参数，URL 中还出现 LeBron_Jamess。

评分指出的失败位置/原因：

```text
["Valid syntax. Successfully decode AST when it should not."]
```
