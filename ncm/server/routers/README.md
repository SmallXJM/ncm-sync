# Service 层架构说明 (重构版)

## 核心设计理念

Service 层专为**单实例 NAS Docker 服务**设计，简化了 Cookie 管理逻辑：

- **一次选择，持续使用** - 程序启动时选择一个 Cookie，持续使用直到失效
- **失效时自动切换** - 当前 Cookie 失效时自动选择下一个可用的
- **内存缓存优化** - 避免频繁数据库查询
- **持久化选择** - 重启后根据 last_selected_at 恢复上次使用的 Cookie

## 架构组件

### 🎯 CookieService - 简化的会话管理中枢

**核心职责**：
- 提供当前可用的 Cookie (`get_current_cookie`)
- 处理使用成功回调 (`mark_cookie_success`)
- 处理使用失败回调 (`mark_cookie_failure`)
- 管理会话生命周期和自动切换

**设计原则**：
- 程序运行期间使用同一个 Cookie
- 失效时自动切换到下一个可用 Cookie
- 内存缓存避免频繁数据库查询
- 重启后恢复上次使用的 Cookie

```python
from ncm.server.routers import get_cookie_service

# 获取服务实例
cookie_service = get_cookie_service()

# 获取当前 Cookie
cookie = cookie_service.get_current_cookie()
if cookie:
    print(f"当前使用的 Cookie: {cookie[:20]}...")

    # 使用 Cookie 进行 API 调用
    try:
        # ... 网络请求 ...
        # 成功时回调
        cookie_service.mark_cookie_success()
    except Exception:
        # 失败时回调
        cookie_service.mark_cookie_failure()
```

### 🔄 装饰器系统

**自动 Cookie 管理装饰器**：

```python
from ncm.service.cookie import with_cookie, with_cookie


@with_cookie
async def my_api_call(**kwargs):
    # Cookie 会自动注入到 kwargs 中
    response = await some_api_call(**kwargs)
    return response


@with_cookie(max_retries=2)
async def my_api_call_with_retry(**kwargs):
    # 失败时自动重试，使用新的 Cookie
    response = await some_api_call(**kwargs)
    return response
```

**简单 Cookie 检查装饰器**：

```python
from ncm.service.cookie.decorators import require_cookie


@require_cookie
async def my_simple_call(**kwargs):
    # 确保有可用 Cookie，但不处理重试
    return await some_api_call(**kwargs)
```

### 🎵 业务服务示例

#### AuthService - 认证服务

```python
from ncm.server.routers import AuthService

auth_service = AuthService()

# 开始二维码登录
qr_info = await auth_service.start_qr_login()
print(f"请扫描二维码: {qr_info['qr_url']}")

# 检查登录状态
status = await auth_service.check_qr_login(qr_info['qr_key'])

if status['status'] == 'success':
    print("登录成功！")

# 获取当前登录状态（使用可用 Cookie）
current_status = await auth_service.get_login_status()

# 获取本地登录状态（无网络请求）
local_status = auth_service.get_local_login_status()
```

#### MusicService - 音乐服务

```python
from ncm.server.routers import MusicService

music_service = MusicService()

# 增强搜索（搜索 + 详情获取）
results = await music_service.enhanced_search(
    keywords="周杰伦",
    search_type="song",
    include_details=True
)

# 歌单分析（歌单信息 + 歌曲详情 + 统计分析）
analysis = await music_service.analyze_playlist(
    playlist_id="123456",
    include_song_details=True
)

# 批量下载准备（链接获取 + 质量检查）
download_info = await music_service.prepare_download_batch(
    song_ids=["1001", "1002", "1003"],
    quality="exhigh"
)
```

#### UserService - 用户服务

```python
from ncm.server.routers import UserService

user_service = UserService()

# 获取用户资料
profile = await user_service.get_user_profile()

# 切换会话
switch_result = await user_service.switch_session("session_id_123")

# 列出所有会话
sessions = user_service.list_all_sessions()

# 获取当前用户信息
current_user = user_service.get_current_account_info()
```

## Cookie 管理流程

### 1. 程序启动时的 Cookie 选择
```
1. 查询所有 valid=true 的会话
2. 按 last_selected_at 降序排序
3. 选择第一个（最近使用的）
4. 更新其 last_selected_at = now()
5. 缓存到内存中
```

### 2. Cookie 使用成功处理
```
1. 更新 last_success_at = now()
2. 重置 fail_count = 0
3. 保持当前 Cookie 不变
```

### 3. Cookie 使用失败处理
```
1. 增加 fail_count += 1
2. 如果 fail_count >= max_failures:
   - 设置 is_valid = false
   - 选择下一个可用 Cookie
3. 更新内存缓存
```

### 4. 自动切换机制
```
当前 Cookie 失效 → 自动选择下一个可用 Cookie → 
更新内存缓存 → 无需显式切换操作
```

## 错误处理策略

### 1. 网络错误
- 自动重试（装饰器控制）
- Cookie 失败计数
- 达到阈值后自动切换

### 2. 认证错误
- 立即标记 Cookie 失效
- 自动切换到下一个可用 Cookie
- 提示用户重新登录（如果没有可用 Cookie）

### 3. 业务错误
- 不影响 Cookie 状态
- 直接返回错误信息

## 扩展指南

### 添加新的业务服务

1. **创建服务类**：
```python
class MyService:
    def __init__(self):
        self.cookie_service = get_cookie_service()
        self.account_repo = AccountRepository()
```

2. **使用装饰器**：
```python
@ncm_service("/ncm/my/endpoint", ["POST"])
@with_cookie(max_retries=2)
async def my_business_workflow(self, **kwargs):
    # 业务逻辑
    pass
```

3. **注册到 __init__.py**：
```python
from .my_service import MyService
__all__.append("MyService")
```

### 自定义 Cookie 管理

如果需要特殊的 Cookie 管理逻辑：

```python
@manual_cookie_management
async def custom_cookie_handling(self, **kwargs):
    try:
        result = await some_api_call(**kwargs)
        return result, True  # 成功
    except Exception:
        return None, False   # 失败
```

## 最佳实践

1. **服务职责单一**：每个服务专注特定业务领域
2. **使用装饰器**：让装饰器处理 Cookie 管理，专注业务逻辑
3. **错误处理**：区分网络错误、认证错误和业务错误
4. **日志记录**：记录关键业务流程和错误信息
5. **状态管理**：复杂状态通过数据库持久化，不依赖内存

## 与旧架构的主要区别

### 简化的设计
- **移除复杂的轮换策略** - 单实例服务不需要复杂轮换
- **内存缓存当前 Cookie** - 避免频繁数据库查询
- **简化的失效处理** - 失效时直接切换，不需要复杂策略

### 保留的核心功能
- **会话管理** - 仍然支持多账户和会话
- **自动切换** - Cookie 失效时自动切换
- **持久化** - 重启后恢复状态

这个重构后的架构确保了：
- **高性能**：内存缓存减少数据库查询
- **高可用性**：自动 Cookie 切换和重试
- **易维护性**：清晰的职责分离和简化的逻辑
- **可扩展性**：装饰器和服务模式易于扩展
- **适用性**：专为单实例 NAS 服务优化