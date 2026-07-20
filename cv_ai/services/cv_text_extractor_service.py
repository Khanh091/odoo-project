import binascii
import logging

from odoo import _, models
from odoo.exceptions import MissingError, ValidationError

from .extractors import DocxCvExtractor, PdfCvExtractor

_logger = logging.getLogger(__name__)


class CvTextExtractorService(models.AbstractModel):
    _name = "cv.ai.text.extractor.service"
    _description = "CV Text Extractor Service"

    def extract_attachment(self, attachment):
        """Extract plain text from a supported CV attachment."""
        if not attachment or not attachment.exists():
            raise MissingError(_("The CV attachment no longer exists."))
        attachment.ensure_one()
        if not attachment.datas:
            raise ValidationError(_("The CV attachment is empty."))

        extractor = next(
            (
                item
                for item in (PdfCvExtractor(), DocxCvExtractor())
                if item.supports(attachment)
            ),
            None,
        )
        if extractor is None:
            raise ValidationError(
                _("Only PDF and DOCX CV files with a valid MIME type are supported.")
            )
        try:
            text = extractor.extract(attachment).strip()
        except (binascii.Error, ValueError) as error:
            _logger.exception("Invalid attachment data for %s", attachment.id)
            raise ValidationError(_("The CV attachment data is invalid.")) from error
        if not text:
            raise ValidationError(_("No text could be extracted from the CV."))
        return text
