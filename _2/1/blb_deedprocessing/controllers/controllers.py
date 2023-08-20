# -*- coding: utf-8 -*-
# from odoo import http


# class BlbDeedprocessing(http.Controller):
#     @http.route('/blb_deedprocessing/blb_deedprocessing/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/blb_deedprocessing/blb_deedprocessing/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('blb_deedprocessing.listing', {
#             'root': '/blb_deedprocessing/blb_deedprocessing',
#             'objects': http.request.env['blb_deedprocessing.blb_deedprocessing'].search([]),
#         })

#     @http.route('/blb_deedprocessing/blb_deedprocessing/objects/<model("blb_deedprocessing.blb_deedprocessing"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('blb_deedprocessing.object', {
#             'object': obj
#         })
