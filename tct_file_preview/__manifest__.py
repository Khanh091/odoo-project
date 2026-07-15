# -*- coding: utf-8 -*-

{
    "name": "TCT File Preview",
    "summary": "Preview uploaded files directly in Odoo",
    "description": """
        Preview image, video, PDF, Word, Excel files directly in Odoo
        without downloading them first.
    """,
    "version": "17.0.1.0.0",
    "category": "Tools",
    "author": "TCT",
    "license": "LGPL-3",
    "depends": [
        "base",
        "web",
    ],
    "data": [
        "security/ir.model.access.csv",
        "views/ir_attachment_views.xml",
        "views/file_preview_wizard_views.xml",
        "views/file_preview_templates.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "tct_file_preview/static/src/scss/file_preview_wizard.scss",
            "tct_file_preview/static/src/js/attachment_preview_gallery.js",
            "tct_file_preview/static/src/xml/attachment_preview_gallery.xml",
            "tct_file_preview/static/src/scss/attachment_preview_gallery.scss",
        ],
    },
    "installable": True,
    "application": True,
    "auto_install": False,
}
