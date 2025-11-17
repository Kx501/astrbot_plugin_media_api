# 多平台媒体API MCP服务器 - 设计文档

本文档整合了所有设计说明，包括配置设计、工具设计、优化方案等。

## 目录

1. [项目概述](#项目概述)
2. [配置文件设计](#配置文件设计)
3. [MCP工具设计](#mcp工具设计)
4. [平台抽象层设计](#平台抽象层设计)
5. [核心模块设计](#核心模块设计)
6. [实现细节](#实现细节)
7. [使用示例](#使用示例)

---

## 项目概述

### 项目目标

创建一个MCP（Model Context Protocol）服务器，集成多个第三方音视频和图片平台API，提供给QQ AI群聊bot使用。

### 核心特性

- **减少token消耗**：只有一个工具，返回格式最简化
- **自动平台选择**：从可用平台中随机选择，Bot无需指定
- **灵活的权限控制**：支持全局和群组两级禁用配置
- **高可靠性**：缓存机制和自动禁用机制
- **通用性**：支持非QQ Bot场景（group_id可选）

### 项目结构

```
media_api/
├── mcp_server.py          # MCP服务器主入口
├── config_manager.py       # 配置管理模块（支持热重载、全局/群组权限检查）
├── platform_base.py        # 平台抽象基类
├── cache_manager.py        # 缓存管理模块（成功缓存、失败回退）
├── failure_tracker.py     # 失败追踪模块（自动禁用机制）
├── platforms/              # 各平台API客户端
│   ├── __init__.py
│   └── example_platform.py # 示例平台实现
├── config/                 # 配置文件目录
│   └── config.json         # 统一配置文件
├── requirements.txt        # Python依赖
├── README.md              # 项目文档
└── DESIGN.md              # 本文档
```

---

## 配置文件设计

### 配置文件结构

配置文件位于 `config/config.json`，采用三层结构：

```json
{
  "global": {
    "disabled_platforms": ["unsplash"],
    "disabled_apis": ["pixabay:get_by_id"]
  },
  "groups": {
    "123456789": {
      "disabled_platforms": ["pexels"],
      "disabled_apis": ["pixabay:search"]
    },
    "987654321": {
      "disabled_platforms": ["platform3"],
      "disabled_apis": ["platform1:search", "platform2:download"]
    }
  },
  "platforms": {
    "pixabay": {
      "api_key": "your-api-key-here"
    },
    "pexels": {
      "api_key": "your-pexels-key"
    },
    "unsplash": {}
  }
}
```

### 配置层级说明

#### 1. global（全局配置）

**作用**：全局禁用某些平台或API，影响所有群组

**字段**：

- `disabled_platforms`（可选）：全局禁用的平台列表
  - 格式：`["platform1", "platform2"]`
  - 这些平台在所有群组中都不能使用
- `disabled_apis`（可选）：全局禁用的API列表
  - 格式：`["平台名:api_id"]`，如 `["ak317:hssp", "xingchenfu:jk"]`
  - 这些API在所有群组中都不能使用
  - `api_id` 是平台内部的API标识，在 `api_map` 中定义

**示例**：

```json
{
  "global": {
    "disabled_platforms": ["unsplash"],
    "disabled_apis": ["pixabay:get_by_id"]
  }
}
```

#### 2. groups（群组配置）

**作用**：针对特定群组的额外禁用配置

**字段**：

- `disabled_platforms`（可选）：该群组额外禁用的平台列表
- `disabled_apis`（可选）：该群组额外禁用的API列表（格式：`["平台名:api_id"]`）

**示例**：

```json
{
  "groups": {
    "123456789": {
      "disabled_platforms": ["pexels"],
      "disabled_apis": ["pixabay:search"]
    }
  }
}
```

#### 3. platforms（平台配置）

**作用**：配置各平台的API密钥等参数

**字段**：

- `api_key`（可选）：API密钥
- `api_secret`（可选）：API密钥（如果需要）
- 其他平台特定参数

**示例**：

```json
{
  "platforms": {
    "pixabay": {
      "api_key": "your-api-key-here"
    },
    "pexels": {
      "api_key": "your-pexels-key"
    },
    "unsplash": {}  // 不需要key的平台可以为空
  }
}
```

### 权限检查逻辑

检查某个群组是否可以使用某个平台的某个API时，按以下顺序：

1. **检查全局禁用**：

   - 如果平台在 `global.disabled_platforms`中 → **禁用**
   - 如果API在 `global.disabled_apis`中（格式：`平台名:API名`） → **禁用**
2. **检查群组禁用**（如果提供了group_id）：

   - 如果平台在 `groups[group_id].disabled_platforms`中 → **禁用**
   - 如果API在 `groups[group_id].disabled_apis`中 → **禁用**
3. **检查平台是否已配置**：

   - 如果平台不在 `platforms`中 → **禁用**（未配置的平台不能使用）
4. **如果都通过** → **允许使用**

### 默认行为

- 如果配置文件中没有 `global`字段 → 全局不禁用任何平台/API
- 如果群组配置中没有 `disabled_platforms`或 `disabled_apis` → 该群组不禁用任何平台/API
- 如果平台不在 `platforms`中配置 → 该平台不可用
- 所有平台和API默认启用，除非明确禁用

---

## MCP工具设计

### 工具数量：只有一个核心工具

**工具名**：`get_media`

**设计原因**：减少Bot和MCP的交互次数，降低token消耗

### 参数设计

#### 在schema中声明的参数：

- `query`（必需）：搜索关键词
- `media_type`（可选）：媒体类型，默认"all"
  - 可选值：`"image"` / `"video"` / `"audio"` / `"all"`

#### 不在schema中声明但支持的参数：

- `group_id`（可选）：群组ID，用于权限检查
  - **设计原因**：让MCP更通用，可用于非QQ Bot场景
  - **自动注入**：由astrbot框架根据消息上下文自动注入，LLM不会看到此参数，也不会尝试填充
  - 如果不提供，则跳过群组权限检查（所有平台都可用）

### Bot看到的工具定义

```json
{
  "name": "get_media",
  "description": "获取媒体资源（图片/视频/音频）",
  "inputSchema": {
    "type": "object",
    "properties": {
      "query": {
        "type": "string",
        "description": "搜索关键词"
      },
      "media_type": {
        "type": "string",
        "description": "媒体类型：image/video/audio/all",
        "default": "all"
      }
    },
    "required": ["query"]
  }
}
```

### 功能流程

1. **接收参数**：query（必需）、media_type（可选）、group_id（可选，不在schema中）
2. **权限检查**：如果提供了group_id，检查该群组的权限配置
3. **平台选择**：从可用平台中随机选择一个
4. **API调用**：调用平台API获取媒体资源
5. **结果处理**：只返回第一个结果的URL和类型
6. **缓存管理**：成功时缓存，失败时使用缓存
7. **失败追踪**：记录失败次数，达到阈值后自动禁用

### 返回格式（最简化）

**成功**：

```json
{
  "url": "https://example.com/image.jpg",
  "type": "image"
}
```

**错误**：

```json
{
  "error": "错误信息"
}
```

**设计说明**：

- 不包含平台名（减少token，Bot不需要知道）
- 不包含元数据（title、description等）
- 只返回第一个结果（平台API通常返回多个结果，如10-20个）

---

## 平台抽象层设计

### PlatformBase抽象类

所有平台必须继承 `PlatformBase`并实现以下方法：

```python
class PlatformBase(ABC):
    def __init__(self, name: str):
        self.name = name
        # 平台需要定义 api_map: {api_id: (url, title, media_type)}
        # 然后调用 self.register_apis_from_map(self.api_map) 自动注册
  
    @abstractmethod
    async def search_media(
        self,
        query: str,
        media_type: str = "all",
        config: Optional[Dict[str, Any]] = None,
        limit: int = 10,
        api_id: Optional[str] = None  # 由MCP服务器传入
    ) -> List[MediaResource]:
        """搜索媒体资源（必需，所有平台都应实现）"""
        pass
  
    @abstractmethod
    async def get_media_by_id(
        self,
        media_id: str,
        config: Optional[Dict[str, Any]] = None
    ) -> Optional[MediaResource]:
        """根据ID获取媒体资源（可选）"""
        pass
  
    @abstractmethod
    def get_available_apis(self) -> List[str]:
        """返回该平台提供的API列表"""
        pass
  
    def get_supported_media_types(self) -> List[str]:
        """返回平台支持的媒体类型列表（默认从api_map推导）"""
        pass
```

### 标准API名称

- `search`：搜索媒体资源（必需，所有平台都应该实现）
- `get_by_id`：根据ID获取媒体资源（可选）
- `download`：下载媒体资源（可选）
- 其他平台特定API

### API声明示例

```python
class PixabayPlatform(PlatformBase):
    def get_available_apis(self) -> List[str]:
        return ["search", "get_by_id"]  # pixabay提供这两个API

class PexelsPlatform(PlatformBase):
    def get_available_apis(self) -> List[str]:
        return ["search", "get_by_id", "download"]  # pexels提供三个API
```

### MediaResource统一返回格式

```python
class MediaResource:
    url: str                    # 媒体URL（必需）
    media_type: str             # 媒体类型：image/video/audio
    title: Optional[str]        # 标题（可选）
    description: Optional[str]  # 描述（可选）
    thumbnail: Optional[str]    # 缩略图URL（可选）
    # ... 其他元数据
```

---

## 核心模块设计

### 1. ConfigManager（配置管理模块）

**功能**：

- 读取、更新配置文件
- 支持配置文件热重载（使用 `watchdog`监控文件变化）
- 线程安全的配置读写
- 支持全局和群组两级权限检查

**主要方法**：

- `is_platform_enabled(group_id, platform)`: 检查平台是否启用（考虑全局+群组）
- `is_api_enabled(group_id, platform, api_id)`: 检查API是否启用（考虑全局+群组，参数为api_id）
- `get_available_platforms(group_id)`: 获取可用平台列表（用于随机选择）

### 2. KeywordRegistry（关键词注册表模块）

**功能**：

- 管理平台到关键词的映射（platform -> (keyword, api_id, media_type)）
- 提供相似度匹配算法（支持精确匹配、部分匹配、模糊匹配）
- 线程安全的关键词注册和查询

**设计要点**：

- **注册格式**：从平台到API三元组（`{platform_name: [(keyword, api_id, media_type), ...]}`）
- **注册方式**：平台通过 `register_apis_from_map()` 自动从 `api_map` 注册，使用API标题作为关键词
- **匹配规则**：相似度匹配（不再全字匹配）
  - 精确匹配：相似度1.0
  - 部分匹配：query包含keyword或keyword包含query
  - 模糊匹配：使用SequenceMatcher计算相似度
- **相似度阈值**：默认0.6（60%）
- **匹配优先级**：全部平级，所有匹配的API一起随机选择

**主要方法**：

- `register(platform, keyword, api_id, media_type)`: 注册单个API的关键词
- `find_matching_apis(query, available_platforms, media_type)`: 查找匹配的API列表，返回 `(platform, api_id, media_type)` 三元组
- `get_keywords_for_platform(platform)`: 获取平台的关键词列表

**简化设计**：

- 平台只需维护 `api_map`（API标识 -> (URL, 标题, 媒体类型)）
- 不再需要 `keyword_map`，直接使用 `api_map` 的标题进行匹配
- 匹配时自动过滤媒体类型，返回匹配的API三元组

### 3. CacheManager（缓存管理模块）

**功能**：

- 成功时缓存API响应结果
- 失败时使用缓存结果响应
- 支持缓存过期时间配置

**缓存策略**：

- 缓存key：`f"{query}:{media_type}:{platform}"`
- 实现方式：内存缓存（字典结构，可扩展为Redis）

### 4. FailureTracker（失败追踪模块）

**功能**：

- 记录每个平台/API的连续失败次数
- 达到阈值（默认3次）后自动禁用
- 自动更新群组配置（添加到 `disabled_platforms`或 `disabled_apis`）

**追踪策略**：

- 失败key：`f"{platform}:{api_id}:{group_id}"`
- 成功调用后重置计数
- 自动禁用只影响群组配置，不会修改全局配置
- 禁用格式：`platform:api_id`（如 `"ak317:hssp"`）

### 5. 日志系统

**日志级别**：详细但不过于详细，方便调试

**记录内容**：

- 工具调用（参数、选择的平台）
- 关键词匹配（匹配的平台列表）
- API调用（成功/失败）
- 缓存命中/未命中
- 自动禁用事件

**不记录**：

- 详细的HTTP请求/响应内容
- 大量重复信息

---

## 实现细节

### MCP服务器主流程

```python
@server.call_tool()
async def call_tool(name: str, arguments: dict):
    if name == "get_media":
        # 1. 提取参数
        query = arguments.get("query")
        media_type = arguments.get("media_type", "all")
        group_id = arguments.get("group_id")  # 可选，不在schema中
      
        # 2. 权限过滤：获取可用平台列表
        available_platforms = config_manager.get_available_platforms(group_id)
        if not available_platforms:
            return {"error": "没有可用的平台"}
      
        # 3. 类型过滤：只保留支持指定media_type的平台
        type_filtered_platforms = []
        for platform_name in available_platforms:
            platform_instance = get_platform(platform_name)
            supported_types = platform_instance.get_supported_media_types()
            if media_type == "all" or media_type in supported_types:
                type_filtered_platforms.append(platform_name)
      
        # 4. 关键词匹配：使用相似度匹配找到匹配的API
        matching_apis = keyword_registry.find_matching_apis(
            query=query,
            available_platforms=type_filtered_platforms,
            media_type=media_type
        )
        # 返回: [(platform, api_id, media_type), ...]
      
        # 5. API禁用检查：过滤被禁用的API
        enabled_apis = []
        for platform, api_id, api_media_type in matching_apis:
            if config_manager.is_api_enabled(group_id, platform, api_id):
                enabled_apis.append((platform, api_id, api_media_type))
      
        # 6. 随机选择一个API
        platform, api_id, api_media_type = random.choice(enabled_apis)
      
        # 7. 检查缓存
        cache_key = f"{query}:{media_type}:{platform}"
        if cache_manager.has_cache(cache_key):
            return cache_manager.get_cache(cache_key)
      
        # 8. 调用平台API（传入api_id）
        try:
            platform_instance = get_platform(platform)
            platform_config = config_manager.get_platform_config(platform)
            results = await platform_instance.search_media(
                query=query,
                media_type=media_type,
                config=platform_config,
                api_id=api_id  # 传入匹配到的api_id
            )
          
            # 9. 只返回第一个结果
            if results:
                result = {
                    "url": results[0].url,
                    "type": results[0].media_type
                }
                # 10. 缓存结果
                cache_manager.set_cache(cache_key, result)
                # 11. 重置失败计数（使用api_id）
                failure_tracker.reset_failure(platform, api_id, group_id)
                return result
            else:
                raise Exception("未找到结果")
              
        except Exception as e:
            # 12. 记录失败（使用api_id）
            failure_tracker.record_failure(platform, api_id, group_id)
          
            # 13. 尝试使用缓存
            if cache_manager.has_cache(cache_key):
                return cache_manager.get_cache(cache_key)
          
            return {"error": str(e)}
```

### 平台选择逻辑

```python
def get_available_platforms(group_id: str = None) -> List[str]:
    """获取可用平台列表"""
    all_platforms = list(config_manager.get_platforms().keys())
    available = []
  
    for platform in all_platforms:
        # 检查全局禁用
        if not config_manager.is_platform_enabled(None, platform):
            continue
      
        # 检查群组禁用（如果提供了group_id）
        if group_id and not config_manager.is_platform_enabled(group_id, platform):
            continue
      
        # 检查平台是否已配置
        if not config_manager.get_platform_config(platform):
            continue
      
        available.append(platform)
  
    return available
```

---

## 使用示例

### Bot调用示例

**场景1：用户说"帮我找一张猫的图片"**

Bot调用：

```json
{
  "name": "get_media",
  "arguments": {
    "query": "猫",
    "media_type": "image",
    "group_id": "123456789"  // Bot框架自动注入
  }
}
```

MCP处理：

1. 检查群组123456789的权限配置
2. 从启用的平台中随机选择一个（如pixabay）
3. 调用pixabay API搜索"猫"的图片
4. 返回第一个结果的URL

返回：

```json
{
  "url": "https://pixabay.com/get/xxx.jpg",
  "type": "image"
}
```

**场景2：通用场景（无group_id）**

Bot调用：

```json
{
  "name": "get_media",
  "arguments": {
    "query": "sunset",
    "media_type": "image"
  }
}
```

MCP处理：

1. 没有group_id，跳过群组权限检查
2. 从所有已配置的平台中随机选择一个
3. 调用API并返回结果

### 配置示例场景

**场景1：全局禁用某个平台**

```json
{
  "global": {
    "disabled_platforms": ["unsplash"]
  }
}
```

**效果**：所有群组都不能使用unsplash平台

**场景2：全局禁用某个API**

```json
{
  "global": {
    "disabled_apis": ["pixabay:get_by_id"]
  }
}
```

**效果**：

- 所有群组都可以使用pixabay的 `search` API
- 所有群组都不能使用pixabay的 `get_by_id` API

**场景3：群组额外禁用**

```json
{
  "global": {
    "disabled_platforms": ["unsplash"]
  },
  "groups": {
    "123456789": {
      "disabled_platforms": ["pexels"],
      "disabled_apis": ["pixabay:search"]
    }
  }
}
```

**效果**：

- 群组123456789：
  - 不能使用unsplash（全局禁用）
  - 不能使用pexels（群组禁用）
  - 不能使用pixabay的search API（群组禁用）
  - 可以使用pixabay的get_by_id API（如果pixabay提供）
- 其他群组：
  - 不能使用unsplash（全局禁用）
  - 可以使用pexels
  - 可以使用pixabay的所有API

---

## 技术栈

- Python 3.8+
- `mcp` SDK（MCP协议实现）
- `httpx`（异步HTTP请求）
- `watchdog`（配置文件热重载监控）

## 优势总结

1. **减少token消耗**：

   - 只有一个工具
   - 返回格式最简化
   - 只返回第一个结果
2. **提高通用性**：

   - group_id可选，可用于非QQ Bot场景
   - 不强制要求群组配置
3. **提高可靠性**：

   - 缓存机制保证有结果返回
   - 自动禁用机制避免重复失败
4. **灵活的权限控制**：

   - 支持全局禁用平台/API
   - 支持群组级别额外禁用
   - 支持平台级别的API声明
5. **易于调试**：

   - 详细的日志记录
   - 关键信息清晰
