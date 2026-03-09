# Fix: SSP HTML Structure Changes (2026)

## Why

**問題現狀**:
TECO SSP 系統在 2026 年 Q1 進行網頁改版,導致現有爬蟲解析失效,應用程式無法正常使用。

### 具體變更

根據 temp.md 中記錄的新版 HTML 結構分析:

1. **登入頁面變更**
   - URL: `/index.aspx` → `/default.aspx`
   - 表單欄位名稱變更:
     - `ctl00$lblAccount` → `ctl00$txtAccount`
     - `ctl00$lblPassWord` → `ctl00$txtPassword`
     - `ctl00$Submit` → `ctl00$btnSubmit`

2. **個人加班記錄頁面變更** (FW21003Z.aspx)
   - 表格 ID 簡化: `ContentPlaceHolder1_gvFlow211` → `gvFlow211`
   - Span ID 結構改變:
     - **舊版**: 帶索引的唯一 ID (如 `ContentPlaceHolder1_gvFlow211_lblOT_Date_0`)
     - **新版**: 固定的重複 ID (如 `lblD_OT_Date`)
   - ID 對應表:
     - `lblOT_Date_{index}` → `lblD_OT_Date`
     - `lblOT_Describe_{index}` → `lblD_OT_Describe`
     - `lblOT_Minute_{index}` → `lblD_OT_Minute_E`
     - `lblChange_Minute_{index}` → `lblD_Change_Minute_E`
     - `lblOT_Manhour_{index}` → `lblD_OT_Manhour`
     - `lblOT_Monhour_{index}` → `lblD_OT_Manhour_T`
     - `lblProcess_Flag_Text_{index}` → `lblD_Flag`
   - Row class 不再使用 `RowStyle` / `AlternatingRowStyle_update`

3. **加班補報表單頁面變更** (FW21006Z.aspx?Kind=B)
   - URL: `/FW21001Z.aspx?Kind=B` → `/FW21006Z.aspx?Kind=B`
   - ID 前綴統一變更: `ContentPlaceHolder1` → `MainContent`
   - 表格 ID: `ContentPlaceHolder1_gvFlow211i` → `MainContent_gvFlow211i`
   - 增加行按鈕:
     - ID: `lbgvAddRowi` → `lbtnAddRowi`
     - PostBack: `ctl00$ContentPlaceHolder1$lbgvAddRowi` → `ctl00$MainContent$lbtnAddRowi`
   - 送出按鈕: `ctl00$ContentPlaceHolder1$btnCommit` → `ctl00$MainContent$btnCommit`
   - 欄位 name 前綴: `ctl00$ContentPlaceHolder1$gvFlow211i$ctl{N}$` → `ctl00$MainContent$gvFlow211i$ctl{N}$`

4. **出勤頁面結構變更** (FW99001Z.aspx) **[2026/03/06 新增]**
   - **打卡記錄改用日曆格式**:
     - **舊版**: 使用表格 `ContentPlaceHolder1_gvNotes005` 顯示打卡記錄
     - **新版**: 改用日曆 `gvCalendar` 顯示出勤資訊
   - 日曆結構:
     - 年月: 從 `MainContent_lblMonthYear` 提取 (如 "2026 年 3 月")
     - 日期: 從 `lblDate*` span 提取 (如 "2")
     - 打卡時間: 從 `lblWork_Time*` 的 `data-popup` 屬性提取 (如 "刷卡 08:55:13&lt;br/&gt;刷卡 19:32:55")
   - **出勤異常清單變更**:
     - 表格 ID 變更: `ContentPlaceHolder1_gvWeb012` → `gvWeb012` / `MainContent_gvWeb012`
     - Span ID 結構改變 (同樣從帶索引變固定):
       - **舊版**: 帶索引的唯一 ID (如 `lblWork_Date_0`, `lblCard_Time_0`)
       - **新版**: 固定的重複 ID (如 `lblAtt_Date`, `lblAtt_Time`)
     - ID 名稱變更:
       - `lblWork_Date_{index}` → `lblAtt_Date`
       - `lblCard_Time_{index}` → `lblAtt_Time`
       - `lblLose_Manhour_{index}` → `lblLose_Manhour`
       - (說明欄位) → `lblAtt_Result` (新增)
     - 按鈕 name 前綴: `ctl00$ContentPlaceHolder1$gvWeb012$...` → `ctl00$MainContent$gvWeb012$...`
   - **空白狀態處理**: 當無異常記錄時,顯示 `MainContent_lblgvWeb012Empty` 而不是空表格

**統一模式**: 所有頁面都從 `ContentPlaceHolder1` 改為 `MainContent`，所有表格內的 span ID 從帶索引改為固定重複 ID。打卡記錄改用日曆格式顯示。

