# overtime-report-submission Spec Delta

## MODIFIED Requirements

### Requirement: 加班補報表單自動填寫

系統 SHALL 能夠根據計算好的加班時數,自動填寫 TECO SSP 系統的「加班補報申請單」表單,減少手動操作並避免錯誤。

**表單結構變更 (2026 Q1)**:

- URL: `/FW21001Z.aspx?Kind=B` → `/FW21006Z.aspx?Kind=B`
- ID 前綴: `ContentPlaceHolder1` → `MainContent`
- 表格 ID: `ContentPlaceHolder1_gvFlow211i` → `MainContent_gvFlow211i`
- 增加行按鈕:
  - ID: `lbgvAddRowi` → `lbtnAddRowi`
  - PostBack: `ctl00$ContentPlaceHolder1$lbgvAddRowi` → `ctl00$MainContent$lbtnAddRowi`
- 送出按鈕: `ctl00$ContentPlaceHolder1$btnCommit` → `ctl00$MainContent$btnCommit`
- 欄位 name 格式: `ctl00$MainContent$gvFlow211i$ctl{N}$txtOT_Datei`

#### Scenario: 填寫單筆加班記錄

- **WHEN** 使用者勾選一筆加班記錄並點擊「預覽填寫」
- **THEN** 系統應該:
  - 登入 SSP 系統 `/FW21006Z.aspx?Kind=B` 頁面 (新版 URL)
  - 提取 ViewState 等必要欄位
  - 使用新版欄位名稱填寫:
    - `ctl00$MainContent$gvFlow211i$ctl02$txtOT_Datei` (加班日期)
    - `ctl00$MainContent$gvFlow211i$ctl02$txtOT_Describei` (加班內容)
    - `ctl00$MainContent$gvFlow211i$ctl02$txtOT_Minutei` (加班時數) 或
    - `ctl00$MainContent$gvFlow211i$ctl02$txtChange_Minutei` (調休時數)
  - 返回填寫結果預覽,不實際送出

#### Scenario: 填寫多筆加班記錄

- **WHEN** 使用者勾選 5 筆加班記錄並點擊「預覽填寫」
- **THEN** 系統應該:
  - 使用「增加列」功能 PostBack: `ctl00$MainContent$lbtnAddRowi` (新版按鈕ID)
  - 新增 4 列 (預設已有 1 列)
  - 逐筆填寫所有欄位 (使用 ctl02, ctl03, ctl04...)
  - 正確處理 ViewState 更新
  - 返回所有記錄的填寫預覽

#### Scenario: 送出加班申請 (正式版本)

- **WHEN** 使用者確認填寫內容無誤,點擊「送出申請」
- **THEN** 系統應該:
  - 顯示確認對話框,列出即將送出的記錄
  - 使用者確認後執行表單送出: `ctl00$MainContent$btnCommit` = "送出"
  - 檢查送出結果
  - 顯示成功訊息或錯誤說明

#### Scenario: 預覽模式保護 (Beta 版本)

- **WHEN** 使用者在 Beta 版本點擊「送出申請」
- **THEN** 系統應該:
  - 顯示警告訊息:「此功能尚在測試階段,無法實際送出」
  - 只執行預覽填寫
  - 不執行 btnCommit PostBack

---

## MODIFIED Requirements

### Requirement: 已申請記錄狀態查詢

系統 SHALL 能夠查詢使用者在 SSP 系統中已申請的加班記錄,避免重複申請並顯示申請狀態。

**HTML 結構變更 (2026 Q1)**:

- 表格 ID: `ContentPlaceHolder1_gvFlow211` → `gvFlow211`
- Span ID 改用固定名稱 (不帶索引):
  - 日期: `lblOT_Date_{N}` → `lblD_OT_Date`
  - 狀態: `lblProcess_Flag_Text_{N}` → `lblD_Flag`
  - 內容: `lblOT_Describe_{N}` → `lblD_OT_Describe`
  - 加班時數: `lblOT_Minute_{N}` → `lblD_OT_Minute_E`
  - 調休時數: `lblChange_Minute_{N}` → `lblD_Change_Minute_E`
  - 當月累計: `lblOT_Manhour_{N}` → `lblD_OT_Manhour`
  - 當季累計: `lblOT_Monhour_{N}` → `lblD_OT_Manhour_T`
- Row 遍歷: 不再依賴 `RowStyle` / `AlternatingRowStyle_update` class,改用 `tbody > tr`

#### Scenario: 查詢當月已申請記錄

- **WHEN** 使用者登入並進入「加班補報」分頁
- **THEN** 系統應該:
  - 自動訪問 FW21003Z.aspx (個人紀錄查詢)
  - 解析 `gvFlow211` 表格 (新版結構)
  - 使用固定 span ID 提取每筆記錄資料 (透過 `tbody > tr` 遍歷)
  - 返回已申請記錄字典: {日期: 狀態}

#### Scenario: 處理多頁已申請記錄

- **WHEN** 已申請記錄超過一頁 (>10 筆)
- **THEN** 系統應該:
  - 解析分頁資訊 (FlowPagerStyle 表格)
  - 使用 `__doPostBack('ctl00$MainContent$gvFlow211','Page$N')` 抓取所有頁面 (注意: EventTarget 也從 `ContentPlaceHolder1` 改為 `MainContent`)
  - 合併所有頁面的記錄
  - 返回完整的已申請記錄列表

#### Scenario: 顯示已申請記錄狀態

- **WHEN** 某日期 (如 2025/11/21) 已申請且狀態為「簽核完成」
- **THEN** 系統應該:
  - 在記錄列表中顯示狀態標籤:「已申請 (簽核完成)」
  - 禁用該記錄的勾選框
  - 變更記錄顏色為灰色或其他區別色
  - 不允許重複送出

---

## MODIFIED Requirements

### Requirement: SSP 系統認證

系統 SHALL 能夠透過 ASP.NET Forms Authentication 登入 TECO SSP 系統。

**登入端點變更 (2026 Q1)**:

- URL: `/index.aspx` → `/default.aspx`
- 表單欄位名稱:
  - `ctl00$lblAccount` → `ctl00$txtAccount`
  - `ctl00$lblPassWord` → `ctl00$txtPassword`
  - `ctl00$Submit` → `ctl00$btnSubmit`

#### Scenario: 成功登入

- **WHEN** 使用者輸入有效的帳號密碼
- **THEN** 系統應該:
  - POST 到 `/default.aspx` (新版 URL)
  - 包含正確的表單欄位: `txtAccount`, `txtPassword`, `btnSubmit`
  - 提取並保留 ViewState、ViewStateGenerator、EventValidation
  - 登入成功後跳轉至 FW99001Z.aspx 或回應包含「登出」文字
  - 返回已登入的 Session 供後續請求使用

#### Scenario: 登入失敗

- **WHEN** 使用者輸入錯誤的帳號或密碼
- **THEN** 系統應該:
  - 顯示錯誤訊息:「登入失敗,請檢查帳號密碼」
  - 不儲存錯誤的憑證
  - 允許重試

#### Scenario: 網路逾時

- **WHEN** 連線 SSP 系統超過 30 秒未回應
- **THEN** 系統應該:
  - 顯示錯誤訊息:「連線逾時,請檢查網路連線」
  - 記錄錯誤日誌
  - 允許重試
