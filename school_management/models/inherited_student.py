# -*- coding: utf-8 -*-
from odoo import models, fields

class InheritedStudent(models.Model):
    _inherit = 'school.student'

    parent_name = fields.Char(string='Tên phụ huynh')
    parent_phone = fields.Char(string='SĐT phụ huynh')
    blood_type = fields.Selection([
        ('A', 'A'), ('B', 'B'), ('AB', 'AB'), ('O', 'O')
    ], string='Nhóm máu')
    emergency_contact = fields.Char(string='Liên hệ khẩn cấp')

    def write(self, vals):
        res = super().write(vals)

        if 'class_id' in vals:
            for student in self:
                if student.class_id:
                    student.teacher_id = student.class_id.teacher_id

        return res