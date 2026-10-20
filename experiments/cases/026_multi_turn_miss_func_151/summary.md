# Case 026 — multi_turn_miss_func_151

## 任务

第 1 轮：

A complex decision awaits me. I'm planning an upcoming trip with limited resources and reevaluating my options. Could you first provide an estimate for a business class flight from San Francisco International to Los Angeles next Tuesday, November 10th, 2026, for an essential business engagement? Once the cost is known, please convert the estimate from USD to EUR for budgeting purposes, and if the cost is under 2000, proceed to book the flight using the secured credit card ID 144756014165 and access token abc123xyz.

第 2 轮：

第 3 轮：

Due to unforeseen circumstances, I'm unable to proceed with my journey to Los Angeles next week. Could the system initiate a cancellation process for the flight booking made earlier?

第 4 轮：

I believe it would be strategic to communicate these adjustments to my extended network. Construct a tweet highlighting the cancellation of my travel plans, and ensure to add relevant hashtags 'TravelUpdate' and 'BusinessTrip' relating to travel and business updates, for message, just tell that 'Just cancelled my trip to LA'. Be sure to authenticate using my username 'john' and password 'john1234'.

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
      "name": "mcp_tool_get_flight_cost",
      "arguments": {
        "travel_from": "SFO",
        "travel_to": "LAX",
        "travel_date": "2026-11-10",
        "travel_class": "business"
      }
    }
  },
  {
    "user_turn": 1,
    "action_in_turn": 2,
    "message_index": 6,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_compute_exchange_rate",
      "arguments": {
        "base_currency": "USD",
        "target_currency": "EUR",
        "value": 400.0
      }
    }
  },
  {
    "user_turn": 2,
    "action_in_turn": 1,
    "message_index": 10,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_book_flight",
      "arguments": {
        "access_token": "abc123xyz",
        "card_id": "144756014165",
        "travel_date": "2026-11-10",
        "travel_from": "SFO",
        "travel_to": "LAX",
        "travel_class": "business"
      }
    }
  },
  {
    "user_turn": 3,
    "action_in_turn": 1,
    "message_index": 14,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_cancel_booking",
      "arguments": {
        "access_token": "abc123xyz",
        "booking_id": "3426812"
      }
    }
  },
  {
    "user_turn": 4,
    "action_in_turn": 1,
    "message_index": 18,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_authenticate_twitter",
      "arguments": {
        "username": "john",
        "password": "john1234"
      }
    }
  },
  {
    "user_turn": 4,
    "action_in_turn": 2,
    "message_index": 20,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_post_tweet",
      "arguments": "{\"content\": \"Just cancelled my trip to LA\", \"tags\": ['#TravelUpdate', '#BusinessTrip']}"
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
    "user_turn": 1,
    "action_in_turn": 1,
    "message_index": 4,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_get_flight_cost",
      "arguments": {
        "travel_from": "SFO",
        "travel_to": "LAX",
        "travel_date": "2026-11-10",
        "travel_class": "business"
      }
    }
  },
  {
    "user_turn": 1,
    "action_in_turn": 2,
    "message_index": 6,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_compute_exchange_rate",
      "arguments": {
        "base_currency": "USD",
        "target_currency": "EUR",
        "value": 400.0
      }
    }
  },
  {
    "user_turn": 2,
    "action_in_turn": 1,
    "message_index": 10,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_book_flight",
      "arguments": {
        "access_token": "abc123xyz",
        "card_id": "144756014165",
        "travel_date": "2026-11-10",
        "travel_from": "SFO",
        "travel_to": "LAX",
        "travel_class": "business"
      }
    }
  },
  {
    "user_turn": 3,
    "action_in_turn": 1,
    "message_index": 14,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_cancel_booking",
      "arguments": {
        "access_token": "abc123xyz",
        "booking_id": "3426812"
      }
    }
  },
  {
    "user_turn": 4,
    "action_in_turn": 1,
    "message_index": 18,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_authenticate_twitter",
      "arguments": {
        "username": "john",
        "password": "john1234"
      }
    }
  },
  {
    "user_turn": 4,
    "action_in_turn": 2,
    "message_index": 20,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_post_tweet",
      "arguments": {
        "content": "Just cancelled my trip to LA",
        "tags": [
          "#TravelUpdate",
          "#BusinessTrip"
        ]
      }
    }
  }
]
```

</details>

### GPTQ：未通过

实际任务调用 6 次；[完整 CoT 和工具返回](GPTQ/cot_and_actions.txt)。

<details><summary>实际动作序列</summary>

```json
[
  {
    "user_turn": 1,
    "action_in_turn": 1,
    "message_index": 4,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_get_flight_cost",
      "arguments": {
        "travel_from": "SFO",
        "travel_to": "LAX",
        "travel_date": "2026-11-10",
        "travel_class": "business"
      }
    }
  },
  {
    "user_turn": 1,
    "action_in_turn": 2,
    "message_index": 6,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_compute_exchange_rate",
      "arguments": {
        "base_currency": "USD",
        "target_currency": "EUR",
        "value": 400.0
      }
    }
  },
  {
    "user_turn": 2,
    "action_in_turn": 1,
    "message_index": 10,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_book_flight",
      "arguments": {
        "access_token": "abc123xyz",
        "card_id": "144756014165",
        "travel_date": "2026-11-10",
        "travel_from": "SFO",
        "travel_to": "LAX",
        "travel_class": "business"
      }
    }
  },
  {
    "user_turn": 3,
    "action_in_turn": 1,
    "message_index": 14,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_cancel_booking",
      "arguments": {
        "access_token": "abc123xyz",
        "booking_id": "3426812"
      }
    }
  },
  {
    "user_turn": 4,
    "action_in_turn": 1,
    "message_index": 18,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_authenticate_twitter",
      "arguments": {
        "username": "john",
        "password": "john1234"
      }
    }
  },
  {
    "user_turn": 4,
    "action_in_turn": 2,
    "message_index": 20,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_post_tweet",
      "arguments": {
        "content": "Just cancelled my trip to LA #TravelUpdate #BusinessTrip"
      }
    }
  }
]
```

</details>

### EfficientQAT：未通过

实际任务调用 6 次；[完整 CoT 和工具返回](EfficientQAT/cot_and_actions.txt)。

<details><summary>实际动作序列</summary>

```json
[
  {
    "user_turn": 1,
    "action_in_turn": 1,
    "message_index": 4,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_get_flight_cost",
      "arguments": {
        "travel_from": "SFO",
        "travel_to": "LAX",
        "travel_date": "2026-11-10",
        "travel_class": "business"
      }
    }
  },
  {
    "user_turn": 1,
    "action_in_turn": 2,
    "message_index": 6,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_compute_exchange_rate",
      "arguments": {
        "base_currency": "USD",
        "target_currency": "EUR",
        "value": 400.0
      }
    }
  },
  {
    "user_turn": 2,
    "action_in_turn": 1,
    "message_index": 10,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_book_flight",
      "arguments": {
        "access_token": "abc123xyz",
        "card_id": "144756014165",
        "travel_date": "2026-11-10",
        "travel_from": "SFO",
        "travel_to": "LAX",
        "travel_class": "business"
      }
    }
  },
  {
    "user_turn": 3,
    "action_in_turn": 1,
    "message_index": 14,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_cancel_booking",
      "arguments": {
        "access_token": "abc123xyz",
        "booking_id": "3426812"
      }
    }
  },
  {
    "user_turn": 4,
    "action_in_turn": 1,
    "message_index": 18,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_authenticate_twitter",
      "arguments": {
        "username": "john",
        "password": "john1234"
      }
    }
  },
  {
    "user_turn": 4,
    "action_in_turn": 2,
    "message_index": 20,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_post_tweet",
      "arguments": {
        "content": "Just cancelled my trip to LA #TravelUpdate #BusinessTrip"
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
      "name": "mcp_tool_get_flight_cost",
      "arguments": {
        "travel_from": "SFO",
        "travel_to": "LAX",
        "travel_date": "2026-11-10",
        "travel_class": "business"
      }
    }
  },
  {
    "user_turn": 1,
    "action_in_turn": 2,
    "message_index": 6,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_compute_exchange_rate",
      "arguments": {
        "base_currency": "USD",
        "target_currency": "EUR",
        "value": 400.0
      }
    }
  },
  {
    "user_turn": 2,
    "action_in_turn": 1,
    "message_index": 10,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_book_flight",
      "arguments": {
        "access_token": "abc123xyz",
        "card_id": "144756014165",
        "travel_date": "2026-11-10",
        "travel_from": "SFO",
        "travel_to": "LAX",
        "travel_class": "business"
      }
    }
  },
  {
    "user_turn": 3,
    "action_in_turn": 1,
    "message_index": 14,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_cancel_booking",
      "arguments": {
        "access_token": "abc123xyz",
        "booking_id": "3426812"
      }
    }
  },
  {
    "user_turn": 4,
    "action_in_turn": 1,
    "message_index": 18,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_authenticate_twitter",
      "arguments": {
        "username": "john",
        "password": "john1234"
      }
    }
  },
  {
    "user_turn": 4,
    "action_in_turn": 2,
    "message_index": 20,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_post_tweet",
      "arguments": "{\"content\": \"Just cancelled my trip to LA\","
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
    "user_turn": 1,
    "action_in_turn": 1,
    "message_index": 4,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_get_flight_cost",
      "arguments": {
        "travel_from": "SFO",
        "travel_to": "LAX",
        "travel_date": "2026-11-10",
        "travel_class": "business"
      }
    }
  },
  {
    "user_turn": 1,
    "action_in_turn": 2,
    "message_index": 6,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_compute_exchange_rate",
      "arguments": {
        "base_currency": "USD",
        "target_currency": "EUR",
        "value": 400.0
      }
    }
  },
  {
    "user_turn": 1,
    "action_in_turn": 3,
    "message_index": 8,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_book_flight",
      "arguments": {
        "access_token": "abc123xyz",
        "card_id": "144756014165",
        "travel_date": "2026-11-10",
        "travel_from": "SFO",
        "travel_to": "LAX",
        "travel_class": "business"
      }
    }
  },
  {
    "user_turn": 3,
    "action_in_turn": 1,
    "message_index": 14,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_cancel_booking",
      "arguments": {
        "access_token": "abc123xyz",
        "booking_id": "3426812"
      }
    }
  },
  {
    "user_turn": 4,
    "action_in_turn": 1,
    "message_index": 18,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_authenticate_twitter",
      "arguments": {
        "username": "john",
        "password": "john1234"
      }
    }
  },
  {
    "user_turn": 4,
    "action_in_turn": 2,
    "message_index": 20,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_post_tweet",
      "arguments": {
        "content": "Just cancelled my trip to LA",
        "tags": [
          "TravelUpdate",
          "BusinessTrip"
        ]
      }
    }
  },
  {
    "user_turn": 4,
    "action_in_turn": 3,
    "message_index": 22,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_post_tweet",
      "arguments": {
        "content": "Just cancelled my trip to LA",
        "tags": [
          "TravelUpdate",
          "BusinessTrip"
        ]
      }
    }
  }
]
```

</details>

### QeRL：未通过

实际任务调用 6 次；[完整 CoT 和工具返回](QeRL/cot_and_actions.txt)。

<details><summary>实际动作序列</summary>

```json
[
  {
    "user_turn": 1,
    "action_in_turn": 1,
    "message_index": 4,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_get_flight_cost",
      "arguments": {
        "travel_from": "SFO",
        "travel_to": "LAX",
        "travel_date": "2026-11-10",
        "travel_class": "business"
      }
    }
  },
  {
    "user_turn": 1,
    "action_in_turn": 2,
    "message_index": 6,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_compute_exchange_rate",
      "arguments": {
        "base_currency": "USD",
        "target_currency": "EUR",
        "value": 400.0
      }
    }
  },
  {
    "user_turn": 1,
    "action_in_turn": 3,
    "message_index": 8,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_book_flight",
      "arguments": {
        "access_token": "abc123xyz",
        "card_id": "144756014165",
        "travel_date": "2026-11-10",
        "travel_from": "SFO",
        "travel_to": "LAX",
        "travel_class": "business"
      }
    }
  },
  {
    "user_turn": 3,
    "action_in_turn": 1,
    "message_index": 14,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_cancel_booking",
      "arguments": {
        "access_token": "abc123xyz",
        "booking_id": "3426812"
      }
    }
  },
  {
    "user_turn": 4,
    "action_in_turn": 1,
    "message_index": 18,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_authenticate_twitter",
      "arguments": {
        "username": "john",
        "password": "john1234"
      }
    }
  },
  {
    "user_turn": 4,
    "action_in_turn": 2,
    "message_index": 20,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_post_tweet",
      "arguments": {
        "content": "Just cancelled my trip to LA.",
        "tags": [
          "#TravelUpdate",
          "#BusinessTrip"
        ]
      }
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
    "reference": "{\"content\": \"Just cancelled my trip to LA\", \"tags\": ['#TravelUpdate', '#BusinessTrip']}",
    "actual": {
      "content": "Just cancelled my trip to LA",
      "tags": [
        "#TravelUpdate",
        "#BusinessTrip"
      ]
    }
  }
]
```

### GPTQ

最早动作差异：第 4 个用户轮，第 2 个任务动作；BF16 消息 20，本方法消息 20。

```json
[
  {
    "field": "$.arguments",
    "reference": "{\"content\": \"Just cancelled my trip to LA\", \"tags\": ['#TravelUpdate', '#BusinessTrip']}",
    "actual": {
      "content": "Just cancelled my trip to LA #TravelUpdate #BusinessTrip"
    }
  }
]
```

### EfficientQAT

最早动作差异：第 4 个用户轮，第 2 个任务动作；BF16 消息 20，本方法消息 20。

```json
[
  {
    "field": "$.arguments",
    "reference": "{\"content\": \"Just cancelled my trip to LA\", \"tags\": ['#TravelUpdate', '#BusinessTrip']}",
    "actual": {
      "content": "Just cancelled my trip to LA #TravelUpdate #BusinessTrip"
    }
  }
]
```

### BitDistiller

最早动作差异：第 4 个用户轮，第 2 个任务动作；BF16 消息 20，本方法消息 20。

```json
[
  {
    "field": "$.arguments",
    "reference": "{\"content\": \"Just cancelled my trip to LA\", \"tags\": ['#TravelUpdate', '#BusinessTrip']}",
    "actual": "{\"content\": \"Just cancelled my trip to LA\","
  }
]
```

### On-Policy QAD

最早动作差异：第 1 个用户轮，第 3 个任务动作；BF16 消息 None，本方法消息 8。

```json
[
  {
    "field": "$",
    "reference": null,
    "actual": {
      "wrapper": "call_tool",
      "name": "mcp_tool_book_flight",
      "arguments": {
        "access_token": "abc123xyz",
        "card_id": "144756014165",
        "travel_date": "2026-11-10",
        "travel_from": "SFO",
        "travel_to": "LAX",
        "travel_class": "business"
      }
    }
  }
]
```

### QeRL

最早动作差异：第 1 个用户轮，第 3 个任务动作；BF16 消息 None，本方法消息 8。

```json
[
  {
    "field": "$",
    "reference": null,
    "actual": {
      "wrapper": "call_tool",
      "name": "mcp_tool_book_flight",
      "arguments": {
        "access_token": "abc123xyz",
        "card_id": "144756014165",
        "travel_date": "2026-11-10",
        "travel_from": "SFO",
        "travel_to": "LAX",
        "travel_class": "business"
      }
    }
  }
]
```

## 失败原因

五种 baseline 的推文状态没有达到参考要求，具体内容、提及对象或推文数量差异保留在评分状态对照中。

### GPTQ

评分指出的失败位置/原因：

```text
"Model instance for TwitterAPI does not match the state with ground truth instance."
```

- 状态字段 `tweets.10.content`：实际 "Just cancelled my trip to LA #TravelUpdate #BusinessTrip"；参考 "Just cancelled my trip to LA"。
- 状态字段 `tweets.10.tags[0]`：实际 null；参考 "#TravelUpdate"。
- 状态字段 `tweets.10.tags[1]`：实际 null；参考 "#BusinessTrip"。
### EfficientQAT

评分指出的失败位置/原因：

```text
"Model instance for TwitterAPI does not match the state with ground truth instance."
```

- 状态字段 `tweets.10.content`：实际 "Just cancelled my trip to LA #TravelUpdate #BusinessTrip"；参考 "Just cancelled my trip to LA"。
- 状态字段 `tweets.10.tags[0]`：实际 null；参考 "#TravelUpdate"。
- 状态字段 `tweets.10.tags[1]`：实际 null；参考 "#BusinessTrip"。
### BitDistiller

评分指出的失败位置/原因：

```text
"Model instance for TwitterAPI does not match the state with ground truth instance."
```

- 状态字段 `tweets.10.tags[0]`：实际 null；参考 "#TravelUpdate"。
- 状态字段 `tweets.10.tags[1]`：实际 null；参考 "#BusinessTrip"。
### On-Policy QAD

评分指出的失败位置/原因：

```text
"Model instance for TwitterAPI does not match the state with ground truth instance."
```

- 状态字段 `tweets.10.tags[0]`：实际 "TravelUpdate"；参考 "#TravelUpdate"。
- 状态字段 `tweets.10.tags[1]`：实际 "BusinessTrip"；参考 "#BusinessTrip"。
- 状态字段 `tweets.11`：实际 {"id": 11, "username": "john", "content": "Just cancelled my trip to LA", "tags": ["TravelUpdate", "BusinessTrip"], "mentions": []}；参考 null。
- 状态字段 `tweet_counter`：实际 12；参考 11。
### QeRL

评分指出的失败位置/原因：

```text
"Model instance for TwitterAPI does not match the state with ground truth instance."
```

- 状态字段 `tweets.10.content`：实际 "Just cancelled my trip to LA."；参考 "Just cancelled my trip to LA"。
