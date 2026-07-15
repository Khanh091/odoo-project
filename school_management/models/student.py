# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import date


class SchoolStudent(models.Model):
    _name = 'school.student'
    _description = 'Học sinh'
    _rec_name = 'name'

    student_code = fields.Char(
        string='Mã học sinh',
        required=True,
        readonly=True,
        copy=False,
        default=lambda self: _('New')
    )

    name = fields.Char(string='Họ và tên', required=True)
    image = fields.Binary(string='Ảnh đại diện')

    gender = fields.Selection([
        ('male', 'Nam'),
        ('female', 'Nữ'),
        ('other', 'Khác')
    ], string='Giới tính', required=True)

    birth_date = fields.Date(string='Ngày sinh', required=True)
    age = fields.Integer(string='Tuổi', compute='_compute_age', store=True)

    phone = fields.Char(string='Số điện thoại')
    email = fields.Char(string='Email')
    address = fields.Text(string='Địa chỉ')

    status = fields.Selection([
        ('studying', 'Đang học'),
        ('dropped', 'Nghỉ học'),
        ('graduated', 'Tốt nghiệp')
    ], string='Trạng thái', default='studying')

    class_id = fields.Many2one('school.class', string='Lớp đang học')
    teacher_id = fields.Many2one('school.teacher', string='Giáo viên chủ nhiệm', related='class_id.teacher_id',
                                 store=True)

    note = fields.Text(string='Ghi chú')
    grade_ids = fields.One2many('school.grade', 'student_id', string='Bảng điểm')
    attachment_ids = fields.Many2many(
        'ir.attachment',
        'school_student_attachment_rel',
        'student_id',
        'attachment_id',
        string='Upload Hồ sơ',
        copy=False,
    )

    _sql_constraints = [
        ('unique_student_email', 'unique(email)', 'Email đã tồn tại!'),
        ('unique_student_code', 'unique(student_code)', 'Mã học sinh đã tồn tại!')
    ]
    available_subject_ids = fields.Many2many(
        'school.subject',
        compute='_compute_available_subjects',
        string='Môn học khả dụng'
    )
    
    @api.depends('class_id')
    def _compute_available_subjects(self):
        for student in self:
            student.available_subject_ids = student.class_id.subject_ids if student.class_id else False 
    @api.depends('birth_date')
    def _compute_age(self):
        for student in self:
            if student.birth_date:
                today = date.today()
                student.age = today.year - student.birth_date.year - (
                        (today.month, today.day) < (student.birth_date.month, student.birth_date.day)
                )
            else:
                student.age = 0

    @api.constrains('birth_date')
    def _check_birth_date(self):
        for record in self:
            if record.birth_date and record.birth_date > date.today():
                raise ValidationError(_("Ngày sinh không được lớn hơn ngày hiện tại!"))

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('student_code', _('New')) == _('New'):
                vals['student_code'] = self.env['ir.sequence'].next_by_code('school.student') or _('New')
        return super().create(vals_list)

    def action_open_grades(self):
        self.ensure_one()
        domain = [('student_id', '=', self.id)]
        context = {'default_student_id': self.id}

        if self.class_id:
            context['default_class_id'] = self.class_id.id  # nếu cần

        return {
            'type': 'ir.actions.act_window',
            'name': f'Điểm của {self.name}',
            'res_model': 'school.grade',
            'view_mode': 'tree,form',
            'domain': domain,
            'context': context,
            'target': 'current',
        }
    @api.onchange('class_id')
    def _onchange_class_id(self):
        if self.class_id:
            self.teacher_id = self.class_id.teacher_id
