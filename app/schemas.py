# Pydantic 校验模型
# Pydantic Schemas

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


# ============ 基础模型 ============

class BaseSchema(BaseModel):
    """基础 Schema"""
    class Config:
        from_attributes = True


# ============ Article 相关 ============

class ArticleBase(BaseSchema):
    """文章基础模型"""
    title: str = Field(..., min_length=1, max_length=200)
    slug: str = Field(..., min_length=1, max_length=200)
    summary: Optional[str] = None
    markdown_content: Optional[str] = None
    cover_image: Optional[str] = None
    status: str = 'draft'


class ArticleCreate(ArticleBase):
    """创建文章"""
    category_id: Optional[int] = None
    tags: List[str] = []


class ArticleUpdate(BaseSchema):
    """更新文章"""
    title: Optional[str] = Field(None, max_length=200)
    slug: Optional[str] = Field(None, max_length=200)
    summary: Optional[str] = None
    markdown_content: Optional[str] = None
    html_content: Optional[str] = None
    cover_image: Optional[str] = None
    status: Optional[str] = None
    category_id: Optional[int] = None
    tags: Optional[List[str]] = None


class ArticleInDB(ArticleBase):
    """数据库中的文章"""
    id: int
    publish_date: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime


class ArticleList(BaseSchema):
    """文章列表项"""
    id: int
    title: str
    slug: str
    summary: Optional[str] = None
    cover_image: Optional[str] = None
    status: str
    publish_date: Optional[datetime] = None
    created_at: datetime
    category_name: Optional[str] = None
    tags: List[str] = []


# ============ Category 相关 ============

class CategoryBase(BaseSchema):
    """分类基础模型"""
    name: str = Field(..., min_length=1, max_length=50)
    slug: str = Field(..., min_length=1, max_length=50)
    description: Optional[str] = None


class CategoryCreate(CategoryBase):
    """创建分类"""
    pass


class CategoryUpdate(BaseSchema):
    """更新分类"""
    name: Optional[str] = Field(None, max_length=50)
    slug: Optional[str] = Field(None, max_length=50)
    description: Optional[str] = None


class CategoryInDB(CategoryBase):
    """数据库中的分类"""
    id: int
    created_at: datetime


# ============ Tag 相关 ============

class TagBase(BaseSchema):
    """标签基础模型"""
    name: str = Field(..., min_length=1, max_length=50)
    slug: str = Field(..., min_length=1, max_length=50)
    description: Optional[str] = None


class TagCreate(TagBase):
    """创建标签"""
    pass


class TagInDB(TagBase):
    """数据库中的标签"""
    id: int
    created_at: datetime


# ============ Comment 相关 ============

class CommentBase(BaseSchema):
    """评论基础模型"""
    content: str = Field(..., min_length=1)


class CommentCreate(CommentBase):
    """创建评论"""
    article_id: int
    author_name: str = Field(..., min_length=1, max_length=50)
    author_email: Optional[str] = None
    is_anonymous: bool = False
    parent_id: Optional[int] = None
    captcha_token: Optional[str] = None


class CommentUpdate(BaseSchema):
    """更新评论"""
    content: Optional[str] = None
    approved: Optional[bool] = None


class CommentInDB(CommentBase):
    """数据库中的评论"""
    id: int
    article_id: int
    author_name: str
    author_email: Optional[str] = None
    is_anonymous: bool
    approved: bool
    parent_id: Optional[int] = None
    created_at: datetime


class CommentPublic(BaseSchema):
    """公开显示的评论（隐藏邮箱）"""
    id: int
    article_id: int
    author_name: str
    content: str
    is_anonymous: bool
    created_at: datetime
    replies: List['CommentPublic'] = []


# ============ AdminUser 相关 ============

class AdminUserBase(BaseSchema):
    """管理员基础模型"""
    username: str = Field(..., min_length=3, max_length=50)


class AdminUserCreate(AdminUserBase):
    """创建管理员"""
    password: str = Field(..., min_length=6)
    email: Optional[str] = None


class AdminUserInDB(AdminUserBase):
    """数据库中的管理员"""
    id: int
    email: Optional[str] = None
    is_active: bool
    created_at: datetime


class AdminLogin(BaseSchema):
    """管理员登录"""
    username: str
    password: str
    csrf_token: Optional[str] = None


class AdminLoginResponse(BaseSchema):
    """登录响应"""
    success: bool
    message: str
    username: Optional[str] = None


# ============ Theme 相关 ============

class ThemeSettingSchema(BaseSchema):
    """主题设置"""
    current_theme: str
    available_themes: List[str] = ['light', 'dark']


class ThemeUpdate(BaseSchema):
    """更新主题"""
    theme: str


# ============ Sync 相关 ============

class SyncAccountBase(BaseSchema):
    """同步账号基础模型"""
    platform_type: str
    account_name: str = Field(..., max_length=100)


class SyncAccountCreate(SyncAccountBase):
    """创建同步账号"""
    config_data: Optional[str] = None
    credential: Optional[str] = None


class SyncAccountInDB(SyncAccountBase):
    """数据库中的同步账号"""
    id: int
    is_active: bool
    created_at: datetime


class SyncRecordSchema(BaseSchema):
    """同步记录"""
    id: int
    article_id: Optional[int]
    platform_type: str
    status: str
    result_message: Optional[str] = None
    synced_at: datetime


class SyncRequest(BaseSchema):
    """同步请求"""
    article_id: int
    platform_type: str


class SyncResponse(BaseSchema):
    """同步响应"""
    success: bool
    message: str
    record_id: Optional[int] = None


# ============ CommentConfig 相关 ============

class CommentConfigSchema(BaseSchema):
    """评论配置"""
    allow_registered_comments: bool = True
    allow_anonymous_comments: bool = True
    require_approval: bool = True


class CommentConfigUpdate(BaseSchema):
    """更新评论配置"""
    allow_registered_comments: Optional[bool] = None
    allow_anonymous_comments: Optional[bool] = None
    require_approval: Optional[bool] = None


# ============ System 相关 ============

class HealthCheck(BaseSchema):
    """健康检查"""
    status: str
    database: str
    timestamp: datetime


class SettingsUpdate(BaseSchema):
    """系统设置更新"""
    app_name: Optional[str] = None
    theme: Optional[str] = None
    comment_config: Optional[CommentConfigUpdate] = None


class ErrorResponse(BaseSchema):
    """错误响应"""
    error: str
    detail: Optional[str] = None


# 解决前向引用
CommentPublic.model_rebuild()