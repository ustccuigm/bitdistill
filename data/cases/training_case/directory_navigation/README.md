# Directory navigation: ls / cd / cat

任务：读取workspace目录中的report.txt并返回内容，不修改文件。

这是把论文teaser的示意任务具体化后补做的实验。原图没有文件名或历史运行编号；这里不声称恢复了原图的训练轨迹。

使用服务器保存的BFCL GorillaFileSystem实现。实际重放显示：ls只返回目录条目，不改变当前目录；此时直接cat(report.txt)返回文件不存在；cd(workspace)后cat(report.txt)可读取正确内容。图中的错误cat动作是按图重放的动作，并非此次模型采样出的失败。

另外实际运行了BF16、无指导学生、有指导学生三个分支。每个分支结果见[results.json](results.json)，完整请求、响应、工具执行和最终状态保存在对应文件夹。若无指导学生也通过，不能将此记录描述成它在本次实验中发生了目录错误。

teacher的实际分析请求、响应和指导位于[steering](steering)，固定输入见[context_before.json](context_before.json)，工具定义见[tools.json](tools.json)，图中动作的环境重放见[figure_action_execution.json](figure_action_execution.json)。验收检查实际读到目标内容、最终答复包含该内容且文件系统未被修改；这不是官方BFCL整套评测分数。
