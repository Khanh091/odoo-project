NULLABLE_STRING = {"type": ["string", "null"]}


def _object_array(properties):
    return {
        "type": "array",
        "items": {
            "type": "object",
            "properties": properties,
            "required": list(properties),
            "additionalProperties": False,
        },
    }


CANDIDATE_JSON_SCHEMA = {
    "type": "object",
    "properties": {
        "full_name": NULLABLE_STRING,
        "email": NULLABLE_STRING,
        "phone": NULLABLE_STRING,
        "current_position": NULLABLE_STRING,
        "location": NULLABLE_STRING,
        "summary": NULLABLE_STRING,
        "skills": {"type": "array", "items": {"type": "string"}},
        "education": _object_array(
            {
                "school": NULLABLE_STRING,
                "degree": NULLABLE_STRING,
                "major": NULLABLE_STRING,
                "start_date": NULLABLE_STRING,
                "end_date": NULLABLE_STRING,
                "description": NULLABLE_STRING,
            }
        ),
        "experiences": _object_array(
            {
                "company": NULLABLE_STRING,
                "position": NULLABLE_STRING,
                "start_date": NULLABLE_STRING,
                "end_date": NULLABLE_STRING,
                "description": NULLABLE_STRING,
            }
        ),
        "certifications": _object_array(
            {
                "name": NULLABLE_STRING,
                "issuer": NULLABLE_STRING,
                "issued_date": NULLABLE_STRING,
            }
        ),
        "languages": _object_array(
            {"name": NULLABLE_STRING, "level": NULLABLE_STRING}
        ),
        "links": {
            "type": "object",
            "properties": {
                "linkedin": NULLABLE_STRING,
                "github": NULLABLE_STRING,
                "portfolio": NULLABLE_STRING,
            },
            "required": ["linkedin", "github", "portfolio"],
            "additionalProperties": False,
        },
        "warnings": {"type": "array", "items": {"type": "string"}},
    },
    "required": [
        "full_name",
        "email",
        "phone",
        "current_position",
        "location",
        "summary",
        "skills",
        "education",
        "experiences",
        "certifications",
        "languages",
        "links",
        "warnings",
    ],
    "additionalProperties": False,
}
