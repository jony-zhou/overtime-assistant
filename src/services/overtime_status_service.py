"""[已棄用] 加班申請狀態查詢服務

警告: 此服務已被 DataSyncService 取代

替代方案:
    from src.services.data_sync_service import DataSyncService

    # 舊用法 (deprecated)
    status_service = OvertimeStatusService()
    records = status_service.fetch_submitted_records(session)

    # 新用法
    data_sync = DataSyncService(auth_service, settings)
    snapshot = data_sync.sync_all()
    records = {r.date: SubmittedRecord(...) for r in snapshot.personal_records}

移除時間: v2.0.0
"""

import requests
from bs4 import BeautifulSoup
import logging
from typing import Dict, Optional
import urllib3

from ..config import Settings
from ..models import SubmittedRecord

logger = logging.getLogger(__name__)


class OvertimeStatusService:
    """
    [已棄用] 加班申請狀態查詢服務 - 查詢已申請的加班記錄

    警告: 此服務已被 DataSyncService 取代,將於 v2.0.0 移除
    請使用 DataSyncService.sync_all() 取得已申請記錄
    """

    def __init__(self, settings: Optional[Settings] = None):
        import warnings

        warnings.warn(
            "OvertimeStatusService 已棄用,請使用 DataSyncService",
            DeprecationWarning,
            stacklevel=2,
        )
        self.settings = settings or Settings()

        if not self.settings.VERIFY_SSL:
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    def fetch_submitted_records(
        self, session: requests.Session
    ) -> Dict[str, SubmittedRecord]:
        """
        查詢已申請的加班記錄

        Args:
            session: 已登入的 Session

        Returns:
            字典 {日期: SubmittedRecord}
        """
        url = f"{self.settings.SSP_BASE_URL}{self.settings.OVERTIME_STATUS_URL}"
        submitted_records = {}

        try:
            logger.info("開始查詢已申請的加班記錄 (不換頁模式)")

            # 使用 ddlPage=9999 一次取得所有記錄
            params = {"ctl00$ContentPlaceHolder1$ddlPage": "9999"}

            response = session.get(
                url,
                params=params,
                timeout=self.settings.REQUEST_TIMEOUT,
                verify=self.settings.VERIFY_SSL,
            )

            soup = BeautifulSoup(response.text, "html.parser")

            # 解析所有資料 (不需要分頁)
            records = self._parse_status_table(soup)
            submitted_records.update(records)

            logger.info(f"✓ 已查詢 {len(submitted_records)} 筆已申請記錄")
            return submitted_records

        except Exception as e:
            logger.error(f"✗ 查詢已申請記錄失敗: {e}")
            return {}

    def _parse_status_table(self, soup: BeautifulSoup) -> Dict[str, SubmittedRecord]:
        """
        解析狀態表格

        Args:
            soup: BeautifulSoup 物件

        Returns:
            字典 {日期: SubmittedRecord}
        """
        records = {}

        try:
            # 找到表格 (新版移除了 ContentPlaceHolder1 前綴)
            table = soup.find("table", id="gvFlow211")
            if not table:
                # 嘗試舊版 ID 以保持相容性
                table = soup.find("table", id="ContentPlaceHolder1_gvFlow211")
                if not table:
                    logger.warning("找不到狀態表格 (gvFlow211)")
                    return records

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

            for index, row in enumerate(rows):
                try:
                    # === 提取欄位 (新版使用固定 ID,不帶索引) ===

                    # 日期 (新版: lblD_OT_Date)
                    date_span = row.find("span", id="lblD_OT_Date")
                    if not date_span:
                        # 嘗試舊版 ID
                        date_span = row.find(
                            "span",
                            id=f"ContentPlaceHolder1_gvFlow211_lblOT_Date_{index}",
                        )
                    if not date_span:
                        logger.warning("記錄 %d: 未找到日期欄位", index)
                        continue

                    date = date_span.get_text(strip=True)

                    # 狀態 (新版: lblD_Flag)
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
                        else "未知"
                    )

                    # 加班時數 (新版: lblD_OT_Minute_E)
                    overtime_span = row.find("span", id="lblD_OT_Minute_E")
                    if not overtime_span:
                        # 嘗試舊版 ID
                        overtime_span = row.find(
                            "span",
                            id=f"ContentPlaceHolder1_gvFlow211_lblOT_Minute_{index}",
                        )
                    overtime_minutes = (
                        float(overtime_span.get_text(strip=True))
                        if overtime_span and overtime_span.get_text(strip=True)
                        else 0.0
                    )

                    # 調休時數 (新版: lblD_Change_Minute_E)
                    change_span = row.find("span", id="lblD_Change_Minute_E")
                    if not change_span:
                        # 嘗試舊版 ID
                        change_span = row.find(
                            "span",
                            id=f"ContentPlaceHolder1_gvFlow211_lblChange_Minute_{index}",
                        )
                    change_minutes = (
                        float(change_span.get_text(strip=True))
                        if change_span and change_span.get_text(strip=True)
                        else 0.0
                    )

                    # 建立記錄
                    record = SubmittedRecord(
                        date=date,
                        status=status,
                        overtime_minutes=overtime_minutes,
                        change_minutes=change_minutes,
                    )

                    records[date] = record
                    logger.debug(f"解析記錄: {record}")

                except Exception as e:
                    logger.warning(f"解析第 {index} 列失敗: {e}")
                    continue

            return records

        except Exception as e:
            logger.error(f"解析狀態表格失敗: {e}")
            return records

    def _get_total_pages(self, soup: BeautifulSoup) -> int:
        """
        [已廢棄] 取得總頁數 (使用 ddlPage=9999 後不再需要)
        保留此方法以避免破壞現有程式碼
        """
        return 1

    def _fetch_status_page(
        self, session: requests.Session, soup: BeautifulSoup, page_num: int
    ) -> Dict[str, SubmittedRecord]:
        """
        [已廢棄] 抓取指定頁面的已申請記錄 (使用 ddlPage=9999 後不再需要)
        保留此方法以避免破壞現有程式碼
        """
        return {}
