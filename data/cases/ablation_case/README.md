# Sales-order steering comparison

任务为`b2b_commerce_1:1`：为Joe's Auto Repair创建订单，加入三种零件及指定数量，应用折扣规则，并按任务要求处理backorder。

任务及成功参考轨迹已从保存的训练记录中定位，见[sales_order_source](sales_order_source)。已完成分支的steer均来自实际模型请求，具体prompt与响应保存在各分支目录。

两个补充对比位置：

- point_1：客户和仓库已查询、订单头尚未创建。使用原失败轨迹的assistant turn 2之前上下文。
- point_2：订单头已创建、还未查询零件。使用同一任务成功参考轨迹的assistant turn 3之前上下文。

每个位置设计比较Teacher/Structured、Teacher/Free-form、Student/Structured、External LLM/Structured。四种方式均已实际执行，External LLM使用gpt-5.6-sol。各本地分支从同一初始数据库及相同前序动作重放起步，学生checkpoint相同，温度0、seed 42。保存实际分析请求与响应、steering prompt、学生完整续跑、工具接口、执行记录及数据库，结果见[results.json](results.json)。模型身份及参数见各请求记录与run_manifest.json；本地Teacher为Gemma BF16，Student为该模型初始CLIP量化checkpoint。

这是基于已定位任务和明确前置状态补做的对比，不把不同训练轮次的两条历史steer拼成同一次干预。先查询零件与先创建订单的差别本身不证明动作错误，任务是否完成以实际状态和任务verifier为准。

## 论文案例展示：订单头尚未创建

采用point_1展示同一任务、同一干预位置下不同指导方式的实际结果，不汇总为成功率或成功次数。

| 指导方式 | 案例结果 |
|---|---|
| Teacher / Structured | 成功：最终订单通过任务验收 |
| Teacher / Free-form | 失败：续跑达到输出上限，最终订单未通过任务验收 |
| Student / Structured | 失败：最终订单未通过任务验收 |
| External LLM / Structured（gpt-5.6-sol） | 失败：学生填入的订单日期早于折扣规则生效日，折扣为零，未通过验收 |

## 补充位置：订单头已创建

point_2保留为独立的补充记录：Teacher / Structured成功，Teacher / Free-form成功，Student / Structured失败；External LLM / Structured（gpt-5.6-sol）成功。此处结果不与主展示合并统计。

实际teacher结构化指导强调按折扣规则计算价格。案例解释应对应保存的prompt、工具执行与验收条件，不能将其改写为已证明“必须先创建订单再查询零件”。

## 外部 LLM 案例原因

point_1的gpt-5.6-sol指导使用了未具体指定的“applicable order date”。学生创建订单时填入2025-05-22，而silver折扣规则从2025-09-10生效，后续定价接口因此返回零折扣，最终验收失败。订单头和订单行均已创建，不能将此案例描述为没有创建订单头。point_2已有订单日期2025-10-23，指导明确复用该日期，后续任务验收成功。实际请求、响应与工具返回见各external_structured目录。
