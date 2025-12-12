# Refactor: Unified Data Model

## Why

**問題現狀**:
目前系統從多個 SSP 頁面分別抓取資料,存在以下問題:

1. **重複抓取**: 相同資料從不同頁面重複取得

   - 個人記錄查詢 (FW21003Z.aspx) - 抓取已申請的加班記錄
   - 加班狀態查詢 (FW21003Z.aspx) - 同一頁面,重複請求
   - 出勤異常清單 (FW99001Z.aspx) - 取得出勤記錄與加班時數

2. **資料耦合**: 多個資料模型描述相同概念

   - `AttendanceRecord` - 出勤記錄 (僅包含日期、時間)
   - `OvertimeSubmissionRecord` - 補報記錄 (包含日期、時數、內容)
   - `SubmittedRecord` - 已申請記錄 (包含日期、狀態、時數)
   - `PersonalRecord` - 個人記錄 (包含日期、內容、狀態、累計)

3. **效能問題**: 每個功能分別請求,增加網路開銷與等待時間

   - 登入後需要 3-4 次 HTTP 請求
   - 重新整理時重複所有請求

4. **資料不一致**: 不同來源的相同資料可能不同步
   - 加班時數可能在不同服務中計算不一致
   - 狀態資訊可能過時

**改進目標**:
建立統一的資料模型與同步機制,減少重複抓取,提升效能與資料一致性。

## What Changes

### 新增統一資料模型

- 建立 `UnifiedOvertimeRecord` 整合所有加班相關資訊
- 建立 `AttendanceQuota` 表示剩餘額度 (特休、調修)
- 建立 `LeaveRecord` 表示假別記錄
- 建立 `PunchRecord` 表示打卡記錄

### 新增資料同步服務

- 建立 `DataSyncService` 統一管理所有資料抓取
- 實作智慧快取機制 (避免重複請求)
- 提供資料更新策略 (全量/增量)

### 重構現有服務

- **BREAKING**: `DataService` 重構為僅處理 HTML 解析
- **BREAKING**: `OvertimeStatusService` 併入 `DataSyncService`
- **BREAKING**: `PersonalRecordService` 併入 `DataSyncService`
- 保留 `AuthService`、`ExportService`、`OvertimeReportService` 不變

### 更新 UI 層

- `MainWindow` 改為使用 `DataSyncService`
- 各分頁改為從統一資料模型讀取
- 新增「重新整理」按鈕觸發增量更新

## Impact

### 受影響的 Specs

- **新增**: `data-synchronization` (統一資料同步機制)

### 受影響的程式碼

- **核心服務層**:

  - `src/services/data_service.py` - 重構為解析器
  - `src/services/overtime_status_service.py` - 移除 (併入 DataSyncService)
  - `src/services/personal_record_service.py` - 移除 (併入 DataSyncService)
  - `src/services/data_sync_service.py` - **新增**

- **資料模型層**:

  - `src/models/attendance.py` - 擴充為統一模型
  - `src/models/quota.py` - **新增** (剩餘額度)
  - `src/models/leave.py` - **新增** (假別記錄)
  - `src/models/punch.py` - **新增** (打卡記錄)

- **UI 層**:

  - `ui/main_window.py` - 更新資料獲取邏輯
  - `ui/components/attendance_tab.py` - 從統一模型讀取
  - `ui/components/overtime_report_tab.py` - 從統一模型讀取
  - `ui/components/personal_record_tab.py` - 從統一模型讀取

- **測試**:
  - `tests/test_data_sync_service.py` - **新增**
  - `tests/test_models.py` - 更新以涵蓋新模型

### 向後相容性

- **BREAKING**: 移除 `OvertimeStatusService` 和 `PersonalRecordService`
- **BREAKING**: 修改 `DataService` 介面
- 保留現有資料模型以支援漸進式遷移
- 提供遷移腳本與文件

### 效能改進預期

- 減少 HTTP 請求數量: 3-4 次 → 2 次
- 首次載入時間: ~5 秒 → ~2 秒
- 重新整理時間: ~3 秒 → ~0.5 秒 (快取命中)

### 風險評估

- **中等風險**: 大規模重構,需仔細測試
- **緩解措施**:
  - 分階段實作 (先新增,後移除)
  - 完整的單元測試覆蓋
  - 在測試環境充分驗證
  - 保留舊服務作為備份 (標記 deprecated)
