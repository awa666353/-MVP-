"""适配器注册表。"""

from __future__ import annotations

from hospital_crawler.adapters.base import HospitalSiteAdapter


class GenericAdapter(HospitalSiteAdapter):
    adapter_id = "generic"


_REGISTRY: dict[str, type[HospitalSiteAdapter]] = {
    "generic": GenericAdapter,
}


def register_adapter(cls: type[HospitalSiteAdapter]) -> type[HospitalSiteAdapter]:
    _REGISTRY[cls.adapter_id] = cls
    return cls


def get_adapter(adapter_id: str) -> HospitalSiteAdapter:
    cls = _REGISTRY.get(adapter_id) or GenericAdapter
    return cls()


# 示例：某复杂站点可取消注释并实现独立文件
# @register_adapter
# class ExampleTertiaryAdapter(HospitalSiteAdapter):
#     adapter_id = "example_hospital_xyz"
#     def parse_override(self, ctx):
#         ...
