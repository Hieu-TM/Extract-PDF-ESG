import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

class NormalizationAgent:
    """
    Standardizes numerical formats, converts string numbers to floats,
    and applies base multipliers (millions, billions).
    """

    def __init__(self, raw_data: Dict[str, Any]):
        self.data = raw_data

    def _normalize_metric(self, metric: Dict[str, Any], is_financial: bool) -> Dict[str, Any]:
        if not metric:
            return metric
        
        for k in ["y0", "y0_1", "y0_2"]:
            val_obj = metric.get(k)
            if val_obj and isinstance(val_obj, dict):
                raw_val = val_obj.get("value")
                unit = val_obj.get("unit") or ""
                
                if raw_val is not None:
                    # Normally LLM returns float directly, but if we need magnitude scaling:
                    text_unit = str(unit).lower()
                    
                    if "billion" in text_unit or "bn" in text_unit or "b" == text_unit.strip():
                        val_obj["normalized_value"] = raw_val * 1_000_000_000
                    elif "million" in text_unit or "m" == text_unit.strip():
                        val_obj["normalized_value"] = raw_val * 1_000_000
                    elif "thousand" in text_unit or "k" in text_unit:
                        val_obj["normalized_value"] = raw_val * 1_000
                    else:
                        val_obj["normalized_value"] = raw_val
                        
                    # If it's revenue, we want everything in millions typically for CSV, or base
                    # If we convert to millions:
                    if is_financial and val_obj["normalized_value"] is not None:
                        # Depending on requirements, maybe standardize to base units always
                        pass
                else:
                    val_obj["normalized_value"] = None
                    
        return metric

    def run(self) -> Dict[str, Any]:
        logger.info("Running Normalization Agent")
        if not self.data:
            return {}

        norm_data = dict(self.data)
        
        # Financial metric
        if "revenue" in norm_data:
            norm_data["revenue"] = self._normalize_metric(norm_data["revenue"], is_financial=True)
            
        # Environmental metrics
        for scope in ["co2_scope_1", "co2_scope_2", "co2_scope_3"]:
            if scope in norm_data:
                norm_data[scope] = self._normalize_metric(norm_data[scope], is_financial=False)
                
        return norm_data

