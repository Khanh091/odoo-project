# -*- coding: utf-8 -*-

from pathlib import Path


CONFIG_PARAM_LIBREOFFICE_PATH = "tct_file_preview.libreoffice_path"
CONFIG_PARAM_CACHE_PATH = "tct_file_preview.cache_path"

WINDOWS_LIBREOFFICE_PATH = Path(r"C:\Program Files\LibreOffice\program\soffice.exe")
LINUX_LIBREOFFICE_PATHS = (
    Path("/usr/bin/libreoffice"),
    Path("/usr/bin/soffice"),
)

CACHE_ROOT_NAME = "tct_file_preview_cache"
CACHE_ATTACHMENT_DIR_PREFIX = "attachment_"
CACHE_ORIGINAL_STEM = "original"
CACHE_PREVIEW_FILENAME = "preview.pdf"
CACHE_METADATA_FILENAME = "metadata.json"

CONVERT_TIMEOUT_SECONDS = 300
PREVIEW_PDF_ROUTE = "/tct_file_preview/preview/pdf/%s"
WEB_CONTENT_ROUTE = "/web/content/%s"

PREVIEW_TYPE_IMAGE = "image"
PREVIEW_TYPE_VIDEO = "video"
PREVIEW_TYPE_PDF = "pdf"
PREVIEW_TYPE_OFFICE = "office"
PREVIEW_TYPE_TEXT = "text"
PREVIEW_TYPE_UNKNOWN = "unknown"

PREVIEWABLE_TYPES = (
    PREVIEW_TYPE_IMAGE,
    PREVIEW_TYPE_VIDEO,
    PREVIEW_TYPE_PDF,
    PREVIEW_TYPE_OFFICE,
    PREVIEW_TYPE_TEXT,
)

OFFICE_MIME_TYPES = {
    "application/msword",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/vnd.ms-excel",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "application/vnd.ms-powerpoint",
    "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    "application/csv",
    "text/csv",
}

OFFICE_EXTENSIONS = {
    ".doc",
    ".docx",
    ".xls",
    ".xlsx",
    ".csv",
    ".ppt",
    ".pptx",
}

PDF_MIMETYPE = "application/pdf"
URL_TYPE = "url"
