# -*- coding: utf-8 -*-
from odoo import models
from odoo.exceptions import UserError


class StudentListExcel(models.AbstractModel):
    _name = 'report.school_management.student_list_excel'
    _inherit = 'report.report_xlsx.abstract'
    _description = 'Student List Excel Report'

    def generate_xlsx_report(self, workbook, data, objs):
        sheet = workbook.add_worksheet('Danh sách học sinh')

        # Header format
        header_format = workbook.add_format({'bold': True, 'bg_color': '#4F81BD', 'font_color': 'white', 'border': 1})
        cell_format = workbook.add_format({'border': 1})

        # Headers
        headers = ['Mã HS', 'Họ và tên', 'Lớp', 'Khối', 'Tuổi', 'Giới tính', 'Trạng thái', 'SĐT', 'Email']
        for col, header in enumerate(headers):
            sheet.write(0, col, header, header_format)

        row = 1
        for student in objs:
            sheet.write(row, 0, student.student_code or '', cell_format)
            sheet.write(row, 1, student.name or '', cell_format)
            sheet.write(row, 2, student.class_id.name if student.class_id else '', cell_format)
            sheet.write(row, 3, student.class_id.grade_level if student.class_id else '', cell_format)
            sheet.write(row, 4, student.age or 0, cell_format)
            sheet.write(row, 5, dict(student._fields['gender'].selection).get(student.gender, ''), cell_format)
            sheet.write(row, 6, dict(student._fields['status'].selection).get(student.status, ''), cell_format)
            sheet.write(row, 7, student.phone or '', cell_format)
            sheet.write(row, 8, student.email or '', cell_format)
            row += 1

        sheet.set_column('A:I', 20)


class StudentGradeExcel(models.AbstractModel):
    _name = 'report.school_management.student_grade_excel'
    _inherit = 'report.report_xlsx.abstract'
    _description = 'Student Grade Excel Report'

    def generate_xlsx_report(self, workbook, data, student):
        sheet = workbook.add_worksheet('Bảng điểm')

        header_format = workbook.add_format({'bold': True, 'bg_color': '#4F81BD', 'font_color': 'white', 'border': 1})
        cell_format = workbook.add_format({'border': 1})

        headers = ['Môn học', 'Điểm GK', 'Điểm CK', 'Điểm TB', 'Xếp loại']
        for col, header in enumerate(headers):
            sheet.write(0, col, header, header_format)

        row = 1
        for grade in student.grade_ids:
            sheet.write(row, 0, grade.subject_id.name or '', cell_format)
            sheet.write(row, 1, grade.midterm_score or 0, cell_format)
            sheet.write(row, 2, grade.final_score or 0, cell_format)
            sheet.write(row, 3, grade.average_score or 0, cell_format)
            sheet.write(row, 4, grade.classification or '', cell_format)
            row += 1
