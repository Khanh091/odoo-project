# -*- coding: utf-8 -*-

from odoo import api, fields, models

from ..services.preview_service import PreviewService
from ..utils.constants import (
    PREVIEW_TYPE_IMAGE,
    PREVIEW_TYPE_OFFICE,
    PREVIEW_TYPE_PDF,
    PREVIEW_TYPE_TEXT,
    PREVIEW_TYPE_VIDEO,
)


class TctFilePreviewWizard(models.TransientModel):
    _name = "tct.file.preview.wizard"
    _description = "TCT File Preview Wizard"

    attachment_id = fields.Many2one(
        "ir.attachment",
        string="Attachment",
        required=True,
        readonly=True,
    )

    name = fields.Char(
        related="attachment_id.name",
        readonly=True,
    )

    preview_type = fields.Selection(
        related="attachment_id.preview_type",
        readonly=True,
    )

    preview_url = fields.Char(
        string="Preview URL",
        readonly=True,
    )

    preview_html = fields.Html(
        string="Preview",
        compute="_compute_preview_html",
        sanitize=False,
        readonly=True,
    )

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        attachment_id = self.env.context.get("default_attachment_id")
        if attachment_id and "preview_url" in fields_list and not res.get("preview_url"):
            attachment = self.env["ir.attachment"].browse(attachment_id)
            if attachment.exists():
                service = PreviewService(self.env)
                res["preview_url"] = service.get_preview_url(attachment, prepare=False)
        return res

    @api.depends("attachment_id", "preview_type", "preview_url")
    def _compute_preview_html(self):
        service = PreviewService(self.env)
        for wizard in self:
            url = wizard.preview_url or ""
            if not url and wizard.attachment_id:
                url = service.get_preview_url(wizard.attachment_id, prepare=False) or ""
            mimetype = wizard.attachment_id.mimetype or ""

            if wizard.preview_type == PREVIEW_TYPE_IMAGE:
                wizard.preview_html = """
                    <div style="text-align:center; width:100%%;">
                        <img src="%s" style="max-width:100%%; max-height:82vh; display:block; margin:0 auto;"/>
                    </div>
                """ % url

            elif wizard.preview_type == PREVIEW_TYPE_VIDEO:
                wizard.preview_html = """
                    <div style="text-align:center; width:100%%;">
                        <video controls style="max-width:100%%; max-height:82vh; display:block; margin:0 auto;">
                            <source src="%s" type="%s"/>
                        </video>
                    </div>
                """ % (url, mimetype)

            elif wizard.preview_type in (PREVIEW_TYPE_PDF, PREVIEW_TYPE_TEXT, PREVIEW_TYPE_OFFICE):
                wizard.preview_html = """
                    <iframe src="%s"
                            style="width:100%%; height:82vh; border:none; display:block;">
                    </iframe>
                """ % url

            else:
                wizard.preview_html = """
                    <div class="alert alert-warning">
                        This file type cannot be previewed.
                    </div>
                """
