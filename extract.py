import os
import sys
import json
import logging
import argparse
import pandas as pd
from jsonschema import validate, ValidationError

from agents.layout_agent import LayoutAgent
from agents.extraction_agent import ExtractionAgent, ESGExtraction
from agents.normalization_agent import NormalizationAgent
from agents.verification_agent import VerificationAgent

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_schema(schema_path: str):
    with open(schema_path, 'r') as f:
        return json.load(f)

def clean_missing(val):
    if val is None or val == "None" or str(val).strip().upper() == "N/A" or pd.isna(val):
        return "N/A"
    return val

def format_comma(val):
    if val == "N/A":
        return val
    try:
        if isinstance(val, (int, float)):
            return f"{val:,.0f}" if val == int(val) else f"{val:,.2f}"
    except:
        pass
    return val

def extract_pipeline(pdf_path: str, output_csv: str, verification_json: str):
    logger.info(f"Starting Extraction Pipeline for {pdf_path}")
    
    company_name = os.path.basename(pdf_path)
    if not os.path.exists(pdf_path):
        logger.error(f"File not found: {pdf_path}")
        sys.exit(1)
        
    # --- 1. Layout Agent ---
    layout_agent = LayoutAgent(pdf_path)
    candidate_pages = layout_agent.run()
    
    if not candidate_pages:
        logger.warning("No candidate pages found. Aborting.")
        sys.exit(0)

    # --- 2. Extraction Agent ---
    extractor = ExtractionAgent(candidate_pages, pdf_path)
    raw_data = extractor.run()
    
    # --- 3. Normalization Agent ---
    normalizer = NormalizationAgent(raw_data)
    normalized_data = normalizer.run()

    # --- 4. Verification Agent ---
    verifier = VerificationAgent(normalized_data, candidate_pages)
    audit_data = verifier.build_verification_json()
    
    # Output Verification JSON
    with open(verification_json, 'w') as f:
        json.dump(audit_data, f, indent=2)
    logger.info(f"Saved verification log to {verification_json}")
    
    # Validate against Schema
    schema_path = os.path.join(os.path.dirname(__file__), "schemas", "esg_schema.json")
    if os.path.exists(schema_path):
        try:
            # We must map our complex structure to the simple schema requested in Step 3
            simple_data = {
                "reporting_year": normalized_data.get("reporting_year"),
                "currency": normalized_data.get("currency"),
                "revenue": {k: v["normalized_value"] for k, v in normalized_data.get("revenue", {}).items() if v},
                "co2_scope_1": {k: v["normalized_value"] for k, v in normalized_data.get("co2_scope_1", {}).items() if v},
                "co2_scope_2": {k: v["normalized_value"] for k, v in normalized_data.get("co2_scope_2", {}).items() if v},
                "co2_scope_3": {k: v["normalized_value"] for k, v in normalized_data.get("co2_scope_3", {}).items() if v}
            }
            # Provide missing keys for validation
            for k in ["revenue", "co2_scope_1", "co2_scope_2", "co2_scope_3"]:
                if k not in simple_data: simple_data[k] = {}
                for y in ["y0", "y0_1", "y0_2"]:
                    if y not in simple_data[k]: simple_data[k][y] = None
                    
            schema = load_schema(schema_path)
            validate(instance=simple_data, schema=schema)
            logger.info("JSON Schema validation passed.")
        except ValidationError as e:
            logger.error(f"JSON Schema validation failed: {e}")
    else:
        logger.warning(f"Schema not found at {schema_path}, skipping validation.")

    # --- Format to CSV Format ---
    def get_val(metric, period):
        obj = normalized_data.get(metric, {}).get(period, {})
        return obj.get("normalized_value") if isinstance(obj, dict) else None
        
    def get_rev_millions(period):
        val = get_val("revenue", period)
        if val is not None:
             return val / 1_000_000.0
        return None

    def format_val(val):
        # We want missing or NaN to be blank, not "N/A" per the output_expected.csv columns
        if val is None or val == "N/A" or pd.isna(val):
            return ""
        try:
            if isinstance(val, (int, float)):
                return f"{val:,.0f}" if val == int(val) else f"{val:,.2f}"
        except:
            pass
        return val

    # Reporting year explicitly stripped of .0 if possible
    rep_year = clean_missing(normalized_data.get("reporting_year"))
    if isinstance(rep_year, float) and rep_year.is_integer():
        rep_year = int(rep_year)
    elif rep_year == "N/A":
        rep_year = ""

    # Scope 3 reporting categories explicitly stripped of .0 if possible
    s3_cats = normalized_data.get("scope_3_reporting_categories_y0")
    if s3_cats is not None:
        if isinstance(s3_cats, float) and s3_cats.is_integer():
            s3_cats = int(s3_cats)
    else:
        s3_cats = ""

    curr = clean_missing(normalized_data.get("currency"))
    if curr == "N/A": curr = ""

    row = {
        "Company name": company_name,
        "Most recent reporting year": rep_year,
        "Financial year end": "31-Dec",
        
        "Y0-Revenue / Turnover (million)": format_val(get_rev_millions("y0")),
        "Y0-Currency": curr,
        " Y0-CO2 Scope 1 \n(tCO2e)  ": format_val(get_val("co2_scope_1", "y0")),
        " Y0-CO2 Scope 2 - market based\n(tCO2e)  ": format_val(get_val("co2_scope_2", "y0")),
        " Y0-CO2 Scope 3\n(tCO2e) ": format_val(get_val("co2_scope_3", "y0")),
        " Y0-Scope 3 reporting categories - (0-15) ": s3_cats,
        
        "Y0-1-Revenue / Turnover (million)": format_val(get_rev_millions("y0_1")),
        " Y0-1-CO2 Scope 1 \n(tCO2e)  ": format_val(get_val("co2_scope_1", "y0_1")),
        " Y0-1-CO2 Scope 2 - market based\n(tCO2e)  ": format_val(get_val("co2_scope_2", "y0_1")),
        " Y0-1-CO2 Scope 3\n(tCO2e) ": format_val(get_val("co2_scope_3", "y0_1")),
        
        "Y0-2-Revenue / Turnover (million)": format_val(get_rev_millions("y0_2")),
        " Y0-2-CO2 Scope 1 \n(tCO2e)  ": format_val(get_val("co2_scope_1", "y0_2")),
        " Y0-2-CO2 Scope 2 - market based\n(tCO2e)  ": format_val(get_val("co2_scope_2", "y0_2")),
        " Y0-2-CO2 Scope 3\n(tCO2e) ": format_val(get_val("co2_scope_3", "y0_2")),
    }

    df_new = pd.DataFrame([row])
    
    if os.path.exists(output_csv):
        df_existing = pd.read_csv(output_csv, dtype=str) # Read as string to preserve exact blanks
        # Drop if same company exists to replace:
        df_existing = df_existing[df_existing["Company name"] != company_name]
        df_combined = pd.concat([df_existing, df_new], ignore_index=True)
    else:
        df_combined = df_new

    # Write without dropping .0 by avoiding automatic NaN float upcasting
    df_combined.fillna("").to_csv(output_csv, index=False)
    logger.info(f"Appended new data to {output_csv}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Deterministic ESG Extraction Agent")
    parser.add_argument("input_pdf", type=str, help="Path to input PDF")
    parser.add_argument("output_csv", type=str, help="Path to output CSV")
    parser.add_argument("verification_json", type=str, help="Path to verification JSON")
    
    args = parser.parse_args()
    
    # Make sure OpenAI key is present
    if not os.environ.get("OPENAI_API_KEY"):
        logger.error("OPENAI_API_KEY environment variable is not set. The LLM extraction will fail unless using a local endpoint mapped to base_url.")
    
    extract_pipeline(args.input_pdf, args.output_csv, args.verification_json)
