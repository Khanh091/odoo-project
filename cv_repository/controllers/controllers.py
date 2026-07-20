# -*- coding: utf-8 -*-
# from odoo import http


# class CvRepository(http.Controller):
#     @http.route('/cv_repository/cv_repository', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/cv_repository/cv_repository/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('cv_repository.listing', {
#             'root': '/cv_repository/cv_repository',
#             'objects': http.request.env['cv_repository.cv_repository'].search([]),
#         })

#     @http.route('/cv_repository/cv_repository/objects/<model("cv_repository.cv_repository"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('cv_repository.object', {
#             'object': obj
#         })

