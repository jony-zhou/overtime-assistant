"""
測試模式假數據生成器
用於開發和測試，不需要實際連線
"""

from datetime import datetime, timedelta
from typing import List
import random

from src.models import (
    AttendanceRecord,
    PersonalRecord,
    PersonalRecordSummary,
    OvertimeReport,
)
from src.models.punch import PunchRecord
from src.models.overtime_submission import OvertimeSubmissionRecord, SubmittedRecord


class MockDataGenerator:
    """假數據生成器"""

    @staticmethod
    def generate_attendance_records(days: int = 30) -> List[AttendanceRecord]:
        """
        生成出勤記錄假數據

        Args:
            days: 生成最近幾天的數據

        Returns:
            出勤記錄列表
        """
        records = []
        today = datetime.now()

        for i in range(days):
            date = today - timedelta(days=i)
            # 只生成工作日
            if date.weekday() < 5:  # 週一到週五
                # 隨機決定是否有加班
                has_overtime = random.random() > 0.3

                if has_overtime:
                    start_time = "08:30:00"
                    # 隨機加班時數 (1-4小時)
                    overtime_hours = round(random.uniform(1.0, 4.0), 1)
                    base_end = datetime.strptime("17:30:00", "%H:%M:%S")
                    actual_end = base_end + timedelta(hours=overtime_hours)
                    end_time = actual_end.strftime("%H:%M:%S")

                    records.append(
                        AttendanceRecord(
                            date=date.strftime("%Y/%m/%d"),
                            start_time=start_time,
                            end_time=end_time,
                            overtime_hours=overtime_hours,
                            total_minutes=int(overtime_hours * 60),
                        )
                    )

        return records

    @staticmethod
    def generate_personal_records(count: int = 20) -> List[PersonalRecord]:
        """
        生成個人加班記錄假數據

        Args:
            count: 生成記錄數量

        Returns:
            個人記錄列表
        """
        records = []
        today = datetime.now()
        monthly_total = 0.0
        quarterly_total = 0.0

        statuses = ["簽核完成", "簽核中", "已結案"]
        contents = [
            "系統開發與測試",
            "緊急問題修復",
            "版本發布作業",
            "客戶需求調整",
            "資料庫維護",
            "文件整理",
            "會議準備",
        ]

        for i in range(count):
            date = today - timedelta(days=i * 2)
            overtime_hours = round(random.uniform(1.0, 4.0), 1)
            monthly_total += overtime_hours
            quarterly_total += overtime_hours

            records.append(
                PersonalRecord(
                    date=date.strftime("%Y/%m/%d"),
                    content=random.choice(contents),
                    status=random.choice(statuses),
                    overtime_hours=overtime_hours,
                    monthly_total=monthly_total,
                    quarterly_total=quarterly_total,
                    report_type="加班",
                )
            )

        return records

    @staticmethod
    def generate_personal_summary(
        records: List[PersonalRecord],
    ) -> PersonalRecordSummary:
        """
        生成個人記錄統計摘要

        Args:
            records: 個人記錄列表

        Returns:
            統計摘要
        """
        if not records:
            return PersonalRecordSummary()

        total_hours = sum(r.overtime_hours for r in records)
        return PersonalRecordSummary(
            total_records=len(records),
            total_overtime_hours=total_hours,
            average_overtime_hours=total_hours / len(records),
            max_overtime_hours=max(r.overtime_hours for r in records),
            current_month_total=records[0].monthly_total if records else 0.0,
            current_quarter_total=records[0].quarterly_total if records else 0.0,
        )

    @staticmethod
    def generate_punch_records(days: int = 30) -> List[PunchRecord]:
        """
        生成打卡記錄假數據

        Args:
            days: 生成最近幾天的數據

        Returns:
            打卡記錄列表
        """
        records = []
        today = datetime.now()

        for i in range(days):
            date = today - timedelta(days=i)
            # 只生成工作日
            if date.weekday() < 5:  # 週一到週五
                punch_times = []
                
                # 上班打卡
                clock_in = datetime.strptime("08:30:00", "%H:%M:%S")
                clock_in += timedelta(minutes=random.randint(-10, 10))
                punch_times.append(clock_in.strftime("%H:%M:%S"))

                # 下班打卡
                clock_out = datetime.strptime("17:30:00", "%H:%M:%S")
                has_overtime = random.random() > 0.3
                if has_overtime:
                    clock_out += timedelta(hours=random.uniform(1.0, 4.0))
                punch_times.append(clock_out.strftime("%H:%M:%S"))

                records.append(
                    PunchRecord(
                        date=date.strftime("%Y/%m/%d"),
                        punch_times=punch_times,
                    )
                )

        return records

    @staticmethod
    def generate_overtime_report(records: List[AttendanceRecord] = None) -> OvertimeReport:
        """
        生成加班報表假數據

        Args:
            records: 出勤記錄列表，如果為 None 則生成新的

        Returns:
            加班報表
        """
        if records is None:
            records = MockDataGenerator.generate_attendance_records(30)

        return OvertimeReport(
            records=records,
            generated_at=datetime.now(),
        )

    @staticmethod
    def generate_overtime_submissions(count: int = 15) -> List[OvertimeSubmissionRecord]:
        """
        生成加班申報記錄假數據

        Args:
            count: 生成記錄數量

        Returns:
            申報記錄列表
        """
        submissions = []
        today = datetime.now()

        for i in range(count):
            date = today - timedelta(days=i * 2)
            overtime_hours = round(random.uniform(1.0, 4.0), 1)

            # 隨機狀態
            if i < 3:
                status = None  # 未申報
                submitted = False
            else:
                status = random.choice(["簽核中", "簽核完成", "已結案"])
                submitted = True

            submissions.append(
                OvertimeSubmissionRecord(
                    date=date.strftime("%Y/%m/%d"),
                    description=f"測試加班內容 {i + 1}" if submitted else "",
                    overtime_hours=overtime_hours,
                    is_overtime=True,
                    is_selected=not submitted,  # 未申報的預設勾選
                    submitted_status=status,
                )
            )

        return submissions
