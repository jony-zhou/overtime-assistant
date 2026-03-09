# GitHub Release v1.3.1

## Release Title

```
v1.3.1 - SSP 2026 HTML 結構相容性修正
```

## Release Notes

### 本版本重點

本版本修正 TECO SSP 系統 2026 年 Q1 改版後的 HTML 結構變更所造成的相容性問題。SSP 網站進行了大規模的版型更新,導致原有的 HTML 解析器失效,本版本針對所有受影響的功能模組進行修正,確保系統能夠正常運作。

**修正範圍包括:**

- 登入服務 (URL 及表單欄位更新)
- 個人加班記錄解析 (表格 ID 及欄位 ID 更新)
- 出勤記錄解析 (異常記錄、打卡記錄、新增日曆格式支援)
- 加班申報服務 (表單送出機制修正)
- 統計資料顯示 (資料來源修正)
- UI 空狀態顯示 (更友善的成功訊息)

---

## 主要更新

### 1. SSP HTML 結構變更總覽

2026 年 Q1 起,SSP 系統進行了以下結構性變更:

#### HTML ID 前綴變更

```diff
舊版 (2025)                        新版 (2026)
- ContentPlaceHolder1_*            + MainContent_* 或直接 ID (無前綴)
- ContentPlaceHolder1_gvFlow211    + gvFlow211
- ContentPlaceHolder1_gvWeb012     + MainContent_gvWeb012
```

#### 欄位 ID 命名規則變更

```diff
舊版: 索引式 ID                    新版: 固定 ID (重複)
- lblOT_Date_0, lblOT_Date_1      + lblD_OT_Date (每行相同)
- lblOT_Describe_0                + lblD_OT_Describe (每行相同)
- lblOT_Manhour_0                 + lblD_OT_Manhour (每行相同)
```

#### 登入頁面變更

```diff
URL:
- /index.aspx                     + /default.aspx

表單欄位:
- lblAccount                      + txtAccount
- lblPassWord                     + txtPassword
- Submit                          + btnSubmit
```

#### 打卡記錄新增日曆格式

新版新增 `gvCalendar` 格式,使用 `data-popup` 屬性儲存刷卡時間:

```html
<span data-popup="刷卡 09:02:15&lt;br&gt;刷卡 18:35:20"></span>
```

---

### 2. 服務層修正

#### 2.1 登入服務 (auth_service.py)

**修正項目:**

- 登入 URL: `index.aspx` → `default.aspx`
- 表單欄位名稱更新:
  - `lblAccount` → `txtAccount`
  - `lblPassWord` → `txtPassword`
  - `Submit` → `btnSubmit`

**影響範圍:** 所有需要登入的功能

#### 2.2 加班申報服務 (overtime_report_service.py)

**修正項目:**

- 表單資料提取: 改為提取**所有**隱藏欄位、下拉選單、文字區域 (原本只提取 ViewState/EventValidation/EventTarget/EventArgument)
- 新增詳細的 debug 日誌輸出
- 送出後自動儲存響應 HTML 至 `logs/debug/submission_response_*.html`
- 優化送出結果檢查,增加多種成功指標判斷

**技術說明:**
ASP.NET WebForms 的 PostBack 機制要求提交時必須包含頁面上的所有隱藏欄位,否則會導致送出失敗或資料遺失。

#### 2.3 加班狀態服務 (overtime_status_service.py)

**修正項目:**

- 表格 ID: `ContentPlaceHolder1_gvFlow211` → `gvFlow211` (含 fallback)
- 欄位 ID 更新為固定格式:
  - `lblOT_Date_{index}` → `lblD_OT_Date`
  - `lblFlag_{index}` → `lblD_Flag`
  - `lblOT_Describe_{index}` → `lblD_OT_Describe`
  - (共 7 個欄位)

**解析策略:** 保留原 ID 作為 fallback,優先嘗試新 ID

---

### 3. 解析器層修正

#### 3.1 個人記錄解析器 (personal_record_parser.py)

**修正項目:**

- 表格 ID: `ContentPlaceHolder1_gvFlow211` → `gvFlow211` (含 fallback)
- 欄位 ID 更新為固定格式:
  - `lblOT_Date_{index}` → `lblD_OT_Date`
  - `lblOT_Describe_{index}` → `lblD_OT_Describe`
  - `lblOT_Minute_E_{index}` → `lblD_OT_Minute_E`
  - `lblChange_Minute_E_{index}` → `lblD_Change_Minute_E`
  - (共 7 個欄位)

**解析策略:** 使用行遍歷 + 相對位置查找,避免依賴 ID 索引

#### 3.2 出勤記錄解析器 (attendance_parser.py)

**修正項目:**

##### (1) 異常記錄解析 (`parse_anomaly_records`)

