"""
效能測試 - 測量資料同步服務的載入時間

測試項目:
- 6.2.1 首次載入時間 (目標 < 3s, 實際約 13s 因網路)
- 6.2.2 快取重新整理時間 (目標 < 0.5s)
- 6.2.3 強制重新整理時間 (目標 < 2s, 實際約 13s 因網路)

注意: 效能測試需要實際登入 SSP 系統,請使用手動測試腳本
"""

import pytest
from src.config.settings import Settings


class TestPerformance:
    """效能測試套件 - 僅測試設定"""

    def test_cache_duration_config(self):
        """驗證快取設定正確"""
        settings = Settings()
        assert hasattr(
            settings, "CACHE_DURATION_SECONDS"
        ), "應該定義 CACHE_DURATION_SECONDS"
        assert settings.CACHE_DURATION_SECONDS == 300, "快取時長應為 5 分鐘 (300 秒)"
        print(f"\n✅ 快取時長設定: {settings.CACHE_DURATION_SECONDS}s (5 分鐘)")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
