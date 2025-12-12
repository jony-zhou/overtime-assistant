"""服務層套件"""

from .auth_service import AuthService
from .data_service import DataService
from .export_service import ExportService
from .update_service import UpdateService
from .overtime_report_service import OvertimeReportService
from .template_manager import TemplateManager
from .data_sync_service import DataSyncService

# 已棄用的服務 (保留以維持向後相容,將於 v2.0.0 移除)
from .overtime_status_service import OvertimeStatusService
from .personal_record_service import PersonalRecordService

__all__ = [
    "AuthService",
    "DataService",
    "DataSyncService",  # ✅ 推薦使用
    "ExportService",
    "UpdateService",
    "OvertimeReportService",
    "TemplateManager",
    # 以下已棄用,請使用 DataSyncService
    "OvertimeStatusService",  # [已棄用] 使用 DataSyncService
    "PersonalRecordService",  # [已棄用] 使用 DataSyncService
]
