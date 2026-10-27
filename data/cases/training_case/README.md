# Training case

整理的数据包含Asset、Service、Menu三个训练steering案例，分别保存指导前记录、指导后候选、steering分析和prompt，以及补充的隔离环境执行结果。

| 案例 | 当前执行结果 |
|---|---|
| [Asset](asset_management_3/SUMMARY.md) | 两种参数均触发响应类型校验错误；未验证修正成功 |
| [Service](appointment_booking_3/SUMMARY.md) | 原接口不存在；修正调用成功创建服务，局部效果已观察到 |
| [Menu](b2b_saas_7/SUMMARY.md) | 两种查询都合法；修正查询取得菜单ID，不代表原动作非法 |

这些结果不等同于三个完整任务全部成功。当前记录不包含新生成的teacher分析、四路消融或完整模型续跑。执行环境使用隔离数据库，没有修改训练环境或原始记录。
