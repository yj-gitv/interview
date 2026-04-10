import os
from dataclasses import dataclass


@dataclass
class ParseResult:
    raw_text: str
    file_name: str
    file_type: str


class ResumeParser:
    SUPPORTED_TYPES = {"pdf", "docx"}

    def parse(self, file_path: str) -> ParseResult:
        file_name = os.path.basename(file_path)
        ext = file_name.rsplit(".", 1)[-1].lower() if "." in file_name else ""

        if ext not in self.SUPPORTED_TYPES:
            raise ValueError(
                f"Unsupported file type: .{ext}. Supported: {self.SUPPORTED_TYPES}"
            )

        if ext == "pdf":
            text = self._parse_pdf(file_path)
        else:
            text = self._parse_docx(file_path)

        return ParseResult(raw_text=text, file_name=file_name, file_type=ext)

    def _parse_pdf(self, file_path: str) -> str:
        import fitz

        doc = fitz.open(file_path)
        pages = []
        for page in doc:
            pages.append(page.get_text())
        doc.close()
        return "\n".join(pages).strip()

    def _parse_docx(self, file_path: str) -> str:
        from docx import Document

        doc = Document(file_path)
        paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
        return "\n".join(paragraphs).strip()
