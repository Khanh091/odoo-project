# -*- coding: utf-8 -*-
from odoo import models, fields

class SchoolSubject(models.Model):
    _name = 'school.subject'
    _description = 'Môn học'
    _rec_name = 'name'

    subject_code = fields.Char(string='Mã môn học', required=True, copy=False)
    name = fields.Char(string='Tên môn học', required=True)
    credits = fields.Integer(string='Số tín chỉ', default=2)
    teacher_ids = fields.Many2many(
        'school.teacher',
        relation='school_teacher_subject_rel',
        column1='subject_id',
        column2='teacher_id',
        string='Giáo viên giảng dạy'
    )

    teaching_line_ids = fields.One2many(
        'school.class.teacher.line',
        'subject_id',
        string='Phân công giảng dạy'
    )
    _sql_constraints = [
        ('unique_subject_code', 'unique(subject_code)', 'Mã môn học đã tồn tại!')
    ]