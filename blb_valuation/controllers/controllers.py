# -*- coding: utf-8 -*-
# from odoo import http


# class BlbValuation(http.Controller):
#     @http.route('/blb_valuation/blb_valuation/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/blb_valuation/blb_valuation/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('blb_valuation.listing', {
#             'root': '/blb_valuation/blb_valuation',
#             'objects': http.request.env['blb_valuation.blb_valuation'].search([]),
#         })

#     @http.route('/blb_valuation/blb_valuation/objects/<model("blb_valuation.blb_valuation"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('blb_valuation.object', {
#             'object': obj
#         })
