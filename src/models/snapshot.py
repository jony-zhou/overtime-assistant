"""出勤快照與統計資料模型"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional

from .attendance import UnifiedOvertimeRecord
from .punch import PunchRecord
from .leave import LeaveRecord
from .quota import AttendanceQuota


@dataclass
class OvertimeStatistics:
    """加班統計資料
    
    彙整特定時間範圍的加班數據，用於報表與儀表板顯示。
    """

    # === 時間範圍 ===
    start_date: str  # YYYY/MM/DD
    end_date: str  # YYYY/MM/DD

    # === 加班統計 ===
    total_overtime_hours: float = 0.0  # 總加班時數
    submitted_overtime_hours: float = 0.0  # 已申報時數
    pending_overtime_hours: float = 0.0  # 待申報時數

    # === 天數統計 ===
    total_days: int = 0  # 總天數
    workdays_with_overtime: int = 0  # 有加班的工作日
    pending_submission_days: int = 0  # 待申報天數

    # === 異常統計 ===
    anomaly_days: int = 0  # 異常天數
    incomplete_punch_days: int = 0  # 打卡不完整天數

    # === 資料一致性 ===
    discrepancy_count: int = 0  # 計算與申報時數不一致筆數

    @property
    def average_overtime_per_day(self) -> float:
        """平均每日加班時數"""
        if self.workdays_with_overtime == 0:
            return 0.0
        return self.total_overtime_hours / self.workdays_with_overtime

    @property
    def submission_rate(self) -> float:
        """申報率 (已申報/總加班時數)"""
        if self.total_overtime_hours == 0:
            return 1.0
        return self.submitted_overtime_hours / self.total_overtime_hours

    @property
    def has_pending_work(self) -> bool:
        """是否有待處理工作 (待申報或異常)"""
        return self.pending_submission_days > 0 or self.anomaly_days > 0

    def __str__(self) -> str:
        """字串表示"""
        return (
            f"OvertimeStatistics("
            f"{self.start_date}~{self.end_date} | "
            f"總計 {self.total_overtime_hours}h | "
            f"已報 {self.submitted_overtime_hours}h | "
            f"待報 {self.pending_overtime_hours}h | "
            f"申報率 {self.submission_rate:.1%}"
            f")"
        )


@dataclass
class AttendanceSnapshot:
    """出勤資料快照
    
    包含特定時間範圍的完整出勤資料，用於:
    - DataSyncService 快取
    - UI 層資料展示
    - 報表產生
    """

    # === 時間範圍 ===
    start_date: str  # YYYY/MM/DD
    end_date: str  # YYYY/MM/DD
    fetched_at: datetime = field(default_factory=datetime.now)  # 資料抓取時間

    # === 原始資料 (Layer 1) ===
    punch_records: List[PunchRecord] = field(default_factory=list)
    leave_records: List[LeaveRecord] = field(default_factory=list)
    quota: Optional[AttendanceQuota] = None

    # === 整合資料 (Layer 2) ===
    unified_records: List[UnifiedOvertimeRecord] = field(default_factory=list)

    # === 統計資料 (Layer 3) ===
    statistics: Optional[OvertimeStatistics] = None

    def is_fresh(self, max_age_seconds: int = 300) -> bool:
        """檢查快取是否新鮮 (預設 5 分鐘)"""
        age = (datetime.now() - self.fetched_at).total_seconds()
        return age < max_age_seconds

    @property
    def record_count(self) -> int:
        """總記錄數"""
        return len(self.unified_records)

    @property
    def has_data(self) -> bool:
        """是否包含資料"""
        return len(self.unified_records) > 0

    def get_record_by_date(self, date: str) -> Optional[UnifiedOvertimeRecord]:
        """依日期取得記錄
        
        Args:
            date: YYYY/MM/DD 格式
            
        Returns:
            找到的記錄，若無則回傳 None
        """
        for record in self.unified_records:
            if record.date == date:
                return record
        return None

    def get_pending_records(self) -> List[UnifiedOvertimeRecord]:
        """取得所有待申報記錄"""
        return [r for r in self.unified_records if r.needs_submission]

    def get_anomaly_records(self) -> List[UnifiedOvertimeRecord]:
        """取得所有異常記錄"""
        return [r for r in self.unified_records if r.has_anomaly]

    def get_submitted_records(self) -> List[UnifiedOvertimeRecord]:
        """取得所有已申報記錄"""
        return [r for r in self.unified_records if r.submitted]

    def __str__(self) -> str:
        """字串表示"""
        age = (datetime.now() - self.fetched_at).total_seconds()
        freshness = "新鮮" if self.is_fresh() else "過期"
        return (
            f"AttendanceSnapshot("
            f"{self.start_date}~{self.end_date} | "
            f"{self.record_count} 筆 | "
            f"{freshness} ({age:.0f}秒前)"
            f")"
        )
