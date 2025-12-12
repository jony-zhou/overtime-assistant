"""HTML 解析器套件

職責: 從 SSP 系統 HTML 中提取結構化資料
遵循 SRP (Single Responsibility Principle) - 解析邏輯與業務邏輯分離
"""

from .attendance_parser import AttendanceParser
from .personal_record_parser import PersonalRecordParser

__all__ = [
    "AttendanceParser",
    "PersonalRecordParser",
]
