from odoo import _, api, fields, models
from odoo.exceptions import UserError


class CvRepositoryBatch(models.Model):
    _name = "cv.repository.batch"
    _description = "CV Import Batch"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "create_date desc"

    name = fields.Char(required=True, tracking=True)
    code = fields.Char(default="New", readonly=True, copy=False, index=True)
    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("processing", "Processing"),
            ("review", "Waiting for Review"),
            ("completed", "Completed"),
            ("partial", "Partial"),
            ("failed", "Failed"),
        ],
        default="draft",
        required=True,
        tracking=True,
        index=True,
    )
    document_ids = fields.One2many(
        "cv.repository.document", "batch_id", string="Documents"
    )
    candidate_ids = fields.One2many(
        "cv.repository.candidate", "batch_id", string="Candidates"
    )
    total_document_count = fields.Integer(compute="_compute_counts")
    uploaded_document_count = fields.Integer(compute="_compute_counts")
    queued_document_count = fields.Integer(compute="_compute_counts")
    processing_document_count = fields.Integer(compute="_compute_counts")
    review_document_count = fields.Integer(compute="_compute_counts")
    approved_document_count = fields.Integer(compute="_compute_counts")
    rejected_document_count = fields.Integer(compute="_compute_counts")
    failed_document_count = fields.Integer(compute="_compute_counts")
    review_candidate_count = fields.Integer(compute="_compute_counts")
    approved_candidate_count = fields.Integer(compute="_compute_counts")
    rejected_candidate_count = fields.Integer(compute="_compute_counts")
    created_by = fields.Many2one(
        "res.users",
        default=lambda self: self.env.user,
        required=True,
        readonly=True,
    )
    processed_at = fields.Datetime(readonly=True)
    note = fields.Text()

    @api.model_create_multi
    def create(self, values_list):
        for values in values_list:
            if values.get("code", "New") == "New":
                values["code"] = self.env["ir.sequence"].next_by_code(
                    "cv.repository.batch"
                ) or _("New")
        return super().create(values_list)

    @api.depends("document_ids.state", "candidate_ids.state")
    def _compute_counts(self):
        for batch in self:
            document_states = batch.document_ids.mapped("state")
            candidate_states = batch.candidate_ids.mapped("state")
            batch.total_document_count = len(document_states)
            batch.uploaded_document_count = document_states.count("uploaded")
            batch.queued_document_count = document_states.count("queued")
            batch.processing_document_count = sum(
                state in ("extracting", "parsing") for state in document_states
            )
            batch.review_document_count = document_states.count("review")
            batch.approved_document_count = document_states.count("approved")
            batch.rejected_document_count = document_states.count("rejected")
            batch.failed_document_count = document_states.count("failed")
            batch.review_candidate_count = candidate_states.count("review")
            batch.approved_candidate_count = candidate_states.count("approved")
            batch.rejected_candidate_count = candidate_states.count("rejected")

    def action_process_all(self):
        for batch in self:
            documents = batch.document_ids.filtered(
                lambda document: document.state in ("uploaded", "failed")
            )
            if not documents:
                raise UserError(_("There are no uploaded or failed CVs to process."))
            for document in documents:
                is_retry = document.state == "failed"
                document._queue_for_processing(
                    is_retry=is_retry,
                    trigger_cron=False,
                )
            documents._trigger_queue_cron()
            batch._update_state()
        return True

    def action_retry_failed(self):
        for batch in self:
            failed_documents = batch.document_ids.filtered(
                lambda document: document.state == "failed"
            )
            if not failed_documents:
                raise UserError(_("There are no failed CVs to retry."))
            for document in failed_documents:
                document._queue_for_processing(
                    is_retry=True,
                    trigger_cron=False,
                )
            failed_documents._trigger_queue_cron()
            batch._update_state()
        return True

    def action_approve_all(self):
        for batch in self:
            candidates = batch.candidate_ids.filtered(
                lambda candidate: candidate.state == "review" and candidate.name
            )
            if not candidates:
                raise UserError(
                    _("There are no valid candidates waiting for approval.")
                )
            candidates.action_approve()
            batch._update_state()
        return True

    def action_open_documents(self):
        self.ensure_one()
        action = self.env.ref("cv_repository.action_cv_repository_document").read()[0]
        action["domain"] = [("batch_id", "=", self.id)]
        action["context"] = {"default_batch_id": self.id}
        return action

    def action_open_candidates(self):
        self.ensure_one()
        action = self.env.ref("cv_repository.action_cv_repository_candidate").read()[0]
        action["domain"] = [("batch_id", "=", self.id)]
        action["context"] = {"default_batch_id": self.id}
        return action

    def _update_state(self):
        for batch in self:
            states = batch.document_ids.mapped("state")
            candidate_states = batch.candidate_ids.mapped("state")
            if any(
                state in ("queued", "extracting", "parsing")
                for state in states
            ):
                new_state = "processing"
            elif states and all(state == "failed" for state in states):
                new_state = "failed"
            elif "failed" in states and any(
                state in ("review", "approved", "rejected") for state in states
            ):
                new_state = "partial"
            elif "review" in candidate_states:
                new_state = "review"
            elif (
                candidate_states
                and all(
                    state in ("approved", "rejected", "archived")
                    for state in candidate_states
                )
                and "failed" not in states
            ):
                new_state = "completed"
            elif states and any(
                state in ("review", "approved", "rejected") for state in states
            ):
                new_state = "review"
            else:
                new_state = "draft"
            batch.state = new_state
