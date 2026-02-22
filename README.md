# ESG Extraction Agent Pipeline

This repository implements a production-grade, deterministic, and audit-ready data pipeline to extract Environmental, Social, and Governance (ESG) metrics from PDF reports.

## Architecture

The system utilizes a multi-agent multi-step strategy:
1. **Layout Agent**: Parses raw text and bounding boxes using `PyMuPDF`. Filters documents efficiently using Regex to select high-value ESG candidate pages.
2. **Extraction Agent**: Batches page contexts to an LLM via the OpenAI API using strictly typed structured output via `pydantic`.
3. **Normalization Agent**: Standardizes numbers and translates multipliers (e.g. millions, bn) to base integers/floats.
4. **Verification Agent**: Builds an audit trail JSON linking the specific extracted value with its original text, confidence rating, source type, and reasoning mapping back to the extracted PDF.

## Requirements

Python 3.9+ is recommended. 
To install the requirements:

```bash
# Set up a virtual environment
python -m venv .venv

# Activate it
# On Windows:
.venv\Scripts\activate
# On Linux/Mac:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

## LLM Configuration

The project utilizes `openai` module to parse contexts deterministically.

You must set up an environment variable with your API key:
```bash
# Windows
set OPENAI_API_KEY=sk-your-key-here
# Linux/Mac
export OPENAI_API_KEY=sk-your-key-here
```

By default it uses `gpt-4o` for maximum reasoning structure, but it can be changed to smaller models (e.g. `gpt-4o-mini`) in `extract.py`.

## Determinism Details

Determinism is prioritized and enforced through:
1. **Zero Temperature**: `temperature=0` is hardcoded into the `ExtractionAgent` LLM call.
2. **Pydantic Schemas**: Responses are forced recursively into expected types, rejecting unexpected string responses in numerical fields.
3. **Regex Cleaners**: Post-processing pipelines in `utils.number_utils` strip comma and period variations strictly.

## Output Formats
### Verification JSON Standard
Outputs will follow exactly the requested deterministic JSON standard. This is saved as the 3rd argument you specify on the CLI. It details reasoning, source text, bounding boxes, and computed confidence ranges.

### Structured Output CSV
Values map exactly to the provided `output.csv` template style. It will append to the current `output.csv` automatically if one exists, matching the column schemas precisely.

## CLI Usage

Run the agent passing the target PDF, the output CSV file, and the output verification path:

```bash
python extract.py sample-1.pdf output.csv verification.json
```
