"""打卡記錄分頁元件

職責:
- 顯示原始打卡時間 (來自 gvNotes005 第一頁)
- 提供快速查看每日刷卡明細
- 輔助驗證出勤異常的刷卡依據
"""

import customtkinter as ctk
from typing import List
from tkinter import ttk
import tkinter as tk

from src.models.punch import PunchRecord
from ui.config.design_system import colors, typography, spacing, border_radius


class PunchRecordTab(ctk.CTkFrame):
    """打卡記錄分頁

    設計理念:
    - 簡潔明瞭: 僅顯示日期和打卡時間
    - 輔助資訊: 幫助用戶確認異常清單的刷卡依據
    - 無需翻頁: 第一頁資料足以參考
    """

    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.punch_records: List[PunchRecord] = []
        self._create_ui()

    def _create_ui(self):
        """建立 UI"""
        # 標題列
        header = ctk.CTkFrame(
            self, fg_color=colors.background_secondary, corner_radius=border_radius.md
        )
        header.pack(fill="x", padx=spacing.lg, pady=(spacing.lg, spacing.md))

        header_content = ctk.CTkFrame(header, fg_color="transparent")
        header_content.pack(fill="x", padx=spacing.md, pady=spacing.md)

        title = ctk.CTkLabel(
            header_content,
            text="🕐 刷卡記錄明細",
            font=(
                typography.font_family_primary,
                typography.size_h3,
                typography.weight_bold,
            ),
            text_color=colors.text_primary,
        )
        title.pack(side="left")

        # 說明文字
        hint = ctk.CTkLabel(
            header_content,
            text="(僅顯示第一頁資料供參考)",
            font=(typography.font_family_primary, typography.size_caption),
            text_color=colors.text_secondary,
        )
        hint.pack(side="left", padx=(spacing.sm, 0))

        # 表格容器
        table_container = ctk.CTkFrame(self, fg_color="transparent")
        table_container.pack(
            fill="both", expand=True, padx=spacing.lg, pady=(0, spacing.lg)
        )

        # 建立 Treeview
        self._create_table(table_container)

    def _create_table(self, parent):
        """建立打卡記錄表格"""
        # Treeview 樣式
        style = ttk.Style()
        style.theme_use("clam")

        # 配置顏色
        style.configure(
            "Punch.Treeview",
            background=colors.background_primary,
            fieldbackground=colors.background_primary,
            foreground=colors.text_primary,
            borderwidth=0,
            font=(typography.font_family_primary, typography.size_body),
            rowheight=35,
        )

        style.configure(
            "Punch.Treeview.Heading",
            background=colors.background_secondary,
            foreground=colors.text_primary,
            borderwidth=0,
            font=(
                typography.font_family_primary,
                typography.size_body,
                typography.weight_bold,
            ),
        )

        style.map("Punch.Treeview", background=[("selected", colors.primary)])

        # 建立 Treeview
        columns = ("date", "punch_times", "count")
        self.tree = ttk.Treeview(
            parent,
            columns=columns,
            show="headings",
            style="Punch.Treeview",
            selectmode="browse",
        )

        # 設定欄位
        self.tree.heading("date", text="日期")
        self.tree.heading("punch_times", text="刷卡時間")
        self.tree.heading("count", text="次數")

        self.tree.column("date", width=120, anchor="center")
        self.tree.column("punch_times", width=400, anchor="w")
        self.tree.column("count", width=80, anchor="center")

        # 捲軸
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)

        # 佈局
        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

    def display_records(self, punch_records: List[PunchRecord]):
        """顯示打卡記錄

        Args:
            punch_records: 打卡記錄列表
        """
        self.punch_records = punch_records

        # 清空現有資料
        for item in self.tree.get_children():
            self.tree.delete(item)

        if not punch_records:
            # 顯示無資料提示
            self.tree.insert(
                "",
                "end",
                values=("", "無打卡記錄", ""),
                tags=("empty",),
            )
            self.tree.tag_configure("empty", foreground=colors.text_secondary)
            return

        # 插入資料
        for record in punch_records:
            # 過濾無效資料 (分頁列或空資料)
            if not record.date or not record.punch_times:
                continue
            # 過濾分頁資料 (日期為數字或包含特殊字元)
            if record.date.isdigit() or len(record.date) < 8:
                continue

            punch_times_str = "  →  ".join(record.punch_times)

            self.tree.insert(
                "",
                "end",
                values=(
                    record.date,
                    punch_times_str,
                    f"{record.punch_count} 次",
                ),
            )

    def clear(self):
        """清空顯示"""
        self.punch_records = []
        for item in self.tree.get_children():
            self.tree.delete(item)
