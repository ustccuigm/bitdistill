# Case 019 — live_simple_31-8-1

## 任务

第 1 轮：

Could you retrieve the list of exports for my bot with ID 'B12345' and for version 'v1'? I'm interested in seeing them in descending order by the last updated date.

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
      "name": "mcp_tool_aws.lexv2_models.list_exports",
      "arguments": {
        "botId": "B12345",
        "botVersion": "v1",
        "sortBy": "DESC"
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
      "name": "mcp_tool_aws.lexv2_models.list_exports",
      "arguments": {
        "botId": "B12345",
        "botVersion": "v1",
        "sortBy": "DESC"
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
      "name": "mcp_tool_aws.lexv2_models.list_exports",
      "arguments": {
        "botId": "B12345",
        "botVersion": "v1",
        "sortBy": "LastUpdatedDateTime",
        "sortDirection": "DESC"
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
      "name": "mcp_tool_aws.lexv2_models.list_exports",
      "arguments": {
        "botId": "B12345",
        "botVersion": "v1",
        "sortBy": "LastUpdatedDateTime_DESC"
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
      "name": "mcp_tool_aws.lexv2_models.list_exports",
      "arguments": {
        "botId": "B12345",
        "botVersion": "v1",
        "sortBy": "LastUpdatedDateTime",
        "filterOperator": "EQ"
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
      "name": "mcp_tool_aws.lexv2_models.list_exports",
      "arguments": {
        "botId": "B12345",
        "botVersion": "v1",
        "sortBy": "LastUpdatedDateTime",
        "filterOperator": "EQ"
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
      "name": "mcp_tool_aws.lexv2_models.list_exports",
      "arguments": {
        "botId": "B12345",
        "botVersion": "v1",
        "sortBy": "LastUpdatedDateTime.DESC"
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
    "field": "$.arguments.sortBy",
    "reference": "DESC",
    "actual": "LastUpdatedDateTime"
  },
  {
    "field": "$.arguments.sortDirection",
    "reference": null,
    "actual": "DESC",
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
    "field": "$.arguments.sortBy",
    "reference": "DESC",
    "actual": "LastUpdatedDateTime_DESC"
  }
]
```

### BitDistiller

最早动作差异：第 1 个用户轮，第 1 个任务动作；BF16 消息 4，本方法消息 4。

```json
[
  {
    "field": "$.arguments.filterOperator",
    "reference": null,
    "actual": "EQ",
    "reference_present": false,
    "actual_present": true
  },
  {
    "field": "$.arguments.sortBy",
    "reference": "DESC",
    "actual": "LastUpdatedDateTime"
  }
]
```

### On-Policy QAD

最早动作差异：第 1 个用户轮，第 1 个任务动作；BF16 消息 4，本方法消息 4。

```json
[
  {
    "field": "$.arguments.filterOperator",
    "reference": null,
    "actual": "EQ",
    "reference_present": false,
    "actual_present": true
  },
  {
    "field": "$.arguments.sortBy",
    "reference": "DESC",
    "actual": "LastUpdatedDateTime"
  }
]
```

### QeRL

最早动作差异：第 1 个用户轮，第 1 个任务动作；BF16 消息 4，本方法消息 4。

```json
[
  {
    "field": "$.arguments.sortBy",
    "reference": "DESC",
    "actual": "LastUpdatedDateTime.DESC"
  }
]
```

## 失败原因

sortBy 应按参考答案填写 DESC；baseline 填入 LastUpdatedDateTime 或拼接方向的字符串，排序参数编码没有匹配参考接口。

### GPTQ

评分指出的失败位置/原因：

```text
["Invalid value for parameter 'sortBy': 'LastUpdatedDateTime'. Expected one of ['DESC']. Case insensitive."]
```

### EfficientQAT

评分指出的失败位置/原因：

```text
["Invalid value for parameter 'sortBy': 'LastUpdatedDateTime_DESC'. Expected one of ['DESC']. Case insensitive."]
```

### BitDistiller

评分指出的失败位置/原因：

```text
["Invalid value for parameter 'sortBy': 'LastUpdatedDateTime'. Expected one of ['DESC']. Case insensitive."]
```

### On-Policy QAD

评分指出的失败位置/原因：

```text
["Invalid value for parameter 'sortBy': 'LastUpdatedDateTime'. Expected one of ['DESC']. Case insensitive."]
```

### QeRL

评分指出的失败位置/原因：

```text
["Invalid value for parameter 'sortBy': 'LastUpdatedDateTime.DESC'. Expected one of ['DESC']. Case insensitive."]
```
