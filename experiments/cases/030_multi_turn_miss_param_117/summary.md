# Case 030 — multi_turn_miss_param_117

## 任务

第 1 轮：

I'd like some assistance today with my investment portfolio. If a specific company is part of my watchlist, please remove it for me. The market trends for their extractions are concerning me recently.

第 2 轮：

That specific company is Zeta Corp.

第 3 轮：

With my watchlist refreshed, please retrieve the current stocks still listed. I need a clear view of what remains on my radar.

第 4 轮：

I'm intrigued by the recent advancements in technology and wish to explore investment opportunities there. Could you provide a list of available technology stock symbols?

第 5 轮：

I've been observing Microsoft's stock performance and I find it quite compelling. Could you give me a detailed update on its current status and trends?

第 6 轮：

I'm ready to act on my analysis. Please purchase 50 shares of Microsoft at $320 each, given today's indicators.

第 7 轮：

Finally, before the end of the trading day, I intend to deposit 10 times the prices of OMEG rounded to nearest thousands into my trading account to secure liquidity for forthcoming ventures.

完整工具定义、初始状态及其他任务字段见 task.json。

## 七种方法的实际表现

### BF16：通过

实际任务调用 9 次；[完整 CoT 和工具返回](BF16/cot_and_actions.txt)。

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
      "name": "mcp_tool_remove_stock_from_watchlist",
      "arguments": {
        "symbol": "ZETA"
      }
    }
  },
  {
    "user_turn": 3,
    "action_in_turn": 1,
    "message_index": 12,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_get_watchlist",
      "arguments": {}
    }
  },
  {
    "user_turn": 4,
    "action_in_turn": 1,
    "message_index": 16,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_get_available_stocks",
      "arguments": {
        "sector": "Technology"
      }
    }
  },
  {
    "user_turn": 5,
    "action_in_turn": 1,
    "message_index": 20,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_get_stock_info",
      "arguments": {
        "symbol": "MSFT"
      }
    }
  },
  {
    "user_turn": 6,
    "action_in_turn": 1,
    "message_index": 24,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_get_account_info",
      "arguments": {}
    }
  },
  {
    "user_turn": 6,
    "action_in_turn": 2,
    "message_index": 26,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_place_order",
      "arguments": {
        "order_type": "Buy",
        "symbol": "MSFT",
        "price": 320,
        "amount": 50
      }
    }
  },
  {
    "user_turn": 7,
    "action_in_turn": 1,
    "message_index": 30,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_get_stock_info",
      "arguments": {
        "symbol": "OMEG"
      }
    }
  },
  {
    "user_turn": 7,
    "action_in_turn": 2,
    "message_index": 32,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_fund_account",
      "arguments": {
        "amount": 5000
      }
    }
  }
]
```

</details>

### Ours：通过

实际任务调用 9 次；[完整 CoT 和工具返回](Ours/cot_and_actions.txt)。

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
      "name": "mcp_tool_remove_stock_from_watchlist",
      "arguments": {
        "symbol": "ZETA"
      }
    }
  },
  {
    "user_turn": 3,
    "action_in_turn": 1,
    "message_index": 14,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_get_watchlist",
      "arguments": {}
    }
  },
  {
    "user_turn": 4,
    "action_in_turn": 1,
    "message_index": 18,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_get_available_stocks",
      "arguments": {
        "sector": "Technology"
      }
    }
  },
  {
    "user_turn": 5,
    "action_in_turn": 1,
    "message_index": 22,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_get_stock_info",
      "arguments": {
        "symbol": "MSFT"
      }
    }
  },
  {
    "user_turn": 6,
    "action_in_turn": 1,
    "message_index": 26,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_place_order",
      "arguments": {
        "order_type": "Buy",
        "symbol": "MSFT",
        "price": 320,
        "amount": 50
      }
    }
  },
  {
    "user_turn": 7,
    "action_in_turn": 1,
    "message_index": 30,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_get_stock_info",
      "arguments": {
        "symbol": "OMEG"
      }
    }
  },
  {
    "user_turn": 7,
    "action_in_turn": 2,
    "message_index": 32,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_fund_account",
      "arguments": {
        "amount": 5000
      }
    }
  }
]
```

