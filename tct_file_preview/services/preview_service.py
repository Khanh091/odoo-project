# -*- coding: utf-8 -*-

import logging
import shutil
import tempfile
from pathlib import Path
from urllib.parse import urlencode

from odoo import _
from odoo.exceptions import AccessError, UserError

from ..utils.constants import (
    OFFICE_EXTENSIONS,
    OFFICE_MIME_TYPES,
    PDF_MIMETYPE,
    PREVIEW_PDF_ROUTE,
    PREVIEW_TYPE_IMAGE,
    PREVIEW_TYPE_OFFICE,
    PREVIEW_TYPE_PDF,
    PREVIEW_TYPE_TEXT,
    PREVIEW_TYPE_UNKNOWN,
    PREVIEW_TYPE_VIDEO,
    PREVIEWABLE_TYPES,
    URL_TYPE,
    WEB_CONTENT_ROUTE,
)
from .libreoffice_converter import LibreOfficeConverter
from .preview_cache_manager import PreviewCacheManager

_logger = logging.getLogger(__name__)


class PreviewService:

    def __init__(self, env):
        self.env = env
        self.cache_manager = PreviewCacheManager(env)
        self.converter = LibreOfficeConverter(env)

    def get_preview_type(self, attachment) -> str:
        attachment.ensure_one()
        mimetype = (attachment.mimetype or "").lower()

        if mimetype.startswith("image/"):
            return PREVIEW_TYPE_IMAGE
        if mimetype.startswith("video/"):
            return PREVIEW_TYPE_VIDEO
        if mimetype == PDF_MIMETYPE:
            return PREVIEW_TYPE_PDF
        if self.is_office_attachment(attachment):
            return PREVIEW_TYPE_OFFICE
        if mimetype.startswith("text/"):
            return PREVIEW_TYPE_TEXT
        return PREVIEW_TYPE_UNKNOWN

    def is_previewable(self, attachment) -> bool:
        return self.get_preview_type(attachment) in PREVIEWABLE_TYPES

    def is_office_attachment(self, attachment) -> bool:
        attachment.ensure_one()
        mimetype = (attachment.mimetype or "").lower()
        extension = Path(attachment.name or "").suffix.lower()
        return mimetype in OFFICE_MIME_TYPES or extension in OFFICE_EXTENSIONS

    def get_preview_url(self, attachment, prepare: bool = False) -> str | bool:
        attachment.ensure_one()
        self.ensure_read_access(attachment)

        if attachment.type == URL_TYPE and attachment.url:
            return attachment.url

        preview_type = self.get_preview_type(attachment)
        if preview_type == PREVIEW_TYPE_OFFICE:
            if prepare:
                self.ensure_pdf_preview(attachment)
            return self._office_preview_url(attachment)

        if attachment.id:
            return self._web_content_url(attachment)

        return False

    def ensure_pdf_preview(self, attachment) -> Path:
        attachment.ensure_one()
        self.ensure_read_access(attachment)

        if not self.is_office_attachment(attachment):
            raise UserError(_("This attachment is not an Office file."))
        if attachment.type == URL_TYPE:
            raise UserError(_("Office preview requires a binary attachment stored in Odoo."))
        if self.cache_manager.is_cache_valid(attachment):
            return self.cache_manager.get_preview_path(attachment)

        raw = attachment.raw
        if not raw:
            raise UserError(_("The attachment does not contain file data."))

        original_path = self.cache_manager.write_original(attachment, raw)
        work_dir = Path(
            tempfile.mkdtemp(
                prefix="convert_",
                dir=str(self.cache_manager.ensure_attachment_dir(attachment)),
            )
        )

        try:
            converted_pdf_path = self.converter.convert_to_pdf(original_path, work_dir)
            return self.cache_manager.save_preview(attachment, converted_pdf_path)
        except UserError:
            raise
        except Exception as exc:
            _logger.exception("Unexpected error while preparing PDF preview for attachment %s", attachment.id)
            raise UserError(_("Failed to generate PDF preview: %s") % exc) from exc
        finally:
            shutil.rmtree(work_dir, ignore_errors=True)

    def has_read_access(self, attachment) -> bool:
        try:
            attachment.check_access_rights("read")
            attachment.check_access_rule("read")
        except AccessError:
            return False
        return True

    def ensure_read_access(self, attachment) -> None:
        if not self.has_read_access(attachment):
            raise AccessError(_("You do not have permission to read this attachment."))

    def _office_preview_url(self, attachment) -> str:
        version = self.cache_manager.get_preview_version(attachment)
        query = urlencode({"v": version}) if version else ""
        route = PREVIEW_PDF_ROUTE % attachment.id
        return f"{route}?{query}" if query else route

    def _web_content_url(self, attachment) -> str:
        query_values = {"download": "false"}
        version = self.cache_manager.get_preview_version(attachment)
        if version:
            query_values["v"] = version
        return f"{WEB_CONTENT_ROUTE % attachment.id}?{urlencode(query_values)}"
