from odoo import _, fields, models
from odoo.exceptions import UserError


class CvRepositoryCandidate(models.Model):
    _name = "cv.repository.candidate"
    _description = "Candidate Repository"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "create_date desc"

    name = fields.Char(required=True, tracking=True, index=True)
    email = fields.Char(index=True, tracking=True)
    phone = fields.Char(index=True, tracking=True)
    current_position = fields.Char()
    location = fields.Char()
    summary = fields.Text()
    skill_text = fields.Text(string="Skills")
    education_json = fields.Json(string="Education")
    experience_json = fields.Json(string="Experience")
    certification_json = fields.Json(string="Certifications")
    language_json = fields.Json(string="Languages")
    link_json = fields.Json(string="Links")
    warning_json = fields.Json(string="Warnings")
    batch_id = fields.Many2one(
        "cv.repository.batch", required=True, ondelete="restrict", index=True
    )
    cv_document_id = fields.Many2one(
        "cv.repository.document", required=True, ondelete="restrict", index=True
    )
    attachment_id = fields.Many2one(
        "ir.attachment",
        related="cv_document_id.attachment_id",
        readonly=True,
    )
    possible_duplicate_id = fields.Many2one(
        "cv.repository.candidate", ondelete="set null", copy=False
    )
    state = fields.Selection(
        [
            ("review", "Waiting for Review"),
            ("approved", "Approved"),
            ("rejected", "Rejected"),
            ("archived", "Archived"),
        ],
        default="review",
        required=True,
        tracking=True,
        index=True,
    )
    approved_by = fields.Many2one("res.users", readonly=True)
    approved_at = fields.Datetime(readonly=True)
    rejected_by = fields.Many2one("res.users", readonly=True)
    rejected_at = fields.Datetime(readonly=True)
    rejection_reason = fields.Text(readonly=True)
    active = fields.Boolean(default=True)

    def action_approve(self):
        candidates = self.filtered(
            lambda candidate: candidate.state == "review" and candidate.name
        )
        if not candidates:
            raise UserError(_("No valid candidate is waiting for approval."))
        now = fields.Datetime.now()
        for candidate in candidates:
            candidate.write(
                {
                    "state": "approved",
                    "approved_by": self.env.user.id,
                    "approved_at": now,
                    "rejected_by": False,
                    "rejected_at": False,
                    "rejection_reason": False,
                }
            )
            candidate.cv_document_id.state = "approved"
            self.env["cv.repository.processing.log"].create_entry(
                candidate.cv_document_id,
                "approve",
                "success",
                _("Candidate approved."),
                candidate_id=candidate.id,
            )
        candidates.mapped("batch_id")._update_state()
        return True

    def action_reject(self):
        candidates = self.filtered(lambda candidate: candidate.state == "review")
        if not candidates:
            raise UserError(_("No candidate is waiting for rejection."))
        return {
            "type": "ir.actions.act_window",
            "name": _("Reject Candidates"),
            "res_model": "cv.repository.reject.candidate.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {"default_candidate_ids": [(6, 0, candidates.ids)]},
        }

    def _reject_with_reason(self, reason):
        candidates = self.filtered(lambda candidate: candidate.state == "review")
        if not candidates:
            raise UserError(_("No candidate is waiting for rejection."))
        now = fields.Datetime.now()
        for candidate in candidates:
            candidate.write(
                {
                    "state": "rejected",
                    "rejected_by": self.env.user.id,
                    "rejected_at": now,
                    "rejection_reason": reason,
                    "approved_by": False,
                    "approved_at": False,
                }
            )
            candidate.cv_document_id.state = "rejected"
            self.env["cv.repository.processing.log"].create_entry(
                candidate.cv_document_id,
                "reject",
                "success",
                _("Candidate rejected."),
                candidate_id=candidate.id,
            )
        candidates.mapped("batch_id")._update_state()
        return True

    def action_reset_to_review(self):
        candidates = self.filtered(
            lambda candidate: candidate.state in ("approved", "rejected")
        )
        if not candidates:
            raise UserError(_("No approved or rejected candidate was selected."))
        candidates.write(
            {
                "state": "review",
                "approved_by": False,
                "approved_at": False,
                "rejected_by": False,
                "rejected_at": False,
                "rejection_reason": False,
            }
        )
        candidates.mapped("cv_document_id").write({"state": "review"})
        candidates.mapped("batch_id")._update_state()
        return True

    def action_archive(self):
        self.write({"active": False, "state": "archived"})
        self.mapped("batch_id")._update_state()
        return True

    def action_open_cv_document(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("CV Document"),
            "res_model": "cv.repository.document",
            "view_mode": "form",
            "res_id": self.cv_document_id.id,
        }

    def action_download_cv(self):
        self.ensure_one()
        return self.cv_document_id.action_download_cv()
