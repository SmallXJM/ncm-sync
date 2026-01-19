# NCM 模块架构

`ncm` 模块的当前架构，经过重构以分离 Client、Server、Service、Data 和 Core 层之间的关注点。

## 目录结构

```
ncm/
├── client/                 # [外部] NCM API 客户端 (防腐层)
│   ├── apis/               # 功能模块 (例如：playlist, song, user)
│   ├── protocol/           # 协议实现
│   │   ├── crypto.py       # 加密 (weapi, eapi, linuxapi)
│   │   ├── headers.py      # HTTP 标头生成
│   │   ├── options.py      # 请求选项与 CryptoType
│   │   └── session.py      # 会话管理
│   ├── decorators.py       # 客户端装饰器 (@ncm_api)
│   ├── exceptions.py       # API 特定异常
│   └── http.py             # 高级 HTTP 客户端封装
│
├── server/                 # [内部] 本地 Web/WS 服务器 (接口层)
│   ├── framework/          # 服务端框架组件
│   │   ├── auto_router.py  # 自动路由注册
│   │   └── ...             # 请求解析、模块扫描
│   ├── middleware/         # FastAPI 中间件
│   ├── routers/            # 路由控制器 (FastAPI APIRouter)
│   │   ├── config/         # 系统配置端点
│   │   ├── download/       # 下载管理端点
│   │   ├── music/          # 音乐资源端点
│   │   └── user/           # 用户认证/个人资料端点
│   ├── websockets/         # WebSocket 处理器
│   ├── app.py              # FastAPI 应用程序入口点
│   └── decorators.py       # 服务端装饰器 (@ncm_service)
│
├── service/                # [核心] 领域服务 (业务逻辑)
│   ├── auth/               # 认证服务
│   ├── cookie/             # Cookie 管理领域
│   ├── download/           # 复杂下载领域
│   │   ├── downloader/     # 核心下载逻辑
│   │   ├── metadata/       # 元数据处理 (标签、封面)
│   │   ├── orchestrator/   # 任务调度与工作流
│   │   ├── service/        # 下载应用服务
│   │   └── storage/        # 文件存储管理
│   ├── lyrics/             # 歌词处理服务
│   ├── music/              # 本地音乐管理
│   └── user/               # 用户管理服务
│
├── data/                   # [持久化] 数据访问层
│   ├── models/             # SQLAlchemy ORM 模型
│   ├── repositories/       # 异步 CRUD 仓库
│   ├── migration/          # 数据库迁移
│   ├── engine.py           # 数据库引擎配置
│   └── session.py          # 会话工厂 (同步/异步)
│
└── core/                   # [基座] 基础设施与通用工具
    ├── constants/          # 项目全局常量
    ├── config.py           # 配置管理
    ├── cookie.py           # Cookie 解析工具
    ├── device.py           # 设备信息工具
    ├── logging.py          # 集中式日志配置
    ├── path.py             # 路径管理
    └── time.py             # 时间工具
```

## 层级说明

### 1. Client 层 (`ncm/client`)
负责与外部网易云音乐 API 的所有交互。
- **角色**: SDK / 防腐层 (Anti-Corruption Layer)。
- **关键组件**:
    - `apis/`: 包含远程 API 调用的定义。
    - `protocol/`: 处理底层加密和协议细节。
    - `decorators.py`: 导出 `@ncm_api` 以将函数标记为 API 客户端。

### 2. Server 层 (`ncm/server`)
通过 HTTP 和 WebSocket 暴露应用程序的功能。
- **角色**: 接口 / 表现层 (Interface / Presentation Layer)。
- **关键组件**:
    - `routers/`: 控制器，负责将 HTTP 请求映射到 Service 层调用。
    - `app.py`: 初始化 FastAPI 应用程序和生命周期事件。
    - `decorators.py`: 导出 `@ncm_service` 以将内部方法暴露为 HTTP 端点。

### 3. Service 层 (`ncm/service`)
包含应用程序的核心业务逻辑。
- **角色**: 领域逻辑 (Domain Logic)。
- **关键组件**:
    - `download/`: 一个复杂的领域，处理整个下载生命周期（编排、元数据、存储）。
    - `music/`: 管理本地音乐文件和库。
    - **注意**: 该层负责编排 `Client`（远程数据）和 `Data`（本地数据库）之间的数据流。

### 4. Data 层 (`ncm/data`)
处理数据持久化和数据库交互。
- **角色**: 基础设施 (持久化)。
- **关键组件**:
    - `models/`: 定义数据库模式 (Schema)。
    - `repositories/`: 封装数据库查询。

### 5. Core 层 (`ncm/core`)
提供所有其他层共用的共享工具和基础设施配置。
- **角色**: 横切关注点 (Cross-cutting concerns)。
- **关键组件**:
    - `config.py`: 加载并验证应用程序设置。
    - `constants/`: 常量值的中心仓库（例如 `DATABASE_NAME`）。
