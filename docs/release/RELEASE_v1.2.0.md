# GitHub Release v1.2.0

## Release Title
```
v1.2.0 - 加班補報自動填寫 + 範本管理
```

## Release Notes

### ⚙️ 重大功能更新：加班補報自動化

此版本新增**加班補報自動填寫**功能,可自動將出勤異常記錄填寫至 SSP 系統的加班補報申請單,並支援**範本管理**功能,大幅提升作業效率。

---

## ✨ 主要新功能

### 1. 🧩 加班範本管理 (v1.2.0 正式版)

**快速填寫常用加班內容**,提升申請效率。

#### 核心功能
- **範本下拉選單**: 「套用範本」快速選擇常用描述
- **範本管理對話框**: 「✎ 管理範本」可新增/刪除/編輯範本
- **永久儲存**: 範本設定寫入 `cache/overtime_templates.json`,重啟後保留
- **預設範本**: 內建「加班作業」、「專案開發」、「系統維護」等常用項目
- **即時同步**: 管理對話框的變更立即反映至下拉選單

#### 使用方式
1. 在加班補報分頁,點擊「套用範本」下拉選單
2. 選擇常用描述,自動填入「加班內容」欄位
3. 點擊「✎ 管理範本」開啟管理對話框
4. 新增: 輸入新範本名稱 → 點擊「新增範本」
5. 刪除: 選擇範本 → 點擊「刪除選中」

---

### 2. ⚙️ 加班補報自動填寫

自動將出勤異常記錄填寫至 SSP 加班補報申請單。

#### 核心功能
- **智慧記錄載入**: 自動載入有加班時數的記錄
- **勾選機制**: 自由選擇要送出的記錄
- **已申請狀態**: 自動查詢並標記已申請/審核中的記錄
- **可編輯欄位**: 
  - 加班時數 (小時制,精確到 0.01 小時)
  - 加班內容 (必填欄位,可使用範本)
  - 加班/調休選擇
- **表單預覽**: 送出前預覽要填寫的內容
- **一鍵送出**: 批次送出所有勾選記錄 (v1.2.0 正式版已啟用)

#### 技術實現
```python
# 服務層
OvertimeStatusService     # 查詢已申請記錄
OvertimeReportService     # 填寫並送出表單

# 資料模型
OvertimeSubmissionRecord  # 補報記錄 (UI 用)
SubmittedRecord          # 已申請記錄 (查詢結果)
OvertimeSubmissionStatus # 狀態列舉

# UI 元件
OvertimeReportTab        # 加班補報分頁
```

#### ASP.NET 表單處理
本功能正確處理 ASP.NET WebForms 的複雜機制:
- ✅ **ViewState 保持**: 每次 PostBack 都保留狀態
- ✅ **動態新增列**: 使用 `__doPostBack('lbgvAddRowi', '')` 
- ✅ **欄位命名**: `txtOT_Datei`, `txtOT_Describei` (i = 索引從 3 開始)
- ✅ **分鐘轉換**: 自動將小時轉換為分鐘數
- ✅ **送出按鈕**: `btnbInsert` 觸發表單提交

---

### 3. 📋 已申請狀態查詢

自動查詢 SSP 系統中已申請的加班記錄。

#### 功能特點
- **多頁查詢**: 自動抓取所有分頁資料 (最多 10 頁)
- **狀態解析**: 解析「簽核中」、「簽核完成」等狀態
- **智慧標記**: 已申請的記錄自動禁用勾選框
- **即時更新**: 點擊「重新整理」可重新查詢

#### 查詢來源
- 頁面: `FW21003Z.aspx`
- 表格: `ContentPlaceHolder1_gvFlow211`
- 分頁: `FlowPagerStyle` 自動解析頁數

---

### 4. 🎯 三分頁介面設計

主視窗重構為分頁模式,提供更清晰的功能區分。

#### 分頁配置
```
主視窗
├── 導覽列 (Logo + 使用者 + 登出)
├── 統計卡片區域 (全域顯示)
│   ├── 📅 總筆數
│   ├── ⏱️ 總加班時數
│   ├── 📊 平均加班時數
│   └── 🔥 最高加班時數
└── 分頁介面
    ├── ⚙️ 加班補報
    │   ├── 範本工具 (套用範本、✎ 管理範本)
    │   ├── 操作按鈕區 (預覽、送出、重新整理)
    │   └── 記錄列表 (勾選框、日期、時數、內容、類型、狀態)
    ├── 📅 異常清單 (預設分頁)
        ├── 操作按鈕區 (複製、匯出)
        └── 出勤表格 (可排序、可複製)
    └── 📊 個人記錄
        └── 已申請記錄 (日期、內容、狀態、時數、累計)
```

