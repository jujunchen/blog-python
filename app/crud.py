# 数据访问与操作逻辑
# CRUD Operations

from typing import List, Optional
from datetime import datetime

from sqlalchemy import or_, and_
from sqlalchemy.orm import Session

from app.models import (
    Article, Category, Tag, Comment, CommentConfig,
    AdminUser, ThemeSetting, SyncAccount, SyncRecord, LoginAttempt
)
from app.schemas import (
    ArticleCreate, ArticleUpdate, CategoryCreate, CategoryUpdate,
    TagCreate, CommentCreate, CommentUpdate, AdminUserCreate,
    SyncAccountCreate, CommentConfigUpdate
)


# ============ Article CRUD ============

def get_article_by_id(db: Session, article_id: int) -> Optional[Article]:
    """根据 ID 获取文章"""
    return db.query(Article).filter(Article.id == article_id).first()


def get_article_by_slug(db: Session, slug: str) -> Optional[Article]:
    """根据 slug 获取文章"""
    return db.query(Article).filter(Article.slug == slug).first()


def get_articles(
    db: Session,
    skip: int = 0,
    limit: int = 10,
    status: str = 'published',
    category_id: Optional[int] = None,
    tag_slug: Optional[str] = None
) -> List[Article]:
    """获取文章列表"""
    query = db.query(Article)

    if status:
        query = query.filter(Article.status == status)
    if category_id:
        query = query.filter(Article.category_id == category_id)
    if tag_slug:
        tag = db.query(Tag).filter(Tag.slug == tag_slug).first()
        if tag:
            query = query.filter(Article.tags.contains(tag))

    return query.order_by(Article.publish_date.desc()).offset(skip).limit(limit).all()


def get_published_articles(db: Session, skip: int = 0, limit: int = 10) -> List[Article]:
    """获取已发布的文章列表"""
    return get_articles(db, skip, limit, status='published')


def get_articles_count(
    db: Session,
    status: Optional[str] = 'published',
    category_id: Optional[int] = None,
    tag_slug: Optional[str] = None
) -> int:
    """获取文章总数"""
    query = db.query(Article)
    if status:
        query = query.filter(Article.status == status)
    if category_id:
        query = query.filter(Article.category_id == category_id)
    if tag_slug:
        tag = db.query(Tag).filter(Tag.slug == tag_slug).first()
        if tag:
            query = query.filter(Article.tags.contains(tag))
    return query.count()


def create_article(db: Session, article: ArticleCreate) -> Article:
    """创建文章"""
    # 处理 slug
    slug = article.slug or generate_slug(db, article.title)

    db_article = Article(
        title=article.title,
        slug=slug,
        summary=article.summary,
        markdown_content=article.markdown_content,
        cover_image=article.cover_image,
        status=article.status,
        category_id=article.category_id
    )

    # 处理标签
    if article.tags:
        for tag_name in article.tags:
            tag = get_or_create_tag(db, tag_name)
            db_article.tags.append(tag)

    db.add(db_article)
    db.commit()
    db.refresh(db_article)
    return db_article


def update_article(db: Session, article_id: int, article: ArticleUpdate) -> Optional[Article]:
    """更新文章"""
    db_article = get_article_by_id(db, article_id)
    if not db_article:
        return None

    update_data = article.model_dump(exclude_unset=True)

    # 处理标签
    if 'tags' in update_data:
        tags = update_data.pop('tags')
        db_article.tags = []
        for tag_name in tags:
            tag = get_or_create_tag(db, tag_name)
            db_article.tags.append(tag)

    for key, value in update_data.items():
        setattr(db_article, key, value)

    db_article.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(db_article)
    return db_article


def delete_article(db: Session, article_id: int) -> bool:
    """删除文章"""
    db_article = get_article_by_id(db, article_id)
    if not db_article:
        return False

    db.delete(db_article)
    db.commit()
    return True


def publish_article(db: Session, article_id: int) -> Optional[Article]:
    """发布文章"""
    db_article = get_article_by_id(db, article_id)
    if not db_article:
        return None

    db_article.status = 'published'
    db_article.publish_date = datetime.utcnow()
    db_article.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(db_article)
    return db_article


def search_articles(db: Session, query: str, skip: int = 0, limit: int = 10) -> List[Article]:
    """搜索文章"""
    search_pattern = f"%{query}%"
    return db.query(Article).filter(
        and_(
            Article.status == 'published',
            or_(
                Article.title.ilike(search_pattern),
                Article.summary.ilike(search_pattern),
                Article.markdown_content.ilike(search_pattern)
            )
        )
    ).order_by(Article.publish_date.desc()).offset(skip).limit(limit).all()


