from odoo import _, models
from odoo.exceptions import ValidationError

from ..schemas.candidate_schema import (
    COLLECTION_FIELDS,
    LINK_FIELDS,
    STRING_FIELDS,
)

OBJECT_FIELDS = {
    "education": (
        "school",
        "degree",
        "major",
        "start_date",
        "end_date",
        "description",
    ),
    "experiences": (
        "company",
        "position",
        "start_date",
        "end_date",
        "description",
    ),
    "certifications": ("name", "issuer", "issued_date"),
    "languages": ("name", "level"),
}


class CvResultValidator(models.AbstractModel):
    _name = "cv.ai.result.validator"
    _description = "CV AI Result Validator"

    def validate_candidate(self, candidate_data):
        """Validate and normalize candidate data returned by an AI provider."""
        if not isinstance(candidate_data, dict):
            raise ValidationError(_("AI candidate data must be a JSON object."))

        result = {
            field_name: self._clean_string(candidate_data.get(field_name))
            for field_name in STRING_FIELDS
        }
        if result["email"]:
            result["email"] = result["email"].lower()
        if not result["full_name"]:
            raise ValidationError(_("The CV does not contain a candidate name."))

        result["skills"] = self._normalize_string_list(
            candidate_data.get("skills")
        )
        for field_name, keys in OBJECT_FIELDS.items():
            result[field_name] = self._normalize_object_list(
                candidate_data.get(field_name), keys
            )
        result["warnings"] = self._normalize_string_list(
            candidate_data.get("warnings")
        )
        links = candidate_data.get("links")
        links = links if isinstance(links, dict) else {}
        result["links"] = {
            key: self._clean_string(links.get(key)) for key in LINK_FIELDS
        }
        for field_name in COLLECTION_FIELDS:
            result.setdefault(field_name, [])
        return result

    def _clean_string(self, value):
        return value.strip() if isinstance(value, str) and value.strip() else None

    def _normalize_string_list(self, value):
        if not isinstance(value, list):
            return []
        normalized = []
        seen = set()
        for item in value:
            clean_item = self._clean_string(item)
            key = clean_item.casefold() if clean_item else None
            if clean_item and key not in seen:
                normalized.append(clean_item)
                seen.add(key)
        return normalized

    def _normalize_object_list(self, value, keys):
        if not isinstance(value, list):
            return []
        normalized = []
        for item in value:
            if isinstance(item, dict):
                normalized.append(
                    {key: self._clean_string(item.get(key)) for key in keys}
                )
        return normalized