</details>

### GPTQ：未通过

实际任务调用 10 次；[完整 CoT 和工具返回](GPTQ/cot_and_actions.txt)。

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
    "user_turn": 1,
    "action_in_turn": 2,
    "message_index": 6,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_notify_price_change",
      "arguments": {
        "stocks": [
          "NVDA",
          "ZETA"
        ],
        "threshold": -10
      }
    }
  },
  {
    "user_turn": 1,
    "action_in_turn": 3,
    "message_index": 8,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_remove_stock_from_watchlist",
      "arguments": {
        "symbol": "NVDA"
      }
    }
  },
  {
    "user_turn": 2,
    "action_in_turn": 1,
    "message_index": 12,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_remove_stock_from_watchlist",
      "arguments": {
        "symbol": "ZETA"
      }
    }
  },
  {
    "user_turn": 3,
    "action_in_turn": 1,
    "message_index": 16,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_get_watchlist",
      "arguments": {}
    }
  },
  {
    "user_turn": 4,
    "action_in_turn": 1,
    "message_index": 20,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_get_available_stocks",
      "arguments": {
        "sector": "Technology"
      }
    }
  },
  {
    "user_turn": 5,
    "action_in_turn": 1,
    "message_index": 24,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_get_stock_info",
      "arguments": {
        "symbol": "MSFT"
      }
    }
  },
  {
    "user_turn": 6,
    "action_in_turn": 1,
    "message_index": 28,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_place_order",
      "arguments": {
        "order_type": "Buy",
        "symbol": "MSFT",
        "price": 320,
        "amount": 50
      }
    }
  },
  {
    "user_turn": 7,
    "action_in_turn": 1,
    "message_index": 32,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_get_stock_info",
      "arguments": {
        "symbol": "OMEG"
      }
    }
  },
  {
    "user_turn": 7,
    "action_in_turn": 2,
    "message_index": 34,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_fund_account",
      "arguments": {
        "amount": 5000
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
      "name": "mcp_tool_get_watchlist",
      "arguments": {}
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
        "symbol": "NVDA"
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
        "symbol": "ZETA"
      }
    }
  },
  {
    "user_turn": 2,
    "action_in_turn": 1,
    "message_index": 12,
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
    "message_index": 14,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_remove_stock_from_watchlist",
      "arguments": {
        "symbol": "ZETA"
      }
    }
  },
  {
    "user_turn": 3,
    "action_in_turn": 1,
    "message_index": 18,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_get_watchlist",
      "arguments": {}
    }
  },
  {
    "user_turn": 4,
    "action_in_turn": 1,
    "message_index": 22,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_get_available_stocks",
      "arguments": {
        "sector": "technology"
      }
    }
  },
  {
    "user_turn": 5,
    "action_in_turn": 1,
    "message_index": 26,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_get_symbol_by_name",
      "arguments": {
        "name": "Microsoft"
      }
    }
  },
  {
    "user_turn": 5,
    "action_in_turn": 2,
    "message_index": 28,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_get_stock_info",
      "arguments": {
        "symbol": "MSFT"
      }
    }
  },
  {
    "user_turn": 6,
    "action_in_turn": 1,
    "message_index": 32,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_place_order",
      "arguments": {
        "order_type": "Buy",
        "symbol": "MSFT",
        "price": 320,
        "amount": 50
      }
    }
  },
  {
    "user_turn": 7,
    "action_in_turn": 1,
    "message_index": 36,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_get_symbol_by_name",
      "arguments": {
        "name": "OMEG"
      }
    }
  }
]
```

</details>

### BitDistiller：未通过

实际任务调用 7 次；[完整 CoT 和工具返回](BitDistiller/cot_and_actions.txt)。

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
      "name": "mcp_tool_remove_stock_from_watchlist",
      "arguments": {
        "symbol": "ZETA"
      }
    }
  },
  {
    "user_turn": 3,
    "action_in_turn": 1,
    "message_index": 12,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_get_watchlist",
      "arguments": {}
    }
  },
  {
    "user_turn": 4,
    "action_in_turn": 1,
    "message_index": 16,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_get_available_stocks",
      "arguments": {
        "sector": "Technology"
      }
    }
  },
  {
    "user_turn": 5,
    "action_in_turn": 1,
    "message_index": 20,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_get_stock_info",
      "arguments": {
        "symbol": "MSFT"
      }
    }
  },
  {
    "user_turn": 6,
    "action_in_turn": 1,
    "message_index": 24,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_place_order",
      "arguments": {
        "order_type": "Buy",
        "symbol": "MSFT",
        "price": 320,
        "amount": 50
      }
    }
  },
  {
    "user_turn": 7,
    "action_in_turn": 1,
    "message_index": 28,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_get_stock_info",
      "arguments": {
        "symbol": "OMEGA"
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
      "name": "mcp_tool_get_watchlist",
      "arguments": {}
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
        "symbol": "NVDA"
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
        "symbol": "ZETA"
      }
    }
  },
  {
    "user_turn": 2,
    "action_in_turn": 1,
    "message_index": 12,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_get_symbol_by_name",
      "arguments": {
        "name": "Zeta Corp"
      }
    }
  },
  {
    "user_turn": 3,
    "action_in_turn": 1,
    "message_index": 16,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_get_watchlist",
      "arguments": {}
    }
  },
  {
    "user_turn": 4,
    "action_in_turn": 1,
    "message_index": 20,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_get_available_stocks",
      "arguments": {
        "sector": "Technology"
      }
    }
  },
  {
    "user_turn": 5,
    "action_in_turn": 1,
    "message_index": 24,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_get_stock_info",
      "arguments": {
        "symbol": "MSFT"
      }
    }
  },
  {
    "user_turn": 6,
    "action_in_turn": 1,
    "message_index": 28,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_place_order",
      "arguments": {
        "order_type": "Buy",
        "symbol": "MSFT",
        "price": 320,
        "amount": 50
      }
    }
  },
  {
    "user_turn": 7,
    "action_in_turn": 1,
    "message_index": 32,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_get_stock_info",
      "arguments": {
        "symbol": "OMEG"
      }
    }
  },
  {
    "user_turn": 7,
    "action_in_turn": 2,
    "message_index": 34,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_fund_account",
      "arguments": {
        "amount": 5000
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
      "name": "mcp_tool_get_watchlist",
      "arguments": {}
    }
  },
  {
    "user_turn": 1,
    "action_in_turn": 2,
    "message_index": 6,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_remove_stock_from_watchlist",
      "arguments": {
        "symbol": "NVDA"
      }
    }
  },
  {
    "user_turn": 1,
    "action_in_turn": 3,
    "message_index": 8,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_remove_stock_from_watchlist",
      "arguments": {
        "symbol": "ZETA"
      }
    }
  },
  {
    "user_turn": 1,
    "action_in_turn": 4,
    "message_index": 10,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_get_watchlist",
      "arguments": {}
    }
  },
  {
    "user_turn": 3,
    "action_in_turn": 1,
    "message_index": 16,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_get_watchlist",
      "arguments": {}
    }
  },
  {
    "user_turn": 4,
    "action_in_turn": 1,
    "message_index": 20,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_get_available_stocks",
      "arguments": {
        "sector": "Technology"
      }
    }
  },
  {
    "user_turn": 5,
    "action_in_turn": 1,
    "message_index": 24,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_get_stock_info",
      "arguments": {
        "symbol": "MSFT"
      }
    }
  },
  {
    "user_turn": 6,
    "action_in_turn": 1,
    "message_index": 28,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_place_order",
      "arguments": {
        "order_type": "Buy",
        "symbol": "MSFT",
        "price": 320,
        "amount": 50
      }
    }
  },
  {
    "user_turn": 7,
    "action_in_turn": 1,
    "message_index": 32,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_get_stock_info",
      "arguments": {
        "symbol": "OMEG"
      }
    }
  },
  {
    "user_turn": 7,
    "action_in_turn": 2,
    "message_index": 34,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_fund_account",
      "arguments": {
        "amount": 5000
      }
    }
  }
]
```

