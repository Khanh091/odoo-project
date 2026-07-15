# -*- coding: utf-8 -*-

import base64
import functools
import io
import logging
import os
import re

import qrcode
import werkzeug.urls

from odoo import _, api, fields, models
from odoo.addons.auth_totp.models.totp import ALGORITHM, DIGITS, TIMESTEP, TOTP, TOTP_SECRET_SIZE
from odoo.exceptions import AccessDenied
from odoo.http import request

_logger = logging.getLogger(__name__)
compress = functools.partial(re.sub, r"\s", "")


def _parse_group_ids(value):
    if not value:
        return []
    if isinstance(value, str):
        return [int(group_id) for group_id in value.split(",") if group_id.strip().isdigit()]
    return []


class ResUsers(models.Model):
    _inherit = "res.users"

    is_high_privilege = fields.Boolean(
        string="High Privilege User",
        compute="_compute_is_high_privilege",
    )

    tct_totp_setup_secret = fields.Char(
        string="Pending TOTP Secret",
        copy=False,
        groups="base.group_system",
    )
    tct_totp_qrcode = fields.Binary(
        string="TOTP QR Code",
        compute="_compute_tct_totp_qrcode",
        groups="base.group_system",
    )

    mfa_required = fields.Boolean(
        string="MFA Required",
        compute="_compute_is_high_privilege",
    )

    def _tct_get_high_privilege_groups(self):
        ICP = self.env["ir.config_parameter"].sudo()
        group_ids = _parse_group_ids(
            ICP.get_param("tct_high_privilege_2fa.high_privilege_group_ids")
        )
        legacy_group_id = ICP.get_param("tct_high_privilege_2fa.high_privilege_group_id")
        if not group_ids and legacy_group_id and legacy_group_id.isdigit():
            group_ids = [int(legacy_group_id)]
        return self.env["res.groups"].browse(group_ids).exists()

    def _tct_is_mfa_enabled(self):
        return (
            self.env["ir.config_parameter"].sudo().get_param("tct_high_privilege_2fa.enable_mfa")
            == "True"
        )

    def _tct_is_ip_whitelist_enabled(self):
        return (
            self.env["ir.config_parameter"].sudo().get_param(
                "tct_high_privilege_2fa.enable_ip_whitelist"
            )
            == "True"
        )

    @api.depends("groups_id")
    def _compute_is_high_privilege(self):
        high_groups = self._tct_get_high_privilege_groups()
        enable_mfa = self._tct_is_mfa_enabled()

        for user in self:
            user.is_high_privilege = bool(high_groups & user.groups_id)
            user.mfa_required = user.is_high_privilege and enable_mfa

    def _tct_generate_totp_secret(self):
        secret_bytes_count = TOTP_SECRET_SIZE // 8
        secret = base64.b32encode(os.urandom(secret_bytes_count)).decode()
        return " ".join(map("".join, zip(*[iter(secret)] * 4)))

    def _tct_get_totp_secret_for_qr(self):
        self.ensure_one()
        return self.tct_totp_setup_secret or self.sudo().totp_secret

    def _tct_get_totp_url(self, secret=None):
        self.ensure_one()
        secret = secret or self._tct_get_totp_secret_for_qr()
        if not secret:
            return False

        issuer = request and request.httprequest.host.split(":", 1)[0]
        issuer = issuer or self.company_id.display_name
        return werkzeug.urls.url_unparse((
            "otpauth",
            "totp",
            werkzeug.urls.url_quote(f"{issuer}:{self.login}", safe=":"),
            werkzeug.urls.url_encode({
                "secret": compress(secret),
                "issuer": issuer,
                "algorithm": ALGORITHM.upper(),
                "digits": DIGITS,
                "period": TIMESTEP,
            }),
            "",
        ))

    def _tct_make_totp_qrcode(self, secret=None):
        self.ensure_one()
        url = self._tct_get_totp_url(secret)
        if not url:
            return False

        data = io.BytesIO()
        qrcode.make(url.encode(), box_size=4).save(data, optimise=True, format="PNG")
        return base64.b64encode(data.getvalue()).decode()

    def _compute_tct_totp_qrcode(self):
        for user in self:
            user.tct_totp_qrcode = user._tct_make_totp_qrcode()

    def _tct_ensure_totp_setup_secret(self):
        self.ensure_one()
        if not self.tct_totp_setup_secret:
            self.sudo().tct_totp_setup_secret = self._tct_generate_totp_secret()
        return self.tct_totp_setup_secret

    def _tct_prepare_high_privilege_totp_setup(self):
        for user in self:
            if user.mfa_required and not user.totp_enabled and not user.tct_totp_setup_secret:
                user.sudo().tct_totp_setup_secret = user._tct_generate_totp_secret()
        return True

    def _tct_disable_totp(self):
        for user in self:
            user._revoke_all_devices()
            user.sudo().write({
                "totp_secret": False,
                "tct_totp_setup_secret": False,
            })
        return True

    def _tct_disable_totp_if_no_high_privilege(self):
        for user in self:
            if not bool(user._tct_get_high_privilege_groups() & user.groups_id) and user.totp_enabled:
                user._tct_disable_totp()
        return True

    def _tct_get_totp_setup_values(self):
        self.ensure_one()
        secret = self._tct_ensure_totp_setup_secret()
        return {
            "login": self.login,
            "secret": secret,
            "qrcode": self._tct_make_totp_qrcode(secret),
            "otpauth_url": self._tct_get_totp_url(secret),
            "error": False,
        }

    def _tct_activate_pending_totp(self, code):
        self.ensure_one()
        secret = self.tct_totp_setup_secret
        if not secret:
            raise AccessDenied(_("TOTP setup is not initialized"))

        match = TOTP(base64.b32decode(compress(secret).upper())).match(code)
        if match is None:
            raise AccessDenied(_("Verification failed, please double-check the 6-digit code"))

        self.sudo().write({
            "totp_secret": compress(secret).upper(),
            "tct_totp_setup_secret": False,
        })
        return True

    def _get_client_ip(self):
        self.ensure_one()

        forwarded = request.httprequest.headers.get("X-Forwarded-For")
        if forwarded:
            ip = forwarded.split(",")[0].strip()
            source = "X-Forwarded-For"
        else:
            ip = request.httprequest.remote_addr
            source = "remote_addr"
        _logger.info("CLIENT IP = %s (from %s)", ip, source)
        return ip

    def _check_ip_whitelist(self):
        self.ensure_one()

        if not self.is_high_privilege or not self._tct_is_ip_whitelist_enabled():
            return True

        client_ip = self._get_client_ip()
        if not client_ip:
            raise AccessDenied(_("Cannot detect client IP"))

        allowed = self.env["tct.allowed.ip"].search([
            ("active", "=", True),
            ("group_ids", "in", self.groups_id.ids),
        ])

        if not allowed:
            raise AccessDenied(_("No whitelist IP configured"))

        for rec in allowed:
            if rec.match_ip(client_ip):
                return True

        raise AccessDenied(_("IP not allowed"))

    def verify_totp(self, code):
        self.ensure_one()

        if not self.totp_enabled or not self.totp_secret:
            raise AccessDenied(_("TOTP not configured"))

        self._totp_check(code)

        return True

    @api.model_create_multi
    def create(self, vals_list):
        users = super().create(vals_list)
        users._tct_prepare_high_privilege_totp_setup()
        return users

    def write(self, vals):
        high_groups = self.env["res.groups"]

        if "groups_id" in vals:
            high_groups = self._tct_get_high_privilege_groups()
            users_with_high_privilege_before = self.filtered(
                lambda user: bool(high_groups & user.groups_id)
            )
        else:
            users_with_high_privilege_before = self.browse()

        res = super().write(vals)

        _logger.info("BEFORE high privilege users: %s", users_with_high_privilege_before.mapped("login"))

        self.invalidate_recordset(["groups_id"])

        _logger.info("AFTER groups: %s", [
            (u.login, u.groups_id.mapped("name")) for u in self
        ])

        if "groups_id" in vals:
            fresh_users = self.sudo().browse(self.ids)
            fresh_users.invalidate_recordset(["groups_id"])

            users_lost_high_privilege = users_with_high_privilege_before.sudo().filtered(
                lambda user: not bool(high_groups & fresh_users.browse(user.id).groups_id)
            )

            if users_lost_high_privilege:
                users_lost_high_privilege._tct_disable_totp()

            fresh_users._tct_prepare_high_privilege_totp_setup()

        return res
