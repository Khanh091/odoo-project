# -*- coding: utf-8 -*-
from odoo import models, fields, api


class GradeReportWizard(models.TransientModel):
    _name = 'school.grade.report.wizard'
    _description = 'Wizard In Bảng điểm Lớp - Môn'

    class_id = fields.Many2one('school.class', string='Lớp', required=True, readonly=True)
    allowed_subject_ids = fields.Many2many(
        'school.subject',
        related='class_id.subject_ids',
        string='Môn học khả dụng',
        readonly=True,
    )
    subject_id = fields.Many2one('school.subject', string='Môn học', required=True)

    @api.onchange('class_id')
    def _onchange_class_id(self):
        if self.class_id:
            return {'domain': {'subject_id': [('id', 'in', self.allowed_subject_ids.ids)]}}

    def action_print_report(self):
        self.ensure_one()
        return self.env.ref('school_management.report_school_grade_class_subject').report_action(self)