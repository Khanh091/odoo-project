from urllib.parse import urlparse

from markupsafe import escape

from odoo import _, api, fields, models
from odoo.exceptions import UserError


class CvRepositoryCandidate(models.Model):
    _name = "cv.repository.candidate"
    _description = "Candidate Repository"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "create_date desc"

    name = fields.Char(required=True, tracking=True, index=True)
    email = fields.Char(index=True, tracking=True)
    phone = fields.Char(index=True, tracking=True)
    current_position = fields.Char()
    location = fields.Char()
    summary = fields.Text()
    skill_text = fields.Text(string="Skills")
    education_json = fields.Json(string="Education")
    experience_json = fields.Json(string="Experience")
    certification_json = fields.Json(string="Certifications")
    language_json = fields.Json(string="Languages")
    link_json = fields.Json(string="Links")
    warning_json = fields.Json(string="Warnings")
    skill_display = fields.Html(compute="_compute_json_displays", sanitize=True)
    education_display = fields.Html(
        compute="_compute_json_displays", sanitize=True
    )
    experience_display = fields.Html(
        compute="_compute_json_displays", sanitize=True
    )
    certification_display = fields.Html(
        compute="_compute_json_displays", sanitize=True
    )
    language_display = fields.Html(
        compute="_compute_json_displays", sanitize=True
    )
    link_display = fields.Html(compute="_compute_json_displays", sanitize=True)
    warning_display = fields.Html(
        compute="_compute_json_displays", sanitize=True
    )
    batch_id = fields.Many2one(
        "cv.repository.batch", required=True, ondelete="restrict", index=True
    )
    cv_document_id = fields.Many2one(
        "cv.repository.document", required=True, ondelete="restrict", index=True
    )
    attachment_id = fields.Many2one(
        "ir.attachment",
        related="cv_document_id.attachment_id",
        readonly=True,
    )
    possible_duplicate_id = fields.Many2one(
        "cv.repository.candidate", ondelete="set null", copy=False
    )
    state = fields.Selection(
        [
            ("review", "Waiting for Review"),
            ("approved", "Approved"),
            ("rejected", "Rejected"),
            ("archived", "Archived"),
        ],
        default="review",
        required=True,
        tracking=True,
        index=True,
    )
    approved_by = fields.Many2one("res.users", readonly=True)
    approved_at = fields.Datetime(readonly=True)
    rejected_by = fields.Many2one("res.users", readonly=True)
    rejected_at = fields.Datetime(readonly=True)
    rejection_reason = fields.Text(readonly=True)
    active = fields.Boolean(default=True)

    @api.depends(
        "skill_text",
        "education_json",
        "experience_json",
        "certification_json",
        "language_json",
        "link_json",
        "warning_json",
    )
    def _compute_json_displays(self):
        for candidate in self:
            candidate.skill_display = candidate._render_skills()
            candidate.education_display = candidate._render_timeline(
                candidate.education_json,
                "education",
            )
            candidate.experience_display = candidate._render_timeline(
                candidate.experience_json,
                "experience",
            )
            candidate.certification_display = candidate._render_certifications()
            candidate.language_display = candidate._render_languages()
            candidate.link_display = candidate._render_links()
            candidate.warning_display = candidate._render_warnings()

    def _render_skills(self):
        skills = [skill.strip() for skill in (self.skill_text or "").splitlines()]
        badges = [
            '<span class="badge rounded-pill text-bg-primary px-3 py-2 '
            'fs-6 fw-normal shadow-sm">'
            f'<i class="fa fa-check me-2"/>{escape(skill)}</span>'
            for skill in skills
            if skill
        ]
        if not badges:
            return self._empty_html(_("No skills were extracted."))
        return (
            '<div class="bg-light border rounded p-4">'
            '<div class="d-flex flex-wrap gap-3">%s</div></div>'
            % "".join(badges)
        )

    def _render_timeline(self, items, item_type):
        cards = []
        for item in items or []:
            if not isinstance(item, dict):
                continue
            if item_type == "education":
                title = item.get("school")
                subtitle = " · ".join(
                    self._clean_values([item.get("degree"), item.get("major")])
                )
            else:
                title = item.get("position")
                subtitle = self._clean_value(item.get("company"))
            period = self._format_period(item)
            description = self._clean_value(item.get("description"))
            cards.append(
                self._render_card(title, subtitle, period, description)
            )
        if not cards:
            label = (
                _("No education information was extracted.")
                if item_type == "education"
                else _("No work experience was extracted.")
            )
            return self._empty_html(label)
        return '<div class="vstack gap-3">%s</div>' % "".join(cards)

    def _render_certifications(self):
        cards = []
        for item in self.certification_json or []:
            if not isinstance(item, dict):
                continue
            issuer = self._clean_value(item.get("issuer"))
            issued_date = self._clean_value(item.get("issued_date"))
            date_text = _("Issued: %s") % issued_date if issued_date else ""
            cards.append(
                self._render_card(item.get("name"), issuer, date_text, "")
            )
        if not cards:
            return self._empty_html(_("No certifications were extracted."))
        return '<div class="row g-3">%s</div>' % "".join(
            f'<div class="col-12 col-lg-6">{card}</div>' for card in cards
        )

    def _render_languages(self):
        entries = []
        for item in self.language_json or []:
            if not isinstance(item, dict):
                continue
            name = self._clean_value(item.get("name"))
            level = self._clean_value(item.get("level"))
            if not name:
                continue
            level_html = (
                f'<span class="text-muted ms-2">{escape(level)}</span>'
                if level
                else ""
            )
            entries.append(
                '<div class="card border-0 bg-light"><div class="card-body py-3">'
                f'<strong>{escape(name)}</strong>{level_html}</div></div>'
            )
        if not entries:
            return self._empty_html(_("No languages were extracted."))
        return '<div class="row g-3">%s</div>' % "".join(
            f'<div class="col-12 col-md-6 col-lg-4">{entry}</div>'
            for entry in entries
        )

    def _render_links(self):
        labels = {
            "linkedin": "LinkedIn",
            "github": "GitHub",
            "portfolio": _("Portfolio"),
        }
        links = []
        values = self.link_json if isinstance(self.link_json, dict) else {}
        for key, label in labels.items():
            url = self._safe_url(values.get(key))
            if not url:
                continue
            links.append(
                '<a class="btn btn-outline-primary me-2 mb-2" target="_blank" '
                f'rel="noopener noreferrer" href="{escape(url)}">'
                f'<i class="fa fa-external-link me-1"/> {escape(label)}</a>'
            )
        if not links:
            return self._empty_html(_("No professional links were extracted."))
        return '<div class="py-2">%s</div>' % "".join(links)

    def _render_warnings(self):
        warnings = self.warning_json if isinstance(self.warning_json, list) else []
        rows = [
            '<li class="mb-1">%s</li>' % escape(self._clean_value(warning))
            for warning in warnings
            if self._clean_value(warning)
        ]
        if not rows:
            return (
                '<div class="alert alert-success mb-0">'
                f'<i class="fa fa-check-circle me-2"/> '
                f'{escape(_("No warnings."))}</div>'
            )
        return (
            '<div class="alert alert-warning mb-0">'
            f'<strong>{escape(_("Please review:"))}</strong>'
            f'<ul class="mb-0 mt-2">{"".join(rows)}</ul></div>'
        )

    def _render_card(self, title, subtitle, period, description):
        safe_title = escape(self._clean_value(title) or _("Not specified"))
        subtitle_html = (
            f'<div class="text-muted mt-1">{escape(subtitle)}</div>'
            if subtitle
            else ""
        )
        period_html = (
            '<span class="badge text-bg-light border">%s</span>' % escape(period)
            if period
            else ""
        )
        description_html = (
            '<div class="mt-3" style="white-space: pre-wrap">%s</div>'
            % escape(description)
            if description
            else ""
        )
        return (
            '<div class="card shadow-sm"><div class="card-body">'
            '<div class="d-flex justify-content-between align-items-start gap-3">'
            f'<div><h5 class="card-title mb-0">{safe_title}</h5>'
            f'{subtitle_html}</div>{period_html}</div>{description_html}'
            '</div></div>'
        )

    def _format_period(self, item):
        start_date = self._clean_value(item.get("start_date"))
        end_date = self._clean_value(item.get("end_date"))
        return " – ".join(value for value in (start_date, end_date) if value)

    def _safe_url(self, value):
        url = self._clean_value(value)
        if not url:
            return ""
        candidate_url = url if "://" in url else f"https://{url}"
        parsed = urlparse(candidate_url)
        if parsed.scheme not in ("http", "https") or not parsed.netloc:
            return ""
        return candidate_url

    def _empty_html(self, message):
        return (
            '<div class="text-muted text-center py-5">'
            f'<i class="fa fa-info-circle me-2"/> {escape(message)}</div>'
        )

    def _clean_values(self, values):
        return [value for value in map(self._clean_value, values) if value]

    def _clean_value(self, value):
        return str(value).strip() if value is not None else ""

    def action_approve(self):
        candidates = self.filtered(
            lambda candidate: candidate.state == "review" and candidate.name
        )
        if not candidates:
            raise UserError(_("No valid candidate is waiting for approval."))
        now = fields.Datetime.now()
        for candidate in candidates:
            candidate.write(
                {
                    "state": "approved",
                    "approved_by": self.env.user.id,
                    "approved_at": now,
                    "rejected_by": False,
                    "rejected_at": False,
                    "rejection_reason": False,
                }
            )
            candidate.cv_document_id.state = "approved"
            self.env["cv.repository.processing.log"].create_entry(
                candidate.cv_document_id,
                "approve",
                "success",
                _("Candidate approved."),
                candidate_id=candidate.id,
            )
        candidates.mapped("batch_id")._update_state()
        return True

    def action_reject(self):
        candidates = self.filtered(lambda candidate: candidate.state == "review")
        if not candidates:
            raise UserError(_("No candidate is waiting for rejection."))
        return {
            "type": "ir.actions.act_window",
            "name": _("Reject Candidates"),
            "res_model": "cv.repository.reject.candidate.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {"default_candidate_ids": [(6, 0, candidates.ids)]},
        }

    def _reject_with_reason(self, reason):
        candidates = self.filtered(lambda candidate: candidate.state == "review")
        if not candidates:
            raise UserError(_("No candidate is waiting for rejection."))
        now = fields.Datetime.now()
        for candidate in candidates:
            candidate.write(
                {
                    "state": "rejected",
                    "rejected_by": self.env.user.id,
                    "rejected_at": now,
                    "rejection_reason": reason,
                    "approved_by": False,
                    "approved_at": False,
                }
            )
            candidate.cv_document_id.state = "rejected"
            self.env["cv.repository.processing.log"].create_entry(
                candidate.cv_document_id,
                "reject",
                "success",
                _("Candidate rejected."),
                candidate_id=candidate.id,
            )
        candidates.mapped("batch_id")._update_state()
        return True

    def action_reset_to_review(self):
        candidates = self.filtered(
            lambda candidate: candidate.state in ("approved", "rejected")
        )
        if not candidates:
            raise UserError(_("No approved or rejected candidate was selected."))
        candidates.write(
            {
                "state": "review",
                "approved_by": False,
                "approved_at": False,
                "rejected_by": False,
                "rejected_at": False,
                "rejection_reason": False,
            }
        )
        candidates.mapped("cv_document_id").write({"state": "review"})
        candidates.mapped("batch_id")._update_state()
        return True

    def action_archive(self):
        self.write({"active": False, "state": "archived"})
        self.mapped("batch_id")._update_state()
        return True

    def action_open_cv_document(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("CV Document"),
            "res_model": "cv.repository.document",
            "view_mode": "form",
            "res_id": self.cv_document_id.id,
        }

    def action_download_cv(self):
        self.ensure_one()
        return self.cv_document_id.action_download_cv()
