import os
import re
from dataclasses import dataclass, field


@dataclass
class PIIMasker:
    codename: str = "候选人"
    _mapping: dict[str, str] = field(default_factory=dict)
    _reverse_mapping: dict[str, str] = field(default_factory=dict)

    PHONE_PATTERN = re.compile(
        r"1[3-9]\d[\-\s]?\d{4}[\-\s]?\d{4}"
    )
    EMAIL_PATTERN = re.compile(
        r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}"
    )
    ID_CARD_PATTERN = re.compile(
        r"\d{17}[\dXx]"
    )
    ADDRESS_PATTERN = re.compile(
        r"(?:住址|地址|家庭住址)[：:]\s*\S+"
    )

    def _record(self, original: str, replacement: str) -> str:
        self._mapping[original] = replacement
        self._reverse_mapping[replacement] = original
        return replacement

    def mask(self, text: str, known_names: list[str] | None = None) -> str:
        result = text

        for name in (known_names or []):
            replacement = self._record(name, self.codename)
            result = result.replace(name, replacement)

        def replace_id(m: re.Match) -> str:
            return self._record(m.group(), "[身份证号已移除]")

        result = self.ID_CARD_PATTERN.sub(replace_id, result)

        def replace_phone(m: re.Match) -> str:
            return self._record(m.group(), "[手机号已移除]")

        def replace_email(m: re.Match) -> str:
            return self._record(m.group(), "[邮箱已移除]")

        result = self.PHONE_PATTERN.sub(replace_phone, result)
        result = self.EMAIL_PATTERN.sub(replace_email, result)

        def replace_address(m: re.Match) -> str:
            return self._record(m.group(), "[地址已移除]")

        result = self.ADDRESS_PATTERN.sub(replace_address, result)

        return result

    def get_mapping(self) -> dict[str, str]:
        return dict(self._mapping)

    def restore(self, masked_text: str) -> str:
        result = masked_text
        for replacement, original in self._reverse_mapping.items():
            result = result.replace(replacement, original)
        return result


_NAME_LABEL_PATTERN = re.compile(
    r"(?:姓\s*名|Name)\s*[：:]\s*([^\s,，\n]{2,4})"
)

_CHINESE_NAME_RE = re.compile(r"^[\u4e00-\u9fff]{2,4}$")

_FILENAME_STRIP_RE = re.compile(
    r"[-_\s]*(简历|resume|cv|个人|应聘|求职).*", re.IGNORECASE
)

_NAME_NEAR_CONTACT_RE = re.compile(
    r"([\u4e00-\u9fff]{2,4})\s*(?:[（(][A-Za-z\s]+[）)])?[\s\n]*"
    r"(?:电话|手机|Tel|Phone|Mobile|[：:]?\s*(?:\+?\d{2,3}[-\s]?)?"
    r"1[3-9]\d[\-\s]?\d{4}[\-\s]?\d{4})",
    re.IGNORECASE,
)

_SECTION_HEADERS = frozenset({
    "教育经历", "教育背景", "工作经历", "工作经验", "项目经历", "项目经验",
    "个人简介", "基本信息", "个人信息", "自我评价", "专业技能", "技能特长",
    "求职意向", "联系方式", "社会实践", "兴趣爱好", "荣誉奖项", "实习经历",
    "培训经历", "证书资质", "所获奖项", "科研经历", "校园经历", "实践经验",
    "获奖情况", "职业技能", "语言能力", "综合能力", "在校经历", "课外活动",
})


def _is_valid_name(text: str) -> bool:
    return bool(_CHINESE_NAME_RE.match(text)) and text not in _SECTION_HEADERS


def extract_name_from_resume(raw_text: str, original_filename: str = "") -> str:
    """Try to extract candidate's real name from resume content or filename."""
    m = _NAME_LABEL_PATTERN.search(raw_text)
    if m and _is_valid_name(m.group(1).strip()):
        return m.group(1).strip()

    m = _NAME_NEAR_CONTACT_RE.search(raw_text)
    if m and _is_valid_name(m.group(1).strip()):
        return m.group(1).strip()

    first_lines = raw_text.strip().splitlines()[:10]
    for line in first_lines:
        line = line.strip()
        if _is_valid_name(line):
            return line

    if original_filename:
        stem = os.path.splitext(original_filename)[0]
        stem = _FILENAME_STRIP_RE.sub("", stem).strip("-_ ")
        if _is_valid_name(stem):
            return stem

    return ""


def mask_display_name(name: str) -> str:
    """Partially mask a name for display: show surname + last char, mask middle.

    - 1 char: return as-is
    - 2 chars (e.g. 李明): 李*
    - 3+ chars (e.g. 张志明): 张*明
    """
    if len(name) <= 1:
        return name
    if len(name) == 2:
        return name[0] + "*"
    return name[0] + "*" * (len(name) - 2) + name[-1]
