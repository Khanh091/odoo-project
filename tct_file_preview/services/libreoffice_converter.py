# -*- coding: utf-8 -*-

import logging
import platform
import shutil
import subprocess
import tempfile
from pathlib import Path

from odoo import _
from odoo.exceptions import UserError

from ..utils.constants import (
    CONFIG_PARAM_LIBREOFFICE_PATH,
    CONVERT_TIMEOUT_SECONDS,
    LINUX_LIBREOFFICE_PATHS,
    WINDOWS_LIBREOFFICE_PATH,
)

_logger = logging.getLogger(__name__)


class LibreOfficeConverter:

    def __init__(self, env, timeout: int = CONVERT_TIMEOUT_SECONDS):
        self.env = env
        self.timeout = timeout

    def get_executable_path(self) -> Path:
        configured_path = self._get_config_param(CONFIG_PARAM_LIBREOFFICE_PATH)
        if configured_path:
            return Path(configured_path).expanduser()

        for candidate in self._default_executable_candidates():
            if candidate.is_file():
                return candidate

        return self._default_executable_candidates()[0]

    def is_available(self) -> bool:
        return self.get_executable_path().is_file()

    def convert_to_pdf(self, source_path: Path, output_dir: Path) -> Path:
        source_path = Path(source_path)
        output_dir = Path(output_dir)
        executable_path = self.get_executable_path()

        if not source_path.is_file():
            raise UserError(_("Source file does not exist: %s") % source_path)
        if not executable_path.is_file():
            raise UserError(
                _("LibreOffice executable was not found at %s. Configure %s in System Parameters.")
                % (executable_path, CONFIG_PARAM_LIBREOFFICE_PATH)
            )

        output_dir.mkdir(parents=True, exist_ok=True)
        profile_dir = Path(tempfile.mkdtemp(prefix="lo_profile_", dir=str(output_dir)))

        command = self._build_command(executable_path, source_path, output_dir, profile_dir)
        _logger.info("Converting attachment preview with LibreOffice: %s", source_path)

        try:
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=self.timeout,
                check=False,
                shell=False,
            )
        except subprocess.TimeoutExpired as exc:
            _logger.exception("LibreOffice conversion timed out for %s", source_path)
            raise UserError(_("LibreOffice conversion timed out after %s seconds.") % self.timeout) from exc
        except OSError as exc:
            _logger.exception("Failed to launch LibreOffice executable %s", executable_path)
            raise UserError(_("Failed to launch LibreOffice: %s") % exc) from exc
        finally:
            shutil.rmtree(profile_dir, ignore_errors=True)

        if result.returncode:
            details = (result.stderr or result.stdout or "").strip()
            _logger.error(
                "LibreOffice conversion failed. returncode=%s stdout=%s stderr=%s",
                result.returncode,
                result.stdout,
                result.stderr,
            )
            raise UserError(
                _("LibreOffice failed to convert the file to PDF. Exit code: %s. Details: %s")
                % (result.returncode, details or _("No output was returned by LibreOffice."))
            )

        pdf_path = output_dir / f"{source_path.stem}.pdf"
        if not pdf_path.is_file():
            _logger.error("LibreOffice finished without creating expected PDF: %s", pdf_path)
            raise UserError(_("LibreOffice did not create the expected PDF output."))

        return pdf_path

    def _build_command(
        self,
        executable_path: Path,
        source_path: Path,
        output_dir: Path,
        profile_dir: Path,
    ) -> list[str]:
        return [
            str(executable_path),
            "--headless",
            "--nologo",
            "--nofirststartwizard",
            "--norestore",
            "--nolockcheck",
            f"-env:UserInstallation={profile_dir.resolve().as_uri()}",
            "--convert-to",
            "pdf",
            "--outdir",
            str(output_dir),
            str(source_path),
        ]

    def _default_executable_candidates(self) -> tuple[Path, ...]:
        if platform.system().lower() == "windows":
            return (WINDOWS_LIBREOFFICE_PATH,)
        return LINUX_LIBREOFFICE_PATHS

    def _get_config_param(self, key: str) -> str | None:
        value = self.env["ir.config_parameter"].sudo().get_param(key)
        return value.strip() if value else None
