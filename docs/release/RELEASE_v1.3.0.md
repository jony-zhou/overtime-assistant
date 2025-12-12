# GitHub Release v1.3.0

## Release Title

```
v1.3.0 - 統一資料同步機制與效能優化
```

## Release Notes

### 本版本重點

本版本重構資料同步機制，引入 `DataSyncService` 統一管理資料抓取與快取，並優化統計卡片顯示。主要改善包括：減少 40% HTTP 請求次數、實作 5 分鐘快取機制、修正個人記錄解析問題。

---

## 主要更新

### 1. 統一資料同步服務 (DataSyncService)

重構資料抓取架構，整合過去分散的資料來源。

#### 改進項目

- 減少 HTTP 請求：從 5 次降至 3 次（減少 40%）
- 快取機制：5 分鐘 TTL，快取讀取時間 < 0.001 秒
- 統一資料模型：使用 `AttendanceSnapshot` 作為單一資料來源
- 資料一致性：所有 UI 元件讀取相同快照
- 錯誤處理：網路錯誤時返回快取資料（Stale-on-Error）

#### 使用方式

```python
# 首次載入 (~13s)
data_sync = DataSyncService(auth_service, settings)
snapshot = data_sync.sync_all()

# 5 分鐘內重新整理 (< 0.001s, 使用快取)
snapshot = data_sync.sync_all()

# 強制重新整理 (~13s)
data_sync._cache_timestamp = 0
snapshot = data_sync.sync_all()
```

---

### 2. 快取機制實作

#### 效能數據

| 指標         | v1.2.x | v1.3.0   | 改進 |
| ------------ | ------ | -------- | ---- |
| HTTP 請求數  | 5      | 3        | -40% |
| 首次載入時間 | 14s    | 13s      | -7%  |
| 快取重新整理 | 3s     | < 0.001s | -99% |
| 重複抓取     | 2 次   | 0 次     | 消除 |

#### 快取配置

- TTL：5 分鐘
- 錯誤處理：網路錯誤時使用快取資料
- 失效策略：超過 5 分鐘自動重新抓取
- 儲存方式：記憶體快取

---

### 3. 資料模型重構

#### 新增類別

- `AttendanceSnapshot` - 出勤資料快照（統一來源）
- `OvertimeStatistics` - 加班統計資料
- `PunchRecord` - 打卡記錄
- `LeaveRecord` - 假別記錄
- `AttendanceQuota` - 剩餘額度
- `UnifiedOvertimeRecord` - 統一加班記錄

#### 新增解析器

- `AttendanceParser` - 出勤頁面解析器
  - `parse_anomaly_table()` - 異常表 (gvWeb012)
  - `parse_punch_table()` - 打卡表 (gvNotes005)
  - `parse_leave_table()` - 假別表 (gvNotes011)
  - `parse_quota()` - 額度解析 (dvNotes019)
- `PersonalRecordParser` - 個人記錄解析器
  - `parse_table()` - 個人記錄表 (gvFlow211)
  - 支援雙層結構（加班/調休）

---

### 4. 統計卡片調整

重新設計統計卡片顯示內容。

#### 卡片配置

1. 待申請筆數 - 尚未申請的異常數量
2. 已申請 - 已提交的記錄數
3. 平均加班時數 - 加班時數平均值
4. 最高加班時數 - 單筆最高時數
5. 總加班時數 - 所有時數總和

#### 調整項目

- 固定顏色配置，不隨資料變化
- 統一 Icon 使用
- 調整卡片間距與樣式

---

### 5. UI 改進與錯誤修正

#### 介面調整

- 統一載入訊息顏色為藍色（`colors.info`）
- 調整訊息文字樣式

#### 錯誤修正

- 修正個人記錄雙層 HTML 解析問題（加班/調休）
- 修正欄位名稱映射錯誤（`overtime_hours`, `report_type`）
- 修正統計卡片資料來源（使用實際申報時數）

---

## 版本比較

