# -*- coding: utf-8 -*-
# from odoo import http


# class BlbAppraisals(http.Controller):
#     @http.route('/blb_appraisals/blb_appraisals/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/blb_appraisals/blb_appraisals/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('blb_appraisals.listing', {
#             'root': '/blb_appraisals/blb_appraisals',
#             'objects': http.request.env['blb_appraisals.blb_appraisals'].search([]),
#         })

#     @http.route('/blb_appraisals/blb_appraisals/objects/<model("blb_appraisals.blb_appraisals"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('blb_appraisals.object', {
#             'object': obj
#         })
