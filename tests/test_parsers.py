"""測試 HTML 解析器"""

import pytest
from pathlib import Path
from src.parsers.attendance_parser import AttendanceParser
from src.parsers.personal_record_parser import PersonalRecordParser
from src.models.punch import PunchRecord
from src.models.leave import LeaveRecord
from src.models.quota import AttendanceQuota


@pytest.fixture
def fixtures_dir():
    """測試資料目錄"""
    return Path(__file__).parent / "fixtures"


@pytest.fixture
def attendance_html(fixtures_dir):
    """出勤頁面 HTML"""
    return (fixtures_dir / "attendance_page.html").read_text(encoding="utf-8")


@pytest.fixture
def anomaly_html(fixtures_dir):
    """異常頁面 HTML"""
    return (fixtures_dir / "anomaly_page.html").read_text(encoding="utf-8")


@pytest.fixture
def personal_record_html(fixtures_dir):
    """個人記錄頁面 HTML"""
    return (fixtures_dir / "personal_record_page.html").read_text(encoding="utf-8")


class TestAttendanceParser:
    """測試 AttendanceParser"""

    def test_parse_punch_records(self, attendance_html):
        """測試打卡記錄解析"""
        parser = AttendanceParser()
        records = parser.parse_punch_records(attendance_html)

        assert len(records) == 2

        # 驗證第一筆 (保持民國年格式)
        assert isinstance(records[0], PunchRecord)
        assert records[0].date == "114/12/01"
        assert len(records[0].punch_times) == 2
        assert "09:02:32" in records[0].punch_times
        assert "18:15:20" in records[0].punch_times

        # 驗證第二筆
        assert records[1].date == "114/12/02"
        assert "08:58:10" in records[1].punch_times
        assert "19:30:45" in records[1].punch_times

    def test_parse_leave_records(self, attendance_html):
        """測試假別記錄解析"""
        parser = AttendanceParser()
        records = parser.parse_leave_records(attendance_html)

        assert len(records) == 1

        record = records[0]
        assert isinstance(record, LeaveRecord)
        assert record.leave_type == "特休"
        assert record.days == 1
        assert record.hours == 0  # lblAbsenceHour 為 0

    def test_parse_quota(self, attendance_html):
        """測試額度解析"""
        parser = AttendanceParser()
        quota = parser.parse_quota(attendance_html)

        assert isinstance(quota, AttendanceQuota)
        assert quota.annual_leave == 15
        assert quota.compensatory_leave == 5
        assert quota.overtime_threshold_minutes == 90

    def test_parse_anomaly_records(self, anomaly_html):
        """測試異常記錄解析"""
        parser = AttendanceParser()
        records = parser.parse_anomaly_records(anomaly_html)

        assert len(records) == 2

        # 驗證第一筆 (保持民國年)
        assert records[0]["date"] == "114/12/01"
        assert records[0]["description"] == "加班:1.5小時"

        # 驗證第二筆
        assert records[1]["date"] == "114/12/02"
        assert records[1]["description"] == "加班:2.0小時"

    def test_parse_punch_records_empty(self):
        """測試空 HTML"""
        parser = AttendanceParser()
        records = parser.parse_punch_records("<html></html>")
        assert records == []

    def test_parse_quota_missing_fields(self):
        """測試缺少欄位的額度"""
        html = """
        <table id="ContentPlaceHolder1_dvNotes019">
            <tr><td>目前特休剩餘：10 天</td></tr>
        </table>
        """
        parser = AttendanceParser()
        quota = parser.parse_quota(html)

        assert quota.annual_leave == 10
        assert quota.compensatory_leave == 0
        assert quota.overtime_threshold_minutes == 0


