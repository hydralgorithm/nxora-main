"""Multi-format resume/JD parser: PDF, TXT, DOCX, XML/HTML, legacy DOC (best effort).

Guarantees: never raises for a bad file — returns whatever text could be extracted,
with `parse_warning` set when extraction looks unreliable (e.g. image-scan PDF,
legacy binary .doc). Produces section splits for location-aware scoring + evidence.
"""
from __future__ import annotations

import io
import re
from dataclasses import dataclass, field


@dataclass
class ResumeSection:
    name: str          # normalized: Summary|Skills|Experience|Projects|Education|Other|Full Text|Header
    text: str


@dataclass
class ResumeData:
    name: str
    file: str
    sections: list[ResumeSection] = field(default_factory=list)
    full_text: str = ""
    parse_warning: str | None = None
    email: str | None = None


_SECTION_PATTERNS = [
    (re.compile(r"^(summary|objective|profile|about me|about)$", re.I), "Summary"),
    (re.compile(r"^(technical skills|skills|skill set|technologies|tech stack)$", re.I), "Skills"),
    (re.compile(r"^(work experience|professional experience|experience|employment|employment history)$", re.I), "Experience"),
    (re.compile(r"^(projects|project experience|personal projects|academic projects)$", re.I), "Projects"),
    (re.compile(r"^(education|academics|qualifications|educational qualifications)$", re.I), "Education"),
    (re.compile(r"^(certifications?|achievements?|awards?|honors?|publications?|interests?|hobbies|languages|extra.?curricular|volunteer.*)$", re.I), "Other"),
]
_HEADER_STRIP = re.compile(r"^[\s\-–—*•·#>]+|[\s:–—-]+$")


def _is_header(line: str) -> str | None:
    cleaned = _HEADER_STRIP.sub("", line.strip())
    if not cleaned or len(cleaned) > 45:
        return None
    for pat, name in _SECTION_PATTERNS:
        if pat.match(cleaned):
            return name
    # "Skills: python, sql" — header label with inline content on the same line.
    if ":" in line:
        label = _HEADER_STRIP.sub("", line.split(":", 1)[0].strip())
        if label and len(label) <= 45:
            for pat, name in _SECTION_PATTERNS:
                if pat.match(label):
                    return name
    return None


_EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")


def _extract_email(text: str) -> str | None:
    """First plausible email in the first 3k chars (contact block). Lowercased."""
    m = _EMAIL_RE.search(text[:3000])
    return m.group(0).lower() if m else None


def _extract_name(text: str, filename: str) -> str:
    for line in text.splitlines()[:6]:
        line = line.strip()
        if not line or len(line) > 50:
            continue
        if "@" in line or re.search(r"\d{3,}", line) or "|" in line:
            continue
        words = re.findall(r"[A-Za-z][a-z'’]*", line)
        if 2 <= len(words) <= 5 and sum(1 for w in words if w[0].isupper()) >= 2:
            return re.sub(r"\s+", " ", line)
    return re.sub(r"[_.-]+", " ", filename.rsplit(".", 1)[0]).strip().title() or "Unknown"


def _pdf_text(data: bytes, filename: str) -> tuple[str, str | None]:
    text = ""
    try:
        import pdfplumber
        with pdfplumber.open(io.BytesIO(data)) as pdf:
            text = "\n".join((page.extract_text() or "") for page in pdf.pages)
    except Exception:
        try:
            from pypdf import PdfReader
            text = "\n".join((p.extract_text() or "") for p in PdfReader(io.BytesIO(data)).pages)
        except Exception:
            text = ""                      # fall through: the sniff below decides
    if len(text.strip()) < 40:
        # Little or no PDF-layer text: either a mislabeled plain-text file or an
        # image scan. Sniff the raw bytes to tell them apart.
        plain = data.decode("utf-8", errors="ignore")
        printable = sum(1 for c in plain if c.isprintable() or c == "\n") / max(1, len(plain))
        if len(plain.strip()) >= 40 and printable > 0.8:
            return plain, "file named .pdf but content is not a PDF — parsed as plain text"
        if not text.strip():
            return text, f"could not parse PDF: {filename}"
        return text, "low text extracted — possible image scan; scored on available text"
    return text, None


def _docx_text(data: bytes) -> str:
    import docx
    d = docx.Document(io.BytesIO(data))
    parts = [p.text for p in d.paragraphs if p.text.strip()]
    for table in d.tables:
        for row in table.rows:
            parts.append(" | ".join(c.text for c in row.cells if c.text.strip()))
    return "\n".join(parts)


def _xml_html_text(data: bytes) -> str:
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(data.decode("utf-8", errors="replace"), "lxml")
    return soup.get_text(separator="\n")


def extract_text(data: bytes, filename: str) -> tuple[str, str | None]:
    """Bytes + filename -> (text, warning). Sniffs content first, trusts extension second."""
    fname = (filename or "").lower()
    if data[:4] == b"%PDF" or fname.endswith(".pdf"):
        return _pdf_text(data, filename)
    if data[:2] == b"PK" or fname.endswith((".docx", ".odt")):
        try:
            return _docx_text(data), None
        except Exception:
            pass
    if data[:8] == b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1" or fname.endswith(".doc"):
        # Legacy binary Word: best-effort printable-ASCII strip.
        text = data.decode("utf-8", errors="ignore")
        text = re.sub(r"[^\x20-\x7E\n]+", " ", text)
        text = re.sub(r"[ ]{3,}", " ", text).strip()
        return text, "legacy .doc format — partial text extraction"
    stripped = data.lstrip()
    if stripped[:5] == b"<?xml" or stripped[:1] == b"<" or fname.endswith((".xml", ".html", ".htm")):
        return _xml_html_text(data), None
    return data.decode("utf-8", errors="replace"), None


def split_sections(text: str) -> list[ResumeSection]:
    sections: list[ResumeSection] = []
    current_name, current_lines = "Header", []
    for line in text.splitlines():
        header = _is_header(line)
        if header:
            if any(l.strip() for l in current_lines):
                sections.append(ResumeSection(current_name, "\n".join(current_lines).strip()))
            current_name, current_lines = header, []
            # Keep inline content that followed the label ("Skills: python, sql").
            inline = line.split(":", 1)[1].strip() if ":" in line else ""
            if inline:
                current_lines.append(inline)
        else:
            current_lines.append(line)
    if any(l.strip() for l in current_lines):
        sections.append(ResumeSection(current_name, "\n".join(current_lines).strip()))
    # Drop a tiny pre-first-header block (usually just the name line).
    if sections and sections[0].name == "Header" and len(sections[0].text) < 60:
        sections.pop(0)
    if not sections:
        sections = [ResumeSection("Full Text", text)]
    return sections


def parse_resume(file_bytes: bytes, filename: str) -> ResumeData:
    text, warning = extract_text(file_bytes, filename)
    text = re.sub(r"[ \t]+", " ", text)
    return ResumeData(
        name=_extract_name(text, filename),
        file=filename,
        sections=split_sections(text),
        full_text=text,
        parse_warning=warning,
        email=_extract_email(text),
    )
