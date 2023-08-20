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



class blb_valuation(models.Model):
    _name = 'blb_valuation.blb_valuation'
    _description = 'BLB Valuation'

    name = fields.Char(string='Client')
    value = fields.Integer(string='Client')
    description = fields.Text(string='Client')



class demand_note(models.Model):
    _name = 'blb_valuation.demand_note'
    _description = 'BLB Valuation - Demand Notes'
    #_inherit = ['mail.thread', 'ir.needaction_mixin']
    _order = 'status desc'

    file_no = fields.Many2one('blb_client.blb_client', string='Client', required=True, readonly=True)
    demand_note = fields.Binary(string='Demand Note', required=True)
    demand_note_name = fields.Char(string="Demand Note Name")
    status = fields.Selection([
        ('review', 'Pending Review'),
        ('revision_required', 'Revision Required'),
        ('revised', 'Revision Done'),
        ('update_done', 'Client File Updated'),
        ('cancel', 'Cancelled'),
        ], string='Status', readonly=True, copy=False, index=True, track_visibility='onchange', default='review')
    revised_ground_rent = fields.Monetary(string="Revised Ground Rent", default="0")
    currency_id = fields.Many2one('res.currency', 'Currency', required=True, default=lambda self: self.env.user.company_id.currency_id.id)
    date_effective = fields.Date(string="Date Effective", default=fields.Date.today)
    remarks = fields.Text(string="Remarks") 
    revised_by = fields.Many2one('res.users', string='Revised by', store=True, readonly=True)

    #Revision Required
    def action_to_revision_required(self):
        return self.write({'status': 'revision_required'})

    #Revision NOT Required
    def action_to_cancel(self):
        return self.write({'status': 'cancel'})

    #Revision Done
    def action_to_revised(self):
        if self.revised_ground_rent == False:
            raise ValidationError(_('Please enter the Revised Ground Rent!'))
        elif self.date_effective == False:
            raise ValidationError(_('Please select the Date Effective!'))
        #Current loggedin user id
        userid = self.env.uid
        return self.write({'status': 'revised', 'revised_by': userid })

    #Client File Updated
    def action_to_update_done(self):
        return self.write({'status': 'update_done'})



class valuation_assessment(models.Model):
    _name = 'blb_valuation.valuation_assessment'
    _description = 'BLB Valuation - Valuation Assessment'
    #_inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'status desc'

    file_no = fields.Many2one('blb_client.blb_client', string='Client', required=True, readonly=True)
    print_item = fields.Binary(string='Print', required=True)
    print_item_name = fields.Char(string="Print Name")
    status = fields.Selection([
        ('pending', 'Pending Valuation'),
        ('make_assessment', 'Make Assessment'),
        ('assessment_compiled', 'Assessment Compiled'),
        ('update_done', 'Client File Updated'),
        ('cancel', 'Cancelled'),
        ], string='Status', readonly=True, copy=False, index=True, track_visibility='onchange', default='pending')
    
    receipt = fields.Binary(string='Receipt')
    receipt_name = fields.Char(string="Receipt Name")
    lease_committee_form = fields.Binary(string='Lease Committee Form')
    lease_committee_form_name = fields.Char(string="Lease Committee Form Name")
    revision_details = fields.Text(string="Revision Details") 
    assessed_by = fields.Many2one('res.users', string='Assessed by', store=True, readonly=True)

    #Make Assessment
    def action_to_make_assessment(self):
        return self.write({'status': 'make_assessment'})

    #Nothing Requires Changing
    def action_to_cancel(self):
        return self.write({'status': 'cancel'})

    #Assessment Compiled
    def action_to_assessment_compiled(self):
        if self.receipt == False:
            raise ValidationError(_('Please attach a Receipt!'))
        elif self.lease_committee_form == False:
            raise ValidationError(_('Please attach a Lease Committee Form!'))
        elif self.revision_details == False:
            raise ValidationError(_('Please enter Revision details!'))
        #Current loggedin user id
        userid = self.env.uid
        return self.write({'status': 'assessment_compiled', 'assessed_by': userid })

    #Client File Updated
    def action_to_update_done(self):
        return self.write({'status': 'update_done'})



class valuation_requests(models.Model):
    _name = 'blb_valuation.valuation_requests'
    _description = 'BLB Valuation - Valuation Requests'
    #_inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'status desc'

    file_no = fields.Many2one('blb_client.blb_client', string='Client', required=True, readonly=True)
    request_item = fields.Binary(string='Request', required=True)
    request_item_name = fields.Char(string="Request Name")
    status = fields.Selection([
        ('pending', 'Pending Valuation'),
        ('assessment_compiled', 'Assessment Compiled'),
        ('field_inspection', 'Field Inspection'),
        ('valuation_done', 'Valuation Done'),        
        ], string='Status', readonly=True, copy=False, index=True, track_visibility='onchange', default='pending')
    
    assessment = fields.Binary(string='Assessment')
    assessment_name = fields.Char(string="Assessment Name")
    other_details = fields.Text(string="Assessment Details") 
    assessed_by = fields.Many2one('res.users', string='Assessed by', store=True, readonly=True)
    requires_field_inspection = fields.Boolean(string="Requires Field Inspection", default=False)

    valuation_report = fields.Binary(string='Valuation Report')
    valuation_report_name = fields.Char(string="Valuation Report Name")

    #Assessment Compiled
    def action_to_assessment_compiled(self):
        if self.assessment == False:
            raise ValidationError(_('Please attach an Assessment!'))
        elif self.other_details == False:
            raise ValidationError(_('Please enter some details on the assessment!'))
        #Current loggedin user id
        userid = self.env.uid
        return self.write({'status': 'assessment_compiled', 'assessed_by': userid })

    #Requires Field Inspection
    def action_to_field_inspection(self):
        return self.write({'status': 'field_inspection', 'requires_field_inspection': True})

    #Valuation Done
    def action_to_valuation_done(self):
        if self.valuation_report == False:
            raise ValidationError(_('Please attach a Valuation Report!'))
        return self.write({'status': 'valuation_done'})