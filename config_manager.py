"""
配置管理模块
支持多群组配置、热重载、线程安全的配置读写
"""
import json
import threading
from pathlib import Path
from typing import Dict, List, Optional, Any
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler


class ConfigReloadHandler(FileSystemEventHandler):
    """配置文件变更处理器"""
    
    def __init__(self, config_manager):
        self.config_manager = config_manager
    
    def on_modified(self, event):
        if not event.is_directory and event.src_path == str(self.config_manager.config_path):
            self.config_manager.reload_config()


class ConfigManager:
    """配置管理器"""
    
    def __init__(self, config_path: str = "config/config.json"):
        self.config_path = Path(config_path)
        self._config: Dict[str, Any] = {}
        self._lock = threading.RLock()
        self._observer: Optional[Any] = None
        
        # 确保配置文件存在
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        if not self.config_path.exists():
            self._save_config({"global": {}, "groups": {}, "platforms": {}})
        
        # 加载配置
        self.reload_config()
        
        # 启动文件监控
        self.start_watching()
    
    def _load_config(self) -> Dict[str, Any]:
        """从文件加载配置"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            # 如果文件不存在或格式错误，返回默认配置
            default_config = {"global": {}, "groups": {}, "platforms": {}}
            self._save_config(default_config)
            return default_config
    
    def _save_config(self, config: Dict[str, Any]):
        """保存配置到文件"""
        with open(self.config_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
    
    def reload_config(self):
        """重新加载配置文件"""
        with self._lock:
            self._config = self._load_config()
    
    def start_watching(self):
        """启动配置文件监控"""
        if self._observer is None:
            self._observer = Observer()
            event_handler = ConfigReloadHandler(self)
            self._observer.schedule(
                event_handler,
                str(self.config_path.parent),
                recursive=False
            )
            self._observer.start()
    
    def stop_watching(self):
        """停止配置文件监控"""
        if self._observer:
            self._observer.stop()
            self._observer.join()
            self._observer = None
    
    def get_config(self) -> Dict[str, Any]:
        """获取完整配置（线程安全）"""
        with self._lock:
            return self._config.copy()
    
    def get_group_config(self, group_id: str) -> Dict[str, Any]:
        """获取指定群组的配置"""
        with self._lock:
            groups = self._config.get("groups", {})
            return groups.get(group_id, {})
    
    def get_platform_config(self, platform: str) -> Dict[str, Any]:
        """获取指定平台的配置"""
        with self._lock:
            platforms = self._config.get("platforms", {})
            return platforms.get(platform, {})
    
    def is_platform_enabled(self, group_id: Optional[str], platform: str) -> bool:
        """
        检查指定群组是否启用了指定平台
        
        权限检查优先级：全局禁用 → 群组禁用 → 平台是否配置
        
        Args:
            group_id: 群组ID，如果为None则只检查全局禁用和平台配置
            platform: 平台名称
        
        Returns:
            是否启用
        """
        with self._lock:
            # 1. 检查全局禁用
            global_config = self._config.get("global", {})
            global_disabled = global_config.get("disabled_platforms", [])
            if platform in global_disabled:
                return False
            
            # 2. 检查群组禁用（如果提供了group_id）
            if group_id:
                group_config = self.get_group_config(group_id)
                group_disabled = group_config.get("disabled_platforms", [])
                if platform in group_disabled:
                    return False
            
            # 3. 检查平台是否已配置
            platforms = self._config.get("platforms", {})
            if platform not in platforms:
                return False
            
            return True
    
    def is_api_enabled(self, group_id: Optional[str], platform: str, api_id: str) -> bool:
        """
        检查指定群组是否启用了指定平台的指定API
        
        权限检查优先级：全局禁用 → 群组禁用 → 平台是否启用
        
        Args:
            group_id: 群组ID，如果为None则只检查全局禁用
            platform: 平台名称
            api_id: API标识（平台内部的API ID，如"hssp"、"zptp"）
        
        Returns:
            是否启用
        """
        with self._lock:
            # 首先检查平台是否启用
            if not self.is_platform_enabled(group_id, platform):
                return False
            
            api_key = f"{platform}:{api_id}"
            
            # 1. 检查全局禁用
            global_config = self._config.get("global", {})
            global_disabled_apis = global_config.get("disabled_apis", [])
            if api_key in global_disabled_apis:
                return False
            
            # 2. 检查群组禁用（如果提供了group_id）
            if group_id:
                group_config = self.get_group_config(group_id)
                group_disabled_apis = group_config.get("disabled_apis", [])
                if api_key in group_disabled_apis:
                    return False
            
            return True
    
    def update_group_config(
        self,
        group_id: str,
        disabled_platforms: Optional[List[str]] = None,
        disabled_apis: Optional[List[str]] = None
    ):
        """更新群组配置"""
        with self._lock:
            if "groups" not in self._config:
                self._config["groups"] = {}
            
            if group_id not in self._config["groups"]:
                self._config["groups"][group_id] = {}
            
            group_config = self._config["groups"][group_id]
            
            if disabled_platforms is not None:
                group_config["disabled_platforms"] = disabled_platforms
            
            if disabled_apis is not None:
                group_config["disabled_apis"] = disabled_apis
            
            self._save_config(self._config)
            self.reload_config()
    
    def update_platform_config(self, platform: str, **kwargs):
        """更新平台配置"""
        with self._lock:
            if "platforms" not in self._config:
                self._config["platforms"] = {}
            
            if platform not in self._config["platforms"]:
                self._config["platforms"][platform] = {}
            
            self._config["platforms"][platform].update(kwargs)
            self._save_config(self._config)
            self.reload_config()
    
    def get_available_platforms(self, group_id: Optional[str] = None) -> List[str]:
        """
        获取可用平台列表（用于随机选择）
        
        Args:
            group_id: 群组ID，如果为None则只考虑全局禁用
        
        Returns:
            可用平台名称列表
        """
        with self._lock:
            platforms = self._config.get("platforms", {})
            available = []
            
            for platform_name in platforms.keys():
                if self.is_platform_enabled(group_id, platform_name):
                    available.append(platform_name)
            
            return available
    
    def list_platforms(self, group_id: Optional[str] = None) -> Dict[str, Any]:
        """列出所有平台及其状态"""
        with self._lock:
            platforms = self._config.get("platforms", {})
            result = {}
            
            for platform_name in platforms.keys():
                enabled = self.is_platform_enabled(group_id, platform_name)
                result[platform_name] = {
                    "enabled": enabled,
                    "config": self.get_platform_config(platform_name)
                }
            
            return result
    
    def __del__(self):
        """析构函数，停止监控"""
        self.stop_watching()

