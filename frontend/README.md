# 前端项目说明（React + Ant Design）

## 项目简介
本项目为库存管理系统前端，基于 React + Ant Design + Vite 构建，支持商品、库存、订单、权限等模块的管理，界面美观，支持响应式。

## 主要依赖
- react
- react-dom
- react-router-dom
- antd
- axios
- echarts
- vite

## 开发启动
```bash
npm install
npm run dev
```
默认端口：5174

## 构建打包
```bash
npm run build
```
产物在 `dist/` 目录。

## 目录结构
- src/pages/         主要页面
- src/layouts/       布局组件
- src/routes/        路由配置
- src/api/           前端接口封装
- src/components/    公共组件
- public/            静态资源

## 常见问题
- 启动端口冲突：修改 `vite.config.ts` 中的端口配置。
- 接口跨域：开发环境已配置代理，生产环境需后端支持 CORS。
- 登录后页面未跳转：请检查 token 存储与路由守卫逻辑。

## 运维建议
- 推荐使用 Nginx 反向代理部署 dist 目录。
- 静态资源可用 OSS/CDN 加速。
- 前端异常建议接入 Sentry 监控。

---
如需二次开发或定制化，请联系前端负责人。
