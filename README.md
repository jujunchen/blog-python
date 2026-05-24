# 博客系统

基于 Python FastAPI + Jinja2 的个人博客系统。

## 功能特性

- 服务端渲染，SEO 友好
- 主题切换（亮色/暗色）
- Markdown 文章编辑与渲染
- 文章同步到 CSDN、微信公众号
- 评论系统（支持注册用户和匿名评论）
- 管理后台

## 界面预览
### 管理后台
![管理后台](doc/images/admin_index.png)
### 首页
![首页](doc/images/index.png)

## 技术栈

- Python 3.11+
- FastAPI
- Jinja2
- SQLAlchemy
- SQLite

## 快速开始

### 方式一：使用便捷脚本（推荐）

**Windows 用户：**

1. 初始化环境（首次运行）：
```bash
setup.bat
```

2. 启动服务：
```bash
start.bat
```

**Linux/Mac 用户：**

1. 初始化环境（首次运行）：
```bash
chmod +x setup.sh start.sh
./setup.sh
```

2. 启动服务：
```bash
./start.sh
```

### 方式二：手动安装

1. 创建虚拟环境（推荐）：
```bash
python -m venv .venv
```

2. 激活虚拟环境：
   - Windows: `.venv\Scripts\activate`
   - Linux/Mac: `source .venv/bin/activate`

3. 安装依赖：
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

4. 启动服务：
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

5. 访问 http://localhost:8000

## 默认管理员账号

- 用户名：admin
- 密码：admin123

## 目录结构

```
blog-python/
├── app/
│   ├── __init__.py
│   ├── main.py          # FastAPI 应用入口
│   ├── models.py        # 数据库模型
│   ├── schemas.py       # Pydantic 校验模型
│   ├── crud.py          # 数据访问层
│   ├── services/        # 服务层
│   │   ├── sync.py      # 同步服务
│   │   └── adapters/    # 平台适配器
│   ├── templates/       # Jinja2 模板
│   └── static/          # 静态资源
├── config.py            # 配置文件
├── requirements.txt     # 依赖
├── setup.bat/sh         # 环境初始化脚本
├── start.bat/sh         # 启动脚本
└── doc/
    └── development_design.md  # 设计方案
```

## 常见问题

### Python 3.13 依赖安装问题

如果你使用 Python 3.13 并遇到依赖编译失败(如 `pydantic-core` 或 `sqlalchemy`),项目已自动升级到兼容版本:
- `pydantic`: 2.5.3 → 2.10.6
- `sqlalchemy`: 2.0.25 → 2.0.36

直接运行 `setup.bat` 或 `setup.sh` 即可自动安装兼容版本。

如需手动解决:
```bash
pip install --upgrade pip
pip install pydantic==2.10.6 sqlalchemy==2.0.36
```

### 脚本执行问题

**Windows PowerShell 用户:**
如果运行脚本时提示 "无法将项识别为 cmdlet",请使用 `.\` 前缀:
```powershell
.\setup.bat
.\start.bat
```

**编码问题:**
脚本已使用 UTF-8 编码,如果仍出现乱码,请确保终端支持 UTF-8:
```powershell
chcp 65001
```
