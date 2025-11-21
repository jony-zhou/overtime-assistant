# GitHub Release v1.0.0

## Release Title
```
v1.0.0 - TECO SSP 加班時數計算器首個正式版
```

## Release Notes

### 🎉 首個正式版發布

TECO SSP 加班時數計算器正式版現已推出!這是一個現代化的圖形介面應用程式,專為自動化計算加班時數而設計。

---

### ✨ 核心功能

#### 🎨 現代化 GUI 介面
- 基於 CustomTkinter 的深色主題設計
- 直覺的操作流程,無需技術背景
- 響應式介面,流暢的使用體驗

#### 🔐 智慧登入系統
- 圖形化登入介面
- 背景執行不阻塞 UI
- 自動處理 ASP.NET ViewState 機制
- SSL 憑證問題自動處理

#### 📊 強大的資料處理
- 自動抓取 TECO SSP 出勤異常清單
- 智慧分頁處理 (最多 10 頁)
- 精準的加班時數計算
- 可排序的表格檢視

#### 📋 便利的資料操作
- 智慧複製功能 (加班時數欄位)
- 支援逐行複製或全選複製
- 快捷鍵 `Ctrl+C` 支援
- 右鍵選單整合

#### 💾 專業的報表匯出
- 一鍵匯出 Excel 報表
- 自動格式化的欄位
- 完整的統計數據
- 時間戳記檔名

#### 🔄 自動版本檢查
- 啟動時自動檢查 GitHub 最新版本
- 非侵入式通知設計
- 智慧快取機制 (6 小時)
- 安全的手動更新流程

---

### 🏗️ 技術特色

#### 架構設計
- ✅ **MVC 分層架構**: 清晰的業務邏輯分離
- ✅ **SOLID 原則**: 可維護、可擴展的程式碼
- ✅ **模組化設計**: 易於測試和維護
- ✅ **依賴注入**: 降低耦合度

#### 程式品質
- ✅ **44 個單元測試**: 完整的測試覆蓋
- ✅ **型別提示**: 完整的 type hints
- ✅ **錯誤處理**: 完善的異常捕獲
- ✅ **日誌系統**: 詳細的執行記錄

#### 安全性
- ✅ **OWASP 最佳實踐**: 遵循安全規範
- ✅ **輸入驗證**: 防止注入攻擊
- ✅ **安全更新機制**: 不自動執行下載的程式碼
- ✅ **最小權限**: 無需管理員權限

---

### 📦 安裝與使用

#### 系統需求
- Windows 10/11
- 無需安裝 Python (獨立執行檔)
- 需要網路連線到 TECO SSP 系統

#### 快速開始
1. 下載 `TECO加班計算器.exe`
2. 雙擊執行
3. 輸入 SSP 帳號密碼
4. 自動計算加班時數
5. 匯出 Excel 報表

#### 第一次使用
- Windows SmartScreen 可能會顯示警告,這是正常的
- 點擊「更多資訊」→「仍要執行」即可
- 建議加入防毒軟體的信任清單

---

### 📊 計算邏輯

```
加班時數 = 下班時間 - 上班時間 - 70分鐘(午休) - 480分鐘(正常工時) - 30分鐘(休息)
```

**自動處理**:
- 上班時間晚於 9:00 時,以 9:00 計算
- 加班時數限制在 0-4 小時之間
- 自動四捨五入到小數點後 1 位

---

### 🔧 客製化選項

使用者可以根據公司規定調整:
- 午休時間 (預設 70 分鐘)
- 正常工時 (預設 480 分鐘)
- 休息時間 (預設 30 分鐘)
- 最大加班時數 (預設 4 小時)

詳見 [README.md](https://github.com/jony-zhou/overtime-assistant/blob/main/readme.md) 的客製化調整章節。

---

### 📝 版本資訊

- **版本號**: v1.0.0
- **發布日期**: 2025-11-21
- **相容性**: Windows 10/11 (64-bit)
- **檔案大小**: 約 50-100 MB

---

### 🐛 已知問題

目前無重大已知問題。如遇到問題請:
1. 檢查 `logs/overtime_calculator.log` 日誌檔
2. 到 [Issues](https://github.com/jony-zhou/overtime-assistant/issues) 回報問題
3. 提供詳細的錯誤訊息和重現步驟

---

### 🙏 致謝

感謝所有測試人員的回饋和建議!

---

### 📚 相關文件

- [README.md](https://github.com/jony-zhou/overtime-assistant/blob/main/readme.md) - 完整使用說明
- [QUICKSTART.md](https://github.com/jony-zhou/overtime-assistant/blob/main/QUICKSTART.md) - 快速開始指南
- [UPDATE.md](https://github.com/jony-zhou/overtime-assistant/blob/main/UPDATE.md) - 更新說明
- [BUILD.md](https://github.com/jony-zhou/overtime-assistant/blob/main/BUILD.md) - 打包指南

---

### 🔐 安全性說明

本程式:
- ✅ 不收集任何個人資訊
- ✅ 不傳送使用數據到第三方
- ✅ 僅訪問 TECO SSP 系統和 GitHub API
- ✅ 登入資訊僅存在於記憶體,不儲存到檔案

帳號密碼直接提交到 TECO SSP 伺服器,本程式不做任何儲存。

---

### 📄 授權

本程式僅供個人使用,請勿用於非法用途。使用本程式所產生的任何後果由使用者自行承擔。

---

### 🚀 下載

請從本頁面的 Assets 區下載 `TECO加班計算器.exe`

**校驗碼** (建議驗證):
- 檔案名稱: `TECO加班計算器.exe`
- 下載後建議使用防毒軟體掃描

---

### 💬 支援

- 🐛 回報問題: [GitHub Issues](https://github.com/jony-zhou/overtime-assistant/issues)
- 💡 功能建議: [GitHub Discussions](https://github.com/jony-zhou/overtime-assistant/discussions)
- 📧 聯絡方式: 透過 GitHub

---

**首次發布,歡迎使用並提供回饋!** 🎉