**影響範圍**:

- 無法登入系統 ❌
- 個人記錄查詢失效 ❌
- 出勤異常清單解析失效 ❌
- **打卡記錄解析失效** ❌ **[2026/03/06 新增]**
- 加班補報功能失效 ❌

## What Changes

### 修正登入服務

- 更新 `AuthService.login()`:
  - 修改登入 URL 為 `/default.aspx`
  - 更新表單欄位名稱

### 修正個人記錄解析器

- 重構 `PersonalRecordParser.parse_records()`:
  - 更新表格 ID 查找邏輯
  - 改用固定 ID 查找 (不依賴索引)

### 修正出勤頁面解析器 **[2026/03/06 更新]**

- 更新 `AttendanceParser.parse_punch_records()` **[關鍵修正]**:
  - **新增日曆格式解析** (gvCalendar):
    - 從 `lblMonthYear` 提取年月
    - 遍歷所有日期單元格 (td)
    - 從 `lblDate*` 提取日期
    - 從 `lblWork_Time*` 的 `data-popup` 屬性提取打卡時間
    - 使用正則表達式解析 "刷卡 HH:MM:SS" 格式
  - 保持舊版表格格式相容性 (gvNotes005)
  - Fallback 機制: 優先嘗試日曆格式,失敗時降級到表格格式

- 更新 `AttendanceParser.parse_anomaly_records()`:
  - 表格 ID 支援多版本: `gvWeb012` / `MainContent_gvWeb012` / `ContentPlaceHolder1_gvWeb012`
  - 更新 Span ID 映射:
    - `lblWork_Date_{index}` → `lblAtt_Date`
    - `lblCard_Time_{index}` → `lblAtt_Time`
    - `lblLose_Manhour_{index}` → `lblLose_Manhour`
    - 說明欄位 → `lblAtt_Result`
  - 改用 `tbody > tr` 遍歷 (不依賴 row class)
  - 使用固定 ID 查找 (不依賴索引)
  - 保持舊版 ID 相容性 (fallback 查找)

### 修正加班補報服務

- 更新 `OvertimeReportService`:
  - 修改增加行 PostBack: `ContentPlaceHolder1$lbgvAddRowi` → `MainContent$lbtnAddRowi`
  - 修正送出按鈕名稱: `ContentPlaceHolder1$btnCommit` → `MainContent$btnCommit`
  - 更新表單欄位 name 前綴: `ContentPlaceHolder1` → `MainContent`

### 更新設定檔

- 更新 `src/config/settings.py`:
  - 修改 `OVERTIME_REPORT_URL = "/FW21006Z.aspx?Kind=B"`

### 驗證其他受影響服務

- 檢查 `AttendanceParser` 是否受影響 (出勤異常頁面)
- 更新相關單元測試

### 更新設定檔

- 如需要,更新 `settings.py` 中的 URL 設定
- 記錄網頁版本變更資訊

## Impact

### 受影響的 Specs

- **無**: 這是恢復既有功能的適配性修正,不改變功能規格

### 受影響的程式碼

- **認證層**:
  - `src/services/auth_service.py` - 修正登入 URL 與表單欄位
  - `tests/test_auth_service.py` - 更新測試案例

- **解析層**:
  - `src/parsers/personal_record_parser.py` - 重構解析邏輯
  - `src/parsers/attendance_parser.py` - 修正異常記錄解析
  - `tests/test_parsers.py` - 更新 fixture 與測試案例

- **表單服務層**:
  - `src/services/overtime_report_service.py` - 修正表單填寫邏輯
  - `tests/test_overtime_report_service.py` (若存在) - 更新測試

- **設定層**:
  - `src/config/settings.py` - 更新 `OVERTIME_REPORT_URL`

- **測試資料**:
  - `tests/fixtures/` - 更新 HTML fixtures (新版網頁結構)

### 向後相容性

- **BREAKING**: 無法與舊版 SSP 網頁相容 (已改版,無法回退)
- **Migration**: 無需遷移,直接修正即可使用

### 風險評估

- **低風險**: 僅修正解析邏輯,不改變業務流程
- **緩解措施**:
  - 保留舊版 HTML fixtures 供對比
  - 完整的單元測試覆蓋
  - 在實際環境充分驗證各項功能

### 測試策略

1. **單元測試** - 使用新版 HTML fixtures 驗證解析邏輯
2. **整合測試** - 實際登入 SSP 系統驗證完整流程:
   - 登入成功
   - 個人記錄查詢正常
   - 出勤異常清單正常
   - 加班補報功能正常 (若啟用)
3. **回歸測試** - 確保其他功能未受影響:
   - Excel 匯出
   - 統計計算
   - UI 顯示
