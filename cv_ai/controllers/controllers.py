# -*- coding: utf-8 -*-
# from odoo import http


# class CvAi(http.Controller):
#     @http.route('/cv_ai/cv_ai', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/cv_ai/cv_ai/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('cv_ai.listing', {
#             'root': '/cv_ai/cv_ai',
#             'objects': http.request.env['cv_ai.cv_ai'].search([]),
#         })

#     @http.route('/cv_ai/cv_ai/objects/<model("cv_ai.cv_ai"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('cv_ai.object', {
#             'object': obj
#         })