class TestPersonalRecordParser:
    """測試 PersonalRecordParser"""

    def test_parse_records(self, personal_record_html):
        """測試個人記錄解析"""
        parser = PersonalRecordParser()
        records = parser.parse_records(personal_record_html)

        assert len(records) == 2

        # 驗證第一筆 (加班時數)
        record1 = records[0]
        assert record1["date"] == "114/12/01"
        assert record1["content"] == "系統開發"
        assert record1["report_type"] == "加班"
        assert record1["overtime_hours"] == 1.5  # 90 分鐘
        assert record1["monthly_total"] == 1.5
        assert record1["quarterly_total"] == 5.0
        assert record1["status"] == "簽核完成"

        # 驗證第二筆 (調休時數)
        record2 = records[1]
        assert record2["date"] == "114/12/02"
        assert record2["content"] == "測試作業"
        assert record2["report_type"] == "調休"
        assert record2["overtime_hours"] == 2.0  # 120 分鐘
        assert record2["monthly_total"] == 2.0
        assert record2["quarterly_total"] == 7.0
        assert record2["status"] == "簽核中"

    def test_parse_hours_minutes(self):
        """測試分鐘轉小時"""
        parser = PersonalRecordParser()

        # 分鐘格式
        assert parser._parse_hours("90") == 1.5
        assert parser._parse_hours("120") == 2.0
        assert parser._parse_hours("45") == 0.75

        # 小時格式
        assert parser._parse_hours("2.5") == 2.5
        assert parser._parse_hours("1.0") == 1.0

        # 異常格式
        assert parser._parse_hours("") == 0.0
        assert parser._parse_hours("  ") == 0.0  # 純空白
        assert parser._parse_hours("invalid") == 0.0

    def test_parse_compensatory_leave_record(self):
        """測試調休記錄解析 (時數在下層)"""
        html = """
        <table id="ContentPlaceHolder1_gvFlow211">
            <tr class="RowStyle">
                <td>
                    <span id="ContentPlaceHolder1_gvFlow211_lblOT_Emp_Name_0">周岳廷</span>
                    <br>
                    <span id="ContentPlaceHolder1_gvFlow211_lblOT_Date_0">2025/11/27</span>
                </td>
                <td>
                    <span id="ContentPlaceHolder1_gvFlow211_lblOT_Dept_Text_0">測試部門</span>
                    <br>
                    <span id="ContentPlaceHolder1_gvFlow211_lblOT_Describe_0" title="調休測試">調休測試</span>
                </td>
                <td>
                    <span id="ContentPlaceHolder1_gvFlow211_Label9_0">加班</span>
                    <br>
                    <span id="ContentPlaceHolder1_gvFlow211_lblT_Change_0" style="color:Blue;">調休</span>
                </td>
                <td>
                    <span id="ContentPlaceHolder1_gvFlow211_lblOT_Minute_0"> </span>&nbsp;
                    <br>
                    <span id="ContentPlaceHolder1_gvFlow211_lblChange_Minute_0">3.5</span>&nbsp;
                </td>
                <td><span id="ContentPlaceHolder1_gvFlow211_lblOT_Manhour_0">3.5</span></td>
                <td><span id="ContentPlaceHolder1_gvFlow211_lblOT_Monhour_0">10.0</span></td>
                <td><span id="ContentPlaceHolder1_gvFlow211_lblProcess_Flag_Text_0">簽核完成</span></td>
            </tr>
        </table>
        """
        parser = PersonalRecordParser()
        records = parser.parse_records(html)

        assert len(records) == 1
        record = records[0]

        # 驗證調休記錄
        assert record["date"] == "2025/11/27"
        assert record["content"] == "調休測試"
        assert record["report_type"] == "調休"  # 應該識別為調休
        assert record["overtime_hours"] == 3.5  # 調休時數
        assert record["monthly_total"] == 3.5
        assert record["quarterly_total"] == 10.0
        assert record["status"] == "簽核完成"

    def test_parse_records_empty(self):
        """測試空 HTML"""
        parser = PersonalRecordParser()
        records = parser.parse_records("<html></html>")
        assert records == []

    def test_parse_records_missing_status(self):
        """測試缺少狀態欄位"""
        html = """
        <table id="ContentPlaceHolder1_gvFlow211">
            <tr class="RowStyle">
                <td>
                    <span id="ContentPlaceHolder1_gvFlow211_lblOT_Personnel_0">測試員</span><br>
                    <span id="ContentPlaceHolder1_gvFlow211_lblOT_Date_0">114/12/01</span>
                </td>
                <td>
                    <span id="ContentPlaceHolder1_gvFlow211_lblOT_Unit_0">部門</span><br>
                    <span id="ContentPlaceHolder1_gvFlow211_lblOT_Describe_0">加班</span>
                </td>
                <td><span id="ContentPlaceHolder1_gvFlow211_lblOT_OT_0">加班</span></td>
                <td>
                    <span id="ContentPlaceHolder1_gvFlow211_lblOT_Minute_0">60</span><br>
                    <span id="ContentPlaceHolder1_gvFlow211_lblChange_Minute_0">0</span>
                </td>
                <td><span id="ContentPlaceHolder1_gvFlow211_lblOT_Manhour_0">1.0</span></td>
                <td><span id="ContentPlaceHolder1_gvFlow211_lblOT_Monhour_0">1.0</span></td>
            </tr>
        </table>
        """
        parser = PersonalRecordParser()
        records = parser.parse_records(html)

        assert len(records) == 1
        assert records[0]["status"] == ""
