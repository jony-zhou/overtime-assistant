## Context

目前系統從 TECO SSP 的三個頁面分別抓取資料:

1. **出勤狀況頁面** (`FW99001Z.aspx#tabs-1`):

   - 打卡紀錄表 (`gvNotes005`)
   - 假別紀錄表 (`gvNotes011`)
   - 剩餘額度 (`dvNotes019`)

2. **出勤異常清單** (`FW99001Z.aspx#tabs-2`):

   - 異常表 (`gvWeb012`) - 包含日期、刷卡時間、異常說明

3. **個人記錄查詢** (`FW21003Z.aspx`):
   - 記錄查詢表 (`gvFlow211`) - 包含加班日期、內容、狀態、申報時數、累計

**問題**:

- 頁面 2 和頁面 3 的資料有重疊 (加班日期、時數)
- 多個服務分別請求相同頁面 (如 `OvertimeStatusService` 和 `PersonalRecordService` 都請求 `FW21003Z.aspx`)
- 資料模型分散,無法有效關聯

## Goals / Non-Goals

### Goals

- 建立統一的資料模型,整合所有 SSP 資料來源
- 減少 HTTP 請求次數,提升效能
- 提供智慧快取機制,避免重複抓取
- 清晰的資料流向,易於維護與擴充

### Non-Goals

- 不改變 SSP 系統本身的結構
- 不增加新的 SSP 頁面
- 不修改加班計算邏輯 (保持現有 `OvertimeCalculator`)
- 不改變 UI 的外觀與互動方式 (僅改資料來源)

## Decisions

### 決策 1: 統一資料模型設計

建立四層資料模型:

```python
# 第一層: 原始資料 (Raw Data) - 直接從 HTML 解析
@dataclass
class PunchRecord:
    """打卡記錄"""
    date: str           # YYYY/MM/DD
    punch_times: List[str]  # ['08:30:00', '18:45:00']

@dataclass
class LeaveRecord:
    """假別記錄"""
    leave_type: str     # 假別名稱
    days: int           # 天數
    hours: int          # 小時數

@dataclass
class AttendanceQuota:
    """剩餘額度"""
    annual_leave: int   # 特休剩餘天數
    compensatory_leave: int  # 調修剩餘天數
    overtime_threshold: int  # 未達換修最低時限 (分鐘)

# 第二層: 整合資料 (Integrated Data) - 合併多來源
@dataclass
class UnifiedOvertimeRecord:
    """統一加班記錄"""
    date: str                    # YYYY/MM/DD
    punch_start: Optional[str]   # 上班打卡時間
    punch_end: Optional[str]     # 下班打卡時間
    calculated_overtime_hours: float  # 計算的加班時數

    # 來自個人記錄查詢
    submitted: bool = False      # 是否已申請
    submission_content: Optional[str] = None  # 加班內容
    submission_status: Optional[str] = None   # 狀態 (簽核中/完成)
    submission_type: Optional[str] = None     # 類型 (加班/調休)
    reported_overtime_hours: Optional[float] = None  # 申報時數
    monthly_total: Optional[float] = None     # 當月累計
    quarterly_total: Optional[float] = None   # 當季累計

    # 來自異常清單
    has_anomaly: bool = False    # 是否有異常
    anomaly_description: Optional[str] = None  # 異常說明

# 第三層: 聚合資料 (Aggregated Data)
@dataclass
class OvertimeStatistics:
    """加班統計"""
    total_records: int
    total_overtime_hours: float
    average_overtime_hours: float
    max_overtime_hours: float
    submitted_records: int
    pending_records: int

# 第四層: 完整快照 (Complete Snapshot)
@dataclass
class AttendanceSnapshot:
    """出勤快照 (單次資料同步結果)"""
    timestamp: datetime
    punch_records: List[PunchRecord]
    leave_records: List[LeaveRecord]
    quota: AttendanceQuota
    overtime_records: List[UnifiedOvertimeRecord]
    statistics: OvertimeStatistics
```

**理由**:

- 分層設計,職責清晰
- 原始資料保留,可追溯
- 整合資料便於 UI 使用
- 支援未來擴充 (如增加新資料來源)

### 決策 2: 資料同步服務架構

