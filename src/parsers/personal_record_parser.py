"""個人記錄頁面 HTML 解析器

解析 FW21003Z.aspx (個人加班記錄) 的表格:
- ContentPlaceHolder1_gvFlow211: 個人加班記錄明細
"""

import logging
from typing import List, Dict
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


class PersonalRecordParser:
    """
    個人加班記錄解析器

    職責:
    - 解析個人加班記錄表格 (gvFlow211)
    - 提取日期、內容、時數、狀態等欄位

    設計原則:
    - SRP: 只負責 HTML → Dict 轉換 (不依賴 PersonalRecord 模型)
    - 與 PersonalRecordService 相容,可直接替換 _parse_personal_records_table
    """

    @staticmethod
    def parse_records(html: str) -> List[Dict]:
        """
        解析個人加班記錄表格

        表格 ID: ContentPlaceHolder1_gvFlow211
        表格結構:
        <tr class="RowStyle|AlternatingRowStyle_update">
            <td>
                <span id="...lblOT_Personnel_0">周岳廷</span><br>
                <span id="...lblOT_Date_0">114/11/24</span>
            </td>
            <td>
                <span id="...lblOT_Unit_0">部門</span><br>
                <span id="...lblOT_Describe_0" title="完整內容">加班內容</span>
            </td>
            <td><span id="...lblOT_OT_0">加班/調休</span></td>
            <td>
                <span id="...lblOT_Minute_0">120</span><br>  <!-- 加班時數(分鐘) -->
                <span id="...lblChange_Minute_0">0</span>    <!-- 調休時數(分鐘) -->
            </td>
            <td><span id="...lblOT_Manhour_0">2.0</span></td>  <!-- 當月累計 -->
            <td><span id="...lblOT_Monhour_0">8.5</span></td>  <!-- 當季累計 -->
            <td><span id="...lblProcess_Flag_Text_0">已核准</span></td>
        </tr>

        Args:
            html: FW21003Z.aspx 的 HTML 內容

        Returns:
            List[Dict]: 記錄列表
                [{
                    'date': '114/11/24',
                    'content': '加班內容',
                    'status': '已核准',
                    'report_type': '加班',  # 或 '調休'
                    'overtime_hours': 2.0,
                    'monthly_total': 2.0,
                    'quarterly_total': 8.5
                }]

        Notes:
            - 時數可能是分鐘 (>10的整數) 或小時 (小數)
            - title 屬性包含完整內容 (優先使用)
            - 使用 ddlPage=9999 參數避免換頁問題
        """
        soup = BeautifulSoup(html, "html.parser")

        # 查找表格
        table = soup.find("table", id="ContentPlaceHolder1_gvFlow211")
        if not table:
            logger.warning("找不到個人記錄表格 (gvFlow211)")
            return []

        # 解析資料列
        rows = table.find_all("tr", class_=["RowStyle", "AlternatingRowStyle_update"])
        records = []

        for index, row in enumerate(rows):
            try:
                # === 提取欄位 ===

                # 日期
                date_span = row.find(
                    "span", id=f"ContentPlaceHolder1_gvFlow211_lblOT_Date_{index}"
                )
                if not date_span:
                    logger.warning("記錄 %d: 未找到日期欄位", index)
                    continue
                date = date_span.get_text(strip=True)

                # 加班內容 (優先使用 title 屬性)
                content_span = row.find(
                    "span", id=f"ContentPlaceHolder1_gvFlow211_lblOT_Describe_{index}"
                )
                content = ""
                if content_span:
                    title_attr = content_span.get("title")
                    content = (
                        title_attr if title_attr else content_span.get_text(strip=True)
                    )

                # 狀態欄位 (判斷是加班還是調休)
                # 上層: 加班狀態 (Label9_X)
                overtime_status_span = row.find(
                    "span", id=f"ContentPlaceHolder1_gvFlow211_Label9_{index}"
                )
                overtime_status = (
                    overtime_status_span.get_text(strip=True)
                    if overtime_status_span
                    else ""
                )

                # 下層: 調休狀態 (lblT_Change_X)
                change_status_span = row.find(
                    "span", id=f"ContentPlaceHolder1_gvFlow211_lblT_Change_{index}"
                )
                change_status = (
                    change_status_span.get_text(strip=True)
                    if change_status_span
                    else ""
                )

                # 申報時數 - 上層: 加班時數 (lblOT_Minute_X)
                overtime_span = row.find(
                    "span", id=f"ContentPlaceHolder1_gvFlow211_lblOT_Minute_{index}"
                )
                overtime_text = (
                    overtime_span.get_text(strip=True) if overtime_span else ""
                )
                overtime_hours = PersonalRecordParser._parse_hours(overtime_text)

                # 申報時數 - 下層: 調休時數 (lblChange_Minute_X)
                change_span = row.find(
                    "span", id=f"ContentPlaceHolder1_gvFlow211_lblChange_Minute_{index}"
                )
                change_text = change_span.get_text(strip=True) if change_span else ""
                change_hours = PersonalRecordParser._parse_hours(change_text)

                # 判斷申報類型 (根據哪個時數 > 0,或根據狀態欄位)
                if overtime_hours > 0:
                    report_type = overtime_status or "加班"
                    total_hours = overtime_hours
                elif change_hours > 0:
                    report_type = change_status or "調休"
                    total_hours = change_hours
                else:
                    # 兩個都是 0,優先使用有狀態文字的那個
                    if overtime_status:
                        report_type = overtime_status
                        total_hours = 0.0
                    elif change_status:
                        report_type = change_status
                        total_hours = 0.0
                    else:
                        report_type = ""
                        total_hours = 0.0

                # 當月累計
                monthly_span = row.find(
                    "span", id=f"ContentPlaceHolder1_gvFlow211_lblOT_Manhour_{index}"
                )
                monthly_text = (
                    monthly_span.get_text(strip=True) if monthly_span else "0"
                )
                monthly_total = PersonalRecordParser._parse_hours(monthly_text)

                # 當季累計
                quarterly_span = row.find(
                    "span", id=f"ContentPlaceHolder1_gvFlow211_lblOT_Monhour_{index}"
                )
                quarterly_text = (
                    quarterly_span.get_text(strip=True) if quarterly_span else "0"
                )
                quarterly_total = PersonalRecordParser._parse_hours(quarterly_text)

                # 簽核狀態
                status_span = row.find(
                    "span",
                    id=f"ContentPlaceHolder1_gvFlow211_lblProcess_Flag_Text_{index}",
                )
                status = (
                    status_span.get_text(strip=True).replace("<br>", " ")
                    if status_span
                    else ""
                )

                # 建立記錄
                record = {
                    "date": date,
                    "content": content,
                    "status": status,
                    "report_type": report_type,
                    "overtime_hours": total_hours,
                    "monthly_total": monthly_total,
                    "quarterly_total": quarterly_total,
                }

                records.append(record)

            except (IndexError, ValueError, AttributeError) as error:
                logger.warning("解析記錄 %d 失敗: %s", index, error)
                continue

        logger.info("解析個人記錄: %d 筆", len(records))
        return records

    # === 輔助方法 ===

    @staticmethod
    def _parse_hours(text: str) -> float:
        """
        解析時數文字

        Args:
            text: 時數文字 ("120" 分鐘 或 "2.0" 小時)

        Returns:
            float: 小時數

        Notes:
            - 空白或空字串返回 0.0
            - 大於 10 的整數視為分鐘,需除以 60
            - 小數或小於 10 的整數視為小時

        Examples:
            "120" -> 2.0
            "2.0" -> 2.0
            "0.5" -> 0.5
            "5" -> 5.0 (視為小時,因為小於 10)
            "" -> 0.0
            "  " -> 0.0
        """
        try:
            # 移除逗號和前後空白
            text = text.replace(",", "").strip()

            # 空字串或純空白返回 0.0
            if not text:
                return 0.0

            value = float(text)

            # 判斷是否為分鐘數 (通常大於 10 的整數)
            if value > 10 and value == int(value):
                return value / 60.0  # 分鐘轉小時

            return value

        except ValueError:
            logger.warning("無法解析時數: %s", text)
            return 0.0