#### UI 優化
- ✅ 統計卡片提升至主視窗層級,所有分頁共享
- ✅ 預設分頁改為「📅 異常清單」,符合主要使用情境
- ✅ 移除冗餘的狀態訊息區,改用對話框
- ✅ 載入狀態提示: "⏳ 正在載入..."
- ✅ 空狀態提示: "📝 目前沒有待補報的加班記錄"
- ✅ 小時制顯示: 改用小時 (float, .2f 格式) 取代分鐘數
- ✅ 可編輯時數: 加班時數欄位支援手動編輯 (精確到 0.01 小時)
- ✅ 必填欄位: 加班內容為必填項目,確保記錄完整性

---

## 🔧 技術改進

### 新增服務層 (Services)

#### `TemplateManager`
```python
class TemplateManager:
    def load_templates() -> List[str]
    def save_templates(templates: List[str]) -> None
    def add_template(template: str) -> bool
    def remove_template(template: str) -> bool
```

**職責**: 管理加班內容範本  
**特點**: JSON 檔案持久化、執行緒安全、錯誤處理

#### `OvertimeStatusService`
```python
class OvertimeStatusService:
    def fetch_submitted_records(session) -> Dict[str, SubmittedRecord]
    def _parse_status_table(html) -> List[SubmittedRecord]
    def _fetch_status_page(session, page_num) -> BeautifulSoup
    def _get_total_pages(soup) -> int
```

**職責**: 查詢已申請的加班記錄  
**特點**: 支援分頁、自動解析狀態文字、錯誤處理

#### `OvertimeReportService`
```python
class OvertimeReportService:
    def preview_form(session, records) -> Dict[str, Any]
    def submit_form(session, records) -> Dict[str, Any]
    def _add_form_rows(session, count) -> BeautifulSoup
    def _build_form_data(soup, records) -> Dict[str, str]
```

**職責**: 填寫並送出加班補報表單  
**特點**: ViewState 管理、動態新增列、表單驗證

#### `PersonalRecordService`
```python
class PersonalRecordService:
    def fetch_personal_records(session) -> List[PersonalRecord]
    def _parse_table_rows(html) -> List[PersonalRecord]
    def _fetch_page(session, page_num) -> BeautifulSoup
```

**職責**: 查詢個人加班補報記錄  
**特點**: 支援分頁、狀態解析、累計時數計算

---

### 新增資料模型 (Models)

#### `OvertimeSubmissionRecord`
```python
@dataclass
class OvertimeSubmissionRecord:
    date: str                       # 加班日期
    description: str                # 加班內容 (可編輯)
    overtime_hours: float           # 加班時數
    is_overtime: bool = True        # True=加班, False=調休
    is_selected: bool = True        # 是否勾選
    submitted_status: Optional[str] = None  # 已申請狀態
    
    @property
    def is_submitted(self) -> bool
    @property
    def overtime_minutes(self) -> int
    @property
    def change_minutes(self) -> int
```

#### `PersonalRecord`
```python
@dataclass
class PersonalRecord:
    date: str                    # 申請日期
    content: str                 # 加班內容
    status: str                  # 申請狀態
    overtime_hours: float        # 加班時數 (小時)
    monthly_total_hours: float   # 本月累計時數
    quarterly_total_hours: float # 本季累計時數
    is_overtime: bool            # True=加班, False=調休
```

#### `SubmittedRecord`
```python
@dataclass
class SubmittedRecord:
    date: str                  # 加班日期
    status: str                # 狀態文字
    overtime_minutes: float    # 加班分鐘數
    change_minutes: float      # 調休分鐘數
    
    @property
    def is_overtime(self) -> bool
```

#### `OvertimeSubmissionStatus` (Enum)
```python
class OvertimeSubmissionStatus(Enum):
    NOT_SUBMITTED = "未申請"
    SUBMITTED = "已申請"
    IN_REVIEW = "簽核中"
    APPROVED = "簽核完成"
    REJECTED = "已撤回"
```

---

### 新增 UI 元件 (Components)

#### `OvertimeReportTab`
加班補報分頁,提供記錄勾選、編輯、範本管理、預覽、送出功能。

**主要功能**:
- `load_data(session, submission_records, submitted_records)`: 載入資料
- `on_template_selected(template)`: 套用範本
- `on_manage_templates()`: 開啟範本管理對話框
- `on_preview()`: 預覽表單
- `on_submit()`: 送出申請
- `on_refresh()`: 重新整理狀態
- `_create_record_item(record)`: 建立記錄卡片

**UI 結構**:
```
OvertimeReportTab
├── Header (範本工具: 套用範本 | ✎ 管理範本)
├── Actions (操作按鈕: 預覽 | 送出 | 重新整理)
├── Loading Container (載入提示)
└── Records Container (CTkScrollableFrame)
    └── Record Cards (勾選框 + 日期 + 時數 + 內容 + 類型 + 狀態)
```

