"""
失败追踪模块
负责追踪API调用失败，达到阈值后自动禁用
"""
from typing import Dict, Optional
from threading import RLock
from .config_manager import ConfigManager


class FailureTracker:
    """失败追踪器"""
    
    def __init__(self, config_manager: ConfigManager, failure_threshold: int = 3):
        """
        初始化失败追踪器
        
        Args:
            config_manager: 配置管理器实例
            failure_threshold: 失败阈值，达到此值后自动禁用，默认3次
        """
        self.config_manager = config_manager
        self.failure_threshold = failure_threshold
        self._failure_count: Dict[str, int] = {}
        self._lock = RLock()
    
    def _get_failure_key(self, platform: str, api_name: str, group_id: Optional[str]) -> str:
        """生成失败计数key"""
        if group_id:
            return f"{platform}:{api_name}:{group_id}"
        return f"{platform}:{api_name}:global"
    
    def record_failure(self, platform: str, api_name: str, group_id: Optional[str] = None):
        """
        记录一次失败
        
        Args:
            platform: 平台名称
            api_name: API名称
            group_id: 群组ID，如果为None则记录全局失败
        """
        key = self._get_failure_key(platform, api_name, group_id)
        
        with self._lock:
            self._failure_count[key] = self._failure_count.get(key, 0) + 1
            count = self._failure_count[key]
            
            # 如果达到阈值，自动禁用
            if count >= self.failure_threshold:
                self._auto_disable(platform, api_name, group_id)
    
    def reset_failure(self, platform: str, api_name: str, group_id: Optional[str] = None):
        """
        重置失败计数（成功调用后调用）
        
        Args:
            platform: 平台名称
            api_name: API名称
            group_id: 群组ID
        """
        key = self._get_failure_key(platform, api_name, group_id)
        
        with self._lock:
            if key in self._failure_count:
                del self._failure_count[key]
    
    def _auto_disable(self, platform: str, api_name: str, group_id: Optional[str]):
        """
        自动禁用平台或API
        
        Args:
            platform: 平台名称
            api_name: API名称
            group_id: 群组ID，如果为None则不自动禁用（全局禁用需要手动配置）
        """
        if not group_id:
            # 全局禁用需要手动配置，不自动禁用
            return
        
        # 如果api_name是search（必需API），则禁用整个平台
        # 否则只禁用该API
        if api_name == "search":
            # 禁用整个平台
            group_config = self.config_manager.get_group_config(group_id)
            disabled_platforms = group_config.get("disabled_platforms", [])
            if platform not in disabled_platforms:
                disabled_platforms.append(platform)
                self.config_manager.update_group_config(
                    group_id=group_id,
                    disabled_platforms=disabled_platforms
                )
        else:
            # 只禁用该API
            group_config = self.config_manager.get_group_config(group_id)
            disabled_apis = group_config.get("disabled_apis", [])
            api_key = f"{platform}:{api_name}"
            if api_key not in disabled_apis:
                disabled_apis.append(api_key)
                self.config_manager.update_group_config(
                    group_id=group_id,
                    disabled_apis=disabled_apis
                )
    
    def get_failure_count(self, platform: str, api_name: str, group_id: Optional[str] = None) -> int:
        """
        获取失败次数
        
        Args:
            platform: 平台名称
            api_name: API名称
            group_id: 群组ID
        
        Returns:
            失败次数
        """
        key = self._get_failure_key(platform, api_name, group_id)
        with self._lock:
            return self._failure_count.get(key, 0)

