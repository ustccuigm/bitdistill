# Case 029 — multi_turn_miss_param_111

## 原始任务

第 1 轮：

I want to keep track of a specific company stock activities, so it would be helpful to have its stock added to my watchlist.

第 2 轮：

The company name is Zeta Corp

第 3 轮：

I've recently placed an order but can't seem to recall the details. It would be useful if you could retrieve the specifics of my last order to aid in planning my next investment move.

第 4 轮：

Considering the latest developments, I (user id USR001) need to quickly communicate with Jane, one of my business partners, regarding the new stock inclusion and the status of my current order. Send the message 'What are the new stock inclusion and the status of my current order?'?

第 5 轮：

Post sending that message to Jane, I would prefer to review all the messages I've sent, as there might be relevant follow-up or advice from my network concerning the stock and order decisions.

完整工具定义、初始状态及其他任务字段见 task.json。

## 七种方法的实际表现

### BF16：通过

实际任务调用 7 次；[完整 CoT 和工具返回](BF16/cot_and_actions.txt)。

<details><summary>实际动作序列</summary>

```json
[
  {
    "user_turn": 2,
    "action_in_turn": 1,
    "message_index": 6,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_get_symbol_by_name",
      "arguments": {
        "name": "Zeta Corp"
      }
    }
  },
  {
    "user_turn": 2,
    "action_in_turn": 2,
    "message_index": 8,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_add_to_watchlist",
      "arguments": {
        "stock": "ZETA"
      }
    }
  },
  {
    "user_turn": 3,
    "action_in_turn": 1,
    "message_index": 12,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_get_order_history",
      "arguments": {}
    }
  },
  {
    "user_turn": 3,
    "action_in_turn": 2,
    "message_index": 14,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_get_order_details",
      "arguments": {
        "order_id": 12345
      }
    }
  },
  {
    "user_turn": 4,
    "action_in_turn": 1,
    "message_index": 18,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_get_user_id",
      "arguments": {
        "user": "Jane"
      }
    }
  },
  {
    "user_turn": 4,
    "action_in_turn": 2,
    "message_index": 20,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_send_message",
      "arguments": "{\"receiver_id\": \"USR002\", \"message\": \"What are the new stock inclusion and the status of my current order?\")}"
    }
  },
  {
    "user_turn": 5,
    "action_in_turn": 1,
    "message_index": 24,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_view_messages_sent",
      "arguments": {}
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
    "user_turn": 2,
    "action_in_turn": 1,
    "message_index": 6,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_get_symbol_by_name",
      "arguments": {
        "name": "Zeta Corp"
      }
    }
  },
  {
    "user_turn": 2,
    "action_in_turn": 2,
    "message_index": 8,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_add_to_watchlist",
      "arguments": {
        "stock": "ZETA"
      }
    }
  },
  {
    "user_turn": 3,
    "action_in_turn": 1,
    "message_index": 12,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_get_order_history",
      "arguments": {}
    }
  },
  {
    "user_turn": 3,
    "action_in_turn": 2,
    "message_index": 14,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_get_order_details",
      "arguments": {
        "order_id": 12345
      }
    }
  },
  {
    "user_turn": 4,
    "action_in_turn": 1,
    "message_index": 18,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_get_user_id",
      "arguments": {
        "user": "Jane"
      }
    }
  },
  {
    "user_turn": 4,
    "action_in_turn": 2,
    "message_index": 20,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_send_message",
      "arguments": "{\"receiver_id\": \"USR002\", \"message\": \"What are the new stock inclusion and the status of my current order?\")}}"
    }
  },
  {
    "user_turn": 5,
    "action_in_turn": 1,
    "message_index": 24,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_view_messages_sent",
      "arguments": {}
    }
  }
]
```

</details>

### GPTQ：未通过

实际任务调用 8 次；[完整 CoT 和工具返回](GPTQ/cot_and_actions.txt)。

<details><summary>实际动作序列</summary>

