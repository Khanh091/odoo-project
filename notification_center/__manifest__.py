{
    "name": "Notification Center",
    "version": "17.0.1.0.0",
    "category": "Tools",
    "summary": "Generic realtime notification center for Odoo",
    "depends": [
        "base",
        "web",
        "bus",
    ],
    "data": [
        "security/notification_security.xml",
        "security/ir.model.access.csv",
        "views/notification_views.xml",
        "views/notification_menu.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "notification_center/static/src/js/notification_service.js",
            "notification_center/static/src/js/notification_systray.js",
            "notification_center/static/src/xml/notification_systray.xml",
            "notification_center/static/src/scss/notification_center.scss",
        ],
    },
    "application": True,
    "installable": True,
    "license": "LGPL-3",
}
