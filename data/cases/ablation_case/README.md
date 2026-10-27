# Ablation case

## Sales-order：等待定位具体实验

当前材料只有[论文图文字](sales_order_figure_text.txt)，描述“创建订单头、查询零件、创建订单行”，但没有具体任务编号、客户和零件标识、原失败轨迹、成功参考轨迹或两个干预前状态。

因此此目录目前是材料整理入口，不是已完成的消融实验结果；图中文字不能充当实际模型请求与响应。

补跑需要固定同一个任务、学生checkpoint、成功参考轨迹及两处干预前状态，然后分别运行Teacher/Structured、Teacher/Free-form、Student/Structured、External LLM/Structured四种方式。保存8组实际请求和响应、student候选动作、环境返回及验收结果，所有尝试都保留。

尚需提供原实验目录或具体task ID及两处状态。不要用任意一个同名sales-order任务替代后声称复现了论文事件。
