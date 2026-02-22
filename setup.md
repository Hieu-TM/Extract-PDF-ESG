# ESG Extraction Agent – Production-Grade Setup (Revised)

You are a Senior AI Systems Engineer and Data Engineer building a **production-grade, audit-ready ESG extraction pipeline**.

The system must extract ESG metrics from PDF reports and output **two files per PDF**:

1. **Structured Output (CSV or JSON)** – Deterministic, validated ESG values.
2. **Verification JSON** – Full audit trail with metadata for every extracted field.

---

# 1. System Architecture (Mandatory Multi-Agent Design)

The solution must follow a modular, agent-based architecture:

## 1.1 Agents

### 1️⃣ Layout Agent
- Extract all text blocks and tables using:
  - PyMuPDF or pdfplumber
  - camelot or tabula-py
- Detect candidate pages containing:
  - Revenue
  - Currency
  - CO2 Scope 1/2/3
- Output structured page-level content.

### 2️⃣ Field Extraction Agent
- Use LLM (temperature=0) to extract ALL ESG fields in a single structured call.
- Must follow a strict JSON schema (see Section 3).
- Return:
  - Raw values
  - Units
  - Source page references

### 3️⃣ Normalization Agent
- Convert units (e.g., millions, billions, bn, m).
- Normalize number formats (comma vs dot separators).
- Enforce numeric type validation.
- Align multi-year values (Y0, Y0-1, Y0-2).

### 4️⃣ Verification Agent
- Attach metadata:
  - Page number
  - Bounding box (if available)
  - Raw snippet
  - Extraction method
  - Confidence score
  - Reasoning summary
- Ensure traceability for audit review.

---

# 2. Scope of Extraction

Extract all fields from:

`Most recent reporting year` → `Y0-2-CO2 Scope 3 (tCO2e)`

Includes:

- Reporting year
- Currency
- Revenue (Y0, Y0-1, Y0-2)
- CO2 Scope 1 (Y0, Y0-1, Y0-2)
- CO2 Scope 2 (Y0, Y0-1, Y0-2)
- CO2 Scope 3 (Y0, Y0-1, Y0-2)

All numeric values must be normalized into consistent base units.

---

# 3. Mandatory ESG JSON Schema

All structured output MUST follow this schema strictly:

```json
{
  "reporting_year": "int",
  "currency": "string",
  "revenue": {
    "y0": "float",
    "y0_1": "float",
    "y0_2": "float"
  },
  "co2_scope_1": {
    "y0": "float",
    "y0_1": "float",
    "y0_2": "float"
  },
  "co2_scope_2": {
    "y0": "float",
    "y0_1": "float",
    "y0_2": "float"
  },
  "co2_scope_3": {
    "y0": "float",
    "y0_1": "float",
    "y0_2": "float"
  }
}
```

Use JSON schema validation before writing final output.

---

# 4. Verification JSON Standard

Each field must include:

```json
{
  "field_name": {
    "value": 12345,
    "unit": "tCO2e",
    "page": 17,
    "source_type": "table | paragraph",
    "bbox": [x1, y1, x2, y2],
    "raw_text": "original snippet",
    "normalized_value": 12345,
    "confidence": 0.93,
    "extraction_method": "regex + LLM",
    "reasoning_summary": "Matched Scope 1 emissions row"
  }
}
```

Confidence must be calculated using:

- Source consistency check
- Regex validation
- LLM extraction agreement

---

# 5. Determinism Requirements

- LLM temperature must be 0.
- All outputs must be schema-validated.
- If multiple candidates are found:
  - Prefer table over paragraph.
  - Prefer consolidated ESG table.
  - Log ambiguity in verification JSON.

---

# 6. Performance Optimization

- Extract entire PDF text once.
- Batch all ESG extraction into a single LLM call.
- Cache LLM responses locally.
- Avoid per-field LLM calls.

---

# 7. Edge Case Handling (Mandatory)

Handle the following cases:

- Currency defined once globally.
- Revenue expressed as €3.5bn, 3,500 million, etc.
- Scope 2 market-based vs location-based.
- Duplicate values across multiple pages.
- Infographic-style data (non-table format).

---

# 8. Logging & Error Handling

- Log every step.
- Capture failed extractions.
- Provide retry mechanism for LLM call.
- Validate numeric ranges.

---

# 9. File Structure

```
project/
│
├── extract.py
├── agents/
│   ├── layout_agent.py
│   ├── extraction_agent.py
│   ├── normalization_agent.py
│   ├── verification_agent.py
│
├── schemas/
│   ├── esg_schema.json
│
├── utils/
│   ├── pdf_utils.py
│   ├── number_utils.py
│
├── logs/
├── requirements.txt
└── README.md
```

---

# 10. CLI Entry Point

The script must run as:

```
python extract.py input.pdf output.json verification.json
```

---

# 11. README Requirements

README must include:

- Virtual environment setup
- Dependency installation
- LLM configuration instructions
- How determinism is enforced
- Explanation of verification JSON format
- Known limitations

---

# 12. Evaluation & Validation

Include:

- Comparison script against ground truth CSV
- Accuracy metrics
- Field-level validation report

---

# Final Objective

Build a deterministic, audit-ready, scalable ESG Extraction Agent capable of production deployment in compliance, finance, or regulatory AI systems.

