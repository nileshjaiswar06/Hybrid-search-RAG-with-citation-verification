from pathlib import Path

from reportlab.pdfgen import canvas

from app.ingestion.loader import PDFLoader
from app.ingestion.parser import PDFParser

from app.ingestion.parser import normalize_text

import pytest

def test_missing_file():
    loader = PDFLoader()

    with pytest.raises(FileNotFoundError):
        loader.load("does-not-exist.pdf")

def test_non_pdf_file(tmp_path):
    file_path = tmp_path / "document.txt"
    file_path.write_text("hello")

    loader = PDFLoader()

    with pytest.raises(ValueError):
        loader.load(file_path)

def test_normalize_text():
    raw = """
        Hello world.

        
        This is a test.
        
    """

    result = normalize_text(raw)

    assert result == (
        "Hello world.\n"
        "This is a test."
    )

def create_test_pdf(path: Path) -> None:
    pdf = canvas.Canvas(str(path))

    pdf.drawString(
        100,
        750,
        "Hybrid RAG Test Document",
    )

    pdf.drawString(
        100,
        730,
        "Employees receive 24 days of annual leave.",
    )

    pdf.showPage()

    pdf.drawString(
        100,
        750,
        "Second page of the test document.",
    )

    pdf.save()


def test_pdf_parser(tmp_path):
    pdf_path = tmp_path / "test.pdf"

    create_test_pdf(pdf_path)

    loader = PDFLoader()
    parser = PDFParser()

    pdf = loader.load(pdf_path)

    try:
        document = parser.parse(
            pdf,
            pdf_path,
        )
    finally:
        pdf.close()

    assert document.filename == "test.pdf"
    assert document.page_count == 2
    assert len(document.pages) == 2

    assert (
        "Employees receive 24 days"
        in document.pages[0].text
    )

    assert document.pages[0].page_number == 1
    assert document.pages[1].page_number == 2

    assert len(document.file_hash) == 64