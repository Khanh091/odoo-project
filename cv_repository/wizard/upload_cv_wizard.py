import os

from odoo import _, fields, models
from odoo.exceptions import ValidationError


class UploadCvWizard(models.TransientModel):
    _name = "cv.repository.upload.wizard"
    _description = "Upload CV Files"

    name = fields.Char(required=True, default=lambda self: self._default_name())
    attachment_ids = fields.Many2many("ir.attachment", required=True)
    process_immediately = fields.Boolean(default=True)
    note = fields.Text()

    def _default_name(self):
        timestamp = fields.Datetime.context_timestamp(self, fields.Datetime.now())
        return _("CV Import %s") % timestamp.strftime("%Y-%m-%d %H:%M")

    def action_upload(self):
        self.ensure_one()
        self._validate_attachments()
        batch = self.env["cv.repository.import.service"].create_batch(
            self.name,
            self.attachment_ids,
            self.note,
        )
        if self.process_immediately:
            batch.document_ids.write(
                {
                    "state": "queued",
                    "error_message": False,
                }
            )
            batch._update_state()
            batch.document_ids._trigger_queue_cron()
        return {
            "type": "ir.actions.act_window",
            "name": _("CV Import Batch"),
            "res_model": "cv.repository.batch",
            "view_mode": "form",
            "res_id": batch.id,
        }

    def _validate_attachments(self):
        docx_mimetype = (
            "application/vnd.openxmlformats-officedocument."
            "wordprocessingml.document"
        )
        allowed_types = {
            ".pdf": {"application/pdf"},
            ".docx": {docx_mimetype},
        }
        for attachment in self.attachment_ids:
            extension = os.path.splitext(attachment.name or "")[1].lower()
            mimetype = (attachment.mimetype or "").lower()
            if (
                extension not in allowed_types
                or mimetype not in allowed_types[extension]
            ):
                raise ValidationError(
                    _("File '%s' is not a valid PDF or DOCX CV.") % attachment.name
                )
            if not attachment.datas or attachment.file_size <= 0:
                raise ValidationError(_("File '%s' is empty.") % attachment.name)
