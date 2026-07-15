# -*- coding: utf-8 -*-
from odoo import models, fields

class InheritedTeacher(models.Model):
    _inherit = 'school.teacher'

    qualification = fields.Char(string='Trình độ chuyên môn')
    experience_years = fields.Integer(string='Số năm kinh nghiệm')