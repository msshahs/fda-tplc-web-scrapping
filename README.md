# FDA Device & Patient Problem Extraction API

A FastAPI service that automates data collection from the FDA's Total Product Life Cycle (TPLC) device database and returns device and patient problems with MAUDE links.


## Setup

### 1) Clone & set up env

```bash
python -m venv .venv && source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python -m playwright install chromium
```

### 2) Run the API

```bash
uvicorn main:app --reload --port 8000
```

Visit Swagger UI: http://localhost:8000/docs

### 3) Try it

In the Swagger UI, try a query like:

- `device_name = syringe`
- `product_code = DXT` (optional)
- `min_year = 2020`

Or curl:

```bash
curl "http://localhost:8000/scrape?device_name=syringe&min_year=2020"
```

## Example output (truncated)

```json
{
  "query": {"device_name": "syringe", "product_code": null, "min_year": 2020},
  "results": [
    {
      "device_name": "Device injector and syringe, angiographic",
      "product_code": "DXT",
      "regulation_number": "870.1650",
      "tplc_url": "https://www.accessdata.fda.gov/...tplc.cfm?id=2716&min_report_year=2020",
      "device_problems": [
        {
          "name": "Adverse Event Without Identified Device or Use Problem",
          "mdr_reports": 220,
          "events": 220,
          "maude_url": "https://www.accessdata.fda.gov/...productproblem=2993&productcode=DXT&reportdatefrom=01/1/2020"
        }
      ],
      "patient_problems": [
        {
          "name": "Air Embolism",
          "mdr_reports": 168,
          "events": 168,
          "maude_url": "https://www.accessdata.fda.gov/..."
        }
      ]
    }
  ]
}
```

