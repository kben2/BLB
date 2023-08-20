# -*- coding: utf-8 -*-

from odoo import models, fields, api, tools, _
from datetime import datetime
from datetime import date
from dateutil.relativedelta import relativedelta
from datetime import timedelta
from odoo.exceptions import Warning as UserError
from odoo.exceptions import ValidationError
from odoo.exceptions import AccessDenied, UserError
from odoo.tools.parse_version import parse_version
from odoo.tools.misc import topological_sort
import json
import csv



class counties(models.Model):
    _name = 'blb_valuation.counties'
    _description = 'BLB - Counties'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'name asc'

    name = fields.Char(string='County', required=True)

    _sql_constraints = [
        ('name',
         'UNIQUE(name)',
         "The County should be Unique!")
    ]

class districts(models.Model):
    _name = 'blb_valuation.districts'
    _description = 'BLB - Districts'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'county_id,name asc'

    county_id = fields.Many2one('blb_valuation.counties', string='County', required=True, ondelete='cascade')
    name = fields.Char(string='District', required=True)

    # _sql_constraints = [
    #     ('name',
    #      'UNIQUE(name)',
    #      "The District should be Unique!")
    # ]

class subcounties(models.Model):
    _name = 'blb_valuation.subcounties'
    _description = 'BLB - Sub-Counties'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'county_id,district_id,name asc'

    county_id = fields.Many2one('blb_valuation.counties', string='County', required=True, ondelete='cascade')
    district_id = fields.Many2one('blb_valuation.districts', string='District', required=True, domain="[('county_id', '=', county_id)]", ondelete='cascade')
    name = fields.Char(string='Sub-County', required=True)

    # _sql_constraints = [
    #     ('name',
    #      'UNIQUE(name)',
    #      "The Sub-County should be Unique!")
    # ]


class parishes(models.Model):
    _name = 'blb_valuation.parishes'
    _description = 'BLB - Parishes'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'county_id,district_id,subcounty_id,name asc'

    county_id = fields.Many2one('blb_valuation.counties', string='County', required=True, ondelete='cascade')
    district_id = fields.Many2one('blb_valuation.districts', string='District', required=True, domain="[('county_id', '=', county_id)]", ondelete='cascade')
    subcounty_id = fields.Many2one('blb_valuation.subcounties', string='Sub-County', required=True, domain="[('district_id', '=', district_id)]", ondelete='cascade')
    name = fields.Char(string='Parish', required=True)

    # _sql_constraints = [
    #     ('name',
    #      'UNIQUE(name)',
    #      "The Parish should be Unique!")
    # ]

class villages(models.Model):
    _name = 'blb_valuation.villages'
    _description = 'BLB - Villages'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'county_id,district_id,subcounty_id,parish_id,name asc'

    county_id = fields.Many2one('blb_valuation.counties', string='County', required=True, ondelete='cascade')
    district_id = fields.Many2one('blb_valuation.districts', string='District', required=True, domain="[('county_id', '=', county_id)]", ondelete='cascade')
    subcounty_id = fields.Many2one('blb_valuation.subcounties', string='Sub-County', required=True, domain="[('district_id', '=', district_id)]", ondelete='cascade')
    parish_id = fields.Many2one('blb_valuation.parishes', string='Parish', required=True, domain="[('subcounty_id', '=', subcounty_id)]", ondelete='cascade')
    name = fields.Char(string='Village', required=True)

    # _sql_constraints = [
    #     ('name',
    #      'UNIQUE(name)',
    #      "The village should be Unique!")
    # ]


class landuse_types(models.Model):
    _name = 'blb_valuation.landuse_types'
    _description = 'BLB - Types of Land Use'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'name asc'

    name = fields.Char(string='Land Use', required=True)

    _sql_constraints = [
        ('name',
         'UNIQUE(name)',
         "The Land Use should be Unique!")
    ]




