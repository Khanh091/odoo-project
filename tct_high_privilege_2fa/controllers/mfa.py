# -*- coding: utf-8 -*-

from odoo import http, _
from odoo.http import request
from odoo.exceptions import AccessDenied
import odoo
import re


def _parse_otp(otp):
    try:
        return int(re.sub(r"\s", "", otp or ""))
    except ValueError as exc:
        raise AccessDenied(_("Invalid authentication code format.")) from exc


def _finalize_mfa_session(uid):
    redirect = request.session.get("mfa_redirect")

    with odoo.registry(request.db).cursor() as cr:
        env = odoo.api.Environment(cr, uid, {})
        request.session.finalize(env)
        request.update_env(user=request.session.uid)
        request.update_context(**request.session.context)

    request.session.pop("mfa_uid", None)
    request.session.pop("mfa_redirect", None)

    return request.redirect(redirect or "/web")


class MFAController(http.Controller):

    @http.route("/tct/mfa/verify", type="http", auth="none", csrf=False, methods=["POST"])
    def verify(self, **kw):

        uid = request.session.get("mfa_uid")
        if not uid:
            raise AccessDenied(_("Session expired"))

        user = request.env["res.users"].sudo().browse(uid)

        try:
            user.verify_totp(_parse_otp(kw.get("otp")))
        except AccessDenied as exc:
            request.env["ir.http"]._auth_method_public()
            return request.render(
                "tct_high_privilege_2fa.mfa_verify_page",
                {
                    "login": kw.get("login") or user.login,
                    "error": str(exc),
                },
            )

        return _finalize_mfa_session(uid)

    @http.route("/tct/mfa/setup", type="http", auth="none", csrf=False, methods=["POST"])
    def setup(self, **kw):

        uid = request.session.get("mfa_uid")
        if not uid:
            raise AccessDenied(_("Session expired"))

        user = request.env["res.users"].sudo().browse(uid)
        try:
            user._tct_activate_pending_totp(_parse_otp(kw.get("otp")))
        except AccessDenied as exc:
            values = user._tct_get_totp_setup_values()
            values["error"] = str(exc)
            request.env["ir.http"]._auth_method_public()
            return request.render("tct_high_privilege_2fa.mfa_setup_page", values)

        return _finalize_mfa_session(uid)
