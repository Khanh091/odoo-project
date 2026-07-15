# -*- coding: utf-8 -*-

{
    "name": "TCT High Privilege 2FA",
    "version": "17.0.1.0.0",
    "summary": "Enforce MFA and IP whitelist for high privilege users",
    "description": """
TCT High Privilege 2FA

Features:
- Enforce MFA (Google Authenticator / TOTP) for high privilege users
- IP whitelist restriction for login
- Integration with auth_totp module
- Policy-based security layer (no auth override)
""",
    "category": "Security",
    "author": "TCT",
    "license": "LGPL-3",
    "application": True,
    "installable": True,
    "auto_install": False,

    "depends": [
        "base",
        "auth_totp",
        "portal",
    ],

    "data": [
        'security/groups.xml',
        "security/security.xml",
        "security/ir.model.access.csv",

        "data/ir_config_parameter.xml",

        "views/res_config_settings_views.xml",
        "views/allowed_ip_views.xml",
        "views/actions.xml",
        "views/menu.xml",
        "views/res_users_views.xml",
        'views/mfa_templates.xml',
        "views/portal_frontend_fix.xml",
    ],
}
