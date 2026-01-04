import pathlib
from typing import Any

import yaml
from pypdf import PdfReader
from docx import Document


def read_yaml(path: str | pathlib.Path) -> Any:
    """Reads a YAML file."""
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def write_yaml(data: Any, path: str | pathlib.Path) -> None:
    """Writes data to a YAML file."""
    with open(path, "w", encoding="utf-8") as f:
        yaml.dump(data, f, sort_keys=False, allow_unicode=True)


def extract_text_from_file(path: str | pathlib.Path) -> str:
    """Extracts text from PDF, Docx, or TXT file."""
    path = pathlib.Path(path)
    suffix = path.suffix.lower()

    if suffix == ".pdf":
        return _extract_text_from_pdf(path)
    elif suffix == ".docx":
        return _extract_text_from_docx(path)
    elif suffix in [".txt", ".md"]:
        return path.read_text(encoding="utf-8")
    else:
        raise ValueError(f"Unsupported file format: {suffix}")


def _extract_text_from_pdf(path: pathlib.Path) -> str:
    """Extracts text from a PDF file."""
    reader = PdfReader(path)
    text = ""
    for page in reader.pages:
        text += page.extract_text() + "\n"
    return text


def _extract_text_from_docx(path: pathlib.Path) -> str:
    """Extracts text from a Docx file."""
    doc = Document(path)
    return "\n".join([para.text for para in doc.paragraphs])
