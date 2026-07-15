import re

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    google_oauth_enabled = fields.Boolean(
        string="Enable Google Login",
        config_parameter="auth_google_oauth.enabled",
    )
    google_oauth_auto_signup = fields.Boolean(
        string="Automatically Create Users",
        config_parameter="auth_google_oauth.auto_signup",
    )
    google_oauth_allowed_domains = fields.Char(
        string="Allowed Email Domains",
        config_parameter="auth_google_oauth.allowed_domains",
        help="Leave empty to allow every verified Google email domain. Use commas or new lines for multiple domains.",
    )
    google_oauth_client_id = fields.Char(
        string="Google Client ID",
        related="auth_oauth_google_client_id",
        readonly=False,
    )
    google_oauth_redirect_uri = fields.Char(
        string="Redirect URI",
        compute="_compute_google_oauth_redirect_uri",
    )

    @api.depends("server_uri_google")
    def _compute_google_oauth_redirect_uri(self):
        uri = self.get_uri()
        for setting in self:
            setting.google_oauth_redirect_uri = uri

    @api.model
    def _normalize_google_allowed_domains(self, domains):
        if not domains:
            return ""
        normalized = []
        for domain in re.split(r"[,\n\r]+", domains):
            domain = domain.strip().lower().lstrip("@")
            if domain and domain not in normalized:
                normalized.append(domain)
        return "\n".join(normalized)

    @api.constrains("google_oauth_allowed_domains")
    def _check_google_oauth_allowed_domains(self):
        for setting in self:
            domains = setting._normalize_google_allowed_domains(setting.google_oauth_allowed_domains)
            for domain in domains.splitlines():
                if "@" in domain or " " in domain:
                    raise ValidationError(_("Allowed Google email domain '%s' is invalid.") % domain)

    def set_values(self):
        for setting in self:
            setting.google_oauth_allowed_domains = setting._normalize_google_allowed_domains(
                setting.google_oauth_allowed_domains
            )
            if setting.google_oauth_enabled and not setting.auth_oauth_google_client_id:
                raise ValidationError(_("Google login cannot be enabled without a Google Client ID."))
            setting.auth_oauth_google_enabled = setting.google_oauth_enabled
        super().set_values()
