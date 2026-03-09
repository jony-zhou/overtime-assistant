# 任務清單

## 1. 環境準備與分析

- [x] 1.1 在實際 SSP 環境中驗證新版網頁結構
- [x] 1.2 抓取新版 HTML 範例並建立 test fixtures
- [x] 1.3 確認所有受影響的頁面清單
  - [x] 1.3.1 登入頁面 (default.aspx) - 已確認
  - [x] 1.3.2 個人記錄頁面 (FW21003Z.aspx) - 已確認
  - [x] 1.3.3 出勤異常頁面 (FW99001Z.aspx) - 已確認 ✅
  - [x] 1.3.4 加班補報頁面 (FW21006Z.aspx?Kind=B) - 已確認

## 2. 修正登入服務

- [x] 2.1 更新 `src/services/auth_service.py`
  - [x] 2.1.1 修改登入 URL: `index.aspx` → `default.aspx`
  - [x] 2.1.2 更新表單欄位: `lblAccount` → `txtAccount`
  - [x] 2.1.3 更新表單欄位: `lblPassWord` → `txtPassword`
  - [x] 2.1.4 更新表單欄位: `Submit` → `btnSubmit`
  - [x] 2.1.5 驗證登入成功判斷邏輯是否需調整
- [ ] 2.2 更新 `tests/test_auth_service.py` (若存在) **(Optional)**
- [x] 2.3 手動測試登入功能 ✅ **使用者驗證通過**

## 3. 修正個人記錄解析器

- [x] 3.1 更新 `src/parsers/personal_record_parser.py`
  - [x] 3.1.1 修改表格 ID 查找: `ContentPlaceHolder1_gvFlow211` → `gvFlow211`
  - [x] 3.1.2 改用 `tbody > tr` 遍歷,不依賴 row class
  - [x] 3.1.3 更新 span ID 查找邏輯 (使用固定 ID):`<br>` - 日期: `lblD_OT_Date<br>` - 內容: `lblD_OT_Describe<br>` - 加班時數: `lblD_OT_Minute_E<br>` - 調休時數: `lblD_Change_Minute_E<br>` - 當月累計: `lblD_OT_Manhour<br>` - 當季累計: `lblD_OT_Manhour_T<br>` - 狀態: `lblD_Flag`
  - [x] 3.1.4 移除索引依賴,改用 `find()` 而非 `find(id=f"..._{index}")`
- [ ] 3.2 建立新版 HTML fixture: `tests/fixtures/personal_record_new.html` **(Optional)**
- [ ] 3.3 更新 `tests/test_parsers.py` **(Optional)**
  - [ ] 3.3.1 新增測試案例: 新版 HTML 解析
  - [ ] 3.3.2 保留測試案例: 舊版 HTML 解析 (標記為 legacy)
- [x] 3.4 執行單元測試: `pytest tests/test_parsers.py -v` ✅ **95-96 tests passed**

## 4. 驗證出勤異常解析器

- [x] 4.1 檢查 `src/parsers/attendance_parser.py` 是否受影響
  - [x] 4.1.1 驗證表格 ID: `ContentPlaceHolder1_gvWeb012`
  - [x] 4.1.2 驗證 span ID 結構
  - [x] 4.1.3 如有變更,按相同模式修正
- [ ] 4.2 更新相關測試 (若需要)
- [ ] 4.3 手動測試出勤異常清單功能

## 4. 修正出勤異常解析器

