# 单元测试
# Unit Tests

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.models import Base
from app import crud


# 测试数据库设置
TEST_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture
def db():
    """创建测试数据库会话"""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture
def init_default_data(db):
    """初始化默认数据"""
    crud.init_database(db)
    return db


# ============ Article 测试 ============

def test_create_article(db, init_default_data):
    """测试创建文章"""
    from app.schemas import ArticleCreate

    article_data = ArticleCreate(
        title="测试文章",
        slug="test-article",
        summary="这是一个测试摘要",
        markdown_content="# 测试\n\n这是测试内容",
        status="draft",
        tags=["测试", "Python"]
    )

    article = crud.create_article(db, article_data)

    assert article.id is not None
    assert article.title == "测试文章"
    assert article.slug == "test-article"
    assert article.status == "draft"
    assert len(article.tags) == 2


def test_get_article_by_id(db, init_default_data):
    """测试根据 ID 获取文章"""
    from app.schemas import ArticleCreate

    article_data = ArticleCreate(
        title="测试文章",
        slug="test-article",
        status="draft"
    )
    article = crud.create_article(db, article_data)

    fetched = crud.get_article_by_id(db, article.id)
    assert fetched is not None
    assert fetched.id == article.id
    assert fetched.title == "测试文章"


def test_get_article_by_slug(db, init_default_data):
    """测试根据 slug 获取文章"""
    from app.schemas import ArticleCreate

    article_data = ArticleCreate(
        title="测试文章",
        slug="test-article-slug",
        status="draft"
    )
    crud.create_article(db, article_data)

    fetched = crud.get_article_by_slug(db, "test-article-slug")
    assert fetched is not None
    assert fetched.slug == "test-article-slug"


def test_get_articles(db, init_default_data):
    """测试获取文章列表"""
    from app.schemas import ArticleCreate

    # 创建多篇文章
    for i in range(5):
        article_data = ArticleCreate(
            title=f"测试文章 {i}",
            slug=f"test-article-{i}",
            status="published"
        )
        crud.create_article(db, article_data)

    articles = crud.get_articles(db, skip=0, limit=10, status="published")
    assert len(articles) == 5


def test_update_article(db, init_default_data):
    """测试更新文章"""
    from app.schemas import ArticleCreate, ArticleUpdate

    article_data = ArticleCreate(
        title="原始标题",
        slug="original-slug",
        status="draft"
    )
    article = crud.create_article(db, article_data)

    update_data = ArticleUpdate(title="新标题", status="published")
    updated = crud.update_article(db, article.id, update_data)

    assert updated is not None
    assert updated.title == "新标题"
    assert updated.status == "published"


def test_delete_article(db, init_default_data):
    """测试删除文章"""
    from app.schemas import ArticleCreate

    article_data = ArticleCreate(
        title="待删除文章",
        slug="delete-me",
        status="draft"
    )
    article = crud.create_article(db, article_data)

    result = crud.delete_article(db, article.id)
    assert result is True

    # 验证已删除
    fetched = crud.get_article_by_id(db, article.id)
    assert fetched is None


def test_publish_article(db, init_default_data):
    """测试发布文章"""
    from app.schemas import ArticleCreate

    article_data = ArticleCreate(
        title="发布测试",
        slug="publish-test",
        status="draft"
    )
    article = crud.create_article(db, article_data)

    published = crud.publish_article(db, article.id)

    assert published is not None
    assert published.status == "published"
    assert published.publish_date is not None


def test_search_articles(db, init_default_data):
    """测试搜索文章"""
    from app.schemas import ArticleCreate

    article_data = ArticleCreate(
        title="Python 教程",
        slug="python-tutorial",
        summary="学习 Python 编程",
        status="published"
    )
    crud.create_article(db, article_data)

    results = crud.search_articles(db, "Python")
    assert len(results) >= 1


# ============ Category 测试 ============

def test_create_category(db, init_default_data):
    """测试创建分类"""
    from app.schemas import CategoryCreate

    category_data = CategoryCreate(
        name="Python",
        slug="python",
        description="Python 相关文章"
    )

    category = crud.create_category(db, category_data)

    assert category.id is not None
    assert category.name == "Python"
    assert category.slug == "python"


def test_get_categories(db, init_default_data):
    """测试获取所有分类"""
    from app.schemas import CategoryCreate

    crud.create_category(db, CategoryCreate(name="分类1", slug="cat1"))
    crud.create_category(db, CategoryCreate(name="分类2", slug="cat2"))

    categories = crud.get_categories(db)
    assert len(categories) == 2


# ============ Tag 测试 ============

def test_get_or_create_tag(db, init_default_data):
    """测试获取或创建标签"""
    tag = crud.get_or_create_tag(db, "Python")

    assert tag.id is not None
    assert tag.name == "Python"
    assert tag.slug == "python"

    # 再次获取应该返回相同标签
    tag2 = crud.get_or_create_tag(db, "Python")
    assert tag2.id == tag.id


# ============ Comment 测试 ============

def test_create_comment(db, init_default_data):
    """测试创建评论"""
    from app.schemas import ArticleCreate, CommentCreate

    # 创建文章
    article_data = ArticleCreate(
        title="评论测试",
        slug="comment-test",
        status="published"
    )
    article = crud.create_article(db, article_data)

    # 创建评论
    comment_data = CommentCreate(
        article_id=article.id,
        author_name="测试用户",
        author_email="test@example.com",
        content="这是测试评论",
        is_anonymous=False
    )
    comment = crud.create_comment(db, comment_data)

    assert comment.id is not None
    assert comment.author_name == "测试用户"
    assert comment.content == "这是测试评论"


