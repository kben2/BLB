# -*- coding: utf-8 -*-
# from odoo import http


# class BlbCorrespondence(http.Controller):
#     @http.route('/blb_correspondence/blb_correspondence/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/blb_correspondence/blb_correspondence/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('blb_correspondence.listing', {
#             'root': '/blb_correspondence/blb_correspondence',
#             'objects': http.request.env['blb_correspondence.blb_correspondence'].search([]),
#         })

#     @http.route('/blb_correspondence/blb_correspondence/objects/<model("blb_correspondence.blb_correspondence"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('blb_correspondence.object', {
#             'object': obj
#         })
