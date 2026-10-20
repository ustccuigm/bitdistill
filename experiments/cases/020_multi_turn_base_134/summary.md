# Case 020 — multi_turn_base_134

## 任务

第 1 轮：

I'm keen to gather comprehensive insights regarding a company trading under 'Quasar Ltd.'. Specifically, I'm looking for its up-to-the-minute stock price, crucial market performance metrics, and the volume of its recent trading activities. Once you have that sorted out, kindly include this company on my watchlist.

第 2 轮：

I submitted an investment order not too long ago, and I'd appreciate having the detailed lineup for it—such as which stock was involved, the total shares purchased, and the current status of the transaction. Additionally, if it's possible, withdraw that order if it hasn't yet gone through.

第 3 轮：

To wrap things up, I'd just like to perform a swift check on my trading account, focusing on the current balance and any credit or debit cards associated with it.

完整工具定义、初始状态及其他任务字段见 task.json。

## 七种方法的实际表现

### BF16：通过

实际任务调用 8 次；[完整 CoT 和工具返回](BF16/cot_and_actions.txt)。

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
        "name": "Quasar Ltd.",
        "sector": "Finance"
      }
    }
  },
  {
    "user_turn": 1,
    "action_in_turn": 2,
    "message_index": 6,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_get_symbol_by_name",
      "arguments": {
        "name": "Quasar Ltd."
      }
    }
  },
  {
    "user_turn": 1,
    "action_in_turn": 3,
    "message_index": 8,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_get_stock_info",
      "arguments": {
        "symbol": "QUAS"
      }
    }
  },
  {
    "user_turn": 1,
    "action_in_turn": 4,
    "message_index": 10,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_add_to_watchlist",
      "arguments": {
        "stock": "QUAS"
      }
    }
  },
  {
    "user_turn": 2,
    "action_in_turn": 1,
    "message_index": 14,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_get_order_history",
      "arguments": {}
    }
  },
  {
    "user_turn": 2,
    "action_in_turn": 2,
    "message_index": 16,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_get_order_details",
      "arguments": {
        "order_id": 12446
      }
    }
  },
  {
    "user_turn": 2,
    "action_in_turn": 3,
    "message_index": 18,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_cancel_order",
      "arguments": {
        "order_id": 12446
      }
    }
  },
  {
    "user_turn": 3,
    "action_in_turn": 1,
    "message_index": 22,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_get_account_info",
      "arguments": {}
    }
  }
]
```

</details>

### Ours：通过

实际任务调用 8 次；[完整 CoT 和工具返回](Ours/cot_and_actions.txt)。

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
        "name": "Quasar Ltd.",
        "sector": "Finance"
      }
    }
  },
  {
    "user_turn": 1,
    "action_in_turn": 2,
    "message_index": 6,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_get_symbol_by_name",
      "arguments": {
        "name": "Quasar Ltd."
      }
    }
  },
  {
    "user_turn": 1,
    "action_in_turn": 3,
    "message_index": 8,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_get_stock_info",
      "arguments": {
        "symbol": "QUAS"
      }
    }
  },
  {
    "user_turn": 1,
    "action_in_turn": 4,
    "message_index": 10,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_add_to_watchlist",
      "arguments": {
        "stock": "QUAS"
      }
    }
  },
  {
    "user_turn": 2,
    "action_in_turn": 1,
    "message_index": 14,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_get_order_history",
      "arguments": {}
    }
  },
  {
    "user_turn": 2,
    "action_in_turn": 2,
    "message_index": 16,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_get_order_details",
      "arguments": {
        "order_id": 12446
      }
    }
  },
  {
    "user_turn": 2,
    "action_in_turn": 3,
    "message_index": 18,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_cancel_order",
      "arguments": {
        "order_id": 12446
      }
    }
  },
  {
    "user_turn": 3,
    "action_in_turn": 1,
    "message_index": 22,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_get_account_info",
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
        "name": "Quasar Ltd.",
        "sector": "Financial Services"
      }
    }
  },
  {
    "user_turn": 1,
    "action_in_turn": 2,
    "message_index": 6,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_get_symbol_by_name",
      "arguments": {
        "name": "Quasar Ltd."
      }
    }
  },
  {
    "user_turn": 1,
    "action_in_turn": 3,
    "message_index": 8,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_get_stock_info",
      "arguments": {
        "symbol": "QUAS"
      }
    }
  },
  {
    "user_turn": 1,
    "action_in_turn": 4,
    "message_index": 10,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_add_to_watchlist",
      "arguments": {
        "stock": "QUAS"
      }
    }
  },
  {
    "user_turn": 2,
    "action_in_turn": 1,
    "message_index": 14,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_get_order_history",
      "arguments": {}
    }
  },
  {
    "user_turn": 2,
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
    "user_turn": 2,
    "action_in_turn": 3,
    "message_index": 18,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_get_order_details",
      "arguments": {
        "order_id": 12446
      }
    }
  },
  {
    "user_turn": 3,
    "action_in_turn": 1,
    "message_index": 22,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_get_account_info",
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
      "name": "mcp_tool_get_symbol_by_name",
      "arguments": {
        "name": "Quasar Ltd.",
        "sector": "Financial Services"
      }
    }
  },
  {
    "user_turn": 1,
    "action_in_turn": 2,
    "message_index": 6,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_get_symbol_by_name",
      "arguments": {
        "name": "Quasar Ltd."
      }
    }
  },
  {
    "user_turn": 1,
    "action_in_turn": 3,
    "message_index": 8,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_get_stock_info",
      "arguments": {
        "symbol": "QUAS"
      }
    }
  },
  {
    "user_turn": 1,
    "action_in_turn": 4,
    "message_index": 10,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_add_to_watchlist",
      "arguments": {
        "stock": "QUAS"
      }
    }
  },
  {
    "user_turn": 2,
    "action_in_turn": 1,
    "message_index": 14,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_get_order_history",
      "arguments": {}
    }
  },
  {
    "user_turn": 2,
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
    "user_turn": 2,
    "action_in_turn": 3,
    "message_index": 18,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_get_order_details",
      "arguments": {
        "order_id": 12446
      }
    }
  },
  {
    "user_turn": 3,
    "action_in_turn": 1,
    "message_index": 22,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_get_account_info",
      "arguments": {}
    }
  }
]
```

