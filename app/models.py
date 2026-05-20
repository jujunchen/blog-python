# 数据库模型定义
# Database Models

from datetime import datetime
from typing import Optional, List

from sqlalchemy import (
    Column, Integer, String, Text, Boolean, DateTime, ForeignKey, Table
)
from sqlalchemy.orm import relationship, declarative_base

Base = declarative_base()

# 关联表：文章与标签的多对多关系
article_tags = Table(
    'article_tags',
    Base.metadata,
    Column('article_id', Integer, ForeignKey('articles.id', ondelete='CASCADE'), primary_key=True),
    Column('tag_id', Integer, ForeignKey('tags.id', ondelete='CASCADE'), primary_key=True)
)


class Article(Base):
    """文章模型"""
    __tablename__ = 'articles'

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    slug = Column(String(200), unique=True, nullable=False, index=True)
    summary = Column(Text)
    markdown_content = Column(Text)
    html_content = Column(Text)
    cover_image = Column(String(500))
    status = Column(String(20), default='draft')  # draft / published
    publish_date = Column(DateTime)
    category_id = Column(Integer, ForeignKey('categories.id'))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关系
    category = relationship('Category', back_populates='articles')
    tags = relationship('Tag', secondary=article_tags, back_populates='articles')
    comments = relationship('Comment', back_populates='article', cascade='all, delete-orphan')

    def __repr__(self):
        return f"<Article(id={self.id}, title='{self.title}')>"


class Category(Base):
    """分类模型"""
    __tablename__ = 'categories'

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), nullable=False, unique=True)
    slug = Column(String(50), unique=True, nullable=False, index=True)
    description = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

    # 关系
    articles = relationship('Article', back_populates='category')

    def __repr__(self):
        return f"<Category(name='{self.name}')>"


class Tag(Base):
    """标签模型"""
    __tablename__ = 'tags'

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), nullable=False, unique=True)
    slug = Column(String(50), unique=True, nullable=False, index=True)
    description = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

    # 关系
    articles = relationship('Article', secondary=article_tags, back_populates='tags')

    def __repr__(self):
        return f"<Tag(name='{self.name}')>"


class ThemeSetting(Base):
    """主题设置模型"""
    __tablename__ = 'theme_settings'

    id = Column(Integer, primary_key=True, index=True)
    current_theme = Column(String(50), default='light')
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<ThemeSetting(current_theme='{self.current_theme}')>"


class SyncAccount(Base):
    """同步账号模型"""
    __tablename__ = 'sync_accounts'

    id = Column(Integer, primary_key=True, index=True)
    platform_type = Column(String(50), nullable=False)  # csdn / wechat
    account_name = Column(String(100), nullable=False)
    config_data = Column(Text)  # JSON 配置数据
    credential = Column(Text)  # 加密的凭证信息
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关系
    records = relationship('SyncRecord', back_populates='sync_account', cascade='all, delete-orphan')

    def __repr__(self):
        return f"<SyncAccount(platform='{self.platform_type}', account='{self.account_name}')>"


class SyncRecord(Base):
    """同步记录模型"""
    __tablename__ = 'sync_records'

    id = Column(Integer, primary_key=True, index=True)
    article_id = Column(Integer, ForeignKey('articles.id', ondelete='SET NULL'))
    sync_account_id = Column(Integer, ForeignKey('sync_accounts.id', ondelete='CASCADE'))
    platform_type = Column(String(50), nullable=False)
    status = Column(String(20), default='pending')  # pending / success / failed
    result_message = Column(Text)
    synced_at = Column(DateTime, default=datetime.utcnow)

    # 关系
    article = relationship('Article')
    sync_account = relationship('SyncAccount', back_populates='records')

    def __repr__(self):
        return f"<SyncRecord(article={self.article_id}, platform='{self.platform_type}')>"


class Comment(Base):
    """评论模型"""
    __tablename__ = 'comments'

    id = Column(Integer, primary_key=True, index=True)
    article_id = Column(Integer, ForeignKey('articles.id', ondelete='CASCADE'), nullable=False)
    author_name = Column(String(50), nullable=False)
    author_email = Column(String(100))  # 不公开显示，仅用于通知
    content = Column(Text, nullable=False)
    is_anonymous = Column(Boolean, default=False)
    approved = Column(Boolean, default=True)
    parent_id = Column(Integer, ForeignKey('comments.id', ondelete='CASCADE'))
    created_at = Column(DateTime, default=datetime.utcnow)

    # 关系（支持嵌套评论）
    article = relationship('Article', back_populates='comments')
    replies = relationship('Comment', backref='parent', remote_side=[id])

    def __repr__(self):
        return f"<Comment(id={self.id}, author='{self.author_name}')>"


class CommentConfig(Base):
    """评论配置模型"""
    __tablename__ = 'comment_configs'

    id = Column(Integer, primary_key=True, index=True)
    allow_registered_comments = Column(Boolean, default=True)
    allow_anonymous_comments = Column(Boolean, default=True)
    require_approval = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<CommentConfig()>"


class AdminUser(Base):
    """管理员用户模型"""
    __tablename__ = 'admin_users'

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    password_hash = Column(String(200), nullable=False)
    email = Column(String(100))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<AdminUser(username='{self.username}')>"


class LoginAttempt(Base):
    """登录尝试记录模型"""
    __tablename__ = 'login_attempts'

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), nullable=False, index=True)
    ip_address = Column(String(50))
    success = Column(Boolean, default=False)
    attempted_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<LoginAttempt(username='{self.username}', success={self.success})>"