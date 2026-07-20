{
    "name": "CV AI",
    "version": "17.0.1.0.0",
    "category": "Human Resources",
    "summary": "Extract candidate information from CV attachments using AI",
    "depends": ["base"],
    "data": [
        "views/res_config_settings_views.xml",
    ],
    "external_dependencies": {
        "python": ["requests", "fitz", "docx"],
    },
    "installable": True,
    "application": False,
    "license": "LGPL-3",
}
