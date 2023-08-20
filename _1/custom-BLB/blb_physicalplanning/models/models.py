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


class blb_physicalplanning(models.Model):
    _name = 'blb_physicalplanning.blb_physicalplanning'
    _description = 'BLB Physical Planning'
    #_inherit = ['mail.thread', 'ir.needaction_mixin']
    _order = 'status desc'

    file_no = fields.Many2one('blb_client.blb_client', string='Client', required=True, readonly=True)
    plot_size = fields.Integer(string="Plot Size(Decimals)")
    plot_direct_access = fields.Boolean(string="Plot has Direct Access?", default=False)
    plot_in_wetland = fields.Boolean(string="Plot in Wetland?", default=False)
    status = fields.Selection([
        ('pending_physical_review', 'Pending Physical Planning Review'),
        ('not_eligible', 'Not Eligible'),
        ('status_report', 'Status Report Compiled'),
        ('defer_comments', 'Defer with Comments'),
        ('eligible', 'Eligible'),
        ('planning_done', 'Phyisical Planning Done'),
        ('completed', 'Completed'),
        ], string='Status', readonly=True, copy=False, index=True, track_visibility='onchange', default='review')

    status_report = fields.Binary(string='Status Report')
    status_report_name = fields.Char(string="Status Report Name")
    defer_comments = fields.Text(string="Defer Comments") 
    survey_job_form = fields.Binary(string='Survey Job Form')
    survey_job_form_name = fields.Char(string="Survey Job Form Name")
    planning_form = fields.Binary(string='Planning Form')
    planning_form_name = fields.Char(string="Planning Form Name")
    processed_by = fields.Many2one('res.users', string='Processed by', store=True, readonly=True)

    #Not Eligible
    def action_to_not_eligible(self):
        return self.write({'status': 'not_eligible'})

    #Status Report Compiled
    def action_to_status_report(self):
        if self.status_report == False:
            raise ValidationError(_('Please attach the Status Report!'))
        return self.write({'status': 'status_report'})

    #Defer with Comments
    def action_to_defer_comments(self):
        if self.status_report == False:
            raise ValidationError(_('Please enter the Comments!'))
        return self.write({'status': 'defer_comments'})

    #Mark Surveyor Job Done
    def action_mark_survey_job_done(self):
        if self.survey_job_form == False:
            raise ValidationError(_('Please attach the Survey Job Form!'))
        return self.write({'status': 'pending_physical_review'})


    #Eligible
    def action_to_eligible(self):
        return self.write({'status': 'eligible'})

    #Planning Done
    def action_to_planning_done(self):
        if self.planning_form == False:
            raise ValidationError(_('Please attach the Planning Form!'))
        return self.write({'status': 'planning_done'})

    #Mark Completed
    def action_mark_completed(self):
        #Current loggedin user id
        userid = self.env.uid
        return self.write({'status': 'completed', 'processed_by': userid })



class consent_requests(models.Model):
    _name = 'blb_physicalplanning.consent_requests'
    _description = 'BLB Physical Planning - Consent Requests'
    #_inherit = ['mail.thread', 'ir.needaction_mixin']
    _order = 'status desc'

    file_no = fields.Many2one('blb_client.blb_client', string='Client', required=True, readonly=True)
    type_request = fields.Selection([
        ('develop', 'Consent to Develop'),
        ('sub_divide', 'Consent to Sub-divide'),
        ('change_user', 'Consent to Change of User'),
        ], string='Type of Consent', required=True)
    status = fields.Selection([
        ('pending_assessment', 'Pending Assessment'),
        ('consent_develop', 'Consent to Develop'),
        ('to_valuation_officer', 'Under Valuation'),
        ('consent_subdivide', 'Consent to Sub-divide'),
        ('consent_changeuser', 'Consent to Change of User'),
        ], string='Status', readonly=True, copy=False, index=True, track_visibility='onchange', default='review')

    capital_value = fields.Monetary(string="Capital Value", default="0")
    fees_payment = fields.Monetary(string="Fees for Payment", default="0")
    currency_id = fields.Many2one('res.currency', 'Currency', required=True, default=lambda self: self.env.user.company_id.currency_id.id)
    remarks = fields.Text(string="Remarks") 
    done_by = fields.Many2one('res.users', string='Done by', store=True, readonly=True)

    #Consent to Develop
    def action_consent_develop(self):
        return self.write({'status': 'consent_develop'})

    #Under Valuation
    def action_to_valuation_officer(self):
        return self.write({'status': 'to_valuation_officer'})

    #Consent to Sub-divide
    def action_consent_subdivide(self):
        if self.capital_value == False:
            raise ValidationError(_('Please enter the Capital Value!'))
        elif self.fees_payment == False:
            raise ValidationError(_('Please enter the Fees for Payment!'))
        elif self.remarks == False:
            raise ValidationError(_('Please enter some Comments!'))
        return self.write({'status': 'consent_subdivide'})

    #Consent to Change of User
    def action_consent_changeuser(self):
        if self.capital_value == False:
            raise ValidationError(_('Please enter the Capital Value!'))
        elif self.fees_payment == False:
            raise ValidationError(_('Please enter the Fees for Payment!'))
        elif self.remarks == False:
            raise ValidationError(_('Please enter some Comments!'))
        return self.write({'status': 'consent_changeuser'})


        