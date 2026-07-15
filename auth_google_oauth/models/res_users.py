import json
import logging
import re

from odoo import Command, api, models, _
from odoo.exceptions import AccessDenied, UserError, ValidationError


_logger = logging.getLogger(__name__)


class ResUsers(models.Model):
    _inherit = "res.users"

    @api.model
    def _get_google_provider(self):
        return self.env.ref("auth_oauth.provider_google", raise_if_not_found=False)

    @api.model
    def _is_google_oauth_provider(self, provider):
        google_provider = self._get_google_provider()
        return bool(google_provider and google_provider.id == int(provider))

    @api.model
    def _get_google_config_param(self, key, default=False):
        # sudo: OAuth login is executed before a normal user session exists, and these are system settings.
        return self.env["ir.config_parameter"].sudo().get_param(key, default)

    @api.model
    def _get_google_allowed_domains(self):
        value = self._get_google_config_param("auth_google_oauth.allowed_domains", "") or ""
        domains = []
        for domain in re.split(r"[,\n\r]+", value):
            domain = domain.strip().lower().lstrip("@")
            if domain and domain not in domains:
                domains.append(domain)
        return domains

    @api.model
    def _is_google_email_domain_allowed(self, email):
        domains = self._get_google_allowed_domains()
        if not domains:
            return True
        if not email or "@" not in email:
            return False
        email_domain = email.rsplit("@", 1)[1].strip().lower()
        return email_domain in domains

    @api.model
    def _is_google_auto_signup_enabled(self):
        return self._get_google_config_param("auth_google_oauth.auto_signup", "False") == "True"

    @api.model
    def _ensure_google_login_enabled(self, provider):
        google_provider = self._get_google_provider()
        if not google_provider:
            raise AccessDenied(_("Google OAuth provider is not available."))
        if not self._get_google_config_param("auth_google_oauth.enabled", "False") == "True":
            raise AccessDenied(_("Google login is disabled."))
        if not google_provider.enabled:
            raise AccessDenied(_("Google OAuth provider is disabled."))
        if not google_provider.client_id:
            raise AccessDenied(_("Google OAuth Client ID is not configured."))
        if int(provider) != google_provider.id:
            raise AccessDenied(_("Invalid Google OAuth provider."))

    @api.model
    def _normalize_google_validation(self, validation):
        email_verified = validation.get("email_verified")
        if isinstance(email_verified, str):
            email_verified = email_verified.lower() == "true"

        oauth_uid = validation.get("user_id") or validation.get("sub")
        email = (validation.get("email") or "").strip().lower()
        if not oauth_uid:
            raise AccessDenied(_("Google did not return a subject identifier."))
        if not email:
            raise AccessDenied(_("Google did not return an email address."))
        if not email_verified:
            raise AccessDenied(_("Only Google accounts with a verified email address can sign in."))
        if not self._is_google_email_domain_allowed(email):
            raise AccessDenied(_("This Google email domain is not allowed to sign in."))

        validation["user_id"] = oauth_uid
        validation["email"] = email
        validation["email_verified"] = True
        return validation

    @api.model
    def _auth_oauth_validate(self, provider, access_token):
        validation = super()._auth_oauth_validate(provider, access_token)
        if self._is_google_oauth_provider(provider):
            self._ensure_google_login_enabled(provider)
            validation = self._normalize_google_validation(validation)
            _logger.info("Validated Google OAuth user for email <%s>", validation["email"])
        return validation

    @api.model
    def _find_google_user_by_email(self, email):
        users = self.with_context(active_test=False).search([
            "|",
            ("login", "=ilike", email),
            ("email", "=ilike", email),
        ])
        if len(users) > 1:
            raise ValidationError(
                _("Multiple Odoo users already use the Google email '%s'. Please fix duplicate users before login.")
                % email
            )
        return users

    @api.model
    def _link_google_user(self, user, provider, oauth_uid, access_token):
        user.write({
            "oauth_provider_id": provider,
            "oauth_uid": oauth_uid,
            "oauth_access_token": access_token,
        })
        _logger.info("Linked Google OAuth identity to existing user <%s>", user.login)
        return user.login

    @api.model
    def _create_google_user(self, provider, validation, access_token):
        if not self._is_google_auto_signup_enabled():
            raise AccessDenied(_("No Odoo user is linked to this Google account and automatic user creation is disabled."))

        group_user = self.env.ref("base.group_user")
        values = {
            "name": validation.get("name") or validation["email"],
            "login": validation["email"],
            "email": validation["email"],
            "oauth_provider_id": provider,
            "oauth_uid": validation["user_id"],
            "oauth_access_token": access_token,
            "active": True,
            "groups_id": [Command.set([group_user.id])],
        }
        user = self.with_context(no_reset_password=True).create(values)
        _logger.info("Created internal Odoo user <%s> from verified Google OAuth login", user.login)
        return user.login

    @api.model
    def _auth_oauth_signin(self, provider, validation, params):
        if not self._is_google_oauth_provider(provider):
            return super()._auth_oauth_signin(provider, validation, params)

        self._ensure_google_login_enabled(provider)
        validation = self._normalize_google_validation(validation)
        oauth_uid = validation["user_id"]
        access_token = params.get("access_token")

        oauth_user = self.with_context(active_test=False).search([
            ("oauth_uid", "=", oauth_uid),
            ("oauth_provider_id", "=", provider),
        ])
        if len(oauth_user) > 1:
            raise ValidationError(_("Multiple users are linked to the same Google account."))
        if oauth_user:
            oauth_user.write({"oauth_access_token": access_token})
            return oauth_user.login

        email_user = self._find_google_user_by_email(validation["email"])
        if email_user:
            return self._link_google_user(email_user, provider, oauth_uid, access_token)

        return self._create_google_user(provider, validation, access_token)

    @api.model
    def auth_oauth(self, provider, params):
        if self._is_google_oauth_provider(provider):
            self._ensure_google_login_enabled(provider)
            state = json.loads(params.get("state", "{}"))
            if state.get("p") != int(provider):
                raise AccessDenied(_("Invalid Google OAuth state."))
        try:
            return super().auth_oauth(provider, params)
        except (AccessDenied, UserError, ValidationError):
            raise
        except Exception as error:
            if self._is_google_oauth_provider(provider):
                _logger.exception("Google OAuth login failed without exposing OAuth credentials")
                raise AccessDenied(_("Google login failed. Please contact your administrator.")) from error
            raise