def get_articles_by_archive(db: Session, year: int, month: Optional[int] = None) -> List[Article]:
    """按归档获取文章"""
    query = db.query(Article).filter(
        Article.status == 'published',
        Article.publish_date.isnot(None)
    )

    from sqlalchemy import extract
    query = query.filter(extract('year', Article.publish_date) == year)

    if month:
        query = query.filter(extract('month', Article.publish_date) == month)

    return query.order_by(Article.publish_date.desc()).all()


def generate_slug(db: Session, title: str) -> str:
    """生成唯一的 slug"""
    base_slug = title.lower().replace(' ', '-')
    slug = base_slug
    counter = 1

    while get_article_by_slug(db, slug):
        slug = f"{base_slug}-{counter}"
        counter += 1

    return slug


# ============ Category CRUD ============

def get_category_by_id(db: Session, category_id: int) -> Optional[Category]:
    """根据 ID 获取分类"""
    return db.query(Category).filter(Category.id == category_id).first()


def get_category_by_slug(db: Session, slug: str) -> Optional[Category]:
    """根据 slug 获取分类"""
    return db.query(Category).filter(Category.slug == slug).first()


def get_categories(db: Session) -> List[Category]:
    """获取所有分类"""
    return db.query(Category).order_by(Category.name).all()


def create_category(db: Session, category: CategoryCreate) -> Category:
    """创建分类"""
    db_category = Category(
        name=category.name,
        slug=category.slug,
        description=category.description
    )
    db.add(db_category)
    db.commit()
    db.refresh(db_category)
    return db_category


def update_category(db: Session, category_id: int, category: CategoryUpdate) -> Optional[Category]:
    """更新分类"""
    db_category = get_category_by_id(db, category_id)
    if not db_category:
        return None

    for key, value in category.model_dump(exclude_unset=True).items():
        setattr(db_category, key, value)

    db.commit()
    db.refresh(db_category)
    return db_category


def delete_category(db: Session, category_id: int) -> bool:
    """删除分类"""
    db_category = get_category_by_id(db, category_id)
    if not db_category:
        return False

    db.delete(db_category)
    db.commit()
    return True


# ============ Tag CRUD ============

def get_tag_by_id(db: Session, tag_id: int) -> Optional[Tag]:
    """根据 ID 获取标签"""
    return db.query(Tag).filter(Tag.id == tag_id).first()


def get_tag_by_slug(db: Session, slug: str) -> Optional[Tag]:
    """根据 slug 获取标签"""
    return db.query(Tag).filter(Tag.slug == slug).first()


def get_tags(db: Session) -> List[Tag]:
    """获取所有标签"""
    return db.query(Tag).order_by(Tag.name).all()


def get_or_create_tag(db: Session, tag_name: str) -> Tag:
    """获取或创建标签"""
    slug = tag_name.lower().replace(' ', '-')
    tag = get_tag_by_slug(db, slug)

    if not tag:
        tag = Tag(name=tag_name, slug=slug)
        db.add(tag)
        db.commit()
        db.refresh(tag)

    return tag


def create_tag(db: Session, tag: TagCreate) -> Tag:
    """创建标签"""
    db_tag = Tag(
        name=tag.name,
        slug=tag.slug,
        description=tag.description
    )
    db.add(db_tag)
    db.commit()
    db.refresh(db_tag)
    return db_tag


def delete_tag(db: Session, tag_id: int) -> bool:
    """删除标签"""
    db_tag = get_tag_by_id(db, tag_id)
    if not db_tag:
        return False

    db.delete(db_tag)
    db.commit()
    return True


# ============ Comment CRUD ============

def get_comment_by_id(db: Session, comment_id: int) -> Optional[Comment]:
    """根据 ID 获取评论"""
    return db.query(Comment).filter(Comment.id == comment_id).first()


def get_comments_by_article(
    db: Session,
    article_id: int,
    approved_only: bool = True,
    skip: int = 0,
    limit: int = 50
) -> List[Comment]:
    """获取文章的评论"""
    query = db.query(Comment).filter(Comment.article_id == article_id)

    if approved_only:
        query = query.filter(Comment.approved == True)

    return query.order_by(Comment.created_at.asc()).offset(skip).limit(limit).all()


