# -*- coding: utf-8 -*-

import json
import logging
from html import escape
from urllib import request as urlrequest
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode

from odoo import models

_logger = logging.getLogger(__name__)


class VnaSupportTelegramService(models.AbstractModel):
    _name = "vna.support.telegram.service"
    _description = "Dịch vụ gửi Telegram cho kênh hỗ trợ VNA"

    def _get_telegram_config(self):
        params = self.env["ir.config_parameter"].sudo()
        enabled = params.get_param("vna_user_support.telegram_enabled") == "True"
        token = params.get_param("vna_user_support.telegram_bot_token")
        chat_id = params.get_param("vna_user_support.telegram_chat_id")
        return enabled, token, chat_id

    def send_new_request_message(self, support_request):
        enabled, token, chat_id = self._get_telegram_config()
        if not enabled:
            return False
        if not token or not chat_id:
            _logger.warning("VNA support Telegram is enabled but token or chat ID is not configured.")
            return False

        text = self._prepare_new_request_message(support_request)
        payload = json.dumps(
            {
                "chat_id": chat_id,
                "text": text,
                "parse_mode": "HTML",
                "disable_web_page_preview": True,
            }
        ).encode("utf-8")
        endpoint = "https://api.telegram.org/bot%s/sendMessage" % token
        req = urlrequest.Request(
            endpoint,
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urlrequest.urlopen(req, timeout=10) as response:
                if response.status >= 300:
                    _logger.warning("VNA support Telegram send failed with HTTP status %s.", response.status)
                    return False
            return True
        except (HTTPError, URLError, TimeoutError, OSError) as exc:
            _logger.warning("VNA support Telegram send failed: %s", exc.__class__.__name__)
            return False

    def _prepare_new_request_message(self, support_request):
        base_url = (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param("web.base.url", "")
            .rstrip("/")
        )

        raw_url = ""
        escaped_url = ""
        if base_url:
            query = urlencode({
                "id": support_request.id,
                "model": support_request._name,
                "view_type": "form",
            })
            raw_url = f"{base_url}/web#{query}"
            escaped_url = escape(raw_url, quote=True)

        priority_selection = dict(support_request._fields["priority"].selection)

        lines = [
            "<b>Yêu cầu hỗ trợ mới</b>",
            f"Mã: {escape(support_request.code or support_request.display_name or '')}",
            f"Tiêu đề: {escape(support_request.name or '')}",
            f"Người tạo: {escape(support_request.requester_id.name or '')}",
            f"Loại yêu cầu: {escape(support_request.request_type_id.display_name or '')}",
            f"Mức ưu tiên: {escape(priority_selection.get(support_request.priority, ''))}",
        ]

        if raw_url:
            lines.extend([
                "",
                f'<a href="{escaped_url}">Xem chi tiết yêu cầu</a>',
                escape(raw_url),
            ])

        return "\n".join(lines)
