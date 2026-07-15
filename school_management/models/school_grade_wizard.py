# -*- coding: utf-8 -*-
from odoo import models, fields, api


class SchoolGradeWizard(models.TransientModel):
    _name = 'school.grade.wizard'
    _description = 'Wizard Nhập Điểm Hàng Loạt'

    class_id = fields.Many2one('school.class', string='Lớp', required=True, readonly=True)
    allowed_subject_ids = fields.Many2many(
        'school.subject',
        related='class_id.subject_ids',
        string='Môn học khả dụng',
        readonly=True,
    )
    subject_id = fields.Many2one('school.subject', string='Môn học', required=True)

    line_ids = fields.One2many('school.grade.wizard.line', 'wizard_id', string='Danh sách học sinh')

    @api.onchange('subject_id')
    def _onchange_subject(self):
        if not self.class_id or not self.subject_id:
            self.line_ids = False
            return

        students = self.class_id.student_ids
        lines = []
        for student in students:
            # Tìm điểm cũ nếu có
            existing = self.env['school.grade'].search([
                ('student_id', '=', student.id),
                ('subject_id', '=', self.subject_id.id)
            ], limit=1)

            lines.append((0, 0, {
                'student_id': student.id,
                'midterm_score': existing.midterm_score if existing else 0.0,
                'final_score': existing.final_score if existing else 0.0,
            }))
        self.line_ids = [(5, 0, 0)] + lines

    def action_save_grades(self):
        """Lưu tất cả điểm"""
        for line in self.line_ids:
            self.env['school.grade'].create_or_update_grade(
                line.student_id,
                self.subject_id,
                line.midterm_score,
                line.final_score
            )
        return {'type': 'ir.actions.act_window_close'}

    @api.onchange('class_id')
    def _onchange_class_id(self):
        if self.class_id:
            return {
                'domain': {
                    'subject_id': [('id', 'in', self.class_id.subject_ids.ids)]
                }
            }
    def action_print_report(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'In Bảng điểm',
            'res_model': 'school.grade.report.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_class_id': self.class_id.id,
                'default_subject_id': self.subject_id.id,
            },
        }
class SchoolGradeWizardLine(models.TransientModel):
    _name = 'school.grade.wizard.line'
    _description = 'Dòng nhập điểm'

    wizard_id = fields.Many2one('school.grade.wizard')
    student_id = fields.Many2one('school.student', string='Học sinh', readonly=True)
    midterm_score = fields.Float(string='Điểm giữa kỳ', digits=(5, 2))
    final_score = fields.Float(string='Điểm cuối kỳ', digits=(5, 2))