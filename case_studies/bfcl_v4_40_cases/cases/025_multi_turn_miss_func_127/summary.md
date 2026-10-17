# Case 025 — multi_turn_miss_func_127

## 原始任务

第 1 轮：

I’m re-evaluating my current investment portfolio and need to make informed decisions. Could you display the current stocks I am monitoring?

第 2 轮：

第 3 轮：

Some stocks are underperforming and I wish to streamline my choices. Could we eliminate BDX from my observed list?

第 4 轮：

I have decided to take decisive action. Let's acquire 150 shares of BDX at the existing market value.

第 5 轮：

Upon completion, please furnish a detailed summary regarding the most recent order details on my account.

完整工具定义、初始状态及其他任务字段见 task.json。

## 七种方法的实际表现

### BF16：通过

实际任务调用 6 次；[完整 CoT 和工具返回](BF16/cot_and_actions.txt)。

<details><summary>实际动作序列</summary>

```json
[
  {
    "user_turn": 1,
    "action_in_turn": 1,
    "message_index": 4,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_get_account_info",
      "arguments": {}
    }
  },
  {
    "user_turn": 2,
    "action_in_turn": 1,
    "message_index": 8,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_get_watchlist",
      "arguments": {}
    }
  },
  {
    "user_turn": 3,
    "action_in_turn": 1,
    "message_index": 12,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_remove_stock_from_watchlist",
      "arguments": {
        "symbol": "BDX"
      }
    }
  },
  {
    "user_turn": 4,
    "action_in_turn": 1,
    "message_index": 16,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_get_stock_info",
      "arguments": {
        "symbol": "BDX"
      }
    }
  },
  {
    "user_turn": 4,
    "action_in_turn": 2,
    "message_index": 18,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_place_order",
      "arguments": {
        "order_type": "Buy",
        "symbol": "BDX",
        "price": 250.0,
        "amount": 150
      }
    }
  },
  {
    "user_turn": 5,
    "action_in_turn": 1,
    "message_index": 22,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_get_order_details",
      "arguments": {
        "order_id": 12446
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
    "user_turn": 2,
    "action_in_turn": 1,
    "message_index": 6,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_get_watchlist",
      "arguments": {}
    }
  },
  {
    "user_turn": 3,
    "action_in_turn": 1,
    "message_index": 10,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_remove_stock_from_watchlist",
      "arguments": {
        "symbol": "BDX"
      }
    }
  },
  {
    "user_turn": 4,
    "action_in_turn": 1,
    "message_index": 14,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_trading_get_login_status",
      "arguments": {}
    }
  },
  {
    "user_turn": 4,
    "action_in_turn": 2,
    "message_index": 16,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_get_stock_info",
      "arguments": {
        "symbol": "BDX"
      }
    }
  },
  {
    "user_turn": 4,
    "action_in_turn": 3,
    "message_index": 18,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_place_order",
      "arguments": {
        "order_type": "Buy",
        "symbol": "BDX",
        "price": 250.0,
        "amount": 150
      }
    }
  },
  {
    "user_turn": 5,
    "action_in_turn": 1,
    "message_index": 22,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_get_order_details",
      "arguments": {
        "order_id": 12446
      }
    }
  }
]
```

</details>

### GPTQ：未通过

实际任务调用 7 次；[完整 CoT 和工具返回](GPTQ/cot_and_actions.txt)。

<details><summary>实际动作序列</summary>

```json
[
  {
    "user_turn": 1,
    "action_in_turn": 1,
    "message_index": 4,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_get_order_history",
      "arguments": {}
    }
  },
  {
    "user_turn": 2,
    "action_in_turn": 1,
    "message_index": 8,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_get_watchlist",
      "arguments": {}
    }
  },
  {
    "user_turn": 3,
    "action_in_turn": 1,
    "message_index": 12,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_remove_stock_from_watchlist",
      "arguments": {
        "symbol": "BDX"
      }
    }
  },
  {
    "user_turn": 5,
    "action_in_turn": 1,
    "message_index": 18,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_trading_login",
      "arguments": {
        "username": "user123",
        "password": "securepass"
      }
    }
  },
  {
    "user_turn": 5,
    "action_in_turn": 2,
    "message_index": 20,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_get_stock_info",
      "arguments": {
        "symbol": "BDX"
      }
    }
  },
  {
    "user_turn": 5,
    "action_in_turn": 3,
    "message_index": 22,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_place_order",
      "arguments": {
        "order_type": "Buy",
        "symbol": "BDX",
        "price": 250.0,
        "amount": 150
      }
    }
  },
  {
    "user_turn": 5,
    "action_in_turn": 4,
    "message_index": 24,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_get_order_details",
      "arguments": {
        "order_id": 12446
      }
    }
  }
]
```

