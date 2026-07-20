import fitz
import logging

from odoo import _
from odoo.exceptions import ValidationError

from .base_extractor import BaseCvExtractor

_logger = logging.getLogger(__name__)


class PdfCvExtractor(BaseCvExtractor):
    supported_mimetypes = ("application/pdf",)
    supported_extensions = (".pdf",)

    def extract(self, attachment):
        pdf_bytes = self._decode_attachment(attachment)
        document = None
        try:
            document = fitz.open(stream=pdf_bytes, filetype="pdf")
            text = "\n".join(page.get_text("text") for page in document)
        except (fitz.FileDataError, RuntimeError, ValueError) as error:
            _logger.exception("Could not read PDF attachment %s", attachment.id)
            raise ValidationError(_("The PDF file could not be read.")) from error
        finally:
            if document is not None:
                document.close()
        if not text.strip():
            raise ValidationError(
                _("The PDF contains no extractable text. OCR is not supported.")
            )
        return text
