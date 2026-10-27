# Sales-order steering comparison

任务为`b2b_commerce_1:1`：为Joe's Auto Repair创建订单，加入三种零件及指定数量，应用折扣规则，并按任务要求处理backorder。

任务及成功参考轨迹已从保存的训练记录中定位，见[sales_order_source](sales_order_source)。论文图里的四段文字不充当模型实际输出，本次四种steer均通过真实模型请求重新生成。

两个补充对比位置：

- point_1：客户和仓库已查询、订单头尚未创建。使用原失败轨迹的assistant turn 2之前上下文。
- point_2：订单头已创建、还未查询零件。使用同一任务成功参考轨迹的assistant turn 3之前上下文。

每个位置设计比较Teacher/Structured、Teacher/Free-form、Student/Structured、External LLM/Structured。前三组已实际执行；External LLM接口返回HTTP 403、账户余额不足，两组尚未完成，不计作模型失败。各本地分支从同一初始数据库及相同前序动作重放起步，学生checkpoint相同，温度0、seed 42。保存实际分析请求与响应、steering prompt、学生完整续跑、工具接口、执行记录及数据库，结果见[results.json](results.json)。模型身份及参数见各请求记录与run_manifest.json；本地Teacher为Gemma BF16，Student为该模型初始CLIP量化checkpoint。

这是基于已定位任务和明确前置状态补做的对比，不把不同训练轮次的两条历史steer拼成同一次干预。先查询零件与先创建订单的差别本身不证明动作错误，任务是否完成以实际状态和任务verifier为准。

| 指导方式 | point_1 | point_2 |
|---|---|---|
| Teacher / Structured | complete | complete |
| Teacher / Free-form | others，达到输出上限 | complete |
| Student / Structured | others | others |
| External LLM / Structured | API余额不足，未完成 | API余额不足，未完成 |

实际teacher结构化指导强调按折扣规则计算价格，不能以论文图中的“必须先创建订单再查询零件”替代此次诊断。一个位置的free-form也通过了验收，因此本实验不支持“free-form总会失败”的结论。