```python
class DataSyncService:
    """統一資料同步服務"""

    def __init__(self, session: requests.Session, settings: Settings):
        self.session = session
        self.settings = settings
        self.cache: Optional[AttendanceSnapshot] = None
        self.cache_timestamp: Optional[datetime] = None

        # HTML 解析器 (注入依賴)
        self.attendance_parser = AttendanceParser()
        self.personal_record_parser = PersonalRecordParser()

    def sync_all(self, force_refresh: bool = False) -> AttendanceSnapshot:
        """全量同步所有資料"""
        if not force_refresh and self._is_cache_valid():
            return self.cache

        # 平行抓取三個頁面
        with ThreadPoolExecutor(max_workers=3) as executor:
            future_attendance = executor.submit(self._fetch_attendance_page)
            future_anomaly = executor.submit(self._fetch_anomaly_page)
            future_personal = executor.submit(self._fetch_personal_record_page)

            attendance_html = future_attendance.result()
            anomaly_html = future_anomaly.result()
            personal_html = future_personal.result()

        # 解析資料
        punch_records = self.attendance_parser.parse_punch_table(attendance_html)
        leave_records = self.attendance_parser.parse_leave_table(attendance_html)
        quota = self.attendance_parser.parse_quota(attendance_html)

        anomaly_records = self.attendance_parser.parse_anomaly_table(anomaly_html)
        personal_records = self.personal_record_parser.parse_table(personal_html)

        # 整合資料
        overtime_records = self._merge_overtime_data(
            anomaly_records, personal_records
        )

        # 建立快照
        snapshot = AttendanceSnapshot(
            timestamp=datetime.now(),
            punch_records=punch_records,
            leave_records=leave_records,
            quota=quota,
            overtime_records=overtime_records,
            statistics=self._calculate_statistics(overtime_records)
        )

        # 更新快取
        self.cache = snapshot
        self.cache_timestamp = datetime.now()

        return snapshot

    def sync_overtime_status(self) -> List[UnifiedOvertimeRecord]:
        """增量同步加班狀態 (僅更新已申請記錄的狀態)"""
        if not self.cache:
            return self.sync_all().overtime_records

        # 僅抓取個人記錄頁面
        personal_html = self._fetch_personal_record_page()
        personal_records = self.personal_record_parser.parse_table(personal_html)

        # 更新快取中的狀態
        for record in self.cache.overtime_records:
            matching = next(
                (p for p in personal_records if p.date == record.date),
                None
            )
            if matching:
                record.submission_status = matching.status
                record.monthly_total = matching.monthly_total
                record.quarterly_total = matching.quarterly_total

        return self.cache.overtime_records

    def _is_cache_valid(self, max_age_seconds: int = 300) -> bool:
        """檢查快取是否有效 (預設 5 分鐘)"""
        if not self.cache or not self.cache_timestamp:
            return False
        age = (datetime.now() - self.cache_timestamp).total_seconds()
        return age < max_age_seconds

    def _merge_overtime_data(
        self,
        anomaly_records: List[Dict],
        personal_records: List[Dict]
    ) -> List[UnifiedOvertimeRecord]:
        """合併異常清單與個人記錄"""
        # 建立日期索引
        personal_by_date = {r['date']: r for r in personal_records}

        unified = []
        for anomaly in anomaly_records:
            date = anomaly['date']
            personal = personal_by_date.get(date)

            record = UnifiedOvertimeRecord(
                date=date,
                punch_start=anomaly.get('start_time'),
                punch_end=anomaly.get('end_time'),
                calculated_overtime_hours=anomaly.get('overtime_hours', 0.0),
                has_anomaly=True,
                anomaly_description=anomaly.get('description'),
                submitted=personal is not None,
                submission_content=personal.get('content') if personal else None,
                submission_status=personal.get('status') if personal else None,
                submission_type=personal.get('type') if personal else None,
                reported_overtime_hours=personal.get('hours') if personal else None,
                monthly_total=personal.get('monthly_total') if personal else None,
                quarterly_total=personal.get('quarterly_total') if personal else None,
            )
            unified.append(record)

        return unified
```

**理由**:

- 統一入口,避免分散的服務
- 平行抓取,提升效能
- 智慧快取,減少不必要的請求
- 支援全量與增量同步,靈活應對不同場景

