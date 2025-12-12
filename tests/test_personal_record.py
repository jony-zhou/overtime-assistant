"""個人記錄相關功能測試"""

import pytest
from src.models.personal_record import PersonalRecord, PersonalRecordSummary


class TestPersonalRecord:
    """個人記錄資料模型測試"""

    def test_personal_record_creation(self):
        """測試建立個人記錄"""
        record = PersonalRecord(
            date="2025/11/01",
            content="加班作業",
            status="通過",
            overtime_hours=2.5,
            monthly_total=10.0,
            quarterly_total=30.0,
            report_type="是",
        )

        assert record.date == "2025/11/01"
        assert record.content == "加班作業"
        assert record.status == "通過"
        assert record.overtime_hours == 2.5
        assert record.monthly_total == 10.0
        assert record.quarterly_total == 30.0
        assert record.report_type == "是"

    def test_personal_record_hours_precision(self):
        """測試時數精確度"""
        record = PersonalRecord(
            date="2025/11/01",
            content="加班",
            status="通過",
            overtime_hours=1.234567,
            monthly_total=10.123456,
            quarterly_total=30.987654,
            report_type="是",
        )

        # 驗證可以儲存精確值
        assert record.overtime_hours == 1.234567
        assert record.monthly_total == 10.123456
        assert record.quarterly_total == 30.987654


class TestPersonalRecordSummary:
    """個人記錄摘要測試"""

    def test_summary_creation(self):
        """測試建立摘要"""
        summary = PersonalRecordSummary(
            total_records=10,
            total_overtime_hours=25.5,
            average_overtime_hours=2.55,
            max_overtime_hours=5.0,
            current_month_total=10.0,
            current_quarter_total=25.5,
        )

        assert summary.total_records == 10
        assert summary.total_overtime_hours == 25.5
        assert summary.average_overtime_hours == 2.55
        assert summary.max_overtime_hours == 5.0
        assert summary.current_month_total == 10.0
        assert summary.current_quarter_total == 25.5

    def test_summary_with_zero_records(self):
        """測試零記錄摘要"""
        summary = PersonalRecordSummary(
            total_records=0,
            total_overtime_hours=0.0,
            average_overtime_hours=0.0,
            max_overtime_hours=0.0,
            current_month_total=0.0,
            current_quarter_total=0.0,
        )

        assert summary.total_records == 0
        assert summary.total_overtime_hours == 0.0
        assert summary.average_overtime_hours == 0.0

    def test_summary_calculations(self):
        """測試摘要計算邏輯"""
        # 模擬計算過程
        records_data = [{"hours": 2.5}, {"hours": 3.0}, {"hours": 1.5}, {"hours": 4.0}]

        total_hours = sum(r["hours"] for r in records_data)
        avg_hours = total_hours / len(records_data)
        max_hours = max(r["hours"] for r in records_data)

        summary = PersonalRecordSummary(
            total_records=len(records_data),
            total_overtime_hours=total_hours,
            average_overtime_hours=avg_hours,
            max_overtime_hours=max_hours,
            current_month_total=total_hours,
            current_quarter_total=total_hours,
        )

        assert summary.total_records == 4
        assert summary.total_overtime_hours == 11.0
        assert summary.average_overtime_hours == 2.75
        assert summary.max_overtime_hours == 4.0


