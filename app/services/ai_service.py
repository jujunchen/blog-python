# AI 服务模块
# AI Service Module

from abc import ABC, abstractmethod
from typing import Optional
import re

from sqlalchemy.orm import Session
import openai

from app import crud


class BaseAIProvider(ABC):
    """AI 提供者抽象基类"""

    @abstractmethod
    def chat_completion(self, messages: list, **kwargs) -> str:
        """聊天补全"""
        pass


class OpenAIProvider(BaseAIProvider):
    """OpenAI 兼容的提供者"""

    def __init__(self, api_key: str, api_base: str = None, model: str = "gpt-3.5-turbo"):
        self.api_key = api_key
        self.api_base = api_base
        self.model = model
        self.client = openai.OpenAI(
            api_key=api_key,
            base_url=api_base if api_base else None
        )

    def chat_completion(self, messages: list, **kwargs) -> str:
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=kwargs.get('temperature', 0.7),
            max_tokens=kwargs.get('max_tokens', 1000),
            timeout=kwargs.get('timeout', 60)
        )
        return response.choices[0].message.content


class OllamaProvider(BaseAIProvider):
    """Ollama 本地模型提供者"""

    def __init__(self, api_base: str = "http://localhost:11434/v1", model: str = "llama2"):
        self.api_base = api_base
        self.model = model
        self.client = openai.OpenAI(
            api_key='ollama',
            base_url=api_base
        )

    def chat_completion(self, messages: list, **kwargs) -> str:
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=kwargs.get('temperature', 0.7),
            max_tokens=kwargs.get('max_tokens', 1000),
            timeout=kwargs.get('timeout', 60)
        )
        return response.choices[0].message.content


class AIService:
    """AI 服务"""

    def __init__(self, db: Session):
        self.db = db
        self.config = crud.get_or_create_default_ai_config(db)
        self._provider = None

    def is_available(self) -> bool:
        """检查 AI 服务是否可用"""
        if not self.config.is_enabled:
            return False
        if self.config.provider == 'openai' and not self.config.api_key:
            return False
        return True

    def _get_provider(self) -> Optional[BaseAIProvider]:
        """获取 AI 提供者"""
        if not self.is_available():
            return None

        if self.config.provider == 'ollama':
            return OllamaProvider(
                api_base=self.config.api_base or "http://localhost:11434/v1",
                model=self.config.model
            )
        else:
            return OpenAIProvider(
                api_key=self.config.api_key,
                api_base=self.config.api_base,
                model=self.config.model
            )

    @property
    def provider(self) -> Optional[BaseAIProvider]:
        """懒加载 AI 提供者"""
        if not self._provider:
            self._provider = self._get_provider()
        return self._provider

    def render_prompt(self, scene: str, **variables) -> Optional[str]:
        """渲染提示词模板，替换变量"""
        template = crud.get_prompt_template_by_scene(self.db, scene)
        if not template:
            return None

        prompt = template.prompt
        for key, value in variables.items():
            placeholder = "{{" + key + "}}"
            prompt = prompt.replace(placeholder, str(value))

        return prompt

    def generate(self, scene: str, **variables) -> str:
        """根据场景生成内容"""
        if not self.is_available():
            raise Exception("AI 服务未启用或配置不完整")

        prompt = self.render_prompt(scene, **variables)
        if not prompt:
            raise Exception(f"未找到场景 '{scene}' 的提示词模板")

        messages = [
            {"role": "system", "content": "你是一个专业的内容创作助手，擅长写作和内容优化。"},
            {"role": "user", "content": prompt}
        ]

        try:
            return self.provider.chat_completion(
                messages=messages,
                temperature=self.config.temperature / 100,
                max_tokens=self.config.max_tokens,
                timeout=self.config.timeout
            )
        except Exception as e:
            raise Exception(f"AI 生成失败: {str(e)}")

    def test_connection(self) -> tuple[bool, str]:
        """测试 AI 连接"""
        if not self.config.api_key and self.config.provider != 'ollama':
            return False, "API Key 不能为空"

        try:
            provider = self._get_provider()
            if not provider:
                return False, "无法初始化 AI 提供者"

            result = provider.chat_completion(
                messages=[{"role": "user", "content": "请回复 'OK' 表示连接成功"}],
                max_tokens=10,
                timeout=30
            )
            return True, "连接成功"
        except Exception as e:
            return False, f"连接失败: {str(e)}"


def get_ai_service(db: Session) -> AIService:
    """获取 AI 服务实例"""
    return AIService(db)