</details>

### BitDistiller：未通过

实际任务调用 8 次；[完整 CoT 和工具返回](BitDistiller/cot_and_actions.txt)。

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
        "name": "Quasar Ltd.",
        "parameters": {}
      }
    }
  },
  {
    "user_turn": 1,
    "action_in_turn": 2,
    "message_index": 6,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_get_symbol_by_name",
      "arguments": {
        "name": "Quasar Ltd."
      }
    }
  },
  {
    "user_turn": 1,
    "action_in_turn": 3,
    "message_index": 8,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_get_stock_info",
      "arguments": {
        "symbol": "QUAS"
      }
    }
  },
  {
    "user_turn": 1,
    "action_in_turn": 4,
    "message_index": 10,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_add_to_watchlist",
      "arguments": {
        "stock": "QUAS"
      }
    }
  },
  {
    "user_turn": 2,
    "action_in_turn": 1,
    "message_index": 14,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_get_order_history",
      "arguments": {}
    }
  },
  {
    "user_turn": 2,
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
    "user_turn": 2,
    "action_in_turn": 3,
    "message_index": 18,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_get_order_details",
      "arguments": {
        "order_id": 12446
      }
    }
  },
  {
    "user_turn": 3,
    "action_in_turn": 1,
    "message_index": 22,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_get_account_info",
      "arguments": {}
    }
  }
]
```

</details>

### On-Policy QAD：未通过

实际任务调用 5 次；[完整 CoT 和工具返回](On-Policy%20QAD/cot_and_actions.txt)。

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
        "name": "Quasar Ltd.",
        "sector": "Financial Services"
      }
    }
  },
  {
    "user_turn": 1,
    "action_in_turn": 2,
    "message_index": 6,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_get_symbol_by_name",
      "arguments": {
        "name": "Quasar Ltd."
      }
    }
  },
  {
    "user_turn": 1,
    "action_in_turn": 3,
    "message_index": 8,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_get_stock_info",
      "arguments": {
        "symbol": "QUAS"
      }
    }
  },
  {
    "user_turn": 1,
    "action_in_turn": 4,
    "message_index": 10,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_add_to_watchlist",
      "arguments": {
        "stock": "QUAS"
      }
    }
  },
  {
    "user_turn": 3,
    "action_in_turn": 1,
    "message_index": 16,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_get_account_info",
      "arguments": {}
    }
  }
]
```

