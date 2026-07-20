from odoo import fields, models


class CvRepositoryProcessingLog(models.Model):
    _name = "cv.repository.processing.log"
    _description = "CV Processing Log"
    _order = "create_date desc"

    document_id = fields.Many2one(
        "cv.repository.document",
        required=True,
        ondelete="cascade",
        index=True,
    )
    batch_id = fields.Many2one(
        "cv.repository.batch",
        required=True,
        ondelete="cascade",
        index=True,
    )
    candidate_id = fields.Many2one(
        "cv.repository.candidate",
        ondelete="set null",
        index=True,
    )
    operation = fields.Selection(
        [
            ("extract", "Extract"),
            ("parse", "Parse"),
            ("create_candidate", "Create Candidate"),
            ("retry", "Retry"),
            ("approve", "Approve"),
            ("reject", "Reject"),
        ],
        required=True,
        index=True,
    )
    status = fields.Selection(
        [("success", "Success"), ("failed", "Failed"), ("warning", "Warning")],
        required=True,
        index=True,
    )
    message = fields.Text(required=True)
    provider = fields.Char()
    model_name = fields.Char()
    duration_ms = fields.Integer()
    created_by = fields.Many2one(
        "res.users",
        default=lambda self: self.env.user,
        required=True,
        readonly=True,
    )

    def create_entry(self, document, operation, status, message, **values):
        """Create a privacy-conscious processing log entry."""
        return self.create(
            {
                "document_id": document.id,
                "batch_id": document.batch_id.id,
                "candidate_id": values.get("candidate_id") or False,
                "operation": operation,
                "status": status,
                "message": message,
                "provider": values.get("provider"),
                "model_name": values.get("model_name"),
                "duration_ms": values.get("duration_ms", 0),
            }
        )
