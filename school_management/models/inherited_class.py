# -*- coding: utf-8 -*-
from odoo import models, fields

class InheritedClass(models.Model):
    _inherit = 'school.class'

    room_number = fields.Char(string='Phòng học')
    max_students = fields.Integer(string='Sĩ số tối đa', default=45)
    is_active = fields.Boolean(string='Đang hoạt động', default=True)