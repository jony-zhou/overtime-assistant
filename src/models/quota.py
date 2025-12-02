"""剩餘額度資料模型"""

from dataclasses import dataclass


@dataclass
class AttendanceQuota:
    """
    剩餘額度 (從 FW99001Z.aspx#tabs-1 的 dvNotes019 解析)

    表示員工的特休、調修剩餘額度
    """

    annual_leave: int = 0  # 特休剩餘天數
    compensatory_leave: int = 0  # 調修剩餘天數
    overtime_threshold_minutes: int = 0  # 未達加班換修最低申請時限 (分鐘)

    def __str__(self) -> str:
        threshold_hours = self.overtime_threshold_minutes / 60
        return (
            f"特休剩餘: {self.annual_leave} 天 | "
            f"調修剩餘: {self.compensatory_leave} 天 | "
            f"未達換修門檻: {threshold_hours:.1f} 小時"
        )

    @property
    def overtime_threshold_hours(self) -> float:
        """未達換修門檻 (小時)"""
        return self.overtime_threshold_minutes / 60.0

    @property
    def has_annual_leave(self) -> bool:
        """是否還有特休額度"""
        return self.annual_leave > 0

    @property
    def has_compensatory_leave(self) -> bool:
        """是否還有調修額度"""
        return self.compensatory_leave > 0
