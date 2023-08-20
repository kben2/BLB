# -*- coding: utf-8 -*-
from odoo import http

# class BLB_Client(http.Controller):
#     @http.route('/blb_client/blb_client/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/blb_client/blb_client/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('blb_client.listing', {
#             'root': '/blb_client/blb_client',
#             'objects': http.request.env['blb_client.blb_client'].search([]),
#         })

#     @http.route('/blb_client/blb_client/objects/<model("blb_client.blb_client"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('blb_client.object', {
#             'object': obj
#         })