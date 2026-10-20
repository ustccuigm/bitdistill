# Case 037 — parallel_multiple_156

## 任务

第 1 轮：

"Could you please help me with the following tasks? First, I have two groups of data points: group1 consists of [12, 15, 18, 22, 25] and group2 consists of [20, 23, 26, 29, 32]. I want to run a two-sample t-test on these groups with the assumption that they have equal variance. Second, I'm currently in Boston, MA and I'm craving for some Sushi. Could you find the closest sushi restaurant that has a Patio and Wi-Fi? Lastly, I've recently taken up painting as a hobby and I'm curious about the common personality traits associated with it. Could you retrieve the top 5 personality traits of people who enjoy painting?"

完整工具定义、初始状态及其他任务字段见 task.json。

## 七种方法的实际表现

### BF16：通过

实际任务调用 3 次；[完整 CoT 和工具返回](BF16/cot_and_actions.txt)。

<details><summary>实际动作序列</summary>

```json
[
  {
    "user_turn": 1,
    "action_in_turn": 1,
    "message_index": 4,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_run_two_sample_ttest",
      "arguments": {
        "group1": [
          12,
          15,
          18,
          22,
          25
        ],
        "group2": [
          20,
          23,
          26,
          29,
          32
        ],
        "equal_variance": true
      }
    }
  },
  {
    "user_turn": 1,
    "action_in_turn": 2,
    "message_index": 6,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_restaurant_search.find_closest",
      "arguments": {
        "location": "Boston, MA",
        "cuisine": "Sushi",
        "amenities": [
          "Patio",
          "Wi-Fi"
        ]
      }
    }
  },
  {
    "user_turn": 1,
    "action_in_turn": 3,
    "message_index": 8,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_get_personality_traits",
      "arguments": {
        "hobby": "painting",
        "trait_count": 5
      }
    }
  }
]
```

</details>

### Ours：通过

实际任务调用 3 次；[完整 CoT 和工具返回](Ours/cot_and_actions.txt)。

<details><summary>实际动作序列</summary>

```json
[
  {
    "user_turn": 1,
    "action_in_turn": 1,
    "message_index": 4,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_run_two_sample_ttest",
      "arguments": {
        "group1": [
          12,
          15,
          18,
          22,
          25
        ],
        "group2": [
          20,
          23,
          26,
          29,
          32
        ],
        "equal_variance": true
      }
    }
  },
  {
    "user_turn": 1,
    "action_in_turn": 2,
    "message_index": 6,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_restaurant_search.find_closest",
      "arguments": {
        "location": "Boston, MA",
        "cuisine": "Sushi",
        "amenities": [
          "Patio",
          "Wi-Fi"
        ]
      }
    }
  },
  {
    "user_turn": 1,
    "action_in_turn": 3,
    "message_index": 8,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_get_personality_traits",
      "arguments": {
        "hobby": "Painting",
        "trait_count": 5
      }
    }
  }
]
```

</details>

### GPTQ：未通过

实际任务调用 3 次；[完整 CoT 和工具返回](GPTQ/cot_and_actions.txt)。

<details><summary>实际动作序列</summary>

```json
[
  {
    "user_turn": 1,
    "action_in_turn": 1,
    "message_index": 4,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_run_two_sample_ttest",
      "arguments": {
        "group1": [
          12,
          15,
          18,
          22,
          25
        ],
        "group2": [
          20,
          23,
          26,
          29,
          32
        ],
        "equal_variance": true
      }
    }
  },
  {
    "user_turn": 1,
    "action_in_turn": 2,
    "message_index": 6,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_restaurant_search.find_closest",
      "arguments": {
        "location": "Boston, MA",
        "cuisine": "Sushi",
        "amenities": [
          "Patio",
          "Wi-Fi"
        ]
      }
    }
  },
  {
    "user_turn": 1,
    "action_in_turn": 3,
    "message_index": 8,
    "action": {
      "wrapper": "call_tool",
      "arguments": {
        "tool,\"trait_count": 5
      }
    }
  }
]
```

</details>

### EfficientQAT：未通过

实际任务调用 3 次；[完整 CoT 和工具返回](EfficientQAT/cot_and_actions.txt)。

<details><summary>实际动作序列</summary>

```json
[
  {
    "user_turn": 1,
    "action_in_turn": 1,
    "message_index": 4,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_run_two_sample_ttest",
      "arguments": {
        "group1": [
          12,
          15,
          18,
          23,
          27
        ],
        "group2": [
          24,
          26,
          29,
          31,
          33
        ],
        "equal_variance": true
      }
    }
  },
  {
    "user_turn": 1,
    "action_in_turn": 2,
    "message_index": 6,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_restaurant_search.find_closest",
      "arguments": {
        "location": "Boston, MA",
        "cuisine": "Sushi",
        "amenities": [
          "Patio",
          "Wi-Fi"
        ]
      }
    }
  },
  {
    "user_turn": 1,
    "action_in_turn": 3,
    "message_index": 8,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_get_personality_traits",
      "arguments": {
        "hobby": "Painting",
        "trait_count": 5
      }
    }
  }
]
```

