# -*- coding: utf-8 -*-

from odoo import api, fields, models
from odoo.exceptions import ValidationError


class VnaSupportRequestType(models.Model):
    _name = "vna.support.request.type"
    _description = "Loại yêu cầu hỗ trợ"
    _order = "sequence, name"

    name = fields.Char(string="Tên loại yêu cầu", required=True, translate=True)
    code = fields.Char(string="Mã", required=True)
    description = fields.Text(string="Mô tả")
    receiver_group_ids = fields.Many2many(
        "res.groups",
        "vna_support_request_type_group_rel",
        "request_type_id",
        "group_id",
        string="Nhóm tiếp nhận",
        required=True,
    )
    sequence = fields.Integer(string="Thứ tự", default=10)
    default_priority = fields.Selection(
        [
            ("low", "Thấp"),
            ("normal", "Bình thường"),
            ("high", "Cao"),
            ("urgent", "Khẩn cấp"),
        ],
        string="Mức ưu tiên mặc định",
        required=True,
        default="normal",
    )
    active = fields.Boolean(string="Đang hoạt động", default=True)

    _sql_constraints = [
        ("vna_support_request_type_code_unique", "unique(code)", "Mã loại yêu cầu phải là duy nhất."),
    ]

    @api.constrains("receiver_group_ids", "active")
    def _check_receiver_groups_when_active(self):
        for request_type in self:
            if request_type.active and not request_type.receiver_group_ids:
                raise ValidationError("Loại yêu cầu đang hoạt động phải có ít nhất một nhóm tiếp nhận.")

