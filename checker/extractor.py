import os
import docx
import PyPDF2


def extract_text_from_file(file) -> str:
    """
    Accepts an uploaded file object.
    Detects type by extension and extracts plain text.
    """
    name = file.name.lower()

    if name.endswith('.txt'):
        return extract_from_txt(file)
    elif name.endswith('.pdf'):
        return extract_from_pdf(file)
    elif name.endswith('.docx'):
        return extract_from_docx(file)
    else:
        raise ValueError(f"Unsupported file type: {name}. Use PDF, DOCX, or TXT.")


def extract_from_txt(file) -> str:
    try:
        content = file.read()
        # Try UTF-8 first, fallback to latin-1
        try:
            return content.decode('utf-8').strip()
        except UnicodeDecodeError:
            return content.decode('latin-1').strip()
    except Exception as e:
        raise ValueError(f"Could not read TXT file: {e}")


def extract_from_pdf(file) -> str:
    try:
        reader = PyPDF2.PdfReader(file)
        text = ''
        for page in reader.pages:
            extracted = page.extract_text()
            if extracted:
                text += extracted + '\n'

        if not text.strip():
            raise ValueError("PDF appears to be scanned or image-based. No text found.")

        return text.strip()
    except Exception as e:
        raise ValueError(f"Could not read PDF file: {e}")


def extract_from_docx(file) -> str:
    try:
        doc = docx.Document(file)
        paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
        text = '\n'.join(paragraphs)

        if not text.strip():
            raise ValueError("DOCX file appears to be empty.")

        return text.strip()
    except Exception as e:
        raise ValueError(f"Could not read DOCX file: {e}")