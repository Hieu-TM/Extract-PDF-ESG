import fitz  # PyMuPDF
import pdfplumber
from typing import List, Dict, Any, Tuple

def extract_text_and_bboxes_pymupdf(pdf_path: str) -> List[Dict[str, Any]]:
    """
    Extract text and bounding boxes using PyMuPDF.
    Returns a list of dicts, one per page.
    """
    doc = fitz.open(pdf_path)
    pages_data = []
    
    for page_num in range(len(doc)):
        page = doc[page_num]
        
        # Get structured blocks (text, bbox)
        blocks = page.get_text("blocks")
        text_blocks = []
        full_text = []
        for b in blocks:
            # b = (x0, y0, x1, y1, "text", block_no, block_type)
            if b[6] == 0:  # 0 indicates text
                text_content = b[4].strip()
                if text_content:
                    text_blocks.append({
                        "bbox": [b[0], b[1], b[2], b[3]],
                        "text": text_content
                    })
                    full_text.append(text_content)
        
        pages_data.append({
            "page": page_num + 1,
            "text": "\n".join(full_text),
            "blocks": text_blocks
        })
    
    doc.close()
    return pages_data

def extract_tables_pdfplumber(pdf_path: str, pages: List[int] = None) -> Dict[int, List[List[List[str]]]]:
    """
    Extract tabular data using pdfplumber to provide additional structure.
    pages parameter is 1-indexed. Returns dict mapped by 1-indexed page.
    """
    results = {}
    with pdfplumber.open(pdf_path) as pdf:
        num_pages = len(pdf.pages)
        pages_to_extract = pages if pages else range(1, num_pages + 1)
        
        for p_idx in pages_to_extract:
            if p_idx < 1 or p_idx > num_pages:
                continue
            page = pdf.pages[p_idx - 1]
            tables = page.extract_tables()
            if tables:
                results[p_idx] = tables
                
    return results
