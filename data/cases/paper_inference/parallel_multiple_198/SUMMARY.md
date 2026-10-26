# parallel_multiple_198

原始任务和工具定义见 task.json；标准答案见 ground_truth.json。完整推理、调用、工具返回、调用消息位置和正式评分位于各方法目录。

对应论文图 7。BF16、Ours 通过，五个比较方法未通过。GPTQ 选中样本在 Higgs Boson 查询时生成错误工具名 m-core-mcp-tool-science-history-get-discovery-details；不是原图所写的遗漏子任务。论文描述应随实际样本调整。

| 方法 | 整题评分 |
| --- | --- |
| BF16 | 通过 |
| GPTQ | 未通过 |
| EfficientQAT | 未通过 |
| BitDistiller | 未通过 |
| On-Policy QAD | 未通过 |
| QeRL | 未通过 |
| Ours | 通过 |