### 決策 3: 解析器分離

將 HTML 解析邏輯從服務層分離:

```python
class AttendanceParser:
    """出勤頁面解析器"""

    def parse_punch_table(self, html: str) -> List[PunchRecord]:
        """解析打卡記錄表 (gvNotes005)"""
        ...

    def parse_leave_table(self, html: str) -> List[LeaveRecord]:
        """解析假別記錄表 (gvNotes011)"""
        ...

    def parse_quota(self, html: str) -> AttendanceQuota:
        """解析剩餘額度 (dvNotes019)"""
        ...

    def parse_anomaly_table(self, html: str) -> List[Dict]:
        """解析異常表 (gvWeb012)"""
        ...

class PersonalRecordParser:
    """個人記錄解析器"""

    def parse_table(self, html: str) -> List[Dict]:
        """解析個人記錄表 (gvFlow211)"""
        ...
```

**理由**:

- 單一職責原則 (SRP)
- 易於測試 (不依賴網路請求)
- 可重用 (不同服務可共用解析器)
- 符合現有 `DataService` 的重構方向

### 決策 4: UI 層適配器模式

提供適配器方法,讓現有 UI 層無縫遷移:

```python
class DataSyncService:
    # ... 上述方法 ...

    # === 適配器方法 (Adapter for legacy UI) ===

    def get_attendance_records(self) -> List[AttendanceRecord]:
        """適配器: 返回舊版 AttendanceRecord 格式"""
        snapshot = self.sync_all()
        return [
            AttendanceRecord(
                date=r.date,
                start_time=r.punch_start or "08:00:00",
                end_time=r.punch_end or "18:00:00",
                overtime_hours=r.calculated_overtime_hours,
                total_minutes=int(r.calculated_overtime_hours * 60)
            )
            for r in snapshot.overtime_records
        ]

    def get_submission_records(self) -> List[OvertimeSubmissionRecord]:
        """適配器: 返回舊版 OvertimeSubmissionRecord 格式"""
        snapshot = self.sync_all()
        return [
            OvertimeSubmissionRecord(
                date=r.date,
                description=r.submission_content or "",
                overtime_hours=r.calculated_overtime_hours,
                is_overtime=r.submission_type != "調休",
                is_selected=not r.submitted,
                submitted_status=r.submission_status
            )
            for r in snapshot.overtime_records
        ]

    def get_personal_records(self) -> Tuple[List[PersonalRecord], PersonalRecordSummary]:
        """適配器: 返回舊版 PersonalRecord 格式"""
        snapshot = self.sync_all()
        submitted = [r for r in snapshot.overtime_records if r.submitted]

        records = [
            PersonalRecord(
                date=r.date,
                content=r.submission_content or "",
                status=r.submission_status or "",
                overtime_hours=r.reported_overtime_hours or 0.0,
                monthly_total=r.monthly_total or 0.0,
                quarterly_total=r.quarterly_total or 0.0,
                report_type=r.submission_type or ""
            )
            for r in submitted
        ]

        summary = PersonalRecordSummary(
            total_records=snapshot.statistics.submitted_records,
            total_overtime_hours=snapshot.statistics.total_overtime_hours,
            average_overtime_hours=snapshot.statistics.average_overtime_hours,
            max_overtime_hours=snapshot.statistics.max_overtime_hours,
            current_month_total=submitted[-1].monthly_total if submitted else 0.0,
            current_quarter_total=submitted[-1].quarterly_total if submitted else 0.0,
        )

        return records, summary
```

**理由**:

- 漸進式遷移,降低風險
- UI 層無需立即修改
- 向後相容,保持穩定
- 便於測試新舊系統行為一致性

## Alternatives Considered

### 方案 A: 保持現狀,優化快取

**描述**: 不重構,僅在現有服務中加入快取機制

**優點**:

- 改動最小,風險低
- 無需學習新架構

**缺點**:

- 無法根本解決重複請求問題
- 快取邏輯分散,難以管理
- 資料不一致問題依然存在

**為何不採用**: 治標不治本,長期維護成本更高

### 方案 B: 完全重寫,使用 ORM

