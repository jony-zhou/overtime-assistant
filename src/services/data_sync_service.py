"""統一資料同步服務

負責從 SSP 系統抓取、解析、整合所有出勤與加班相關資料。

核心功能:
- 全量同步: 抓取所有頁面資料並建立 AttendanceSnapshot
- 增量同步: 僅更新已申請記錄的狀態
- 智慧快取: 5 分鐘內重複請求直接返回快取資料
- 平行抓取: 同時請求多個頁面提升效能
- 資料整合: 合併異常記錄與個人記錄為統一模型

設計原則:
- SOLID: 單一資料來源,統一服務介面
- DRY: 避免重複抓取相同資料
- Fail-safe: 網路錯誤時提供降級策略
"""

import logging
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from requests import Session
from requests.exceptions import RequestException, Timeout
import urllib3

from ..config.settings import Settings
from ..parsers.attendance_parser import AttendanceParser
from ..parsers.personal_record_parser import PersonalRecordParser
from ..models.snapshot import AttendanceSnapshot, OvertimeStatistics
from ..models.attendance import UnifiedOvertimeRecord
from ..models.punch import PunchRecord
from ..models.personal_record import PersonalRecord, PersonalRecordSummary

logger = logging.getLogger(__name__)


class DataSyncService:
    """
    統一資料同步服務

    使用方式:
        ```python
        service = DataSyncService(session, settings)
        snapshot = service.sync_all()  # 首次抓取
        snapshot = service.sync_all()  # 使用快取
        snapshot = service.sync_all(force_refresh=True)  # 強制重新抓取
        ```
    """

    def __init__(self, session: Session, settings: Settings):
        """
        初始化資料同步服務

        Args:
            session: 已登入的 requests.Session
            settings: 應用程式設定
        """
        self.session = session
        self.settings = settings

        # 禁用 SSL 警告 (內部系統)
        if not self.settings.VERIFY_SSL:
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

        # HTML 解析器 (依賴注入)
        self.attendance_parser = AttendanceParser()
        self.personal_record_parser = PersonalRecordParser()

        # 快取
        self._cache: Optional[AttendanceSnapshot] = None
        self._cache_timestamp: Optional[datetime] = None

        logger.info("DataSyncService 初始化完成")

    def sync_all(self, force_refresh: bool = False) -> AttendanceSnapshot:
        """
        全量同步所有出勤資料

        執行流程:
        1. 檢查快取是否有效 (若非強制重新整理)
        2. 平行抓取出勤頁面與個人記錄頁面
        3. 解析 HTML 為資料模型
        4. 整合異常記錄與個人記錄
        5. 計算統計資料
        6. 更新快取

        Args:
            force_refresh: 是否強制重新抓取 (忽略快取)

        Returns:
            AttendanceSnapshot: 完整的出勤資料快照

        Raises:
            RequestException: HTTP 請求失敗
            Exception: 資料解析失敗
        """
        # 快取檢查
        if not force_refresh and self._is_cache_valid():
            logger.info("使用快取資料 (age: %.1f 秒)", self._get_cache_age())
            return self._cache

        logger.info("開始全量同步資料...")

        try:
            # 平行抓取頁面 (優化: 異常記錄已在出勤頁面,只需 2 次請求)
            html_pages = self._fetch_all_pages_parallel()

            # 解析資料
            attendance_html = html_pages["attendance"]
            personal_html = html_pages["personal"]

            # 解析出勤頁面 (tabs-1)
            punch_records = self.attendance_parser.parse_punch_records(attendance_html)
            leave_records = self.attendance_parser.parse_leave_records(attendance_html)
            quota = self.attendance_parser.parse_quota(attendance_html)

            # 解析異常記錄 (tabs-2, 但在同一個 HTML 中)
            anomaly_records = self.attendance_parser.parse_anomaly_records(
                attendance_html
            )

            # 解析個人記錄
            personal_records = self.personal_record_parser.parse_records(personal_html)

            # 整合資料為統一模型
            unified_records = self._merge_overtime_data(
                anomaly_records, personal_records
            )

            # 計算統計資料
            start_date, end_date = self._calculate_date_range(unified_records)
            statistics = self._calculate_statistics(
                unified_records, start_date, end_date
            )

            # 建立快照
            snapshot = AttendanceSnapshot(
                start_date=start_date,
                end_date=end_date,
                fetched_at=datetime.now(),
                punch_records=punch_records,
                leave_records=leave_records,
                quota=quota,
                unified_records=unified_records,
                statistics=statistics,
            )

            # 更新快取
            self._cache = snapshot
            self._cache_timestamp = datetime.now()

            logger.info(
                "全量同步完成: %d 筆記錄, 耗時 %.2f 秒",
                len(unified_records),
                (datetime.now() - snapshot.fetched_at).total_seconds(),
            )

            return snapshot

        except Timeout as e:
            logger.error("資料同步逾時: %s", str(e))
            # 嘗試使用過期快取
            if self._cache:
                logger.warning("使用過期快取資料 (age: %.1f 秒)", self._get_cache_age())
                return self._cache
            raise

        except RequestException as e:
            logger.error("資料同步失敗 (網路錯誤): %s", str(e))
            # 嘗試使用過期快取
            if self._cache:
                logger.warning("使用過期快取資料 (age: %.1f 秒)", self._get_cache_age())
                return self._cache
            raise

        except Exception as e:
            logger.error("資料同步失敗 (未知錯誤): %s", str(e), exc_info=True)
            raise

    def sync_overtime_status(self) -> List[UnifiedOvertimeRecord]:
        """
        增量同步加班狀態

        僅更新已申請記錄的狀態,不重新抓取出勤資料。
        適用場景: 申請加班後檢查審核狀態

        Returns:
            List[UnifiedOvertimeRecord]: 更新後的統一記錄列表

        Notes:
            - 若無快取,會執行完整同步
            - 只抓取個人記錄頁面 (1 次 HTTP 請求)
        """
        if not self._cache:
            logger.warning("無快取資料,執行完整同步")
            return self.sync_all().unified_records

        logger.info("開始增量同步加班狀態...")

        try:
            # 僅抓取個人記錄頁面
            personal_html = self._fetch_personal_record_page()
            personal_records = self.personal_record_parser.parse_records(personal_html)

            # 建立日期索引
            personal_by_date = {r["date"]: r for r in personal_records}

            # 更新快取中的狀態
            updated_count = 0
            for record in self._cache.unified_records:
                personal = personal_by_date.get(record.date)
                if personal:
                    record.submitted = True
                    record.submission_status = personal.get("status")
                    record.monthly_total = personal.get("monthly_total")
                    record.quarterly_total = personal.get("quarterly_total")
                    updated_count += 1

            logger.info("增量同步完成: 更新 %d 筆記錄", updated_count)
            return self._cache.unified_records

        except Exception as e:
            logger.error("增量同步失敗: %s", str(e))
            # 返回快取資料
            return self._cache.unified_records

    def clear_cache(self):
        """清除快取"""
        self._cache = None
        self._cache_timestamp = None
        logger.info("快取已清除")

    # === 適配器方法 (向後相容) ===

    def get_attendance_records(self) -> List[Dict[str, str]]:
        """
        適配器: 返回舊版出勤記錄格式

        資料來源策略變更:
        - 舊版: 使用 punch_records 計算加班時數 (跨月份,邏輯複雜)
        - 新版: 使用 unified_records (has_anomaly=True) 官方異常清單

        優點:
        - ✅ 責任分離: 網頁判斷異常,我們只負責呈現
        - ✅ 資料一致性: 與網頁 gvWeb012 完全一致
        - ✅ 無需翻頁: 異常清單已過濾本月資料

        Returns:
            List[Dict]: [{'date': 'YYYY/MM/DD', 'time_range': 'HH:MM:SS~HH:MM:SS'}]
        """
        snapshot = self.sync_all()
        records = []

        # 使用異常記錄 (has_anomaly=True)
        anomaly_records = [r for r in snapshot.unified_records if r.has_anomaly]

        for record in anomaly_records:
            if record.punch_start and record.punch_end:
                records.append(
                    {
                        "date": record.date,
                        "time_range": f"{record.punch_start}~{record.punch_end}",
                    }
                )

        logger.debug("返回 %d 筆異常記錄 (來自 gvWeb012)", len(records))
        return records

    def get_personal_records(
        self,
    ) -> Tuple[List[PersonalRecord], PersonalRecordSummary]:
        """
        適配器: 返回舊版個人記錄格式

        Returns:
            Tuple: (個人記錄列表, 統計摘要)
        """
        snapshot = self.sync_all()
        submitted = [r for r in snapshot.unified_records if r.submitted]

        # 轉換為 PersonalRecord
        records = []
        for r in submitted:
            # Debug log
            logger.debug(
                "轉換個人記錄 %s: reported_hours=%s, monthly=%s, quarterly=%s, type=%s",
                r.date,
                r.reported_overtime_hours,
                r.monthly_total,
                r.quarterly_total,
                r.submission_type,
            )

            record = PersonalRecord(
                date=r.date,
                content=r.submission_content or "",
                status=r.submission_status or "",
                overtime_hours=r.reported_overtime_hours or 0.0,
                monthly_total=r.monthly_total or 0.0,
                quarterly_total=r.quarterly_total or 0.0,
                report_type=r.submission_type or "",
            )
            records.append(record)

        # 計算統計摘要
        if records:
            summary = PersonalRecordSummary(
                total_records=len(records),
                total_overtime_hours=sum(r.overtime_hours for r in records),
                average_overtime_hours=sum(r.overtime_hours for r in records)
                / len(records),
                max_overtime_hours=max(r.overtime_hours for r in records),
                current_month_total=records[-1].monthly_total,
                current_quarter_total=records[-1].quarterly_total,
            )
        else:
            summary = PersonalRecordSummary(
                total_records=0,
                total_overtime_hours=0.0,
                average_overtime_hours=0.0,
                max_overtime_hours=0.0,
                current_month_total=0.0,
                current_quarter_total=0.0,
            )

        return records, summary

    def get_punch_records(self) -> List[PunchRecord]:
        """
        適配器: 返回打卡記錄列表 (供新增的打卡記錄分頁使用)

        資料來源: snapshot.punch_records (來自 gvNotes005 第一頁)

        Returns:
            List[PunchRecord]: 打卡記錄列表,按日期排序
        """
        snapshot = self.sync_all()
        return sorted(snapshot.punch_records, key=lambda r: r.date, reverse=True)

    # === 私有方法 ===

    def _is_cache_valid(self) -> bool:
        """
        檢查快取是否有效

        Returns:
            bool: 快取有效則返回 True
        """
        if not self._cache or not self._cache_timestamp:
            return False

        max_age = getattr(self.settings, "CACHE_DURATION_SECONDS", 300)
        age = (datetime.now() - self._cache_timestamp).total_seconds()
        return age < max_age

    def _get_cache_age(self) -> float:
        """取得快取年齡 (秒)"""
        if not self._cache_timestamp:
            return 0.0
        return (datetime.now() - self._cache_timestamp).total_seconds()

    def _fetch_all_pages_parallel(self) -> Dict[str, str]:
        """
        平行抓取所有頁面

        優化策略:
        - 異常記錄已包含在出勤頁面 (tabs-2)
        - 只需抓取 2 個頁面: 出勤 + 個人記錄
        - 使用 ThreadPoolExecutor 平行執行

        Returns:
            Dict: {'attendance': HTML, 'personal': HTML}
        """
        with ThreadPoolExecutor(max_workers=2) as executor:
            future_attendance = executor.submit(self._fetch_attendance_page)
            future_personal = executor.submit(self._fetch_personal_record_page)

            results = {
                "attendance": future_attendance.result(),
                "personal": future_personal.result(),
            }

            # 異常記錄使用相同的 HTML (在 tabs-2)
            results["anomaly"] = results["attendance"]

        return results

    def _fetch_attendance_page(self) -> str:
        """抓取出勤頁面 (FW99001Z.aspx)

        包含:
        - tabs-1: 打卡記錄 (gvNotes005) - 僅第一頁
        - tabs-2: 出勤異常 (gvWeb012) - 完整清單
        - tabs-3: 假別統計 (gvNotes011)

        Note: 不進行翻頁,僅抓取第一頁即可滿足需求
        """
        url = f"{self.settings.SSP_BASE_URL}{self.settings.ATTENDANCE_URL}"
        response = self.session.get(
            url, timeout=self.settings.REQUEST_TIMEOUT, verify=self.settings.VERIFY_SSL
        )
        response.raise_for_status()
        return response.text

    def _fetch_personal_record_page(self) -> str:
        """抓取個人記錄頁面 (FW21003Z.aspx)"""
        url = f"{self.settings.SSP_BASE_URL}{self.settings.PERSONAL_RECORD_URL}"
        response = self.session.get(
            url, timeout=self.settings.REQUEST_TIMEOUT, verify=self.settings.VERIFY_SSL
        )
        response.raise_for_status()
        return response.text

    def _merge_overtime_data(
        self, anomaly_records: List[Dict], personal_records: List[Dict]
    ) -> List[UnifiedOvertimeRecord]:
        """
        合併異常記錄與個人記錄為統一模型

        整合策略:
        - 以異常記錄為基礎 (所有需要申報的加班)
        - 匹配個人記錄 (已申報狀態)
        - 補充未在異常清單中的個人記錄 (手動申請的調休等)

        Args:
            anomaly_records: 異常記錄列表 (來自 gvWeb012)
            personal_records: 個人記錄列表 (來自 gvFlow211)

        Returns:
            List[UnifiedOvertimeRecord]: 整合後的統一記錄
        """
        # 建立日期索引
        personal_by_date = {r["date"]: r for r in personal_records}
        anomaly_dates = {r["date"] for r in anomaly_records}

        unified = []

        # 1. 處理異常記錄
        for anomaly in anomaly_records:
            date = anomaly["date"]
            personal = personal_by_date.get(date)

            # 解析 punch_range (格式: "09:00:15~19:31:09")
            punch_start = None
            punch_end = None
            if anomaly.get("punch_range"):
                punch_range = anomaly["punch_range"].strip()
                if "~" in punch_range:
                    times = punch_range.split("~")
                    if len(times) == 2:
                        punch_start = times[0].strip()
                        punch_end = times[1].strip()

            record = UnifiedOvertimeRecord(
                date=date,
                punch_start=punch_start,
                punch_end=punch_end,
                calculated_overtime_hours=anomaly.get("overtime_hours", 0.0),
                has_anomaly=True,
                anomaly_description=anomaly.get("description"),
                submitted=personal is not None,
                submission_content=personal.get("content") if personal else None,
                submission_status=personal.get("status") if personal else None,
                submission_type=personal.get("report_type") if personal else None,
                reported_overtime_hours=(
                    personal.get("overtime_hours") if personal else None
                ),
                monthly_total=personal.get("monthly_total") if personal else None,
                quarterly_total=personal.get("quarterly_total") if personal else None,
            )

            # Debug log
            if personal:
                logger.debug(
                    "合併記錄 %s: 類型=%s, 時數=%s, 月累計=%s, 季累計=%s",
                    date,
                    personal.get("report_type"),
                    personal.get("overtime_hours"),
                    personal.get("monthly_total"),
                    personal.get("quarterly_total"),
                )
            unified.append(record)

        # 2. 補充個人記錄中但不在異常清單的記錄 (如手動申請調休)
        for personal in personal_records:
            if personal["date"] not in anomaly_dates:
                record = UnifiedOvertimeRecord(
                    date=personal["date"],
                    punch_start=None,
                    punch_end=None,
                    calculated_overtime_hours=0.0,
                    has_anomaly=False,
                    anomaly_description=None,
                    submitted=True,
                    submission_content=personal.get("content"),
                    submission_status=personal.get("status"),
                    submission_type=personal.get("report_type"),
                    reported_overtime_hours=personal.get("overtime_hours", 0.0),
                    monthly_total=personal.get("monthly_total"),
                    quarterly_total=personal.get("quarterly_total"),
                )

                # Debug log
                logger.debug(
                    "補充個人記錄 %s: 類型=%s, 時數=%s, 月累計=%s, 季累計=%s",
                    personal["date"],
                    personal.get("report_type"),
                    personal.get("overtime_hours"),
                    personal.get("monthly_total"),
                    personal.get("quarterly_total"),
                )

                unified.append(record)

        # 依日期排序
        unified.sort(key=lambda x: x.date, reverse=True)

        logger.info(
            "資料整合完成: %d 筆異常記錄, %d 筆已申報",
            len(anomaly_records),
            sum(1 for r in unified if r.submitted),
        )

        return unified

    def _calculate_date_range(
        self, records: List[UnifiedOvertimeRecord]
    ) -> Tuple[str, str]:
        """
        計算記錄的日期範圍

        Returns:
            Tuple[str, str]: (start_date, end_date)
        """
        if not records:
            today = datetime.now().strftime("%Y/%m/%d")
            return today, today

        dates = [r.date for r in records]
        return min(dates), max(dates)

    def _calculate_statistics(
        self, records: List[UnifiedOvertimeRecord], start_date: str, end_date: str
    ) -> OvertimeStatistics:
        """
        計算加班統計資料

        Args:
            records: 統一記錄列表
            start_date: 開始日期
            end_date: 結束日期

        Returns:
            OvertimeStatistics: 統計資料
        """
        if not records:
            return OvertimeStatistics(start_date=start_date, end_date=end_date)

        # 計算各項統計
        total_overtime_hours = sum(r.calculated_overtime_hours for r in records)
        submitted_records = [r for r in records if r.submitted]
        submitted_overtime_hours = sum(
            r.reported_overtime_hours
            for r in submitted_records
            if r.reported_overtime_hours
        )
        pending_records = [r for r in records if not r.submitted]
        pending_overtime_hours = sum(
            r.calculated_overtime_hours for r in pending_records
        )

        workdays_with_overtime = len(
            [r for r in records if r.calculated_overtime_hours > 0]
        )
        anomaly_days = len([r for r in records if r.has_anomaly])

        # 計算不一致筆數 (計算時數與申報時數差異 > 0.1)
        discrepancy_count = sum(
            1
            for r in submitted_records
            if r.reported_overtime_hours
            and abs(r.calculated_overtime_hours - r.reported_overtime_hours) > 0.1
        )

        return OvertimeStatistics(
            start_date=start_date,
            end_date=end_date,
            total_overtime_hours=total_overtime_hours,
            submitted_overtime_hours=submitted_overtime_hours,
            pending_overtime_hours=pending_overtime_hours,
            total_days=len(records),
            workdays_with_overtime=workdays_with_overtime,
            pending_submission_days=len(pending_records),
            anomaly_days=anomaly_days,
            incomplete_punch_days=0,  # TODO: 實作打卡不完整檢測
            discrepancy_count=discrepancy_count,
        )
