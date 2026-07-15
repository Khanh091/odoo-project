# -*- coding: utf-8 -*-
from odoo import api, models


class ReportGradeClassSubject(models.AbstractModel):
    _name = 'report.school_management.report_grade_class_subject'
    _description = 'Báo cáo bảng điểm lớp - môn'

    @api.model
    def _get_report_values(self, docids, data=None):
        s = 'school.grade.report.wizard';
        wizard = self.env['school.grade.report.wizard'].browse(docids).exists()

        # if not wizard:
        #     wizard = self.env['school.grade.wizard'].browse(docids).exists()
        #     s = 'school.grade.wizard';

        wizard.ensure_one()
        class_id = wizard.class_id
        subject = wizard.subject_id
        grades = self.env['school.grade'].search([
            ('student_id.class_id', '=', class_id.id),
            ('subject_id', '=', subject.id),
        ], order='id')

        grade_by_student = {grade.student_id.id: grade for grade in grades}
        rows = []

        for student in class_id.student_ids.sorted(lambda s: s.name or ''):
            grade = grade_by_student.get(student.id)
            rows.append({
                'student_code': student.student_code,
                'student_name': student.name,
                'midterm_score': grade.midterm_score if grade else 0.0,
                'final_score': grade.final_score if grade else 0.0,
                'average_score': grade.average_score if grade else 0.0,
                'classification': grade.classification if grade else '',
            })
        rows.sort(key=lambda x: x['student_code'])
        return {
            'doc_ids': wizard.ids,
            'doc_model': s,
            'docs': wizard,
            'rows': rows,
            'class_name': class_id.name,
            'school_year': class_id.school_year,
            'subject_name': subject.name,
        }
