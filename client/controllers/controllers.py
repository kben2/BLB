# -*- coding: utf-8 -*-
from odoo import http

# class Client(http.Controller):
#     @http.route('/client/client/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/client/client/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('client.listing', {
#             'root': '/client/client',
#             'objects': http.request.env['client.client'].search([]),
#         })

#     @http.route('/client/client/objects/<model("client.client"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('client.object', {
#             'object': obj
#         })