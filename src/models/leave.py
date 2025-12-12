"""假別記錄資料模型"""

from dataclasses import dataclass


@dataclass
class LeaveRecord:
    """
    假別記錄 (從 FW99001Z.aspx#tabs-1 的 gvNotes011 解析)

    表示員工的請假記錄 (特休、病假、事假等)
    """

    leave_type: str  # 假別名稱 (如「特休」、「病假」)
    days: int = 0  # 請假天數
    hours: int = 0  # 請假小時數

    def __str__(self) -> str:
        if self.hours > 0:
            return f"{self.leave_type}: {self.days} 天 {self.hours} 小時"
        return f"{self.leave_type}: {self.days} 天"

    @property
    def total_hours(self) -> float:
        """總小時數 (假設 1 天 = 8 小時)"""
        return (self.days * 8) + self.hours

    @property
    def is_annual_leave(self) -> bool:
        """是否為特休"""
        return "特休" in self.leave_type

    @property
    def is_sick_leave(self) -> bool:
        """是否為病假"""
        return "病假" in self.leave_type

    @property
    def is_personal_leave(self) -> bool:
        """是否為事假"""
        return "事假" in self.leave_type
