# -*- coding: utf-8 -*-
{
    'name': 'School Management',
    'version': '1.0',
    'category': 'Education',
    'summary': 'Quản lý học sinh, giáo viên, lớp học, môn học và điểm số trên Odoo',
    'description': """
        Module quản lý trường học đầy đủ chức năng:
        - Quản lý Học sinh, Giáo viên, Lớp học, Môn học, Điểm
        - Tính toán tự động (tuổi, điểm TB)
        - Smart Button, Onchange, Compute Fields
        - Báo cáo PDF + Excel
        - Kế thừa Model & View
        - Security đầy đủ
    """,
    'author': 'Your Name',
    'depends': ['base', 'web', 'report_xlsx', 'tct_file_preview'],
    'data': [
        'security/res.groups.xml',
        'security/record_rules.xml',
        'security/ir.model.access.csv',
        'data/sequence.xml',

        'views/actions.xml',           # Actions phải lên trước Views
        'views/menus.xml',

        'views/school_grade_views.xml',   # Grade views nên lên trước class views
        'views/school_student_views.xml',
        'views/school_teacher_views.xml',
        'views/school_grade_wizard_views.xml',
        'views/school_grade_report_wizard_views.xml',
        'views/school_class_views.xml',
        'views/school_subject_views.xml',
        'views/school_student_kanban.xml',

        'views/inheritance/inherited_student_views.xml',
        'views/inheritance/inherited_class_views.xml',
        'views/inheritance/inherited_teacher_views.xml',

        'reports/school_reports.xml',
        'reports/student_list_template.xml',
        'reports/student_grade_template.xml',
        'reports/school_grade_report.xml',
    ],
    'demo': [
        'demo/demo.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
