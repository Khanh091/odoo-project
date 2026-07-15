# -*- coding: utf-8 -*-

import ipaddress

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class TctAllowedIp(models.Model):
    _name = "tct.allowed.ip"
    _description = "Allowed Login IP"
    _order = "name"

    name = fields.Char(required=True)

    ip_address = fields.Char(
        required=True,
        help="Example: 192.168.1.100, 192.168.1.0/24, or 0.0.0.0 to allow all IPs.",
    )

    group_ids = fields.Many2many(
        comodel_name="res.groups",
        relation="tct_allowed_ip_group_rel",
        column1="allowed_ip_id",
        column2="group_id",
        string="Applied Groups",
    )

    note = fields.Text()

    active = fields.Boolean(default=True)

    _sql_constraints = [
        (
            "unique_ip_address",
            "unique(ip_address)",
            "IP already exists.",
        )
    ]

    @api.constrains("ip_address")
    def _check_ip_address(self):
        for record in self:
            try:
                ipaddress.ip_network(record.ip_address, strict=False)
            except Exception:
                raise ValidationError(
                    _("Invalid IP or CIDR format.")
                )

    def match_ip(self, client_ip):
        self.ensure_one()

        if (self.ip_address or "").strip() == "0.0.0.0":
            return True

        try:
            ip = ipaddress.ip_address(client_ip)
            network = ipaddress.ip_network(self.ip_address, strict=False)
            return ip in network
        except Exception:
            return False
