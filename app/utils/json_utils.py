def build_extraction_prompt(raw_text: str) -> str:
    return f"""
You are an information extraction system for scheduling.

Extract scheduling constraints from the text below.

Return ONLY a valid JSON object with this EXACT structure:

{{
  "job_type": "workforce_schedule",
  "entities": {{
    "employees": [
      {{
        "name": "string",
        "skills": ["string"],
        "availability": ["string"],
        "max_shifts_per_week": 0,
        "cannot_work_with": ["string"]
      }}
    ],
    "shifts": [
      {{
        "id": "string",
        "day": "string",
        "time": "string",
        "location": "string",
        "required_skills": ["string"],
        "min_staff": 1,
        "max_staff": 1
      }}
    ]
  }},
  "constraints": {{
    "hard_constraints": ["string"],
    "soft_constraints": ["string"],
    "cannot_work_with_pairs": [["employee name", "employee name"]]
  }},
  "edges": [
    {{
      "source": "employee name",
      "target": "employee name",
      "type": "cannot_work_with"
    }}
  ]
}}

STRICT RULES:
- Output MUST be valid JSON
- Do NOT include markdown
- Do NOT include explanations or text outside JSON
- Do NOT invent employees, shifts, or constraints
- If information is missing, use empty lists [] or null
- All keys must be present exactly as shown
- Use lowercase strings for values

NORMALIZATION RULES:
- Days -> lowercase (monday, tuesday, ...)
- Times -> preserve explicit time ranges when present, e.g. "09:00-13:00"; otherwise use simple labels (morning, afternoon, evening, night)
- Skills -> lowercase with underscores instead of spaces (e.g., "front_desk", "system_cert_a")
- Locations -> preserve apartment/building names from shift sentences, e.g. "apt_a", "apt_b"
- Cannot-work-together constraints -> include explicit pairs in constraints.cannot_work_with_pairs
- Relationship edges -> include cannot-work-together relationships in edges using type "cannot_work_with"

IF NO SCHEDULING INFORMATION IS FOUND, RETURN:
{{
  "job_type": "workforce_schedule",
  "entities": {{
    "employees": [],
    "shifts": []
  }},
  "constraints": {{
    "hard_constraints": [],
    "soft_constraints": [],
    "cannot_work_with_pairs": []
  }},
  "edges": []
}}

Text:
\"\"\"{raw_text}\"\"\"
""".strip()