- 表格 ID: `ContentPlaceHolder1_gvWeb012` → `MainContent_gvWeb012` (含 fallback)
- 欄位 ID 更新:
  - `lblWork_Date_{index}` → `lblAtt_Date`
  - `lblShift_Time_{index}` → `lblAtt_Shift_Time`
  - `lblPunchIn_Time_{index}` → `lblAtt_PunchIn_Time`
  - `lblPunchOut_Time_{index}` → `lblAtt_PunchOut_Time`
  - `lblNote_{index}` → `lblAtt_Note`

##### (2) 打卡記錄解析 (`parse_punch_records`)

- **新增日曆格式支援** (`gvCalendar`)
  - 使用 `data-popup` 屬性提取刷卡時間
  - 正則表達式: `刷卡 (\d{2}:\d{2}:\d{2})`
  - 月份/日期從 `lblMonthYear` / `lblDate*` 欄位提取
- 保留原表格格式支援 (`gvNotes005`) 作為 fallback
- 自動偵測格式並選擇對應解析器

**範例: 日曆格式解析**

```html
<span id="lblWork_Time_07" data-popup="刷卡 09:02:15&lt;br&gt;刷卡 18:35:20">
  09:02~18:35
</span>
```

```python
punch_times = re.findall(r'刷卡 (\d{2}:\d{2}:\d{2})', data_popup)
# => ['09:02:15', '18:35:20']
```

---

### 4. UI 層改進

#### 4.1 統計卡片修正 (main_window.py)

**問題:** 統計卡片在無異常記錄時不顯示資料

**修正:**

- 改進資料來源判斷邏輯:

```python
# 修正前
has_data = report and report.records

# 修正後
has_data = (
    (report and report.records)
    or personal_records
    or submitted_records
)
```

- 即使無異常記錄,若有個人記錄或已申請記錄,仍顯示統計資料

#### 4.2 空狀態訊息優化

**出勤記錄頁籤 (attendance_tab.py):**

```diff
- "🔍 本月尚無出勤異常記錄"
+ "✅ 太好了!本月沒有出勤異常記錄"
顏色: 藍色 → 綠色
```

**加班申報頁籤 (overtime_report_tab.py):**

新增 `_show_empty_state()` 方法:

```python
"✅ 太好了!本月沒有出勤異常\n\n無需申報加班補休"
```

---

### 5. 配置更新

#### 設定檔 (config/settings.py)

```python
# 加班申報頁面 URL 修正
OVERTIME_REPORT_URL = "/FW21006Z.aspx?Kind=B"
```

---

## 版本比較

| 項目            | v1.3.0      | v1.3.1                 |
| --------------- | ----------- | ---------------------- |
| SSP 2026 相容性 | ❌ 不相容   | ✅ 完全相容            |
| 登入功能        | ❌ 失敗     | ✅ 正常                |
| 個人記錄解析    | ❌ 失敗     | ✅ 正常 (5 筆記錄)     |
| 打卡記錄解析    | ❌ 失敗     | ✅ 正常 (日曆格式)     |
| 異常記錄解析    | ❌ 失敗     | ✅ 正常                |
| 加班申報送出    | ❌ 失敗     | ✅ 正常 (完整欄位)     |
| 統計卡片顯示    | ⚠️ 部分錯誤 | ✅ 正常                |
| 空狀態訊息      | 普通        | ✅ 友善訊息 + 綠色     |
| Debug 日誌      | 基礎        | ✅ 詳細 (含 HTML 儲存) |
| Fallback 機制   | 無          | ✅ 雙重 ID 查找        |

---

## 修改檔案清單

### 核心邏輯 (3 個檔案)

1. **src/core/version.py**
   - 版本號: `1.3.0` → `1.3.1`
   - 版本名稱: "SSP 2026 HTML 結構相容性修正"

2. **src/config/settings.py**
   - 更新 `OVERTIME_REPORT_URL`

### 服務層 (3 個檔案)

3. **src/services/auth_service.py**
   - 登入 URL 更新
   - 表單欄位名稱更新

4. **src/services/overtime_report_service.py**
   - 表單資料提取機制重構
   - 新增詳細 debug 日誌
   - 新增響應 HTML 儲存功能

5. **src/services/overtime_status_service.py**
   - 表格 ID 更新 (含 fallback)
   - 欄位 ID 更新為固定格式

### 解析器層 (2 個檔案)

6. **src/parsers/personal_record_parser.py**
   - 表格 ID 更新 (含 fallback)
   - 欄位 ID 更新為固定格式

7. **src/parsers/attendance_parser.py**
   - 異常記錄欄位 ID 更新
   - **新增日曆格式解析** (`gvCalendar`)
   - 打卡記錄雙格式支援

### UI 層 (3 個檔案)

8. **ui/main_window.py**
   - 統計卡片資料來源判斷邏輯修正

9. **ui/components/attendance_tab.py**
   - 空狀態訊息更新 (綠色成功訊息)

10. **ui/components/overtime_report_tab.py**
    - 新增 `_show_empty_state()` 方法

---

## 技術架構

### Fallback 機制設計

