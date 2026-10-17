# BFCL v4: 40 selected cases

40 个按结果选取的案例，每例展示 BF16、Ours、GPTQ、EfficientQAT、BitDistiller、On-Policy QAD、QeRL 七种方法的所选轨迹。结果指这些轨迹的原始 BFCL 评分。

逐例 summary.md 仅包含原始任务、七种方法的实际表现、分歧位置和失败原因。原始任务及工具定义见 task.json，完整推理与工具返回见各方法的 cot_and_actions.txt 和 trajectory.json。评分、请求和采样原始记录一并保留。

部分案例涉及字符串或格式匹配，具体含义在失败原因中说明。分歧位置是实际动作对照，不是 token 概率测量。

| Case | 原始任务 ID | 总结 |
| --- | --- | --- |
| 001 | irrelevance_162 | [查看](cases/001_irrelevance_162/summary.md) |
| 002 | irrelevance_44 | [查看](cases/002_irrelevance_44/summary.md) |
| 003 | live_irrelevance_222-34-11 | [查看](cases/003_live_irrelevance_222-34-11/summary.md) |
| 004 | live_irrelevance_307-76-5 | [查看](cases/004_live_irrelevance_307-76-5/summary.md) |
| 005 | live_irrelevance_530-164-0 | [查看](cases/005_live_irrelevance_530-164-0/summary.md) |
| 006 | live_irrelevance_578-181-0 | [查看](cases/006_live_irrelevance_578-181-0/summary.md) |
| 007 | live_irrelevance_593-188-0 | [查看](cases/007_live_irrelevance_593-188-0/summary.md) |
| 008 | live_irrelevance_620-196-1 | [查看](cases/008_live_irrelevance_620-196-1/summary.md) |
| 009 | live_irrelevance_623-196-4 | [查看](cases/009_live_irrelevance_623-196-4/summary.md) |
| 010 | live_irrelevance_875-360-0 | [查看](cases/010_live_irrelevance_875-360-0/summary.md) |
| 011 | live_irrelevance_876-361-0 | [查看](cases/011_live_irrelevance_876-361-0/summary.md) |
| 012 | live_multiple_1031-259-0 | [查看](cases/012_live_multiple_1031-259-0/summary.md) |
| 013 | live_multiple_142-55-0 | [查看](cases/013_live_multiple_142-55-0/summary.md) |
| 014 | live_multiple_386-137-4 | [查看](cases/014_live_multiple_386-137-4/summary.md) |
| 015 | live_multiple_500-148-10 | [查看](cases/015_live_multiple_500-148-10/summary.md) |
| 016 | live_multiple_557-154-3 | [查看](cases/016_live_multiple_557-154-3/summary.md) |
| 017 | live_multiple_853-180-1 | [查看](cases/017_live_multiple_853-180-1/summary.md) |
| 018 | live_parallel_multiple_4-3-0 | [查看](cases/018_live_parallel_multiple_4-3-0/summary.md) |
| 019 | live_simple_31-8-1 | [查看](cases/019_live_simple_31-8-1/summary.md) |
| 020 | multi_turn_base_134 | [查看](cases/020_multi_turn_base_134/summary.md) |
| 021 | multi_turn_base_189 | [查看](cases/021_multi_turn_base_189/summary.md) |
| 022 | multi_turn_base_39 | [查看](cases/022_multi_turn_base_39/summary.md) |
| 023 | multi_turn_long_context_39 | [查看](cases/023_multi_turn_long_context_39/summary.md) |
| 024 | multi_turn_long_context_49 | [查看](cases/024_multi_turn_long_context_49/summary.md) |
| 025 | multi_turn_miss_func_127 | [查看](cases/025_multi_turn_miss_func_127/summary.md) |
| 026 | multi_turn_miss_func_151 | [查看](cases/026_multi_turn_miss_func_151/summary.md) |
| 027 | multi_turn_miss_func_181 | [查看](cases/027_multi_turn_miss_func_181/summary.md) |
| 028 | multi_turn_miss_func_47 | [查看](cases/028_multi_turn_miss_func_47/summary.md) |
| 029 | multi_turn_miss_param_111 | [查看](cases/029_multi_turn_miss_param_111/summary.md) |
| 030 | multi_turn_miss_param_117 | [查看](cases/030_multi_turn_miss_param_117/summary.md) |
| 031 | multi_turn_miss_param_127 | [查看](cases/031_multi_turn_miss_param_127/summary.md) |
| 032 | multi_turn_miss_param_152 | [查看](cases/032_multi_turn_miss_param_152/summary.md) |
| 033 | multi_turn_miss_param_26 | [查看](cases/033_multi_turn_miss_param_26/summary.md) |
| 034 | parallel_191 | [查看](cases/034_parallel_191/summary.md) |
| 035 | parallel_93 | [查看](cases/035_parallel_93/summary.md) |
| 036 | parallel_multiple_144 | [查看](cases/036_parallel_multiple_144/summary.md) |
| 037 | parallel_multiple_156 | [查看](cases/037_parallel_multiple_156/summary.md) |
| 038 | parallel_multiple_75 | [查看](cases/038_parallel_multiple_75/summary.md) |
| 039 | simple_python_130 | [查看](cases/039_simple_python_130/summary.md) |
| 040 | simple_python_395 | [查看](cases/040_simple_python_395/summary.md) |