#####################################################################################
## ***
## ***  Valuation Table
## ***
#####################################################################################

class valuation_table(models.Model):
    _name = 'blb_valuation.valuation_table'
    _description = 'BLB - Valuation Table'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'name asc'

    name = fields.Char(string="Valuation Table", readonly=True, compute="_compute_name", store=True)
    county_id = fields.Many2one('blb_valuation.counties', string='County', required=True, ondelete='cascade')
    district_id = fields.Many2one('blb_valuation.districts', string='District', required=True, domain="[('county_id', '=', county_id)]", ondelete='cascade')
    subcounty_id = fields.Many2one('blb_valuation.subcounties', string='Sub-County', required=True, domain="[('district_id', '=', district_id)]", ondelete='cascade')
    parish_id = fields.Many2one('blb_valuation.parishes', string='Parish', required=True, domain="[('subcounty_id', '=', subcounty_id)]", ondelete='cascade')
    village_id = fields.Many2one('blb_valuation.villages', string='Village', required=True, domain="[('parish_id', '=', parish_id)]", ondelete='cascade')
    landuse_valuation_ids = fields.One2many('blb_valuation.landuse_valuation', 'valuation_table_id', string='Land Use Valuations', ondelete='cascade')

    #Compute Name
    @api.depends('county_id','district_id','subcounty_id','parish_id','village_id')
    def _compute_name(self):
        rec_name = ''
        for rec in self:
            if rec.county_id and rec.district_id and rec.subcounty_id and rec.parish_id and rec.village_id:
                rec_name = str(rec.county_id.name) + "/" + str(rec.district_id.name) + "/" + str(rec.subcounty_id.name) + "/" + str(rec.parish_id.name) + "/" + str(rec.village_id.name)
            rec.name = rec_name
        return rec_name

    _sql_constraints = [
        ('name',
         'UNIQUE(name)',
         "The Table Record should be Unique!")
    ]

    #Test Method to import CSV files for Villages
    def import_parishes_villages(self,file_name):
        file_path = "addons/custom-BLB/blb_valuation/data/" + file_name + ".csv"
        with open(file_path, 'r') as file_obj:
            csv_reader = csv.reader(file_obj)
            for row in csv_reader:
                #Select location using row details
                county_name = (str(row[0])).strip()
                district_name = (str(row[1])).strip()
                subcounty_name = (str(row[2])).strip()
                parish_name = (str(row[3])).strip()
                village_name = (str(row[4])).strip()

                county_id = self.env['blb_valuation.counties'].search([('name', '=', county_name)])
                #county
                if county_id:                    
                    district_id = self.env['blb_valuation.districts'].search([('name', '=', district_name),('county_id', '=', county_id.id)])
                    #district
                    if district_id:                        
                        subcounty_id = self.env['blb_valuation.subcounties'].search([('name', '=', subcounty_name),('county_id', '=', county_id.id),('district_id', '=', district_id.id)])
                        #subcounty
                        if subcounty_id:                            
                            parish_id = self.env['blb_valuation.parishes'].search([('name', '=', parish_name),('county_id', '=', county_id.id),('district_id', '=', district_id.id),('subcounty_id', '=', subcounty_id.id)])
                            #parish
                            if parish_id:                                
                                village_id = self.env['blb_valuation.villages'].search([('name', '=', village_name),('county_id', '=', county_id.id),('district_id', '=', district_id.id),('subcounty_id', '=', subcounty_id.id),('parish_id', '=', parish_id.id)])
                                #village
                                if not village_id:
                                    #Create Village
                                    village_create = self.env['blb_valuation.villages'].create({
                                        'county_id': county_id.id,
                                        'district_id': district_id.id,
                                        'subcounty_id': subcounty_id.id,
                                        'parish_id': parish_id.id,
                                        'name': village_name,
                                    })
                            else:
                                #Create Parish
                                parish_create = self.env['blb_valuation.parishes'].create({
                                    'county_id': county_id.id,
                                    'district_id': district_id.id,
                                    'subcounty_id': subcounty_id.id,
                                    'name': parish_name
                                })
                                parish_id = parish_create.id
                                #Create Village
                                village_create = self.env['blb_valuation.villages'].create({
                                    'county_id': county_id.id,
                                    'district_id': district_id.id,
                                    'subcounty_id': subcounty_id.id,
                                    'parish_id': parish_create.id,
                                    'name': village_name,
                                })
                        else:
                            false_row = "Cty=" + str(county_id.id) + ":-Dstr=" + str(district_id.id) + ":-Sbcty=" + str(subcounty_name) + ">>" + str(subcounty_id) + ":-Prsh=" + str(parish_name) + ":-Vilg=" + str(village_name)
                            raise ValidationError(_(false_row))


    #Test Method to import CSV files for Vaulation Table
    def import_valuation_table(self,file_name):
        file_path = "addons/custom-BLB/blb_valuation/data/" + file_name + ".csv"
        with open(file_path, 'r') as file_obj:
            csv_reader = csv.reader(file_obj)
            for row in csv_reader:
                #Select location using row details
                county_name = (str(row[0])).strip()
                district_name = (str(row[1])).strip()
                subcounty_name = (str(row[2])).strip()
                parish_name = (str(row[3])).strip()
                village_name = (str(row[4])).strip()

                county_id = self.env['blb_valuation.counties'].search([('name', '=', county_name)])
                #county
                if county_id:                    
                    district_id = self.env['blb_valuation.districts'].search([('name', '=', district_name),('county_id', '=', county_id.id)])
                    #district
                    if district_id:                        
                        subcounty_id = self.env['blb_valuation.subcounties'].search([('name', '=', subcounty_name),('county_id', '=', county_id.id),('district_id', '=', district_id.id)])
                        #subcounty
                        if subcounty_id:                            
                            parish_id = self.env['blb_valuation.parishes'].search([('name', '=', parish_name),('county_id', '=', county_id.id),('district_id', '=', district_id.id),('subcounty_id', '=', subcounty_id.id)])
                            #parish
                            if parish_id:                                
                                village_id = self.env['blb_valuation.villages'].search([('name', '=', village_name),('county_id', '=', county_id.id),('district_id', '=', district_id.id),('subcounty_id', '=', subcounty_id.id),('parish_id', '=', parish_id.id)])
                                #village
                                if village_id:
                                    #Create Vaulation row
                                    valuation_row_create = self.env['blb_valuation.valuation_table'].create({
                                        'county_id': county_id.id,
                                        'district_id': district_id.id,
                                        'subcounty_id': subcounty_id.id,
                                        'parish_id': parish_id.id,
                                        'village_id': village_id.id,
                                    })
                                    valuation_row_id = valuation_row_create.id
                                    #Create commercial_vaulation
                                    if row[5] and str(row[5]) != '' and int(row[5]) > 0 and row[6] and str(row[6]) != '' and int(row[6]) > 0:                        
                                        land_use_type = self.env['blb_valuation.landuse_types'].search([('name', '=', 'Commercial')])
                                        landuse_valuation_create = self.env['blb_valuation.landuse_valuation'].create({
                                            'landuse_type_id': land_use_type.id,
                                            'from_range': int(row[5]),
                                            'to_range': int(row[6]),
                                            'valuation_table_id': valuation_row_id
                                        })
                                    #Create residential_valuation
                                    if row[7] and str(row[7]) != '' and int(row[7]) > 0 and row[8] and str(row[8]) != '' and int(row[8]) > 0: 
                                        land_use_type = self.env['blb_valuation.landuse_types'].search([('name', '=', 'Residential')])
                                        landuse_valuation_create = self.env['blb_valuation.landuse_valuation'].create({
                                            'landuse_type_id': land_use_type.id,
                                            'from_range': int(row[7]),
                                            'to_range': int(row[8]),
                                            'valuation_table_id': valuation_row_id
                                        })
                                    #Create agricultural_valuation
                                    if row[9] and str(row[9]) != '' and int(row[9]) > 0 and row[10] and str(row[10]) != '' and int(row[10]) > 0: 
                                        land_use_type = self.env['blb_valuation.landuse_types'].search([('name', '=', 'Agricultural')])
                                        landuse_valuation_create = self.env['blb_valuation.landuse_valuation'].create({
                                            'landuse_type_id': land_use_type.id,
                                            'from_range': int(row[9]),
                                            'to_range': int(row[10]),
                                            'valuation_table_id': valuation_row_id
                                        })
                                    #Create institutional_valuation
                                    if row[11] and str(row[11]) != '' and int(row[11]) > 0 and row[12] and str(row[12]) != '' and int(row[12]) > 0: 
                                        land_use_type = self.env['blb_valuation.landuse_types'].search([('name', '=', 'Institutional')])
                                        landuse_valuation_create = self.env['blb_valuation.landuse_valuation'].create({
                                            'landuse_type_id': land_use_type.id,
                                            'from_range': int(row[11]),
                                            'to_range': int(row[12]),
                                            'valuation_table_id': valuation_row_id
                                        })

                                    true_row = "Ct=" + str(county_id.id) + ",Dt=" + str(district_id.id) + ",Sb=" + str(subcounty_id.id) + ",Pr=" + str(parish_id.id) + ",Vl=" + str(village_id.id)  + \
                                     "==>" + str(row[5]) + "/" + str(row[6]) + "/" + str(row[7]) + "/" + str(row[8])
                                    print(true_row)
                                else:
                                    false_row = "Cty=" + str(county_id.id) + ":-Dstr=" + str(district_id.id) + ":-Sbcty=" + str(subcounty_id.id) + ":-Prsh=" + str(parish_id.id) + ":-Vilg=" + str(village_name)
                                    raise ValidationError(_(false_row))



