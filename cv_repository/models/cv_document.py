import json
import logging
import time

from odoo import _, fields, models
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
            ("extracting", "Extracting"),
            ("parsing", "Parsing"),
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
        success = self._process_document(raise_on_error=False)
        if success:
            return self.action_open_candidate()
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("CV processing failed"),
                "message": self.error_message,
                "type": "danger",
                "sticky": True,
            },
        }

    def action_retry(self):
        self.ensure_one()
        if self.state != "failed":
            raise UserError(_("Only failed CV documents can be retried."))
        success = self._process_document(raise_on_error=False, is_retry=True)
        if success:
            return self.action_open_candidate()
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("CV retry failed"),
                "message": self.error_message,
                "type": "danger",
                "sticky": True,
            },
        }

    def _process_document(self, raise_on_error=False, is_retry=False):
        self.ensure_one()
        started_at = time.monotonic()
        try:
            with self.env.cr.savepoint():
                self._validate_attachment()
                self.write({"error_message": False, "state": "extracting"})
                result = self.env["cv.ai.service"].parse_attachment(
                    self.attachment_id
                )
                self.state = "parsing"
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
                if is_retry:
                    values["retry_count"] = self.retry_count + 1
                self.write(values)
            duration_ms = int((time.monotonic() - started_at) * 1000)
            self.env["cv.repository.processing.log"].create_entry(
                self,
                "retry" if is_retry else "create_candidate",
                "success",
                _("CV processed successfully."),
                candidate_id=candidate.id,
                provider=result.get("provider"),
                model_name=result.get("model"),
                duration_ms=duration_ms,
            )
            self.batch_id._update_state()
            return True
        except (MissingError, UserError, ValidationError) as error:
            _logger.exception("CV document %s processing failed", self.id)
            self._record_failure(error, started_at, is_retry)
            if raise_on_error:
                raise
            return False
        except (json.JSONDecodeError, TypeError, ValueError) as error:
            _logger.exception("CV document %s processing failed", self.id)
            self._record_failure(error, started_at, is_retry)
            if raise_on_error:
                raise UserError(_("The CV could not be processed.")) from error
            return False
        except Exception as error:
            _logger.exception("Unexpected CV document %s processing failure", self.id)
            self._record_failure(error, started_at, is_retry)
            if raise_on_error:
                raise UserError(_("The CV could not be processed.")) from error
            return False

    def _record_failure(self, error, started_at, is_retry):
        values = {
            "state": "failed",
            "error_message": str(error) or _("Unknown CV processing error."),
            "processed_at": fields.Datetime.now(),
            "processed_by": self.env.user.id,
        }
        if is_retry:
            values["retry_count"] = self.retry_count + 1
        self.write(values)
        self.env["cv.repository.processing.log"].create_entry(
            self,
            "retry" if is_retry else "parse",
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
