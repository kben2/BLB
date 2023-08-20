# -*- coding: utf-8 -*-
# from odoo import http


# class BlbSurvey(http.Controller):
#     @http.route('/blb_survey/blb_survey/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/blb_survey/blb_survey/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('blb_survey.listing', {
#             'root': '/blb_survey/blb_survey',
#             'objects': http.request.env['blb_survey.blb_survey'].search([]),
#         })

#     @http.route('/blb_survey/blb_survey/objects/<model("blb_survey.blb_survey"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('blb_survey.object', {
#             'object': obj
#         })
