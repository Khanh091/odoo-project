from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    cv_ai_ollama_base_url = fields.Char(
        string="Ollama URL",
        config_parameter="cv_ai.ollama_base_url",
        default="http://localhost:11434",
        required=True,
    )
    cv_ai_ollama_model = fields.Char(
        string="Ollama Model",
        config_parameter="cv_ai.ollama_model",
        default="qwen3:1.7b",
        required=True,
    )
    cv_ai_request_timeout = fields.Integer(
        string="Request Timeout (seconds)",
        config_parameter="cv_ai.request_timeout",
        default=120,
        required=True,
    )
    cv_ai_max_text_length = fields.Integer(
        string="Maximum CV Text Length",
        config_parameter="cv_ai.max_text_length",
        default=50000,
        required=True,
    )
