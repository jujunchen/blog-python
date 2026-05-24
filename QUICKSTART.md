# 快速开始指南 🚀

## 一分钟启动项目

### 1️⃣ 初始化环境 (仅首次运行)

**Windows:**
```powershell
.\setup.bat
```

**Linux/Mac:**
```bash
chmod +x setup.sh
./setup.sh
```

### 2️⃣ 启动服务器

**Windows:**
```powershell
.\start.bat
```

**Linux/Mac:**
```bash
chmod +x start.sh
./start.sh
```

### 3️⃣ 访问博客

打开浏览器访问: **http://localhost:8000**

**管理员账号:**
- 用户名: `admin`
- 密码: `admin123`

---

## 常见问题速查

### ❓ 提示 "无法识别的命令"
**解决**: 使用 `.\` 前缀
```powershell
.\setup.bat  # ✅ 正确
setup.bat    # ❌ 错误
```

### ❓ 依赖安装失败
**解决**: 清理缓存后重试
```bash
pip cache purge
.\setup.bat
```

### ❓ 端口被占用
**解决**: 修改 start.bat 中的端口号
```batch
uvicorn app.main:app --reload --host 0.0.0.0 --port 8001
```

---

## 项目结构速览

```
blog-python/
├── setup.bat/sh      ← 环境初始化脚本
├── start.bat/sh      ← 启动脚本
├── requirements.txt  ← 依赖列表
├── app/
│   ├── main.py       ← 应用入口
│   ├── models.py     ← 数据模型
│   ├── crud.py       ← 数据库操作
│   ├── services/     ← 业务逻辑
│   ├── templates/    ← 页面模板
│   └── static/       ← 静态资源
└── config.py         ← 配置文件
```

---

## Python 3.13 兼容性

项目已完全适配 Python 3.13:
- ✅ pydantic 2.10.6 (预编译 wheel)
- ✅ sqlalchemy 2.0.36
- ✅ 所有依赖均已验证

无需额外配置,直接运行即可! 🎉