# -*- coding: utf-8 -*-

from odoo import api, fields, models


def _parse_group_ids(value):
    if not value:
        return []
    if isinstance(value, str):
        return [int(group_id) for group_id in value.split(",") if group_id.strip().isdigit()]
    return []


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    tct_high_privilege_group_ids = fields.Many2many(
        "res.groups",
        string="High Privilege Groups",
    )

    tct_enable_mfa = fields.Boolean(
        string="Enable MFA Enforcement",
        config_parameter="tct_high_privilege_2fa.enable_mfa",
    )

    tct_enable_ip_whitelist = fields.Boolean(
        string="Enable IP Whitelist",
        config_parameter="tct_high_privilege_2fa.enable_ip_whitelist",
    )

    @api.model
    def get_values(self):
        res = super().get_values()

        ICP = self.env["ir.config_parameter"].sudo()
        group_ids = _parse_group_ids(
            ICP.get_param("tct_high_privilege_2fa.high_privilege_group_ids")
        )
        legacy_group_id = ICP.get_param("tct_high_privilege_2fa.high_privilege_group_id")
        if not group_ids and legacy_group_id and legacy_group_id.isdigit():
            group_ids = [int(legacy_group_id)]

        res.update(
            tct_high_privilege_group_ids=[(6, 0, group_ids)],
            tct_enable_mfa=ICP.get_param(
                "tct_high_privilege_2fa.enable_mfa"
            ) == "True",
            tct_enable_ip_whitelist=ICP.get_param(
                "tct_high_privilege_2fa.enable_ip_whitelist"
            ) == "True",
        )

        return res

    def set_values(self):
        super().set_values()

        ICP = self.env["ir.config_parameter"].sudo()
        group_ids = self.tct_high_privilege_group_ids.ids

        ICP.set_param(
            "tct_high_privilege_2fa.high_privilege_group_ids",
            ",".join(str(group_id) for group_id in group_ids),
        )
        ICP.set_param(
            "tct_high_privilege_2fa.high_privilege_group_id",
            group_ids[0] if group_ids else False,
        )

        ICP.set_param(
            "tct_high_privilege_2fa.enable_mfa",
            self.tct_enable_mfa,
        )

        ICP.set_param(
            "tct_high_privilege_2fa.enable_ip_whitelist",
            self.tct_enable_ip_whitelist,
        )

        if self.tct_enable_mfa and group_ids:
            users = self.env["res.users"].search([("groups_id", "in", group_ids)])
            users._tct_prepare_high_privilege_totp_setup()
