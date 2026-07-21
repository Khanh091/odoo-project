from odoo import _, models
from odoo.exceptions import ValidationError


class CandidateCreationService(models.AbstractModel):
    _name = "cv.repository.candidate.creation.service"
    _description = "Candidate Creation Service"

    def create_or_update_from_ai_result(self, batch, document, ai_result):
        batch.ensure_one()
        document.ensure_one()
        if not isinstance(ai_result, dict) or not ai_result.get("full_name"):
            raise ValidationError(_("Valid AI candidate data is required."))
        if document.batch_id != batch:
            raise ValidationError(_("The CV document does not belong to this batch."))

        existing = document.candidate_id
        duplicate, duplicate_kind = self.env[
            "cv.repository.duplicate.candidate.service"
        ].find_duplicate(ai_result, exclude_candidate=existing)
        warnings = list(ai_result.get("warnings") or [])
        if duplicate_kind == "email":
            warnings.append(_("A candidate with the same email already exists."))
        elif duplicate_kind == "phone":
            warnings.append(
                _("A candidate with the same phone number already exists.")
            )

        values = {
            "name": ai_result["full_name"],
            "email": ai_result.get("email"),
            "phone": ai_result.get("phone"),
            "current_position": ai_result.get("current_position"),
            "location": ai_result.get("location"),
            "summary": ai_result.get("summary"),
            "skill_text": "\n".join(ai_result.get("skills") or []),
            "education_json": ai_result.get("education") or [],
            "experience_json": ai_result.get("experiences") or [],
            "certification_json": ai_result.get("certifications") or [],
            "language_json": ai_result.get("languages") or [],
            "link_json": ai_result.get("links") or {},
            "warning_json": warnings,
            "batch_id": batch.id,
            "cv_document_id": document.id,
            "possible_duplicate_id": duplicate.id or False,
            "state": "review",
            "active": True,
            "approved_by": False,
            "approved_at": False,
            "rejected_by": False,
            "rejected_at": False,
            "rejection_reason": False,
        }
        if existing:
            existing.write(values)
            return existing
        return self.env["cv.repository.candidate"].create(values)
