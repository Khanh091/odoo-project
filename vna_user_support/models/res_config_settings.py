# -*- coding: utf-8 -*-

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    vna_support_telegram_enabled = fields.Boolean(
        string="Bật thông báo Telegram",
        config_parameter="vna_user_support.telegram_enabled",
    )
    vna_support_telegram_bot_token = fields.Char(
        string="Telegram Bot Token",
        config_parameter="vna_user_support.telegram_bot_token",
    )
    vna_support_telegram_chat_id = fields.Char(
        string="Telegram Group Chat ID",
        config_parameter="vna_user_support.telegram_chat_id",
    )
