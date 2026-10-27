# Training steering cases

Asset、Service、Menu三个任务的整理数据：指导前轨迹、保存的steering分析和prompt、指导后候选动作，以及同一前置状态上的无指导/有指导完整续跑。

- [Asset](asset_management_3/SUMMARY.md)
- [Service](appointment_booking_3/SUMMARY.md)
- [Menu](b2b_saas_7/SUMMARY.md)

最终任务验收见[continuation_results.json](continuation_results.json)。各案例continuation文件夹保存请求、响应、工具执行、初始与最终数据库及代码verifier结果。局部调用成功与整个任务成功分别记录；原有的动作差异不会自动被视为因果错误。
