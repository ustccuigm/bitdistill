# Case 021 — multi_turn_base_189

## 原始任务

第 1 轮：

Planning an incredible journey from NYC to Tokyo on December 24th 2026 in first class! I have my credit card ready with the id card_5678, which is expiring soon, and I'd like to allocate business expenses wisely. The cardholder's name matches mine, Michael Thompson, and I can provide the CVV when needed, which is 456. Just double check how much the flight costs for me and then could you make the booking using access token 'abc123xyz'?

第 2 轮：

After sorting out my travel plans, draft a tweet about how flexible and adaptable my itinerary turned out to be, including a tag to my favorite travel blog '#TravelBlog' and mention my adventure-loving friend '@Spontaneity'. You may use my account with username 'john' and password 'john1234'. The tweet should read 'Flexibility is key! Plans changed, but the adventure continues.'

第 3 轮：

Can you amplify the message by retweeting my recent post about the itinerary that you just posted, highlighting our spontaneity with travel plans to reach a larger audience?

完整工具定义、初始状态及其他任务字段见 task.json。

## 七种方法的实际表现

### BF16：通过

实际任务调用 7 次；[完整 CoT 和工具返回](BF16/cot_and_actions.txt)。

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
        "location": "New York"
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
        "location": "Tokyo"
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
        "travel_from": "JFK",
        "travel_to": "HND",
        "travel_date": "2026-12-24",
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
        "access_token": "abc123xyz",
        "card_id": "card_5678",
        "travel_date": "2026-12-24",
        "travel_from": "JFK",
        "travel_to": "HND",
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
      "name": "mcp_tool_authenticate_twitter",
      "arguments": {
        "username": "john",
        "password": "john1234"
      }
    }
  },
  {
    "user_turn": 2,
    "action_in_turn": 2,
    "message_index": 16,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_post_tweet",
      "arguments": {
        "content": "Flexibility is key! Plans changed, but the adventure continues.",
        "tags": [
          "#TravelBlog"
        ],
        "mentions": [
          "@Spontaneity"
        ]
      }
    }
  },
  {
    "user_turn": 3,
    "action_in_turn": 1,
    "message_index": 20,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_retweet",
      "arguments": {
        "tweet_id": 10
      }
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
    "user_turn": 1,
    "action_in_turn": 1,
    "message_index": 4,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_get_nearest_airport_by_city",
      "arguments": {
        "location": "New York"
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
        "location": "Tokyo"
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
        "travel_from": "JFK",
        "travel_to": "HND",
        "travel_date": "2026-12-24",
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
        "access_token": "abc123xyz",
        "card_id": "card_5678",
        "travel_date": "2026-12-24",
        "travel_from": "JFK",
        "travel_to": "HND",
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
      "name": "mcp_tool_authenticate_twitter",
      "arguments": {
        "username": "john",
        "password": "john1234"
      }
    }
  },
  {
    "user_turn": 2,
    "action_in_turn": 2,
    "message_index": 16,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_post_tweet",
      "arguments": {
        "content": "Flexibility is key! Plans changed, but the adventure continues.",
        "mentions": [
          "@Spontaneity"
        ],
        "tags": [
          "#TravelBlog"
        ]
      }
    }
  },
  {
    "user_turn": 3,
    "action_in_turn": 1,
    "message_index": 20,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_retweet",
      "arguments": {
        "tweet_id": 10
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
      "name": "mcp_tool_get_nearest_airport_by_city",
      "arguments": {
        "location": "New York"
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
        "location": "Tokyo"
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
        "travel_from": "JFK",
        "travel_to": "HND",
        "travel_date": "2026-12-24",
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
      "name": "mcp_tool_authenticate_twitter",
      "arguments": {
        "username": "john",
        "password": "john1234"
      }
    }
  },
  {
    "user_turn": 2,
    "action_in_turn": 2,
    "message_index": 14,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_post_tweet",
      "arguments": "{\"content\": \"Flexibility is key! Plans changed, but the adventure continues.\", \"tags\": ['#TravelBlog'], \"mentions\": ['@Spontaneity']}"
    }
  },
  {
    "user_turn": 3,
    "action_in_turn": 1,
    "message_index": 18,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_retweet",
      "arguments": {
        "tweet_id": 10
      }
    }
  }
]
```

</details>

### EfficientQAT：未通过

实际任务调用 12 次；[完整 CoT 和工具返回](EfficientQAT/cot_and_actions.txt)。

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
        "location": "New York"
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
        "location": "Tokyo"
      }
    }
  },
  {
    "user_turn": 1,
    "action_in_turn": 3,
    "message_index": 8,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_call_checkout_flow_for_payment_and_reservation",
      "arguments": {
        "access_token": "abc123xyz",
        "card_id": "card_5678",
        "travel_from": "JFK",
        "travel_to": "HND",
        "travel_date": "2026-12-24",
        "travel_class": "first",
        "passenger_info": {
          "first_name": "Michael",
          "last_name": "Thompson",
          "date_of_birth": "1985-05-15",
          "passport_number": "USPAS12345678"
        },
        "payment_method": {
          "cvv": "456"
        }
      }
    }
  },
  {
    "user_turn": 1,
    "action_in_turn": 4,
    "message_index": 10,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_register_credit_card",
      "arguments": {
        "access_token": "abc123xyz",
        "card_number": "XXXX5678",
        "expiration_month": "12",
        "expiration_year": "26",
        "cardholder_name": "Michael Thompson",
        "card_verification_number": "456"
      }
    }
  },
  {
    "user_turn": 1,
    "action_in_turn": 5,
    "message_index": 12,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_register_credit_card",
      "arguments": {
        "access_number": "abc123xyz",
        "card_number": "XXXX5678",
        "expiration_date": "12/26",
        "cardholder_name": "Michael Thompson",
        "card_verification_number": "456"
      }
    }
  },
  {
    "user_turn": 1,
    "action_in_turn": 6,
    "message_index": 14,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_register_credit_card",
      "arguments": {
        "card_number": "XXXX5678",
        "expiration_date": "12/26",
        "cardholder_name": "Michael Thompson",
        "card_verification_number": "456"
      }
    }
  },
  {
    "user_turn": 1,
    "action_in_turn": 7,
    "message_index": 16,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_register_credit_card",
      "arguments": {
        "access_token": "abc123xyz",
        "card_number": "XXXX5678",
        "expiration_date": "12/26",
        "cardholder_name": "Michael Thompson",
        "card_verification_number": "456"
      }
    }
  },
  {
    "user_turn": 1,
    "action_in_turn": 8,
    "message_index": 18,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_book_flight",
      "arguments": {
        "access_token": "abc123xyz",
        "card_id": "262919693687",
        "travel_date": "2026-12-24",
        "travel_from": "JFK",
        "travel_to": "HND",
        "travel_class": "first"
      }
    }
  },
  {
    "user_turn": 2,
    "action_in_turn": 1,
    "message_index": 22,
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
    "user_turn": 2,
    "action_in_turn": 2,
    "message_index": 24,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_post_tweet",
      "arguments": {
        "content": "Flexibility is key! Plans changed, but the adventure continues.",
        "tags": [
          "#TravelBlog"
        ],
        "mentions": [
          "@Spontaneity"
        ]
      }
    }
  },
  {
    "user_turn": 3,
    "action_in_turn": 1,
    "message_index": 28,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_quote_retweet",
      "arguments": {
        "tweet_id": 10,
        "quoted_text": "Flexibility is key! Plans changed, but the adventure continues.",
        "comment": "Embracing spontaneous adventures makes every trip unforgettable! 😊"
      }
    }
  },
  {
    "user_turn": 3,
    "action_in_turn": 2,
    "message_index": 30,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_book_flight",
      "arguments": {
        "access_token": "abc123xyz",
        "card_id": "262919693687",
        "travel_date": "2026-12-24",
        "travel_from": "JFK",
        "travel_to": "HND",
        "travel_class": "first"
      }
    }
  }
]
```