</details>

## 分歧位置

消息编号从 0 开始，用户轮和动作编号从 1 开始。按同一用户轮的任务动作序号与 BF16 比较，忽略 list_tools。最早动作差异不一定就是失败起点：正确的工具顺序、补救步骤也可能不同；评分失败位置另见下一节。

### Ours

最早动作差异：第 1 个用户轮，第 1 个任务动作；BF16 消息 None，本方法消息 4。

```json
[
  {
    "field": "$",
    "reference": null,
    "actual": {
      "wrapper": "call_tool",
      "name": "mcp_tool_get_watchlist",
      "arguments": {}
    }
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
      "name": "mcp_tool_get_watchlist",
      "arguments": {}
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
      "name": "mcp_tool_get_watchlist",
      "arguments": {}
    }
  }
]
```

### BitDistiller

最早动作差异：第 6 个用户轮，第 1 个任务动作；BF16 消息 24，本方法消息 24。

```json
[
  {
    "field": "$.arguments.amount",
    "reference": null,
    "actual": 50,
    "reference_present": false,
    "actual_present": true
  },
  {
    "field": "$.arguments.order_type",
    "reference": null,
    "actual": "Buy",
    "reference_present": false,
    "actual_present": true
  },
  {
    "field": "$.arguments.price",
    "reference": null,
    "actual": 320,
    "reference_present": false,
    "actual_present": true
  },
  {
    "field": "$.arguments.symbol",
    "reference": null,
    "actual": "MSFT",
    "reference_present": false,
    "actual_present": true
  },
  {
    "field": "$.name",
    "reference": "mcp_tool_get_account_info",
    "actual": "mcp_tool_place_order"
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
      "name": "mcp_tool_get_watchlist",
      "arguments": {}
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
      "name": "mcp_tool_get_watchlist",
      "arguments": {}
    }
  }
]
```

