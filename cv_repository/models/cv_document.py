import json
import logging
import time

from odoo import _, api, fields, models
from odoo.exceptions import MissingError, UserError, ValidationError

_logger = logging.getLogger(__name__)


class CvRepositoryDocument(models.Model):
    _name = "cv.repository.document"
    _description = "CV Document"
    _inherit = ["mail.thread"]
    _order = "create_date desc"

    name = fields.Char(required=True, tracking=True)
    batch_id = fields.Many2one(
        "cv.repository.batch", required=True, ondelete="cascade", index=True
    )
    attachment_id = fields.Many2one(
        "ir.attachment", required=True, ondelete="restrict"
    )
    candidate_id = fields.Many2one(
        "cv.repository.candidate", ondelete="set null", copy=False
    )
    state = fields.Selection(
        [
            ("uploaded", "Uploaded"),
            ("queued", "Queued"),
            ("extracting", "Extracting Text"),
            ("parsing", "Parsing with AI"),
            ("review", "Waiting for Review"),
            ("approved", "Approved"),
            ("rejected", "Rejected"),
            ("failed", "Failed"),
        ],
        default="uploaded",
        required=True,
        tracking=True,
        index=True,
    )
    mimetype = fields.Char(related="attachment_id.mimetype", readonly=True)
    file_size = fields.Integer(related="attachment_id.file_size", readonly=True)
    extracted_text = fields.Text(readonly=True)
    ai_result_json = fields.Text(readonly=True)
    error_message = fields.Text(readonly=True)
    processed_at = fields.Datetime(readonly=True)
    processed_by = fields.Many2one("res.users", readonly=True)
    retry_count = fields.Integer(default=0, readonly=True)
    processing_log_ids = fields.One2many(
        "cv.repository.processing.log", "document_id", string="Processing Logs"
    )

    def action_process(self):
        self.ensure_one()
        if self.state != "uploaded":
            raise UserError(_("Only uploaded CV documents can be queued."))
        self._queue_for_processing()
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("CV queued"),
                "message": _("The CV will be processed by the scheduled job."),
                "type": "success",
                "sticky": False,
            },
        }

    def action_retry(self):
        self.ensure_one()
        if self.state != "failed":
            raise UserError(_("Only failed CV documents can be retried."))
        self._queue_for_processing(is_retry=True)
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("CV retry queued"),
                "message": _("The CV retry will run in the background."),
                "type": "success",
                "sticky": False,
            },
        }

    def _queue_for_processing(self, is_retry=False, trigger_cron=True):
        self.ensure_one()
        self._validate_attachment()
        values = {
            "state": "queued",
            "error_message": False,
        }
        if is_retry:
            values["retry_count"] = self.retry_count + 1
        self.write(values)
        self.batch_id._update_state()
        if trigger_cron:
            self._trigger_queue_cron()

    @api.model
    def _trigger_queue_cron(self):
        cron = self.env.ref(
            "cv_repository.ir_cron_process_queued_cv_documents",
            raise_if_not_found=False,
        )
        if cron:
            cron._trigger()

    @api.model
    def cron_process_queued_documents(self, limit=1):
        processing_limit = max(int(limit or 1), 1)
        documents = self.search(
            [("state", "=", "queued")],
            order="create_date asc, id asc",
            limit=processing_limit,
        )
        for document in documents:
            with self.env.cr.savepoint():
                document._process_document(raise_on_error=False)
        if self.search_count([("state", "=", "queued")], limit=1):
            self._trigger_queue_cron()
        return True

    def _process_document(self, raise_on_error=False):
        self.ensure_one()
        started_at = time.monotonic()
        try:
            with self.env.cr.savepoint():
                self._validate_attachment()
                self.write({"error_message": False, "state": "extracting"})
                self._mark_as_parsing()
                result = self.env["cv.ai.service"].parse_attachment(
                    self.attachment_id,
                    before_ai_callback=self._mark_as_parsing,
                )
                candidate = self.env[
                    "cv.repository.candidate.creation.service"
                ].create_or_update_from_ai_result(
                    self.batch_id,
                    self,
                    result,
                )
                values = {
                    "extracted_text": result["raw_text"],
                    "ai_result_json": json.dumps(
                        result,
                        ensure_ascii=False,
                    ),
                    "candidate_id": candidate.id,
                    "state": "review",
                    "processed_at": fields.Datetime.now(),
                    "processed_by": self.env.user.id,
                }
                self.write(values)
            duration_ms = int((time.monotonic() - started_at) * 1000)
            self.env["cv.repository.processing.log"].create_entry(
                self,
                "retry" if self.retry_count else "create_candidate",
                "success",
                _("CV processed successfully."),
                candidate_id=candidate.id,
                provider=result.get("provider"),
                model_name=result.get("model"),
                duration_ms=duration_ms,
            )
            self.batch_id.processed_at = fields.Datetime.now()
            self.batch_id._update_state()
            return True
        except (MissingError, UserError, ValidationError) as error:
            _logger.exception("CV document %s processing failed", self.id)
            self._record_failure(error, started_at)
            if raise_on_error:
                raise
            return False
        except (json.JSONDecodeError, TypeError, ValueError) as error:
            _logger.exception("CV document %s processing failed", self.id)
            self._record_failure(error, started_at)
            if raise_on_error:
                raise UserError(_("The CV could not be processed.")) from error
            return False
        except Exception as error:
            _logger.exception("Unexpected CV document %s processing failure", self.id)
            self._record_failure(error, started_at)
            if raise_on_error:
                raise UserError(_("The CV could not be processed.")) from error
            return False

    def _mark_as_parsing(self):
        self.ensure_one()
        self.state = "parsing"

    def _record_failure(self, error, started_at):
        values = {
            "state": "failed",
            "error_message": str(error) or _("Unknown CV processing error."),
            "processed_at": fields.Datetime.now(),
            "processed_by": self.env.user.id,
        }
        self.write(values)
        self.env["cv.repository.processing.log"].create_entry(
            self,
            "retry" if self.retry_count else "parse",
            "failed",
            _("CV processing failed: %s") % values["error_message"],
            duration_ms=int((time.monotonic() - started_at) * 1000),
        )
        self.batch_id._update_state()

    def _validate_attachment(self):
        if not self.attachment_id or not self.attachment_id.exists():
            raise MissingError(_("The CV attachment no longer exists."))
        if not self.attachment_id.datas:
            raise ValidationError(_("The CV attachment is empty."))

    def action_open_candidate(self):
        self.ensure_one()
        if not self.candidate_id:
            raise UserError(_("This document does not have a candidate yet."))
        return {
            "type": "ir.actions.act_window",
            "name": _("Candidate"),
            "res_model": "cv.repository.candidate",
            "view_mode": "form",
            "res_id": self.candidate_id.id,
        }

    def action_download_cv(self):
        self.ensure_one()
        self._validate_attachment()
        return {
            "type": "ir.actions.act_url",
            "url": f"/web/content/{self.attachment_id.id}?download=true",
            "target": "self",
        }
