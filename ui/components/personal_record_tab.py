"""個人記錄分頁 UI"""

import customtkinter as ctk
from tkinter import ttk, messagebox
import logging
from typing import List, Optional

from src.models.personal_record import PersonalRecord, PersonalRecordSummary
from ui.config import colors, typography, spacing

logger = logging.getLogger(__name__)


class PersonalRecordTab(ctk.CTkFrame):
    """
    個人記錄分頁

    功能:
    - 顯示個人已申請的加班記錄
    - 顯示:日期、加班內容、狀態、申報、當月累計、當季累計
    - 支援重新整理
    """

    def __init__(self, parent):
        """
        初始化個人記錄分頁

        Args:
            parent: 父元件
        """
        super().__init__(parent, fg_color="transparent")

        self.records: List[PersonalRecord] = []
        self.summary: Optional[PersonalRecordSummary] = None

        self._create_ui()

    def _create_ui(self):
        """建立 UI"""
        # 頂部操作區
        self._create_header()

        # 表格容器
        self._create_table()

    def _create_header(self):
        """建立頂部操作區"""
        header = ctk.CTkFrame(
            self, fg_color=colors.background_secondary, corner_radius=12, height=60
        )
        header.pack(fill="x", padx=spacing.lg, pady=(spacing.lg, spacing.md))
        header.pack_propagate(False)

        # 內容容器
        content = ctk.CTkFrame(header, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=spacing.lg, pady=spacing.md)

        # 左側: 標題
        title_frame = ctk.CTkFrame(content, fg_color="transparent")
        title_frame.pack(side="left")

        title_label = ctk.CTkLabel(
            title_frame,
            text="📋 個人加班記錄",
            font=(
                typography.font_family_primary,
                typography.size_h3,
                typography.weight_bold,
            ),
            text_color=colors.text_primary,
        )
        title_label.pack(side="left")

        # 右側: 操作按鈕
        button_frame = ctk.CTkFrame(content, fg_color="transparent")
        button_frame.pack(side="right")

        # 重新整理按鈕
        self.refresh_button = ctk.CTkButton(
            button_frame,
            text="🔄 重新整理",
            font=(typography.font_family_primary, typography.size_body),
            fg_color=colors.secondary,
            hover_color=colors.secondary_hover,
            width=120,
            height=36,
            corner_radius=8,
            command=self.on_refresh,
        )
        self.refresh_button.pack(side="left", padx=spacing.sm)

    def _create_table(self):
        """建立表格"""
        # 表格容器
        table_container = ctk.CTkFrame(
            self, fg_color=colors.background_secondary, corner_radius=12
        )
        table_container.pack(
            fill="both", expand=True, padx=spacing.lg, pady=(0, spacing.lg)
        )

        # 建立 Treeview
        columns = (
            "date",
            "content",
            "status",
            "hours",
            "monthly",
            "quarterly",
            "report",
        )

        self.tree = ttk.Treeview(
            table_container,
            columns=columns,
            show="headings",
            selectmode="browse",
            height=20,
        )

        # 設定欄位標題和寬度
        column_configs = [
            ("date", "加班日期", 100),
            ("content", "加班內容", 250),
            ("status", "狀態", 100),
            ("hours", "加班時數", 80),
            ("monthly", "當月累計", 80),
            ("quarterly", "當季累計", 80),
            ("report", "申報", 80),
        ]

        for col_id, heading, width in column_configs:
            self.tree.heading(col_id, text=heading, anchor="center")
            self.tree.column(col_id, width=width, anchor="center")

        # 樣式設定
        style = ttk.Style()
        style.theme_use("clam")

        # 設定顏色 (深色主題)
        style.configure(
            "Treeview",
            background=colors.background_secondary,
            foreground=colors.text_primary,
            fieldbackground=colors.background_secondary,
            borderwidth=0,
            font=("Microsoft JhengHei UI", 11),
        )

        style.configure(
            "Treeview.Heading",
            background=colors.background_tertiary,
            foreground=colors.text_primary,
            borderwidth=0,
            font=("Microsoft JhengHei UI", 11, "bold"),
        )

        style.map(
            "Treeview",
            background=[("selected", colors.primary)],
            foreground=[("selected", colors.text_primary)],
        )

        # 捲軸
        scrollbar = ttk.Scrollbar(
            table_container, orient="vertical", command=self.tree.yview
        )
        self.tree.configure(yscrollcommand=scrollbar.set)

        # 佈局
        self.tree.pack(
            side="left", fill="both", expand=True, padx=spacing.md, pady=spacing.md
        )
        scrollbar.pack(side="right", fill="y", pady=spacing.md)

        # 空狀態標籤 (初始隱藏)
        self.empty_label = ctk.CTkLabel(
            table_container,
            text="📝 尚無個人加班記錄\n\n請先登入並載入資料",
            font=(typography.font_family_primary, typography.size_body),
            text_color=colors.info,
            justify="center",
        )

    def display_records(
        self, records: List[PersonalRecord], summary: PersonalRecordSummary
    ):
        """
        顯示個人記錄

        Args:
            records: 個人記錄列表
            summary: 統計摘要
        """
        self.records = records
        self.summary = summary

        # 清空表格
        for item in self.tree.get_children():
            self.tree.delete(item)

        # 檢查是否有資料
        if not records:
            self.tree.pack_forget()
            self.empty_label.pack(expand=True, pady=spacing.xl)
            return

        # 顯示表格
        self.empty_label.pack_forget()
        self.tree.pack(
            side="left", fill="both", expand=True, padx=spacing.md, pady=spacing.md
        )

        # 插入資料
        for record in records:
            # 確保數值欄位不為 None
            overtime_hours = (
                record.overtime_hours if record.overtime_hours is not None else 0.0
            )
            monthly_total = (
                record.monthly_total if record.monthly_total is not None else 0.0
            )
            quarterly_total = (
                record.quarterly_total if record.quarterly_total is not None else 0.0
            )

            self.tree.insert(
                "",
                "end",
                values=(
                    record.date,
                    record.content,
                    record.status,
                    f"{overtime_hours:.2f} hr",
                    f"{monthly_total:.2f} hr",
                    f"{quarterly_total:.2f} hr",
                    record.report_type,
                ),
            )

        logger.info(f"個人記錄顯示完成: {len(records)} 筆")

    def on_refresh(self):
        """重新整理 (需由父視窗實作)"""
        # 這個方法會在主視窗中被覆寫
        messagebox.showinfo("提示", "請由主視窗重新整理資料")

    def clear_table(self):
        """清空表格"""
        for item in self.tree.get_children():
            self.tree.delete(item)

        self.records = []
        self.summary = None

        self.tree.pack_forget()
        self.empty_label.pack(expand=True, pady=spacing.xl)