## 失败原因

失败分布在关注列表、股票列表查询、账户交易状态和缺失调用，不能统一说成首次股票查询出错。

### GPTQ

评分指出的失败位置/原因：

```text
"Model instance for TradingBot does not match the state with ground truth instance."
```

- 状态字段 `watch_list[0]`：实际 null；参考 "NVDA"。
### EfficientQAT

评分指出的失败位置/原因：

```text
"Model response execution results so far does not contain all the ground truth response execution results for turn 3."
```


缺少的执行返回：

```text
["{\"stock_list\": [\"AAPL\", \"GOOG\", \"MSFT\", \"NVDA\"]}"]
```

### BitDistiller

评分指出的失败位置/原因：

```text
"Model instance for TradingBot does not match the state with ground truth instance."
```

- 状态字段 `account_info.balance`：实际 16000.0；参考 21000.0。
- 状态字段 `transaction_history[0]`：实际 null；参考 {"type": "deposit", "amount": 5000, "timestamp": "2024-09-02 05:40:15"}。
### On-Policy QAD

评分指出的失败位置/原因：

```text
"Model instance for TradingBot does not match the state with ground truth instance."
```

- 状态字段 `watch_list[1]`：实际 "ZETA"；参考 null。
### QeRL

评分指出的失败位置/原因：

```text
"Model response list is empty for turn 1"
```
