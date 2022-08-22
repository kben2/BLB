# -*- coding: utf-8 -*-
from odoo import http

# class Layer(http.Controller):
#     @http.route('/layer/layer/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/layer/layer/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('layer.listing', {
#             'root': '/layer/layer',
#             'objects': http.request.env['layer.layer'].search([]),
#         })

#     @http.route('/layer/layer/objects/<model("layer.layer"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('layer.object', {
#             'object': obj
#         })