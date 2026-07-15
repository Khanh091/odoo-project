# -*- coding: utf-8 -*-
from odoo import models, fields, api, _

class SchoolTeacher(models.Model):
    _name = 'school.teacher'
    _description = 'Giáo viên'
    _rec_name = 'name'

    teacher_code = fields.Char(
        string='Mã giáo viên',
        required=True,
        readonly=True,
        copy=False,
        default=lambda self: _('New')
    )

    name = fields.Char(string='Họ tên', required=True)
    gender = fields.Selection([('male', 'Nam'), ('female', 'Nữ'), ('other', 'Khác')], string='Giới tính')
    birth_date = fields.Date(string='Ngày sinh')
    phone = fields.Char(string='Số điện thoại')
    email = fields.Char(string='Email')
    user_id = fields.Many2one('res.users', string='Người dùng hệ thống', ondelete='set null')
    specialty = fields.Char(string='Chuyên môn')
    start_date = fields.Date(string='Ngày vào làm', default=fields.Date.today)
    school_class_ids = fields.One2many(
        'school.class',
        'teacher_id',
        string='Các lớp chủ nhiệm'
    )

    subject_ids = fields.Many2many(
        'school.subject',
        relation='school_teacher_subject_rel',
        column1='teacher_id',
        column2='subject_id',
        string='Các môn giảng dạy'
    )

    teaching_line_ids = fields.One2many(
        'school.class.teacher.line',
        'teacher_id',
        string='Các lớp đang giảng dạy'
    )
    # Compute Field: Tổng số lớp đang chủ nhiệm
    total_classes = fields.Integer(string='Số lớp chủ nhiệm', compute='_compute_total_classes', store=True)

    _sql_constraints = [
        ('unique_teacher_code', 'unique(teacher_code)', 'Mã giáo viên đã tồn tại!')
    ]

    @api.depends('school_class_ids')
    def _compute_total_classes(self):
        for teacher in self:
            teacher.total_classes = len(teacher.school_class_ids)

    school_class_ids = fields.One2many('school.class', 'teacher_id', string='Các lớp chủ nhiệm')

    def action_view_classes(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Các lớp đang chủ nhiệm',
            'res_model': 'school.class',
            'view_mode': 'tree,form',
            'domain': [('teacher_id', '=', self.id)],
        }

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('teacher_code', _('New')) == _('New'):
                vals['teacher_code'] = self.env['ir.sequence'].next_by_code('school.teacher') or _('New')
        return super().create(vals_list)