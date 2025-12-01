## 1. 資料模型建立

- [ ] 1.1 建立 `src/models/punch.py` - 定義 `PunchRecord`
- [ ] 1.2 建立 `src/models/leave.py` - 定義 `LeaveRecord`
- [ ] 1.3 建立 `src/models/quota.py` - 定義 `AttendanceQuota`
- [ ] 1.4 擴充 `src/models/attendance.py` - 定義 `UnifiedOvertimeRecord`
- [ ] 1.5 建立 `src/models/snapshot.py` - 定義 `AttendanceSnapshot` 和 `OvertimeStatistics`
- [ ] 1.6 更新 `src/models/__init__.py` - 匯出新模型

## 2. HTML 解析器重構

- [ ] 2.1 建立 `src/parsers/__init__.py`
- [ ] 2.2 建立 `src/parsers/attendance_parser.py` - 實作 `AttendanceParser`
  - [ ] 2.2.1 `parse_punch_table()` - 解析打卡記錄表 (gvNotes005)
  - [ ] 2.2.2 `parse_leave_table()` - 解析假別記錄表 (gvNotes011)
  - [ ] 2.2.3 `parse_quota()` - 解析剩餘額度 (dvNotes019)
  - [ ] 2.2.4 `parse_anomaly_table()` - 解析異常表 (gvWeb012)
- [ ] 2.3 建立 `src/parsers/personal_record_parser.py` - 實作 `PersonalRecordParser`
  - [ ] 2.3.1 `parse_table()` - 解析個人記錄表 (gvFlow211)
  - [ ] 2.3.2 重用 `PersonalRecordService._parse_hours()` 邏輯
- [ ] 2.4 撰寫解析器單元測試 `tests/test_parsers.py`

## 3. 資料同步服務實作

- [ ] 3.1 建立 `src/services/data_sync_service.py` - 實作 `DataSyncService`
  - [ ] 3.1.1 `__init__()` - 初始化 session、parsers、cache
  - [ ] 3.1.2 `sync_all()` - 全量同步所有資料
  - [ ] 3.1.3 `sync_overtime_status()` - 增量同步加班狀態
  - [ ] 3.1.4 `_fetch_attendance_page()` - 抓取出勤頁面
  - [ ] 3.1.5 `_fetch_anomaly_page()` - 抓取異常頁面
  - [ ] 3.1.6 `_fetch_personal_record_page()` - 抓取個人記錄頁面
  - [ ] 3.1.7 `_merge_overtime_data()` - 合併異常與個人記錄
  - [ ] 3.1.8 `_calculate_statistics()` - 計算統計資料
  - [ ] 3.1.9 `_is_cache_valid()` - 檢查快取有效性
- [ ] 3.2 實作適配器方法
  - [ ] 3.2.1 `get_attendance_records()` - 返回 `List[AttendanceRecord]`
  - [ ] 3.2.2 `get_submission_records()` - 返回 `List[OvertimeSubmissionRecord]`
  - [ ] 3.2.3 `get_personal_records()` - 返回 `(List[PersonalRecord], PersonalRecordSummary)`
- [ ] 3.3 撰寫服務單元測試 `tests/test_data_sync_service.py`
  - [ ] 3.3.1 測試全量同步
  - [ ] 3.3.2 測試增量同步
  - [ ] 3.3.3 測試快取機制
  - [ ] 3.3.4 測試資料合併邏輯
  - [ ] 3.3.5 測試適配器方法

## 4. 設定檔更新

- [ ] 4.1 在 `src/config/settings.py` 新增 `CACHE_DURATION_SECONDS = 300`
- [ ] 4.2 確保所有 URL 設定正確 (FW99001Z.aspx, FW21003Z.aspx)

## 5. UI 層整合

- [ ] 5.1 更新 `ui/main_window.py`
  - [ ] 5.1.1 初始化 `DataSyncService` 取代舊服務
  - [ ] 5.1.2 `_fetch_data_task()` 改用 `data_sync_service.sync_all()`
  - [ ] 5.1.3 `on_refresh()` 使用快取優先策略
  - [ ] 5.1.4 `on_refresh_personal_records()` 改用 `sync_overtime_status()`
- [ ] 5.2 更新 `ui/components/attendance_tab.py`
  - [ ] 5.2.1 從 `AttendanceSnapshot` 讀取資料
