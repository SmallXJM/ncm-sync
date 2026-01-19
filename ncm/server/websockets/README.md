# Download WebSocket 框架

该目录提供下载领域的 WebSocket 扩展框架，支持模块化扩展和热加载。

## 接口使用说明

- 连接地址：`/ncm/download/ws`
- 订阅消息格式：
  - `{"subscribe": "all"}`
  - `{"subscribe": "tasks"}`
  - `{"unsubscribe": "tasks"}`
- 可选控制字段：
  - `{"reload": true}` 触发模块热加载
  - `{"module": "<name>", ...}` 发送给指定模块的自定义消息

服务端推送数据格式：

- 任务信息：

```json
{"tasks": {"items": [], "count": 0}}
```

## 扩展开发指南

1. 在本目录新增模块文件，例如 `example.py`。
2. 实现一个模块类：

```python
from ncm.server.websockets.base import DownloadWsContext, WsModule, WsModuleRegistry


class ExampleWsModule:
    name = "example"

    def __init__(self, context: DownloadWsContext) -> None:
        self._context = context

    async def get_payload(self) -> dict | None:
        return {}

    async def handle_message(self, message: dict) -> dict | None:
        return None
```

3. 在同一文件中实现注册函数：

```python
def register_ws_modules(registry: WsModuleRegistry) -> None:
    module: WsModule = ExampleWsModule(registry.context)
    registry.register(module)
```

框架会自动扫描并加载该模块，无需修改主控制器。