| 項目         | v1.2.1     | v1.3.0         |
| ------------ | ---------- | -------------- |
| HTTP 請求數  | 5 次       | 3 次（-40%）   |
| 快取機制     | 無         | 5 分鐘 TTL     |
| 重新整理速度 | 3 秒       | < 0.001 秒     |
| 資料一致性   | 可能不一致 | 統一快照       |
| 個人記錄解析 | 部分錯誤   | 雙層結構支援   |
| 統計卡片     | 基礎顯示   | 調整後配置     |
| 載入訊息顏色 | 預設       | 藍色           |
| 容錯機制     | 無         | Stale-on-Error |
| 資料模型     | 分散       | 統一 Snapshot  |

---

## 技術架構

### 資料同步流程

```
登入後
  ↓
DataSyncService.sync_all()
  ↓
檢查快取（5 分鐘 TTL）
  ↓
├─ 快取有效 → 返回快照（< 0.001s）
└─ 快取無效 → 重新抓取
      ↓
   同時抓取：
   ├─ 出勤頁面（異常/打卡/假別/額度）
   ├─ 個人記錄頁面
   └─ 已申請狀態
      ↓
   合併資料 → 建立快照
      ↓
   更新快取 → 返回快照（~13s）
```

### Stale-on-Error 機制

```python
def sync_all(self):
    try:
        snapshot = self._fetch_and_merge()
        self._snapshot_cache = snapshot
        self._cache_timestamp = time.time()
        return snapshot
    except Exception as e:
        logger.error(f"資料同步失敗: {e}")
        if self._snapshot_cache:
            logger.info("返回舊快取資料")
            return self._snapshot_cache  # 容錯機制
        raise
```

---

## 安裝與使用

### 下載

從本頁面的 **Assets** 區下載 `overtime-assistant-1.3.0.exe`

### 系統需求

- **作業系統**: Windows 10/11 (64-bit)
- **記憶體**: 建議 4GB 以上
- **硬碟空間**: 約 100MB
- **網路**: 需連線以同步資料

### 使用方式

1. 下載 `overtime-assistant-1.3.0.exe`
2. 直接執行（無需安裝）
3. 登入後自動使用新的資料同步機制
4. 享受更快的重新整理速度！

---

## 升級指南

### 從 v1.2.x 升級

#### 升級步驟

1. 備份資料（建議）:

   ```powershell
   Copy-Item cache/ cache_backup/ -Recurse
   ```

2. 下載新版本:

   - 下載 `overtime-assistant-1.3.0.exe`

3. 執行:

   - 替換舊版本執行檔
   - 首次啟動會建立快取

4. 驗證:
   - 登入後檢查載入時間（約 13 秒）
   - 測試重新整理（應小於 0.001 秒）
   - 確認統計卡片顯示正確

#### 相容性

- 所有 v1.2.x 資料完全相容
- 設定檔保留（快取、範本、憑證）
- 無需重新設定登入資訊

#### 檢查清單

- [ ] 體驗首次載入（約 13 秒）
- [ ] 測試快取重新整理（< 0.001 秒）
- [ ] 查看統計卡片
- [ ] 確認個人記錄顯示
- [ ] 驗證載入訊息顏色

---

## 已知問題

### 限制事項

- 快取僅存於記憶體，應用程式重啟後清除（v1.4.0 計劃支援持久化）
- 首次載入需要網路連線
- 資料抓取尚未平行化（v1.4.0 計劃改善）

### 已修正

- 個人記錄時數顯示 0.00（已修正雙層解析）
- 統計卡片資料不正確（已修正資料來源）
- 重複 HTTP 請求（已消除）
- 資料不一致（已統一快照）

---

## 技術細節

### 修改的檔案

- `src/services/data_sync_service.py` - 新增統一資料同步服務
- `src/parsers/attendance_parser.py` - 新增出勤解析器
- `src/parsers/personal_record_parser.py` - 新增個人記錄解析器（雙層支援）
- `src/models/attendance.py` - 新增 AttendanceSnapshot 等模型
- `ui/main_window.py` - 統計卡片優化
- `ui/components/*.py` - 載入訊息藍色化
- `src/config/settings.py` - 新增 CACHE_DURATION_SECONDS 設定

### 新增的檔案

