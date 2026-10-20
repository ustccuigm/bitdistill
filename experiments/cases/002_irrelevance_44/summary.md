# Case 002 — irrelevance_44

## 任务

第 1 轮：

What is the gene sequence for evolutionary changes in whales?

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
      "name": "mcp_tool_gene_sequencer",
      "arguments": {
        "species": "whale",
        "mutation_rate": 0.5,
        "evolution_duration": 50000000
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
      "name": "mcp_tool_gene_sequencer",
      "arguments": {
        "species": "Whale",
        "mutation_rate": 0.3,
        "evolution_duration": 10000000
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
      "name": "mcp_tool_gene_sequencer",
      "arguments": {
        "species": "whale",
        "mutation_rate": 0.05,
        "evolution_duration": 30000000,
        "mutation_factors": [
          "environmental_pressures",
          "dietary_changes"
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
      "name": "mcp_tool_gene_sequencer",
      "arguments": {
        "species": "whale",
        "mutation_rate": 0.1,
        "evolution_duration": 10000000
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
      "name": "mcp_tool_gene_sequencer",
      "arguments": {
        "species": "whale",
        "mutation_rate": 0.1,
        "evolution_duration": 5000000
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
      "name": "mcp_tool_gene_sequencer",
      "arguments": {
        "species": "whale",
        "mutation_rate": 0.5,
        "evolution_duration": 50000000
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
      "name": "mcp_tool_gene_sequencer",
      "arguments": {
        "species": "Whale",
        "mutation_rate": 0.3,
        "evolution_duration": 10000000
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
      "name": "mcp_tool_gene_sequencer",
      "arguments": {
        "species": "whale",
        "mutation_rate": 0.05,
        "evolution_duration": 30000000,
        "mutation_factors": [
          "environmental_pressures",
          "dietary_changes"
        ]
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
      "name": "mcp_tool_gene_sequencer",
      "arguments": {
        "species": "whale",
        "mutation_rate": 0.1,
        "evolution_duration": 10000000
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
      "name": "mcp_tool_gene_sequencer",
      "arguments": {
        "species": "whale",
        "mutation_rate": 0.1,
        "evolution_duration": 5000000
      }
    }
  }
]
```

## 失败原因

工具需要 mutation_rate 和 evolution_duration；用户没有提供这些必填条件，评分要求先澄清，而不是自行设定模拟参数。

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
