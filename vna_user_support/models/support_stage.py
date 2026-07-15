# -*- coding: utf-8 -*-

from odoo import api, fields, models
from odoo.exceptions import ValidationError


class VnaSupportStage(models.Model):
    _name = "vna.support.stage"
    _description = "Trạng thái yêu cầu hỗ trợ"
    _order = "sequence, id"

    name = fields.Char(string="Tên trạng thái", required=True, translate=True)
    code = fields.Char(string="Mã", required=True)
    sequence = fields.Integer(string="Thứ tự", default=10)
    fold = fields.Boolean(string="Thu gọn trong Kanban")
    is_initial = fields.Boolean(string="Trạng thái khởi tạo")
    is_closed = fields.Boolean(string="Trạng thái đóng")
    is_cancelled = fields.Boolean(string="Trạng thái hủy")
    active = fields.Boolean(string="Đang hoạt động", default=True)

    _sql_constraints = [
        ("vna_support_stage_code_unique", "unique(code)", "Mã trạng thái phải là duy nhất."),
    ]

    @api.constrains("is_initial")
    def _check_single_initial_stage(self):
        for stage in self:
            if stage.is_initial:
                domain = [("is_initial", "=", True), ("id", "!=", stage.id)]
                if self.search_count(domain):
                    raise ValidationError("Chỉ được có một trạng thái khởi tạo.")