所有解析器均採用雙重 ID 查找策略,確保向後相容:

```python
# 優先嘗試新 ID
table = soup.find("table", id="gvFlow211")

# 失敗則嘗試舊 ID
if not table:
    table = soup.find("table", id="ContentPlaceHolder1_gvFlow211")

# 仍失敗則拋出錯誤
if not table:
    raise ValueError("找不到表格")
```

### 日曆格式解析流程

```
parse_punch_records()
  ↓
檢查 gvCalendar (新格式)
  ↓
├─ 找到 → 使用 data-popup 解析
│    ↓
│    提取月份 (lblMonthYear)
│    ↓
│    遍歷 lblDate_* / lblWork_Time_*
│    ↓
│    正則匹配: 刷卡 (\d{2}:\d{2}:\d{2})
│    ↓
│    建立 PunchRecord
│
└─ 未找到 → 使用 gvNotes005 (舊格式)
     ↓
     按原邏輯解析
```

### 表單送出機制

```python
# 舊版 (錯誤)
form_data = {
    '__VIEWSTATE': '...',
    '__EVENTVALIDATION': '...',
    # ... 只提取少數欄位
}

# 新版 (正確)
form_data = {
    '__VIEWSTATE': '...',
    '__EVENTVALIDATION': '...',
    '__EVENTTARGET': '...',
    '__EVENTARGUMENT': '...',
    'ctl00$hfLeftSidebarOpen': 'true',  # 新增
    'ctl00$MainContent$ddlYear': '2026',  # 新增
    # ... 提取所有隱藏欄位、下拉選單、文字區域
}
```

**關鍵:** ASP.NET PostBack 需要所有表單欄位,否則伺服器端狀態驗證失敗。

---

## 測試驗證

### 使用者測試回饋

經過完整使用者測試,所有功能均驗證通過:

✅ **登入功能** - "登入成功"  
✅ **個人記錄** - "個人紀錄有五筆資料"  
✅ **打卡記錄** - "打卡紀錄有正常顯示了" (3-7 筆記錄)  
✅ **異常記錄** - 正常解析異常表  
✅ **統計卡片** - "上方狀態列的資料都有了"  
✅ **加班申報** - "目前看起來都正確了 沒有問題"  
✅ **空狀態顯示** - 友善的成功訊息

**最終確認:** "目前看起來都正確了 沒有問題"

---

## 安裝與使用

### 下載

從本頁面的 **Assets** 區下載 `overtime-assistant-1.3.1.exe`

### 系統需求

- **作業系統**: Windows 10/11 (64-bit)
- **記憶體**: 建議 4GB 以上
- **硬碟空間**: 約 100MB
- **網路**: 需連線至 TECO SSP 系統

### 從 v1.3.0 升級

1. 關閉舊版程式
2. 下載 `overtime-assistant-1.3.1.exe`
3. 直接執行 (設定與快取會自動保留)
4. 重新登入以套用新的解析器

**注意:** v1.3.0 無法在 2026 年使用,必須升級至 v1.3.1

---

## 已知問題與限制

### 限制

- SSP 系統若再次改版,需重新適配解析器
- 日曆格式解析依賴 `data-popup` 屬性,若 SSP 修改此實作方式將失效

### Debug 功能

- 表單送出失敗時,自動儲存響應 HTML 至 `logs/debug/`
- 可用於分析 SSP 系統變更

---

## 開發資訊

### OpenSpec 提案

本版本實作內容依據 OpenSpec 提案:

- **提案編號**: fix-ssp-html-structure-2026
- **提案文件**: `openspec/changes/fix-ssp-html-structure-2026/proposal.md`
- **任務追蹤**: `openspec/changes/fix-ssp-html-structure-2026/tasks.md`

### Git Commit 結構

本版本包含以下邏輯分組提交:

1. `chore: 更新版本號至 v1.3.1`
2. `fix(auth): 修正登入服務適配 SSP 2026 HTML 結構`
3. `fix(parsers): 更新個人記錄與出勤記錄解析器`
4. `fix(services): 修正加班申報表單送出機制`
5. `fix(ui): 改進統計卡片與空狀態顯示`
6. `fix(config): 更新加班申報頁面 URL`
7. `docs: 新增 RELEASE_v1.3.1 文件`

---

## 感謝

感謝使用者詳細的測試回饋,協助我們逐一驗證並修正所有功能模組。

---

## 下一步規劃

### 短期 (v1.3.x)

- 持續監控 SSP 系統變更
- 優化 debug 日誌機制

### 長期 (v2.0.0)

- 移除 legacy 服務 (`DataService`, `OvertimeStatusService`, `PersonalRecordService`)
- 全面切換至 `DataSyncService`
- 改進快取機制 (考慮持久化快取)

---

**完整變更記錄:** 請參考 [CHANGELOG.md](../../CHANGELOG.md)

**問題回報:** 請至 [GitHub Issues](https://github.com/your-org/overtime-assistant/issues) 提出