def get_all_comments(
    db: Session,
    approved_only: Optional[bool] = None,
    skip: int = 0,
    limit: int = 50
) -> List[Comment]:
    """获取所有评论"""
    query = db.query(Comment)

    if approved_only is not None:
        query = query.filter(Comment.approved == approved_only)

    return query.order_by(Comment.created_at.desc()).offset(skip).limit(limit).all()


def get_comments_count(db: Session, article_id: Optional[int] = None, approved_only: bool = True) -> int:
    """获取评论总数"""
    query = db.query(Comment)

    if article_id:
        query = query.filter(Comment.article_id == article_id)
    if approved_only:
        query = query.filter(Comment.approved == True)

    return query.count()


def create_comment(db: Session, comment: CommentCreate) -> Comment:
    """创建评论"""
    db_comment = Comment(
        article_id=comment.article_id,
        author_name=comment.author_name,
        author_email=comment.author_email,
        content=comment.content,
        is_anonymous=comment.is_anonymous,
        parent_id=comment.parent_id,
        approved=not _is_approval_required(db)
    )
    db.add(db_comment)
    db.commit()
    db.refresh(db_comment)
    return db_comment


def update_comment(db: Session, comment_id: int, comment: CommentUpdate) -> Optional[Comment]:
    """更新评论"""
    db_comment = get_comment_by_id(db, comment_id)
    if not db_comment:
        return None

    update_data = comment.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_comment, key, value)

    db.commit()
    db.refresh(db_comment)
    return db_comment


def approve_comment(db: Session, comment_id: int) -> Optional[Comment]:
    """审核通过评论"""
    return update_comment(db, comment_id, CommentUpdate(approved=True))


def delete_comment(db: Session, comment_id: int) -> bool:
    """删除评论"""
    db_comment = get_comment_by_id(db, comment_id)
    if not db_comment:
        return False

    db.delete(db_comment)
    db.commit()
    return True


def _is_approval_required(db: Session) -> bool:
    """检查是否需要审核评论"""
    config = db.query(CommentConfig).first()
    return config.require_approval if config else True


# ============ CommentConfig CRUD ============

def get_comment_config(db: Session) -> CommentConfig:
    """获取评论配置"""
    config = db.query(CommentConfig).first()
    if not config:
        config = CommentConfig()
        db.add(config)
        db.commit()
        db.refresh(config)
    return config


def update_comment_config(db: Session, config: CommentConfigUpdate) -> CommentConfig:
    """更新评论配置"""
    db_config = get_comment_config(db)

    update_data = config.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_config, key, value)

    db_config.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(db_config)
    return db_config


# ============ AdminUser CRUD ============

def get_admin_by_username(db: Session, username: str) -> Optional[AdminUser]:
    """根据用户名获取管理员"""
    return db.query(AdminUser).filter(AdminUser.username == username).first()


def get_admin_by_id(db: Session, admin_id: int) -> Optional[AdminUser]:
    """根据 ID 获取管理员"""
    return db.query(AdminUser).filter(AdminUser.id == admin_id).first()


