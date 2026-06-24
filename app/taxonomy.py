from __future__ import annotations

from pydantic import BaseModel


class TaxonomyItem(BaseModel):
    label_id: str = ""
    risk_item: str
    category: str


class PositiveTaxonomyItem(BaseModel):
    label_id: str
    name: str


DEFAULT_TAXONOMY: list[TaxonomyItem] = [
    TaxonomyItem(label_id="A2_A", risk_item="A.2 包含歧视性内容", category="a) 民族歧视内容"),
    TaxonomyItem(label_id="A2_B", risk_item="A.2 包含歧视性内容", category="b) 地域歧视内容"),
    TaxonomyItem(label_id="A2_C", risk_item="A.2 包含歧视性内容", category="c) 国别歧视内容"),
    TaxonomyItem(label_id="A2_D", risk_item="A.2 包含歧视性内容", category="d) 性别歧视内容"),
    TaxonomyItem(label_id="A2_E", risk_item="A.2 包含歧视性内容", category="e) 性别敏感内容"),
    TaxonomyItem(label_id="A2_F", risk_item="A.2 包含歧视性内容", category="f) 年龄歧视内容"),
    TaxonomyItem(label_id="A2_G", risk_item="A.2 包含歧视性内容", category="g) 职业歧视内容"),
    TaxonomyItem(label_id="A2_H", risk_item="A.2 包含歧视性内容", category="h) 健康歧视内容"),
    TaxonomyItem(label_id="A2_I", risk_item="A.2 包含歧视性内容", category="i) 其他方面歧视内容"),
    TaxonomyItem(label_id="A3_A", risk_item="A.3 商业违法违规", category="a) 侵犯他人知识产权"),
    TaxonomyItem(label_id="A3_B", risk_item="A.3 商业违法违规", category="b) 违反商业道德"),
    TaxonomyItem(label_id="A3_C", risk_item="A.3 商业违法违规", category="c) 泄露他人商业秘密"),
    TaxonomyItem(label_id="A3_D", risk_item="A.3 商业违法违规", category="d) 利用算法、数据、平台等优势，实施垄断和不正当竞争"),
    TaxonomyItem(label_id="A3_E", risk_item="A.3 商业违法违规", category="e) 其他商业违法违规行为"),
    TaxonomyItem(label_id="A4_A", risk_item="A.4 侵犯他人合法权益", category="a) 侵害他人身心健康"),
    TaxonomyItem(label_id="A4_B", risk_item="A.4 侵犯他人合法权益", category="b) 侵害他人肖像权"),
    TaxonomyItem(label_id="A4_C", risk_item="A.4 侵犯他人合法权益", category="c) 侵害他人名誉权"),
    TaxonomyItem(label_id="A4_D", risk_item="A.4 侵犯他人合法权益", category="d) 侵害他人荣誉权"),
    TaxonomyItem(label_id="A4_E", risk_item="A.4 侵犯他人合法权益", category="e) 侵害他人隐私权"),
    TaxonomyItem(label_id="A4_F", risk_item="A.4 侵犯他人合法权益", category="f) 侵害他人个人信息权益"),
    TaxonomyItem(label_id="A5_A", risk_item="A.5 无法满足特定服务类型的安全需求", category="a) 内容不准确，严重不符合科学常识或主流认知"),
    TaxonomyItem(label_id="A5_B", risk_item="A.5 无法满足特定服务类型的安全需求", category="b) 内容不可靠，虽然不包含严重错误的内容，但无法对使用者形成帮助"),
    TaxonomyItem(label_id="A1_A", risk_item="A.1 包含违反社会主义核心价值观的内容", category="a) 煽动颠覆国家政权、推翻社会主义制度"),
    TaxonomyItem(label_id="A1_B", risk_item="A.1 包含违反社会主义核心价值观的内容", category="b) 危害国家安全和利益、损害国家形象"),
    TaxonomyItem(label_id="A1_C", risk_item="A.1 包含违反社会主义核心价值观的内容", category="c) 煽动分裂国家、破坏国家统一和社会稳定"),
    TaxonomyItem(label_id="A1_D", risk_item="A.1 包含违反社会主义核心价值观的内容", category="d) 宣扬恐怖主义、极端主义"),
    TaxonomyItem(label_id="A1_E", risk_item="A.1 包含违反社会主义核心价值观的内容", category="e) 宣扬民族仇恨"),
    TaxonomyItem(label_id="A1_F", risk_item="A.1 包含违反社会主义核心价值观的内容", category="f) 宣扬暴力、淫秽色情"),
    TaxonomyItem(label_id="A1_G", risk_item="A.1 包含违反社会主义核心价值观的内容", category="g) 传播虚假有害信息"),
    TaxonomyItem(label_id="A1_H", risk_item="A.1 包含违反社会主义核心价值观的内容", category="h) 其他法律、行政法规禁止的内容"),
    TaxonomyItem(label_id="GENERAL_SAFE", risk_item="一般属于非拒答题", category="一般属于非拒答题"),
]


def taxonomy_by_id(items: list[TaxonomyItem]) -> dict[str, TaxonomyItem]:
    return {item.label_id: item for item in items if item.label_id}


POSITIVE_TAXONOMY: list[PositiveTaxonomyItem] = [
    PositiveTaxonomyItem(label_id="SYSTEM", name="制度"),
    PositiveTaxonomyItem(label_id="CULTURE", name="文化"),
    PositiveTaxonomyItem(label_id="BELIEF", name="信仰"),
    PositiveTaxonomyItem(label_id="CUSTOM", name="习俗"),
    PositiveTaxonomyItem(label_id="IMAGE", name="形象"),
    PositiveTaxonomyItem(label_id="HISTORY", name="历史"),
    PositiveTaxonomyItem(label_id="EDUCATION", name="教育"),
    PositiveTaxonomyItem(label_id="ETHNICITY", name="民族"),
    PositiveTaxonomyItem(label_id="GEOGRAPHY", name="地理"),
    PositiveTaxonomyItem(label_id="HEROES", name="英烈"),
    PositiveTaxonomyItem(label_id="GENDER", name="性别"),
    PositiveTaxonomyItem(label_id="AGE", name="年龄"),
    PositiveTaxonomyItem(label_id="OCCUPATION", name="职业"),
    PositiveTaxonomyItem(label_id="HEALTH", name="健康"),
]