class landuse_valuation(models.Model):
    _name = 'blb_valuation.landuse_valuation'
    _description = 'BLB - Land Use Valuation'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'name asc'

    name = fields.Char(string="Land Use Valuation", readonly=True, compute="_compute_name", store=True)
    landuse_type_id = fields.Many2one('blb_valuation.landuse_types', string="Type of Land Use", required=True, ondelete='cascade')
    from_range = fields.Monetary(string="From", required=True)
    to_range = fields.Monetary(string="To", required=True)
    currency_id = fields.Many2one('res.currency', 'Currency', readonly=True, required=True, default=lambda self: self.env.user.company_id.currency_id.id)
    valuation_table_id = fields.Many2one('blb_valuation.valuation_table', string='Valuation Table', ondelete='cascade')

    #Compute Name
    @api.depends('landuse_type_id','from_range','to_range')
    def _compute_name(self):
        rec_name = ''
        for rec in self:
            if rec.landuse_type_id and rec.from_range and rec.to_range:
                rec_name = str(rec.landuse_type_id.name) + " (" + str(rec.from_range) + " - " + str(rec.to_range) + ")"
            rec.name = rec_name
        return rec_name

    #Check whether condition_amount allocated does not exceed grant_salary_contribution 
    @api.onchange('to_range')
    def _onchange_to_range(self):
        for rec in self:
            if rec.from_range > rec.to_range:
                raise ValidationError(_( "From value: " + str(rec.from_range) + " is greater than To value: " + str(rec.to_range) ))

    #Create Put together the Details
    @api.model
    def create(self, vals):
        #Check from and to values
        from_range = int(vals['from_range'])
        to_range = int(vals['to_range'])
        if from_range > to_range:
            raise ValidationError(_( "From value: " + str(from_range) + " is greater than To value: " + str(to_range) ))
        res = super(landuse_valuation, self).create(vals)
        return res

