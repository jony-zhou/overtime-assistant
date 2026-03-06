"""加班補報表單填寫服務"""

import logging
from typing import List, Dict, Any, Optional
import requests
from bs4 import BeautifulSoup
import urllib3

from ..config import Settings
from ..models import OvertimeSubmissionRecord

logger = logging.getLogger(__name__)


class OvertimeReportService:
    """加班補報表單填寫服務"""

    def __init__(self, settings: Optional[Settings] = None):
        self.settings = settings or Settings()

        if not self.settings.VERIFY_SSL:
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    def preview_form(
        self, session: requests.Session, records: List[OvertimeSubmissionRecord]
    ) -> Dict[str, Any]:
        """
        預覽表單填寫 (不實際送出)

        Args:
            session: 已登入的 Session
            records: 要填寫的記錄列表

        Returns:
            預覽結果
        """
        url = f"{self.settings.SSP_BASE_URL}{self.settings.OVERTIME_REPORT_URL}"

        try:
            logger.info(f"正在預覽填寫 {len(records)} 筆記錄...")

            # 取得初始頁面
            response = session.get(
                url,
                timeout=self.settings.REQUEST_TIMEOUT,
                verify=self.settings.VERIFY_SSL,
            )

            soup = BeautifulSoup(response.text, "html.parser")

            # 如果需要多筆記錄,先增加列
            if len(records) > 1:
                soup = self._add_form_rows(session, soup, len(records) - 1)

            # 構建表單資料
            form_data = self._build_form_data(soup, records)

            preview_result = {
                "success": True,
                "records_count": len(records),
                "form_data": form_data,
                "preview_data": [
                    {
                        "date": r.date,
                        "description": r.description,
                        "overtime_hours": r.overtime_hours if r.is_overtime else 0,
                        "change_hours": r.overtime_hours if not r.is_overtime else 0,
                        "type": "加班" if r.is_overtime else "調休",
                    }
                    for r in records
                ],
            }

            logger.info(f"✓ 預覽成功: {len(records)} 筆記錄")
            return preview_result

        except Exception as e:
            logger.error(f"✗ 預覽失敗: {e}")
            return {"success": False, "error": str(e)}

    def submit_form(
        self, session: requests.Session, records: List[OvertimeSubmissionRecord]
    ) -> Dict[str, Any]:
        """
        送出加班補報表單

        Args:
            session: 已登入的 Session
            records: 要送出的記錄列表

        Returns:
            送出結果
        """
        # Beta 版本檢查
        if not self.settings.ENABLE_SUBMISSION:
            logger.warning("送出功能已禁用 (Beta 版本)")
            return {
                "success": False,
                "error": "此功能尚在測試階段,無法實際送出。請使用「預覽填寫」功能。",
            }

        url = f"{self.settings.SSP_BASE_URL}{self.settings.OVERTIME_REPORT_URL}"

        try:
            logger.info(f"正在送出 {len(records)} 筆加班申請...")

            # 取得初始頁面
            response = session.get(
                url,
                timeout=self.settings.REQUEST_TIMEOUT,
                verify=self.settings.VERIFY_SSL,
            )

            soup = BeautifulSoup(response.text, "html.parser")

            # 如果需要多筆記錄,先增加列
            if len(records) > 1:
                soup = self._add_form_rows(session, soup, len(records) - 1)

            # 構建表單資料
            form_data = self._build_form_data(soup, records)

            # 加入送出按鈕 (新版: ctl00$MainContent$btnCommit)
            form_data["ctl00$MainContent$btnCommit"] = "送出"

            # 記錄準備送出的表單資料（除了 ViewState 等大型欄位）
            logger.debug("準備送出的表單資料:")
            for key, value in form_data.items():
                if not key.startswith("__"):  # 跳過 __VIEWSTATE 等內部欄位
                    logger.debug(f"  {key} = {value}")

            # 送出表單
            response = session.post(
                url,
                data=form_data,
                timeout=self.settings.REQUEST_TIMEOUT,
                verify=self.settings.VERIFY_SSL,
            )

            logger.debug(f"表單送出響應狀態碼: {response.status_code}")
            logger.debug(f"響應 URL: {response.url}")

            # 檢查送出結果
            success = self._check_submission_result(response.text)

            if success:
                logger.info(f"✓ 成功送出 {len(records)} 筆加班申請")
                return {"success": True, "submitted_count": len(records)}
            else:
                logger.error("✗ 送出失敗")
                return {"success": False, "error": "表單送出失敗,請檢查日誌"}

        except Exception as e:
            logger.error(f"✗ 送出失敗: {e}")
            return {"success": False, "error": str(e)}

    def _add_form_rows(
        self, session: requests.Session, soup: BeautifulSoup, count: int
    ) -> BeautifulSoup:
        """
        增加表單列

        Args:
            session: 已登入的 Session
            soup: 當前頁面的 BeautifulSoup 物件
            count: 要增加的列數

        Returns:
            更新後的 BeautifulSoup 物件
        """
        url = f"{self.settings.SSP_BASE_URL}{self.settings.OVERTIME_REPORT_URL}"

        try:
            for i in range(count):
                logger.debug(f"正在增加第 {i + 1} 列...")

                # 提取所有隱藏欄位（確保表單狀態完整）
                post_data = {}
                hidden_inputs = soup.find_all("input", {"type": "hidden"})
                for hidden_input in hidden_inputs:
                    name = hidden_input.get("name")
                    value = hidden_input.get("value", "")
                    if name:
                        post_data[name] = value

                # 確認必要欄位存在
                if "__VIEWSTATE" not in post_data:
                    raise ValueError("找不到 ViewState")

                # 設置 PostBack 目標（觸發「增加列」）
                post_data["__EVENTTARGET"] = "ctl00$MainContent$lbtnAddRowi"
                post_data["__EVENTARGUMENT"] = ""

                # 發送 PostBack 請求
                response = session.post(
                    url,
                    data=post_data,
                    timeout=self.settings.REQUEST_TIMEOUT,
                    verify=self.settings.VERIFY_SSL,
                )

                # 更新 soup
                soup = BeautifulSoup(response.text, "html.parser")

            logger.debug(f"✓ 成功增加 {count} 列")
            return soup

        except Exception as e:
            logger.error(f"✗ 增加列失敗: {e}")
            raise

    def _build_form_data(
        self, soup: BeautifulSoup, records: List[OvertimeSubmissionRecord]
    ) -> Dict[str, str]:
        """
        構建表單資料

        Args:
            soup: BeautifulSoup 物件
            records: 記錄列表

        Returns:
            表單資料字典
        """
        # 提取所有隱藏欄位（包括 ViewState 和其他 ASP.NET 狀態欄位）
        form_data = {}

        # 提取所有 input[type="hidden"] 欄位
        hidden_inputs = soup.find_all("input", {"type": "hidden"})
        for hidden_input in hidden_inputs:
            name = hidden_input.get("name")
            value = hidden_input.get("value", "")
            if name:
                form_data[name] = value
                logger.debug(
                    f"提取隱藏欄位: {name} = {value[:50] if len(value) > 50 else value}"
                )

        # 提取所有 select 下拉選單的當前值
        selects = soup.find_all("select")
        for select in selects:
            name = select.get("name")
            if name:
                selected_option = select.find("option", selected=True)
                value = selected_option.get("value", "") if selected_option else ""
                form_data[name] = value
                logger.debug(f"提取下拉選單: {name} = {value}")

        # 提取所有 textarea 的當前值（但稍後會被覆蓋）
        textareas = soup.find_all("textarea")
        for textarea in textareas:
            name = textarea.get("name")
            if name:
                value = textarea.get_text(strip=True)
                form_data[name] = value

        # 確認必要的 ViewState 欄位存在
        if "__VIEWSTATE" not in form_data:
            raise ValueError("找不到 __VIEWSTATE 欄位")

        # 填寫每筆記錄 (第一筆從 ctl02 開始,新版從 ctl02,舊版從 ctl03)
        # 新版使用 MainContent 前綴
        for index, record in enumerate(records):
            ctl_index = f"{index + 2:02d}"  # 02, 03, 04... (新版從 02 開始)

            # 日期
            form_data[f"ctl00$MainContent$gvFlow211i$ctl{ctl_index}$txtOT_Datei"] = (
                record.date
            )

            # 加班內容
            form_data[
                f"ctl00$MainContent$gvFlow211i$ctl{ctl_index}$txtOT_Describei"
            ] = record.description

            # 加班或調休時數（雖然欄位名稱是 Minute，實際接受小時值）
            if record.is_overtime:
                form_data[
                    f"ctl00$MainContent$gvFlow211i$ctl{ctl_index}$txtOT_Minutei"
                ] = str(record.overtime_hours)
                form_data[
                    f"ctl00$MainContent$gvFlow211i$ctl{ctl_index}$txtChange_Minutei"
                ] = "0"
            else:
                form_data[
                    f"ctl00$MainContent$gvFlow211i$ctl{ctl_index}$txtOT_Minutei"
                ] = "0"
                form_data[
                    f"ctl00$MainContent$gvFlow211i$ctl{ctl_index}$txtChange_Minutei"
                ] = str(record.overtime_hours)

        return form_data

    def _check_submission_result(self, html: str) -> bool:
        """
        檢查表單送出結果

        Args:
            html: 回應的 HTML

        Returns:
            是否成功
        """
        try:
            soup = BeautifulSoup(html, "html.parser")

            # 檢查是否有成功訊息
            success_indicators = [
                "送出成功",
                "申請成功",
                "已送出",
                "已完成",
            ]

            # 檢查是否有明確的錯誤訊息
            error_indicators = [
                "系統錯誤",
                "送出失敗",
                "申請失敗",
                "欄位錯誤",
                "資料錯誤",
            ]

            page_text = soup.get_text()

            # 先檢查成功指標
            for indicator in success_indicators:
                if indicator in page_text:
                    logger.info(f"✓ 發現成功指標: {indicator}")
                    return True

            # 再檢查錯誤指標
            for indicator in error_indicators:
                if indicator in page_text:
                    logger.error(f"✗ 發現錯誤指標: {indicator}")
                    return False

            # 檢查表單是否已清空（成功提交的特徵）
            # 如果找不到輸入表格，可能是已重定向到成功頁面
            input_table = soup.find("table", {"id": "MainContent_gvFlow211i"})
            if not input_table:
                logger.info("✓ 表單已清空或重定向，視為成功")
                return True

            # 沒有明確指標，檢查表單內容
            # 如果所有輸入欄位都是空的或預設值，可能是提交成功後清空了
            input_fields = input_table.find_all("input", {"type": "text"})
            if input_fields:
                has_content = any(
                    field.get("value") and field.get("value") != "0"
                    for field in input_fields
                )
                if not has_content:
                    logger.info("✓ 表單已清空，視為提交成功")
                    return True

            # 無法確定結果，記錄警告
            logger.warning("⚠ 無法明確判斷提交結果，預設視為成功")
            logger.debug(f"頁面文字前 500 字元: {page_text[:500]}")

            # 輸出響應頁面的 HTML 到檔案以便調試
            try:
                import os
                from datetime import datetime

                debug_dir = "logs/debug"
                os.makedirs(debug_dir, exist_ok=True)
                debug_file = os.path.join(
                    debug_dir,
                    f"submission_response_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html",
                )
                with open(debug_file, "w", encoding="utf-8") as f:
                    f.write(html)
                logger.info(f"響應頁面已保存至: {debug_file}")
            except Exception as save_error:
                logger.debug(f"無法保存響應頁面: {save_error}")

            return True

        except Exception as error:
            logger.error(f"✗ 檢查送出結果失敗: {error}")
            return False
