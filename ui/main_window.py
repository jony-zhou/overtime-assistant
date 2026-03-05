"""
主視窗 - 專業 UI/UX 設計
遵循 SOLID、DRY、KISS、YAGNI 原則
"""

import sys
import threading
import logging
from tkinter import messagebox as mb
from typing import Optional
from pathlib import Path
from datetime import datetime
from PIL import Image, ImageTk
import customtkinter as ctk
from src.models import OvertimeReport
from src.models.personal_record import PersonalRecord, PersonalRecordSummary
from src.services import (
    AuthService,
    DataService,
    ExportService,
    UpdateService,
    DataSyncService,
)
from src.services.credential_manager import CredentialManager
from src.core import OvertimeCalculator, VERSION
from src.config import Settings
from ui.components import (
    LoginFrame,
    show_update_dialog,
    OvertimeReportTab,
    AttendanceTab,
    PersonalRecordTab,
    PunchRecordTab,
)
from ui.components.statistics_card import StatisticsCard
from ui.config import (
    colors,
    typography,
    spacing,
    border_radius,
    default_styles,
    get_font_config,
)

# 加入專案根目錄到路徑
sys.path.insert(0, str(Path(__file__).parent.parent))

logger = logging.getLogger(__name__)


class MainWindow(ctk.CTk):
    """
    主視窗

    職責:
    - 管理整體 UI 布局
    - 協調各個元件之間的互動
    - 處理使用者操作流程
    """

    def __init__(self, test_mode: bool = False):
        super().__init__()

        # 測試模式標誌
        self.test_mode = test_mode

        # 統計卡片屬性 (初始化為 None,稍後建立)
        self.card_total_records: Optional[StatisticsCard] = None
        self.card_total_hours: Optional[StatisticsCard] = None
        self.card_avg_hours: Optional[StatisticsCard] = None
        self.card_max_hours: Optional[StatisticsCard] = None
        self.card_unreported: Optional[StatisticsCard] = None

        self.auth_service = None
        self.data_service = None
        self.data_sync_service = None  # 統一資料同步服務
        self.current_report = None
        self.personal_records = []
        self.personal_summary = None
        self.punch_records = []  # 打卡記錄
        self.submitted_records = {}  # 快取已申請記錄
        self._login_password = None  # 清除密碼

        # 初始化屬性
        self.version = VERSION
        self._init_window_settings()
        self._init_services()
        self._init_data()

        # 建立 UI
        self._create_ui()

        # 測試模式：直接載入假數據
        if self.test_mode:
            self._load_mock_data()
        else:
            # 啟動後檢查更新 (非阻塞式)
            self.after(1000, self._check_for_updates)

    def _init_window_settings(self):
        """初始化視窗設定 (Single Responsibility)"""
        title = f"TECO SSP 加班助手 v{self.version}"
        if self.test_mode:
            title += " [測試模式]" 
        self.title(title)
        self.geometry("1200x900")

        # 設定主題
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        # 設定圖示
        self._load_app_icon()

    def _load_app_icon(self):
        """載入應用程式圖示"""
        icon_ico = Path(__file__).parent.parent / "assets" / "icon.ico"
        icon_png = Path(__file__).parent.parent / "assets" / "icon.png"

        try:
            if icon_ico.exists():
                self.iconbitmap(str(icon_ico))
            elif icon_png.exists():

                icon_image = Image.open(str(icon_png))
                photo = ImageTk.PhotoImage(icon_image)
                self.iconphoto(True, photo)
                self._icon_photo = photo  # 保持引用
        except Exception as e:
            logger.debug(f"圖示載入失敗: {e}")

    def _init_services(self):
        """初始化服務 (Dependency Injection 準備)"""
        self.settings = Settings()
        self.credential_manager = CredentialManager()
        self.auth_service: Optional[AuthService] = None
        self.data_service: Optional[DataService] = None
        self.export_service = ExportService(self.settings)
        self.calculator = OvertimeCalculator(self.settings)

    def _init_data(self):
        """初始化資料"""
        self.current_report: Optional[OvertimeReport] = None
        self.personal_records: list[PersonalRecord] = []
        self.personal_summary: Optional[PersonalRecordSummary] = None
        self._login_username: Optional[str] = None
        self._login_password: Optional[str] = None
        self._remember_me: bool = False

    def _create_ui(self):
        """建立使用者介面"""
        # === 主容器 ===
        self.main_container = ctk.CTkFrame(self, fg_color=colors.background_primary)
        self.main_container.pack(fill="both", expand=True)

        if self.test_mode:
            # 測試模式：直接顯示主頁面，不顯示登入頁面
            self._create_main_page()
            self.main_content.pack(fill="both", expand=True)
            # 設定測試用戶資訊
            self._login_username = "測試用戶"
        else:
            # === 登入頁面 (初始顯示) ===
            self._create_login_page()

            # 載入儲存的憑證 (如果有)
            self._load_saved_credentials()

            # === 主頁面 (初始隱藏) ===
            self._create_main_page()

    def _create_login_page(self):
        """建立登入頁面 (DRY - 單一方法負責登入 UI)"""
        self.login_frame = LoginFrame(self.main_container, self.on_login)
        self.login_frame.pack(fill="both", expand=True)

    def _load_saved_credentials(self):
        """
        載入儲存的憑證

        OWASP 考量:
        - 僅在使用者之前選擇「記住我」時才自動填入
        - 不自動登入,仅填入欄位
        """
        if self.credential_manager.has_saved_credentials():
            username, password = self.credential_manager.load_credentials()

            if username:
                self.login_frame.set_account(username)
                self.login_frame.set_remember_me(True)

                if password:
                    self.login_frame.set_password(password)
                    logger.info("已載入儲存的憑證")

    def _create_main_page(self):
        """建立主頁面 (使用分頁介面)"""
        self.main_content = ctk.CTkFrame(
            self.main_container, fg_color=colors.background_primary
        )

        # 建立各個區塊
        self._create_navbar()
        self._create_statistics_section()  # 統計卡片區域 (取代狀態區)
        self._create_tabview()  # 分頁介面
        self._create_footer()

    def _create_navbar(self):
        """建立頂部導覽列 (優化視覺階層)"""
        navbar = ctk.CTkFrame(
            self.main_content,
            fg_color=colors.background_secondary,
            height=64,
            corner_radius=0,
        )
        navbar.pack(fill="x")
        navbar.pack_propagate(False)

        # 導覽列內容容器
        content = ctk.CTkFrame(navbar, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=spacing.lg, pady=spacing.md)

        # 左側: Logo + 標題
        self._create_navbar_left(content)

        # 右側: 使用者資訊 + 登出按鈕
        self._create_navbar_right(content)

    def _create_navbar_left(self, parent):
        """建立導覽列左側 (Logo + 標題)"""
        left_section = ctk.CTkFrame(parent, fg_color="transparent")
        left_section.pack(side="left")

        # Logo (使用 assets 圖示)
        try:
            from PIL import Image
            from pathlib import Path

            # 取得圖示路徑
            icon_path = Path(__file__).parent.parent / "assets" / "icon.png"

            if icon_path.exists():
                # 載入並使用 CTkImage (支援高 DPI)
                img = Image.open(str(icon_path))
                ctk_image = ctk.CTkImage(light_image=img, dark_image=img, size=(32, 32))

                logo = ctk.CTkLabel(left_section, image=ctk_image, text="")
                logo.pack(side="left", padx=(0, spacing.sm))
            else:
                # 降級方案: 使用 emoji
                logo = ctk.CTkLabel(
                    left_section,
                    text="⏰",
                    font=get_font_config(28),
                    text_color=colors.primary,
                )
                logo.pack(side="left", padx=(0, spacing.sm))
        except Exception as e:
            logger.debug(f"載入導覽列圖示失敗: {e}")
            # 降級方案: 使用 emoji
            logo = ctk.CTkLabel(
                left_section,
                text="⏰",
                font=get_font_config(28),
                text_color=colors.primary,
            )
            logo.pack(side="left", padx=(0, spacing.sm))

        # 標題
        title = ctk.CTkLabel(
            left_section,
            text="TECO SSP 加班助手",
            font=get_font_config(typography.size_h3, typography.weight_bold),
            text_color=colors.text_primary,
        )
        title.pack(side="left")

    def _create_navbar_right(self, parent):
        """建立導覽列右側 (使用者資訊 + 檢查更新 + 登出)"""
        right_section = ctk.CTkFrame(parent, fg_color="transparent")
        right_section.pack(side="right")

        # 使用者標籤
        self.user_label = ctk.CTkLabel(
            right_section,
            text="👤 使用者",
            font=get_font_config(typography.size_body),
            text_color=colors.text_secondary,
        )
        self.user_label.pack(side="left", padx=(0, spacing.md))

        # 檢查更新按鈕
        self.check_update_button = ctk.CTkButton(
            right_section,
            text="🔄 檢查更新",
            width=100,
            height=36,
            font=get_font_config(typography.size_body),
            fg_color=colors.info,
            hover_color=colors.info_hover,
            command=self.on_check_update,
        )
        self.check_update_button.pack(side="left", padx=(0, spacing.sm))

        # 登出按鈕
        self.logout_button = ctk.CTkButton(
            right_section,
            **default_styles.ERROR_BUTTON,
            text="🚪 登出",
            width=100,
            height=36,
            font=get_font_config(typography.size_body),
            command=self.on_logout,
        )
        self.logout_button.pack(side="left")

    def _create_tabview(self):
        """建立分頁介面 (優化視覺設計)"""
        # 分頁容器
        self.tabview = ctk.CTkTabview(
            self.main_content,
            fg_color=colors.background_primary,
            segmented_button_fg_color=colors.background_secondary,
            segmented_button_selected_color=colors.primary,
            segmented_button_selected_hover_color=colors.primary_hover,
            segmented_button_unselected_color=colors.background_tertiary,
            segmented_button_unselected_hover_color=colors.background_secondary,
            border_width=0,
            corner_radius=border_radius.md,
        )
        self.tabview.pack(
            fill="both", expand=True, padx=spacing.lg, pady=(0, spacing.md)
        )

        # 建立分頁 1: 異常清單 (優先載入 - 預設顯示)
        self.tabview.add("📅 異常清單")
        self.attendance_tab = AttendanceTab(
            self.tabview.tab("📅 異常清單"),
            on_export=self.on_export,
            on_refresh=self.on_refresh,
        )
        self.attendance_tab.pack(fill="both", expand=True, padx=0, pady=0)

        # 建立分頁 2: 加班補報 (主要功能)
        self.tabview.add("⚙️ 加班補報")
        self.overtime_tab = OvertimeReportTab(self.tabview.tab("⚙️ 加班補報"))
        self.overtime_tab.pack(fill="both", expand=True, padx=0, pady=0)

        # 建立分頁 3: 打卡記錄 (輔助參考)
        self.tabview.add("🕐 打卡記錄")
        self.punch_record_tab = PunchRecordTab(self.tabview.tab("🕐 打卡記錄"))
        self.punch_record_tab.pack(fill="both", expand=True, padx=0, pady=0)

        # 建立分頁 4: 個人記錄 (歷史記錄)
        self.tabview.add("📊 個人記錄")
        self.personal_record_tab = PersonalRecordTab(self.tabview.tab("📊 個人記錄"))
        self.personal_record_tab.pack(fill="both", expand=True, padx=0, pady=0)
        # 覆寫重新整理方法
        self.personal_record_tab.on_refresh = self.on_refresh_personal_records

        # 預設顯示異常清單分頁 (優先載入,避免顯示"請登入"過久)
        self.tabview.set("📅 異常清單")

    def _create_statistics_section(self):
        """建立統計卡片區域 (始終顯示)"""
        self.stats_container = ctk.CTkFrame(self.main_content, fg_color="transparent")
        self.stats_container.pack(fill="x", padx=spacing.lg, pady=spacing.md)

        # Grid 布局 (5 欄)
        self.stats_container.grid_columnconfigure((0, 1, 2, 3, 4), weight=1)

        # 建立 4 張統計卡片
        self._create_statistics_cards()

    def _create_statistics_cards(self):
        """建立統計卡片"""
        from ui.components.statistics_card import StatisticsCard

        # 卡片配置 (重點: 待申請資訊)
        cards_config = [
            {
                "attr": "card_total_records",
                "title": "待申請",
                "value": "0",
                "icon": "⚠️",
                "color": colors.error,  # 紅色警示
                "column": 0,
            },
            {
                "attr": "card_total_hours",
                "title": "已申請",
                "value": "0",
                "icon": "✔️",
                "color": colors.success,  # 綠色
                "column": 1,
            },
            {
                "attr": "card_avg_hours",
                "title": "平均加班時數",
                "value": "0.0 小時",
                "icon": "📊",
                "color": colors.info,  # 藍色資訊
                "column": 2,
            },
            {
                "attr": "card_max_hours",
                "title": "最高加班時數",
                "value": "0.0 小時",
                "icon": "🔥",
                "color": colors.warning,  # 橘色
                "column": 3,
            },
            {
                "attr": "card_unreported",
                "title": "總加班時數",
                "value": "0.0 小時",
                "icon": "⏱️",
                "color": colors.success,  # 綠色
                "column": 4,
            },
        ]

        # 動態建立卡片
        for config in cards_config:
            card = StatisticsCard(
                self.stats_container,
                title=config["title"],
                value=config["value"],
                icon=config["icon"],
                color=config["color"],
            )
            card.grid(
                row=0,
                column=config["column"],
                padx=spacing.sm,
                pady=spacing.md,
                sticky="ew",
            )
            setattr(self, config["attr"], card)

    def _create_footer(self):
        """建立底部資訊列"""
        footer = ctk.CTkFrame(
            self.main_content,
            fg_color=colors.background_secondary,
            height=40,
            corner_radius=0,
        )
        footer.pack(fill="x", side="bottom")
        footer.pack_propagate(False)

        # Footer 內容
        content = ctk.CTkFrame(footer, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=spacing.lg)

        # 左側: 更新時間
        self.update_time_label = ctk.CTkLabel(
            content,
            text="最後更新: --",
            font=get_font_config(typography.size_caption),
            text_color=colors.text_tertiary,
        )
        self.update_time_label.pack(side="left")

        # 右側: 版本號
        version_label = ctk.CTkLabel(
            content,
            text=f"v{self.version}",
            font=get_font_config(typography.size_caption),
            text_color=colors.text_tertiary,
        )
        version_label.pack(side="right")

    # === 事件處理方法 ===

    def on_login(self, username: str, password: str, remember_me: bool = False):
        """
        登入處理

        遵循 OWASP 最佳實踐:
        - 不在 log 中記錄密碼
        - 使用安全的認證服務
        """
        self.login_frame.set_loading(True)

        # 儲存登入資訊 (密碼僅在記住我時儲存)
        self._login_username = username
        self._remember_me = remember_me
        if remember_me:
            self._login_password = password  # TODO: Task 5 - 改用 keyring 加密儲存

        # 背景執行登入 (避免阻塞 UI)
        self._execute_in_background(
            self._login_task,
            args=(username, password),
            callback=self._on_login_complete,
        )

    def _login_task(self, username: str, password: str) -> tuple[bool, Optional[str]]:
        """
        登入任務 (背景執行)

        Returns:
            tuple: (成功狀態, 錯誤訊息)
        """
        try:
            self.auth_service = AuthService(self.settings)
            success = self.auth_service.login(username, password)
            return (success, None)
        except Exception as e:
            logger.error(f"登入錯誤: {e}", exc_info=True)
            return (False, str(e))

    def _on_login_complete(self, result: tuple[bool, Optional[str]]):
        """登入完成回調"""
        success, error = result
        self.login_frame.set_loading(False)

        if success:
            # 儲存憑證 (如果選擇記住我)
            if self._remember_me:
                self.credential_manager.save_credentials(
                    self._login_username, self._login_password
                )
            else:
                # 清除之前儲存的憑證
                self.credential_manager.clear_credentials()

            self._switch_to_main_page()
            self._start_data_fetch()
        else:
            self._show_login_error(error)

    def _switch_to_main_page(self):
        """切換到主頁面 (DRY - 統一的頁面切換邏輯)"""
        # 隱藏登入頁面
        self.login_frame.pack_forget()

        # 顯示主頁面
        self.main_content.pack(fill="both", expand=True)

        # 更新使用者資訊
        if self._login_username:
            self.user_label.configure(text=f"👤 {self._login_username}")

    def _start_data_fetch(self):
        """開始資料抓取"""
        # 建立統一資料同步服務 (取代 DataService + PersonalRecordService)
        session = self.auth_service.get_session()
        self.data_sync_service = DataSyncService(session, self.settings)

        # 保留舊 DataService 作為備用 (用於某些特殊情況)
        self.data_service = DataService(session, self.settings)

        # 抓取資料
        self.fetch_data()

    def _show_login_error(self, error: Optional[str]):
        """顯示登入錯誤 (OWASP - 不洩漏過多系統資訊)"""
        import tkinter.messagebox as mb

        error_msg = "登入失敗,請檢查帳號密碼" if not error else f"登入失敗: {error}"
        mb.showerror("登入失敗", error_msg)

    def fetch_data(self):
        """抓取出勤資料"""
        self._execute_in_background(
            self._fetch_data_task, callback=self._on_fetch_complete
        )

    def _fetch_data_task(
        self,
    ) -> tuple[
        Optional[OvertimeReport],
        Optional[str],
        list[PersonalRecord],
        Optional[PersonalRecordSummary],
        dict,
    ]:
        """
        資料抓取任務 (背景執行)

        使用 DataSyncService 進行統一資料同步,減少重複請求

        最佳實踐:
        - 一次性抓取所有資料 (異常、個人記錄、已申請狀態)
        - 避免分頁切換時重複查詢
        - 使用快取機制提升效能

        Returns:
            tuple: (報表資料, 錯誤訊息, 個人記錄, 個人記錄摘要, 已申請記錄)
        """
        from src.services.overtime_status_service import OvertimeStatusService

        try:
            submitted_records = {}

            # 使用 DataSyncService 統一抓取所有資料 (一次抓取,減少重複請求)
            if self.data_sync_service:
                # 同步所有資料 (打卡/假別/額度/異常/個人記錄)
                _snapshot = self.data_sync_service.sync_all()

                # 使用 adapter 轉換為舊格式 (向後相容)
                raw_records = self.data_sync_service.get_attendance_records()
                personal_records, personal_summary = (
                    self.data_sync_service.get_personal_records()
                )

                # 一併抓取已申請狀態 (避免後續重複查詢)
                if self.auth_service:
                    session = self.auth_service.get_session()
                    status_service = OvertimeStatusService(self.settings)
                    submitted_records = status_service.fetch_submitted_records(session)

                logger.info(
                    "DataSyncService 同步完成: %d 筆異常, %d 筆個人記錄, %d 筆已申請",
                    len(raw_records),
                    len(personal_records),
                    len(submitted_records),
                )
            else:
                # Fallback: 使用舊服務 (未初始化 DataSyncService 時)
                raw_records = self.data_service.get_attendance_data()
                personal_records, personal_summary = [], None

            if not raw_records:
                return (
                    None,
                    "沒有找到出勤記錄",
                    personal_records,
                    personal_summary,
                    submitted_records,
                )

            report = self.calculator.calculate_overtime(raw_records)
            return (report, None, personal_records, personal_summary, submitted_records)

        except Exception as e:
            logger.error(f"抓取資料錯誤: {e}", exc_info=True)
            return (None, str(e), [], None, {})

    def _on_fetch_complete(
        self,
        result: tuple[
            Optional[OvertimeReport],
            Optional[str],
            list[PersonalRecord],
            Optional[PersonalRecordSummary],
            dict,
        ],
    ):
        """資料抓取完成回調"""
        report, error, personal_records, personal_summary, submitted_records = result

        # 儲存個人記錄和已申請記錄
        self.personal_records = personal_records
        self.personal_summary = personal_summary
        self.submitted_records = submitted_records  # 快取已申請記錄

        # 顯示個人記錄
        if personal_records and personal_summary:
            self.personal_record_tab.display_records(personal_records, personal_summary)

        # 顯示打卡記錄 (新增)
        if self.data_sync_service:
            punch_records = self.data_sync_service.get_punch_records()
            self.punch_records = punch_records
            self.punch_record_tab.display_records(punch_records)
            logger.info("打卡記錄顯示完成: %d 筆", len(punch_records))

        if report and report.records:
            self._handle_successful_fetch(report)
        else:
            self._handle_failed_fetch(error)

    def _handle_successful_fetch(self, report: OvertimeReport):
        """處理成功的資料抓取 (載入資料到分頁)"""
        self.current_report = report

        # 顯示並更新統計卡片
        self.stats_container.pack(fill="x", padx=spacing.lg, pady=(0, spacing.md))
        self._update_statistics_cards(report)

        # 載入資料到異常清單分頁
        self.attendance_tab.display_report(report)

        # 載入資料到加班補報分頁
        submission_records = report.to_submission_records()
        if self.auth_service and hasattr(self.auth_service, "get_session"):
            session = self.auth_service.get_session()
            self.overtime_tab.load_data(submission_records, session)

        # 更新時間戳記
        self._update_timestamp()

    def _update_statistics_cards(self, report: OvertimeReport):
        """更新統計卡片數據

        計算邏輯:
        - 第1張: 待申請筆數 (紅色警示)
        - 第2張: 已申請 (已申請的記錄)
        - 第3張: 平均加班時數
        - 第4張: 最高加班時數
        - 第5張: 總加班時數
        """
        if not all(
            [
                self.card_total_records,
                self.card_total_hours,
                self.card_avg_hours,
                self.card_max_hours,
                self.card_unreported,
            ]
        ):
            return

        # 計算待申請與已申請
        total_anomaly = len(report.records) if report and report.records else 0
        submitted_count = len(self.submitted_records) if self.submitted_records else 0
        pending_count = max(0, total_anomaly - submitted_count)

        # 計算申請中筆數 (已申請但未核准的)
        in_progress_count = 0
        if self.personal_records:
            for personal_record in self.personal_records:
                # 申請中的狀態: 未撤銷、未核准、未退件
                if personal_record.status not in ["已撤銷", "已核准", "已退件"]:
                    in_progress_count += 1

        # 計算加班時數統計
        total_hours = 0.0
        hours_list = []

        if self.personal_records:
            for personal_record in self.personal_records:
                if personal_record.overtime_hours:
                    total_hours += personal_record.overtime_hours
                    hours_list.append(personal_record.overtime_hours)

        # 平均與最高時數
        avg_hours = total_hours / len(hours_list) if hours_list else 0.0
        max_hours = max(hours_list) if hours_list else 0.0

        logger.debug(
            "統計卡片: 待申請=%d, 已申請=%d, 總時數=%.2f, 平均=%.2f, 最高=%.2f",
            pending_count,
            in_progress_count,
            total_hours,
            avg_hours,
            max_hours,
        )

        # 第1張: 待申請筆數 (紅色警示)
        self.card_total_records.update_value(str(pending_count))

        # 第2張: 已申請
        self.card_total_hours.update_value(str(in_progress_count))

        # 第3張: 平均加班時數
        self.card_avg_hours.update_value(f"{avg_hours:.2f} 小時")

        # 第4張: 最高加班時數
        self.card_max_hours.update_value(f"{max_hours:.2f} 小時")

        # 第5張: 總加班時數
        self.card_unreported.update_value(f"{total_hours:.2f} 小時")

    def _show_report(self, report: OvertimeReport):
        """
        [已廢棄] 舊版報表顯示 (分頁模式已整合至 AttendanceTab)
        保留此方法以避免破壞現有程式碼
        """
        pass

    def _update_timestamp(self):
        """更新時間戳記"""
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.update_time_label.configure(text=f"最後更新: {current_time}")

    def _handle_failed_fetch(self, error: Optional[str]):
        """處理失敗的資料抓取"""
        error_msg = f"抓取資料失敗: {error}" if error else "抓取資料失敗"
        mb.showerror("錯誤", error_msg)

    def on_export(self):
        """匯出處理"""
        if not self.current_report:
            mb.showerror("錯誤", "沒有可匯出的資料")
            return

        self._execute_in_background(
            self._export_task, callback=self._on_export_complete
        )

    def _export_task(self) -> tuple[Optional[str], Optional[str]]:
        """
        匯出任務 (背景執行)

        Returns:
            tuple: (檔案名稱, 錯誤訊息)
        """
        try:
            filename = self.export_service.export_to_excel(self.current_report)
            return (filename, None)
        except Exception as e:
            logger.error(f"匯出錯誤: {e}", exc_info=True)
            return (None, str(e))

    def _on_export_complete(self, result: tuple[Optional[str], Optional[str]]):
        """匯出完成回調"""
        filename, error = result

        if filename:
            mb.showinfo("匯出成功", f"已匯出至: {filename}")
        else:
            error_msg = f"匯出錯誤: {error}" if error else "匯出失敗"
            mb.showerror("匯出失敗", error_msg)

    def on_refresh(self):
        """重新整理資料 (分頁模式)

        使用 DataSyncService 的快取機制:
        - 如果快取有效 (5 分鐘內),直接返回
        - 否則重新抓取
        """
        if not self.data_sync_service and not self.data_service:
            mb.showerror("錯誤", "請先登入")
            return

        # 使用快取優先 (不強制重新整理)
        self.fetch_data()

    def on_refresh_personal_records(self):
        """重新整理個人記錄 (使用增量同步)

        使用 DataSyncService.sync_overtime_status() 增量同步:
        - 僅更新已申請記錄的狀態
        - 不重新抓取出勤資料
        - 比完整同步更快 (1 次 HTTP vs 2 次)
        """
        if not self.data_sync_service:
            mb.showerror("錯誤", "請先登入")
            return

        self._execute_in_background(
            self._fetch_personal_records_task,
            callback=self._on_personal_records_complete,
        )

    def _fetch_personal_records_task(
        self,
    ) -> tuple[list[PersonalRecord], Optional[PersonalRecordSummary], Optional[str]]:
        """
        個人記錄抓取任務 (背景執行)

        使用 DataSyncService.sync_overtime_status() 增量同步

        Returns:
            tuple: (個人記錄列表, 摘要, 錯誤訊息)
        """
        try:
            # 使用 DataSyncService 增量同步
            if self.data_sync_service:
                self.data_sync_service.sync_overtime_status()
                personal_records, personal_summary = (
                    self.data_sync_service.get_personal_records()
                )
            else:
                # Fallback: 使用舊服務 (不應該發生)
                logger.warning("未初始化 DataSyncService, 使用完整同步")
                return ([], None, "DataSyncService 未初始化")

            return (personal_records, personal_summary, None)
        except Exception as e:
            logger.error(f"個人記錄載入錯誤: {e}", exc_info=True)
            return ([], None, str(e))

    def _on_personal_records_complete(
        self,
        result: tuple[
            list[PersonalRecord], Optional[PersonalRecordSummary], Optional[str]
        ],
    ):
        """個人記錄載入完成回調"""
        personal_records, personal_summary, error = result

        if personal_records and personal_summary:
            self.personal_records = personal_records
            self.personal_summary = personal_summary
            self.personal_record_tab.display_records(personal_records, personal_summary)

            # 更新統計卡片 (如果有異常清單資料)
            if self.current_report:
                self._update_statistics_cards(self.current_report)

            mb.showinfo("成功", f"成功載入 {len(personal_records)} 筆個人記錄")
        else:
            error_msg = f"載入個人記錄失敗: {error}" if error else "載入個人記錄失敗"
            mb.showerror("錯誤", error_msg)

    def on_logout(self):
        """
        登出處理

        OWASP 最佳實踐:
        - 清除所有敏感資料
        - 重置 UI 狀態
        """
        # 清除服務和資料
        self._clear_sensitive_data()

        # 重置 UI
        self._switch_to_login_page()

    def on_check_update(self):
        """手動檢查更新"""
        logger.info("使用者手動觸發更新檢查")

        # 禁用按鈕,避免重複點擊
        self.check_update_button.configure(state="disabled", text="🔄 檢查中...")

        # 背景執行檢查
        self._execute_in_background(
            self._check_update_task, callback=self._on_manual_update_check_complete
        )

    def _on_manual_update_check_complete(self, update_info: Optional[dict]):
        """手動檢查更新完成回調"""
        # 恢復按鈕狀態
        self.check_update_button.configure(state="normal", text="🔄 檢查更新")

        if update_info:
            if update_info.get("has_update"):
                logger.info(f"發現新版本 {update_info.get('latest_version')}")
                show_update_dialog(self, update_info)
            else:
                mb.showinfo(
                    "已是最新版本",
                    f"目前版本 v{update_info.get('current_version')} 已是最新版本!",
                )
        else:
            mb.showerror("檢查失敗", "無法檢查更新,請確認網路連線正常")

    def _clear_sensitive_data(self):
        """
        清除敏感資料 (OWASP)

        注意: 不清除儲存的憑證,僅清除記憶體中的資料
        使用者下次登入時仍可使用記住我功能
        """

        # 清空個人記錄分頁
        if hasattr(self, "personal_record_tab"):
            self.personal_record_tab.clear_table()

    def _switch_to_login_page(self):
        """切換到登入頁面 (分頁模式)"""
        # 隱藏主頁面
        self.main_content.pack_forget()

        # 顯示登入頁面
        self.login_frame.pack(fill="both", expand=True)

        # 清空密碼欄位 (OWASP)
        if hasattr(self.login_frame, "password_entry"):
            self.login_frame.password_entry.delete(0, "end")

    def _check_for_updates(self):
        """背景檢查版本更新"""
        logger.info("開始檢查應用程式更新...")

        self._execute_in_background(
            self._check_update_task, callback=self._on_update_check_complete
        )

    def _check_update_task(self) -> Optional[dict]:
        """
        更新檢查任務

        Returns:
            dict: 更新資訊 或 None
        """
        try:
            update_service = UpdateService()
            return update_service.check_for_updates(timeout=5)
        except Exception as e:
            logger.warning(f"版本更新檢查失敗: {e}")
            return None

    def _on_update_check_complete(self, update_info: Optional[dict]):
        """更新檢查完成回調"""
        if update_info and update_info.get("has_update"):
            logger.info(f"發現新版本 {update_info.get('latest_version')}")
            show_update_dialog(self, update_info)
        else:
            logger.info("目前已是最新版本")

    # === 測試模式相關方法 ===

    def _load_mock_data(self):
        """載入假數據（測試模式）"""
        try:
            from src.utils.mock_data import MockDataGenerator

            logger.info("測試模式：載入假數據...")

            # 生成假數據
            attendance_records = MockDataGenerator.generate_attendance_records(30)
            personal_records = MockDataGenerator.generate_personal_records(20)
            personal_summary = MockDataGenerator.generate_personal_summary(
                personal_records
            )
            punch_records = MockDataGenerator.generate_punch_records(30)

            # 直接創建加班報表（不通過計算器，因為假數據已經有加班時數）
            report = MockDataGenerator.generate_overtime_report(attendance_records)

            # 設定資料
            self.current_report = report
            self.personal_records = personal_records
            self.personal_summary = personal_summary
            self.punch_records = punch_records

            # 顯示資料
            self._display_mock_data(report, personal_records, personal_summary, punch_records)

            logger.info(
                "測試模式：假數據載入完成 (%d 筆出勤, %d 筆個人記錄, %d 筆打卡)",
                len(attendance_records),
                len(personal_records),
                len(punch_records),
            )
        except Exception as e:
            logger.error(f"測試模式：載入假數據失敗: {e}", exc_info=True)
            mb.showerror("錯誤", f"載入測試數據失敗: {e}")

    def _display_mock_data(
        self,
        report: OvertimeReport,
        personal_records: list,
        personal_summary: PersonalRecordSummary,
        punch_records: list,
    ):
        """顯示假數據到各個分頁"""
        # 更新使用者資訊
        if self._login_username:
            self.user_label.configure(text=f"👤 {self._login_username}")

        # 顯示統計卡片
        self.stats_container.pack(fill="x", padx=spacing.lg, pady=(0, spacing.md))
        self._update_statistics_cards(report)

        # 顯示出勤記錄
        self.attendance_tab.display_report(report)

        # 顯示個人記錄
        self.personal_record_tab.display_records(personal_records, personal_summary)

        # 顯示打卡記錄
        self.punch_record_tab.display_records(punch_records)

        # 顯示加班申報（測試模式下禁用申報功能）
        submission_records = report.to_submission_records()
        self.overtime_tab.load_data(submission_records, None)  # session=None 在測試模式
        
        # 顯示測試模式提示
        self.overtime_tab._show_status(
            "⚠️ 測試模式：申報功能已禁用，此模式僅用於查看 UI",
            colors.warning
        )

        # 更新時間戳記
        self._update_timestamp()

    # === 工具方法 ===

    def _execute_in_background(
        self, task: callable, args: tuple = (), callback: Optional[callable] = None
    ):
        """
        在背景執行任務 (DRY - 統一的背景任務執行模式)

        Args:
            task: 要執行的任務函式
            args: 任務參數
            callback: 完成後的回調函式
        """

        def thread_func():
            result = task(*args)
            if callback:
                self.after(0, callback, result)

        thread = threading.Thread(target=thread_func, daemon=True)
        thread.start()
