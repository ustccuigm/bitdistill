# Case 006 — live_irrelevance_578-181-0

## 任务

第 1 轮：

what is the price ACHD

完整工具定义、初始状态及其他任务字段见 task.json。

## 七种方法的实际表现

### BF16：通过

指出现有工具只提供规格，不能完成价格查询，没有调用任务工具。

实际任务调用 0 次；[完整 CoT 和工具返回](BF16/cot_and_actions.txt)。

<details><summary>实际动作序列</summary>

```json
[]
```

</details>

### Ours：通过

没有扩展工具未声明的能力，说明现有工具不能提供价格。

实际任务调用 0 次；[完整 CoT 和工具返回](Ours/cot_and_actions.txt)。

<details><summary>实际动作序列</summary>

```json
[]
```

</details>

### GPTQ：未通过

假设规格可能包含价格，把 ACHD 当作 PartNumber 调用。

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
      "name": "mcp_tool_raptor.mpn.specs",
      "arguments": {
        "identifier": "ACHD",
        "search_type": "PartNumber"
      }
    }
  }
]
```

</details>

### EfficientQAT：未通过

以规格里也许有价格为理由，将 ACHD 作为 PartNumber 查询。

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
      "name": "mcp_tool_raptor.mpn.specs",
      "arguments": {
        "identifier": "ACHD",
        "search_type": "PartNumber"
      }
    }
  }
]
```

</details>

### BitDistiller：未通过

已经区分价格与规格，仍假设返回结果可能顺带包含价格，使用 MPN 查询。

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
      "name": "mcp_tool_raptor.mpn.specs",
      "arguments": {
        "identifier": "ACHD",
        "search_type": "MPN"
      }
    }
  }
]
```

</details>

### On-Policy QAD：未通过

把“也许规格包含价格”作为继续调用的依据，使用 MPN 查询。

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
      "name": "mcp_tool_raptor.mpn.specs",
      "arguments": {
        "identifier": "ACHD",
        "search_type": "MPN"
      }
    }
  }
]
```

</details>

### QeRL：未通过

先猜 ACHD 是 MPN，再希望规格结果中包含价格。

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
      "name": "mcp_tool_raptor.mpn.specs",
      "arguments": {
        "identifier": "ACHD",
        "search_type": "MPN"
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
      "name": "mcp_tool_raptor.mpn.specs",
      "arguments": {
        "identifier": "ACHD",
        "search_type": "PartNumber"
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
      "name": "mcp_tool_raptor.mpn.specs",
      "arguments": {
        "identifier": "ACHD",
        "search_type": "PartNumber"
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
      "name": "mcp_tool_raptor.mpn.specs",
      "arguments": {
        "identifier": "ACHD",
        "search_type": "MPN"
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
      "name": "mcp_tool_raptor.mpn.specs",
      "arguments": {
        "identifier": "ACHD",
        "search_type": "MPN"
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
      "name": "mcp_tool_raptor.mpn.specs",
      "arguments": {
        "identifier": "ACHD",
        "search_type": "MPN"
      }
    }
  }
]
```

## 失败原因

五个 baseline 的所选轨迹都调用了规格查询工具，把 ACHD 当作某种零件编号。推理中的关键跳转是从“用户要价格，工具给规格”，转成“规格也许包含价格，所以先试一下”。BF16 和 Ours 则依据工具声明指出无法取得价格，没有发起不匹配的调用。该 case 的特点是工具限制已经进入推理，却没有约束最终动作；这里不涉及数据库状态变化，也不需要假设错误不可逆。

### GPTQ

假设规格可能包含价格，把 ACHD 当作 PartNumber 调用。

评分指出的失败位置/原因：

```text
["Valid syntax. Successfully decode AST when it should not."]
```

### EfficientQAT

以规格里也许有价格为理由，将 ACHD 作为 PartNumber 查询。

评分指出的失败位置/原因：

```text
["Valid syntax. Successfully decode AST when it should not."]
```

### BitDistiller

已经区分价格与规格，仍假设返回结果可能顺带包含价格，使用 MPN 查询。

评分指出的失败位置/原因：

```text
["Valid syntax. Successfully decode AST when it should not."]
```

### On-Policy QAD

把“也许规格包含价格”作为继续调用的依据，使用 MPN 查询。

评分指出的失败位置/原因：

```text
["Valid syntax. Successfully decode AST when it should not."]
```

### QeRL

先猜 ACHD 是 MPN，再希望规格结果中包含价格。

评分指出的失败位置/原因：

```text
["Valid syntax. Successfully decode AST when it should not."]
```