</details>

### BitDistiller：未通过

实际任务调用 4 次；[完整 CoT 和工具返回](BitDistiller/cot_and_actions.txt)。

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
        "travel_from": "JFK",
        "travel_to": "NRT",
        "travel_date": "2026-12-24",
        "travel_class": "first"
      }
    }
  },
  {
    "user_turn": 2,
    "action_in_turn": 1,
    "message_index": 8,
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
    "user_turn": 2,
    "action_in_turn": 2,
    "message_index": 10,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_post_tweet",
      "arguments": {
        "content": "Flexibility is key! Plans changed, but the adventure continues.",
        "tags": [
          "#TravelBlog"
        ],
        "mentions": [
          "@Spontaneity"
        ]
      }
    }
  },
  {
    "user_turn": 3,
    "action_in_turn": 1,
    "message_index": 14,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_retweet",
      "arguments": {
        "tweet_id": 10
      }
    }
  }
]
```

</details>

### On-Policy QAD：未通过

实际任务调用 17 次；[完整 CoT 和工具返回](On-Policy%20QAD/cot_and_actions.txt)。

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
        "location": "New York"
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
        "location": "Tokyo"
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
        "travel_from": "JFK",
        "travel_to": "HND",
        "travel_date": "2026-12-24",
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
        "access_token": "abc123xyz",
        "card_id": "card_5678",
        "travel_date": "2026-12-24",
        "travel_from": "JFK",
        "travel_to": "HND",
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
      "name": "mcp_tool_authenticate_twitter",
      "arguments": {
        "username": "john",
        "password": "john1234"
      }
    }
  },
  {
    "user_turn": 2,
    "action_in_turn": 2,
    "message_index": 16,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_post_tweet",
      "arguments": {
        "content": "Flexibility is key! Plans changed, but the adventure continues.",
        "tags": [
          "#TravelBlog"
        ],
        "mentions": [
          "@Spontaneity"
        ]
      }
    }
  },
  {
    "user_turn": 2,
    "action_in_turn": 3,
    "message_index": 18,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_post_tweet",
      "arguments": {
        "content": "Flexibility is key! Plans changed, but the adventure continues.",
        "tags": [
          "#TravelBlog"
        ],
        "mentions": [
          "@Spontaneity"
        ]
      }
    }
  },
  {
    "user_turn": 2,
    "action_in_turn": 4,
    "message_index": 20,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_post_tweet",
      "arguments": {
        "content": "Flexibility is key! Plans changed, but the adventure continues.",
        "tags": [
          "#TravelBlog"
        ],
        "mentions": [
          "@Spontaneity"
        ]
      }
    }
  },
  {
    "user_turn": 2,
    "action_in_turn": 5,
    "message_index": 22,
    "action": {
      "wrapper": "call_tool",
      "name": "mactoring",
      "arguments": {}
    }
  },
  {
    "user_turn": 3,
    "action_in_turn": 1,
    "message_index": 26,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_retweet",
      "arguments": {
        "tweet_id": 12
      }
    }
  },
  {
    "user_turn": 3,
    "action_in_turn": 2,
    "message_index": 28,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_search_tweets",
      "arguments": {
        "keyword": "spontaneity"
      }
    }
  },
  {
    "user_turn": 3,
    "action_in_turn": 3,
    "message_index": 30,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_mention",
      "arguments": {
        "tweet_id": 1,
        "mentioned_usernames": [
          "@Spontaneity"
        ]
      }
    }
  },
  {
    "user_turn": 3,
    "action_in_turn": 4,
    "message_index": 32,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_get_tweet_comments",
      "arguments": {
        "tweet_id": 1
      }
    }
  },
  {
    "user_turn": 3,
    "action_in_turn": 5,
    "message_index": 34,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_like_tweet",
      "arguments": {
        "tweet_id": 1
      }
    }
  },
  {
    "user_turn": 3,
    "action_in_turn": 6,
    "message_index": 36,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_post_tweet",
      "arguments": {
        "content": "Retweet success!",
        "tags": [
          "#TravelBlog"
        ],
        "mentions": [
          "@Spontaneity"
        ]
      }
    }
  },
  {
    "user_turn": 3,
    "action_in_turn": 7,
    "message_index": 38,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_get_tweet_comments",
      "arguments": {
        "tweet_id": 13
      }
    }
  },
  {
    "user_turn": 3,
    "action_in_turn": 8,
    "message_index": 40,
    "action": {
      "wrapper": "call_tool",
      "arguments": {
        "tool": "mcp_tool_get_tweet_comments",
        "arguments": {
          "tweet_id": 13
        }
      }
    }
  }
]
```

