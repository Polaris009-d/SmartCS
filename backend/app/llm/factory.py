"""
LLM Provider 工厂 — 根据配置创建提供商实例
"""
from app.llm.base import BaseLLMProvider
from app.core.config import settings

_provider: BaseLLMProvider | None = None


def get_llm_provider() -> BaseLLMProvider:
    """获取 LLM 提供商实例（惰性初始化单例）"""
    global _provider
    if _provider is not None:
        return _provider

    provider_name = settings.LLM_PROVIDER.lower()
    if provider_name == "openai":
        from app.llm.openai_provider import OpenAIProvider
        _provider = OpenAIProvider()
    elif provider_name == "anthropic":
        from app.llm.anthropic_provider import AnthropicProvider
        _provider = AnthropicProvider()
    elif provider_name == "local":
        # 本地模型通过 OpenAI 兼容接口（Ollama / vLLM）
        from app.llm.openai_provider import OpenAIProvider
        _provider = OpenAIProvider()
    else:
        raise ValueError(f"Unsupported LLM provider: {settings.LLM_PROVIDER}")
    return _provider


def reset_llm_provider():
    """重置提供商实例（配置变更后调用）"""
    global _provider
    _provider = None
