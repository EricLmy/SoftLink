# 项目说明文档

本项目为库存管理工具系统，包含前端（React+Vite）与后端（Flask+SQLAlchemy）两部分，支持容器化部署，具备完善的自动化测试与环境配置，适合企业级库存、订单、告警等场景。

---

## 一、前端项目说明（frontend）

### 1. 目录结构与主要文件

```
frontend/
├── src/                # 前端核心源码目录
│   ├── assets/         # 静态资源（图片、图标等）
│   ├── components/     # 可复用UI组件（如Layout.tsx）
│   ├── config/         # 配置相关（如全局常量、环境变量封装）
│   ├── layouts/        # 页面布局组件（如MainLayout.tsx，统一导航、侧边栏等）
│   ├── pages/          # 业务页面（每个模块一个tsx文件）
│   ├── routes/         # 路由配置（index.tsx，定义页面跳转与权限控制）
│   ├── services/       # API服务层（接口请求封装）
│   ├── utils/          # 工具函数（如格式化、通用请求等）
│   ├── App.tsx         # 应用主入口组件
│   ├── main.tsx        # 应用启动入口
│   ├── index.css       # 全局样式
│   └── App.css         # 应用级样式
├── public/             # 公共静态资源（如favicon、svg等）
├── tests/              # 端到端自动化测试（Selenium、Jest等）
│   ├── test_inventory_e2e.py   # 库存相关E2E测试
│   ├── test_product_e2e.py     # 商品相关E2E测试
│   ├── test_login_e2e.py       # 登录注册E2E测试
│   └── login.test.tsx          # 登录页面单元测试
├── package.json        # 项目依赖与脚本配置
├── package-lock.json   # 依赖锁定文件
├── tsconfig.json       # TypeScript 配置
├── tsconfig.app.json   # 应用TS配置
├── tsconfig.node.json  # Node相关TS配置
├── vite.config.ts      # Vite 构建工具配置
├── .env.example        # 环境变量示例
├── Dockerfile          # 前端容器化部署脚本
├── README.md           # 项目说明文档
└── .gitignore          # Git忽略文件
```

#### 主要目录与文件说明
- `src/pages/`：每个页面对应一个tsx文件，如 `Login.tsx`（登录）、`Register.tsx`（注册）、`Product.tsx`（商品管理）、`Inventory.tsx`（库存管理）、`Order.tsx`（订单管理）、`Alert.tsx`（告警中心）等。
- `src/components/`：可复用组件，如 `Layout.tsx`（通用布局）。
- `src/layouts/`：整体布局组件，如 `MainLayout.tsx`，实现统一导航、侧边栏等。
- `src/routes/index.tsx`：前端路由配置，负责页面跳转、权限校验。
- `src/services/`：接口请求封装，便于统一管理API调用。
- `src/utils/`：工具函数，如 `request.ts`（通用请求封装）、`format.ts`（格式化工具）。
- `tests/`：端到端自动化测试脚本，覆盖主要业务流程。
- `public/`：静态资源目录，存放favicon、logo等。
- `Dockerfile`：前端镜像构建脚本，便于容器化部署。
- `vite.config.ts`：Vite构建工具配置，支持热更新、代理等。

---

### 2. 启动与部署说明

#### 本地开发环境
```bash
cd frontend
npm install
# 或
yarn install
npm run dev
# 或
yarn dev
```
默认开发端口为 `5173`，可通过 `.env` 文件自定义。

访问地址：`http://localhost:5173`

#### 生产环境构建与部署
```bash
npm run build
# 或
yarn build
```
构建产物在 `dist/` 目录。

本地预览：
```bash
npm run preview
```

#### Docker 部署
- 使用 `Dockerfile` 构建前端镜像，推荐与后端、数据库等服务一同用 `docker-compose` 管理。

---

### 3. 环境变量与配置
- `.env.example`：环境变量示例，复制为 `.env` 并根据实际情况填写。
- 常用变量如 `VITE_API_BASE_URL`（后端API地址）、`VITE_APP_TITLE` 等。

---

### 4. 自动化测试
- `tests/` 目录下为端到端测试脚本，需先启动前后端服务后运行。
- 推荐命令：`pytest tests/ --maxfail=3 --disable-warnings -v`
- 也可用 `Jest` 针对 React 组件做单元测试。

---

## 二、后端项目说明（backend）

### 1. 目录结构与主要文件

