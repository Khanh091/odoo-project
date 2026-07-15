# -*- coding: utf-8 -*-
from odoo import models, fields

class InheritedGrade(models.Model):
    _inherit = 'school.grade'

    comment = fields.Text(string='Nhận xét giáo viên')
    exam_date = fields.Date(string='Ngày thi')