- [x] 4.1 更新 `src/parsers/attendance_parser.py`
  - [x] 4.1.1 修正 `parse_anomaly_records()` 方法
  - [x] 4.1.2 更新 Span ID 查找邏輯:
    - [x] `lblWork_Date_{index}` → `lblAtt_Date`
    - [x] `lblCard_Time_{index}` → `lblAtt_Time`
    - [x] `lblLose_Manhour_{index}` → `lblLose_Manhour`
    - [x] 說明欄位 → `lblAtt_Result`
  - [x] 4.1.3 改用 `tbody > tr` 遍歷 (不依賴 row class)
  - [x] 4.1.4 使用固定 ID 查找 (移除索引依賴)
  - [x] 4.1.5 修正 `parse_punch_records()` 方法
    - [x] 新版改用出勤日曆 (`gvCalendar`) 取代打卡記錄表格 (`gvNotes005`)
    - [x] 從 `lblMonthYear` 提取年月
    - [x] 從 `lblDate*` 提取日期
    - [x] 從 `lblWork_Time*` 的 `data-popup` 屬性提取打卡時間
    - [x] 保持舊版表格格式相容性
- [ ] 4.2 建立新版 HTML fixture: `tests/fixtures/attendance_anomaly_new.html` **(Optional)**
- [ ] 4.3 更新 `tests/test_parsers.py` **(Optional)**
  - [ ] 4.3.1 新增測試案例: 新版異常記錄解析
  - [ ] 4.3.2 保留測試案例: 舊版異常記錄解析 (標記為 legacy)
- [x] 4.4 執行單元測試: `pytest tests/test_parsers.py::test_parse_anomaly_records -v` ✅ **使用者驗證: 3-7 筆打卡記錄正常顯示**

## 5. 修正加班補報服務

- [x] 5.1 更新 `src/services/overtime_report_service.py`
  - [x] 5.1.1 修改增加行 PostBack: `ContentPlaceHolder1$lbtnAddRowi` → `MainContent$lbtnAddRowi`
  - [x] 5.1.2 更新表單欄位 name 前綴: `ContentPlaceHolder1` → `MainContent`
  - [x] 5.1.3 修正送出按鈕 name: `ContentPlaceHolder1$btnCommit` → `MainContent$btnCommit`
  - [x] 5.1.4 **重構表單資料提取機制** (提取所有隱藏欄位、下拉選單、文字區域)
  - [x] 5.1.5 新增詳細 debug 日誌與 HTML 儲存功能
- [x] 5.2 更新 `src/config/settings.py`
  - [x] 5.2.1 修改 URL: `OVERTIME_REPORT_URL = "/FW21006Z.aspx?Kind=B"`
