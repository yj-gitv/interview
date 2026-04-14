import pytest

from app.services.resume_parser import ResumeParser


class TestPDFParsing:
    def test_extracts_text_from_pdf(self, sample_pdf):
        parser = ResumeParser()
        result = parser.parse(sample_pdf)
        assert result.raw_text != ""
        assert "产品经理" in result.raw_text

    def test_extracts_filename(self, sample_pdf):
        parser = ResumeParser()
        result = parser.parse(sample_pdf)
        assert result.file_name == "resume.pdf"


class TestDOCXParsing:
    def test_extracts_text_from_docx(self, sample_docx):
        parser = ResumeParser()
        result = parser.parse(sample_docx)
        assert result.raw_text != ""
        assert "运营经理" in result.raw_text


class TestTXTParsing:
    def test_extracts_text_from_txt(self, tmp_path):
        path = tmp_path / "jd.txt"
        path.write_text("岗位职责\n负责增长", encoding="utf-8")
        parser = ResumeParser()
        result = parser.parse(str(path))
        assert "负责增长" in result.raw_text
        assert result.file_type == "txt"


class TestUnsupportedFormat:
    def test_raises_for_unsupported(self, tmp_path):
        bad_path = tmp_path / "resume.md"
        bad_path.write_text("x")
        parser = ResumeParser()
        with pytest.raises(ValueError, match="Unsupported"):
            parser.parse(str(bad_path))


class TestParseResult:
    def test_result_has_required_fields(self, sample_pdf):
        parser = ResumeParser()
        result = parser.parse(sample_pdf)
        assert hasattr(result, "raw_text")
        assert hasattr(result, "file_name")
        assert hasattr(result, "file_type")
        assert result.file_type == "pdf"
