from typing import Dict, Any

def ocr_and_extract(file_bytes: bytes, filename: str, doc_type: str) -> Dict[str, Any]:
    return {
        "docType": doc_type,
        "source": "stub",
        "filename": filename,
        "extracted": {
            "note": "OCR not yet enabled. Connect AWS Textract/Google Vision."
        },
        "confidence": 0.0,
    }
