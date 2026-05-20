# 微信公众号同步适配器
# WeChat Sync Adapter

import hashlib
import time
import json
from typing import Dict, Any

import config


class WeChatAdapter:
    """微信公众号同步适配器"""

    API_BASE_URL = "https://api.weixin.qq.com"

    def sync_article(self, article, account) -> Dict[str, Any]:
        """同步文章到微信公众号"""
        try:
            # 检查凭证配置
            if not account.credential:
                return {
                    "success": False,
                    "message": "未配置微信公众号凭证"
                }

            # 解析凭证
            credential_data = self._parse_credential(account.credential)
            if not credential_data:
                return {
                    "success": False,
                    "message": "无效的微信公众号凭证"
                }

            # 构建文章数据
            payload = self._build_wechat_payload(article)

            # 实际应该调用微信公众号的草稿接口和发布接口
            # 1. 创建草稿
            # 2. 发布草稿

            # 模拟 API 调用
            time.sleep(0.5)  # 模拟网络延迟

            return {
                "success": True,
                "message": "文章已同步到微信公众号",
                "external_id": self._generate_media_id(article)
            }

        except Exception as e:
            return {
                "success": False,
                "message": f"微信公众号同步失败: {str(e)}"
            }

    def test_connection(self, account) -> bool:
        """测试微信公众号账号连通性"""
        try:
            # 检查凭证配置
            if not account.credential:
                return False

            # 解析凭证
            credential_data = self._parse_credential(account.credential)
            if not credential_data:
                return False

            # 实际应该调用微信的 access_token 获取接口来验证
            # access_token = self._get_access_token(credential_data)

            return True

        except Exception:
            return False

    def _parse_credential(self, credential: str) -> Dict[str, str]:
        """解析凭证数据"""
        try:
            # 凭证应该是 JSON 格式，包含 appid, appsecret 等
            return json.loads(credential)
        except json.JSONDecodeError:
            # 如果不是 JSON，尝试其他解析方式
            return {}

    def _get_access_token(self, credential_data: Dict[str, str]) -> str:
        """获取 access_token"""
        # 实际应该调用微信 API 获取 access_token
        # url = f"{self.API_BASE_URL}/cgi-bin/token?grant_type=client_credential&appid={appid}&secret={appsecret}"

        # 这里返回模拟的 token
        return "mock_access_token"

    def _build_wechat_payload(self, article) -> Dict[str, Any]:
        """构建微信公众号专用载荷"""
        # 微信公众号需要特定的格式
        return {
            "title": article.title,
            "author": "作者",
            "digest": article.summary or "",
            "content": article.html_content or article.markdown_content,
            "content_source_url": "",
            "thumb_media_id": "",  # 需要上传图片获取 media_id
            "need_open_comment": 1,
            "only_fans_can_comment": 0,
            "local_url": article.cover_image or "",
        }

    def _generate_media_id(self, article) -> str:
        """生成媒体平台文章 ID"""
        return hashlib.md5(
            f"wechat_{article.id}_{article.slug}".encode()
        ).hexdigest()[:16]


# 导出适配器类
SyncAdapter = None  # 避免循环导入