</details>

### QeRL：未通过

实际任务调用 7 次；[完整 CoT 和工具返回](QeRL/cot_and_actions.txt)。

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
        "name": "Quasar Ltd."
      }
    }
  },
  {
    "user_turn": 1,
    "action_in_turn": 2,
    "message_index": 6,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_get_stock_info",
      "arguments": {
        "symbol": "QUAS"
      }
    }
  },
  {
    "user_turn": 1,
    "action_in_turn": 3,
    "message_index": 8,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_add_to_watchlist",
      "arguments": {
        "stock": "QUAS"
      }
    }
  },
  {
    "user_turn": 2,
    "action_in_turn": 1,
    "message_index": 12,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_get_order_history",
      "arguments": {}
    }
  },
  {
    "user_turn": 2,
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
    "user_turn": 2,
    "action_in_turn": 3,
    "message_index": 16,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_get_order_details",
      "arguments": {
        "order_id": 12446
      }
    }
  },
  {
    "user_turn": 3,
    "action_in_turn": 1,
    "message_index": 20,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_get_account_info",
      "arguments": {}
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
    "field": "$.arguments.sector",
    "reference": "Finance",
    "actual": "Financial Services"
  }
]
```

### EfficientQAT

最早动作差异：第 1 个用户轮，第 1 个任务动作；BF16 消息 4，本方法消息 4。

```json
[
  {
    "field": "$.arguments.sector",
    "reference": "Finance",
    "actual": "Financial Services"
  }
]
```

### BitDistiller

最早动作差异：第 1 个用户轮，第 1 个任务动作；BF16 消息 4，本方法消息 4。

```json
[
  {
    "field": "$.arguments.parameters",
    "reference": null,
    "actual": {},
    "reference_present": false,
    "actual_present": true
  },
  {
    "field": "$.arguments.sector",
    "reference": "Finance",
    "actual": null,
    "reference_present": true,
    "actual_present": false
  }
]
```

### On-Policy QAD

最早动作差异：第 1 个用户轮，第 1 个任务动作；BF16 消息 4，本方法消息 4。

```json
[
  {
    "field": "$.arguments.sector",
    "reference": "Finance",
    "actual": "Financial Services"
  }
]
```

### QeRL

最早动作差异：第 1 个用户轮，第 1 个任务动作；BF16 消息 4，本方法消息 4。

```json
[
  {
    "field": "$.arguments.sector",
    "reference": "Finance",
    "actual": null,
    "reference_present": true,
    "actual_present": false
  }
]
```

## 失败原因

取消待处理订单这一步没有完成：多数 baseline 的订单 12446 仍为 Pending，参考状态为 Cancelled；On-Policy QAD 在该用户轮没有可执行任务调用。

### GPTQ

评分指出的失败位置/原因：

```text
"Model instance for TradingBot does not match the state with ground truth instance."
```

- 状态字段 `orders.12446.status`：实际 "Pending"；参考 "Cancelled"。
### EfficientQAT

评分指出的失败位置/原因：

```text
"Model instance for TradingBot does not match the state with ground truth instance."
```

- 状态字段 `orders.12446.status`：实际 "Pending"；参考 "Cancelled"。
### BitDistiller

评分指出的失败位置/原因：

```text
"Model instance for TradingBot does not match the state with ground truth instance."
```

- 状态字段 `orders.12446.status`：实际 "Pending"；参考 "Cancelled"。
### On-Policy QAD

评分指出的失败位置/原因：

```text
"Model response list is empty for turn 1"
```

### QeRL

评分指出的失败位置/原因：

```text
"Model instance for TradingBot does not match the state with ground truth instance."
```

- 状态字段 `orders.12446.status`：实际 "Pending"；参考 "Cancelled"。
