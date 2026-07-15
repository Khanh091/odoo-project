# -*- coding: utf-8 -*-
from odoo import models, fields, api


class SchoolClass(models.Model):
    _name = 'school.class'
    _description = 'Lớp học'
    _rec_name = 'name'

    class_code = fields.Char(string='Mã lớp', required=True, copy=False)
    name = fields.Char(string='Tên lớp', required=True)
    grade_level = fields.Char(string='Khối', required=True)
    school_year = fields.Char(string='Năm học', required=True)

    teacher_id = fields.Many2one('school.teacher', string='Giáo viên chủ nhiệm')
    student_ids = fields.One2many('school.student', 'class_id', string='Danh sách học sinh')
    subject_ids = fields.Many2many(
        'school.subject',
        string='Các môn học',
        relation='school_class_subject_rel', 
        column1='class_id',
        column2='subject_id'
    )
    teaching_line_ids = fields.One2many(
        'school.class.teacher.line',
        'class_id',
        string='Giáo viên giảng dạy'
    )
    #compute field: Tổng số học sinh
    total_students = fields.Integer(string='Tổng số học sinh', compute='_compute_total_students', store=True)

    _sql_constraints = [
        ('unique_class_code', 'unique(class_code)', 'Mã lớp đã tồn tại!')
    ]

    @api.depends('student_ids')
    def _compute_total_students(self):
        for record in self:
            record.total_students = len(record.student_ids)

    @api.onchange('subject_ids')
    def _onchange_subject_ids(self):
        if not self.subject_ids:
            self.teaching_line_ids = [(5, 0, 0)]
            return

        valid_subjects = self.subject_ids.ids

        self.teaching_line_ids = self.teaching_line_ids.filtered(
            lambda line: line.subject_id.id in valid_subjects
        )
    # Smart Button
    def action_view_students(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': f'Học sinh lớp {self.name}',
            'res_model': 'school.student',
            'view_mode': 'tree,form,kanban',
            'domain': [('class_id', '=', self.id)],
            'context': {'default_class_id': self.id},
        }