#### `PersonalRecordTab`
個人記錄分頁,顯示已申請的加班補報記錄。

**主要功能**:
- `load_data(session, personal_records)`: 載入個人記錄
- `_create_record_card(record)`: 建立記錄卡片
- `_create_statistics_summary(records)`: 建立統計摘要

#### `AttendanceTab`
出勤異常清單分頁,重構自原 `ReportFrame`。

**主要功能**:
- `display_report(report)`: 顯示報表
- `copy_total_hours()`: 複製總時數
- `on_export()`: 匯出 Excel

---

### 配置更新 (Config)

`src/config/settings.py`:
```python
@dataclass
class Settings:
    # 新增 URL
    OVERTIME_REPORT_URL: str = "/FW21001Z.aspx?Kind=B"     # 加班補報申請單
    OVERTIME_STATUS_URL: str = "/FW21003Z.aspx"            # 已申請狀態查詢
    PERSONAL_RECORD_URL: str = "/FW21003Z.aspx"            # 個人記錄查詢
    
    # 移除預設值 (改為必填)
    # DEFAULT_OVERTIME_DESCRIPTION 已移除
```

`cache/overtime_templates.json`:
```json
{
  "templates": [
    "加班作業",
    "專案開發",
    "系統維護",
    "緊急支援",
    "測試驗證"
  ]
}
```

---

## ✅ 測試覆蓋

### 新增測試檔案
- `tests/test_overtime_submission.py`: 11 個測試
- `tests/test_personal_record.py`: 19 個測試
- `tests/test_template_manager.py`: 8 個測試
- `tests/test_overtime_report_tab.py`: 擴充範本功能測試

### 測試內容
1. **加班補報模型**:
   - OvertimeSubmissionStatus 列舉
   - OvertimeSubmissionRecord 資料轉換
   - SubmittedRecord 狀態判斷
   - OvertimeReport 轉換邏輯
   
2. **個人記錄模型**:
   - PersonalRecord 建立與屬性
   - PersonalRecordSummary 統計計算
   - 空記錄處理
   - 邊界值測試

3. **範本管理**:
   - 載入/儲存範本
   - 新增/刪除範本
   - 檔案不存在處理
   - 無效資料處理

4. **UI 整合**:
   - 範本選單同步
   - 範本套用流程
   - 管理對話框互動

### 測試結果
```bash
pytest
================= 75 passed =================
```

---

## 📦 檔案變更

### 新增檔案
- `src/services/template_manager.py` - 範本管理服務
- `src/services/overtime_status_service.py` - 已申請狀態查詢
- `src/services/overtime_report_service.py` - 加班補報填寫服務
- `src/services/personal_record_service.py` - 個人記錄查詢服務
- `src/models/overtime_submission.py` - 加班補報資料模型
- `src/models/personal_record.py` - 個人記錄資料模型
- `ui/components/overtime_report_tab.py` - 加班補報分頁
- `ui/components/personal_record_tab.py` - 個人記錄分頁
- `cache/overtime_templates.json` - 範本設定檔

### 修改檔案
- `src/core/version.py` - 版本號更新至 1.2.0
- `ui/main_window.py` - 重構為三分頁模式
- `ui/components/attendance_tab.py` - 重構自 ReportFrame
- `src/config/settings.py` - 新增 URL 與設定
- `readme.md` - 更新使用說明

### 相依套件
無新增相依套件,與 v1.1.1 相同。

---

## 🚀 安裝與使用

### 下載
從本頁面的 **Assets** 區下載 `overtime-assistant-1.2.0.exe`

### 系統需求
- **作業系統**: Windows 10/11 (64-bit)
- **記憶體**: 建議 4GB 以上
- **硬碟空間**: 約 100MB

### 使用方式
1. 下載 `overtime-assistant-1.2.0.exe`
2. 直接執行 (無需安裝)
3. 登入後即可使用加班補報功能

---

## 🚨 重要提醒

### 送出功能已啟用
v1.2.0 正式版**已啟用**送出功能:

```python
# src/services/overtime_report_service.py
ENABLE_SUBMISSION = True  # 正式版啟用送出功能
```

### 使用建議
1. **首次使用先預覽**,確認填寫內容正確
2. **檢查預覽結果**:
   - 日期格式 (YYYY/MM/DD)
   - 加班內容 (必填)
   - 加班/調休選擇
   - 時數 (小時 → 自動轉換為分鐘)
3. **確認無誤後送出**
4. **善用範本功能**,提升填寫效率

---

## 📋 使用指南

### 快速開始

#### 1. 登入系統
執行程式 → 輸入 SSP 帳號密碼 → 點擊「登入」

