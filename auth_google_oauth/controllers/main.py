import json
import logging

import werkzeug.urls
from werkzeug.exceptions import BadRequest

from odoo import SUPERUSER_ID, _, http
from odoo.exceptions import AccessDenied
from odoo.http import request
from odoo.tools.misc import clean_context

from odoo.addons.auth_oauth.controllers.main import OAuthController, OAuthLogin, fragment_to_query_string
from odoo.addons.web.controllers.utils import _get_login_redirect_url, ensure_db


_logger = logging.getLogger(__name__)


class GoogleOAuthLogin(OAuthLogin):
    @http.route()
    def web_login(self, *args, **kw):
        response = super().web_login(*args, **kw)
        if response.is_qweb and request.params.get("google_oauth_error"):
            response.qcontext["error"] = request.params["google_oauth_error"]
        return response


class GoogleOAuthController(OAuthController):
    @http.route("/auth_oauth/signin", type="http", auth="none")
    @fragment_to_query_string
    def signin(self, **kw):
        state = json.loads(kw["state"])

        dbname = state["d"]
        if not http.db_filter([dbname]):
            return BadRequest()
        ensure_db(db=dbname)

        provider = state["p"]
        google_provider_id = request.env["ir.model.data"].sudo()._xmlid_to_res_id(
            "auth_oauth.provider_google",
            raise_if_not_found=False,
        )
        is_google_provider = bool(google_provider_id and google_provider_id == int(provider))
        request.update_context(**clean_context(state.get("c", {})))
        try:
            _, login, key = request.env["res.users"].with_user(SUPERUSER_ID).auth_oauth(provider, kw)
            request.env.cr.commit()

            action = state.get("a")
            menu = state.get("m")
            redirect = werkzeug.urls.url_unquote_plus(state["r"]) if state.get("r") else False
            url = "/web"
            if redirect:
                url = redirect
            elif action:
                url = "/web#action=%s" % action
            elif menu:
                url = "/web#menu_id=%s" % menu

            pre_uid = request.session.authenticate(dbname, login, key)
            resp = request.redirect(_get_login_redirect_url(pre_uid, url), 303)
            resp.autocorrect_location_header = False
            if werkzeug.urls.url_parse(resp.location).path == "/web" and not request.env.user._is_internal():
                resp.location = "/"
            return resp
        except AttributeError:
            _logger.error("auth_signup not installed on database %s: oauth sign up cancelled.", dbname)
            url = "/web/login?oauth_error=1"
        except AccessDenied as error:
            if is_google_provider:
                message = str(error) or _("Google OAuth access denied.")
                _logger.info("Google OAuth access denied: %s", message)
                url = "/web/login?google_oauth_error=%s" % werkzeug.urls.url_quote_plus(message)
            else:
                _logger.info("OAuth2: access denied, redirect to main page in case a valid session exists, without setting cookies")
                url = "/web/login?oauth_error=3"
        except Exception:
            _logger.exception("OAuth request handling failed without exposing OAuth credentials")
            if is_google_provider:
                message = _("Google login failed. Please contact your administrator.")
                url = "/web/login?google_oauth_error=%s" % werkzeug.urls.url_quote_plus(message)
            else:
                url = "/web/login?oauth_error=2"

        redirect = request.redirect(url, 303)
        redirect.autocorrect_location_header = False
        return redirect
