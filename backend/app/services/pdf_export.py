import os

from fpdf import FPDF


class PDFExportService:
    def __init__(self):
        self._font_path = self._find_cjk_font()

    def _find_cjk_font(self) -> str | None:
        candidates = [
            "/System/Library/Fonts/PingFang.ttc",
            "/System/Library/Fonts/STHeiti Light.ttc",
            "/System/Library/Fonts/Hiragino Sans GB.ttc",
            "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
        ]
        for path in candidates:
            if os.path.exists(path):
                return path
        return None

    def export(
        self,
        output_path: str,
        candidate_codename: str,
        position_title: str,
        interview_date: str,
        duration_minutes: int,
        candidate_overview: str,
        scores: dict[str, float],
        highlights: list[str],
        concerns: list[str],
        jd_alignment: list[dict],
        recommendation: str,
        recommendation_reason: str,
        next_steps: str,
        transcript_lines: list[dict] | None = None,
    ):
        pdf = FPDF()
        pdf.add_page()

        if self._font_path:
            pdf.add_font("CJK", "", self._font_path, uni=True)
            pdf.set_font("CJK", size=18)
        else:
            pdf.set_font("Helvetica", size=18)

        pdf.cell(0, 12, text="Interview Summary Report", new_x="LMARGIN", new_y="NEXT", align="C")
        pdf.ln(4)

        self._set_body_font(pdf, 11)
        pdf.cell(0, 8, text=f"Candidate: {candidate_codename}  |  Position: {position_title}", new_x="LMARGIN", new_y="NEXT")
        pdf.cell(0, 8, text=f"Date: {interview_date}  |  Duration: {duration_minutes} min  |  Recommendation: {recommendation}", new_x="LMARGIN", new_y="NEXT")
        pdf.ln(4)

        self._section_header(pdf, "Candidate Overview")
        self._set_body_font(pdf, 10)
        pdf.multi_cell(0, 6, text=candidate_overview)
        pdf.ln(3)

        self._section_header(pdf, "Scores")
        self._set_body_font(pdf, 10)
        for label, score in scores.items():
            pdf.cell(0, 7, text=f"  {label}: {score}/100", new_x="LMARGIN", new_y="NEXT")
        pdf.ln(3)

        if highlights:
            self._section_header(pdf, "Highlights")
            self._set_body_font(pdf, 10)
            for h in highlights:
                pdf.cell(0, 7, text=f"  + {h}", new_x="LMARGIN", new_y="NEXT")
            pdf.ln(3)

        if concerns:
            self._section_header(pdf, "Concerns")
            self._set_body_font(pdf, 10)
            for c in concerns:
                pdf.cell(0, 7, text=f"  - {c}", new_x="LMARGIN", new_y="NEXT")
            pdf.ln(3)

        if jd_alignment:
            self._section_header(pdf, "JD Alignment")
            self._set_body_font(pdf, 10)
            for item in jd_alignment:
                req = item.get("requirement", "")
                status = item.get("status", "")
                note = item.get("note", "")
                pdf.cell(0, 7, text=f"  [{status}] {req}: {note}", new_x="LMARGIN", new_y="NEXT")
            pdf.ln(3)

        self._section_header(pdf, "Recommendation")
        self._set_body_font(pdf, 10)
        pdf.multi_cell(0, 6, text=f"{recommendation}: {recommendation_reason}")
        pdf.ln(3)

        if next_steps:
            self._section_header(pdf, "Next Steps")
            self._set_body_font(pdf, 10)
            pdf.multi_cell(0, 6, text=next_steps)

        if transcript_lines:
            pdf.add_page()
            self._section_header(pdf, "Full Interview Transcript")
            pdf.ln(3)
            speaker_labels = {"interviewer": "面试官", "candidate": "候选人"}
            self._set_body_font(pdf, 9)
            for entry in transcript_lines:
                ts = entry.get("timestamp", 0)
                minutes = int(ts) // 60
                seconds = int(ts) % 60
                speaker = speaker_labels.get(entry.get("speaker", ""), entry.get("speaker", ""))
                text = entry.get("sanitized_text", "")
                line = f"[{minutes:02d}:{seconds:02d}] {speaker}: {text}"
                pdf.multi_cell(0, 5, text=line)
                pdf.ln(1)

        os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
        pdf.output(output_path)

    def _section_header(self, pdf: FPDF, text: str):
        if self._font_path:
            pdf.set_font("CJK", size=13)
        else:
            pdf.set_font("Helvetica", "B", size=13)
        pdf.cell(0, 9, text=text, new_x="LMARGIN", new_y="NEXT")

    def _set_body_font(self, pdf: FPDF, size: int):
        if self._font_path:
            pdf.set_font("CJK", size=size)
        else:
            pdf.set_font("Helvetica", size=size)
