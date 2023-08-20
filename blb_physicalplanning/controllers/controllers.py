# -*- coding: utf-8 -*-
# from odoo import http


# class BlbPhysicalplanning(http.Controller):
#     @http.route('/blb_physicalplanning/blb_physicalplanning/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/blb_physicalplanning/blb_physicalplanning/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('blb_physicalplanning.listing', {
#             'root': '/blb_physicalplanning/blb_physicalplanning',
#             'objects': http.request.env['blb_physicalplanning.blb_physicalplanning'].search([]),
#         })

#     @http.route('/blb_physicalplanning/blb_physicalplanning/objects/<model("blb_physicalplanning.blb_physicalplanning"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('blb_physicalplanning.object', {
#             'object': obj
#         })
