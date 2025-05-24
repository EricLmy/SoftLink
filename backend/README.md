# 后端项目说明（Flask）

## 项目简介
本项目为库存管理系统后端，基于 Flask + SQLAlchemy + PostgreSQL，提供商品、库存、订单、权限等模块的 RESTful API。

## 主要依赖
- flask
- flask-restx
- flask-jwt-extended
- flask-sqlalchemy
- flask-migrate
- psycopg2-binary
- celery
- redis

## 开发启动
```bash
pip install -r requirements.txt
python backend/startup_check_and_run.py run
```
默认端口：5000

## 数据库迁移
```bash
python backend/startup_check_and_run.py db upgrade
```

## 接口文档
- 访问 `/api/product/doc` 查看商品管理接口文档（Swagger UI）。
- 其他模块接口文档可参考 `/api/xxx/doc`。

## 目录结构
- app/models/    数据库模型
- app/api/       业务接口
- app/extensions/扩展与中间件
- app/config/    配置文件
- migrations/    数据库迁移

## 常见问题
- 数据库连接失败：请检查 PostgreSQL 配置与服务状态。
- Redis/Celery 启动失败：请检查 Redis 服务。
- 跨域问题：已支持 CORS，前端需配置正确。

## 运维建议
- 推荐使用 Docker Compose 一键部署。
- 生产环境建议定期备份数据库。
- 日志建议接入 ELK/Sentry 监控。

---
如需二次开发或定制化，请联系后端负责人。 