"""認證服務"""

import requests
from bs4 import BeautifulSoup
import logging
from typing import Optional
import urllib3

from ..config import Settings

logger = logging.getLogger(__name__)


class AuthService:
    """認證服務 - 處理 SSP 系統登入"""

    def __init__(self, settings: Optional[Settings] = None):
        self.settings = settings or Settings()
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }
        )

        if not self.settings.VERIFY_SSL:
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    def login(self, username: str, password: str) -> bool:
        """
        登入 SSP 系統

        Args:
            username: 使用者帳號
            password: 使用者密碼

        Returns:
            bool: 登入是否成功
        """
        login_url = f"{self.settings.SSP_BASE_URL}/default.aspx"

        try:
            logger.info("正在連接登入頁面...")
            response = self.session.get(
                login_url,
                timeout=self.settings.REQUEST_TIMEOUT,
                verify=self.settings.VERIFY_SSL,
            )
            soup = BeautifulSoup(response.text, "html.parser")

            # 提取 ASP.NET 必要的隱藏欄位
            viewstate = soup.find("input", {"name": "__VIEWSTATE"})
            viewstate_generator = soup.find("input", {"name": "__VIEWSTATEGENERATOR"})
            event_validation = soup.find("input", {"name": "__EVENTVALIDATION"})

            if not viewstate:
                logger.error("無法找到 ViewState,可能網頁結構已變更")
                return False

            # 準備登入資料
            login_data = {
                "__VIEWSTATE": viewstate["value"],
                "__VIEWSTATEGENERATOR": (
                    viewstate_generator["value"] if viewstate_generator else ""
                ),
                "__EVENTVALIDATION": (
                    event_validation["value"] if event_validation else ""
                ),
                "ctl00$txtAccount": username,
                "ctl00$txtPassword": password,
                "ctl00$btnSubmit": "送出",
            }

            logger.info("正在驗證登入資訊...")
            response = self.session.post(
                login_url,
                data=login_data,
                timeout=self.settings.REQUEST_TIMEOUT,
                verify=self.settings.VERIFY_SSL,
            )

            # 檢查是否登入成功 (v1.3.2 強化驗證)
            # 1. 檢查是否被重導回根目錄 (密碼錯誤的情況)
            if response.url.rstrip("/") == self.settings.SSP_BASE_URL.rstrip("/"):
                logger.error("✗ 登入失敗: 帳號或密碼錯誤 (被重導回登入頁)")
                return False

            # 2. 檢查 URL 是否包含 default.aspx 或 FW99001Z.aspx
            if "default.aspx" not in response.url and "FW99001Z.aspx" not in response.url:
                logger.error("✗ 登入失敗: 未跳轉到正確頁面")
                return False

            # 3. 二次驗證: 檢查 session 是否真的有效
            session_valid, error_msg = self.verify_session()
            if not session_valid:
                logger.error(f"✗ 登入失敗: {error_msg}")
                return False

            logger.info("✓ 登入成功")
            return True

        except requests.exceptions.Timeout:
            logger.error("✗ 連線逾時,請檢查網路連線")
            return False
        except Exception as e:
            logger.error(f"✗ 登入時發生錯誤: {e}", exc_info=True)
            return False

    def verify_session(self) -> tuple[bool, str]:
        """
        驗證 session 是否真的有效

        嘗試存取主頁面,檢查是否能正常載入用戶資料

        Returns:
            tuple[bool, str]: (是否有效, 錯誤訊息)
        """
        try:
            # 嘗試存取主頁面
            main_page_url = f"{self.settings.SSP_BASE_URL}/FW99001Z.aspx"
            response = self.session.get(
                main_page_url,
                timeout=self.settings.REQUEST_TIMEOUT,
                verify=self.settings.VERIFY_SSL,
            )

            # 檢查是否被重導回登入頁
            if "default.aspx" in response.url and "FW99001Z.aspx" not in response.url:
                return (False, "Session 無效,被重導回登入頁")

            # 檢查頁面是否包含登出按鈕或其他用戶相關元素
            soup = BeautifulSoup(response.text, "html.parser")

            # 檢查是否有登出連結 (成功登入的標誌)
            logout_link = soup.find("a", string=lambda t: t and "登出" in t)
            if logout_link:
                logger.info("✓ Session 驗證成功 (找到登出按鈕)")
                return (True, "")

            # 檢查是否有用戶資訊區塊
            user_info = soup.find(id=lambda x: x and ("user" in x.lower() or "member" in x.lower()))
            if user_info:
                logger.info("✓ Session 驗證成功 (找到用戶資訊)")
                return (True, "")

            # 如果沒有明確的登入標示,但 URL 正確,也視為成功 (可能頁面結構變更)
            if "FW99001Z.aspx" in response.url:
                logger.warning("⚠ Session 可能有效 (URL 正確但未找到明確的登入標示)")
                return (True, "")

            return (False, "無法確認 Session 有效性")

        except Exception as e:
            logger.error(f"✗ Session 驗證錯誤: {e}")
            return (False, f"驗證過程發生錯誤: {str(e)}")

    def get_session(self) -> requests.Session:
        """取得已登入的 session"""
        return self.session
