# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from datetime import datetime
from datetime import date
from dateutil.relativedelta import relativedelta
from datetime import timedelta
from odoo.exceptions import Warning as UserError
from odoo.exceptions import ValidationError

class layer(models.Model):
    _name = 'blb_layer.blb_layer'
    #_inherit = ['mail.thread', 'ir.needaction_mixin']
    _description = 'Layers'
    _order = 'name asc'

    name = fields.Char(string="Layer Name", required=True)
    description = fields.Text(string="Layer Description")
    layer_coordinates_system = fields.Many2one('blb_layer.coordinates_system', string='Co-ordinates System', required=True, ondelete='cascade')
    layer_db_table = fields.Char(string="Table Name", readonly=True, compute="_compute_layertable", store=True)

    _sql_constraints = [
        ('name_unique',
         'UNIQUE(name)',
         "The Layer Name must be unique")
    ]

    @api.depends('name')
    def _compute_layertable(self):
        layertable = ""
        for record in self:
        	if record.name:
        		layertable =  str(record.name) + '_layer'
        	record.layer_db_table = layertable.lower()
        return layertable


class coordinates_system(models.Model):
    _name = 'blb_layer.coordinates_system'
    #_inherit = ['mail.thread', 'ir.needaction_mixin']
    _description = 'Layers - Coordinates System'

    srid = fields.Selection([
        ('4326', "4326"),
        ('21096', "21096"),
        ('21036', "21036"),
        ('3857', "3857"),
    ], string="SRID", required=True)  
    coordinates_system = fields.Char(string="Co-ordinates System", readonly=True, compute="_compute_coordinate_system", store=True)

    _sql_constraints = [
        ('srid_unique',
         'UNIQUE(srid)',
         "The SRID must be unique")
    ]

    @api.depends('srid')
    def _compute_coordinate_system(self):
        thesystem = ""
        for record in self:
        	if record.srid == '4326':
        		thesystem = 'WGS 84'
        	elif record.srid == '21096':
        		thesystem = 'Arc 1960 / UTM Zone 36N'
        	elif record.srid == '21036':
        		thesystem = 'Arc 1960 / UTM Zone 36S'
        	elif record.srid == '3857':
        		thesystem = 'Spherical Mercator'
        	record.coordinates_system = thesystem
        return thesystem

    def name_get(self):
        result = []
        for coord_sys in self:
            name = coord_sys.coordinates_system + ' (' + coord_sys.srid + ')'
            result.append((coord_sys.id, name))
        return result