</details>

### EfficientQAT：未通过

实际任务调用 7 次；[完整 CoT 和工具返回](EfficientQAT/cot_and_actions.txt)。

<details><summary>实际动作序列</summary>

```json
[
  {
    "user_turn": 1,
    "action_in_turn": 1,
    "message_index": 4,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_get_watchlist",
      "arguments": {}
    }
  },
  {
    "user_turn": 3,
    "action_in_turn": 1,
    "message_index": 10,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_remove_stock_from_watchlist",
      "arguments": {
        "symbol": "BDX"
      }
    }
  },
  {
    "user_turn": 4,
    "action_in_turn": 1,
    "message_index": 14,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_trading_get_login_status",
      "arguments": {}
    }
  },
  {
    "user_turn": 4,
    "action_in_turn": 2,
    "message_index": 16,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_get_stock_info",
      "arguments": {
        "symbol": "BDX"
      }
    }
  },
  {
    "user_turn": 4,
    "action_in_turn": 3,
    "message_index": 18,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_get_account_info",
      "arguments": {}
    }
  },
  {
    "user_turn": 4,
    "action_in_turn": 4,
    "message_index": 20,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_place_order",
      "arguments": {
        "order_type": "BUY",
        "symbol": "BDX",
        "price": 250.0,
        "amount": 150
      }
    }
  },
  {
    "user_turn": 5,
    "action_in_turn": 1,
    "message_index": 24,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_get_order_details",
      "arguments": {
        "order_id": 12446
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
      "name": "mcp_tool_get_order_history",
      "arguments": {}
    }
  },
  {
    "user_turn": 2,
    "action_in_turn": 1,
    "message_index": 8,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_get_watchlist",
      "arguments": {}
    }
  },
  {
    "user_turn": 3,
    "action_in_turn": 1,
    "message_index": 12,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_remove_stock_from_watchlist",
      "arguments": {
        "symbol": "BDX"
      }
    }
  },
  {
    "user_turn": 4,
    "action_in_turn": 1,
    "message_index": 16,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_trading_get_login_status",
      "arguments": {}
    }
  },
  {
    "user_turn": 4,
    "action_in_turn": 2,
    "message_index": 18,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_get_stock_info",
      "arguments": {
        "symbol": "BDX"
      }
    }
  },
  {
    "user_turn": 4,
    "action_in_turn": 3,
    "message_index": 20,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_place_order",
      "arguments": {
        "order_type": "Buy",
        "symbol": "BDX",
        "price": 250.0,
        "amount": 150
      }
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
      "name": "mcp_tool_get_watchlist",
      "arguments": {}
    }
  },
  {
    "user_turn": 3,
    "action_in_turn": 1,
    "message_index": 10,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_remove_stock_from_watchlist",
      "arguments": {
        "symbol": "BDX"
      }
    }
  },
  {
    "user_turn": 5,
    "action_in_turn": 1,
    "message_index": 16,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_get_stock_info",
      "arguments": {
        "symbol": "BDX"
      }
    }
  },
  {
    "user_turn": 5,
    "action_in_turn": 2,
    "message_index": 18,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_place_order",
      "arguments": {
        "order_type": "Buy",
        "symbol": "BDX",
        "price": 250.0,
        "amount": 150
      }
    }
  },
  {
    "user_turn": 5,
    "action_in_turn": 3,
    "message_index": 20,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_get_order_details",
      "arguments": {
        "order_id": 12446
      }
    }
  }
]
```

</details>

### QeRL：未通过

实际任务调用 5 次；[完整 CoT 和工具返回](QeRL/cot_and_actions.txt)。

<details><summary>实际动作序列</summary>

