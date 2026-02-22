import re
from typing import List, Dict, Any
import logging
from utils.pdf_utils import extract_text_and_bboxes_pymupdf

logger = logging.getLogger(__name__)

# Keywords indicating potential ESG data presence
ESG_KEYWORDS = [
    r"scope\s*1", r"scope\s*2", r"scope\s*3",
    r"revenue", r"turnover", r"financials",
    r"emissions", r"ghg", r"carbon", r"co2",
    r"millions", r"billions", r"€", r"\$", r"£"
]

class LayoutAgent:
    """
    LayoutAgent focuses on scanning a document's layout, extracting raw text,
    identifying structured content (bounding boxes, tables), and filtering out
    pages that likely lack relevant ESG data to reduce token context size.
    """
    
    def __init__(self, pdf_path: str):
        self.pdf_path = pdf_path
        self.pages_data = []

    def run(self) -> List[Dict[str, Any]]:
        logger.info(f"Running Layout Agent on: {self.pdf_path}")
        self.pages_data = extract_text_and_bboxes_pymupdf(self.pdf_path)
        
        # Identify candidate pages using regex heuristics
        candidate_pages = []
        for page in self.pages_data:
            text = page["text"].lower()
            match_count = sum(1 for kw in ESG_KEYWORDS if re.search(kw, text))
            page["keyword_score"] = match_count
            
            # Simple threshold: at least 1 keyword from the list.
            if match_count > 0:
                candidate_pages.append(page)
        
        logger.info(f"Identified {len(candidate_pages)} candidate pages out of {len(self.pages_data)}")
        
        # Sort candidate pages by keyword density (top 20)
        candidate_pages = sorted(candidate_pages, key=lambda x: x["keyword_score"], reverse=True)
        # Limiting to a reasonable number to avoid LLM token overflow, while including high priority pages
        selected = candidate_pages[:20] 
        selected = sorted(selected, key=lambda x: x["page"]) # Keep it in logical reading order
        
        return selected

