"""
應用程式更新通知對話框
現代化設計 - 參考 VS Code, Slack, Discord 等主流應用
"""

import customtkinter as ctk
import webbrowser
from typing import Dict, Any, Optional
from pathlib import Path
from PIL import Image
import logging

logger = logging.getLogger(__name__)


class UpdateDialog(ctk.CTkToplevel):
    """
    更新通知對話框 - 現代化設計

    設計靈感:
    - VS Code 更新通知: 簡潔、專業
    - Slack 更新提示: 友善、清晰
    - Discord 更新介面: 現代、美觀

    設計原則:
    - 視覺層次清晰
    - 重要資訊突出
    - 操作路徑明確
    - 色彩和諧統一
    """

    def __init__(self, parent: ctk.CTk, update_info: Dict[str, Any]):
        """
        初始化更新對話框

        Args:
            parent: 父視窗
            update_info: 更新資訊字典
        """
        super().__init__(parent)

        self.update_info = update_info

        # 除錯日誌
        logger.info("=" * 50)
        logger.info("更新對話框資料:")
        logger.info(f"  has_update: {update_info.get('has_update')}")
        logger.info(f"  current_version: {update_info.get('current_version')}")
        logger.info(f"  latest_version: {update_info.get('latest_version')}")
        logger.info(f"  download_url: {update_info.get('download_url')}")
        logger.info(f"  release_url: {update_info.get('release_url')}")
        logger.info(f"  published_at: {update_info.get('published_at')}")
        logger.info("=" * 50)

        # 視窗設定
        self.title("軟體更新")
        self.geometry("560x650")
        self.resizable(False, False)

        # 設定圖示
        self._load_window_icon()

        # 置中顯示
        self._center_window()
        self.transient(parent)
        self.grab_set()

        # 建立 UI
        self._create_widgets()

        # 聚焦到此視窗
        self.focus()

    def _load_window_icon(self):
        """載入視窗圖示 (Favicon)"""
        try:
            # 取得圖示路徑
            icon_ico = Path(__file__).parent.parent.parent / "assets" / "icon.ico"
            icon_png = Path(__file__).parent.parent.parent / "assets" / "icon.png"

            logger.debug(f"嘗試載入視窗圖示: {icon_ico}")
            logger.debug(f".ico 檔案存在: {icon_ico.exists()}")
            logger.debug(f".png 檔案存在: {icon_png.exists()}")

            # Windows 優先使用 .ico 格式
            if icon_ico.exists():
                logger.info(f"載入視窗圖示: {icon_ico}")
                self.iconbitmap(str(icon_ico))

                # 同時設定 iconphoto (某些情況下需要)
                if icon_png.exists():
                    try:
                        from PIL import ImageTk

                        icon_image = Image.open(str(icon_png))
                        photo = ImageTk.PhotoImage(icon_image)
                        self.iconphoto(True, photo)
                        self._icon_photo = photo  # 保持引用
                    except Exception:
                        pass
            elif icon_png.exists():
                # 降級方案: 使用 PNG
                logger.info(f"使用 PNG 作為視窗圖示: {icon_png}")
                from PIL import ImageTk

                icon_image = Image.open(str(icon_png))
                photo = ImageTk.PhotoImage(icon_image)
                self.iconphoto(True, photo)
                self._icon_photo = photo
            else:
                logger.warning("找不到視窗圖示檔案")
        except Exception as e:
            logger.warning(f"視窗圖示載入失敗: {e}")

    def _center_window(self):
        """將視窗置中顯示"""
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f"{width}x{height}+{x}+{y}")

    def _create_widgets(self) -> None:
        """建立 UI 元件 - 現代化設計"""
        # === 主容器 ===
        main_container = ctk.CTkFrame(self, fg_color="#1a1a1a", corner_radius=0)
        main_container.pack(fill="both", expand=True)

        # === 頂部橫幅區域 (深色背景 + 漸層效果) ===
        self._create_header_section(main_container)

        # === 內容區域 (淺色背景) ===
        content_frame = ctk.CTkFrame(
            main_container, fg_color="#2b2b2b", corner_radius=0
        )
        content_frame.pack(fill="both", expand=True, padx=0, pady=0)

        # 內容容器 (加入邊距)
        content_container = ctk.CTkFrame(content_frame, fg_color="transparent")
        content_container.pack(fill="both", expand=True, padx=30, pady=20)

        # 版本資訊卡片
        self._create_version_card(content_container)

        # 更新內容區域
        self._create_release_notes_section(content_container)

        # 下載連結區域
        self._create_download_section(content_container)

        # === 底部操作按鈕區域 ===
        self._create_action_buttons(main_container)

    def _create_header_section(self, parent):
        """建立頂部橫幅區域"""
        header = ctk.CTkFrame(parent, fg_color="#0d7377", height=140, corner_radius=0)
        header.pack(fill="x")
        header.pack_propagate(False)

        # 圖示 + 標題容器
        title_container = ctk.CTkFrame(header, fg_color="transparent")
        title_container.pack(expand=True)

        # 應用程式圖示 (大圖示)
        try:
            icon_path = Path(__file__).parent.parent.parent / "assets" / "icon.png"
            if icon_path.exists():
                img = Image.open(str(icon_path))
                ctk_image = ctk.CTkImage(light_image=img, dark_image=img, size=(64, 64))
                icon_label = ctk.CTkLabel(title_container, image=ctk_image, text="")
                icon_label.pack(pady=(10, 5))
            else:
                # 降級方案: 使用 emoji
                icon_label = ctk.CTkLabel(
                    title_container,
                    text="🎉",
                    font=ctk.CTkFont(size=48),
                )
                icon_label.pack(pady=(10, 5))
        except Exception as e:
            logger.debug(f"圖示載入失敗: {e}")
            icon_label = ctk.CTkLabel(
                title_container,
                text="🎉",
                font=ctk.CTkFont(size=48),
            )
            icon_label.pack(pady=(10, 5))

        # 主標題
        title = ctk.CTkLabel(
            title_container,
            text="發現新版本",
            font=ctk.CTkFont(size=28, weight="bold"),
            text_color="#ffffff",
        )
        title.pack()

        # 副標題
        subtitle = ctk.CTkLabel(
            title_container,
            text="有更棒的功能等著您體驗!",
            font=ctk.CTkFont(size=13),
            text_color="#d0f4f7",
        )
        subtitle.pack(pady=(5, 10))

    def _create_version_card(self, parent):
        """建立版本資訊卡片"""
        card = ctk.CTkFrame(parent, fg_color="#323232", corner_radius=12)
        card.pack(fill="x", pady=(0, 15))

        card_content = ctk.CTkFrame(card, fg_color="transparent")
        card_content.pack(fill="x", padx=20, pady=15)

        current_ver = self.update_info.get("current_version", "Unknown")
        latest_ver = self.update_info.get("latest_version", "Unknown")

        # 使用 Grid 布局
        card_content.grid_columnconfigure((0, 1, 2), weight=1)

        # 當前版本
        current_container = ctk.CTkFrame(card_content, fg_color="transparent")
        current_container.grid(row=0, column=0, padx=10, sticky="ew")

        ctk.CTkLabel(
            current_container,
            text="目前版本",
            font=ctk.CTkFont(size=12),
            text_color="#9e9e9e",
        ).pack()
        ctk.CTkLabel(
            current_container,
            text=f"v{current_ver}",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color="#ffffff",
        ).pack(pady=(5, 0))

        # 箭頭
        arrow_container = ctk.CTkFrame(card_content, fg_color="transparent")
        arrow_container.grid(row=0, column=1, padx=10)

        ctk.CTkLabel(
            arrow_container,
            text="→",
            font=ctk.CTkFont(size=28),
            text_color="#0d7377",
        ).pack(pady=10)

        # 最新版本
        latest_container = ctk.CTkFrame(card_content, fg_color="transparent")
        latest_container.grid(row=0, column=2, padx=10, sticky="ew")

        ctk.CTkLabel(
            latest_container,
            text="最新版本",
            font=ctk.CTkFont(size=12),
            text_color="#9e9e9e",
        ).pack()
        ctk.CTkLabel(
            latest_container,
            text=f"v{latest_ver}",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color="#14ffec",
        ).pack(pady=(5, 0))

        # 發布日期
        published_at = self.update_info.get("published_at", "")
        if published_at:
            try:
                from datetime import datetime

                pub_date = datetime.fromisoformat(published_at.replace("Z", "+00:00"))
                date_str = pub_date.strftime("%Y年%m月%d日")

                date_label = ctk.CTkLabel(
                    card,
                    text=f"📅 發布於 {date_str}",
                    font=ctk.CTkFont(size=11),
                    text_color="#757575",
                )
                date_label.pack(pady=(0, 10))
            except Exception:
                pass

    def _create_release_notes_section(self, parent):
        """建立更新內容區域"""
        # 標題
        notes_title = ctk.CTkLabel(
            parent,
            text="📋 更新內容",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="#ffffff",
            anchor="w",
        )
        notes_title.pack(fill="x", pady=(0, 8))

        # 內容文字框 (深色背景)
        notes_frame = ctk.CTkFrame(parent, fg_color="#323232", corner_radius=8)
        notes_frame.pack(fill="both", expand=True, pady=(0, 15))

        notes_text = ctk.CTkTextbox(
            notes_frame,
            font=ctk.CTkFont(size=12),
            fg_color="#323232",
            text_color="#e0e0e0",
            wrap="word",
            corner_radius=8,
        )
        notes_text.pack(fill="both", expand=True, padx=2, pady=2)

        release_notes = self.update_info.get("release_notes", "無更新說明")
        notes_text.insert("1.0", release_notes)
        notes_text.configure(state="disabled")

    def _create_download_section(self, parent):
        """建立下載連結區域"""
        download_url = self.update_info.get("download_url", "")
        release_url = self.update_info.get("release_url", "")

        logger.info(f"對話框中的 download_url: '{download_url}'")
        logger.info(f"對話框中的 release_url: '{release_url}'")

        # 下載資訊卡片
        download_card = ctk.CTkFrame(parent, fg_color="#1e3a3f", corner_radius=8)
        download_card.pack(fill="x", pady=(0, 15))

        download_content = ctk.CTkFrame(download_card, fg_color="transparent")
        download_content.pack(fill="x", padx=15, pady=12)

        if download_url or release_url:
            url_to_display = download_url if download_url else release_url

            # 圖示 + 文字
            icon_label = ctk.CTkLabel(
                download_content,
                text="📥",
                font=ctk.CTkFont(size=16),
            )
            icon_label.pack(side="left", padx=(0, 8))

            # 連結按鈕
            display_url = url_to_display
            if len(display_url) > 55:
                display_url = display_url[:52] + "..."

            url_button = ctk.CTkButton(
                download_content,
                text=display_url,
                command=lambda: self._open_url(url_to_display),
                font=ctk.CTkFont(size=11, underline=True),
                fg_color="transparent",
                text_color="#14ffec",
                hover_color="#0d7377",
                anchor="w",
                cursor="hand2",
            )
            url_button.pack(side="left", fill="x", expand=True)
        else:
            # 無連結提示
            warning_label = ctk.CTkLabel(
                download_content,
                text="⚠️ 無可用的下載連結,請前往 GitHub Releases 頁面",
                font=ctk.CTkFont(size=11),
                text_color="#ff9800",
            )
            warning_label.pack()

    def _create_action_buttons(self, parent):
        """建立底部操作按鈕"""
        button_container = ctk.CTkFrame(
            parent, fg_color="#1f1f1f", height=90, corner_radius=0
        )
        button_container.pack(fill="x", side="bottom")
        button_container.pack_propagate(False)

        button_frame = ctk.CTkFrame(button_container, fg_color="transparent")
        button_frame.pack(fill="x", padx=30, pady=15)

        # 主要操作按鈕 (下載並關閉)
        primary_btn = ctk.CTkButton(
            button_frame,
            text="⬇️  立即下載並關閉程式",
            command=self._on_download_and_close,
            font=ctk.CTkFont(size=14, weight="bold"),
            height=45,
            fg_color="#0d7377",
            hover_color="#14ffec",
            text_color="#ffffff",
            corner_radius=8,
        )
        primary_btn.pack(fill="x", pady=(0, 8))

        # 次要操作按鈕容器
        secondary_frame = ctk.CTkFrame(button_frame, fg_color="transparent")
        secondary_frame.pack(fill="x")

        # 僅開啟下載頁面
        secondary_btn = ctk.CTkButton(
            secondary_frame,
            text="🌐 開啟下載頁面",
            command=self._on_download,
            font=ctk.CTkFont(size=12),
            height=38,
            fg_color="#424242",
            hover_color="#616161",
            text_color="#e0e0e0",
            corner_radius=6,
        )
        secondary_btn.pack(side="left", fill="x", expand=True, padx=(0, 5))

        # 稍後提醒
        later_btn = ctk.CTkButton(
            secondary_frame,
            text="稍後提醒",
            command=self._on_later,
            font=ctk.CTkFont(size=12),
            height=38,
            fg_color="transparent",
            hover_color="#424242",
            text_color="#9e9e9e",
            border_width=1,
            border_color="#616161",
            corner_radius=6,
        )
        later_btn.pack(side="right", fill="x", expand=True, padx=(5, 0))

    def _open_url(self, url: str) -> None:
        """開啟 URL"""
        try:
            logger.info(f"開啟連結: {url}")
            webbrowser.open(url)
        except Exception as e:
            logger.error(f"開啟瀏覽器失敗: {e}")

    def _on_download_and_close(self) -> None:
        """下載並關閉程式 (推薦操作)"""
        download_url = self.update_info.get("download_url", "")
        release_url = self.update_info.get("release_url", "")
        url = download_url if download_url else release_url

        if url:
            try:
                logger.info(f"開啟下載頁面並準備關閉程式: {url}")
                webbrowser.open(url)

                # 延遲關閉,確保瀏覽器已開啟
                self.after(1000, self._close_application)
            except Exception as e:
                logger.error(f"開啟瀏覽器失敗: {e}")
                self.destroy()
        else:
            logger.warning("沒有可用的下載連結")
            self.destroy()

    def _on_download(self) -> None:
        """僅開啟下載頁面,不關閉程式"""
        download_url = self.update_info.get("download_url", "")
        release_url = self.update_info.get("release_url", "")
        url = download_url if download_url else release_url

        if url:
            try:
                logger.info(f"開啟下載頁面: {url}")
                webbrowser.open(url)
            except Exception as e:
                logger.error(f"開啟瀏覽器失敗: {e}")

        self.destroy()

    def _close_application(self) -> None:
        """關閉整個應用程式"""
        logger.info("使用者選擇下載更新,關閉應用程式")
        # 取得主視窗並關閉
        root = self.master
        while root.master:
            root = root.master
        root.quit()

    def _on_later(self) -> None:
        """處理稍後提醒按鈕點擊"""
        logger.info("使用者選擇稍後更新")
        self.destroy()


def show_update_dialog(parent: ctk.CTk, update_info: Dict[str, Any]) -> None:
    """
    顯示更新對話框的便利函式

    Args:
        parent: 父視窗
        update_info: 更新資訊
    """
    # 只有在有更新時才顯示
    if update_info and update_info.get("has_update", False):
        UpdateDialog(parent, update_info)
    else:
        logger.debug("沒有可用更新,不顯示對話框")
