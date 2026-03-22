"""
预留：弱结构化页面通过 LLM 抽取。
实现为空，接口保持稳定供后续接入 OpenAI / 本地模型 / Supabase Edge Function。
"""

from __future__ import annotations

from hospital_crawler.models import LLMExtractRequest, LLMExtractResult


async def extract_with_llm(request: LLMExtractRequest) -> LLMExtractResult:
    """
    后续实现：
    - 对 plain_text 分块
    - 调用模型返回 JSON
    - 映射到 HospitalExtracted 子集
    """
    return LLMExtractResult(data={}, model="none", confidence=0.0)
