{
    "name": "Google OAuth Login",
    "version": "17.0.1.0.0",
    "summary": "Secure Google OAuth login for Odoo",
    "description": """
Google OAuth Login
==================

Reusable Google OAuth login based on Odoo's standard auth_oauth module.
    """,
    "category": "Authentication",
    "license": "LGPL-3",
    "depends": [
        "auth_oauth",
    ],
    "data": [
        "data/oauth_provider_data.xml",
        "views/res_config_settings_views.xml",
    ],
    "installable": True,
    "application": True,
    "auto_install": False,
}
