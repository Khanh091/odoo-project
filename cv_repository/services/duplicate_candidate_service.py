import re

from odoo import models


class DuplicateCandidateService(models.AbstractModel):
    _name = "cv.repository.duplicate.candidate.service"
    _description = "Duplicate Candidate Service"

    def find_duplicate(self, candidate_data, exclude_candidate=None):
        """Find a possible duplicate by email, or normalized phone as fallback."""
        domain = []
        if exclude_candidate:
            domain.append(("id", "!=", exclude_candidate.id))
        email = (candidate_data.get("email") or "").strip().lower()
        if email:
            duplicate = self.env["cv.repository.candidate"].search(
                domain + [("email", "=ilike", email)], limit=1
            )
            if duplicate:
                return duplicate, "email"
            return self.env["cv.repository.candidate"], None

        phone = self._normalize_phone(candidate_data.get("phone"))
        if phone:
            candidates = self.env["cv.repository.candidate"].search(
                domain + [("phone", "!=", False)]
            )
            duplicate = candidates.filtered(
                lambda candidate: self._normalize_phone(candidate.phone) == phone
            )[:1]
            if duplicate:
                return duplicate, "phone"
        return self.env["cv.repository.candidate"], None

    def _normalize_phone(self, value):
        return re.sub(r"[\s\-\.()]", "", value or "")
