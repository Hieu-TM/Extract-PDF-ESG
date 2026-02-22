import logging
import json
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

class VerificationAgent:
    """
    Synthesizes the extraction and normalization data into the final Audit/Verification JSON structure
    while attaching metadata like confidence and extraction method.
    """
    
    def __init__(self, normalized_data: Dict[str, Any], candidate_pages: List[Dict[str, Any]]):
        self.data = normalized_data
        self.pages = candidate_pages

    def _find_bbox(self, text_snippet: str, page_num: int) -> List[float]:
        if not text_snippet or not page_num:
            return None
            
        for p in self.pages:
            if p["page"] == page_num:
                for block in p.get("blocks", []):
                    if text_snippet.lower() in block["text"].lower() or block["text"].lower() in text_snippet.lower():
                        return block["bbox"]
        return None

    def _compute_confidence(self, val_obj: Dict[str, Any]) -> float:
        # Heuristic confidence calculation
        if val_obj is None or val_obj.get("value") is None:
            return 0.0
            
        score = 0.5 # Base score for LLM returning a value
        
        # Increment if it provided clear reasoning
        if val_obj.get("reasoning_summary"):
            score += 0.2
            
        # Increment if found on a specific page
        if val_obj.get("page"):
            score += 0.2
            
        score = min(score, 1.0)
        return score

    def build_verification_json(self) -> Dict[str, Any]:
        logger.info("Building Verification JSON")
        audit_trail = {}
        
        if not self.data:
            return audit_trail
            
        for metric_name, metric_data in self.data.items():
            if metric_name in ["reporting_year", "currency", "scope_3_reporting_categories_y0"]:
                audit_trail[metric_name] = {"value": metric_data}
                continue
            
            for period in ["y0", "y0_1", "y0_2"]:
                field_key = f"{metric_name}_{period}"
                val_obj = metric_data.get(period)
                
                if val_obj and val_obj.get("value") is not None:
                    bbox = self._find_bbox(val_obj.get("raw_text"), val_obj.get("page"))
                    
                    audit_record = {
                        "value": val_obj.get("value"),
                        "unit": val_obj.get("unit"),
                        "page": val_obj.get("page"),
                        "source_type": val_obj.get("source_type"),
                        "bbox": bbox,
                        "raw_text": val_obj.get("raw_text"),
                        "normalized_value": val_obj.get("normalized_value"),
                        "confidence": self._compute_confidence(val_obj),
                        "extraction_method": "LLM Structured Output (gpt-4o) + Normalization",
                        "reasoning_summary": val_obj.get("reasoning_summary")
                    }
                    audit_trail[field_key] = audit_record
                    
        return audit_trail
