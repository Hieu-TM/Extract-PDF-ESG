import os
import json
import logging
from typing import List, Dict, Any, Optional, Literal
from pydantic import BaseModel, Field
from openai import OpenAI
from utils.pdf_utils import extract_tables_pdfplumber

logger = logging.getLogger(__name__)

# --- Pydantic Schemas for Structured Output ---

class ExtractedValue(BaseModel):
    value: Optional[float] = Field(description="The extracted numeric value. Use null if not found.")
    raw_text: Optional[str] = Field(description="The exact original text snippet it was extracted from. Max 3-5 words.")
    unit: Optional[str] = Field(description="The context unit (e.g., millions, bn, tCO2e, £). Use null if unknown.")
    page: Optional[int] = Field(description="The page number. Use null if unknown.")
    source_type: Optional[Literal["table", "paragraph", "infographic"]] = Field(description="Format of the data context.")
    reasoning_summary: Optional[str] = Field(description="Brief reasoning on why this was chosen (e.g., 'Matched Scope 1 row for 2022').")

class Metric(BaseModel):
    y0: Optional[ExtractedValue] = Field(description="Reporting year (most recent)")
    y0_1: Optional[ExtractedValue] = Field(description="Previous year (Y-1)")
    y0_2: Optional[ExtractedValue] = Field(description="Two years prior (Y-2)")

class ESGExtraction(BaseModel):
    reporting_year: Optional[int] = Field(description="The most recent reporting year identified (e.g., 2023).")
    currency: Optional[str] = Field(description="Global currency identified for financials (e.g., USD, EUR).")
    revenue: Metric
    co2_scope_1: Metric
    co2_scope_2: Metric
    co2_scope_3: Metric
    scope_3_reporting_categories_y0: Optional[int] = Field(description="The number of Scope 3 reporting categories (from 0 to 15) for Y0.")

# --- Agent Implementation ---

class ExtractionAgent:
    """
    Uses OpenAI's structured outputs to deterministically extract all ESG fields.
    Takes candidate pages and batches them into a single call.
    """
    
    def __init__(self, candidate_pages: List[Dict[str, Any]], pdf_path: str):
        self.candidate_pages = candidate_pages
        self.pdf_path = pdf_path
        self.client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY", ""))

    def run(self) -> Dict[str, Any]:
        logger.info("Running Extraction Agent")
        
        if not self.candidate_pages:
            logger.warning("No candidate pages provided to Extraction Agent.")
            return {}

        # Optionally grab tables for candidate pages to improve tabular reading
        page_nums = [p["page"] for p in self.candidate_pages]
        # Skip plumber parsing if large to save time, but good for robust logic:
        # tables_by_page = extract_tables_pdfplumber(self.pdf_path, page_nums)
        
        # Build prompt context
        context_parts = []
        for p in self.candidate_pages:
            # You could inject table representation here as well for better LLM comprehension
            context_parts.append(f"--- PAGE {p['page']} ---\n{p['text']}\n")
            
        context_string = "\n".join(context_parts)
        
        prompt = (
            "You are an expert ESG Data Extractor. Your task is to extract exact ESG metrics "
            "from the following text. The most recent reporting year is Y0, the previous year is Y0-1, etc. "
            "If multiple candidates are found, prefer tables over paragraphs, prefer consolidated ESG tables. "
            "IMPORTANT: If a value is missing or not explicitly stated, return null.\n\n"
            "CONTEXT:\n"
            f"{context_string}"
        )
        
        try:
            # Note: requires an OpenAI model supporting parse/structured outputs, e.g., gpt-4o-2024-08-06 or newer
            # using 'gpt-4o-mini' for speed/cost.
            response = self.client.beta.chat.completions.parse(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are a precise, deterministic AI extraction pipeline element."},
                    {"role": "user", "content": prompt}
                ],
                response_format=ESGExtraction,
                temperature=0.0 # Determinism requirement
            )
            
            result = response.choices[0].message.parsed
            if result:
                return result.model_dump()
            return {}
        except Exception as e:
            logger.error(f"LLM Extraction failed: {e}")
            return {}
