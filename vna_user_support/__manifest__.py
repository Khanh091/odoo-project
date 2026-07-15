# -*- coding: utf-8 -*-
{
    "name": "VNA User Support",
    "summary": "Quản lý kênh hỗ trợ người dùng nội bộ Vietnam Airlines",
    "description": """
Module quản lý yêu cầu hỗ trợ người dùng nội bộ cho Vietnam Airlines.
Hỗ trợ phân loại yêu cầu, nhóm nghiệp vụ tiếp nhận, email thông báo,
Telegram thông báo yêu cầu mới và theo dõi lịch sử qua chatter.
    """,
    "author": "Vietnam Airlines",
    "website": "https://www.vietnamairlines.com",
    "category": "Services/Helpdesk",
    "version": "17.0.1.0.0",
    "license": "LGPL-3",
    "depends": ["base", "mail", "notification_center"],
    "data": [
        "security/support_security.xml",
        "security/ir.model.access.csv",
        "data/ir_sequence_data.xml",
        "data/support_stage_data.xml",
        "data/support_team_data.xml",
        "data/support_request_type_data.xml",
        "data/mail_template_data.xml",
        "wizard/support_cancel_wizard_views.xml",
        "views/support_request_type_views.xml",
        "views/support_stage_views.xml",
        "views/support_team_views.xml",
        "views/support_request_views.xml",
        "views/res_config_settings_views.xml",
        "views/support_menu.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "vna_user_support/static/src/scss/support_request.scss",
        ],
    },
    "application": True,
    "installable": True,
}
