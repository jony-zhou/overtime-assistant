"""出勤記錄資料模型"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class AttendanceRecord:
    """出勤記錄"""

    date: str  # 格式: YYYY/MM/DD
    start_time: str  # 格式: HH:MM:SS
    end_time: str  # 格式: HH:MM:SS
    overtime_hours: float = 0.0
    total_minutes: int = 0

    @property
    def date_obj(self) -> datetime:
        """轉換為 datetime 物件"""
        return datetime.strptime(self.date, "%Y/%m/%d")

    @property
    def start_datetime(self) -> datetime:
        """開始時間 datetime 物件"""
        return datetime.strptime(f"{self.date} {self.start_time}", "%Y/%m/%d %H:%M:%S")

    @property
    def end_datetime(self) -> datetime:
        """結束時間 datetime 物件"""
        return datetime.strptime(f"{self.date} {self.end_time}", "%Y/%m/%d %H:%M:%S")

    def __hash__(self):
        """用於去重"""
        return hash(f"{self.date}_{self.start_time}_{self.end_time}")


@dataclass
class UnifiedOvertimeRecord:
    """
    統一加班記錄 (整合多資料來源)

    整合以下資料:
    - 異常清單 (gvWeb012): 打卡時間、計算的加班時數、異常說明
    - 個人記錄 (gvFlow211): 申報狀態、申報內容、累計時數

    使用場景:
    - DataSyncService 的核心資料模型
    - UI 層統一展示介面
    - 報表產生
    """

    # === 基本資訊 ===
    date: str  # YYYY/MM/DD

    # === 打卡記錄 (來自異常清單) ===
    punch_start: Optional[str] = None  # 上班打卡時間 (HH:MM:SS)
    punch_end: Optional[str] = None  # 下班打卡時間 (HH:MM:SS)
    calculated_overtime_hours: float = 0.0  # 系統計算的加班時數

    # === 異常資訊 (來自異常清單) ===
    has_anomaly: bool = False  # 是否有異常
    anomaly_description: Optional[str] = None  # 異常說明

    # === 申報資訊 (來自個人記錄) ===
    submitted: bool = False  # 是否已申報
    submission_content: Optional[str] = None  # 加班內容
    submission_status: Optional[str] = None  # 簽核狀態 (簽核中/完成)
    submission_type: Optional[str] = None  # 申報類型 (加班/調休)
    reported_overtime_hours: Optional[float] = None  # 申報的加班時數

    # === 統計資訊 (來自個人記錄) ===
    monthly_total: Optional[float] = None  # 當月累計
    quarterly_total: Optional[float] = None  # 當季累計

    @property
    def needs_submission(self) -> bool:
        """是否需要申報"""
        return (
            self.has_anomaly
            and not self.submitted
            and self.calculated_overtime_hours > 0
        )

    @property
    def is_pending_approval(self) -> bool:
        """是否待審核"""
        return self.submitted and self.submission_status == "簽核中"

    @property
    def is_approved(self) -> bool:
        """是否已核准"""
        return self.submitted and self.submission_status == "完成"

    @property
    def has_discrepancy(self) -> bool:
        """計算時數與申報時數是否不一致"""
        if not self.submitted or not self.reported_overtime_hours:
            return False
        return abs(self.calculated_overtime_hours - self.reported_overtime_hours) > 0.1

    @property
    def time_range(self) -> str:
        """時間範圍字串"""
        if self.punch_start and self.punch_end:
            return f"{self.punch_start}~{self.punch_end}"
        return "無打卡記錄"

    def __str__(self) -> str:
        """字串表示"""
        status = []
        if self.has_anomaly:
            status.append("異常")
        if self.submitted:
            status.append(f"已申報({self.submission_status})")
        else:
            status.append("待申報")

        status_str = "|".join(status)
        return f"{self.date} {self.time_range} {self.calculated_overtime_hours}h [{status_str}]"
