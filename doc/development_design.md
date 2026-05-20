# 个人博客系统开发设计方案

## 概述

本项目是一套基于 Python 的个人博客系统，采用 FastAPI + Jinja2 模式实现前后端一体化，并兼顾 SEO、主题切换、Markdown 编辑、评论管理与内容同步能力。

核心目标：
- 通过服务端模板渲染保证 SEO 友好
- 支持主题切换，并可在前端持久化用户选择
- 支持文章 Markdown 编辑与渲染
- 支持文章同步到 CSDN、微信公众号等自媒体平台，并可扩展更多平台
- 提供单一管理员后台，不需要复杂权限配置
- 评论支持注册用户评论和匿名评论，并由后台配置开关控制
- 不包含自动发布或定时发布功能，发布流程由管理员手动执行

## 技术选型

- Python 3.11+（或兼容最新稳定 Python 版本）
- FastAPI：负责路由、业务逻辑、API 和模板渲染
- Jinja2：页面渲染模板
- SQLite：初期数据库，后续可平滑迁移到 PostgreSQL 或 MySQL
- SQLAlchemy（或 Tortoise ORM）：数据库模型与 ORM 支持
- Markdown 渲染库：`markdown`、`markdown-it-py` 或 `mistune`
- 静态资源：CSS、少量 JavaScript

## 系统架构

1. 前端页面以 Jinja2 模板渲染为主，所有公开页面直接返回完整 HTML，保证搜索引擎抓取效果。
2. 后端由 FastAPI 提供页面路由、管理后台页面、API 和表单接口。
3. 主题模块通过模板变量控制 CSS 引入，前端切换后结果可持久化到后台配置或会话 Cookie。
4. 同步服务采用适配器插件机制，新增平台时只需新增适配器模块并注册。
5. 评论功能支持注册用户与匿名评论，由后台配置开关控制是否开放。

## 目录结构建议

- `app/main.py` — FastAPI 应用入口，路由注册和模板配置
- `app/models.py` — 数据模型定义
- `app/schemas.py` — Pydantic 校验模型
- `app/crud.py` — 数据访问与操作逻辑
- `app/services/sync.py` — 同步服务管理和调度
- `app/services/adapters/` — 平台适配器模块目录
- `app/templates/` — Jinja2 页面模板
- `app/static/` — CSS、JS、图片等静态资源
- `config.py` — 配置项与插件注册
- `doc/development_design.md` — 本设计方案文档
- `README.md` — 项目说明和部署文档

## 数据模型设计

### Article

- id
- title
- slug
- summary
- markdown_content
- html_content
- cover_image
- status（draft/published）
- publish_date
- category_id
- tags
- created_at
- updated_at

### Category / Tag

- id
- name
- slug
- description

### ThemeSetting

- id
- current_theme
- available_themes
- updated_at

### SyncAccount

- id
- platform_type
- account_name
- config_data
- credential
- created_at
- updated_at

### SyncRecord

- id
- article_id
- platform_type
- status
- result_message
- synced_at

### Comment

- id
- article_id
- author_name
- author_email
- content
- is_anonymous
- approved
- created_at

### CommentConfig

- id
- allow_registered_comments
- allow_anonymous_comments
- require_approval
- created_at
- updated_at

### AdminUser

- id
- username
- password_hash
- created_at
- updated_at

## 主要页面与路由设计

### 公开页面

- `/`：博客首页，文章列表与分页
- `/article/{slug}`：文章详情页
- `/category/{slug}`：分类文章页
- `/tag/{slug}`：标签文章页
- `/search`：搜索结果页
- `/archives`：归档页
- `/sitemap.xml`：站点地图
- `/robots.txt`：搜索引擎规则

### 管理后台

- `/admin/login`：管理员登录
- `/admin/dashboard`：后台首页
- `/admin/articles`：文章列表管理
- `/admin/articles/new`：新增文章
- `/admin/articles/{id}/edit`：编辑文章
- `/admin/sync`：同步管理与执行
- `/admin/comments`：评论管理（审核/删除）
- `/admin/settings`：系统设置、主题设置、评论开关

### API / 表单接口

