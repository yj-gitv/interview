import os

import pytest

from app.services.pdf_export import PDFExportService


class TestPDFExport:
    def test_generates_pdf_file(self, tmp_path):
        service = PDFExportService()
        output_path = str(tmp_path / "report.pdf")
        service.export(
            output_path=output_path,
            candidate_codename="候选人A",
            position_title="产品经理",
            interview_date="2026-04-10",
            duration_minutes=45,
            candidate_overview="候选人表现良好，有丰富的产品经验。",
            scores={
                "表达清晰度": 85,
                "案例丰富度": 78,
                "思维深度": 80,
                "自我认知": 72,
                "岗位热情": 88,
                "综合评分": 81,
            },
            highlights=["数据驱动", "表达清晰"],
            concerns=["管理经验不足"],
            jd_alignment=[
                {"requirement": "用户增长", "status": "达成", "note": "有直接经验"},
            ],
            recommendation="推荐",
            recommendation_reason="核心能力匹配度高",
            next_steps="二面重点考察管理能力",
        )
        assert os.path.exists(output_path)
        assert os.path.getsize(output_path) > 0

    def test_pdf_contains_basic_structure(self, tmp_path):
        service = PDFExportService()
        output_path = str(tmp_path / "report.pdf")
        service.export(
            output_path=output_path,
            candidate_codename="候选人B",
            position_title="运营经理",
            interview_date="2026-04-10",
            duration_minutes=30,
            candidate_overview="表现一般。",
            scores={"综合评分": 60},
            highlights=["沟通能力"],
            concerns=[],
            jd_alignment=[],
            recommendation="待定",
            recommendation_reason="需要更多信息",
            next_steps="",
        )
        with open(output_path, "rb") as f:
            header = f.read(5)
        assert header == b"%PDF-"
