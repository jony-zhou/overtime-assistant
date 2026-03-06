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

        # 查找表格 (新版移除了 ContentPlaceHolder1 前綴)
        table = soup.find("table", id="gvFlow211")
        if not table:
            # 嘗試舊版 ID 以保持相容性
            table = soup.find("table", id="ContentPlaceHolder1_gvFlow211")
            if not table:
                logger.warning("找不到個人記錄表格 (gvFlow211)")
                return []

        # 解析資料列 (新版不再依賴 class,改用 tbody > tr)
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

        for index, row in enumerate(rows):
            try:
                # === 提取欄位 (新版使用固定 ID,不帶索引) ===

                # 日期 (新版: lblD_OT_Date)
                date_span = row.find("span", id="lblD_OT_Date")
                if not date_span:
                    # 嘗試舊版 ID
                    date_span = row.find(
                        "span", id=f"ContentPlaceHolder1_gvFlow211_lblOT_Date_{index}"
                    )
                if not date_span:
                    logger.warning("記錄 %d: 未找到日期欄位", index)
                    continue
                date = date_span.get_text(strip=True)

                # 加班內容 (新版: lblD_OT_Describe)
                content_span = row.find("span", id="lblD_OT_Describe")
                if not content_span:
                    # 嘗試舊版 ID
                    content_span = row.find(
                        "span",
                        id=f"ContentPlaceHolder1_gvFlow211_lblOT_Describe_{index}",
                    )
                content = ""
                if content_span:
                    title_attr = content_span.get("title")
                    content = (
                        title_attr if title_attr else content_span.get_text(strip=True)
                    )

                # 申報時數 - 加班時數 (新版: lblD_OT_Minute_E)
                overtime_span = row.find("span", id="lblD_OT_Minute_E")
                if not overtime_span:
                    # 嘗試舊版 ID
                    overtime_span = row.find(
                        "span", id=f"ContentPlaceHolder1_gvFlow211_lblOT_Minute_{index}"
                    )
                overtime_text = (
                    overtime_span.get_text(strip=True) if overtime_span else "0"
                )
                overtime_hours = PersonalRecordParser._parse_hours(overtime_text)

                # 申報時數 - 調休時數 (新版: lblD_Change_Minute_E)
                change_span = row.find("span", id="lblD_Change_Minute_E")
                if not change_span:
                    # 嘗試舊版 ID
                    change_span = row.find(
                        "span",
                        id=f"ContentPlaceHolder1_gvFlow211_lblChange_Minute_{index}",
                    )
                change_text = change_span.get_text(strip=True) if change_span else "0"
                change_hours = PersonalRecordParser._parse_hours(change_text)

                # 判斷申報類型 (根據時數判斷)
                if overtime_hours > 0:
                    report_type = "加班"
                    total_hours = overtime_hours
                elif change_hours > 0:
                    report_type = "調休"
                    total_hours = change_hours
                else:
                    report_type = ""
                    total_hours = 0.0

                # 當月累計 (新版: lblD_OT_Manhour)
                monthly_span = row.find("span", id="lblD_OT_Manhour")
                if not monthly_span:
                    # 嘗試舊版 ID
                    monthly_span = row.find(
                        "span",
                        id=f"ContentPlaceHolder1_gvFlow211_lblOT_Manhour_{index}",
                    )
                monthly_text = (
                    monthly_span.get_text(strip=True) if monthly_span else "0"
                )
                monthly_total = PersonalRecordParser._parse_hours(monthly_text)

                # 當季累計 (新版: lblD_OT_Manhour_T)
                quarterly_span = row.find("span", id="lblD_OT_Manhour_T")
                if not quarterly_span:
                    # 嘗試舊版 ID
                    quarterly_span = row.find(
                        "span",
                        id=f"ContentPlaceHolder1_gvFlow211_lblOT_Monhour_{index}",
                    )
                quarterly_text = (
                    quarterly_span.get_text(strip=True) if quarterly_span else "0"
                )
                quarterly_total = PersonalRecordParser._parse_hours(quarterly_text)

                # 簽核狀態 (新版: lblD_Flag)
                status_span = row.find("span", id="lblD_Flag")
                if not status_span:
                    # 嘗試舊版 ID
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
