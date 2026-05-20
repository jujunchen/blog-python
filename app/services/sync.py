# 同步服务
# Sync Service

import time
import logging
from typing import Optional

import config
from app import crud

logger = logging.getLogger(__name__)


class SyncService:
    """同步服务管理器"""

    def __init__(self):
        self.adapters = {}

    def register_adapter(self, platform_type: str, adapter):
        """注册同步适配器"""
        self.adapters[platform_type] = adapter

    def get_adapter(self, platform_type: str):
        """获取同步适配器"""
        return self.adapters.get(platform_type)

    def sync_article(
        self,
        db,
        article,
        platform_type: str,
        max_retries: int = None
    ) -> dict:
        """
        同步文章到指定平台

        Args:
            db: 数据库会话
            article: 文章对象
            platform_type: 平台类型
            max_retries: 最大重试次数

        Returns:
            dict: 同步结果
        """
        max_retries = max_retries or config.SYNC_MAX_RETRIES

        adapter = self.get_adapter(platform_type)
        if not adapter:
            return {
                "success": False,
                "message": f"未找到平台适配器: {platform_type}"
            }

        # 获取同步账号
        accounts = crud.get_sync_accounts(db, platform_type=platform_type, active_only=True)
        if not accounts:
            return {
                "success": False,
                "message": f"未找到可用的 {platform_type} 同步账号"
            }

        account = accounts[0]

        # 创建同步记录
        record = crud.create_sync_record(
            db=db,
            article_id=article.id,
            sync_account_id=account.id,
            platform_type=platform_type,
            status='pending'
        )

        # 执行同步，带重试机制
        retry_count = 0
        last_error = None

        while retry_count < max_retries:
            try:
                # 执行同步
                result = adapter.sync_article(article, account)

                if result.get("success"):
                    # 同步成功
                    crud.update_sync_record(db, record.id, 'success', result.get("message", "同步成功"))
                    return {
                        "success": True,
                        "message": "同步成功",
                        "record_id": record.id
                    }
                else:
                    last_error = result.get("message", "同步失败")
                    logger.warning(f"同步失败 (尝试 {retry_count + 1}/{max_retries}): {last_error}")

            except Exception as e:
                last_error = str(e)
                logger.error(f"同步异常 (尝试 {retry_count + 1}/{max_retries}): {e}")

            retry_count += 1

            if retry_count < max_retries:
                # 重试延迟
                if retry_count == 1:
                    time.sleep(config.SYNC_RETRY_DELAY)  # 30秒
                else:
                    time.sleep(config.SYNC_LONG_RETRY_DELAY)  # 5分钟

        # 所有重试都失败
        crud.update_sync_record(db, record.id, 'failed', last_error)
        return {
            "success": False,
            "message": f"同步失败，已重试 {max_retries} 次",
            "error": last_error,
            "record_id": record.id
        }

    def test_connection(self, db, platform_type: str) -> dict:
        """测试平台连接"""
        adapter = self.get_adapter(platform_type)
        if not adapter:
            return {
                "success": False,
                "message": f"未找到平台适配器: {platform_type}"
            }

        accounts = crud.get_sync_accounts(db, platform_type=platform_type, active_only=True)
        if not accounts:
            return {
                "success": False,
                "message": f"未找到可用的 {platform_type} 同步账号"
            }

        try:
            result = adapter.test_connection(accounts[0])
            return {
                "success": result,
                "message": "连接成功" if result else "连接失败"
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"连接测试异常: {str(e)}"
            }


# 全局同步服务实例
sync_service = SyncService()


def sync_article_to_platform(db, article, platform_type: str) -> dict:
    """同步文章到平台的便捷函数"""
    return sync_service.sync_article(db, article, platform_type)


def register_default_adapters():
    """注册默认适配器"""
    from app.services.adapters.csdn import CSDNAdapter
    from app.services.adapters.wechat import WeChatAdapter

    sync_service.register_adapter('csdn', CSDNAdapter())
    sync_service.register_adapter('wechat', WeChatAdapter())


# 启动时自动注册适配器
register_default_adapters()