- [ ] 5.3 建立新版 HTML fixture: `tests/fixtures/overtime_report_new.html` **(Optional)**
- [ ] 5.4 更新相關測試 (若存在) **(Optional)**
- [5.5 統計卡片與 UI 改進

- [x] 5.6 更新 `src/services/overtime_status_service.py`
  - [x] 5.6.1 修改表格 ID: `ContentPlaceHolder1_gvFlow211` → `gvFlow211`
  - [x] 5.6.2 更新 span ID 查找邏輯 (使用固定 ID)
- [x] 5.7 更新 `ui/main_window.py` **(Optional - 已有參考資料)**
- [ ] 7.3 更新 `readme.md` - 記錄網頁版本相容性 **(Optional)**
- [ ] 7.4 建立 `docs/SSP_MIGRATION_2026.md` (若需要) **(Optional)**
  - [x] 5.8.1 優化空狀態訊息 (綠色成功訊息)
- [x] 5.9 更新 `ui/components/overtime_report_tab.py`
  - [x] 5.9.1 新增 `_show_empty_state()` 方法

## x] 5.5 手動測試加班補報功能 ✅ **使用者驗證: 送出成功** ✅ **95-96 tests passed**

- [x] 8.1.2 確保覆蓋率維持 > 70%
- [x] 8.1.3 修正所有失敗的測試
- [x] 8.2 整合測試 (實際環境) ✅ **完整使用者測試通過**
  - [x] 8.2.1 測試完整登入流程 ✅ "登入成功"
  - [x] 8.2.2 測試三個分頁資料載入:
    - [x] 出勤異常清單 ✅ "正常解析"
    - [x] 加班補報 ✅ "目前看起來都正確了 沒有問題"
    - [x] 個人記錄查詢 ✅ "個人紀錄有五筆資料"
  - [x] 8.2.3 測試重新整理功能 ✅
  - [x] 8.2.4 測試打卡記錄顯示 ✅ "打卡紀錄有正常顯示了 (3-7 筆)"
  - [x] 8.2.5 測試統計卡片 ✅ "上方狀態列的資料都有了"
- [x] 8.3 回歸測試
  - [x] 8.3.1 驗證加班時數計算邏輯 ✅
  - [x] 8.3.2 驗證統計數據正確性 ✅
  - [x] 8.3.3 驗證 UI 顯示正常 ✅

## 9. 打包與發布準備

- [x] 9.1 更新版本號: v1.3.0 → v1.3.1
- [x] 9.2 更新發布文件: `docs/release/RELEASE_v1.3.1.md`
- [x] 9.3 Git Commit 結構化提交 (7 個邏輯分組)
- [ ] 9.4 測試打包: `python -m PyInstaller overtime_calculator.spec --clean` **(待發布前執行)**
- [ ] 9.5 驗證 .exe 可執行且功能正常 **(待發布前執行)**
- [ ] 9.6 準備發布至 GitHub Release **(待發布前執行)**加班時數計算邏輯
  - [ ] 8.3.2 驗證統計數據正確性
  - [ ] 8.3.3 驗證 UI 顯示正常

## 9. 打包與發布準備

- [ ] 9

所有功能必須在實際 SSP 環境中測試通過:

✅ **登入成功** - 使用者確認: "登入成功"  
✅ **個人記錄查詢正常顯示** - 使用者確認: "個人紀錄有五筆資料"  
✅ **出勤異常清單正常顯示** - 使用者確認: "正常解析"  
✅ **打卡記錄正常顯示** - 使用者確認: "打卡紀錄有正常顯示了 (3-7 筆記錄)"  
✅ **統計卡片正常顯示** - 使用者確認: "上方狀態列的資料都有了"  
✅ **加班補報功能正常** - 使用者確認: "目前看起來都正確了 沒有問題"  
✅ **所有單元測試通過** - 95 tests passed  
✅ **無回歸問題**  
✅ **打包測試通過** - 使用者確認: "打包後可以正常使用"

---

## 最終確認

**使用者最終確認:** "目前看起來都正確了 沒有問題" + "打包後可以正常使用"

**完成日期:** 2026-03-09  
**版本號:** v1.3.1  
**Git Commits:** 8 個邏輯分組提交  
**發布文件:** docs/release/RELEASE_v1.3.1.md ✅  
**打包狀態:** ✅ 成功

**提案狀態:** ✅ **準備歸檔**

---

## 後續工作 (Optional)

以下為非必要的後續改進項目:

- [ ] 建立新版 HTML fixtures (2.2, 3.2, 4.2, 5.3)
- [ ] 更新單元測試以涵蓋新版 HTML 結構 (2.2, 3.3, 4.3, 5.4)
- [ ] 整合參考文件 (temp.md, 加班申報.md) 到正式文件 (7.2)
- [ ] 更新 README 記錄網頁版本相容性 (7.3)
- [ ] 建立 SSP 遷移文件 (7.4)
- [ ] 待發布前打包測試 (9.4-9.6)
- [ ] 8.2 更新 CHANGELOG
- [ ] 8.3 測試打包: `python -m PyInstaller overtime_calculator.spec --clean`
- [ ] 8.4 驗證 .exe 可執行且功能正常
- [ ] 8.5 準備發布說明

## 驗收標準 (不實際送出)

所有功能必須在實際 SSP 環境中測試通過:

✅ 登入成功`<br>`✅ 個人記錄查詢正常顯示`<br>`✅ 出勤異常清單正常顯示`<br>`✅ 加班補報功能可預覽`<br>`✅ Excel 匯出功能正常`<br>`✅ 所有單元測試通過`<br>`✅ 無回歸問題
