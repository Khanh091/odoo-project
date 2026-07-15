# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class SchoolGrade(models.Model):
    _name = 'school.grade'
    _description = 'Bảng điểm'
    _rec_name = 'student_id'

    student_id = fields.Many2one('school.student', string='Học sinh', required=True, ondelete='cascade')
    subject_id = fields.Many2one('school.subject', string='Môn học', required=True)
    class_id = fields.Many2one('school.class', string='Lớp',
                               related='student_id.class_id', store=True, readonly=True)

    midterm_score = fields.Float(string='Điểm giữa kỳ', digits=(5, 2))
    final_score = fields.Float(string='Điểm cuối kỳ', digits=(5, 2))
    average_score = fields.Float(string='Điểm trung bình', compute='_compute_average', store=True, digits=(5, 2))
    classification = fields.Char(string='Xếp loại', compute='_compute_classification', store=True)

    _sql_constraints = [
        ('unique_student_subject', 'unique(student_id, subject_id)', 'Học sinh đã có điểm môn này!')
    ]

    @api.onchange('student_id')
    def _onchange_student_id(self):
        if self.student_id:
            self.class_id = self.student_id.class_id

            # Tự động gợi ý môn học đầu tiên của lớp
            if self.student_id.class_id and self.student_id.class_id.subject_ids:
                self.subject_id = self.student_id.class_id.subject_ids[0].id

    @api.onchange('class_id')
    def _onchange_class_id(self):
        if self.class_id:
            # Lọc học sinh theo lớp
            return {'domain': {'student_id': [('class_id', '=', self.class_id.id)]}}
    @api.depends('midterm_score', 'final_score')
    def _compute_average(self):
        for record in self:
            if record.midterm_score or record.final_score:
                record.average_score = (record.midterm_score + record.final_score * 2) / 3
            else:
                record.average_score = 0.0

    @api.depends('average_score')
    def _compute_classification(self):
        for record in self:
            avg = record.average_score
            if avg >= 9.0:
                record.classification = 'Xuất sắc'
            elif avg >= 8.0:
                record.classification = 'Giỏi'
            elif avg >= 7.0:
                record.classification = 'Khá'
            elif avg >= 5.0:
                record.classification = 'Trung bình'
            else:
                record.classification = 'Yếu'

    @api.onchange('midterm_score', 'final_score')
    def _onchange_scores(self):
        if self.midterm_score or self.final_score:
            self.average_score = (self.midterm_score + self.final_score * 2) / 3

    # Ràng buộc quan trọng: Môn phải thuộc lớp của học sinh
    @api.constrains('student_id', 'subject_id')
    def _check_subject_in_class(self):
        for record in self:
            if record.student_id and record.student_id.class_id and record.subject_id:
                if record.subject_id not in record.student_id.class_id.subject_ids:
                    raise ValidationError(_(
                        "Môn học '%s' không thuộc lớp '%s' của học sinh %s!"
                    ) % (record.subject_id.name, record.student_id.class_id.name, record.student_id.name))

    # Validation điểm
    @api.constrains('midterm_score', 'final_score')
    def _check_score_range(self):
        for record in self:
            if record.midterm_score and not (0 <= record.midterm_score <= 10):
                raise ValidationError(_("Điểm giữa kỳ phải nằm trong khoảng từ 0 đến 10!"))
            if record.final_score and not (0 <= record.final_score <= 10):
                raise ValidationError(_("Điểm cuối kỳ phải nằm trong khoảng từ 0 đến 10!"))
    @api.model
    def create_or_update_grade(self, student, subject, midterm, final):
        grade = self.search([('student_id', '=', student.id), ('subject_id', '=', subject.id)], limit=1)
        if grade:
            grade.write({
                'midterm_score': midterm,
                'final_score': final,
            })
        else:
            self.create({
                'student_id': student.id,
                'subject_id': subject.id,
                'midterm_score': midterm,
                'final_score': final,
            })