- `/api/comments`：文章评论提交
- `/api/theme`：主题切换请求
- `/api/sync`：手动同步触发
- `/admin/login`：管理员登录表单处理
- `/admin/articles/...`：文章提交与保存

## 主题系统设计

- 提供至少两套主题：例如亮色主题与暗色主题，或经典主题与现代主题。
- 通过 Jinja2 模板变量 `current_theme` 或 `theme_css` 引入对应 CSS 文件。
- 主题选择可以在后台设置页中调整，并持久化到 `ThemeSetting`。
- 也可支持前端通过 Cookie / 会话存储当前主题，用户切换即时生效。

## 同步适配器设计

### 适配器接口

统一接口 `SyncAdapter`，至少包含方法：
- `sync_article(article)`：执行文章同步
- `test_connection()`：测试账号连通性
- `build_payload(article)`：构造同步请求数据

### 默认适配器

- `app/services/adapters/csdn.py`：CSDN 平台同步实现
- `app/services/adapters/wechat.py`：微信公众号同步实现

### 注册与扩展

- 同步服务从配置中读取已启用平台
- 新平台只需新增适配器模块并注册到同步服务
- 同步数据包含文章标题、内容、摘要、封面、分类、标签等

## 评论功能设计

- 支持“注册用户评论”和“匿名评论”两种模式
- 后台设置页面提供开关：
  - 是否启用注册用户评论
  - 是否启用匿名评论
  - 是否启用评论审核
- 评论提交时根据配置校验权限或是否允许匿名提交
- 评论列表可以在后台审核、删除
- 前端评论区显示评论输入表单和登录提示

## SEO 支持

- 所有页面均通过服务器端渲染输出完整 HTML
- 每篇文章与页面都生成 `meta title` 和 `meta description`
- 文章详情页采用友好 URL：`/article/{slug}`
- 生成 `sitemap.xml`，便于搜索引擎抓取
- 提供 `robots.txt`，控制搜索引擎爬虫行为
- 文章摘要、结构化数据（如 JSON-LD）可作为后续优化项

## 部署与验证

### 本地开发

- 使用 `uvicorn` 启动 FastAPI 应用
- 本地测试页面是否可正常渲染、主题切换和评论提交

### Docker / VPS 部署

- 可选构建 Docker 镜像，便于跨平台部署
- 可在 VPS 上直接运行 Python/uvicorn，并使用 Nginx 反向代理

### 验证点

- 页面渲染正常且 HTML 源码可见
- 文章 Markdown 能正确转换并显示为 HTML
- 主题切换实时生效并可持久化
- 同步适配器机制可扩展，新适配器只需新增模块
- 评论配置开关生效，注册用户与匿名评论按设置启用或禁用
- SEO 要素正确输出，包括 meta、sitemap、robots

## 进一步扩展建议

- 后续可接入更多同步平台，例如简书、知乎专栏、微博
- 后续可增加静态页面生成方案，用于极致 SEO 和部署性能
- 后续可增加简单缓存机制，提升页面响应速度

## 安全性设计

- 所有表单提交均需实现 CSRF 防护机制，使用 Starlette 内置的 CSRF 中间件或自定义实现
- 评论提交模块建议集成 CAPTCHA（如 Google reCAPTCHA 或 hCaptcha）防止机器人 spam
- 管理后台登录需实现失败次数限制（如 5 次后锁定 15 分钟），并记录登录尝试日志

## 同步机制补充

- 同步服务应实现失败重试策略：首次失败后等待 30 秒重试，若再失败则等待 5 分钟，最多重试 3 次
- 每次同步操作记录详细日志，包括请求参数、响应状态、错误信息，便于排查问题
- 建议为每个平台适配器实现独立的超时设置（建议 30-60 秒）

## 评论功能补充

- 用户邮箱地址不会在前端公开显示，仅用于评论回复通知和通过邮箱找回评论
- 建议增加"通过邮箱验证找回评论"功能，允许用户凭邮箱查看自己历史评论

## 性能

- Markdown 转 HTML 推荐采用"保存时预渲染"策略：文章保存时一次性转换并存储 `html_content`，读取时直接使用，避免每次访问都转换
