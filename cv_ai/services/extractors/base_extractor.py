import base64
import os


class BaseCvExtractor:
    """Base contract for in-memory CV text extractors."""

    supported_mimetypes = ()
    supported_extensions = ()

    def supports(self, attachment):
        extension = os.path.splitext(attachment.name or "")[1].lower()
        mimetype = (attachment.mimetype or "").lower()
        return (
            extension in self.supported_extensions
            and mimetype in self.supported_mimetypes
        )

    def extract(self, attachment):
        raise NotImplementedError

    def _decode_attachment(self, attachment):
        return base64.b64decode(attachment.datas, validate=True)