```json
[
  {
    "user_turn": 1,
    "action_in_turn": 1,
    "message_index": 4,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_get_symbol_by_name",
      "arguments": {
        "name": "Company X"
      }
    }
  },
  {
    "user_turn": 2,
    "action_in_turn": 1,
    "message_index": 8,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_get_symbol_by_name",
      "arguments": {
        "name": "Zeta Corp"
      }
    }
  },
  {
    "user_turn": 2,
    "action_in_turn": 2,
    "message_index": 10,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_add_to_watchlist",
      "arguments": {
        "stock": "ZETA"
      }
    }
  },
  {
    "user_turn": 3,
    "action_in_turn": 1,
    "message_index": 14,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_get_order_history",
      "arguments": {}
    }
  },
  {
    "user_turn": 3,
    "action_in_turn": 2,
    "message_index": 16,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_get_order_details",
      "arguments": {
        "order_id": 12345
      }
    }
  },
  {
    "user_turn": 4,
    "action_in_turn": 1,
    "message_index": 20,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_get_user_id",
      "arguments": {
        "user": "Jane"
      }
    }
  },
  {
    "user_turn": 4,
    "action_in_turn": 2,
    "message_index": 22,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_send_message",
      "arguments": "{\"receiver_id\": \"USR002\", \"message\": \"What are the new stock inclusion and the status of my current order?\\`}"
    }
  },
  {
    "user_turn": 5,
    "action_in_turn": 1,
    "message_index": 26,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_view_messages_sent",
      "arguments": {}
    }
  }
]
```

</details>

### EfficientQAT：未通过

实际任务调用 8 次；[完整 CoT 和工具返回](EfficientQAT/cot_and_actions.txt)。

<details><summary>实际动作序列</summary>

```json
[
  {
    "user_turn": 1,
    "action_in_turn": 1,
    "message_index": 4,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_add_to_watchlist",
      "arguments": {
        "stock": "AAPL"
      }
    }
  },
  {
    "user_turn": 2,
    "action_in_turn": 1,
    "message_index": 8,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_get_symbol_by_name",
      "arguments": {
        "name": "Zeta Corp"
      }
    }
  },
  {
    "user_turn": 2,
    "action_in_turn": 2,
    "message_index": 10,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_add_to_watchlist",
      "arguments": {
        "stock": "ZETA"
      }
    }
  },
  {
    "user_turn": 3,
    "action_in_turn": 1,
    "message_index": 14,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_get_order_history",
      "arguments": {}
    }
  },
  {
    "user_turn": 3,
    "action_in_turn": 2,
    "message_index": 16,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_get_order_details",
      "arguments": {
        "order_id": 12345
      }
    }
  },
  {
    "user_turn": 4,
    "action_in_turn": 1,
    "message_index": 20,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_get_user_id",
      "arguments": {
        "user": "Jane"
      }
    }
  },
  {
    "user_turn": 4,
    "action_in_turn": 2,
    "message_index": 22,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_send_message",
      "arguments": {
        "receiver_id": "USR002",
        "message": "What are the new stock inclusion and the status of my current order?"
      }
    }
  },
  {
    "user_turn": 5,
    "action_in_turn": 1,
    "message_index": 26,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_view_messages_sent",
      "arguments": {}
    }
  }
]
```

</details>

### BitDistiller：未通过

实际任务调用 9 次；[完整 CoT 和工具返回](BitDistiller/cot_and_actions.txt)。

<details><summary>实际动作序列</summary>

```json
[
  {
    "user_turn": 1,
    "action_in_turn": 1,
    "message_index": 4,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_get_symbol_by_name",
      "arguments": {
        "name": "Apple"
      }
    }
  },
  {
    "user_turn": 1,
    "action_in_turn": 2,
    "message_index": 6,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_add_to_watchlist",
      "arguments": {
        "stock": "AAPL"
      }
    }
  },
  {
    "user_turn": 2,
    "action_in_turn": 1,
    "message_index": 10,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_get_symbol_by_name",
      "arguments": {
        "name": "Zeta Corp"
      }
    }
  },
  {
    "user_turn": 2,
    "action_in_turn": 2,
    "message_index": 12,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_add_to_watchlist",
      "arguments": {
        "stock": "ZETA"
      }
    }
  },
  {
    "user_turn": 3,
    "action_in_turn": 1,
    "message_index": 16,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_get_order_history",
      "arguments": {}
    }
  },
  {
    "user_turn": 3,
    "action_in_turn": 2,
    "message_index": 18,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_get_order_details",
      "arguments": {
        "order_id": 12345
      }
    }
  },
  {
    "user_turn": 4,
    "action_in_turn": 1,
    "message_index": 22,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_get_user_id",
      "arguments": {
        "user": "Jane"
      }
    }
  },
  {
    "user_turn": 4,
    "action_in_turn": 2,
    "message_index": 24,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_send_message",
      "arguments": "{\"receiver_id\": \"USR002\", \"message\": \"What are the new stock inclusion and the status of my current order?\\`}"
    }
  },
  {
    "user_turn": 5,
    "action_in_turn": 1,
    "message_index": 28,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_view_messages_sent",
      "arguments": {}
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
    "user_turn": 2,
    "action_in_turn": 1,
    "message_index": 6,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_get_symbol_by_name",
      "arguments": {
        "name": "Zeta Corp"
      }
    }
  },
  {
    "user_turn": 2,
    "action_in_turn": 2,
    "message_index": 8,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_add_to_watchlist",
      "arguments": {
        "stock": "ZETA"
      }
    }
  },
  {
    "user_turn": 3,
    "action_in_turn": 1,
    "message_index": 12,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_get_order_history",
      "arguments": {}
    }
  },
  {
    "user_turn": 3,
    "action_in_turn": 2,
    "message_index": 14,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_get_order_details",
      "arguments": {
        "order_id": 12345
      }
    }
  },
  {
    "user_turn": 4,
    "action_in_turn": 1,
    "message_index": 18,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_get_user_id",
      "arguments": {
        "user": "Jane"
      }
    }
  },
  {
    "user_turn": 4,
    "action_in_turn": 2,
    "message_index": 20,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_send_message",
      "arguments": "{\"receiver_id\": \"USR002\", \"message\": \"What are the new stock inclusion and the status of my current order?\\`}"
    }
  },
  {
    "user_turn": 5,
    "action_in_turn": 1,
    "message_index": 24,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_view_messages_sent",
      "arguments": {}
    }
  }
]
```

</details>

### QeRL：未通过

实际任务调用 8 次；[完整 CoT 和工具返回](QeRL/cot_and_actions.txt)。

<details><summary>实际动作序列</summary>

```json
[
  {
    "user_turn": 1,
    "action_in_turn": 1,
    "message_index": 4,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_get_symbol_by_name",
      "arguments": {
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
      "name": "mcp_tool_get_symbol_by_name",
      "arguments": {
        "name": "Zeta Corp"
      }
    }
  },
  {
    "user_turn": 2,
    "action_in_turn": 2,
    "message_index": 10,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_add_to_watchlist",
      "arguments": {
        "stock": "ZETA"
      }
    }
  },
  {
    "user_turn": 3,
    "action_in_turn": 1,
    "message_index": 14,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_get_order_history",
      "arguments": {}
    }
  },
  {
    "user_turn": 3,
    "action_in_turn": 2,
    "message_index": 16,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_get_order_details",
      "arguments": {
        "order_id": 12345
      }
    }
  },
  {
    "user_turn": 4,
    "action_in_turn": 1,
    "message_index": 20,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_get_user_id",
      "arguments": {
        "user": "Jane"
      }
    }
  },
  {
    "user_turn": 4,
    "action_in_turn": 2,
    "message_index": 22,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_send_message",
      "arguments": "{\"receiver_id\": \"USR002\", \"message\": \"What are the new stock inclusion and the status of my current order?\\`}"
    }
  },
  {
    "user_turn": 5,
    "action_in_turn": 1,
    "message_index": 26,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_view_messages_sent",
      "arguments": {}
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
    "field": "$.arguments",
    "reference": "{\"receiver_id\": \"USR002\", \"message\": \"What are the new stock inclusion and the status of my current order?\")}",
    "actual": "{\"receiver_id\": \"USR002\", \"message\": \"What are the new stock inclusion and the status of my current order?\")}}"
  }
]
```

### GPTQ

最早动作差异：第 1 个用户轮，第 1 个任务动作；BF16 消息 None，本方法消息 4。

```json
[
  {
    "field": "$",
    "reference": null,
    "actual": {
      "wrapper": "call_tool",
      "name": "mcp_tool_get_symbol_by_name",
      "arguments": {
        "name": "Company X"
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
      "name": "mcp_tool_add_to_watchlist",
      "arguments": {
        "stock": "AAPL"
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
      "name": "mcp_tool_get_symbol_by_name",
      "arguments": {
        "name": "Apple"
      }
    }
  }
]
```

### On-Policy QAD

最早动作差异：第 4 个用户轮，第 2 个任务动作；BF16 消息 20，本方法消息 20。

```json
[
  {
    "field": "$.arguments",
    "reference": "{\"receiver_id\": \"USR002\", \"message\": \"What are the new stock inclusion and the status of my current order?\")}",
    "actual": "{\"receiver_id\": \"USR002\", \"message\": \"What are the new stock inclusion and the status of my current order?\\`}"
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
      "name": "mcp_tool_get_symbol_by_name",
      "arguments": {
        "name": ""
      }
    }
  }
]
```

## 失败原因

GPTQ、On-Policy QAD、QeRL 的消息 inbox 状态不符；EfficientQAT 和 BitDistiller 的关注股票列表不符，属于不同子任务的执行差异。

### GPTQ

评分指出的失败位置/原因：

```text
"Model instance for MessageAPI does not match the state with ground truth instance."
```

- 状态字段 `inbox[5].USR002`：实际 "What are the new stock inclusion and the status of my current order?\\`"；参考 "What are the new stock inclusion and the status of my current order?"。
### EfficientQAT

评分指出的失败位置/原因：

```text
"Model instance for TradingBot does not match the state with ground truth instance."
```

- 状态字段 `watch_list[2]`：实际 "AAPL"；参考 null。
### BitDistiller

评分指出的失败位置/原因：

```text
"Model instance for TradingBot does not match the state with ground truth instance."
```

- 状态字段 `watch_list[2]`：实际 "AAPL"；参考 null。
### On-Policy QAD

评分指出的失败位置/原因：

```text
"Model instance for MessageAPI does not match the state with ground truth instance."
```

- 状态字段 `inbox[5].USR002`：实际 "What are the new stock inclusion and the status of my current order?\\`"；参考 "What are the new stock inclusion and the status of my current order?"。
### QeRL

评分指出的失败位置/原因：

```text
"Model instance for MessageAPI does not match the state with ground truth instance."
```

- 状态字段 `inbox[5].USR002`：实际 "What are the new stock inclusion and the status of my current order?\\`"；参考 "What are the new stock inclusion and the status of my current order?"。