```
backend/
├── app/                # 主业务代码目录
│   ├── api/            # 业务接口（每个模块一个py文件，如auth、user、product等）
│   ├── models/         # 数据模型（ORM定义，表结构）
│   ├── config.py       # 配置管理
│   ├── extensions.py   # 第三方扩展初始化（如db、jwt等）
│   ├── decorators.py   # 通用装饰器
│   └── __init__.py     # 应用初始化
├── migrations/         # 数据库迁移脚本（Alembic/Flask-Migrate）
│   ├── versions/       # 版本化迁移脚本
│   ├── env.py          # 迁移环境配置
│   └── alembic.ini     # Alembic配置
├── tests/              # 后端自动化测试（Pytest）
│   ├── test_auth.py            # 认证相关测试
│   ├── test_inventory.py       # 库存相关测试
│   ├── test_order.py           # 订单相关测试
│   ├── test_stock_record.py    # 出入库相关测试
│   ├── test_alert.py           # 告警相关测试
│   └── conftest.py             # 测试环境配置
├── scripts/            # 运维/工具脚本（如插入测试数据）
│   └── insert_test_data.py
├── instance/           # 本地配置/数据库文件（如dev.db）
├── .env                # 环境变量配置（生产/开发环境切换）
├── .env.example        # 环境变量示例
├── requirements.txt    # Python依赖列表
├── Dockerfile          # 后端容器化部署脚本
├── run.py              # 启动入口
├── startup_check_and_run.py # 启动前检查与运行脚本
├── README.md           # 项目说明文档
└── .gitignore          # Git忽略文件
```

#### 主要目录与文件说明
- `app/api/`：每个业务模块一个文件，如 `auth.py`（认证）、`user.py`（用户）、`product.py`（商品）、`inventory.py`（库存）、`order.py`（订单）、`stock_record.py`（出入库）、`alert.py`（告警）等，采用 Flask-Restx 组织接口。
- `app/models/`：ORM数据模型定义，所有表结构与字段。
- `app/config.py`：全局配置（数据库、JWT密钥等）。
- `app/extensions.py`：第三方库初始化（如SQLAlchemy、JWT）。
- `migrations/`：数据库迁移脚本，支持表结构变更管理。
- `tests/`：Pytest自动化测试，覆盖主要业务流程。
- `scripts/`：运维脚本，如批量插入测试数据。
- `instance/`：本地数据库文件或私有配置。
- `requirements.txt`：后端依赖包列表。
- `Dockerfile`：后端镜像构建脚本，便于容器化部署。
- `run.py`：后端服务启动入口。

---

### 2. 启动与部署说明

#### 本地开发环境
```bash
cd backend
pip install -r requirements.txt
```

数据库迁移：
```bash
flask db upgrade
# 或
python -m flask db upgrade
```

启动开发服务：
```bash
python run.py
# 或
flask run
```
默认端口为 `5000`，可通过 `.env` 配置。

访问API文档：`http://localhost:5000/api/doc/`

#### 生产环境部署
- 使用 `Dockerfile` 构建后端镜像，推荐与前端、数据库等服务一同用 `docker-compose` 管理。

---

### 3. 环境变量与配置
- `.env.example`：环境变量示例，复制为 `.env` 并根据实际情况填写。
- 常用变量如 `FLASK_ENV`（环境类型）、`DATABASE_URL`（数据库连接）、`JWT_SECRET_KEY`（JWT密钥）等。

---

### 4. 自动化测试
- `tests/` 目录下为后端单元测试脚本，推荐使用 `pytest` 执行。
- 推荐命令：`pytest tests/ --maxfail=3 --disable-warnings -v`
- 覆盖认证、商品、库存、订单、告警等主要业务流程。

---

### 5. 常见维护建议
- **新增业务模块**：在 `app/api/` 和 `app/models/` 下分别添加接口和数据模型，并同步更新数据库迁移脚本。
- **接口变更**：同步维护前端 `src/services/` 与后端 `app/api/`，保持接口文档与实现一致。
- **环境切换**：通过 `.env` 文件灵活切换开发、测试、生产环境。
- **自动化测试**：每次功能迭代后，务必补充和执行自动化测试，保证主流程稳定。

---

如需更详细的某个模块说明、部署脚本示例或CI/CD集成建议，请随时联系维护人或核心开发团队。

## 开发和测试进度

- [x] 前端主流程页面开发（仪表盘、商品、库存、订单、告警、权限、个人中心、登录/注册）
- [x] 后端API开发与数据库建模
- [x] 前端E2E自动化测试脚本编写
- [x] 后端pytest单元测试脚本编写
- [x] Docker化与一键部署脚本
- [x] 环境变量与配置管理
- [x] 代码规范与注释完善
- [ ] 持续修正E2E测试与页面内容细节
- [ ] 权限管理与子账号功能细化
- [ ] CI/CD自动化集成
- [ ] 安全加固与上线准备 