# 阶乘：parallel_60

## 原始任务

[
  [
    {
      "role": "user",
      "content": "What is the results of the factorial of 5, the factorial of 7, and the factorial of 9?"
    }
  ]
]

## 七种方法表现与分歧

下列各方法展示一个选中样本，消息下标从 0 开始；完整推理和工具返回见各方法的 cot_and_actions.md。

### BF16：通过
消息 4:
```json
{"name": "call_tool", "arguments": {"tool_name": "mcp_tool_math.factorial", "arguments": "{\"number\": 5}"}}
```
消息 6:
```json
{"name": "call_tool", "arguments": {"tool_name": "mcp_tool_math.factorial", "arguments": "{\"number\": 7}"}}
```
消息 8:
```json
{"name": "call_tool", "arguments": {"tool_name": "mcp_tool_math.factorial", "arguments": "{\"number\": 9}"}}
```

### Ours：通过
消息 4:
```json
{"name": "call_tool", "arguments": {"tool_name": "mcp_tool_math.factorial", "arguments": "{\"number\": 5}"}}
```
消息 6:
```json
{"name": "call_tool", "arguments": {"tool_name": "mcp_tool_math.factorial", "arguments": "{\"number\": 7}"}}
```
消息 8:
```json
{"name": "call_tool", "arguments": {"tool_name": "mcp_tool_math.factorial", "arguments": "{\"number\": 9}"}}
```

### GPTQ：未通过
消息 4:
```json
{"name": "call_tool", "arguments": {"tool_name": "mcp_tool_math.factorial", "arguments": "{\"number\": 5}"}}
```
消息 6:
```json
{"name": "call_tool", "arguments": {"tool_name": "mcp_tool_math.factorial", "arguments": "{\"number\": 7}"}}
```
消息 8:
```json
{"name": "call_tool", "arguments": {"tool_name": "m-core-math-factorial", "arguments": "{\"number\": 9}"}}
```
正式评分：["Invalid syntax. Failed to decode AST. 'BinOp' object has no attribute 'elts'"]

### EfficientQAT：未通过
消息 4:
```json
{"name": "call_tool", "arguments": {"tool_name": "mcp_tool_math.factorial", "arguments": "{\"number\": 5}"}}
```
消息 6:
```json
{"name": "call_tool", "arguments": {"tool_name": "mcp_tool_math.factorial", "arguments": "{\"number\": 7}"}}
```
正式评分：["Wrong number of functions."]

### BitDistiller：未通过
消息 4:
```json
{"name": "call_tool", "arguments": {"tool_name": "mcp_tool_math.factorial", "arguments": "{\"number\": 5}"}}
```
消息 6:
```json
{"name": "call_tool", "arguments": {"tool_name": "mcp_tool_math.factorial", "arguments": "{\"number\": 7}"}}
```
正式评分：["Wrong number of functions."]

### On-Policy QAD：未通过
未生成有效任务工具调用；完整回复见 cot_and_actions.md。
正式评分：["Wrong number of functions."]

### QeRL：未通过
未生成有效任务工具调用；完整回复见 cot_and_actions.md。
正式评分：["Wrong number of functions."]

## 失败原因

选中的 GPTQ 完成 5! 和 7! 的调用，第三次却把 math.factorial 换成 m-core-math-factorial，无法形成合法调用。这与论文中“第三次调用损坏、执行不完整”的错误类型相似，但不是原图 GPTQ“直接回答、不调用工具”的行为；图中文字应据此调整。