</details>

### BitDistiller：未通过

实际任务调用 3 次；[完整 CoT 和工具返回](BitDistiller/cot_and_actions.txt)。

<details><summary>实际动作序列</summary>

```json
[
  {
    "user_turn": 1,
    "action_in_turn": 1,
    "message_index": 4,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_run_two_sample_ttest",
      "arguments": {
        "group1": [
          12,
          15,
          18,
          22,
          25
        ],
        "group2": [
          20,
          23,
          26,
          29,
          30
        ],
        "equal_variance": true
      }
    }
  },
  {
    "user_turn": 1,
    "action_in_turn": 2,
    "message_index": 6,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_restaurant_search.find_closest",
      "arguments": {
        "location": "Boston, MA",
        "cuisine": "Sushi",
        "amenities": [
          "patio",
          "wifi"
        ]
      }
    }
  },
  {
    "user_turn": 1,
    "action_in_turn": 3,
    "message_index": 8,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_get_personality_traits",
      "arguments": {
        "hobby": "painting",
        "trait_count": 5
      }
    }
  }
]
```

</details>

### On-Policy QAD：未通过

实际任务调用 3 次；[完整 CoT 和工具返回](On-Policy%20QAD/cot_and_actions.txt)。

<details><summary>实际动作序列</summary>

```json
[
  {
    "user_turn": 1,
    "action_in_turn": 1,
    "message_index": 4,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_run_two_sample_ttest",
      "arguments": {
        "group1": [
          12,
          15,
          18,
          22,
          25
        ],
        "group2": [
          20,
          23,
          26,
          29,
          33
        ],
        "equal_variance": true
      }
    }
  },
  {
    "user_turn": 1,
    "action_in_turn": 2,
    "message_index": 6,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_restaurant_search.find_closest",
      "arguments": {
        "location": "Boston, MA",
        "cuisine": "Sushi",
        "amenities": [
          "Patio",
          "Wi-Fi"
        ]
      }
    }
  },
  {
    "user_turn": 1,
    "action_in_turn": 3,
    "message_index": 8,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_get_personality_traits",
      "arguments": {
        "hobby": "Painting",
        "trait_count": 5
      }
    }
  }
]
```

</details>

### QeRL：未通过

实际任务调用 3 次；[完整 CoT 和工具返回](QeRL/cot_and_actions.txt)。

<details><summary>实际动作序列</summary>

```json
[
  {
    "user_turn": 1,
    "action_in_turn": 1,
    "message_index": 4,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_run_two_sample_ttest",
      "arguments": {
        "group1": [
          12,
          15,
          18,
          22,
          25
        ],
        "group2": [
          20,
          23,
          26,
          29,
          30
        ],
        "equal_variance": true
      }
    }
  },
  {
    "user_turn": 1,
    "action_in_turn": 2,
    "message_index": 6,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_restaurant_search.find_closest",
      "arguments": {
        "location": "Boston, MA",
        "cuisine": "Sushi",
        "amenities": [
          "Patio",
          "Wi-Fi"
        ]
      }
    }
  },
  {
    "user_turn": 1,
    "action_in_turn": 3,
    "message_index": 8,
    "action": {
      "wrapper": "call_tool",
      "name": "mcp_tool_get_personality_traits",
      "arguments": {
        "hobby": "Painting",
        "trait_count": 5
      }
    }
  }
]
```

</details>

## 分歧位置

消息编号从 0 开始，用户轮和动作编号从 1 开始。按同一用户轮的任务动作序号与 BF16 比较，忽略 list_tools。最早动作差异不一定就是失败起点：正确的工具顺序、补救步骤也可能不同；评分失败位置另见下一节。

### Ours

最早动作差异：第 1 个用户轮，第 3 个任务动作；BF16 消息 8，本方法消息 8。

```json
[
  {
    "field": "$.arguments.hobby",
    "reference": "painting",
    "actual": "Painting"
  }
]
```

### GPTQ

最早动作差异：第 1 个用户轮，第 3 个任务动作；BF16 消息 8，本方法消息 8。

```json
[
  {
    "field": "$.arguments.hobby",
    "reference": "painting",
    "actual": null,
    "reference_present": true,
    "actual_present": false
  },
  {
    "field": "$.arguments.tool,\"trait_count",
    "reference": null,
    "actual": 5,
    "reference_present": false,
    "actual_present": true
  },
  {
    "field": "$.arguments.trait_count",
    "reference": 5,
    "actual": null,
    "reference_present": true,
    "actual_present": false
  },
  {
    "field": "$.name",
    "reference": "mcp_tool_get_personality_traits",
    "actual": null,
    "reference_present": true,
    "actual_present": false
  }
]
```

