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
        解析打卡記錄表格
        
        表格 ID: ContentPlaceHolder1_gvNotes005
        表格結構:
        <tr class="RowStyle|AlternatingRowStyle_update">
            <td>2025/12/01</td>  <!-- 刷卡日期 -->
            <td>09:02:32</td>    <!-- 刷卡時間 -->
        </tr>
        
        Args:
            html: FW99001Z.aspx#tabs-1 的 HTML 內容
            
        Returns:
            List[PunchRecord]: 打卡記錄列表
            
        Notes:
            - 同一日期可能有多筆打卡記錄
            - 自動合併為 PunchRecord.punch_times 列表
            - 支援分頁表格 (自動跳過 PagerStyle row)
        """
        soup = BeautifulSoup(html, "html.parser")
        
        # 查找打卡表格
        table = soup.find("table", id="ContentPlaceHolder1_gvNotes005")
        if not table:
            logger.warning("找不到打卡表格 (gvNotes005)")
            return []
        
        # 解析資料列
        rows = table.find_all("tr")
        punch_data: Dict[str, List[str]] = {}  # {date: [punch_times]}
        
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
        
        # 轉換為 PunchRecord
        records = [
            PunchRecord(date=date, punch_times=sorted(times))
            for date, times in punch_data.items()
        ]
        
        logger.info("解析打卡記錄: %d 個日期, 共 %d 筆打卡", len(records), sum(len(r.punch_times) for r in records))
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
            
            days = AttendanceParser._extract_number(day_span.get_text() if day_span else "0 天")
            hours = AttendanceParser._extract_number(hour_span.get_text() if hour_span else "0 小時")
            
            if leave_type and (days > 0 or hours > 0):
                records.append(LeaveRecord(
                    leave_type=leave_type,
                    days=days,
                    hours=hours
                ))
        
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
                overtime_threshold_minutes = AttendanceParser._extract_time_to_minutes(text)
        
        quota = AttendanceQuota(
            annual_leave=annual_leave,
            compensatory_leave=compensatory_leave,
            overtime_threshold_minutes=overtime_threshold_minutes
        )
        
        logger.info("解析額度: 特休 %d 天, 調休 %d 天, 門檻 %d 分鐘", annual_leave, compensatory_leave, overtime_threshold_minutes)
        return quota

    @staticmethod
    def parse_anomaly_records(html: str) -> List[Dict]:
        """
        解析出勤異常表格
        
        表格 ID: ContentPlaceHolder1_gvWeb012
        表格結構:
        <tr class="RowStyle|AlternatingRowStyle_update">
            <td>
                <span id="...lblWork_Date_0">2025/11/28</span><br>
                <span id="...lblCard_Time_0">&nbsp;&nbsp;09:00:15~19:31:09&nbsp;&nbsp;</span>
            </td>
            <td><span id="...lblLose_Manhour_0">0</span></td>
            <td>下班刷卡超出正常下班時刻</td>
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
        """
        soup = BeautifulSoup(html, "html.parser")
        
        # 查找異常表格
        table = soup.find("table", id="ContentPlaceHolder1_gvWeb012")
        if not table:
            logger.warning("找不到異常表格 (gvWeb012)")
            return []
        
        # 解析資料列
        rows = table.find_all("tr")
        records = []
        
        for row in rows:
            # 跳過表頭和分頁
            if row.find("th") or AttendanceParser._is_pager_row(row):
                continue
            
            cells = row.find_all("td")
            if len(cells) < 3:
                continue
            
            # 出勤日期和刷卡時間
            date_span = cells[0].find("span", id=re.compile(r"lblWork_Date"))
            time_span = cells[0].find("span", id=re.compile(r"lblCard_Time"))
            
            date = date_span.get_text(strip=True) if date_span else ""
            punch_range = time_span.get_text(strip=True) if time_span else ""
            
            # 異常說明
            description = cells[2].get_text(strip=True)
            
            if date and description:
                records.append({
                    'date': date,
                    'punch_range': punch_range,
                    'description': description
                })
        
        logger.info("解析異常記錄: %d 筆", len(records))
        return records

    # === 輔助方法 ===

    @staticmethod
    def _is_pager_row(row) -> bool:
        """判斷是否為分頁列"""
        row_class = row.get("class", [])
        return "PagerStyle" in (row_class if isinstance(row_class, list) else [row_class])

    @staticmethod
    def _extract_number(text: str) -> int:
        """從文字中提取數字
        
        Examples:
            " 18 天" -> 18
            " 0 小時" -> 0
            "目前特休剩餘：1 天" -> 1
        """
        match = re.search(r'(\d+)', text)
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
        hour_match = re.search(r'(\d+)\s*小時', text)
        if hour_match:
            hours = int(hour_match.group(1))
        
        # 提取分鐘
        min_match = re.search(r'(\d+)\s*分鐘', text)
        if min_match:
            minutes = int(min_match.group(1))
        
        return hours * 60 + minutes
