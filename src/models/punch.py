"""打卡記錄資料模型"""

from dataclasses import dataclass
from typing import List


@dataclass
class PunchRecord:
    """
    打卡記錄 (從 FW99001Z.aspx#tabs-1 解析)
    
    表示單一日期的所有打卡時間
    """
    
    date: str  # 打卡日期 (YYYY/MM/DD)
    punch_times: List[str]  # 打卡時間列表 (HH:MM:SS 格式)
    
    def __str__(self) -> str:
        times_str = ", ".join(self.punch_times) if self.punch_times else "無打卡記錄"
        return f"{self.date}: {times_str}"
    
    @property
    def has_punch(self) -> bool:
        """是否有打卡記錄"""
        return bool(self.punch_times)
    
    @property
    def punch_count(self) -> int:
        """打卡次數"""
        return len(self.punch_times)
