"""出勤頁面 HTML 解析器

解析 FW99001Z.aspx (出勤狀況頁面) 的三個表格:
- ContentPlaceHolder1_gvNotes005: 打卡記錄
- ContentPlaceHolder1_gvNotes011: 假別統計
- ContentPlaceHolder1_dvNotes019: 剩餘額度
- ContentPlaceHolder1_gvWeb012: 出勤異常 (tabs-2)
"""

import logging
import re
from typing import List, Dict, Optional
from bs4 import BeautifulSoup

from ..models import PunchRecord, LeaveRecord, AttendanceQuota

logger = logging.getLogger(__name__)


class AttendanceParser:
    """
    出勤頁面解析器

    職責:
    - 解析打卡記錄表格 (gvNotes005)
    - 解析假別統計表格 (gvNotes011)
    - 解析剩餘額度表格 (dvNotes019)
    - 解析出勤異常表格 (gvWeb012)

    設計原則:
    - SRP: 只負責 HTML → 資料模型轉換
    - DRY: 共用表格查找與row處理邏輯
    - Fail-safe: 解析失敗時返回空列表而非拋出異常
    """

    @staticmethod
    def parse_punch_records(html: str) -> List[PunchRecord]:
        """
        解析打卡記錄

        新版 (2026): 從出勤日曆 (gvCalendar) 提取
        舊版: 從打卡記錄表格 (gvNotes005) 提取

        新版表格結構:
        <table id="gvCalendar">
            <tr>
                <td>
                    <span id="lblDate1">2</span>  <!-- 日期 -->
                    <a id="lblWork_Time1" data-popup="刷卡 08:55:13&lt;br/&gt;刷卡 19:32:55">08:55~19:32</a>
                </td>
            </tr>
        </table>

        舊版表格結構:
        <table id="ContentPlaceHolder1_gvNotes005">
            <tr>
                <td>2025/12/01</td>  <!-- 刷卡日期 -->
                <td>09:02:32</td>    <!-- 刷卡時間 -->
            </tr>
        </table>

        Args:
            html: FW99001Z.aspx 的 HTML 內容

        Returns:
            List[PunchRecord]: 打卡記錄列表

        Notes:
            - 同一日期可能有多筆打卡記錄
            - 自動合併為 PunchRecord.punch_times 列表
        """
        soup = BeautifulSoup(html, "html.parser")
        punch_data: Dict[str, List[str]] = {}  # {date: [punch_times]}

        # 嘗試新版日曆格式 (2026)
        calendar_table = soup.find("table", id="gvCalendar")
        if calendar_table:
            # 提取年月 (如 "2026 年 3 月")
            year_month_span = soup.find("span", id=re.compile(r"lblMonthYear"))
            if year_month_span:
                year_month_text = year_month_span.get_text(strip=True)
                # 解析 "2026 年 3 月" -> (2026, 3)
                year_match = re.search(r"(\d{4})\s*年", year_month_text)
                month_match = re.search(r"(\d{1,2})\s*月", year_month_text)

                if year_match and month_match:
                    year = year_match.group(1)
                    month = int(month_match.group(1))

                    # 遍歷所有日期單元格
                    date_cells = calendar_table.find_all("td", class_="text-center")
                    for cell in date_cells:
                        # 找日期 span
                        date_span = cell.find("span", id=re.compile(r"lblDate\d+"))
                        if not date_span:
                            continue

                        day = date_span.get_text(strip=True)
                        if not day.isdigit():
                            continue

                        # 組合完整日期 (YYYY/MM/DD)
                        full_date = f"{year}/{month:02d}/{int(day):02d}"

                        # 找出勤資訊
                        work_time_link = cell.find(
                            "a", id=re.compile(r"lblWork_Time\d+")
                        )
                        if work_time_link:
                            # 從 data-popup 提取完整打卡時間
                            popup_data = work_time_link.get("data-popup", "")
                            if popup_data:
                                # 解析 "刷卡 08:55:13<br/>刷卡 19:32:55"
                                times = re.findall(
                                    r"刷卡\s+(\d{2}:\d{2}:\d{2})", popup_data
                                )
                                if times:
                                    punch_data[full_date] = times

                logger.info("解析打卡記錄 (日曆格式): %d 個日期", len(punch_data))

        # 若無日曆格式,嘗試舊版表格格式
        if not punch_data:
            table = soup.find("table", id="ContentPlaceHolder1_gvNotes005")
            if table:
                rows = table.find_all("tr")

                for row in rows:
                    # 跳過表頭和分頁
                    if row.find("th") or AttendanceParser._is_pager_row(row):
                        continue

                    cells = row.find_all("td")
                    if len(cells) < 2:
                        continue

                    date = cells[0].get_text(strip=True)
                    punch_time = cells[1].get_text(strip=True)

                    if date and punch_time:
                        if date not in punch_data:
                            punch_data[date] = []
                        punch_data[date].append(punch_time)

                logger.info("解析打卡記錄 (表格格式): %d 個日期", len(punch_data))

        # 轉換為 PunchRecord
        if not punch_data:
            logger.warning("找不到打卡記錄 (gvCalendar 或 gvNotes005)")
            return []

        records = [
            PunchRecord(date=date, punch_times=sorted(times))
            for date, times in punch_data.items()
        ]

        logger.info(
            "✓ 解析完成: %d 個日期, 共 %d 筆打卡",
            len(records),
            sum(len(r.punch_times) for r in records),
        )
        return records

    @staticmethod
    def parse_leave_records(html: str) -> List[LeaveRecord]:
        """
        解析假別統計表格

        表格 ID: ContentPlaceHolder1_gvNotes011
        表格結構:
        <tr class="RowStyle|AlternatingRowStyle_update">
            <td>114年公出</td>  <!-- 假別 -->
            <td>
                <span id="...lblAbsenceDay_0"> 18 天</span>
                <span id="...lblAbsenceHour_0"> 0 小時</span>
            </td>
        </tr>

        Args:
            html: FW99001Z.aspx#tabs-1 的 HTML 內容

        Returns:
            List[LeaveRecord]: 假別記錄列表

        Notes:
            - 天數和小時需分別提取 (使用 span id)
            - 支援 "X 天" 和 "X 小時" 格式
        """
        soup = BeautifulSoup(html, "html.parser")

        # 查找假別表格
        table = soup.find("table", id="ContentPlaceHolder1_gvNotes011")
        if not table:
            logger.warning("找不到假別表格 (gvNotes011)")
            return []

        # 解析資料列
        rows = table.find_all("tr")
        records = []

        for row in rows:
            # 跳過表頭
            if row.find("th"):
                continue

            cells = row.find_all("td")
            if len(cells) < 2:
                continue

            # 假別名稱
            leave_type = cells[0].get_text(strip=True)

            # 天數和小時 (從 span 中提取)
            day_span = cells[1].find("span", id=re.compile(r"lblAbsenceDay"))
            hour_span = cells[1].find("span", id=re.compile(r"lblAbsenceHour"))

            days = AttendanceParser._extract_number(
                day_span.get_text() if day_span else "0 天"
            )
            hours = AttendanceParser._extract_number(
                hour_span.get_text() if hour_span else "0 小時"
            )

            if leave_type and (days > 0 or hours > 0):
                records.append(
                    LeaveRecord(leave_type=leave_type, days=days, hours=hours)
                )

        logger.info("解析假別記錄: %d 筆", len(records))
        return records

    @staticmethod
    def parse_quota(html: str) -> Optional[AttendanceQuota]:
        """
        解析剩餘額度表格

        表格 ID: ContentPlaceHolder1_dvNotes019
        表格結構:
        <tr class="RowStyle|AlternatingRowStyle_update">
            <td>年度特休可用：1 天</td>
        </tr>
        <tr>
            <td>年度調休可用：15 天</td>
        </tr>
        <tr>
            <td>目前特休剩餘：1 天</td>
        </tr>
        <tr>
            <td>目前調休剩餘：8 天</td>
        </tr>
        <tr>
            <td>未達加班換休最低申請時限： 1 小時 33 分鐘</td>
        </tr>

        Args:
            html: FW99001Z.aspx#tabs-1 的 HTML 內容

        Returns:
            AttendanceQuota | None: 額度資訊,找不到表格時返回 None

        Notes:
            - 只提取 "目前特休剩餘" 和 "目前調休剩餘"
            - "未達加班換休最低申請時限" 轉換為分鐘數
        """
        soup = BeautifulSoup(html, "html.parser")

        # 查找額度表格
        table = soup.find("table", id="ContentPlaceHolder1_dvNotes019")
        if not table:
            logger.warning("找不到額度表格 (dvNotes019)")
            return None

        # 解析資料列
        rows = table.find_all("tr")
        annual_leave = 0
        compensatory_leave = 0
        overtime_threshold_minutes = 0

        for row in rows:
            # 跳過表頭
            if row.find("th"):
                continue

            cell = row.find("td")
            if not cell:
                continue

            text = cell.get_text(strip=True)

            # 目前特休剩餘
            if "目前特休剩餘" in text:
                annual_leave = AttendanceParser._extract_number(text)

            # 目前調休剩餘
            elif "目前調休剩餘" in text:
                compensatory_leave = AttendanceParser._extract_number(text)

            # 未達加班換休最低申請時限
            elif "未達加班換休最低申請時限" in text or "最低申請時限" in text:
                overtime_threshold_minutes = AttendanceParser._extract_time_to_minutes(
                    text
                )

        quota = AttendanceQuota(
            annual_leave=annual_leave,
            compensatory_leave=compensatory_leave,
            overtime_threshold_minutes=overtime_threshold_minutes,
        )

        logger.info(
            "解析額度: 特休 %d 天, 調休 %d 天, 門檻 %d 分鐘",
            annual_leave,
            compensatory_leave,
            overtime_threshold_minutes,
        )
        return quota

    @staticmethod
    def parse_anomaly_records(html: str) -> List[Dict]:
        """
        解析出勤異常表格

        表格 ID: gvWeb012 (新版) / ContentPlaceHolder1_gvWeb012 (舊版)
        表格結構:
        <tr>
            <td>
                <span id="lblAtt_Date">2025/11/28</span><br>
                <span id="lblAtt_Time">&nbsp;&nbsp;09:00:15~19:31:09&nbsp;&nbsp;</span>
            </td>
            <td><span id="lblLose_Manhour">0</span></td>
            <td><span id="lblAtt_Result">下班刷卡超出正常下班時刻</span></td>
            <td>...</td>
        </tr>

        Args:
            html: FW99001Z.aspx#tabs-2 的 HTML 內容

        Returns:
            List[Dict]: 異常記錄列表
                [{
                    'date': 'YYYY/MM/DD',
                    'punch_range': 'HH:MM:SS~HH:MM:SS',
                    'description': '下班刷卡超出正常下班時刻'
                }]

        Notes:
            - 用於標記 UnifiedOvertimeRecord.has_anomaly
            - 僅提取必要欄位 (不解析按鈕)
            - 新版使用固定 ID (lblAtt_Date, lblAtt_Time, lblAtt_Result)
            - 舊版使用帶索引 ID (lblWork_Date_{index}, lblCard_Time_{index})
        """
        soup = BeautifulSoup(html, "html.parser")

        # 查找異常表格 (嘗試新版和舊版 ID)
        table = soup.find("table", id="gvWeb012")
        if not table:
            table = soup.find("table", id="MainContent_gvWeb012")
        if not table:
            table = soup.find("table", id="ContentPlaceHolder1_gvWeb012")
        if not table:
            logger.warning("找不到異常表格 (gvWeb012)")
            return []

        # 解析資料列 (新版使用 tbody > tr,舊版使用 class)
        tbody = table.find("tbody")
        if tbody:
            rows = tbody.find_all("tr", recursive=False)
        else:
            # 若無 tbody,嘗試直接找 tr (排除表頭)
            rows = [
                tr
                for tr in table.find_all("tr")
                if not tr.find_parent("thead") and tr.find("td")
            ]

        records = []

        for row in rows:
            # 跳過表頭和分頁
            if row.find("th") or AttendanceParser._is_pager_row(row):
                continue

            cells = row.find_all("td")
            if len(cells) < 3:
                continue

            # 出勤日期和刷卡時間 (新版使用固定 ID)
            date_span = cells[0].find("span", id="lblAtt_Date")
            time_span = cells[0].find("span", id="lblAtt_Time")

            # 若找不到新版 ID,嘗試舊版 ID (使用 regex)
            if not date_span:
                date_span = cells[0].find("span", id=re.compile(r"lblWork_Date"))
            if not time_span:
                time_span = cells[0].find("span", id=re.compile(r"lblCard_Time"))

            date = date_span.get_text(strip=True) if date_span else ""
            punch_range = time_span.get_text(strip=True) if time_span else ""

            # 異常說明 (新版: lblAtt_Result)
            desc_span = cells[2].find("span", id="lblAtt_Result")
            if desc_span:
                description = desc_span.get_text(strip=True)
            else:
                # 若找不到 span,直接取 td 文字 (舊版)
                description = cells[2].get_text(strip=True)

            if date and description:
                records.append(
                    {
                        "date": date,
                        "punch_range": punch_range,
                        "description": description,
                    }
                )

        logger.info("解析異常記錄: %d 筆", len(records))
        return records

    # === 輔助方法 ===

    @staticmethod
    def _is_pager_row(row) -> bool:
        """判斷是否為分頁列"""
        row_class = row.get("class", [])
        return "PagerStyle" in (
            row_class if isinstance(row_class, list) else [row_class]
        )

    @staticmethod
    def _extract_number(text: str) -> int:
        """從文字中提取數字

        Examples:
            " 18 天" -> 18
            " 0 小時" -> 0
            "目前特休剩餘：1 天" -> 1
        """
        match = re.search(r"(\d+)", text)
        return int(match.group(1)) if match else 0

    @staticmethod
    def _extract_time_to_minutes(text: str) -> int:
        """從文字中提取時間並轉換為分鐘

        Examples:
            " 1 小時 33 分鐘" -> 93
            " 2 小時 0 分鐘" -> 120
            " 45 分鐘" -> 45
        """
        hours = 0
        minutes = 0

        # 提取小時
        hour_match = re.search(r"(\d+)\s*小時", text)
        if hour_match:
            hours = int(hour_match.group(1))

        # 提取分鐘
        min_match = re.search(r"(\d+)\s*分鐘", text)
        if min_match:
            minutes = int(min_match.group(1))

        return hours * 60 + minutes