</details>

### QeRL：未通过

实际任务调用 12 次；[完整 CoT 和工具返回](QeRL/cot_and_actions.txt)。

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
        "location": "New York"
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
        "location": "Tokyo"
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
        "travel_from": "JFK",
        "travel_to": "HND",
        "travel_date": "2026-12-24",
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
        "access_token": "abc123xyz",
        "card_id": "card_5678",
        "travel_date": "2026-12-24",
        "travel_from": "JFK",
        "travel_to": "HND",
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
      "name": "mcp_tool_authenticate_twitter",
      "arguments": {
        "username": "john",
        "password": "john1234"
      }
    }
  },
  {
    "user_turn": 2,
    "action_in_turn": 2,
    "message_index": 16,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_post_tweet",
      "arguments": {
        "content": "Flexibility is key! Plans changed, but the adventure continues.",
        "tags": [
          "#TravelBlog"
        ],
        "mentions": [
          "@Spontaneity"
        ]
      }
    }
  },
  {
    "user_turn": 2,
    "action_in_turn": 3,
    "message_index": 18,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_post_tweet",
      "arguments": {
        "content": "Flexibility is key! Plans changed, but the adventure continues.",
        "tags": [
          "#TravelBlog"
        ],
        "mentions": [
          "@Spontaneity"
        ]
      }
    }
  },
  {
    "user_turn": 2,
    "action_in_turn": 4,
    "message_index": 20,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_post_tweet",
      "arguments": {
        "content": "Flexibility is key! Plans changed, but the adventure continues.",
        "tags": [
          "#TravelBlog"
        ],
        "mentions": [
          "@Spontaneity"
        ]
      }
    }
  },
  {
    "user_turn": 2,
    "action_in_turn": 5,
    "message_index": 22,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_post_tweet",
      "arguments": {
        "content": "Flexility is key! Plans changed, but the adventure continues.",
        "tags": [
          "#TravelBlog"
        ],
        "mentions": [
          "@Spontaneity"
        ]
      }
    }
  },
  {
    "user_turn": 2,
    "action_in_turn": 6,
    "message_index": 24,
    "action": {
      "wrapper": "call_tool",
      "name": "m://post_tweet",
      "arguments": {
        "content": "Flexibility is key! Plans changed, but the adventure continues.",
        "tags": [
          "#TravelBlog"
        ],
        "mentions": [
          "@Spontaneity"
        ]
      }
    }
  },
  {
    "user_turn": 2,
    "action_in_turn": 7,
    "message_index": 26,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_post_tweet",
      "arguments": {
        "content": "Flexibility is key! Plans changed, but the adventure continues.",
        "tags": [
          "#TravelBlog"
        ],
        "mentions": [
          "@Spontaneity"
        ]
      }
    }
  },
  {
    "user_turn": 3,
    "action_in_turn": 1,
    "message_index": 30,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_retweet",
      "arguments": {
        "tweet_id": 14
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

最早动作差异：第 1 个用户轮，第 4 个任务动作；BF16 消息 10，本方法消息 None。

该位置没有对应任务调用；该轮 assistant 消息为 [2, 4, 6, 8, 10]。

```json
[
  {
    "field": "$",
    "reference": {
      "wrapper": "call_tool",
      "name": "mcp_tool_book_flight",
      "arguments": {
        "access_token": "abc123xyz",
        "card_id": "card_5678",
        "travel_date": "2026-12-24",
        "travel_from": "JFK",
        "travel_to": "HND",
        "travel_class": "first"
      }
    },
    "actual": null
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
    "actual": "abc123xyz",
    "reference_present": false,
    "actual_present": true
  },
  {
    "field": "$.arguments.card_id",
    "reference": null,
    "actual": "card_5678",
    "reference_present": false,
    "actual_present": true
  },
  {
    "field": "$.arguments.passenger_info",
    "reference": null,
    "actual": {
      "first_name": "Michael",
      "last_name": "Thompson",
      "date_of_birth": "1985-05-15",
      "passport_number": "USPAS12345678"
    },
    "reference_present": false,
    "actual_present": true
  },
  {
    "field": "$.arguments.payment_method",
    "reference": null,
    "actual": {
      "cvv": "456"
    },
    "reference_present": false,
    "actual_present": true
  },
  {
    "field": "$.name",
    "reference": "mcp_tool_get_flight_cost",
    "actual": "mcp_tool_call_checkout_flow_for_payment_and_reservation"
  }
]
```

### BitDistiller

最早动作差异：第 1 个用户轮，第 1 个任务动作；BF16 消息 4，本方法消息 4。

```json
[
  {
    "field": "$.arguments.location",
    "reference": "New York",
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
    "actual": "2026-12-24",
    "reference_present": false,
    "actual_present": true
  },
  {
    "field": "$.arguments.travel_from",
    "reference": null,
    "actual": "JFK",
    "reference_present": false,
    "actual_present": true
  },
  {
    "field": "$.arguments.travel_to",
    "reference": null,
    "actual": "NRT",
    "reference_present": false,
    "actual_present": true
  },
  {
    "field": "$.name",
    "reference": "mcp_tool_get_nearest_airport_by_city",
    "actual": "mcp_tool_get_flight_cost"
  }
]
```

### On-Policy QAD

最早动作差异：第 2 个用户轮，第 3 个任务动作；BF16 消息 None，本方法消息 18。

```json
[
  {
    "field": "$",
    "reference": null,
    "actual": {
      "wrapper": "call_tool",
      "name": "mcp_tool_post_tweet",
      "arguments": {
        "content": "Flexibility is key! Plans changed, but the adventure continues.",
        "tags": [
          "#TravelBlog"
        ],
        "mentions": [
          "@Spontaneity"
        ]
      }
    }
  }
]
```

### QeRL

最早动作差异：第 2 个用户轮，第 3 个任务动作；BF16 消息 None，本方法消息 18。

```json
[
  {
    "field": "$",
    "reference": null,
    "actual": {
      "wrapper": "call_tool",
      "name": "mcp_tool_post_tweet",
      "arguments": {
        "content": "Flexibility is key! Plans changed, but the adventure continues.",
        "tags": [
          "#TravelBlog"
        ],
        "mentions": [
          "@Spontaneity"
        ]
      }
    }
  }
]
```

## 失败原因

不同方法失败在不同子任务：部分没有形成参考订票记录或扣款状态，部分没有形成要求的推文状态。不能把五种方法都概括成同一个订票错误。

### GPTQ

评分指出的失败位置/原因：

```text
"Model instance for TravelAPI does not match the state with ground truth instance."
```

- 状态字段 `credit_card_list.card_5678.balance`：实际 50000.0；参考 46000.0。
- 状态字段 `booking_record.3426812`：实际 null；参考 {"card_id": "card_5678", "travel_date": "2026-12-24", "travel_from": "JFK", "travel_to": "HND", "travel_class": "first", "travel_cost": 4000.0, "transaction_id": "45451592"}。
### EfficientQAT

评分指出的失败位置/原因：

```text
"Model instance for TravelAPI does not match the state with ground truth instance."
```

- 状态字段 `credit_card_list.262919693687`：实际 {"card_number": "XXXX5678", "expiration_date": "12/26", "cardholder_name": "Michael Thompson", "card_verification_number": "456", "balance": 40620.0}；参考 null。
- 状态字段 `credit_card_list.card_5678.balance`：实际 50000.0；参考 46000.0。
- 状态字段 `booking_record.3426812`：实际 null；参考 {"card_id": "card_5678", "travel_date": "2026-12-24", "travel_from": "JFK", "travel_to": "HND", "travel_class": "first", "travel_cost": 4000.0, "transaction_id": "45451592"}。
- 状态字段 `booking_record.7223063`：实际 {"card_id": "262919693687", "travel_date": "2026-12-24", "travel_from": "JFK", "travel_to": "HND", "travel_class": "first", "travel_cost": 4000.0, "transaction_id": "35535380"}；参考 null。
### BitDistiller

评分指出的失败位置/原因：

```text
"Model instance for TravelAPI does not match the state with ground truth instance."
```

- 状态字段 `credit_card_list.card_5678.balance`：实际 50000.0；参考 46000.0。
- 状态字段 `booking_record.3426812`：实际 null；参考 {"card_id": "card_5678", "travel_date": "2026-12-24", "travel_from": "JFK", "travel_to": "HND", "travel_class": "first", "travel_cost": 4000.0, "transaction_id": "45451592"}。
### On-Policy QAD

评分指出的失败位置/原因：

```text
"Model instance for TwitterAPI does not match the state with ground truth instance."
```

- 状态字段 `tweets.11`：实际 {"id": 11, "username": "john", "content": "Flexibility is key! Plans changed, but the adventure continues.", "tags": ["#TravelBlog"], "mentions": ["@Spontaneity"]}；参考 null。
- 状态字段 `tweets.12`：实际 {"id": 12, "username": "john", "content": "Flexibility is key! Plans changed, but the adventure continues.", "tags": ["#TravelBlog"], "mentions": ["@Spontaneity"]}；参考 null。
- 状态字段 `tweet_counter`：实际 13；参考 11。
### QeRL

评分指出的失败位置/原因：

```text
"Model instance for TwitterAPI does not match the state with ground truth instance."
```

- 状态字段 `tweets.11`：实际 {"id": 11, "username": "john", "content": "Flexibility is key! Plans changed, but the adventure continues.", "tags": ["#TravelBlog"], "mentions": ["@Spontaneity"]}；参考 null。
- 状态字段 `tweets.12`：实际 {"id": 12, "username": "john", "content": "Flexibility is key! Plans changed, but the adventure continues.", "tags": ["#TravelBlog"], "mentions": ["@Spontaneity"]}；参考 null。
- 状态字段 `tweets.13`：实际 {"id": 13, "username": "john", "content": "Flexility is key! Plans changed, but the adventure continues.", "tags": ["#TravelBlog"], "mentions": ["@Spontaneity"]}；参考 null。
- 状态字段 `tweets.14`：实际 {"id": 14, "username": "john", "content": "Flexibility is key! Plans changed, but the adventure continues.", "tags": ["#TravelBlog"], "mentions": ["@Spontaneity"]}；参考 null。
- 状态字段 `tweet_counter`：实际 15；参考 11。
