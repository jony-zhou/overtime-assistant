"""
版本管理模組測試
"""
import pytest
from src.core.version import Version, get_current_version, is_newer_version, VERSION


class TestVersion:
    """測試 Version 類別"""
    
    def test_from_string_valid(self):
        """測試從有效字串建立版本"""
        v = Version.from_string("1.2.3")
        assert v.major == 1
        assert v.minor == 2
        assert v.patch == 3
    
    def test_from_string_with_v_prefix(self):
        """測試從帶 v 前綴的字串建立版本"""
        v = Version.from_string("v1.2.3")
        assert v.major == 1
        assert v.minor == 2
        assert v.patch == 3
    
    def test_from_string_invalid(self):
        """測試無效字串拋出異常"""
        with pytest.raises(ValueError):
            Version.from_string("invalid")
        
        with pytest.raises(ValueError):
            Version.from_string("1.2")
        
        with pytest.raises(ValueError):
            Version.from_string("1.2.3.4")
    
    def test_to_string(self):
        """測試轉換為字串"""
        v = Version(1, 2, 3)
        assert v.to_string() == "1.2.3"
        assert str(v) == "1.2.3"
    
    def test_comparison_equal(self):
        """測試相等比較"""
        v1 = Version(1, 2, 3)
        v2 = Version(1, 2, 3)
        assert v1 == v2
    
    def test_comparison_less_than(self):
        """測試小於比較"""
        v1 = Version(1, 2, 3)
        v2 = Version(1, 2, 4)
        v3 = Version(1, 3, 0)
        v4 = Version(2, 0, 0)
        
        assert v1 < v2
        assert v1 < v3
        assert v1 < v4
        assert v2 < v3
        assert v3 < v4
    
    def test_comparison_greater_than(self):
        """測試大於比較"""
        v1 = Version(2, 0, 0)
        v2 = Version(1, 9, 9)
        
        assert v1 > v2
    
    def test_comparison_less_equal(self):
        """測試小於等於比較"""
        v1 = Version(1, 2, 3)
        v2 = Version(1, 2, 3)
        v3 = Version(1, 2, 4)
        
        assert v1 <= v2
        assert v1 <= v3
    
    def test_comparison_greater_equal(self):
        """測試大於等於比較"""
        v1 = Version(1, 2, 3)
        v2 = Version(1, 2, 3)
        v3 = Version(1, 2, 2)
        
        assert v1 >= v2
        assert v1 >= v3
    
    def test_immutable(self):
        """測試版本物件不可變"""
        v = Version(1, 2, 3)
        with pytest.raises(AttributeError):
            v.major = 2


class TestVersionHelpers:
    """測試版本輔助函式"""
    
    def test_get_current_version(self):
        """測試取得當前版本"""
        current = get_current_version()
        assert isinstance(current, Version)
        assert current.to_string() == VERSION
    
    def test_is_newer_version_true(self):
        """測試檢測更新版本"""
        assert is_newer_version("1.0.0", "1.0.1") is True
        assert is_newer_version("1.0.0", "1.1.0") is True
        assert is_newer_version("1.0.0", "2.0.0") is True
    
    def test_is_newer_version_false(self):
        """測試檢測相同或舊版本"""
        assert is_newer_version("1.0.1", "1.0.0") is False
        assert is_newer_version("1.1.0", "1.0.9") is False
        assert is_newer_version("2.0.0", "1.9.9") is False
        assert is_newer_version("1.0.0", "1.0.0") is False
    
    def test_is_newer_version_with_v_prefix(self):
        """測試帶 v 前綴的版本比較"""
        assert is_newer_version("v1.0.0", "v1.0.1") is True
        assert is_newer_version("1.0.0", "v1.0.1") is True
        assert is_newer_version("v1.0.0", "1.0.1") is True
    
    def test_is_newer_version_invalid(self):
        """測試無效版本號的處理"""
        # 無效版本號時應返回 False (保守處理)
        assert is_newer_version("invalid", "1.0.0") is False
        assert is_newer_version("1.0.0", "invalid") is False
