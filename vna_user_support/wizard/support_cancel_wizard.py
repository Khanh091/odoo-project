# -*- coding: utf-8 -*-

from odoo import fields, models
from odoo.exceptions import UserError


class VnaSupportCancelWizard(models.TransientModel):
    _name = "vna.support.cancel.wizard"
    _description = "Wizard hủy yêu cầu hỗ trợ"

    request_id = fields.Many2one("vna.support.request", string="Yêu cầu", required=True)
    cancel_reason = fields.Text(string="Lý do hủy", required=True)

    def action_confirm_cancel(self):
        self.ensure_one()
        cancelled_stage = self.env["vna.support.stage"].search(
            [("code", "=", "cancelled"), ("active", "=", True)],
            limit=1,
        )
        if not cancelled_stage:
            raise UserError("Chưa cấu hình trạng thái Đã hủy.")
        self.request_id.write(
            {
                "cancel_reason": self.cancel_reason,
                "stage_id": cancelled_stage.id,
            }
        )
        return {"type": "ir.actions.act_window_close"}