#### 2. 查看異常清單
預設顯示「📅 異常清單」分頁,查看出勤異常和加班時數

#### 3. 使用加班補報
點擊「⚙️ 加班補報」分頁:
- ✅ 綠色勾選: 將會送出的記錄
- ⚠️ 灰色禁用: 已申請/審核中的記錄
- ✏️ 可編輯欄位: 時數、內容、類型

#### 4. 使用範本功能
1. 點擊「套用範本」下拉選單
2. 選擇常用描述 (如「專案開發」)
3. 內容自動填入加班內容欄位
4. 點擊「✎ 管理範本」可自訂範本

#### 5. 預覽與送出
1. 點擊「預覽表單」檢查內容
2. 確認無誤後點擊「送出申請」
3. 點擊「重新整理」更新狀態

#### 6. 查看個人記錄
點擊「📊 個人記錄」分頁,查看已申請的記錄與統計

---

### 進階功能

#### 範本管理
1. 點擊「✎ 管理範本」開啟對話框
2. **新增範本**: 輸入名稱 → 點擊「新增範本」
3. **刪除範本**: 選擇範本 → 點擊「刪除選中」
4. 設定自動儲存至 `cache/overtime_templates.json`

#### 手動編輯時數
1. 點擊加班時數欄位
2. 輸入小時數 (例如: 1.5, 2.75)
3. 系統自動轉換為分鐘數送出

#### 切換加班/調休
1. 點擊記錄卡片中的下拉選單
2. 選擇「加班」或「調休」
3. 送出時填寫對應欄位

---

## 🔄 升級指南

### 從 v1.1.x 升級

#### 升級步驟
1. ✅ 下載 `overtime-assistant-1.2.0.exe`
2. ✅ 直接執行新版本 (無需解除安裝舊版)
3. ✅ 登入後即可使用新功能

#### 資料相容性
- ✅ **完全向下相容**: 無需遷移資料
- ✅ **設定檔相容**: 所有設定保持不變
- ✅ **憑證相容**: 記住我功能正常運作
- ✅ **新增範本檔**: 首次執行自動建立 `cache/overtime_templates.json`

#### 新功能檢查清單
- [ ] 測試加班補報分頁
- [ ] 嘗試範本管理功能
- [ ] 預覽表單內容
- [ ] 送出一筆測試記錄
- [ ] 查看個人記錄分頁

---

## 📊 版本比較

| 版本 | 加班補報 | 範本管理 | 個人記錄 | UI 設計 | 說明 |
|------|---------|---------|---------|---------|------|
| v1.0.x | ❌ | ❌ | ❌ | 基礎 UI | 早期版本 |
| v1.1.x | ❌ | ❌ | ❌ | ✅ 專業設計 | UI/UX 改版 |
| v1.2.0 | ✅ | ✅ | ✅ | ✅ 三分頁 | **功能大更新** ⭐ |

---

## 💬 支援

- 🐛 **回報問題**: [GitHub Issues](https://github.com/jony-zhou/overtime-assistant/issues)
- 💡 **功能建議**: [GitHub Discussions](https://github.com/jony-zhou/overtime-assistant/discussions)
- 📖 **完整文件**: [README](https://github.com/jony-zhou/overtime-assistant/blob/main/readme.md)

---

## 📅 發布資訊

- **版本號**: v1.2.0
- **發布日期**: 2025-12-01
- **變更類型**: Minor Version (次版本)
- **相容性**: Windows 10/11 (64-bit)
- **檔案大小**: 約 50-100 MB
- **重要性**: 強烈建議升級 (重大功能更新)

---

## 🔖 完整更新歷史

### v1.2.0 (2025/12/01) - 當前版本
- ⚙️ 加班補報自動填寫功能
- 🧩 加班範本管理功能
- 📊 個人記錄查詢分頁
- ⏰ 小時制時數編輯
- 🎯 三分頁介面設計

### v1.1.1 (2025/01/21)
- 🎨 圖示解析度提升至 128x128

### v1.1.0 (2025/01/21)
- 🎨 專業 UI/UX 大改版
- 🔐 安全記住我功能
- 📊 統計儀表板

### v1.0.2 (2025/11/21)
- 🐛 修復版本檢查功能

### v1.0.1 (2025/11/21)
- 🔧 修正打包檔名

### v1.0.0 (2025/11/21)
- 🎉 首個正式版

---

**⚙️ 大幅提升效率!加班補報從此自動化!** ✨

---

### 備註

這是一個重大功能更新版本,強烈建議所有使用者升級。新增的加班補報自動填寫功能可大幅節省人工操作時間,範本管理功能讓重複性作業更加便利。如果您從 v1.1.x 升級,所有資料和設定完全相容,無需額外操作。
