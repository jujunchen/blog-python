# FastAPI 应用入口
# Main Application

from datetime import datetime
from typing import Optional
import hashlib
import time
import secrets

from fastapi import FastAPI, Request, Depends, HTTPException, Form, Cookie, File, UploadFile
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse, PlainTextResponse
import os
import uuid
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

import config
from app.models import Base
from app import crud

# ============ 数据库设置 ============

engine = create_engine(config.DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    """数据库依赖"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ============ 应用初始化 ============

app = FastAPI(title=config.APP_NAME, version=config.APP_VERSION)

# Session 中间件 (需要 secret key)
app.add_middleware(SessionMiddleware, secret_key=config.SECRET_KEY or secrets.token_hex(32))

# 静态文件
app.mount("/static", StaticFiles(directory=config.STATIC_DIR), name="static")

# 模板引擎
templates = Jinja2Templates(directory=config.TEMPLATES_DIR)
templates.env.globals["config"] = config
templates.env.globals["now"] = datetime.now


# ============ 工具函数 ============

def get_current_theme(db: Session, theme_cookie: Optional[str] = None) -> str:
    """获取当前主题"""
    # 优先从数据库读取主题设置
    setting = crud.get_theme_setting(db)
    current_theme = setting.current_theme if setting else config.DEFAULT_THEME

    # 如果cookie中的主题合法且与数据库不同，以cookie为准（用户手动切换）
    if theme_cookie and theme_cookie in config.AVAILABLE_THEMES:
        return theme_cookie

    # print(f"[DEBUG] 获取当前主题: {current_theme}")
    return current_theme


def get_admin_from_session(request: Request, db: Session = Depends(get_db)) -> Optional[dict]:
    """从 session 获取管理员信息"""
    admin_id = request.session.get("admin_id")
    if not admin_id:
        return None
    admin = crud.get_admin_by_id(db, admin_id)
    if not admin or not admin.is_active:
        return None
    return {"id": admin.id, "username": admin.username}


def require_admin(request: Request, db: Session = Depends(get_db)) -> dict:
    """要求登录的管理员"""
    admin = get_admin_from_session(request, db)
    if not admin:
        raise HTTPException(status_code=401, detail="请先登录")
    return admin


def markdown_to_html(markdown_text: str) -> str:
    """Markdown 转 HTML"""
    import markdown
    return markdown.markdown(
        markdown_text,
        extensions=['tables', 'fenced_code', 'codehilite', 'nl2br']
    )


def generate_csrf_token() -> str:
    """生成 CSRF token"""
    return hashlib.sha256(f"{time.time()}{config.CSRF_SECRET_KEY}".encode()).hexdigest()


def verify_csrf_token(request: Request, csrf_token: str) -> bool:
    """验证 CSRF token"""
    cookie_token = request.cookies.get(config.CSRF_COOKIE_NAME)
    return cookie_token and csrf_token and cookie_token == csrf_token


def is_valid_slug(slug: str) -> bool:
    """验证 slug 格式：只能包含字母、数字和连字符"""
    import re
    return bool(re.match(r'^[a-zA-Z0-9-]+$', slug))


def flash_message(request: Request, message: str, category: str = "info"):
    """设置 Flash 消息"""
    if "messages" not in request.session:
        request.session["messages"] = []
    request.session["messages"].append({"message": message, "category": category})


def get_flashed_messages(request: Request) -> list:
    """获取并清除所有 Flash 消息"""
    messages = request.session.pop("messages", [])
    return messages


# ============ 中间件 ============

@app.middleware("http")
async def add_theme_to_request(request: Request, call_next):
    """添加主题到请求上下文"""
    response = await call_next(request)
    return response


# ============ 公开页面路由 ============

@app.get("/", response_class=HTMLResponse)
async def home(request: Request, db: Session = Depends(get_db)):
    """博客首页"""
    page = int(request.query_params.get("page", 1))
    per_page = 10
    skip = (page - 1) * per_page

    articles = crud.get_published_articles(db, skip, per_page)
    total = crud.get_articles_count(db, status='published')

    theme = get_current_theme(db, request.cookies.get("theme"))

    return templates.TemplateResponse("blog/home.html", {
        "request": request,
        "articles": articles,
        "total": total,
        "page": page,
        "per_page": per_page,
        "theme": theme,
        "categories": crud.get_categories(db),
        "tags": crud.get_tags(db)[:10]
    })


@app.get("/article/{slug}", response_class=HTMLResponse)
async def article_detail(slug: str, request: Request, db: Session = Depends(get_db)):
    """文章详情页"""
    article = crud.get_article_by_slug(db, slug)

    if not article or article.status != 'published':
        raise HTTPException(status_code=404, detail="文章未找到")

    comments = crud.get_comments_by_article(db, article.id, approved_only=True)
    comment_config = crud.get_comment_config(db)
    theme = get_current_theme(db, request.cookies.get("theme"))

    # 生成 HTML 内容（如果需要预渲染）
    if not article.html_content and article.markdown_content:
        article.html_content = markdown_to_html(article.markdown_content)

    return templates.TemplateResponse("blog/article.html", {
        "request": request,
        "article": article,
        "comments": comments,
        "comment_config": comment_config,
        "theme": theme
    })


@app.get("/category/{slug}", response_class=HTMLResponse)
async def category_articles(slug: str, request: Request, db: Session = Depends(get_db)):
    """分类文章页"""
    category = crud.get_category_by_slug(db, slug)
    if not category:
        raise HTTPException(status_code=404, detail="分类未找到")

    page = int(request.query_params.get("page", 1))
    per_page = 10
    skip = (page - 1) * per_page

    articles = crud.get_articles(db, skip, per_page, status='published', category_id=category.id)
    total = crud.get_articles_count(db, status='published', category_id=category.id)
    theme = get_current_theme(db, request.cookies.get("theme"))

    return templates.TemplateResponse("blog/category.html", {
        "request": request,
        "category": category,
        "articles": articles,
        "total": total,
        "page": page,
        "per_page": per_page,
        "theme": theme
    })


@app.get("/tag/{slug}", response_class=HTMLResponse)
async def tag_articles(slug: str, request: Request, db: Session = Depends(get_db)):
    """标签文章页"""
    tag = crud.get_tag_by_slug(db, slug)
    if not tag:
        raise HTTPException(status_code=404, detail="标签未找到")

    page = int(request.query_params.get("page", 1))
    per_page = 10
    skip = (page - 1) * per_page

    articles = crud.get_articles(db, skip, per_page, status='published', tag_slug=slug)
    total = crud.get_articles_count(db, status='published', tag_slug=slug)
    theme = get_current_theme(db, request.cookies.get("theme"))

    return templates.TemplateResponse("blog/tag.html", {
        "request": request,
        "tag": tag,
        "articles": articles,
        "total": total,
        "page": page,
        "per_page": per_page,
        "theme": theme
    })


@app.get("/search", response_class=HTMLResponse)
async def search(request: Request, db: Session = Depends(get_db)):
    """搜索结果页"""
    query = request.query_params.get("q", "")
    page = int(request.query_params.get("page", 1))
    per_page = 10
    skip = (page - 1) * per_page

    if query:
        articles = crud.search_articles(db, query, skip, per_page)
        total = len(articles)  # 简化，实际应该查询总数
    else:
        articles = []
        total = 0

    theme = get_current_theme(db, request.cookies.get("theme"))

    return templates.TemplateResponse("blog/search.html", {
        "request": request,
        "query": query,
        "articles": articles,
        "total": total,
        "page": page,
        "per_page": per_page,
        "theme": theme
    })


@app.get("/archives", response_class=HTMLResponse)
async def archives(request: Request, db: Session = Depends(get_db)):
    """归档页"""
    articles = crud.get_published_articles(db, skip=0, limit=100)

    # 按年月分组
    archives = {}
    for article in articles:
        if article.publish_date:
            year = article.publish_date.year
            month = article.publish_date.month
            key = f"{year}-{month:02d}"
            if key not in archives:
                archives[key] = []
            archives[key].append(article)

    theme = get_current_theme(db, request.cookies.get("theme"))

    return templates.TemplateResponse("blog/archives.html", {
        "request": request,
        "archives": archives,
        "theme": theme
    })


# ============ SEO 路由 ============

@app.get("/sitemap.xml", response_class=HTMLResponse)
async def sitemap(request: Request, db: Session = Depends(get_db)):
    """站点地图"""
    articles = crud.get_published_articles(db, skip=0, limit=1000)
    categories = crud.get_categories(db)

    base_url = str(request.base_url).rstrip("/")

    xml_content = """<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
"""
    for article in articles:
        xml_content += f"""  <url>
    <loc>{base_url}/article/{article.slug}</loc>
    <lastmod>{article.updated_at.strftime('%Y-%m-%d')}</lastmod>
    <changefreq>weekly</changefreq>
    <priority>0.8</priority>
  </url>
"""

    for category in categories:
        xml_content += f"""  <url>
    <loc>{base_url}/category/{category.slug}</loc>
    <changefreq>weekly</changefreq>
    <priority>0.6</priority>
  </url>
"""

    xml_content += "</urlset>"

    return HTMLResponse(content=xml_content, media_type="application/xml")


@app.get("/robots.txt", response_class=PlainTextResponse)
async def robots():
    """搜索引擎规则"""
    return "User-agent: *\nAllow: /\n\nSitemap: /sitemap.xml"


# ============ Health Check ============

@app.get("/health")
async def health_check(db: Session = Depends(get_db)):
    """健康检查"""
    try:
        # 检查数据库连接
        db.execute("SELECT 1")
        return {
            "status": "healthy",
            "database": "connected",
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "database": "disconnected",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }


# ============ API 接口 ============

@app.post("/api/theme")
async def switch_theme(theme: str, request: Request, db: Session = Depends(get_db)):
    """切换主题"""
    if theme not in config.AVAILABLE_THEMES:
        raise HTTPException(status_code=400, detail="无效的主题")

    crud.update_theme_setting(db, theme)

    response = JSONResponse({"success": True, "theme": theme})
    response.set_cookie(key="theme", value=theme, max_age=86400 * 30)  # 30天
    return response


@app.post("/api/comments")
async def create_comment(
    article_id: int,
    author_name: str = Form(...),
    content: str = Form(...),
    author_email: Optional[str] = Form(None),
    is_anonymous: bool = Form(False),
    parent_id: Optional[int] = Form(None),
    captcha_token: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    """提交评论"""
    # 检查评论配置
    comment_config = crud.get_comment_config(db)

    if is_anonymous and not comment_config.allow_anonymous_comments:
        raise HTTPException(status_code=403, detail="不允许匿名评论")

    if not is_anonymous and not comment_config.allow_registered_comments:
        raise HTTPException(status_code=403, detail="不允许注册用户评论")

    # 验证 CAPTCHA（如果配置了）
    if config.CAPTCHA_SECRET_KEY:
        if not captcha_token:
            raise HTTPException(status_code=400, detail="请完成人机验证")
        # 实际应该验证 reCAPTCHA token

    # 创建评论
    comment_data = {
        "article_id": article_id,
        "author_name": author_name,
        "content": content,
        "author_email": author_email,
        "is_anonymous": is_anonymous,
        "parent_id": parent_id,
        "captcha_token": captcha_token
    }

    from app.schemas import CommentCreate
    comment = crud.create_comment(db, CommentCreate(**comment_data))

    return {
        "success": True,
        "message": "评论提交成功" if comment.approved else "评论提交成功，等待审核",
        "comment_id": comment.id
    }


# ============ 管理后台路由 ============

@app.get("/admin/login", response_class=HTMLResponse)
async def admin_login_page(request: Request):
    """管理员登录页面"""
    if request.session.get("admin_id"):
        return RedirectResponse(url="/admin/dashboard")

    csrf_token = generate_csrf_token()
    response = templates.TemplateResponse("admin/login.html", {
        "request": request,
        "csrf_token": csrf_token,
        "error": None
    })
    response.set_cookie(key=config.CSRF_COOKIE_NAME, value=csrf_token, httponly=True)
    return response


@app.post("/admin/login")
async def admin_login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    csrf_token: str = Form(...),
    db: Session = Depends(get_db)
):
    """处理管理员登录"""
    client_ip = request.client.host if request.client else "unknown"

    # 验证 CSRF
    cookie_token = request.cookies.get(config.CSRF_COOKIE_NAME)
    if not cookie_token or cookie_token != csrf_token:
        return templates.TemplateResponse("admin/login.html", {
            "request": request,
            "csrf_token": generate_csrf_token(),
            "error": "无效的请求，请重试"
        })

    # 检查账号是否锁定
    if crud.is_account_locked(db, username, config.LOGIN_MAX_ATTEMPTS, config.LOGIN_LOCKOUT_DURATION // 60):
        return templates.TemplateResponse("admin/login.html", {
            "request": request,
            "csrf_token": generate_csrf_token(),
            "error": "登录失败次数过多，请15分钟后再试"
        })

    # 验证账号密码
    admin = crud.get_admin_by_username(db, username)
    if not admin or not crud.verify_password(password, admin.password_hash):
        crud.record_login_attempt(db, username, client_ip, False)
        return templates.TemplateResponse("admin/login.html", {
            "request": request,
            "csrf_token": generate_csrf_token(),
            "error": "用户名或密码错误"
        })

    # 登录成功
    crud.record_login_attempt(db, username, client_ip, True)
    request.session["admin_id"] = admin.id

    response = RedirectResponse(url="/admin/dashboard", status_code=302)
    response.set_cookie(key=config.CSRF_COOKIE_NAME, value=generate_csrf_token())
    return response


@app.get("/admin/logout")
async def admin_logout(request: Request):
    """管理员登出"""
    request.session.clear()
    return RedirectResponse(url="/admin/login")


@app.get("/admin/dashboard", response_class=HTMLResponse)
async def admin_dashboard(request: Request, db: Session = Depends(get_db)):
    """后台首页"""
    admin = require_admin(request, db)

    # 获取统计数据
    articles = crud.get_articles(db, skip=0, limit=100, status=None)
    published_count = len([a for a in articles if a.status == 'published'])
    draft_count = len([a for a in articles if a.status == 'draft'])
    total_comments = crud.get_comments_count(db, article_id=None, approved_only=None)
    pending_comments = crud.get_comments_count(db, article_id=None, approved_only=False)

    recent_articles = crud.get_articles(db, skip=0, limit=5, status=None)
    recent_sync_records = crud.get_recent_sync_records(db, limit=5)

    return templates.TemplateResponse("admin/dashboard.html", {
        "request": request,
        "admin": admin,
        "published_count": published_count,
        "draft_count": draft_count,
        "total_comments": total_comments,
        "pending_comments": pending_comments,
        "recent_articles": recent_articles,
        "recent_sync_records": recent_sync_records
    })


@app.get("/admin/articles", response_class=HTMLResponse)
async def admin_articles(request: Request, db: Session = Depends(get_db)):
    """文章列表管理"""
    admin = require_admin(request, db)

    page = int(request.query_params.get("page", 1))
    per_page = 20
    skip = (page - 1) * per_page

    articles = crud.get_articles(db, skip, per_page, status=None)
    total = crud.get_articles_count(db, status=None)

    return templates.TemplateResponse("admin/articles.html", {
        "request": request,
        "admin": admin,
        "articles": articles,
        "total": total,
        "page": page,
        "per_page": per_page
    })


@app.get("/admin/articles/new", response_class=HTMLResponse)
async def admin_new_article(request: Request, db: Session = Depends(get_db)):
    """新增文章页面"""
    admin = require_admin(request, db)

    categories = crud.get_categories(db)
    tags = crud.get_tags(db)
    csrf_token = generate_csrf_token()

    from app.services.ai_service import AIService
    ai_service = AIService(db)
    ai_available = ai_service.is_available()

    return templates.TemplateResponse("admin/article_form.html", {
        "request": request,
        "admin": admin,
        "article": None,
        "categories": categories,
        "tags": tags,
        "csrf_token": csrf_token,
        "ai_available": ai_available
    })


@app.post("/admin/articles/new")
async def admin_create_article(
    request: Request,
    title: str = Form(...),
    slug: str = Form(...),
    summary: str = Form(""),
    markdown_content: str = Form(""),
    cover_image: str = Form(""),
    status: str = Form("draft"),
    category_id: int = Form(None),
    tags: str = Form(""),
    db: Session = Depends(get_db)
):
    """创建文章"""
    admin = require_admin(request, db)

    from app.schemas import ArticleCreate
    tag_list = [t.strip() for t in tags.split(",") if t.strip()]

    article = crud.create_article(db, ArticleCreate(
        title=title,
        slug=slug,
        summary=summary,
        markdown_content=markdown_content,
        cover_image=cover_image,
        status=status,
        category_id=category_id,
        tags=tag_list
    ))

    # 如果是发布状态，渲染 HTML
    if status == 'published':
        article.html_content = markdown_to_html(markdown_content)
        article.publish_date = datetime.utcnow()
        db.commit()

    return RedirectResponse(url="/admin/articles", status_code=302)


@app.get("/admin/articles/{article_id}/edit", response_class=HTMLResponse)
async def admin_edit_article(article_id: int, request: Request, db: Session = Depends(get_db)):
    """编辑文章页面"""
    admin = require_admin(request, db)

    article = crud.get_article_by_id(db, article_id)
    if not article:
        raise HTTPException(status_code=404, detail="文章未找到")

    categories = crud.get_categories(db)
    all_tags = crud.get_tags(db)
    article_tags = [t.name for t in article.tags]
    csrf_token = generate_csrf_token()

    from app.services.ai_service import AIService
    ai_service = AIService(db)
    ai_available = ai_service.is_available()

    return templates.TemplateResponse("admin/article_form.html", {
        "request": request,
        "admin": admin,
        "article": article,
        "categories": categories,
        "tags": all_tags,
        "article_tags": article_tags,
        "csrf_token": csrf_token,
        "ai_available": ai_available
    })


@app.post("/admin/articles/{article_id}/edit")
async def admin_update_article(
    article_id: int,
    request: Request,
    title: str = Form(...),
    slug: str = Form(...),
    summary: str = Form(""),
    markdown_content: str = Form(""),
    cover_image: str = Form(""),
    status: str = Form("draft"),
    category_id: int = Form(None),
    tags: str = Form(""),
    db: Session = Depends(get_db)
):
    """更新文章"""
    admin = require_admin(request, db)

    from app.schemas import ArticleUpdate
    tag_list = [t.strip() for t in tags.split(",") if t.strip()]

    # 生成 HTML 内容
    html_content = markdown_to_html(markdown_content) if markdown_content else None

    article = crud.update_article(db, article_id, ArticleUpdate(
        title=title,
        slug=slug,
        summary=summary,
        markdown_content=markdown_content,
        html_content=html_content,
        cover_image=cover_image,
        status=status,
        category_id=category_id,
        tags=tag_list
    ))

    if not article:
        raise HTTPException(status_code=404, detail="文章未找到")

    # 如果是发布状态，更新发布时间
    if status == 'published' and not article.publish_date:
        article.publish_date = datetime.utcnow()
        db.commit()

    return RedirectResponse(url="/admin/articles", status_code=302)


@app.get("/admin/articles/{article_id}/delete")
async def admin_delete_article(article_id: int, request: Request, db: Session = Depends(get_db)):
    """删除文章"""
    admin = require_admin(request, db)
    crud.delete_article(db, article_id)
    return RedirectResponse(url="/admin/articles", status_code=302)


@app.post("/admin/articles/{article_id}/publish")
async def admin_publish_article(article_id: int, request: Request, db: Session = Depends(get_db)):
    """发布文章"""
    admin = require_admin(request, db)
    article = crud.publish_article(db, article_id)
    if article:
        article.html_content = markdown_to_html(article.markdown_content) if article.markdown_content else None
        db.commit()
    return RedirectResponse(url="/admin/articles", status_code=302)


# ============ 评论管理 ============

@app.get("/admin/comments", response_class=HTMLResponse)
async def admin_comments(request: Request, db: Session = Depends(get_db)):
    """评论管理页面"""
    admin = require_admin(request, db)

    page = int(request.query_params.get("page", 1))
    per_page = 20
    skip = (page - 1) * per_page

    status_filter = request.query_params.get("status")
    approved_only = None if status_filter == "all" else (status_filter == "approved")

    comments = crud.get_all_comments(db, approved_only, skip, per_page)

    return templates.TemplateResponse("admin/comments.html", {
        "request": request,
        "admin": admin,
        "comments": comments,
        "status_filter": status_filter
    })


@app.post("/admin/comments/{comment_id}/approve")
async def approve_comment(comment_id: int, request: Request, db: Session = Depends(get_db)):
    """审核通过评论"""
    admin = require_admin(request, db)
    crud.approve_comment(db, comment_id)
    return {"success": True}


@app.post("/admin/comments/{comment_id}/delete")
async def delete_comment_api(comment_id: int, request: Request, db: Session = Depends(get_db)):
    """删除评论"""
    admin = require_admin(request, db)
    crud.delete_comment(db, comment_id)
    return {"success": True}


# ============ 图片上传 API ============

UPLOAD_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static", "uploads")
ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png", "gif", "webp"}

def allowed_file(filename: str) -> bool:
    """检查文件扩展名是否允许"""
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

@app.post("/admin/api/upload-image")
async def upload_image(request: Request, image: UploadFile = File(...)):
    """上传图片接口"""
    # 验证管理员权限
    from sqlalchemy.orm import sessionmaker
    engine = create_engine(config.DATABASE_URL, connect_args={"check_same_thread": False})
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    try:
        require_admin(request, db)
    finally:
        db.close()

    # 确保上传目录存在
    os.makedirs(UPLOAD_DIR, exist_ok=True)

    # 验证文件
    if not image.filename or not allowed_file(image.filename):
        return JSONResponse(
            status_code=400,
            content={"success": False, "message": "只支持 jpg、jpeg、png、gif、webp 格式的图片"}
        )

    # 生成唯一文件名
    ext = image.filename.rsplit(".", 1)[1].lower()
    filename = f"{int(time.time())}_{uuid.uuid4().hex[:8]}.{ext}"
    file_path = os.path.join(UPLOAD_DIR, filename)

    # 保存文件
    try:
        contents = await image.read()
        with open(file_path, "wb") as f:
            f.write(contents)
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"success": False, "message": f"文件保存失败: {str(e)}"}
        )

    # 返回可访问的 URL
    file_url = f"/static/uploads/{filename}"
    return {"success": True, "url": file_url}


# ============ 分类管理 ============

@app.get("/admin/categories", response_class=HTMLResponse)
async def admin_categories(request: Request, db: Session = Depends(get_db)):
    """分类管理页面"""
    admin = require_admin(request, db)
    categories = crud.get_categories(db)
    messages = get_flashed_messages(request)
    return templates.TemplateResponse("admin/categories.html", {
        "request": request,
        "admin": admin,
        "categories": categories,
        "messages": messages
    })


@app.get("/admin/categories/new", response_class=HTMLResponse)
async def admin_new_category(request: Request, db: Session = Depends(get_db)):
    """新增分类页面"""
    admin = require_admin(request, db)
    csrf_token = generate_csrf_token()
    messages = get_flashed_messages(request)
    response = templates.TemplateResponse("admin/category_form.html", {
        "request": request,
        "admin": admin,
        "category": None,
        "csrf_token": csrf_token,
        "messages": messages
    })
    response.set_cookie(key=config.CSRF_COOKIE_NAME, value=csrf_token, httponly=True)
    return response


@app.post("/admin/categories/new")
async def admin_create_category(
    request: Request,
    name: str = Form(...),
    slug: str = Form(...),
    description: str = Form(""),
    csrf_token: str = Form(...),
    db: Session = Depends(get_db)
):
    """创建分类"""
    admin = require_admin(request, db)

    # 验证 CSRF
    if not verify_csrf_token(request, csrf_token):
        flash_message(request, "无效的请求，请重试", "error")
        return RedirectResponse(url="/admin/categories/new", status_code=303)

    # 验证 slug 格式
    if not is_valid_slug(slug):
        flash_message(request, "Slug 只能包含字母、数字和连字符", "error")
        return RedirectResponse(url="/admin/categories/new", status_code=303)

    # 检查 slug 唯一性
    if crud.get_category_by_slug(db, slug):
        flash_message(request, "该 Slug 已存在，请使用其他名称", "error")
        return RedirectResponse(url="/admin/categories/new", status_code=303)

    from app.schemas import CategoryCreate
    crud.create_category(db, CategoryCreate(
        name=name, slug=slug, description=description
    ))

    flash_message(request, "分类创建成功", "success")
    return RedirectResponse(url="/admin/categories", status_code=303)


@app.get("/admin/categories/{category_id}/edit", response_class=HTMLResponse)
async def admin_edit_category(category_id: int, request: Request, db: Session = Depends(get_db)):
    """编辑分类页面"""
    admin = require_admin(request, db)
    category = crud.get_category_by_id(db, category_id)
    if not category:
        raise HTTPException(status_code=404, detail="分类未找到")
    csrf_token = generate_csrf_token()
    messages = get_flashed_messages(request)
    response = templates.TemplateResponse("admin/category_form.html", {
        "request": request,
        "admin": admin,
        "category": category,
        "csrf_token": csrf_token,
        "messages": messages
    })
    response.set_cookie(key=config.CSRF_COOKIE_NAME, value=csrf_token, httponly=True)
    return response


@app.post("/admin/categories/{category_id}/edit")
async def admin_update_category(
    category_id: int,
    request: Request,
    name: str = Form(...),
    slug: str = Form(...),
    description: str = Form(""),
    csrf_token: str = Form(...),
    db: Session = Depends(get_db)
):
    """更新分类"""
    admin = require_admin(request, db)

    # 验证 CSRF
    if not verify_csrf_token(request, csrf_token):
        flash_message(request, "无效的请求，请重试", "error")
        return RedirectResponse(url=f"/admin/categories/{category_id}/edit", status_code=303)

    # 验证 slug 格式
    if not is_valid_slug(slug):
        flash_message(request, "Slug 只能包含字母、数字和连字符", "error")
        return RedirectResponse(url=f"/admin/categories/{category_id}/edit", status_code=303)

    # 检查 slug 唯一性（排除当前分类）
    existing_category = crud.get_category_by_slug(db, slug)
    if existing_category and existing_category.id != category_id:
        flash_message(request, "该 Slug 已存在，请使用其他名称", "error")
        return RedirectResponse(url=f"/admin/categories/{category_id}/edit", status_code=303)

    from app.schemas import CategoryUpdate
    category = crud.update_category(db, category_id, CategoryUpdate(
        name=name, slug=slug, description=description
    ))
    if not category:
        flash_message(request, "分类未找到", "error")
        return RedirectResponse(url="/admin/categories", status_code=303)

    flash_message(request, "分类更新成功", "success")
    return RedirectResponse(url="/admin/categories", status_code=303)


@app.get("/admin/categories/{category_id}/delete")
async def admin_delete_category(category_id: int, request: Request, db: Session = Depends(get_db)):
    """删除分类"""
    admin = require_admin(request, db)
    success = crud.delete_category(db, category_id)
    if success:
        flash_message(request, "分类删除成功", "success")
    else:
        flash_message(request, "分类删除失败", "error")
    return RedirectResponse(url="/admin/categories", status_code=303)


# ============ 设置页面 ============

@app.get("/admin/settings", response_class=HTMLResponse)
async def admin_settings(request: Request, db: Session = Depends(get_db)):
    """系统设置页面"""
    admin = require_admin(request, db)

    theme_setting = crud.get_theme_setting(db)
    comment_config = crud.get_comment_config(db)

    return templates.TemplateResponse("admin/settings.html", {
        "request": request,
        "admin": admin,
        "theme_setting": theme_setting,
        "comment_config": comment_config
    })


@app.post("/admin/settings/theme")
async def update_theme_setting_api(
    request: Request,
    theme: str = Form(...),
    db: Session = Depends(get_db)
):
    """更新主题设置"""
    admin = require_admin(request, db)

    print(f"[DEBUG] 收到主题切换请求: theme={theme}, 可用主题={config.AVAILABLE_THEMES}")

    if theme not in config.AVAILABLE_THEMES:
        raise HTTPException(status_code=400, detail=f"无效的主题: {theme}")

    try:
        crud.update_theme_setting(db, theme)
        print(f"[DEBUG] 主题已更新到数据库: {theme}")
        return {"success": True, "theme": theme}
    except Exception as e:
        print(f"[ERROR] 主题更新失败: {e}")
        raise HTTPException(status_code=500, detail=f"保存失败: {str(e)}")


@app.post("/admin/settings/comment")
async def update_comment_config_api(
    allow_registered: bool = Form(...),
    allow_anonymous: bool = Form(...),
    require_approval: bool = Form(...),
    request: Request = None,
    db: Session = Depends(get_db)
):
    """更新评论配置"""
    admin = require_admin(request, db)

    from app.schemas import CommentConfigUpdate
    crud.update_comment_config(db, CommentConfigUpdate(
        allow_registered_comments=allow_registered,
        allow_anonymous_comments=allow_anonymous,
        require_approval=require_approval
    ))

    return {"success": True}


# ============ 同步管理 ============

@app.get("/admin/sync", response_class=HTMLResponse)
async def admin_sync(request: Request, db: Session = Depends(get_db)):
    """同步管理页面"""
    admin = require_admin(request, db)

    accounts = crud.get_sync_accounts(db)
    recent_records = crud.get_recent_sync_records(db, limit=50)

    return templates.TemplateResponse("admin/sync.html", {
        "request": request,
        "admin": admin,
        "accounts": accounts,
        "records": recent_records,
        "platforms": config.SYNC_PLATFORMS
    })


@app.post("/admin/sync/account")
async def create_sync_account_api(
    platform_type: str = Form(...),
    account_name: str = Form(...),
    credential: str = Form(""),
    request: Request = None,
    db: Session = Depends(get_db)
):
    """创建同步账号"""
    admin = require_admin(request, db)

    from app.schemas import SyncAccountCreate
    account = crud.create_sync_account(db, SyncAccountCreate(
        platform_type=platform_type,
        account_name=account_name,
        credential=credential
    ))

    return {"success": True, "account_id": account.id}


@app.post("/api/sync")
async def trigger_sync(
    article_id: int,
    platform_type: str,
    request: Request,
    db: Session = Depends(get_db)
):
    """手动同步触发"""
    admin = require_admin(request, db)

    article = crud.get_article_by_id(db, article_id)
    if not article:
        raise HTTPException(status_code=404, detail="文章未找到")

    accounts = crud.get_sync_accounts(db, platform_type=platform_type, active_only=True)
    if not accounts:
        raise HTTPException(status_code=400, detail="未找到可用的同步账号")

    # 调用同步服务
    from app.services.sync import sync_article_to_platform
    result = sync_article_to_platform(db, article, platform_type)

    return result


# ============ AI 设置管理 ============

@app.get("/admin/ai/config", response_class=HTMLResponse)
async def admin_ai_config(request: Request, db: Session = Depends(get_db)):
    """AI 配置页面"""
    admin = require_admin(request, db)

    ai_config = crud.get_or_create_default_ai_config(db)
    templates_list = crud.get_prompt_templates(db, active_only=False)
    messages = get_flashed_messages(request)

    return templates.TemplateResponse("admin/ai_config.html", {
        "request": request,
        "admin": admin,
        "ai_config": ai_config,
        "templates": templates_list,
        "messages": messages
    })


@app.post("/admin/ai/config")
async def update_ai_config(
    request: Request,
    provider: str = Form(...),
    api_key: str = Form(""),
    api_base: str = Form(""),
    model: str = Form(...),
    temperature: int = Form(70),
    max_tokens: int = Form(1000),
    timeout: int = Form(60),
    is_enabled: bool = Form(False),
    db: Session = Depends(get_db)
):
    """更新 AI 配置"""
    admin = require_admin(request, db)

    config_data = {
        'provider': provider,
        'api_key': api_key,
        'api_base': api_base,
        'model': model,
        'temperature': temperature,
        'max_tokens': max_tokens,
        'timeout': timeout,
        'is_enabled': is_enabled
    }

    crud.update_ai_config(db, config_data)
    flash_message(request, "AI 配置已更新", "success")
    return RedirectResponse(url="/admin/ai/config", status_code=303)


@app.post("/admin/ai/config/test")
async def test_ai_config(request: Request, db: Session = Depends(get_db)):
    """测试 AI 连接"""
    admin = require_admin(request, db)

    from app.services.ai_service import AIService
    ai_service = AIService(db)
    success, message = ai_service.test_connection()

    return {"success": success, "message": message}


@app.get("/admin/ai/prompts", response_class=HTMLResponse)
async def admin_ai_prompts(request: Request, db: Session = Depends(get_db)):
    """提示词模板管理页面"""
    admin = require_admin(request, db)

    templates_list = crud.get_prompt_templates(db, active_only=False)
    messages = get_flashed_messages(request)

    return templates.TemplateResponse("admin/ai_prompts.html", {
        "request": request,
        "admin": admin,
        "templates": templates_list,
        "messages": messages
    })


@app.post("/admin/ai/prompts")
async def create_or_update_prompt_template(
    request: Request,
    template_id: int = Form(None),
    name: str = Form(...),
    scene: str = Form(...),
    prompt: str = Form(...),
    description: str = Form(""),
    sort_order: int = Form(0),
    is_active: bool = Form(True),
    db: Session = Depends(get_db)
):
    """创建或更新提示词模板"""
    admin = require_admin(request, db)

    template_data = {
        'name': name,
        'scene': scene,
        'prompt': prompt,
        'description': description,
        'sort_order': sort_order,
        'is_active': is_active
    }

    if template_id:
        # 检查是否为系统模板
        from app.models import AIPromptTemplate
        template = db.query(AIPromptTemplate).filter(AIPromptTemplate.id == template_id).first()
        if template and template.is_system:
            flash_message(request, "无法编辑系统模板", "error")
        else:
            crud.update_prompt_template(db, template_id, template_data)
            flash_message(request, "模板已更新", "success")
    else:
        crud.create_prompt_template(db, template_data)
        flash_message(request, "模板已创建", "success")

    return RedirectResponse(url="/admin/ai/prompts", status_code=303)


@app.get("/admin/ai/prompts/{template_id}/delete")
async def delete_prompt_template(template_id: int, request: Request, db: Session = Depends(get_db)):
    """删除提示词模板"""
    admin = require_admin(request, db)

    success = crud.delete_prompt_template(db, template_id)
    if success:
        flash_message(request, "模板已删除", "success")
    else:
        flash_message(request, "无法删除系统模板", "error")

    return RedirectResponse(url="/admin/ai/prompts", status_code=303)


# ============ AI 生成 API ============

@app.post("/admin/api/ai/generate")
async def ai_generate(
    request: Request,
    db: Session = Depends(get_db)
):
    """AI 生成内容 API"""
    admin = require_admin(request, db)

    try:
        data = await request.json()
        scene = data.get('scene')
        variables = data.get('variables', {})

        if not scene:
            return JSONResponse(
                status_code=400,
                content={"success": False, "message": "场景不能为空"}
            )

        from app.services.ai_service import AIService
        ai_service = AIService(db)

        if not ai_service.is_available():
            return JSONResponse(
                status_code=400,
                content={"success": False, "message": "AI 服务未启用或配置不完整"}
            )

        result = ai_service.generate(scene, **variables)
        return {"success": True, "result": result}

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"success": False, "message": str(e)}
        )


# ============ 启动事件 ============

@app.on_event("startup")
async def startup_event():
    """应用启动时的初始化"""
    # 创建数据库表
    Base.metadata.create_all(bind=engine)

    # 初始化数据库
    db = SessionLocal()
    try:
        crud.init_database(db)
    finally:
        db.close()


from fastapi.responses import PlainTextResponse


# ============ 错误处理 ============

@app.exception_handler(404)
async def not_found(request: Request, exc):
    """404 错误页面"""
    return templates.TemplateResponse("error/404.html", {
        "request": request,
        "error": "页面未找到"
    })


@app.exception_handler(500)
async def server_error(request: Request, exc):
    """500 错误页面"""
    return templates.TemplateResponse("error/500.html", {
        "request": request,
        "error": "服务器内部错误"
    })


# 导入错误响应类
from fastapi.responses import PlainTextResponse