### EfficientQAT

最早动作差异：第 1 个用户轮，第 1 个任务动作；BF16 消息 4，本方法消息 4。

```json
[
  {
    "field": "$.arguments.group1[3]",
    "reference": 22,
    "actual": 23
  },
  {
    "field": "$.arguments.group1[4]",
    "reference": 25,
    "actual": 27
  },
  {
    "field": "$.arguments.group2[0]",
    "reference": 20,
    "actual": 24
  },
  {
    "field": "$.arguments.group2[1]",
    "reference": 23,
    "actual": 26
  },
  {
    "field": "$.arguments.group2[2]",
    "reference": 26,
    "actual": 29
  },
  {
    "field": "$.arguments.group2[3]",
    "reference": 29,
    "actual": 31
  },
  {
    "field": "$.arguments.group2[4]",
    "reference": 32,
    "actual": 33
  }
]
```

### BitDistiller

最早动作差异：第 1 个用户轮，第 1 个任务动作；BF16 消息 4，本方法消息 4。

```json
[
  {
    "field": "$.arguments.group2[4]",
    "reference": 32,
    "actual": 30
  }
]
```

### On-Policy QAD

最早动作差异：第 1 个用户轮，第 1 个任务动作；BF16 消息 4，本方法消息 4。

```json
[
  {
    "field": "$.arguments.group2[4]",
    "reference": 32,
    "actual": 33
  }
]
```

### QeRL

最早动作差异：第 1 个用户轮，第 1 个任务动作；BF16 消息 4，本方法消息 4。

```json
[
  {
    "field": "$.arguments.group2[4]",
    "reference": 32,
    "actual": 30
  }
]
```

## 失败原因

GPTQ 调用数量不匹配；其他 baseline 改变了 t 检验输入数据，例如把 group2 最后一项 32 写成 30 或 33，实际计算对象因此变化。

### GPTQ

评分指出的失败位置/原因：

```text
["Wrong number of functions."]
```

### EfficientQAT

评分指出的失败位置/原因：

```text
["Could not find a matching function among index [0, 1, 2] of model output for index 0 of possible answers.", {"Model Result Index 0": {"sub_error": ["Invalid value for parameter 'group1': [12, 15, 18, 23, 27]. Expected one of [[12, 15, 18, 22, 25]]."], "sub_error_type": "value_error:list/tuple", "model_output_item": {"run_two_sample_ttest": {"group1": [12, 15, 18, 23, 27], "group2": [24, 26, 29, 31, 33], "equal_variance": true}}, "possible_answer_item": {"run_two_sample_ttest": {"group1": [[12, 15, 18, 22, 25]], "group2": [[20, 23, 26, 29, 32]], "equal_variance": [true, ""]}}}}, {"Model Result Index 1": {"sub_error": ["Function name 'run_two_sample_ttest' not found in model output."], "sub_error_type": "simple_function_checker:wrong_func_name", "model_output_item": {"restaurant_search.find_closest": {"location": "Boston, MA", "cuisine": "Sushi", "amenities": ["Patio", "Wi-Fi"]}}, "possible_answer_item": {"run_two_sample_ttest": {"group1": [[12, 15, 18, 22, 25]], "group2": [[20, 23, 26, 29, 32]], "equal_variance": [true, ""]}}}}, {"Model Result Index 2": {"sub_error": ["Function name 'run_two_sample_ttest' not found in model output."], "sub_error_type": "simple_function_checker:wrong_func_name", "model_output_item": {"get_personality_traits": {"hobby": "Painting", "trait_count": 5}}, "possible_answer_item": {"run_two_sample_ttest": {"group1": [[12, 15, 18, 22, 25]], "group2": [[20, 23, 26, 29, 32]], "equal_variance": [true, ""]}}}}]
```

### BitDistiller

评分指出的失败位置/原因：

