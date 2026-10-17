# Case 031 — multi_turn_miss_param_127

## 原始任务

第 1 轮：

I’m re-evaluating my current investment portfolio and need to make informed decisions. Could you display the some stocks?

第 2 轮：

The stocks that I am montoring.

第 3 轮：

Some stocks are underperforming and I wish to streamline my choices. Could we eliminate BDX from my observed list?

第 4 轮：

I have decided to take decisive action. Let's acquire 150 shares of BDX at the existing market value.

第 5 轮：

Upon completion, please furnish a detailed summary regarding the most recent order details on my account.

完整工具定义、初始状态及其他任务字段见 task.json。

## 七种方法的实际表现

### BF16：通过

购买后用订单号 12446 查询详情。

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
      "name": "mcp_tool_get_available_stocks",
      "arguments": {
        "sector": "Technology"
      }
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

按流程取得价格、购买，再查询该订单的详情。

实际任务调用 6 次；[完整 CoT 和工具返回](Ours/cot_and_actions.txt)。

<details><summary>实际动作序列</summary>

```json
[
  {
    "user_turn": 1,
    "action_in_turn": 1,
    "message_index": 4,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_get_available_stocks",
      "arguments": {
        "sector": "Technology"
      }
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

### GPTQ：未通过

完成购买，最后一轮没有详情工具调用。

实际任务调用 5 次；[完整 CoT 和工具返回](GPTQ/cot_and_actions.txt)。

<details><summary>实际动作序列</summary>

```json
[
  {
    "user_turn": 1,
    "action_in_turn": 1,
    "message_index": 4,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_get_available_stocks",
      "arguments": {
        "sector": "Technology"
      }
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

### EfficientQAT：未通过

成功提交订单，随后省略详情查询。

实际任务调用 5 次；[完整 CoT 和工具返回](EfficientQAT/cot_and_actions.txt)。

<details><summary>实际动作序列</summary>

```json
[
  {
    "user_turn": 1,
    "action_in_turn": 1,
    "message_index": 4,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_get_available_stocks",
      "arguments": {
        "sector": "Technology"
      }
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

### BitDistiller：未通过

下单动作正确，但没有取得最新订单详情。

实际任务调用 5 次；[完整 CoT 和工具返回](BitDistiller/cot_and_actions.txt)。

<details><summary>实际动作序列</summary>

```json
[
  {
    "user_turn": 1,
    "action_in_turn": 1,
    "message_index": 4,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_get_available_stocks",
      "arguments": {
        "sector": "Technology"
      }
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

### On-Policy QAD：未通过

漏查关注列表，购买后也没有查询订单详情。

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
      "name": "mcp_tool_get_available_stocks",
      "arguments": {
        "sector": "Technology"
      }
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
  }
]
```

</details>

### QeRL：未通过

购买成功后停留在自然语言回答，没有调用详情接口。

实际任务调用 4 次；[完整 CoT 和工具返回](QeRL/cot_and_actions.txt)。

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
      "name": "mcp_tool_get_stock_info",
      "arguments": {
        "symbol": "BDX"
      }
    }
  },
  {
    "user_turn": 4,
    "action_in_turn": 2,
    "message_index": 16,
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

- Ours：按用户轮和动作序号比较，任务动作序列与 BF16 相同。

### GPTQ

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

### EfficientQAT

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

### BitDistiller

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

### On-Policy QAD

最早动作差异：第 2 个用户轮，第 1 个任务动作；BF16 消息 8，本方法消息 None。

该位置没有对应任务调用；该轮 assistant 消息为 [8]。

```json
[
  {
    "field": "$",
    "reference": {
      "wrapper": "call_tool",
      "name": "mcp_tool_get_watchlist",
      "arguments": {}
    },
    "actual": null
  }
]
```

### QeRL

最早动作差异：第 1 个用户轮，第 1 个任务动作；BF16 消息 4，本方法消息 None。

该位置没有对应任务调用；该轮 assistant 消息为 [2, 4]。

```json
[
  {
    "field": "$",
    "reference": {
      "wrapper": "call_tool",
      "name": "mcp_tool_get_available_stocks",
      "arguments": {
        "sector": "Technology"
      }
    },
    "actual": null
  }
]
```

## 失败原因

五个 baseline 的所选轨迹都成功执行了购买，但在最后用户要求最新订单详情时没有调用 get_order_details；On-Policy QAD 还在更早的关注列表查询轮次省略了 get_watchlist。下单返回 Pending，只说明订单已提交，不能代替之后的详情查询。BF16 和 Ours 使用下单返回的订单号 12446 查询详情，得到当前订单信息。可观察的共同分歧在购买后的下一轮：是沿用旧下单结果直接答复，还是重新获取用户要求的最新详情。

### GPTQ

完成购买，最后一轮没有详情工具调用。

评分指出的失败位置/原因：

```text
"Model response list is empty for turn 4"
```

### EfficientQAT

成功提交订单，随后省略详情查询。

评分指出的失败位置/原因：

```text
"Model response list is empty for turn 4"
```

### BitDistiller

下单动作正确，但没有取得最新订单详情。

评分指出的失败位置/原因：

```text
"Model response list is empty for turn 4"
```

### On-Policy QAD

漏查关注列表，购买后也没有查询订单详情。

评分指出的失败位置/原因：

```text
"Model response list is empty for turn 1"
```

### QeRL

购买成功后停留在自然语言回答，没有调用详情接口。

评分指出的失败位置/原因：

```text
"Model response list is empty for turn 4"
```

