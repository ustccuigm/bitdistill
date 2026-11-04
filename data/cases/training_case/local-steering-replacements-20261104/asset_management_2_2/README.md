# 借出了相机，却漏记借出地点

Check out the asset with asset tag 'CAM-NYC-0007' (category 'DSLR Camera') from the location 'NYC Office > Media Closet' to user 'jane.smith@company.com' for the project 'Q3 Brand Shoot', setting the due date to 2025-08-15 and adding a note that the camera must be returned with both batteries and SD card.

这条案例展示地点字段遗漏的修正：接口成功不代表记录完整，关键是检查本次新记录中是否真正保存了指定地点。

- before/: 无指导响应、轨迹与新记录验收。
- steering/attempt-0/: 实际 teacher 请求、响应与完整 steering prompt。
- after/attempt-0/: 修正响应、局部状态快照和撤掉指导后的续跑。
- tools.json、pre_state.db: 工具定义与共同干预前状态。
- independent_review.json: 将新记录地点改回空值后，验收重新失败。
