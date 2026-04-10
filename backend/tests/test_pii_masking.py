from app.services.pii_masking import PIIMasker


class TestPhoneNumber:
    def test_masks_chinese_mobile(self):
        masker = PIIMasker()
        text = "我的手机号是13812345678，请联系我"
        result = masker.mask(text)
        assert "13812345678" not in result
        assert "[手机号已移除]" in result

    def test_masks_phone_with_dashes(self):
        masker = PIIMasker()
        text = "电话：138-1234-5678"
        result = masker.mask(text)
        assert "138-1234-5678" not in result


class TestEmail:
    def test_masks_email(self):
        masker = PIIMasker()
        text = "邮箱：zhangsan@example.com"
        result = masker.mask(text)
        assert "zhangsan@example.com" not in result
        assert "[邮箱已移除]" in result


class TestIDCard:
    def test_masks_18_digit_id(self):
        masker = PIIMasker()
        text = "身份证号：110101199001011234"
        result = masker.mask(text)
        assert "110101199001011234" not in result
        assert "[身份证号已移除]" in result

    def test_masks_id_with_x(self):
        masker = PIIMasker()
        text = "身份证 11010119900101123X"
        result = masker.mask(text)
        assert "11010119900101123X" not in result


class TestName:
    def test_replaces_name_with_codename(self):
        masker = PIIMasker(codename="候选人A")
        text = "张三在2020年加入阿里巴巴"
        result = masker.mask(text, known_names=["张三"])
        assert "张三" not in result
        assert "候选人A" in result
        assert "阿里巴巴" in result

    def test_preserves_company_names(self):
        masker = PIIMasker()
        text = "在腾讯工作了5年，后来去了字节跳动"
        result = masker.mask(text)
        assert "腾讯" in result
        assert "字节跳动" in result


class TestAddress:
    def test_masks_address_pattern(self):
        masker = PIIMasker()
        text = "住址：北京市朝阳区建国路88号"
        result = masker.mask(text)
        assert "建国路88号" not in result
        assert "[地址已移除]" in result


class TestMappingTable:
    def test_returns_mapping(self):
        masker = PIIMasker(codename="候选人A")
        text = "张三的手机号13812345678"
        result = masker.mask(text, known_names=["张三"])
        mapping = masker.get_mapping()
        assert "张三" in str(mapping)
        assert "13812345678" in str(mapping)

    def test_restore_from_mapping(self):
        masker = PIIMasker(codename="候选人A")
        original = "张三的手机号13812345678"
        masked = masker.mask(original, known_names=["张三"])
        restored = masker.restore(masked)
        assert "张三" in restored
        assert "13812345678" in restored
