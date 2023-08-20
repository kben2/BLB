# -*- coding: utf-8 -*-
from odoo import http

# class BLB_Layer(http.Controller):
#     @http.route('/blb_layer/blb_layer/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/blb_layer/blb_layer/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('blb_layer.listing', {
#             'root': '/blb_layer/blb_layer',
#             'objects': http.request.env['blb_layer.blb_layer'].search([]),
#         })

#     @http.route('/blb_layer/blb_layer/objects/<model("blb_layer.blb_layer"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('blb_layer.object', {
#             'object': obj
#         })