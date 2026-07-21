from odoo import _, fields, models
from odoo.exceptions import UserError


class RejectCandidateWizard(models.TransientModel):
    _name = "cv.repository.reject.candidate.wizard"
    _description = "Reject Candidates"

    candidate_ids = fields.Many2many(
        "cv.repository.candidate",
        "cv_repo_reject_wizard_candidate_rel",
        "wizard_id",
        "candidate_id",
        required=True,
        default=lambda self: self._default_candidate_ids(),
    )
    reason = fields.Text(required=True)

    def _default_candidate_ids(self):
        if self.env.context.get("active_model") == "cv.repository.candidate":
            return [(6, 0, self.env.context.get("active_ids", []))]
        return [(6, 0, [])]

    def action_confirm_rejection(self):
        self.ensure_one()
        reason = (self.reason or "").strip()
        if not reason:
            raise UserError(_("A rejection reason is required."))
        self.candidate_ids._reject_with_reason(reason)
        return {"type": "ir.actions.act_window_close"}
