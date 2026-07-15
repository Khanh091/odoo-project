# -*- coding: utf-8 -*-

from odoo import http
from odoo.exceptions import AccessDenied
from odoo.http import request
from odoo.addons.web.controllers.home import Home


class AuthController(Home):

    def _continue_authenticated_login(self, user, uid, redirect=None):
        if request.session.uid:
            request.params["login_success"] = True
            return request.redirect(self._login_redirect(uid, redirect=redirect))

        mfa_url = user._mfa_url()
        if mfa_url:
            return request.redirect(mfa_url)

        if request.session.get("pre_uid") == uid:
            request.session.finalize(request.env)
            request.update_env(user=request.session.uid)
            request.update_context(**request.session.context)
            request.params["login_success"] = True
            return request.redirect(self._login_redirect(uid, redirect=redirect))

        return request.redirect("/web/login")

    @http.route("/web/login", type="http", auth="none", methods=["GET", "POST"])
    def web_login(self, redirect=None, **kw):
        if request.httprequest.method != "POST":
            return super().web_login(redirect=redirect, **kw)

        login = request.params.get("login")
        password = request.params.get("password")
        if not login or not password:
            return super().web_login(redirect=redirect, **kw)

        try:
            uid = request.session.authenticate(request.db, login, password)
        except AccessDenied:
            return super().web_login(redirect=redirect, **kw)

        user = request.env["res.users"].sudo().browse(uid)
        user._tct_disable_totp_if_no_high_privilege()
        if not user.is_high_privilege:
            return self._continue_authenticated_login(user, uid, redirect=redirect)

        user._check_ip_whitelist()
        if not user.mfa_required:
            return self._continue_authenticated_login(user, uid, redirect=redirect)

        #giữ user ở pre-auth khi otp chưa xác thực
        if request.session.uid:
            request.session.logout(keep_db=True)

        request.session["pre_uid"] = uid
        request.session["pre_login"] = login
        request.session["mfa_uid"] = uid
        request.session["mfa_redirect"] = redirect

        request.env["ir.http"]._auth_method_public()
        if not user.totp_enabled:
            return request.render(
                "tct_high_privilege_2fa.mfa_setup_page",
                user._tct_get_totp_setup_values(),
            )

        return request.render("tct_high_privilege_2fa.mfa_verify_page", {"login": login})
