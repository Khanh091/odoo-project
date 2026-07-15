# -*- coding: utf-8 -*-

import json
from datetime import timezone
from pathlib import Path
from typing import Any

from odoo import fields, tools

from ..utils.constants import (
    CACHE_ATTACHMENT_DIR_PREFIX,
    CACHE_METADATA_FILENAME,
    CACHE_ORIGINAL_STEM,
    CACHE_PREVIEW_FILENAME,
    CACHE_ROOT_NAME,
    CONFIG_PARAM_CACHE_PATH,
)


class PreviewCacheManager:

    def __init__(self, env):
        self.env = env

    def get_cache_root(self) -> Path:
        configured_path = self._get_config_param(CONFIG_PARAM_CACHE_PATH)
        if configured_path:
            return Path(configured_path).expanduser()
        return Path(tools.config["data_dir"]) / CACHE_ROOT_NAME

    def get_attachment_dir(self, attachment) -> Path:
        attachment.ensure_one()
        return self.get_cache_root() / f"{CACHE_ATTACHMENT_DIR_PREFIX}{attachment.id}"

    def get_original_path(self, attachment) -> Path:
        attachment.ensure_one()
        extension = Path(attachment.name or "").suffix
        return self.get_attachment_dir(attachment) / f"{CACHE_ORIGINAL_STEM}{extension}"

    def get_preview_path(self, attachment) -> Path:
        return self.get_attachment_dir(attachment) / CACHE_PREVIEW_FILENAME

    def get_metadata_path(self, attachment) -> Path:
        return self.get_attachment_dir(attachment) / CACHE_METADATA_FILENAME

    def ensure_attachment_dir(self, attachment) -> Path:
        cache_dir = self.get_attachment_dir(attachment)
        cache_dir.mkdir(parents=True, exist_ok=True)
        return cache_dir

    def is_cache_valid(self, attachment) -> bool:
        preview_path = self.get_preview_path(attachment)
        original_path = self.get_original_path(attachment)
        metadata_path = self.get_metadata_path(attachment)

        if not preview_path.is_file() or not original_path.is_file() or not metadata_path.is_file():
            return False
        if original_path.stat().st_mtime > preview_path.stat().st_mtime:
            return False

        metadata = self._read_metadata(metadata_path)
        return metadata == self._build_metadata(attachment)

    def write_original(self, attachment, content: bytes) -> Path:
        self.ensure_attachment_dir(attachment)
        original_path = self.get_original_path(attachment)
        original_path.write_bytes(content)
        return original_path

    def save_preview(self, attachment, converted_pdf_path: Path) -> Path:
        preview_path = self.get_preview_path(attachment)
        if preview_path.exists():
            preview_path.unlink()
        converted_pdf_path.replace(preview_path)
        self._write_metadata(self.get_metadata_path(attachment), attachment)
        return preview_path

    def get_preview_version(self, attachment) -> str | None:
        source_dt = self._safe_datetime_value(attachment.write_date or attachment.create_date)
        if not source_dt:
            return None
        return source_dt.strftime("%Y%m%d%H%M%S")

    def _build_metadata(self, attachment) -> dict[str, Any]:
        return {
            "attachment_id": attachment.id,
            "write_date": self.get_preview_version(attachment),
            "checksum": attachment.checksum or "",
            "file_size": attachment.file_size or 0,
            "name": attachment.name or "",
            "mimetype": attachment.mimetype or "",
        }

    def _read_metadata(self, metadata_path: Path) -> dict[str, Any]:
        try:
            return json.loads(metadata_path.read_text(encoding="utf-8"))
        except Exception:
            return {}

    def _write_metadata(self, metadata_path: Path, attachment) -> None:
        metadata_path.write_text(
            json.dumps(self._build_metadata(attachment), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def _get_config_param(self, key: str) -> str | None:
        value = self.env["ir.config_parameter"].sudo().get_param(key)
        return value.strip() if value else None

    @staticmethod
    def _safe_datetime_value(value):
        if not value:
            return None
        if isinstance(value, str):
            value = fields.Datetime.to_datetime(value)
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)
