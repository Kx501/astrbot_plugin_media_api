"""
平台API客户端模块
"""
from .example_platform import ExamplePlatform
from .ak317_platform import AK317Platform
from .xingchenfu_platform import XingChenFuPlatform
from .lolimi_platform import LolimiPlatform

# 平台注册表（类）
PLATFORMS = {
    "example": ExamplePlatform,
    "ak317": AK317Platform,
    "xingchenfu": XingChenFuPlatform,
    "lolimi": LolimiPlatform,
}

# 平台实例缓存（用于关键词注册）
_platform_instances = {}


def _initialize_platforms():
    """初始化所有平台实例并注册关键词"""
    for name, platform_class in PLATFORMS.items():
        if name not in _platform_instances:
            instance = platform_class()
            _platform_instances[name] = instance
            # 关键词注册在平台__init__中自动完成


# 在导入时初始化所有平台
_initialize_platforms()


def get_platform(name: str):
    """根据名称获取平台实例"""
    # 从缓存中获取（已初始化并注册关键词）
    if name in _platform_instances:
        return _platform_instances[name]
    
    # 如果缓存中没有，创建新实例（不应该发生，但作为fallback）
    platform_class = PLATFORMS.get(name)
    if platform_class:
        instance = platform_class()
        _platform_instances[name] = instance
        return instance
    return None


def list_platforms():
    """列出所有已注册的平台"""
    return list(PLATFORMS.keys())
