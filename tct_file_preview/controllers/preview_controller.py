# -*- coding: utf-8 -*-

from pathlib import Path

from odoo import http
from odoo.http import content_disposition, request
from werkzeug.exceptions import NotFound, Forbidden

from ..services.preview_service import PreviewService


class TctFilePreviewController(http.Controller):

    @http.route(
        "/tct_file_preview/preview/<int:attachment_id>",
        type="http",
        auth="user",
        website=False,
    )
    def preview_file(self, attachment_id, **kwargs):
        attachment = request.env["ir.attachment"].browse(attachment_id)

        if not attachment.exists():
            raise NotFound()

        service = PreviewService(request.env)
        if not service.has_read_access(attachment):
            raise Forbidden()

        preview_type = service.get_preview_type(attachment)
        if not service.is_previewable(attachment):
            raise Forbidden("This file type cannot be previewed")

        preview_url = service.get_preview_url(attachment, prepare=True)

        return request.render(
            "tct_file_preview.file_preview_page",
            {
                "attachment": attachment,
                "preview_type": preview_type,
                "preview_url": preview_url,
            },
        )

    @http.route(
        "/tct_file_preview/preview/pdf/<int:attachment_id>",
        type="http",
        auth="user",
        website=False,
    )
    def preview_pdf(self, attachment_id, **kwargs):
        attachment = request.env["ir.attachment"].browse(attachment_id)

        if not attachment.exists():
            raise NotFound()

        service = PreviewService(request.env)
        if not service.has_read_access(attachment):
            raise Forbidden()

        pdf_path = service.ensure_pdf_preview(attachment)
        pdf_bytes = pdf_path.read_bytes()
        filename = f"{Path(attachment.name or pdf_path.name).stem}.pdf"

        return request.make_response(
            pdf_bytes,
            headers=[
                ("Content-Type", "application/pdf"),
                ("Content-Length", str(len(pdf_bytes))),
                ("Content-Disposition", content_disposition(filename, disposition_type="inline")),
                ("Cache-Control", "private, no-cache, no-store, must-revalidate"),
                ("Pragma", "no-cache"),
            ],
        )
