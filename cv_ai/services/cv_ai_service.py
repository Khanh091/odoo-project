from odoo import _, models


class CvAiService(models.AbstractModel):
    _name = "cv.ai.service"
    _description = "CV AI Service"

    def parse_attachment(self, attachment, before_ai_callback=None):
        text = self.env["cv.ai.text.extractor.service"].extract_attachment(
            attachment
        )
        parameters = self.env["ir.config_parameter"].sudo()
        max_length = self._positive_integer(
            parameters.get_param("cv_ai.max_text_length", "50000"), 50000
        )
        truncated = len(text) > max_length
        provider_text = text[:max_length] if truncated else text
        if before_ai_callback:
            before_ai_callback()
        candidate_data = self.env["cv.ai.ollama.provider"].extract_candidate(
            provider_text
        )
        result = self.env["cv.ai.result.validator"].validate_candidate(
            candidate_data
        )
        if truncated:
            result["warnings"].append(
                _("CV text was truncated before AI processing.")
            )
        result.update(
            {
                "raw_text": text,
                "provider": "ollama",
                "model": parameters.get_param(
                    "cv_ai.ollama_model", "qwen3:1.7b"
                ),
            }
        )
        return result

    def _positive_integer(self, value, default):
        normalized_value = str(value or "").strip()
        if not normalized_value.isdecimal():
            return default
        parsed_value = int(normalized_value)
        return parsed_value if parsed_value > 0 else default