```text
["Could not find a matching function among index [0, 1, 2] of model output for index 0 of possible answers.", {"Model Result Index 0": {"sub_error": ["Invalid value for parameter 'group2': [20, 23, 26, 29, 30]. Expected one of [[20, 23, 26, 29, 32]]."], "sub_error_type": "value_error:list/tuple", "model_output_item": {"run_two_sample_ttest": {"group1": [12, 15, 18, 22, 25], "group2": [20, 23, 26, 29, 30], "equal_variance": true}}, "possible_answer_item": {"run_two_sample_ttest": {"group1": [[12, 15, 18, 22, 25]], "group2": [[20, 23, 26, 29, 32]], "equal_variance": [true, ""]}}}}, {"Model Result Index 1": {"sub_error": ["Function name 'run_two_sample_ttest' not found in model output."], "sub_error_type": "simple_function_checker:wrong_func_name", "model_output_item": {"restaurant_search.find_closest": {"location": "Boston, MA", "cuisine": "Sushi", "amenities": ["patio", "wifi"]}}, "possible_answer_item": {"run_two_sample_ttest": {"group1": [[12, 15, 18, 22, 25]], "group2": [[20, 23, 26, 29, 32]], "equal_variance": [true, ""]}}}}, {"Model Result Index 2": {"sub_error": ["Function name 'run_two_sample_ttest' not found in model output."], "sub_error_type": "simple_function_checker:wrong_func_name", "model_output_item": {"get_personality_traits": {"hobby": "painting", "trait_count": 5}}, "possible_answer_item": {"run_two_sample_ttest": {"group1": [[12, 15, 18, 22, 25]], "group2": [[20, 23, 26, 29, 32]], "equal_variance": [true, ""]}}}}]
```

### On-Policy QAD

评分指出的失败位置/原因：

```text
["Could not find a matching function among index [0, 1, 2] of model output for index 0 of possible answers.", {"Model Result Index 0": {"sub_error": ["Invalid value for parameter 'group2': [20, 23, 26, 29, 33]. Expected one of [[20, 23, 26, 29, 32]]."], "sub_error_type": "value_error:list/tuple", "model_output_item": {"run_two_sample_ttest": {"group1": [12, 15, 18, 22, 25], "group2": [20, 23, 26, 29, 33], "equal_variance": true}}, "possible_answer_item": {"run_two_sample_ttest": {"group1": [[12, 15, 18, 22, 25]], "group2": [[20, 23, 26, 29, 32]], "equal_variance": [true, ""]}}}}, {"Model Result Index 1": {"sub_error": ["Function name 'run_two_sample_ttest' not found in model output."], "sub_error_type": "simple_function_checker:wrong_func_name", "model_output_item": {"restaurant_search.find_closest": {"location": "Boston, MA", "cuisine": "Sushi", "amenities": ["Patio", "Wi-Fi"]}}, "possible_answer_item": {"run_two_sample_ttest": {"group1": [[12, 15, 18, 22, 25]], "group2": [[20, 23, 26, 29, 32]], "equal_variance": [true, ""]}}}}, {"Model Result Index 2": {"sub_error": ["Function name 'run_two_sample_ttest' not found in model output."], "sub_error_type": "simple_function_checker:wrong_func_name", "model_output_item": {"get_personality_traits": {"hobby": "Painting", "trait_count": 5}}, "possible_answer_item": {"run_two_sample_ttest": {"group1": [[12, 15, 18, 22, 25]], "group2": [[20, 23, 26, 29, 32]], "equal_variance": [true, ""]}}}}]
```

### QeRL

评分指出的失败位置/原因：

```text
["Could not find a matching function among index [0, 1, 2] of model output for index 0 of possible answers.", {"Model Result Index 0": {"sub_error": ["Invalid value for parameter 'group2': [20, 23, 26, 29, 30]. Expected one of [[20, 23, 26, 29, 32]]."], "sub_error_type": "value_error:list/tuple", "model_output_item": {"run_two_sample_ttest": {"group1": [12, 15, 18, 22, 25], "group2": [20, 23, 26, 29, 30], "equal_variance": true}}, "possible_answer_item": {"run_two_sample_ttest": {"group1": [[12, 15, 18, 22, 25]], "group2": [[20, 23, 26, 29, 32]], "equal_variance": [true, ""]}}}}, {"Model Result Index 1": {"sub_error": ["Function name 'run_two_sample_ttest' not found in model output."], "sub_error_type": "simple_function_checker:wrong_func_name", "model_output_item": {"restaurant_search.find_closest": {"location": "Boston, MA", "cuisine": "Sushi", "amenities": ["Patio", "Wi-Fi"]}}, "possible_answer_item": {"run_two_sample_ttest": {"group1": [[12, 15, 18, 22, 25]], "group2": [[20, 23, 26, 29, 32]], "equal_variance": [true, ""]}}}}, {"Model Result Index 2": {"sub_error": ["Function name 'run_two_sample_ttest' not found in model output."], "sub_error_type": "simple_function_checker:wrong_func_name", "model_output_item": {"get_personality_traits": {"hobby": "Painting", "trait_count": 5}}, "possible_answer_item": {"run_two_sample_ttest": {"group1": [[12, 15, 18, 22, 25]], "group2": [[20, 23, 26, 29, 32]], "equal_variance": [true, ""]}}}}]
```
