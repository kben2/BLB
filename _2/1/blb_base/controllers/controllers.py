# -*- coding: utf-8 -*-
# from odoo import http


# class BlbBase(http.Controller):
#     @http.route('/blb_base/blb_base/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/blb_base/blb_base/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('blb_base.listing', {
#             'root': '/blb_base/blb_base',
#             'objects': http.request.env['blb_base.blb_base'].search([]),
#         })

#     @http.route('/blb_base/blb_base/objects/<model("blb_base.blb_base"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('blb_base.object', {
#             'object': obj
#         })
