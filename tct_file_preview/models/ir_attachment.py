# -*- coding: utf-8 -*-

from odoo import api, fields, models

from ..services.preview_service import PreviewService
from ..utils.constants import (
    PREVIEW_TYPE_IMAGE,
    PREVIEW_TYPE_OFFICE,
    PREVIEW_TYPE_PDF,
    PREVIEW_TYPE_TEXT,
    PREVIEW_TYPE_UNKNOWN,
    PREVIEW_TYPE_VIDEO,
    PREVIEWABLE_TYPES,
)


class IrAttachment(models.Model):
    _inherit = "ir.attachment"

    preview_type = fields.Selection(
        selection=[
            (PREVIEW_TYPE_IMAGE, "Image"),
            (PREVIEW_TYPE_VIDEO, "Video"),
            (PREVIEW_TYPE_PDF, "PDF"),
            (PREVIEW_TYPE_OFFICE, "Office Document"),
            (PREVIEW_TYPE_TEXT, "Text"),
            (PREVIEW_TYPE_UNKNOWN, "Unknown"),
        ],
        string="Preview Type",
        compute="_compute_preview_type",
        store=False,
    )

    preview_url = fields.Char(
        string="Preview URL",
        compute="_compute_preview_url",
        store=False,
    )

    can_preview = fields.Boolean(
        string="Can Preview",
        compute="_compute_can_preview",
        store=False,
    )

    @api.depends("mimetype", "url", "type", "name")
    def _compute_preview_type(self):
        service = PreviewService(self.env)
        for attachment in self:
            attachment.preview_type = service.get_preview_type(attachment)

    @api.depends("preview_type")
    def _compute_can_preview(self):
        for attachment in self:
            attachment.can_preview = attachment.preview_type in PREVIEWABLE_TYPES

    @api.depends("type", "url", "mimetype", "name", "write_date", "create_date", "checksum", "file_size")
    def _compute_preview_url(self):
        service = PreviewService(self.env)
        for attachment in self:
            attachment.preview_url = service.get_preview_url(attachment, prepare=False)

    def action_preview_file(self):
        self.ensure_one()
        service = PreviewService(self.env)
        preview_url = service.get_preview_url(self, prepare=True)
        form_view = self.env.ref(
            "tct_file_preview.view_tct_file_preview_wizard_form"
        )

        wizard = self.env["tct.file.preview.wizard"].create({
            "attachment_id": self.id,
            "preview_url": preview_url,
        })

        return {
            "type": "ir.actions.act_window",
            "name": "File Preview",
            "res_model": "tct.file.preview.wizard",
            "res_id": wizard.id,
            "view_mode": "form",
            "views": [(form_view.id, "form")],
            "target": "new",
            "context": dict(self.env.context, dialog_size="extra-large"),
        }
