import json
import logging

import requests

from odoo import _, models
from odoo.exceptions import UserError, ValidationError

from ...schemas import CANDIDATE_JSON_SCHEMA

_logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """Extract candidate information from the supplied CV.
Return only JSON that exactly matches the provided schema.
Never infer or invent information that is not present in the CV.
Preserve proper names, email addresses, and phone numbers exactly.
Normalize skills into a concise list without duplicates.
Prefer YYYY-MM for dates when the source supports that precision.
Use null or an empty list for missing data.
Do not wrap the JSON in a Markdown code fence."""


class OllamaProvider(models.AbstractModel):
    _name = "cv.ai.ollama.provider"
    _description = "Ollama CV AI Provider"

    def extract_candidate(self, cv_text):
        """Extract structured candidate data from CV text using Ollama."""
        parameters = self.env["ir.config_parameter"].sudo()
        base_url = parameters.get_param(
            "cv_ai.ollama_base_url", "http://localhost:11434"
        ).rstrip("/")
        model_name = parameters.get_param("cv_ai.ollama_model", "qwen3:8b")
        timeout = self._positive_integer(
            parameters.get_param("cv_ai.request_timeout", "120"), 120
        )
        payload = {
            "model": model_name,
            "stream": False,
            "format": CANDIDATE_JSON_SCHEMA,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": cv_text},
            ],
            "options": {"temperature": 0},
        }
        try:
            response = requests.post(
                f"{base_url}/api/chat",
                json=payload,
                timeout=timeout,
            )
            response.raise_for_status()
        except requests.Timeout as error:
            _logger.exception("Ollama request timed out")
            raise UserError(_("Ollama did not respond before the timeout.")) from error
        except requests.ConnectionError as error:
            _logger.exception("Could not connect to Ollama")
            raise UserError(
                _("Could not connect to the configured Ollama server.")
            ) from error
        except requests.HTTPError as error:
            _logger.exception("Ollama returned HTTP status %s", response.status_code)
            raise UserError(
                _("Ollama returned an HTTP error (status %s).")
                % response.status_code
            ) from error
        except requests.RequestException as error:
            _logger.exception("Ollama request failed")
            raise UserError(_("The Ollama request failed.")) from error

        try:
            response_data = response.json()
        except requests.JSONDecodeError as error:
            _logger.exception("Ollama response was not JSON")
            raise ValidationError(_("Ollama returned an invalid response.")) from error
        content = (response_data.get("message") or {}).get("content")
        if not isinstance(content, str) or not content.strip():
            raise ValidationError(_("Ollama response did not contain candidate JSON."))
        try:
            return json.loads(content)
        except json.JSONDecodeError as error:
            _logger.exception("Ollama candidate content was not valid JSON")
            raise ValidationError(
                _("Ollama returned invalid candidate JSON.")
            ) from error

    def _positive_integer(self, value, default):
        normalized_value = str(value or "").strip()
        if not normalized_value.isdecimal():
            return default
        parsed_value = int(normalized_value)
        return parsed_value if parsed_value > 0 else default