- `docs/development/DATA_SYNC_MECHANISM.md` - 資料同步機制設計文件
- `docs/development/PERFORMANCE_TESTING.md` - 效能測試報告
- `tests/test_data_sync_service.py` - DataSyncService 單元測試（11 個）
- `tests/test_parsers.py` - 解析器單元測試（9 個）
- `tests/test_performance.py` - 效能測試
- `debug_personal_records.py` - 個人記錄除錯腳本

### 棄用的服務

以下服務標記為 `@deprecated`（將於 v2.0.0 移除）:

- `OvertimeStatusService` - 請使用 `DataSyncService.sync_all()`
- `PersonalRecordService` - 請使用 `DataSyncService.get_personal_records()`

#### 遷移範例

```python
# ❌ 舊用法（deprecated）
status_service = OvertimeStatusService()
records = status_service.fetch_submitted_records(session)

# ✅ 新用法
data_sync = DataSyncService(auth_service, settings)
snapshot = data_sync.sync_all()
personal_records = snapshot.personal_records
```

### 測試

- 單元測試：96 個測試全部通過
- 覆蓋率：> 70%
- 效能測試：詳見 `docs/development/PERFORMANCE_TESTING.md`

---

## 使用說明

### 重新整理

- 5 分鐘內點擊「重新整理」會使用快取
- 超過 5 分鐘自動重新抓取資料
- 網路錯誤時使用快取資料

### 統計卡片

- 待申請筆數：需要處理的異常數量
- 已申請：已提交的加班申請
- 平均加班時數：平均加班強度
- 最高加班時數：單日最高記錄
- 總加班時數：本月累計總時數

---

## 安全性

### OWASP 實踐

- HTTPS Only：所有 API 請求使用 HTTPS
- 憑證加密：使用 Windows DPAPI 加密儲存
- 日誌安全：不記錄密碼等敏感資訊
- Session 管理：自動處理過期
- 錯誤處理：完善的例外處理

### 隱私

- 所有資料存放於本機
- 快取僅在記憶體中
- 不收集使用者行為資料
- 不傳送資料到第三方

---

## 相關文件

- **資料同步機制**: [DATA_SYNC_MECHANISM.md](../development/DATA_SYNC_MECHANISM.md)
- **效能測試報告**: [PERFORMANCE_TESTING.md](../development/PERFORMANCE_TESTING.md)
- **版本管理**: [VERSION_MANAGEMENT.md](../development/VERSION_MANAGEMENT.md)
- **使用說明**: [README.md](../../readme.md)
- **完整 Changelog**: [CHANGELOG.md](../../CHANGELOG.md)

---

## 發布資訊

- **版本號**: v1.3.0
- **發布日期**: 2025-12-02
- **變更類型**: Minor Version（新功能 + 效能優化）
- **相容性**: Windows 10/11 (64-bit)
- **檔案大小**: 約 50-100 MB
- **升級建議**: 強烈建議升級（大幅效能提升）

---

## 更新歷史

### v1.3.0 (2025/12/02)

- 統一資料同步機制（DataSyncService）
- 快取策略（5 分鐘 TTL）
- 統計卡片調整
- 資料模型重構
- UI 載入訊息調整
- 個人記錄解析修正

### v1.2.1 (2025/12/01)

- 現代化更新對話框
- 手動檢查更新功能

### v1.2.0 (2025/12/01)

- 加班補報自動填寫
- 加班範本管理

### v1.1.1 (2025/01/21)

- 圖示解析度提升

### v1.1.0 (2025/01/21)

- UI/UX 改版

### v1.0.2 (2025/11/21)

- 修復版本檢查

### v1.0.1 (2025/11/21)

- 修正打包檔名

### v1.0.0 (2025/11/21)

- 首個正式版

---

## 未來計劃

### v1.4.0（預計 2025 Q1）

1. 平行載入 - 預估節省 50% 時間
2. 持久化快取 - 重啟後保留快取
3. 增量更新 - 僅抓取變更記錄
4. 預載入策略 - 背景載入資料

---

### 備註

本版本重構資料同步機制，引入快取策略以提升效能。建議升級以獲得更好的載入速度與資料一致性。