def test_get_comments_by_article(db, init_default_data):
    """测试获取文章评论"""
    from app.schemas import ArticleCreate, CommentCreate

    article_data = ArticleCreate(
        title="评论列表测试",
        slug="comments-list-test",
        status="published"
    )
    article = crud.create_article(db, article_data)

    # 创建多条评论
    for i in range(3):
        comment_data = CommentCreate(
            article_id=article.id,
            author_name=f"用户{i}",
            content=f"评论 {i}",
            is_anonymous=False
        )
        crud.create_comment(db, comment_data)

    comments = crud.get_comments_by_article(db, article.id, approved_only=False)
    assert len(comments) == 3


def test_approve_comment(db, init_default_data):
    """测试审核评论"""
    from app.schemas import ArticleCreate, CommentCreate

    article_data = ArticleCreate(
        title="审核评论测试",
        slug="approve-comment-test",
        status="published"
    )
    article = crud.create_article(db, article_data)

    comment_data = CommentCreate(
        article_id=article.id,
        author_name="测试用户",
        content="待审核评论",
        is_anonymous=False
    )
    comment = crud.create_comment(db, comment_data)

    # 初始状态应该根据配置决定
    # 审核通过
    approved = crud.approve_comment(db, comment.id)
    assert approved.approved is True


# ============ AdminUser 测试 ============

def test_create_admin(db, init_default_data):
    """测试创建管理员"""
    from app.schemas import AdminUserCreate

    admin_data = AdminUserCreate(
        username="newadmin",
        password="password123",
        email="newadmin@example.com"
    )

    password_hash = crud.hash_password(admin_data.password)
    admin = crud.create_admin(db, admin_data, password_hash)

    assert admin.id is not None
    assert admin.username == "newadmin"


def test_verify_password(db, init_default_data):
    """测试密码验证"""
    password = "testpassword"
    password_hash = crud.hash_password(password)

    assert crud.verify_password(password, password_hash) is True
    assert crud.verify_password("wrongpassword", password_hash) is False


def test_login_attempt_lockout(db, init_default_data):
    """测试登录失败锁定"""
    username = "testuser"

    # 记录多次失败尝试
    for _ in range(5):
        crud.record_login_attempt(db, username, "127.0.0.1", False)

    # 应该被锁定
    assert crud.is_account_locked(db, username) is True


# ============ Theme 测试 ============

def test_get_theme_setting(db, init_default_data):
    """测试获取主题设置"""
    setting = crud.get_theme_setting(db)

    assert setting is not None
    assert setting.current_theme in ["light", "dark"]


def test_update_theme_setting(db, init_default_data):
    """测试更新主题设置"""
    setting = crud.update_theme_setting(db, "dark")

    assert setting.current_theme == "dark"


# ============ SyncAccount 测试 ============

def test_create_sync_account(db, init_default_data):
    """测试创建同步账号"""
    from app.schemas import SyncAccountCreate

    account_data = SyncAccountCreate(
        platform_type="csdn",
        account_name="mycsdn",
        credential="test-token"
    )

    account = crud.create_sync_account(db, account_data)

    assert account.id is not None
    assert account.platform_type == "csdn"
    assert account.account_name == "mycsdn"


def test_get_sync_accounts(db, init_default_data):
    """测试获取同步账号"""
    from app.schemas import SyncAccountCreate

    crud.create_sync_account(db, SyncAccountCreate(
        platform_type="csdn",
        account_name="csdn1"
    ))
    crud.create_sync_account(db, SyncAccountCreate(
        platform_type="wechat",
        account_name="wechat1"
    ))

    accounts = crud.get_sync_accounts(db)
    assert len(accounts) == 2

    csdn_accounts = crud.get_sync_accounts(db, platform_type="csdn")
    assert len(csdn_accounts) == 1
    assert csdn_accounts[0].platform_type == "csdn"


# ============ SyncRecord 测试 ============

def test_create_sync_record(db, init_default_data):
    """测试创建同步记录"""
    from app.schemas import ArticleCreate, SyncAccountCreate

    article_data = ArticleCreate(
        title="同步记录测试",
        slug="sync-record-test",
        status="published"
    )
    article = crud.create_article(db, article_data)

    account_data = SyncAccountCreate(
        platform_type="csdn",
        account_name="csdn"
    )
    account = crud.create_sync_account(db, account_data)

    record = crud.create_sync_record(
        db=db,
        article_id=article.id,
        sync_account_id=account.id,
        platform_type="csdn",
        status="success"
    )

    assert record.id is not None
    assert record.status == "success"


# ============ CommentConfig 测试 ============

def test_get_comment_config(db, init_default_data):
    """测试获取评论配置"""
    config = crud.get_comment_config(db)

    assert config is not None
    assert config.allow_registered_comments is not None
    assert config.allow_anonymous_comments is not None


def test_update_comment_config(db, init_default_data):
    """测试更新评论配置"""
    from app.schemas import CommentConfigUpdate

    update_data = CommentConfigUpdate(
        allow_anonymous_comments=False,
        require_approval=False
    )

    config = crud.update_comment_config(db, update_data)

    assert config.allow_anonymous_comments is False
    assert config.require_approval is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])