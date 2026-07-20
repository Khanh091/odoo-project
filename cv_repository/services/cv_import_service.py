from odoo import _, models
from odoo.exceptions import ValidationError


class CvImportService(models.AbstractModel):
    _name = "cv.repository.import.service"
    _description = "CV Import Service"

    def create_batch(self, name, attachments, note=None):
        """Create an import batch and bind each attachment to its document."""
        if not attachments:
            raise ValidationError(_("Select at least one CV file."))
        batch = self.env["cv.repository.batch"].create(
            {"name": name, "note": note}
        )
        for attachment in attachments:
            document = self.env["cv.repository.document"].create(
                {
                    "name": attachment.name,
                    "batch_id": batch.id,
                    "attachment_id": attachment.id,
                    "state": "uploaded",
                }
            )
            attachment.write(
                {"res_model": "cv.repository.document", "res_id": document.id}
            )
        return batch