- [ ] 5.3 更新 `ui/components/overtime_report_tab.py`
  - [ ] 5.3.1 使用適配器方法 `get_submission_records()`
- [ ] 5.4 更新 `ui/components/personal_record_tab.py`
  - [ ] 5.4.1 使用適配器方法 `get_personal_records()`

## 6. 整合測試

- [ ] 6.1 手動測試完整流程
  - [ ] 6.1.1 登入並載入資料
  - [ ] 6.1.2 驗證三個分頁資料正確
  - [ ] 6.1.3 測試重新整理功能 (應使用快取)
  - [ ] 6.1.4 測試強制重新整理 (應重新抓取)
- [ ] 6.2 效能測試
  - [ ] 6.2.1 測量首次載入時間 (目標 < 3 秒)
  - [ ] 6.2.2 測量快取重新整理時間 (目標 < 0.5 秒)
  - [ ] 6.2.3 測量強制重新整理時間 (目標 < 2 秒)
- [ ] 6.3 執行完整測試套件 `pytest --cov=src --cov-report=html`
  - [ ] 6.3.1 確保覆蓋率 > 70%
  - [ ] 6.3.2 所有測試通過

## 7. 舊服務清理

- [ ] 7.1 標記 `OvertimeStatusService` 為 `@deprecated`
- [ ] 7.2 標記 `PersonalRecordService` 為 `@deprecated`
- [ ] 7.3 更新 `src/services/__init__.py`
  - [ ] 7.3.1 匯出 `DataSyncService`
  - [ ] 7.3.2 移除 `OvertimeStatusService` (或保留標記 deprecated)
  - [ ] 7.3.3 移除 `PersonalRecordService` (或保留標記 deprecated)
- [ ] 7.4 重構 `DataService` (選擇性 - 可保留用於其他用途或標記 deprecated)

## 8. 文件更新

- [ ] 8.1 更新 `openspec/project.md`
  - [ ] 8.1.1 更新架構圖
  - [ ] 8.1.2 更新服務層說明
  - [ ] 8.1.3 新增資料同步機制說明
- [ ] 8.2 更新 `readme.md`
  - [ ] 8.2.1 更新技術架構說明
  - [ ] 8.2.2 新增快取機制說明
- [ ] 8.3 建立 `docs/development/DATA_SYNC_MECHANISM.md`
  - [ ] 8.3.1 說明資料模型設計
  - [ ] 8.3.2 說明同步流程
  - [ ] 8.3.3 說明快取策略
  - [ ] 8.3.4 提供開發指南與最佳實踐

## 9. 驗證與發布準備

- [ ] 9.1 執行所有單元測試 `pytest`
- [ ] 9.2 執行整合測試 (手動)
- [ ] 9.3 檢查程式碼品質 (無 linter 警告)
- [ ] 9.4 更新版本號至 `1.3.0` (MINOR 版本 - 新功能)
- [ ] 9.5 更新 `CHANGELOG.md` 或建立 Release Notes
- [ ] 9.6 打包執行檔 `pyinstaller overtime_calculator.spec --clean`
- [ ] 9.7 測試打包後的執行檔

## 依賴關係

**必須按順序完成**:
1 → 2 → 3 → 4 → 5 → 6 → 7 → 8 → 9

**可平行執行**:

- 2.2 和 2.3 可平行
- 5.2, 5.3, 5.4 可平行 (在 5.1 完成後)

## 估計時間

- 資料模型與解析器: 2-3 天
- 資料同步服務: 2-3 天
- UI 整合與測試: 1-2 天
- 清理與文件: 1 天

**總計**: 6-9 天 (約 1.5-2 週)

## 驗證標準

每個階段完成後需確認:

- [ ] 所有相關單元測試通過
- [ ] 無新增 linter 警告或錯誤
- [ ] 文件已更新
- [ ] 手動測試相關功能正常運作

**最終驗證清單**:

- [ ] 所有測試通過 (pytest 100%)
- [ ] 覆蓋率 > 70%
- [ ] 效能符合預期 (載入 < 3s, 快取 < 0.5s)
- [ ] UI 所有功能正常
- [ ] 打包執行檔可執行
- [ ] 文件完整更新
