# Case 032 — multi_turn_miss_param_152

## 原始任务

第 1 轮：

I'm in the process of scheduling a journey from San Francisco to Chicago on the 15th of the year 2026's eleventh month. It's important the travel is in first class. Before booking, I really can't afford a ticket that is over $5000. If everything is good, then please proceed to book it using my credit card with ID 144756014165 and access token 'secureAccessToken12345'. My personal details should be integrated into the reservation.

第 2 轮：

After reconsideration, I want to cancel one of the flights some time later

第 3 轮：

Oh the flight planned for London on the 15th is no longer necessary. I require the cancellation of this booking immediately.

第 4 轮：

Concerning the flight cancellation, it is crucial to alert customer service without delay. Kindly generate a high-priority ticket named 'Flight Cancellation Alert,' detailing the reservation specifics 'Request to cancel.'. My ticket username is `mthompson` and password is `securePass123

完整工具定义、初始状态及其他任务字段见 task.json。

## 七种方法的实际表现

### BF16：通过

实际任务调用 12 次；[完整 CoT 和工具返回](BF16/cot_and_actions.txt)。

<details><summary>实际动作序列</summary>

```json
[
  {
    "user_turn": 1,
    "action_in_turn": 1,
    "message_index": 4,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_get_nearest_airport_by_city",
      "arguments": {
        "location": "San Francisco"
      }
    }
  },
  {
    "user_turn": 1,
    "action_in_turn": 2,
    "message_index": 6,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_get_nearest_airport_by_city",
      "arguments": {
        "location": "Chicago"
      }
    }
  },
  {
    "user_turn": 1,
    "action_in_turn": 3,
    "message_index": 8,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_get_flight_cost",
      "arguments": {
        "travel_from": "SFO",
        "travel_to": "ORD",
        "travel_date": "2026-11-15",
        "travel_class": "first"
      }
    }
  },
  {
    "user_turn": 1,
    "action_in_turn": 4,
    "message_index": 10,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_verify_traveler_information",
      "arguments": {
        "first_name": "John",
        "last_name": "Doe",
        "date_of_birth": "1980-01-01",
        "passport_number": "ABC123456"
      }
    }
  },
  {
    "user_turn": 1,
    "action_in_turn": 5,
    "message_index": 12,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_book_flight",
      "arguments": {
        "access_token": "secureAccessToken12345",
        "card_id": "144756014165",
        "travel_date": "2026-11-15",
        "travel_from": "SFO",
        "travel_to": "ORD",
        "travel_class": "first"
      }
    }
  },
  {
    "user_turn": 2,
    "action_in_turn": 1,
    "message_index": 16,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_cancel_booking",
      "arguments": {
        "access_token": "secureAccessToken12345",
        "booking_id": "3426812"
      }
    }
  },
  {
    "user_turn": 2,
    "action_in_turn": 2,
    "message_index": 18,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_cancel_booking",
      "arguments": {
        "access_token": "secureAccessToken12345",
        "booking_id": "3426812"
      }
    }
  },
  {
    "user_turn": 3,
    "action_in_turn": 1,
    "message_index": 22,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_cancel_booking",
      "arguments": {
        "access_token": "secureAccessToken12345",
        "booking_id": "3426812"
      }
    }
  },
  {
    "user_turn": 3,
    "action_in_turn": 2,
    "message_index": 24,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_get_booking_history",
      "arguments": {
        "access_token": "secureAccessToken12345"
      }
    }
  },
  {
    "user_turn": 4,
    "action_in_turn": 1,
    "message_index": 28,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_create_ticket",
      "arguments": {
        "title": "Flight Cancellation Alert",
        "description": "Request to cancel.",
        "priority": 5
      }
    }
  },
  {
    "user_turn": 4,
    "action_in_turn": 2,
    "message_index": 30,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_ticket_login",
      "arguments": {
        "username": "mthompson",
        "password": "securePass123"
      }
    }
  },
  {
    "user_turn": 4,
    "action_in_turn": 3,
    "message_index": 32,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_create_ticket",
      "arguments": {
        "title": "Flight Cancellation Alert",
        "description": "Request to cancel.",
        "priority": 5
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
      "name": "mcp_tool_get_nearest_airport_by_city",
      "arguments": {
        "location": "San Francisco"
      }
    }
  },
  {
    "user_turn": 1,
    "action_in_turn": 2,
    "message_index": 6,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_get_nearest_airport_by_city",
      "arguments": {
        "location": "Chicago"
      }
    }
  },
  {
    "user_turn": 1,
    "action_in_turn": 3,
    "message_index": 8,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_get_flight_cost",
      "arguments": {
        "travel_from": "SFO",
        "travel_to": "ORD",
        "travel_date": "2026-11-15",
        "travel_class": "first"
      }
    }
  },
  {
    "user_turn": 1,
    "action_in_turn": 4,
    "message_index": 10,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_book_flight",
      "arguments": {
        "access_token": "secureAccessToken12345",
        "card_id": "144756014165",
        "travel_date": "2026-11-15",
        "travel_from": "SFO",
        "travel_to": "ORD",
        "travel_class": "first"
      }
    }
  },
  {
    "user_turn": 2,
    "action_in_turn": 1,
    "message_index": 14,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_cancel_booking",
      "arguments": {
        "access_token": "secureAccessToken12345",
        "booking_id": "3426812"
      }
    }
  },
  {
    "user_turn": 3,
    "action_in_turn": 1,
    "message_index": 18,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_get_booking_history",
      "arguments": {
        "access_token": "secureAccessToken12345"
      }
    }
  },
  {
    "user_turn": 4,
    "action_in_turn": 1,
    "message_index": 22,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_ticket_login",
      "arguments": {
        "username": "mthompson",
        "password": "securePass123"
      }
    }
  },
  {
    "user_turn": 4,
    "action_in_turn": 2,
    "message_index": 24,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_create_ticket",
      "arguments": {
        "title": "Flight Cancellation Alert",
        "description": "Request to cancel.",
        "priority": 5
      }
    }
  }
]
```

</details>

### GPTQ：未通过

实际任务调用 11 次；[完整 CoT 和工具返回](GPTQ/cot_and_actions.txt)。

<details><summary>实际动作序列</summary>

```json
[
  {
    "user_turn": 1,
    "action_in_turn": 1,
    "message_index": 4,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_get_nearest_airport_by_city",
      "arguments": {
        "location": "San Francisco"
      }
    }
  },
  {
    "user_turn": 1,
    "action_in_turn": 2,
    "message_index": 6,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_get_nearest_airport_by_city",
      "arguments": {
        "location": "Chicago"
      }
    }
  },
  {
    "user_turn": 1,
    "action_in_turn": 3,
    "message_index": 8,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_get_flight_cost",
      "arguments": {
        "travel_from": "SFO",
        "travel_to": "ORD",
        "travel_date": "2026-11-15",
        "travel_class": "first"
      }
    }
  },
  {
    "user_turn": 1,
    "action_in_turn": 4,
    "message_index": 10,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_verify_traveler_information",
      "arguments": {
        "first_name": "User",
        "last_name": "Example",
        "date_of_birth": "1980-01-01",
        "passport_number": "EX123456"
      }
    }
  },
  {
    "user_turn": 1,
    "action_in_turn": 5,
    "message_index": 12,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_verify_traveler_information",
      "arguments": {
        "first_name": "Michael",
        "last_name": "Thompson",
        "date_of_birth": "1980-01-01",
        "passport_number": "TPM123456"
      }
    }
  },
  {
    "user_turn": 1,
    "action_in_turn": 6,
    "message_index": 14,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_verify_traveler_information",
      "arguments": {
        "first_name": "Michael",
        "last_name": "Thompson",
        "date_of_birth": "1980-01-01",
        "passport_number": "US123456789"
      }
    }
  },
  {
    "user_turn": 1,
    "action_in_turn": 7,
    "message_index": 16,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_book_flight",
      "arguments": {
        "access_token": "secureAccessToken12345",
        "card_id": "144756014165",
        "travel_date": "2026-11-15",
        "travel_from": "SFO",
        "travel_to": "ORD",
        "travel_class": "first"
      }
    }
  },
  {
    "user_turn": 2,
    "action_in_turn": 1,
    "message_index": 20,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_cancel_booking",
      "arguments": {
        "access_token": "secureAccessToken12345",
        "booking_id": "3426812"
      }
    }
  },
  {
    "user_turn": 4,
    "action_in_turn": 1,
    "message_index": 26,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_create_ticket",
      "arguments": {
        "title": "Flight Cancellation Alert",
        "description": "Request to cancel.",
        "priority": 5
      }
    }
  },
  {
    "user_turn": 4,
    "action_in_turn": 2,
    "message_index": 28,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_ticket_login",
      "arguments": {
        "username": "mthompson",
        "password": "securePass123"
      }
    }
  },
  {
    "user_turn": 4,
    "action_in_turn": 3,
    "message_index": 30,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_create_ticket",
      "arguments": {
        "title": "Flight Cancellation Alert",
        "description": "Request to cancel.",
        "priority": 5
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
      "name": "mcp_tool_get_nearest_airport_by_city",
      "arguments": {
        "location": "San Francisco"
      }
    }
  },
  {
    "user_turn": 1,
    "action_in_turn": 2,
    "message_index": 6,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_get_nearest_airport_by_city",
      "arguments": {
        "location": "Chicago"
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
        "access_token": "secureAccessToken12345",
        "card_id": "144756014165",
        "travel_date": "2026-12-15",
        "travel_from": "SFO",
        "travel_to": "ORD",
        "travel_class": "first"
      }
    }
  },
  {
    "user_turn": 2,
    "action_in_turn": 1,
    "message_index": 12,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_cancel_booking",
      "arguments": {
        "access_token": "secureAccessToken12345",
        "booking_id": "3426812"
      }
    }
  },
  {
    "user_turn": 3,
    "action_in_turn": 1,
    "message_index": 16,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_get_booking_history",
      "arguments": {
        "access_token": "secureAccessToken12345"
      }
    }
  },
  {
    "user_turn": 4,
    "action_in_turn": 1,
    "message_index": 20,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_ticket_login",
      "arguments": {
        "username": "mthompson",
        "password": "securePass123"
      }
    }
  },
  {
    "user_turn": 4,
    "action_in_turn": 2,
    "message_index": 22,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_create_ticket",
      "arguments": {
        "title": "Flight Cancellation Alert",
        "description": "Request to cancel.",
        "priority": 5
      }
    }
  }
]
```

</details>

### BitDistiller：未通过

实际任务调用 17 次；[完整 CoT 和工具返回](BitDistiller/cot_and_actions.txt)。

<details><summary>实际动作序列</summary>

```json
[
  {
    "user_turn": 1,
    "action_in_turn": 1,
    "message_index": 4,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_get_nearest_airport_by_city",
      "arguments": {
        "location": "San Francisco"
      }
    }
  },
  {
    "user_turn": 1,
    "action_in_turn": 2,
    "message_index": 6,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_get_nearest_airport_by_city",
      "arguments": {
        "location": "Chicago"
      }
    }
  },
  {
    "user_turn": 1,
    "action_in_turn": 3,
    "message_index": 8,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_get_flight_cost",
      "arguments": {
        "travel_from": "SFO",
        "travel_to": "ORD",
        "travel_date": "2026-12-15",
        "travel_class": "first"
      }
    }
  },
  {
    "user_turn": 1,
    "action_in_turn": 4,
    "message_index": 10,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_verify_traveler_information",
      "arguments": {
        "first_name": "John",
        "last_name": "Doe",
        "date_of_birth": "1980-01-01",
        "passport_number": "ABC123456"
      }
    }
  },
  {
    "user_turn": 1,
    "action_in_turn": 5,
    "message_index": 12,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_book_flight",
      "arguments": {
        "access_token": "secureAccessToken12345",
        "card_id": "144756014165",
        "travel_date": "2026-12-15",
        "travel_from": "SFO",
        "travel_to": "ORD",
        "travel_class": "first"
      }
    }
  },
  {
    "user_turn": 2,
    "action_in_turn": 1,
    "message_index": 16,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_cancel_booking",
      "arguments": {
        "access_token": "secureAccessToken12345",
        "booking_id": "3426812"
      }
    }
  },
  {
    "user_turn": 3,
    "action_in_turn": 1,
    "message_index": 20,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_get_booking_history",
      "arguments": {
        "access_token": "secureAccessToken12345"
      }
    }
  },
  {
    "user_turn": 4,
    "action_in_turn": 1,
    "message_index": 24,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_ticket_login",
      "arguments": {
        "username": "mthompson",
        "password": "securePass123"
      }
    }
  },
  {
    "user_turn": 4,
    "action_in_turn": 2,
    "message_index": 26,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_create_ticket",
      "arguments": {
        "title": "Flight Cancellation Alert",
        "description": "Request to cancel.",
        "priority": 5
      }
    }
  },
  {
    "user_turn": 4,
    "action_in_turn": 3,
    "message_index": 28,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_edit_ticket",
      "arguments": {
        "ticket_id": 1,
        "updates": {
          "status": "In Progress"
        }
      }
    }
  },
  {
    "user_turn": 4,
    "action_in_turn": 4,
    "message_index": 30,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_get_ticket",
      "arguments": {
        "ticket_id": 1
      }
    }
  },
  {
    "user_turn": 4,
    "action_in_turn": 5,
    "message_index": 32,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_resolve_ticket",
      "arguments": {
        "ticket_id": 1,
        "resolution": "Customer service alerted regarding flight cancellation request."
      }
    }
  },
  {
    "user_turn": 4,
    "action_in_turn": 6,
    "message_index": 34,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_get_ticket",
      "arguments": {
        "ticket_id": 1
      }
    }
  },
  {
    "user_turn": 4,
    "action_in_turn": 7,
    "message_index": 36,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_close_ticket",
      "arguments": {
        "ticket_id": 1
      }
    }
  },
  {
    "user_turn": 4,
    "action_in_turn": 8,
    "message_index": 38,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_get_ticket",
      "arguments": {
        "ticket_id": 1
      }
    }
  },
  {
    "user_turn": 4,
    "action_in_turn": 9,
    "message_index": 40,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_ticket_get_login_status",
      "arguments": {}
    }
  },
  {
    "user_turn": 4,
    "action_in_turn": 10,
    "message_index": 42,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_logout",
      "arguments": {}
    }
  }
]
```

</details>

### On-Policy QAD：未通过

实际任务调用 6 次；[完整 CoT 和工具返回](On-Policy%20QAD/cot_and_actions.txt)。

<details><summary>实际动作序列</summary>

```json
[
  {
    "user_turn": 1,
    "action_in_turn": 1,
    "message_index": 4,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_get_nearest_airport_by_city",
      "arguments": {
        "location": "San Francisco"
      }
    }
  },
  {
    "user_turn": 1,
    "action_in_turn": 2,
    "message_index": 6,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_get_nearest_airport_by_city",
      "arguments": {
        "location": "Chicago"
      }
    }
  },
  {
    "user_turn": 1,
    "action_in_turn": 3,
    "message_index": 8,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_get_flight_cost",
      "arguments": {
        "travel_from": "SFO",
        "travel_to": "ORD",
        "travel_date": "2026-12-15",
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
      "name": "mcp_tool_create_ticket",
      "arguments": {
        "title": "Flight Cancellation Alert",
        "description": "Request to cancel.",
        "priority": 5
      }
    }
  },
  {
    "user_turn": 4,
    "action_in_turn": 2,
    "message_index": 18,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_ticket_login",
      "arguments": {
        "username": "mthompson",
        "password": "securePass123"
      }
    }
  },
  {
    "user_turn": 4,
    "action_in_turn": 3,
    "message_index": 20,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_create_ticket",
      "arguments": {
        "title": "Flight Cancellation Alert",
        "description": "Request to cancel.",
        "priority": 5
      }
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
      "name": "mcp_tool_get_nearest_airport_by_city",
      "arguments": {
        "location": "San Francisco"
      }
    }
  },
  {
    "user_turn": 1,
    "action_in_turn": 2,
    "message_index": 6,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_get_nearest_airport_by_city",
      "arguments": {
        "location": "Chicago"
      }
    }
  },
  {
    "user_turn": 1,
    "action_in_turn": 3,
    "message_index": 8,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_get_flight_cost",
      "arguments": {
        "travel_from": "SFO",
        "travel_to": "ORD",
        "travel_date": "2026-12-15",
        "travel_class": "first"
      }
    }
  },
  {
    "user_turn": 1,
    "action_in_turn": 4,
    "message_index": 10,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_book_flight",
      "arguments": {
        "access_token": "secureAccessToken12345",
        "card_id": "144756014165",
        "travel_date": "2026-12-15",
        "travel_from": "SFO",
        "travel_to": "ORD",
        "travel_class": "first"
      }
    }
  },
  {
    "user_turn": 2,
    "action_in_turn": 1,
    "message_index": 14,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_cancel_booking",
      "arguments": {
        "access_token": "secureAccessToken12345",
        "booking_id": "3426812"
      }
    }
  },
  {
    "user_turn": 3,
    "action_in_turn": 1,
    "message_index": 18,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_get_booking_history",
      "arguments": {
        "access_token": "secureAccessToken12345"
      }
    }
  },
  {
    "user_turn": 4,
    "action_in_turn": 1,
    "message_index": 22,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_ticket_login",
      "arguments": {
        "username": "mthompson",
        "password": "securePass123"
      }
    }
  },
  {
    "user_turn": 4,
    "action_in_turn": 2,
    "message_index": 24,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_create_ticket",
      "arguments": {
        "title": "Flight Cancellation Alert",
        "description": "Request to cancel.",
        "priority": 5
      }
    }
  }
]
```

</details>

## 分歧位置

消息编号从 0 开始，用户轮和动作编号从 1 开始。按同一用户轮的任务动作序号与 BF16 比较，忽略 list_tools。最早动作差异不一定就是失败起点：正确的工具顺序、补救步骤也可能不同；评分失败位置另见下一节。

### Ours

最早动作差异：第 1 个用户轮，第 4 个任务动作；BF16 消息 10，本方法消息 10。

```json
[
  {
    "field": "$.arguments.access_token",
    "reference": null,
    "actual": "secureAccessToken12345",
    "reference_present": false,
    "actual_present": true
  },
  {
    "field": "$.arguments.card_id",
    "reference": null,
    "actual": "144756014165",
    "reference_present": false,
    "actual_present": true
  },
  {
    "field": "$.arguments.date_of_birth",
    "reference": "1980-01-01",
    "actual": null,
    "reference_present": true,
    "actual_present": false
  },
  {
    "field": "$.arguments.first_name",
    "reference": "John",
    "actual": null,
    "reference_present": true,
    "actual_present": false
  },
  {
    "field": "$.arguments.last_name",
    "reference": "Doe",
    "actual": null,
    "reference_present": true,
    "actual_present": false
  },
  {
    "field": "$.arguments.passport_number",
    "reference": "ABC123456",
    "actual": null,
    "reference_present": true,
    "actual_present": false
  },
  {
    "field": "$.arguments.travel_class",
    "reference": null,
    "actual": "first",
    "reference_present": false,
    "actual_present": true
  },
  {
    "field": "$.arguments.travel_date",
    "reference": null,
    "actual": "2026-11-15",
    "reference_present": false,
    "actual_present": true
  },
  {
    "field": "$.arguments.travel_from",
    "reference": null,
    "actual": "SFO",
    "reference_present": false,
    "actual_present": true
  },
  {
    "field": "$.arguments.travel_to",
    "reference": null,
    "actual": "ORD",
    "reference_present": false,
    "actual_present": true
  },
  {
    "field": "$.name",
    "reference": "mcp_tool_verify_traveler_information",
    "actual": "mcp_tool_book_flight"
  }
]
```

### GPTQ

最早动作差异：第 1 个用户轮，第 4 个任务动作；BF16 消息 10，本方法消息 10。

```json
[
  {
    "field": "$.arguments.first_name",
    "reference": "John",
    "actual": "User"
  },
  {
    "field": "$.arguments.last_name",
    "reference": "Doe",
    "actual": "Example"
  },
  {
    "field": "$.arguments.passport_number",
    "reference": "ABC123456",
    "actual": "EX123456"
  }
]
```

### EfficientQAT

最早动作差异：第 1 个用户轮，第 3 个任务动作；BF16 消息 8，本方法消息 8。

```json
[
  {
    "field": "$.arguments.access_token",
    "reference": null,
    "actual": "secureAccessToken12345",
    "reference_present": false,
    "actual_present": true
  },
  {
    "field": "$.arguments.card_id",
    "reference": null,
    "actual": "144756014165",
    "reference_present": false,
    "actual_present": true
  },
  {
    "field": "$.arguments.travel_date",
    "reference": "2026-11-15",
    "actual": "2026-12-15"
  },
  {
    "field": "$.name",
    "reference": "mcp_tool_get_flight_cost",
    "actual": "mcp_tool_book_flight"
  }
]
```

### BitDistiller

最早动作差异：第 1 个用户轮，第 3 个任务动作；BF16 消息 8，本方法消息 8。

```json
[
  {
    "field": "$.arguments.travel_date",
    "reference": "2026-11-15",
    "actual": "2026-12-15"
  }
]
```

### On-Policy QAD

最早动作差异：第 1 个用户轮，第 3 个任务动作；BF16 消息 8，本方法消息 8。

```json
[
  {
    "field": "$.arguments.travel_date",
    "reference": "2026-11-15",
    "actual": "2026-12-15"
  }
]
```

### QeRL

最早动作差异：第 1 个用户轮，第 3 个任务动作；BF16 消息 8，本方法消息 8。

```json
[
  {
    "field": "$.arguments.travel_date",
    "reference": "2026-11-15",
    "actual": "2026-12-15"
  }
]
```

## 失败原因

GPTQ 在后续用户轮没有任务调用；其他方法的订票记录或信用卡扣款状态不同于参考结果。

### GPTQ

评分指出的失败位置/原因：

```text
"Model response list is empty for turn 2"
```

### EfficientQAT

评分指出的失败位置/原因：

```text
"Model instance for TravelAPI does not match the state with ground truth instance."
```

- 状态字段 `credit_card_list.144756014165.balance`：实际 8000.0；参考 6000.0。
- 状态字段 `booking_record.3426812.travel_cost`：实际 2000.0；参考 4000.0。
- 状态字段 `booking_record.3426812.travel_date`：实际 "2026-12-15"；参考 "2026-11-15"。
### BitDistiller

评分指出的失败位置/原因：

```text
"Model instance for TravelAPI does not match the state with ground truth instance."
```

- 状态字段 `credit_card_list.144756014165.balance`：实际 8000.0；参考 6000.0。
- 状态字段 `booking_record.3426812.travel_cost`：实际 2000.0；参考 4000.0。
- 状态字段 `booking_record.3426812.travel_date`：实际 "2026-12-15"；参考 "2026-11-15"。
### On-Policy QAD

评分指出的失败位置/原因：

```text
"Model instance for TravelAPI does not match the state with ground truth instance."
```

- 状态字段 `credit_card_list.144756014165.balance`：实际 10000.0；参考 6000.0。
- 状态字段 `booking_record.3426812`：实际 null；参考 {"card_id": "144756014165", "travel_date": "2026-11-15", "travel_from": "SFO", "travel_to": "ORD", "travel_class": "first", "travel_cost": 4000.0, "transaction_id": "45451592"}。
### QeRL

评分指出的失败位置/原因：

```text
"Model instance for TravelAPI does not match the state with ground truth instance."
```

- 状态字段 `credit_card_list.144756014165.balance`：实际 8000.0；参考 6000.0。
- 状态字段 `booking_record.3426812.travel_cost`：实际 2000.0；参考 4000.0。
- 状态字段 `booking_record.3426812.travel_date`：实际 "2026-12-15"；参考 "2026-11-15"。
