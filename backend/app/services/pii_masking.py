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