class TestPersonalRecordIntegration:
    """個人記錄整合測試"""

    def test_multiple_records_aggregation(self):
        """測試多筆記錄聚合"""
        records = [
            PersonalRecord(
                date="2024/11/20",
                content="開發",
                status="核准",
                overtime_hours=2.5,
                monthly_total=2.5,
                quarterly_total=2.5,
                report_type="是",
            ),
            PersonalRecord(
                date="2024/11/21",
                content="測試",
                status="核准",
                overtime_hours=3.0,
                monthly_total=5.5,
                quarterly_total=5.5,
                report_type="是",
            ),
            PersonalRecord(
                date="2024/11/22",
                content="部署",
                status="核准",
                overtime_hours=1.5,
                monthly_total=7.0,
                quarterly_total=7.0,
                report_type="是",
            ),
        ]

        # 計算聚合值
        total_hours = sum(r.overtime_hours for r in records)
        avg_hours = total_hours / len(records)
        max_hours = max(r.overtime_hours for r in records)

        assert len(records) == 3
        assert total_hours == 7.0
        assert avg_hours == pytest.approx(2.33, rel=0.01)
        assert max_hours == 3.0

    def test_record_status_filtering(self):
        """測試記錄狀態篩選"""
        records = [
            PersonalRecord(
                date="2024/11/20",
                content="開發",
                status="核准",
                overtime_hours=2.5,
                monthly_total=2.5,
                quarterly_total=2.5,
                report_type="是",
            ),
            PersonalRecord(
                date="2024/11/21",
                content="測試",
                status="待核",
                overtime_hours=3.0,
                monthly_total=5.5,
                quarterly_total=5.5,
                report_type="否",
            ),
            PersonalRecord(
                date="2024/11/22",
                content="部署",
                status="核准",
                overtime_hours=1.5,
                monthly_total=7.0,
                quarterly_total=7.0,
                report_type="是",
            ),
        ]

        # 篩選已核准的記錄
        approved = [r for r in records if r.status == "核准"]
        pending = [r for r in records if r.status == "待核"]

        assert len(approved) == 2
        assert len(pending) == 1
        assert sum(r.overtime_hours for r in approved) == 4.0

    def test_monthly_quarterly_totals(self):
        """測試當月和當季累計"""
        records = [
            PersonalRecord(
                date="2024/11/01",
                content="開發",
                status="核准",
                overtime_hours=2.0,
                monthly_total=2.0,
                quarterly_total=2.0,
                report_type="是",
            ),
            PersonalRecord(
                date="2024/11/15",
                content="測試",
                status="核准",
                overtime_hours=3.0,
                monthly_total=5.0,
                quarterly_total=5.0,
                report_type="是",
            ),
            PersonalRecord(
                date="2024/11/25",
                content="部署",
                status="核准",
                overtime_hours=2.5,
                monthly_total=7.5,
                quarterly_total=7.5,
                report_type="是",
            ),
        ]

        # 驗證累計值遞增
        assert records[0].monthly_total == 2.0
        assert records[1].monthly_total == 5.0
        assert records[2].monthly_total == 7.5

        # 當月累計應等於當季累計（同一個月）
        for record in records:
            assert record.monthly_total == record.quarterly_total


class TestPersonalRecordEdgeCases:
    """個人記錄邊界情況測試"""

    def test_zero_hours_record(self):
        """測試零時數記錄"""
        record = PersonalRecord(
            date="2024/11/20",
            content="會議",
            status="核准",
            overtime_hours=0.0,
            monthly_total=0.0,
            quarterly_total=0.0,
            report_type="否",
        )

        assert record.overtime_hours == 0.0

    def test_large_hours_value(self):
        """測試大時數值"""
        record = PersonalRecord(
            date="2024/11/20",
            content="緊急專案",
            status="核准",
            overtime_hours=12.75,
            monthly_total=50.5,
            quarterly_total=150.25,
            report_type="是",
        )

        assert record.overtime_hours == 12.75
        assert record.monthly_total == 50.5

    def test_special_characters_in_content(self):
        """測試內容包含特殊字元"""
        record = PersonalRecord(
            date="2024/11/20",
            content="系統開發 & 測試 (含文件撰寫)",
            status="核准",
            overtime_hours=3.5,
            monthly_total=10.0,
            quarterly_total=25.0,
            report_type="是",
        )

        assert "系統開發 & 測試 (含文件撰寫)" in record.content

    def test_summary_with_single_record(self):
        """測試單筆記錄的摘要"""
        summary = PersonalRecordSummary(
            total_records=1,
            total_overtime_hours=3.5,
            average_overtime_hours=3.5,
            max_overtime_hours=3.5,
            current_month_total=3.5,
            current_quarter_total=3.5,
        )

        # 單筆記錄：平均值、最大值、總時數應相同
        assert summary.average_overtime_hours == summary.max_overtime_hours
        assert summary.average_overtime_hours == summary.total_overtime_hours
