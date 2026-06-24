PROMPTS = {
    "startup": """
Extract structured data from the following text about a startup.
Return ONLY valid JSON. If a field is not found, use null.
NEVER guess or hallucinate values.

Text:
{text}

Return this exact JSON structure:
{{
  "schemaVersion": "1.0",
  "recordType": "STARTUP",
  "source": {{"name": null, "url": null}},
  "content": {{
    "entityName": null,
    "data": {{
      "description": null,
      "foundedYear": null,
      "employeeCount": null,
      "location": null,
      "website": null,
      "fundingTotal": null
    }}
  }},
  "collectedAt": null
}}
""",

    "product": """
Extract structured data from the following text about an AI product.
Return ONLY valid JSON. If a field is not found, use null.
NEVER guess or hallucinate values.

For pricingModel, only use one of: FREE, FREEMIUM, PAID, ENTERPRISE
If pricing is unclear, use null.

Text:
{text}

Return this exact JSON structure:
{{
  "schemaVersion": "1.0",
  "recordType": "PRODUCT",
  "source": {{"name": null, "url": null}},
  "content": {{
    "productName": null,
    "startupName": null,
    "description": null,
    "pricingModel": null,
    "website": null,
    "category": null
  }},
  "collectedAt": null
}}
""",

    "job": """
Extract structured job data from the following text.
Return ONLY valid JSON. If a field is not found, use null.
NEVER guess or hallucinate values.

For role_family, use one of: Engineering, Research, Product, Design, Marketing, Sales, Operations, Other

Text:
{text}

Return this exact JSON structure:
{{
  "schemaVersion": "1.0",
  "recordType": "JOB",
  "content": {{
    "company": null,
    "role_title": null,
    "role_family": null,
    "date": null,
    "is_remote": null,
    "location": null,
    "salary_range": null
  }},
  "collectedAt": null
}}
"""
}
