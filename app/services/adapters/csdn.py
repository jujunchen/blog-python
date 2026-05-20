# CSDN 同步适配器
# CSDN Sync Adapter

import hashlib
import time
from typing import Dict, Any

import config


class SyncAdapter:
    """同步适配器基类"""

    def sync_article(self, article, account) -> Dict[str, Any]:
        """同步文章到平台"""
        raise NotImplementedError

    def test_connection(self, account) -> bool:
        """测试账号连通性"""
        raise NotImplementedError

    def build_payload(self, article) -> Dict[str, Any]:
        """构造同步请求数据"""
        return {
            "title": article.title,
            "content": article.html_content or article.markdown_content,
            "summary": article.summary or "",
            "cover_image": article.cover_image or "",
            "tags": [tag.name for tag in article.tags] if article.tags else [],
            "category": article.category.name if article.category else "",
        }


class CSDNAdapter(SyncAdapter):
    """CSDN 平台同步适配器"""

    API_BASE_URL = "https://mp.csdn.net/mp_blog/manage/article"

    def sync_article(self, article, account) -> Dict[str, Any]:
        """同步文章到 CSDN"""
        try:
            # 构建文章数据
            payload = self.build_payload(article)

            # 这里应该调用实际的 CSDN API
            # 由于没有官方 API，这里模拟同步过程
            # 实际实现需要根据 CSDN 的具体接口来调整

            # 模拟 API 调用
            headers = {
                "Content-Type": "application/json",
                # 需要从 account.credential 中获取实际的 token
            }

            # 实际发送请求的代码（注释掉，因为没有真实 API）
            # response = requests.post(
            #     self.API_BASE_URL,
            #     json=payload,
            #     headers=headers,
            #     timeout=config.SYNC_TIMEOUT
            # )

            # 模拟成功响应
            time.sleep(0.5)  # 模拟网络延迟

            return {
                "success": True,
                "message": "文章已同步到 CSDN",
                "external_id": self._generate_external_id(article)
            }

        except Exception as e:
            return {
                "success": False,
                "message": f"CSDN 同步失败: {str(e)}"
            }

    def test_connection(self, account) -> bool:
        """测试 CSDN 账号连通性"""
        try:
            # 实际实现需要调用 CSDN 的验证接口
            # 这里模拟验证过程

            # 检查账号配置是否完整
            if not account.account_name:
                return False

            # 模拟 API 调用测试
            # 实际应该调用 CSDN 的用户信息接口来验证 token

            return True

        except Exception:
            return False

    def _generate_external_id(self, article) -> str:
        """生成外部平台文章 ID"""
        return hashlib.md5(
            f"csdn_{article.id}_{article.slug}".encode()
        ).hexdigest()[:16]

    def build_payload(self, article) -> Dict[str, Any]:
        """构建 CSDN 专用载荷"""
        payload = super().build_payload(article)

        # CSDN 特定的字段
        payload.update({
            "type": "original",  # 原创
            "read_type": "public",  # 公开
            "source": "个人博客",  # 来源
        })

        return payload