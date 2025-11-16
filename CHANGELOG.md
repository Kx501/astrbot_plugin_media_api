# 更新日志

## 2025-11-16 - 架构重构

### 重大变更

1. **简化数据结构**

   - 删除 `keyword_map`，直接使用 `api_map` 的标题进行匹配
   - 删除 `video_apis` 和 `image_api_url`，所有信息统一在 `api_map` 中
   - 平台只需维护一个 `api_map` 数据结构
2. **改进匹配机制**

   - 匹配流程优化：先类型过滤 → 再关键词匹配 → 最后随机选择
   - 关键词匹配改为相似度匹配（精确、部分、模糊）
   - 匹配返回 `(platform, api_id, media_type)` 三元组
3. **API禁用机制改进**

   - 禁用格式改为 `platform:api_id`（如 `"ak317:hssp"`）
   - 支持精确到单个API的禁用控制
   - `ConfigManager.is_api_enabled()` 参数改为 `api_id`
4. **平台注册机制**

   - 新增 `register_apis_from_map()` 方法，自动从 `api_map` 注册
   - 新增 `get_supported_media_types()` 方法，声明平台支持的媒体类型
   - 平台 `search_media()` 方法新增 `api_id` 参数
5. **KeywordRegistry重构**

   - 注册格式改为 `(keyword, api_id, media_type)` 三元组
   - `find_matching_apis()` 返回匹配的API三元组列表
   - 匹配时自动过滤媒体类型

### 更新的文件

- `keyword_registry.py`: 重构为支持三元组注册和匹配
- `platform_base.py`: 新增 `register_apis_from_map()` 和 `get_supported_media_types()`
- `config_manager.py`: `is_api_enabled()` 参数改为 `api_id`
- `mcp_server.py`: 实现新的匹配流程
- `platforms/ak317_platform.py`: 删除冗余数据结构，简化实现
- `platforms/xingchenfu_platform.py`: 删除冗余数据结构，简化实现
- `platforms/lolimi_platform.py`: 删除冗余数据结构，简化实现
- `README.md`: 更新文档，反映最新架构
- `DESIGN.md`: 更新设计文档，反映最新架构

### 向后兼容性

⚠️ **不兼容变更**：

- 配置中的 `disabled_apis` 格式从 `"platform:api_name"` 改为 `"platform:api_id"`
- 平台需要实现 `get_supported_media_types()` 方法
- 平台的 `search_media()` 方法需要接受 `api_id` 参数
