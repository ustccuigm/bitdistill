# Case 027 — multi_turn_miss_func_181

## 原始任务

第 1 轮：

I've recently retired after spending years poring over electrical blueprints and energy systems across Spain. I'm planning an invigorating journey and wish to ensure all my travel details are meticulously verified. Please confirm my information using the passport number '123456' I've shared with you. The name and DoB are Carlos Martinez and March 23, 1968

第 2 轮：

In verifying this, kindly identify the most convenient airport for me if I'm residing in bustling New York City. Additionally, provide an estimate for a first-class journey to the sun-drenched coast of Los Angeles next week Oct 10 2026.

第 3 轮：

With this estimate in hand, arrange the flight using my credentials with id 'card_3456' and access token 'abc123xyz', ensuring a seamless payment process and detailing my travel itinerary.

第 4 轮：

第 5 轮：

However, an unexpected situation has prompted me to reconsider. Kindly cancel the flight immediately, sparing no time.

第 6 轮：

As I've encountered some unexpected issues, I need to submit a formal complaint about the abrupt cancellation. Title it 'Flight Cancellation Experience' and include in the message: 'The abrupt cancellation caused significant inconvenience, disrupting my travel plans and causing financial loss.'. My username is cmartinez, and password is SecurePass123

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
      "name": "mcp_tool_verify_traveler_information",
      "arguments": {
        "first_name": "Carlos",
        "last_name": "Martinez",
        "date_of_birth": "1968-03-23",
        "passport_number": "123456"
      }
    }
  },
  {
    "user_turn": 2,
    "action_in_turn": 1,
    "message_index": 8,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_get_nearest_airport_by_city",
      "arguments": {
        "location": "New York"
      }
    }
  },
  {
    "user_turn": 2,
    "action_in_turn": 2,
    "message_index": 10,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_get_flight_cost",
      "arguments": {
        "travel_from": "JFK",
        "travel_to": "LAX",
        "travel_date": "2026-10-10",
        "travel_class": "first"
      }
    }
  },
  {
    "user_turn": 3,
    "action_in_turn": 1,
    "message_index": 14,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_purchase_insurance",
      "arguments": {
        "access_token": "abc123xyz",
        "insurance_type": "trip_cancellation",
        "insurance_cost": 200.0,
        "booking_id": "BK123456",
        "card_id": "card_3456"
      }
    }
  },
  {
    "user_turn": 4,
    "action_in_turn": 1,
    "message_index": 18,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_book_flight",
      "arguments": {
        "access_token": "abc123xyz",
        "card_id": "card_3456",
        "travel_date": "2026-10-10",
        "travel_from": "JFK",
        "travel_to": "LAX",
        "travel_class": "first"
      }
    }
  },
  {
    "user_turn": 5,
    "action_in_turn": 1,
    "message_index": 22,
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
    "user_turn": 6,
    "action_in_turn": 1,
    "message_index": 26,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_ticket_login",
      "arguments": {
        "username": "cmartinez",
        "password": "SecurePass123"
      }
    }
  },
  {
    "user_turn": 6,
    "action_in_turn": 2,
    "message_index": 28,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_create_ticket",
      "arguments": {
        "title": "Flight Cancellation Experience",
        "description": "The abrupt cancellation caused significant inconvenience, disrupting my travel plans and causing financial loss.",
        "priority": 1
      }
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
      "name": "mcp_tool_verify_traveler_information",
      "arguments": {
        "first_name": "Carlos",
        "last_name": "Martinez",
        "date_of_birth": "1968-03-23",
        "passport_number": "123456"
      }
    }
  },
  {
    "user_turn": 2,
    "action_in_turn": 1,
    "message_index": 8,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_get_nearest_airport_by_city",
      "arguments": {
        "location": "New York"
      }
    }
  },
  {
    "user_turn": 2,
    "action_in_turn": 2,
    "message_index": 10,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_get_flight_cost",
      "arguments": {
        "travel_from": "JFK",
        "travel_to": "LAX",
        "travel_date": "2026-10-10",
        "travel_class": "first"
      }
    }
  },
  {
    "user_turn": 3,
    "action_in_turn": 1,
    "message_index": 14,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_purchase_insurance",
      "arguments": {
        "access_token": "abc123xyz",
        "insurance_type": "trip_cancellation",
        "insurance_cost": 150.0,
        "booking_id": "auto-generated-id",
        "card_id": "card_3456"
      }
    }
  },
  {
    "user_turn": 4,
    "action_in_turn": 1,
    "message_index": 18,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_book_flight",
      "arguments": {
        "access_token": "abc123xyz",
        "card_id": "card_3456",
        "travel_date": "2026-10-10",
        "travel_from": "JFK",
        "travel_to": "LAX",
        "travel_class": "first"
      }
    }
  },
  {
    "user_turn": 5,
    "action_in_turn": 1,
    "message_index": 22,
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
    "user_turn": 6,
    "action_in_turn": 1,
    "message_index": 26,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_ticket_login",
      "arguments": {
        "username": "cmartinez",
        "password": "SecurePass123"
      }
    }
  },
  {
    "user_turn": 6,
    "action_in_turn": 2,
    "message_index": 28,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_create_ticket",
      "arguments": {
        "title": "Flight Cancellation Experience",
        "description": "The abrupt cancellation caused significant inconvenience, disrupting my travel plans and causing financial loss.",
        "priority": 1
      }
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
      "name": "mcp_tool_verify_traveler_information",
      "arguments": {
        "first_name": "Carlos",
        "last_name": "Martinez",
        "date_of_birth": "1968-03-23",
        "passport_number": "123456"
      }
    }
  },
  {
    "user_turn": 2,
    "action_in_turn": 1,
    "message_index": 8,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_get_nearest_airport_by_city",
      "arguments": {
        "location": "New York"
      }
    }
  },
  {
    "user_turn": 2,
    "action_in_turn": 2,
    "message_index": 10,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_get_flight_cost",
      "arguments": {
        "travel_from": "JFK",
        "travel_to": "LAX",
        "travel_date": "2026-10-10",
        "travel_class": "first"
      }
    }
  },
  {
    "user_turn": 3,
    "action_in_turn": 1,
    "message_index": 14,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_purchase_insurance",
      "arguments": {
        "access_token": "abc123xyz",
        "insurance_type": "trip_cancellation",
        "insurance_cost": 150.0,
        "booking_id": "auto-generated-id",
        "card_id": "card_3456"
      }
    }
  },
  {
    "user_turn": 4,
    "action_in_turn": 1,
    "message_index": 18,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_book_flight",
      "arguments": {
        "access_token": "abc123xyz",
        "card_id": "card_3456",
        "travel_date": "2026-10-10",
        "travel_from": "JFK",
        "travel_to": "LAX",
        "travel_class": "first"
      }
    }
  },
  {
    "user_turn": 5,
    "action_in_turn": 1,
    "message_index": 22,
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
    "user_turn": 6,
    "action_in_turn": 1,
    "message_index": 26,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_ticket_login",
      "arguments": {
        "username": "cmartinez",
        "password": "SecurePass123"
      }
    }
  },
  {
    "user_turn": 6,
    "action_in_turn": 2,
    "message_index": 28,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_create_ticket",
      "arguments": {
        "title": "Flight Cancellation Experience",
        "description": "The abrupt cancellation caused significant inconvenience, disrupting my travel plans and causing financial loss.",
        "priority": 2
      }
    }
  }
]
```

</details>

### EfficientQAT：未通过

实际任务调用 9 次；[完整 CoT 和工具返回](EfficientQAT/cot_and_actions.txt)。

<details><summary>实际动作序列</summary>

```json
[
  {
    "user_turn": 1,
    "action_in_turn": 1,
    "message_index": 4,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_verify_traveler_information",
      "arguments": {
        "first_name": "Carlos",
        "last_name": "Martinez",
        "date_of_birth": "1968-03-23",
        "passport_number": "123456"
      }
    }
  },
  {
    "user_turn": 2,
    "action_in_turn": 1,
    "message_index": 8,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_get_nearest_airport_by_city",
      "arguments": {
        "location": "New York"
      }
    }
  },
  {
    "user_turn": 2,
    "action_in_turn": 2,
    "message_index": 10,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_get_flight_cost",
      "arguments": {
        "travel_from": "JFK",
        "travel_to": "LAX",
        "travel_date": "2026-10-10",
        "travel_class": "first"
      }
    }
  },
  {
    "user_turn": 3,
    "action_in_turn": 1,
    "message_index": 14,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_purchase_insurance",
      "arguments": {
        "access_token": "abc123xyz",
        "insurance_type": "flight_delay",
        "insurance_cost": 150.0,
        "booking_id": "auto-generated-id-123",
        "card_id": "card_3456"
      }
    }
  },
  {
    "user_turn": 4,
    "action_in_turn": 1,
    "message_index": 18,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_book_flight",
      "arguments": {
        "access_token": "abc123xyz",
        "card_id": "card_3456",
        "travel_date": "2026-10-10",
        "travel_from": "JFK",
        "travel_to": "LAX",
        "travel_class": "first"
      }
    }
  },
  {
    "user_turn": 5,
    "action_in_turn": 1,
    "message_index": 22,
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
    "user_turn": 6,
    "action_in_turn": 1,
    "message_index": 26,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_create_ticket",
      "arguments": {
        "title": "Flight Cancellation Experience",
        "description": "The abrupt cancellation caused significant inconvenience, disrupting my travel plans and causing financial loss.",
        "priority": 5
      }
    }
  },
  {
    "user_turn": 6,
    "action_in_turn": 2,
    "message_index": 28,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_ticket_login",
      "arguments": {
        "username": "cmartinez",
        "password": "SecurePass123"
      }
    }
  },
  {
    "user_turn": 6,
    "action_in_turn": 3,
    "message_index": 30,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_create_ticket",
      "arguments": {
        "title": "Flight Cancellation Experience",
        "description": "The abrupt cancellation caused significant inconvenience, disrupting my travel plans and causing financial loss.",
        "priority": 5
      }
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
      "name": "mcp_tool_verify_traveler_information",
      "arguments": {
        "first_name": "Carlos",
        "last_name": "Martinez",
        "date_of_birth": "1968-03-23",
        "passport_number": "123456"
      }
    }
  },
  {
    "user_turn": 2,
    "action_in_turn": 1,
    "message_index": 8,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_get_nearest_airport_by_city",
      "arguments": {
        "location": "New York"
      }
    }
  },
  {
    "user_turn": 2,
    "action_in_turn": 2,
    "message_index": 10,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_get_flight_cost",
      "arguments": {
        "travel_from": "JFK",
        "travel_to": "LAX",
        "travel_date": "2026-10-10",
        "travel_class": "first"
      }
    }
  },
  {
    "user_turn": 4,
    "action_in_turn": 1,
    "message_index": 16,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_book_flight",
      "arguments": {
        "access_token": "abc123xyz",
        "card_id": "card_3456",
        "travel_date": "2026-10-10",
        "travel_from": "JFK",
        "travel_to": "LAX",
        "travel_class": "first"
      }
    }
  },
  {
    "user_turn": 5,
    "action_in_turn": 1,
    "message_index": 20,
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
    "user_turn": 6,
    "action_in_turn": 1,
    "message_index": 24,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_create_ticket",
      "arguments": {
        "title": "Flight Cancellation Experience",
        "description": "The abrupt cancellation caused significant inconvenience, disrupting my travel plans and causing financial loss.",
        "priority": 5
      }
    }
  },
  {
    "user_turn": 6,
    "action_in_turn": 2,
    "message_index": 26,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_ticket_login",
      "arguments": {
        "username": "cmartinez",
        "password": "SecurePass123"
      }
    }
  },
  {
    "user_turn": 6,
    "action_in_turn": 3,
    "message_index": 28,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_create_ticket",
      "arguments": {
        "title": "Flight Cancellation Experience",
        "description": "The abrupt cancellation caused significant inconvenience, disrupting my travel plans and causing financial loss.",
        "priority": 5
      }
    }
  }
]
```

</details>

### On-Policy QAD：未通过

实际任务调用 8 次；[完整 CoT 和工具返回](On-Policy%20QAD/cot_and_actions.txt)。

<details><summary>实际动作序列</summary>

```json
[
  {
    "user_turn": 1,
    "action_in_turn": 1,
    "message_index": 4,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_verify_traveler_information",
      "arguments": {
        "first_name": "Carlos",
        "last_name": "Martinez",
        "date_of_birth": "1968-03-23",
        "passport_number": "123456"
      }
    }
  },
  {
    "user_turn": 2,
    "action_in_turn": 1,
    "message_index": 8,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_get_nearest_airport_by_city",
      "arguments": {
        "location": "New York"
      }
    }
  },
  {
    "user_turn": 2,
    "action_in_turn": 2,
    "message_index": 10,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_get_flight_cost",
      "arguments": {
        "travel_from": "JFK",
        "travel_to": "LAX",
        "travel_date": "2026-10-10",
        "travel_class": "first"
      }
    }
  },
  {
    "user_turn": 4,
    "action_in_turn": 1,
    "message_index": 16,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_book_flight",
      "arguments": {
        "access_token": "abc123xyz",
        "card_id": "card_3456",
        "travel_date": "2026-10-10",
        "travel_from": "JFK",
        "travel_to": "LAX",
        "travel_class": "first"
      }
    }
  },
  {
    "user_turn": 5,
    "action_in_turn": 1,
    "message_index": 20,
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
    "user_turn": 6,
    "action_in_turn": 1,
    "message_index": 24,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_create_ticket",
      "arguments": {
        "title": "Flight Cancellation Experience",
        "description": "The abrupt cancellation caused significant inconvenience, disrupting my travel plans and causing financial loss.",
        "priority": 5
      }
    }
  },
  {
    "user_turn": 6,
    "action_in_turn": 2,
    "message_index": 26,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_ticket_login",
      "arguments": {
        "username": "cmartinez",
        "password": "SecurePass123"
      }
    }
  },
  {
    "user_turn": 6,
    "action_in_turn": 3,
    "message_index": 28,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_create_ticket",
      "arguments": {
        "title": "Flight Cancellation Experience",
        "description": "The abrupt cancellation caused significant inconvenience, disrupting my travel plans and causing financial loss.",
        "priority": 5
      }
    }
  }
]
```

</details>

### QeRL：未通过

实际任务调用 9 次；[完整 CoT 和工具返回](QeRL/cot_and_actions.txt)。

<details><summary>实际动作序列</summary>

```json
[
  {
    "user_turn": 1,
    "action_in_turn": 1,
    "message_index": 4,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_verify_traveler_information",
      "arguments": {
        "first_name": "Carlos",
        "last_name": "Martinez",
        "date_of_birth": "1968-03-23",
        "passport_number": "123456"
      }
    }
  },
  {
    "user_turn": 2,
    "action_in_turn": 1,
    "message_index": 8,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_get_nearest_airport_by_city",
      "arguments": {
        "location": "New York"
      }
    }
  },
  {
    "user_turn": 2,
    "action_in_turn": 2,
    "message_index": 10,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_get_flight_cost",
      "arguments": {
        "travel_from": "JFK",
        "travel_to": "LAX",
        "travel_date": "2026-10-10",
        "travel_class": "first"
      }
    }
  },
  {
    "user_turn": 3,
    "action_in_turn": 1,
    "message_index": 14,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_purchase_insurance",
      "arguments": {
        "access_token": "abc123xyz",
        "insurance_type": "trip_cancellation",
        "insurance_cost": 200.0,
        "booking_id": "FLIGHT_123456",
        "card_id": "card_3456"
      }
    }
  },
  {
    "user_turn": 4,
    "action_in_turn": 1,
    "message_index": 18,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_book_flight",
      "arguments": {
        "access_token": "abc123xyz",
        "card_id": "card_3456",
        "travel_date": "2026-10-10",
        "travel_from": "JFK",
        "travel_to": "LAX",
        "travel_class": "first"
      }
    }
  },
  {
    "user_turn": 4,
    "action_in_turn": 2,
    "message_index": 20,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_purchase_insurance",
      "arguments": {
        "access_token": "abc123xyz",
        "insurance_type": "trip_cancellation",
        "insurance_cost": 200.0,
        "booking_id": "3426812",
        "card_id": "card_3456"
      }
    }
  },
  {
    "user_turn": 5,
    "action_in_turn": 1,
    "message_index": 24,
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
    "user_turn": 6,
    "action_in_turn": 1,
    "message_index": 28,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_ticket_login",
      "arguments": {
        "username": "cmartinez",
        "password": "SecurePass123"
      }
    }
  },
  {
    "user_turn": 6,
    "action_in_turn": 2,
    "message_index": 30,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_create_ticket",
      "arguments": {
        "title": "Flight Cancellation Experience",
        "description": "The abrupt cancellation caused significant inconvenience, disrupting my travel plans and causing financial loss.",
        "priority": 1
      }
    }
  }
]
```

</details>

## 分歧位置

消息编号从 0 开始，用户轮和动作编号从 1 开始。按同一用户轮的任务动作序号与 BF16 比较，忽略 list_tools。最早动作差异不一定就是失败起点：正确的工具顺序、补救步骤也可能不同；评分失败位置另见下一节。

### Ours

最早动作差异：第 3 个用户轮，第 1 个任务动作；BF16 消息 14，本方法消息 14。

```json
[
  {
    "field": "$.arguments.booking_id",
    "reference": "BK123456",
    "actual": "auto-generated-id"
  },
  {
    "field": "$.arguments.insurance_cost",
    "reference": 200.0,
    "actual": 150.0
  }
]
```

### GPTQ

最早动作差异：第 3 个用户轮，第 1 个任务动作；BF16 消息 14，本方法消息 14。

```json
[
  {
    "field": "$.arguments.booking_id",
    "reference": "BK123456",
    "actual": "auto-generated-id"
  },
  {
    "field": "$.arguments.insurance_cost",
    "reference": 200.0,
    "actual": 150.0
  }
]
```

### EfficientQAT

最早动作差异：第 3 个用户轮，第 1 个任务动作；BF16 消息 14，本方法消息 14。

```json
[
  {
    "field": "$.arguments.booking_id",
    "reference": "BK123456",
    "actual": "auto-generated-id-123"
  },
  {
    "field": "$.arguments.insurance_cost",
    "reference": 200.0,
    "actual": 150.0
  },
  {
    "field": "$.arguments.insurance_type",
    "reference": "trip_cancellation",
    "actual": "flight_delay"
  }
]
```

### BitDistiller

最早动作差异：第 3 个用户轮，第 1 个任务动作；BF16 消息 14，本方法消息 None。

该位置没有对应任务调用；该轮 assistant 消息为 [14]。

```json
[
  {
    "field": "$",
    "reference": {
      "wrapper": "call_tool",
      "name": "mcp_tool_purchase_insurance",
      "arguments": {
        "access_token": "abc123xyz",
        "insurance_type": "trip_cancellation",
        "insurance_cost": 200.0,
        "booking_id": "BK123456",
        "card_id": "card_3456"
      }
    },
    "actual": null
  }
]
```

### On-Policy QAD

最早动作差异：第 3 个用户轮，第 1 个任务动作；BF16 消息 14，本方法消息 None。

该位置没有对应任务调用；该轮 assistant 消息为 [14]。

```json
[
  {
    "field": "$",
    "reference": {
      "wrapper": "call_tool",
      "name": "mcp_tool_purchase_insurance",
      "arguments": {
        "access_token": "abc123xyz",
        "insurance_type": "trip_cancellation",
        "insurance_cost": 200.0,
        "booking_id": "BK123456",
        "card_id": "card_3456"
      }
    },
    "actual": null
  }
]
```

### QeRL

最早动作差异：第 3 个用户轮，第 1 个任务动作；BF16 消息 14，本方法消息 14。

```json
[
  {
    "field": "$.arguments.booking_id",
    "reference": "BK123456",
    "actual": "FLIGHT_123456"
  }
]
```

## 失败原因

四种 baseline 的 ticket_queue 未达到参考状态；QeRL 的首个评分失败涉及信用卡状态。各方法的失败阶段不同。

### GPTQ

评分指出的失败位置/原因：

```text
"Model instance for TicketAPI does not match the state with ground truth instance."
```

- 状态字段 `ticket_queue[1].priority`：实际 2；参考 1。
### EfficientQAT

评分指出的失败位置/原因：

```text
"Model instance for TicketAPI does not match the state with ground truth instance."
```

- 状态字段 `ticket_queue[1].priority`：实际 5；参考 1。
### BitDistiller

评分指出的失败位置/原因：

```text
"Model instance for TicketAPI does not match the state with ground truth instance."
```

- 状态字段 `ticket_queue[1].priority`：实际 5；参考 1。
### On-Policy QAD

评分指出的失败位置/原因：

```text
"Model instance for TicketAPI does not match the state with ground truth instance."
```

- 状态字段 `ticket_queue[1].priority`：实际 5；参考 1。
### QeRL

评分指出的失败位置/原因：

```text
"Model instance for TravelAPI does not match the state with ground truth instance."
```

- 状态字段 `credit_card_list.card_3456.balance`：实际 9100.0；参考 9300.0。
