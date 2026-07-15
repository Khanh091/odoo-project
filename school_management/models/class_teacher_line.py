# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class SchoolClassTeacherLine(models.Model):
    _name = "school.class.teacher.line"
    _description = "Phân công giáo viên giảng dạy"
    _rec_name = "teacher_id"

    class_id = fields.Many2one(
        "school.class",
        string="Lớp",
        required=True,
        ondelete="cascade"
    )

    subject_id = fields.Many2one(
        "school.subject",
        string="Môn học",
        required=True
    )

    teacher_id = fields.Many2one(
        "school.teacher",
        required=True,
        default=lambda self: self.env.context.get("default_teacher_id")
    )

    _sql_constraints = [
        (
            "unique_class_subject",
            "unique(class_id, subject_id)",
            "Lớp này đã được phân công giáo viên cho môn học này!"
        )
    ]

    @api.onchange("class_id")
    def _onchange_class_id(self):
        self.subject_id = False
        self.teacher_id = False

        if self.class_id:
            return {
                "domain": {
                    "subject_id": [
                        ("id", "in", self.class_id.subject_ids.ids)
                    ]
                }
            }

        return {
            "domain": {
                "subject_id": []
            }
        }

    @api.onchange("subject_id")
    def _onchange_subject_id(self):
        self.teacher_id = False

        if self.subject_id:
            return {
                "domain": {
                    "teacher_id": [
                        ("subject_ids", "in", [self.subject_id.id])
                    ]
                }
            }

        return {
            "domain": {
                "teacher_id": []
            }
        }

    @api.constrains("subject_id", "class_id")
    def _check_subject_in_class(self):
        for record in self:
            if (
                record.class_id
                and record.subject_id
                and record.subject_id not in record.class_id.subject_ids
            ):
                raise ValidationError(_(
                    "Môn học '%s' không thuộc lớp '%s'."
                ) % (
                    record.subject_id.name,
                    record.class_id.name
                ))

    @api.constrains("teacher_id", "subject_id")
    def _check_teacher_can_teach_subject(self):
        for record in self:
            if (
                record.teacher_id
                and record.subject_id
                and record.subject_id not in record.teacher_id.subject_ids
            ):
                raise ValidationError(_(
                    "Giáo viên '%s' không được phân công giảng dạy môn '%s'."
                ) % (
                    record.teacher_id.name,
                    record.subject_id.name
                ))