```json
[
  {
    "user_turn": 1,
    "action_in_turn": 1,
    "message_index": 4,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_get_account_info",
      "arguments": {}
    }
  },
  {
    "user_turn": 2,
    "action_in_turn": 1,
    "message_index": 8,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_get_watchlist",
      "arguments": {}
    }
  },
  {
    "user_turn": 3,
    "action_in_turn": 1,
    "message_index": 12,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_remove_stock_from_watchlist",
      "arguments": {
        "symbol": "BDX"
      }
    }
  },
  {
    "user_turn": 4,
    "action_in_turn": 1,
    "message_index": 16,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_get_stock_info",
      "arguments": {
        "symbol": "BDX"
      }
    }
  },
  {
    "user_turn": 4,
    "action_in_turn": 2,
    "message_index": 18,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_place_order",
      "arguments": {
        "order_type": "Buy",
        "symbol": "BDX",
        "price": 250.0,
        "amount": 150
      }
    }
  }
]
```

</details>

## 分歧位置

消息编号从 0 开始，用户轮和动作编号从 1 开始。按同一用户轮的任务动作序号与 BF16 比较，忽略 list_tools。最早动作差异不一定就是失败起点：正确的工具顺序、补救步骤也可能不同；评分失败位置另见下一节。

### Ours

最早动作差异：第 1 个用户轮，第 1 个任务动作；BF16 消息 4，本方法消息 None。

该位置没有对应任务调用；该轮 assistant 消息为 [2, 4]。

```json
[
  {
    "field": "$",
    "reference": {
      "wrapper": "call_tool",
      "name": "mcp_tool_get_account_info",
      "arguments": {}
    },
    "actual": null
  }
]
```

### GPTQ

最早动作差异：第 1 个用户轮，第 1 个任务动作；BF16 消息 4，本方法消息 4。

```json
[
  {
    "field": "$.name",
    "reference": "mcp_tool_get_account_info",
    "actual": "mcp_tool_get_order_history"
  }
]
```

### EfficientQAT

最早动作差异：第 1 个用户轮，第 1 个任务动作；BF16 消息 4，本方法消息 4。

```json
[
  {
    "field": "$.name",
    "reference": "mcp_tool_get_account_info",
    "actual": "mcp_tool_get_watchlist"
  }
]
```

### BitDistiller

最早动作差异：第 1 个用户轮，第 1 个任务动作；BF16 消息 4，本方法消息 4。

```json
[
  {
    "field": "$.name",
    "reference": "mcp_tool_get_account_info",
    "actual": "mcp_tool_get_order_history"
  }
]
```

### On-Policy QAD

最早动作差异：第 1 个用户轮，第 1 个任务动作；BF16 消息 4，本方法消息 4。

```json
[
  {
    "field": "$.name",
    "reference": "mcp_tool_get_account_info",
    "actual": "mcp_tool_get_watchlist"
  }
]
```

### QeRL

最早动作差异：第 5 个用户轮，第 1 个任务动作；BF16 消息 22，本方法消息 None。

该位置没有对应任务调用；该轮 assistant 消息为 [22]。

```json
[
  {
    "field": "$",
    "reference": {
      "wrapper": "call_tool",
      "name": "mcp_tool_get_order_details",
      "arguments": {
        "order_id": 12446
      }
    },
    "actual": null
  }
]
```

## 失败原因

部分 baseline 在购买或详情查询轮没有调用；EfficientQAT 的订单状态不匹配。缺少可用工具时的澄清轮和后续实际执行轮需要分开看。

### GPTQ

评分指出的失败位置/原因：

```text
"Model response list is empty for turn 3"
```

### EfficientQAT

评分指出的失败位置/原因：

```text
"Model instance for TradingBot does not match the state with ground truth instance."
```

- 状态字段 `orders.12446.order_type`：实际 "BUY"；参考 "Buy"。
### BitDistiller

评分指出的失败位置/原因：

```text
"Model response list is empty for turn 4"
```

### On-Policy QAD

评分指出的失败位置/原因：

```text
"Model response list is empty for turn 3"
```

### QeRL

评分指出的失败位置/原因：

```text
"Model response list is empty for turn 4"
```

