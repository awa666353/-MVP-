"""
统一数据 Schema（Pydantic v2）。
用于校验、序列化及后续对接 Supabase / RAG。
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field, field_validator


class SeedHospital(BaseModel):
    """种子医院（CSV/JSON 输入）。"""

    name: str = Field(..., description="医院全称")
    official_url: str = Field(..., description="官网首页 URL")
    province: str = Field(default="", description="省份")
    city: str = Field(default="", description="城市")
    adapter_id: str = Field(default="generic", description="可选：站点适配器 ID")
    notes: str = Field(default="", description="备注")

    @field_validator("official_url")
    @classmethod
    def strip_url(cls, v: str) -> str:
        return (v or "").strip()


class SourceProvenance(BaseModel):
    """单字段或单段文本的来源溯源。"""

    source_url: str = ""
    page_title: str = ""
    fetched_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at_page: Optional[str] = None  # 页面声明的更新时间（原始字符串）
    raw_snippet: str = Field(default="", description="原始文本片段，便于审计")


class RegistrationMethodItem(BaseModel):
    """结构化挂号方式条目。"""

    method_code: str = Field(..., description="标准化代码，如 wechat / phone")
    method_label_zh: str = Field(default="", description="中文展示名")
    detail_text: str = Field(default="")
    booking_url: str = Field(default="")
    supports_booking: Optional[bool] = None
    provenance: Optional[SourceProvenance] = None


class DepartmentItem(BaseModel):
    """科室或重点专科条目。"""

    name: str
    category: str = Field(
        default="general",
        description="national_clinical / provincial / advantage / department_list / other",
    )
    description: str = Field(default="")
    provenance: Optional[SourceProvenance] = None


class HospitalExtracted(BaseModel):
    """从多页聚合后的医院业务视图（写入前经 normalize）。"""

    # 基础信息
    name: str = ""
    short_name: str = ""
    level: str = ""
    nature: str = ""
    province: str = ""
    city: str = ""
    address: str = ""
    phone: str = ""
    postal_code: str = ""
    website_url: str = ""
    introduction: str = ""

    # 挂号
    registration_entry_url: str = ""
    outpatient_hours: str = ""
    visit_notes: str = ""
    supports_appointment: Optional[bool] = None

    # 扩展预留
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    featured_tech: str = ""
    expert_team_url: str = ""
    branch_campus_info: str = ""
    emergency_info: str = ""
    internet_hospital_info: str = ""

    registration_methods: list[RegistrationMethodItem] = Field(default_factory=list)
    departments: list[DepartmentItem] = Field(default_factory=list)

    # 聚合置信度 0~1
    confidence_score: float = 0.0
    review_flags: list[str] = Field(default_factory=list)

    # 溯源（主记录级）
    primary_source_url: str = ""
    last_crawled_at: Optional[datetime] = None


class RawPageRecord(BaseModel):
    """原始页面存档。"""

    url: str
    final_url: str = ""
    http_status: int = 0
    content_type: str = ""
    title: str = ""
    html_sha256: str = ""
    text_preview: str = Field(default="", max_length=8000)
    fetched_at: datetime = Field(default_factory=datetime.utcnow)
    crawl_task_id: Optional[int] = None


class ParsedPageBundle(BaseModel):
    """单页解析结果（多解析器可合并）。"""

    page_type: str = Field(default="unknown")
    hospital_partial: HospitalExtracted = Field(default_factory=HospitalExtracted)
    extra: dict[str, Any] = Field(default_factory=dict)


class LLMExtractRequest(BaseModel):
    """预留：弱结构化页面交给 LLM 抽取时的请求体。"""

    url: str
    title: str
    plain_text: str
    target_fields: list[str] = Field(default_factory=list)


class LLMExtractResult(BaseModel):
    """预留：LLM 返回的结构化结果（实现见 llm_stub）。"""

    data: dict[str, Any] = Field(default_factory=dict)
    model: str = ""
    confidence: float = 0.0
