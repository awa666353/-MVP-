"""
医院官网栏目关键词词典：用于链接发现与页面分类打分。
可按站点扩展，勿写死在业务逻辑中。
"""

from __future__ import annotations

from typing import Final

# 页面类型 -> 关键词列表（含同义词、常见栏目名）
PAGE_KEYWORDS: Final[dict[str, list[str]]] = {
    "hospital_profile": [
        "医院概况",
        "医院介绍",
        "医院简介",
        "本院简介",
        "单位简介",
        "关于我们",
        "医院文化",
        "历史沿革",
    ],
    "registration": [
        "挂号",
        "预约挂号",
        "门诊服务",
        "就医指南",
        "就诊指南",
        "门诊时间",
        "门诊须知",
        "预约须知",
        "挂号指南",
        "互联网医院",
        "在线预约",
    ],
    "department": [
        "科室设置",
        "科室介绍",
        "临床科室",
        "医技科室",
        "重点专科",
        "特色专科",
        "优势学科",
        "重点学科",
        "专科介绍",
    ],
    "contact": [
        "联系我们",
        "联系方式",
        "交通指南",
        "来院路线",
        "地址",
        "院区分布",
        "多院区",
        "分支机构",
    ],
}

# 挂号方式识别关键词 -> 标准化枚举值
REGISTRATION_KEYWORD_MAP: Final[dict[str, str]] = {
    "预约挂号": "online_booking",
    "网上挂号": "web",
    "官网挂号": "web",
    "在线预约": "online_booking",
    "微信": "wechat",
    "公众号": "wechat",
    "微信小程序": "wechat_mini",
    "支付宝": "alipay",
    "电话预约": "phone",
    "电话挂号": "phone",
    "现场挂号": "onsite",
    "窗口": "onsite",
    "自助机": "kiosk",
    "自助挂号": "kiosk",
    "第三方": "third_party",
    "健康云": "third_party",
    "114": "third_party",
    "门诊服务": "general_outpatient",  # 弱信号，normalize 层可降权
}

# 优势学科 / 重点专科段落关键词（用于分段与条目拆分）
DEPARTMENT_HIGHLIGHT_KEYWORDS: Final[list[str]] = [
    "国家临床重点专科",
    "国家重点专科",
    "省级重点专科",
    "省重点专科",
    "市级重点专科",
    "重点学科",
    "优势学科",
    "特色专科",
    "重点专科建设项目",
    "重点专科",
]

# 医院等级 / 性质常见词（normalize 用）
HOSPITAL_LEVEL_PATTERNS: Final[list[str]] = [
    "三级甲等",
    "三级乙等",
    "三级医院",
    "二级甲等",
    "二级乙等",
    "二甲",
    "三甲",
    "三乙",
]

NATURE_KEYWORDS: Final[dict[str, str]] = {
    "公立": "public",
    "民营": "private",
    "私立": "private",
    "专科": "specialty_hospital",
    "中医院": "tcm",
    "妇幼": "maternal_child",
}