def create_admin(db: Session, admin: AdminUserCreate, password_hash: str) -> AdminUser:
    """创建管理员"""
    db_admin = AdminUser(
        username=admin.username,
        password_hash=password_hash,
        email=admin.email
    )
    db.add(db_admin)
    db.commit()
    db.refresh(db_admin)
    return db_admin


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证密码"""
    import hashlib
    return hashlib.sha256(plain_password.encode()).hexdigest() == hashed_password


def hash_password(password: str) -> str:
    """密码哈希"""
    import hashlib
    return hashlib.sha256(password.encode()).hexdigest()


# ============ LoginAttempt CRUD ============

def record_login_attempt(db: Session, username: str, ip_address: str, success: bool) -> LoginAttempt:
    """记录登录尝试"""
    attempt = LoginAttempt(
        username=username,
        ip_address=ip_address,
        success=success
    )
    db.add(attempt)
    db.commit()
    db.refresh(attempt)
    return attempt


def get_recent_failed_attempts(db: Session, username: str, minutes: int = 15) -> int:
    """获取最近的失败尝试次数"""
    from datetime import timedelta
    cutoff = datetime.utcnow() - timedelta(minutes=minutes)

    return db.query(LoginAttempt).filter(
        and_(
            LoginAttempt.username == username,
            LoginAttempt.success == False,
            LoginAttempt.attempted_at >= cutoff
        )
    ).count()


def is_account_locked(db: Session, username: str, max_attempts: int = 5, lockout_minutes: int = 15) -> bool:
    """检查账号是否被锁定"""
    return get_recent_failed_attempts(db, username, lockout_minutes) >= max_attempts


# ============ ThemeSetting CRUD ============

def get_theme_setting(db: Session) -> ThemeSetting:
    """获取主题设置"""
    setting = db.query(ThemeSetting).first()
    if not setting:
        setting = ThemeSetting(current_theme='light')
        db.add(setting)
        db.commit()
        db.refresh(setting)
    return setting


def update_theme_setting(db: Session, theme: str) -> ThemeSetting:
    """更新主题设置"""
    setting = get_theme_setting(db)
    setting.current_theme = theme
    setting.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(setting)
    return setting


# ============ SyncAccount CRUD ============

def get_sync_accounts(db: Session, platform_type: Optional[str] = None, active_only: bool = False) -> List[SyncAccount]:
    """获取同步账号"""
    query = db.query(SyncAccount)

    if platform_type:
        query = query.filter(SyncAccount.platform_type == platform_type)
    if active_only:
        query = query.filter(SyncAccount.is_active == True)

    return query.order_by(SyncAccount.created_at.desc()).all()


def get_sync_account_by_id(db: Session, account_id: int) -> Optional[SyncAccount]:
    """根据 ID 获取同步账号"""
    return db.query(SyncAccount).filter(SyncAccount.id == account_id).first()


def create_sync_account(db: Session, account: SyncAccountCreate) -> SyncAccount:
    """创建同步账号"""
    db_account = SyncAccount(
        platform_type=account.platform_type,
        account_name=account.account_name,
        config_data=account.config_data,
        credential=account.credential
    )
    db.add(db_account)
    db.commit()
    db.refresh(db_account)
    return db_account


def update_sync_account(db: Session, account_id: int, account: SyncAccountCreate) -> Optional[SyncAccount]:
    """更新同步账号"""
    db_account = get_sync_account_by_id(db, account_id)
    if not db_account:
        return None

    for key, value in account.model_dump(exclude_unset=True).items():
        setattr(db_account, key, value)

    db_account.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(db_account)
    return db_account


def delete_sync_account(db: Session, account_id: int) -> bool:
    """删除同步账号"""
    db_account = get_sync_account_by_id(db, account_id)
    if not db_account:
        return False

    db.delete(db_account)
    db.commit()
    return True


# ============ SyncRecord CRUD ============

def create_sync_record(
    db: Session,
    article_id: int,
    sync_account_id: int,
    platform_type: str,
    status: str = 'pending',
    result_message: str = None
) -> SyncRecord:
    """创建同步记录"""
    record = SyncRecord(
        article_id=article_id,
        sync_account_id=sync_account_id,
        platform_type=platform_type,
        status=status,
        result_message=result_message
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


def update_sync_record(
    db: Session,
    record_id: int,
    status: str,
    result_message: str = None
) -> Optional[SyncRecord]:
    """更新同步记录"""
    record = db.query(SyncRecord).filter(SyncRecord.id == record_id).first()
    if not record:
        return None

    record.status = status
    record.result_message = result_message
    db.commit()
    db.refresh(record)
    return record


def get_sync_records_by_article(db: Session, article_id: int) -> List[SyncRecord]:
    """获取文章的所有同步记录"""
    return db.query(SyncRecord).filter(
        SyncRecord.article_id == article_id
    ).order_by(SyncRecord.synced_at.desc()).all()


def get_recent_sync_records(db: Session, limit: int = 20) -> List[SyncRecord]:
    """获取最近的同步记录"""
    return db.query(SyncRecord).order_by(
        SyncRecord.synced_at.desc()
    ).limit(limit).all()


# ============ Database Initialization ============

def init_database(db: Session):
    """初始化数据库，创建默认数据"""
    # 创建默认管理员
    admin = get_admin_by_username(db, 'admin')
    if not admin:
        admin = AdminUser(
            username='admin',
            password_hash=hash_password('admin123'),
            email='admin@example.com'
        )
        db.add(admin)

    # 创建默认主题设置
    theme = db.query(ThemeSetting).first()
    if not theme:
        theme = ThemeSetting(current_theme='light')
        db.add(theme)

    # 创建默认评论配置
    config = db.query(CommentConfig).first()
    if not config:
        config = CommentConfig(
            allow_registered_comments=True,
            allow_anonymous_comments=True,
            require_approval=True
        )
        db.add(config)

    db.commit()