**描述**: 引入資料庫 (如 SQLite),將 SSP 資料同步到本地資料庫,使用 ORM (如 SQLAlchemy) 管理

**優點**:

- 強大的查詢能力
- 資料持久化
- 支援複雜關聯查詢

**缺點**:

- 過度設計,違反 YAGNI 原則
- 增加複雜度與學習成本
- 資料庫同步邏輯複雜
- 單次使用無需持久化

**為何不採用**: 本專案為短時使用工具,無需資料庫級別的持久化

### 方案 C: 微服務架構

**描述**: 將資料抓取、解析、快取拆分為獨立的微服務

**優點**:

- 職責分離,易於擴展
- 可獨立部署與測試

**缺點**:

- 過度設計,違反 KISS 原則
- 增加部署與維護成本
- 單機桌面應用無需分散式架構

**為何不採用**: 不符合桌面應用的技術棧與需求

## Risks / Trade-offs

### 風險 1: 重構範圍大,可能引入 Bug

**影響**: 高
**機率**: 中

**緩解措施**:

- 分階段實作 (先新增,後廢棄)
- 完整的單元測試覆蓋 (目標 80%+)
- 在測試環境充分驗證
- 提供回滾計畫 (保留舊服務)

### 風險 2: SSP 系統結構變更導致解析失敗

**影響**: 高
**機率**: 低

**緩解措施**:

- 解析器使用多重選擇器 (fallback)
- 記錄詳細的解析日誌
- 提供友善的錯誤訊息
- 監控 SSP 系統變更

### 權衡 1: 快取 vs 即時性

**選擇**: 預設快取 5 分鐘,提供強制重新整理選項

**理由**:

- 出勤資料變更頻率低 (通常每日一次)
- 5 分鐘內的延遲可接受
- 大幅提升效能與使用者體驗

### 權衡 2: 統一模型 vs 靈活性

**選擇**: 統一模型,犧牲部分靈活性

**理由**:

- 本專案資料來源固定 (僅 SSP)
- 統一模型帶來的效能與維護性優勢大於靈活性損失
- 若未來需擴充,可透過繼承擴展

## Migration Plan

### 階段一: 新增新服務 (不破壞現有功能)

**時間**: 2-3 天

1. 建立新資料模型 (`UnifiedOvertimeRecord`, `AttendanceQuota` 等)
2. 建立 `DataSyncService` 與解析器
3. 實作適配器方法
4. 撰寫單元測試

**驗證**: 新舊服務並存,輸出結果一致

### 階段二: UI 層遷移

**時間**: 1-2 天

1. `MainWindow` 改用 `DataSyncService`
2. 各分頁改用適配器方法
3. 更新「重新整理」按鈕邏輯
4. 整合測試

**驗證**: UI 功能正常,效能提升符合預期

### 階段三: 清理舊服務

**時間**: 1 天

1. 標記舊服務為 `@deprecated`
2. 移除 `OvertimeStatusService`
3. 移除 `PersonalRecordService`
4. 重構 `DataService` 為解析器
5. 更新文件

**驗證**: 所有測試通過,無編譯警告

### 回滾計畫

若發現嚴重問題:

1. **立即回滾**: 恢復 Git 提交至階段一完成前
2. **保留新服務**: 標記為實驗性功能
3. **收集問題**: 記錄失敗原因與使用者回饋
4. **修正後重試**: 修復問題後再次部署

## Open Questions

1. **快取策略**: 5 分鐘是否合適?是否需要可設定?

   - **建議**: 預設 5 分鐘,在 `Settings` 中提供 `CACHE_DURATION_SECONDS` 可設定

2. **錯誤處理**: 若某個頁面抓取失敗,是否應使用快取資料?

   - **建議**: 提供降級策略 - 若新資料抓取失敗,返回快取資料並警告使用者

3. **平行抓取**: 是否會觸發 SSP 系統的反爬蟲機制?

   - **建議**: 初期使用平行抓取,若發現問題改為序列抓取

4. **測試覆蓋率**: 目標覆蓋率為何?

   - **建議**: 核心邏輯 (DataSyncService、解析器) 達到 80%+,適配器方法 60%+

5. **向後相容性**: 是否需要支援舊版資料模型的序列化?
   - **建議**: 不需要,本專案無資料持久化需求
