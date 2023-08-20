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


class blb_correspondence(models.Model):
    _name = 'blb_correspondence.blb_correspondence'
    _description = 'BLB - Correspondence'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'status desc'

    name = fields.Char(string="Name", compute="_compute_name", store=True) 
    date_request = fields.Date(string="Date Request Received", required=True)
    type_client = fields.Selection([
        ('BLB Client', 'BLB Client'),
        ('Other', 'Other'),
        ], string='Is a BLB Client?', required=True)
    client_file_no = fields.Many2one('blb_client.blb_client', string='Client/File No.')
    client_other = fields.Char(string="Author From")
    type_request = fields.Selection([
        ('OPM Request', 'OPM Request'),
        ('Survey Request', 'Survey Request'),
        ('Planning Request', 'Planning Request'),
        ('Valuation Request', 'Valuation Request'),
        ('Enforcer Request', 'Enforcer Request'),
        ('Research Request', 'Research Request'),
        ], string='Type of Request', required=True)
    status = fields.Selection([
        ('pending_assignment', 'Pending Assignment'),
        ('assigned_opm', 'Assigned to OPM'),
        ('assigned_survey', 'Assigned to Survey Unit'),
        ('assigned_surveyor', 'Assigned to Surveyor'),
        ('assigned_planning', 'Assigned to Planning Unit'),
        ('assigned_planner', 'Assigned to Planner'),
        ('assigned_valuation', 'Assigned to Valuation Unit'),
        ('assigned_valuer', 'Assigned to Valuer'),
        ('assigned_enforcement', 'Assigned to Enforcement Unit'),
        ('assigned_enforcer', 'Assigned to Enforcer'),
        ('assigned_research', 'Assigned to Research'),
        ('assigned_researcher', 'Assigned to Researcher'),
        ('feedback_given', 'Feedback Given'),
        ('closed', 'Closed'),
        ], string='Status', readonly=True, copy=False, index=True, track_visibility='onchange', default='pending_assignment')

    request = fields.Text(string="Request/Description/Reason", required=True) 
    remarks = fields.Text(string="Remarks")

    allocated_to = fields.Many2one('res.users', string='Allocated to')
    date_allocated = fields.Date(string="Date Allocated", default=fields.Date.today, readonly=True)
    report = fields.Binary(string='Report')
    report_name = fields.Char(string="Report Name")
    report_remarks = fields.Text(string="Remarks") 
    done_by = fields.Many2one('res.users', string='Feedback given by', readonly=True, default=lambda self: self.env.user)
    date_done = fields.Date(string="Date Feedback given", default=fields.Date.today, readonly=True)
    #current_user = fields.Many2one('res.users','Current User', default=lambda self: self.env.uid) 

    #Compute Name
    @api.depends('client_file_no','client_other','type_request')
    def _compute_name(self):
        correspondence_name = ""    
        for rec in self:
            if rec.client_file_no and rec.type_request:
                #raise ValidationError(_(rec.client_file_no.name))
                correspondence_name = str(rec.client_file_no.name) + " - " + str(rec.type_request)
            elif rec.client_other and rec.type_request:
                correspondence_name = str(rec.client_other) + " - " + str(rec.type_request)
            rec.name = correspondence_name
        return correspondence_name

    #assigned_opm
    def action_to_unit(self):
        status = 'pending_assignment'
        if self.type_request == 'OPM Request':
            status = 'assigned_opm'
        elif self.type_request == 'Survey Request':
            status = 'assigned_survey'
        elif self.type_request == 'Planning Request':
            status = 'assigned_planning'
        elif self.type_request == 'Valuation Request':
            status = 'assigned_valuation'
        elif self.type_request == 'Enforcer Request':
            status = 'assigned_enforcement'
        elif self.type_request == 'Research Request':
            status = 'assigned_research'
        #Check of requirements
        if self.remarks == False:
            raise ValidationError(_('Please enter the Remarks!'))
        return self.write({'status': status})

    #To Surveyor 
    def action_assigned_surveyor(self):
        #raise ValidationError(_(self.allocated_to.id))     
        if self.allocated_to.id == False or self.allocated_to.id == '':
            raise ValidationError(_('Please select Allocated Surveyor!'))
        #Send notification/sms/email
        user_id = self.allocated_to.id
        user_name = self.allocated_to.name        
        notification_subject = "Correspondence Allocation"
        notification_details = "You have been allocated a Correspondence: " + str(self.name)
        self.env["blb_base.notifications"]._send_system_notification(user_id,notification_subject,notification_details) 
        #get email
        email_to = self.allocated_to.login
        self.env["blb_base.notifications"]._send_email(user_id,email_to,notification_subject,notification_details)
        #Get phone details
        partner_id = self.allocated_to.partner_id
        phone_number = partner_id.phone
        self.env["blb_base.notifications"]._send_sms(user_id,phone_number,notification_details)
        #Change status
        today = date.today()
        return self.write({'date_allocated': today, 'status': 'assigned_surveyor'})

    #To Planner
    def action_assigned_planner(self):
        if self.allocated_to.id == False or self.allocated_to.id == '':
            raise ValidationError(_('Please select Allocated Planner!'))
        #Send notification/sms/email
        user_id = self.allocated_to.id
        user_name = self.allocated_to.name        
        notification_subject = "Correspondence Allocation"
        notification_details = "You have been allocated a Correspondence: " + str(self.name)
        self.env["blb_base.notifications"]._send_system_notification(user_id,notification_subject,notification_details) 
        #get email
        email_to = self.allocated_to.login
        self.env["blb_base.notifications"]._send_email(user_id,email_to,notification_subject,notification_details)
        #Get phone details
        partner_id = self.allocated_to.partner_id
        phone_number = partner_id.phone
        self.env["blb_base.notifications"]._send_sms(user_id,phone_number,notification_details)
        #Change status 
        today = date.today()
        return self.write({'date_allocated': today, 'status': 'assigned_planner'})

   	#To Valuer
    def action_assigned_valuer(self):
        if self.allocated_to.id == False or self.allocated_to.id == '':
            raise ValidationError(_('Please select Allocated Valuer!'))
        #Send notification/sms/email
        user_id = self.allocated_to.id
        user_name = self.allocated_to.name        
        notification_subject = "Correspondence Allocation"
        notification_details = "You have been allocated a Correspondence: " + str(self.name)
        self.env["blb_base.notifications"]._send_system_notification(user_id,notification_subject,notification_details) 
        #get email
        email_to = self.allocated_to.login
        self.env["blb_base.notifications"]._send_email(user_id,email_to,notification_subject,notification_details)
        #Get phone details
        partner_id = self.allocated_to.partner_id
        phone_number = partner_id.phone
        self.env["blb_base.notifications"]._send_sms(user_id,phone_number,notification_details)
        #Change status 
        today = date.today()
        return self.write({'date_allocated': today, 'status': 'assigned_valuer'})

    #To Enforcer
    def action_assigned_enforcer(self):
        if self.allocated_to.id == False or self.allocated_to.id == '':
            raise ValidationError(_('Please select Allocated Enforcer!'))
        #Send notification/sms/email
        user_id = self.allocated_to.id
        user_name = self.allocated_to.name        
        notification_subject = "Correspondence Allocation"
        notification_details = "You have been allocated a Correspondence: " + str(self.name)
        self.env["blb_base.notifications"]._send_system_notification(user_id,notification_subject,notification_details) 
        #get email
        email_to = self.allocated_to.login
        self.env["blb_base.notifications"]._send_email(user_id,email_to,notification_subject,notification_details)
        #Get phone details
        partner_id = self.allocated_to.partner_id
        phone_number = partner_id.phone
        self.env["blb_base.notifications"]._send_sms(user_id,phone_number,notification_details)
        #Change status 
        today = date.today()
        return self.write({'date_allocated': today, 'status': 'assigned_enforcer'})

    #To Researcher
    def action_assigned_researcher(self):
        if self.allocated_to.id == False or self.allocated_to.id == '':
            raise ValidationError(_('Please select Allocated Researcher!'))
        #Send notification/sms/email
        user_id = self.allocated_to.id
        user_name = self.allocated_to.name        
        notification_subject = "Correspondence Allocation"
        notification_details = "You have been allocated a Correspondence: " + str(self.name)
        self.env["blb_base.notifications"]._send_system_notification(user_id,notification_subject,notification_details) 
        #get email
        email_to = self.allocated_to.login
        self.env["blb_base.notifications"]._send_email(user_id,email_to,notification_subject,notification_details)
        #Get phone details
        partner_id = self.allocated_to.partner_id
        phone_number = partner_id.phone
        self.env["blb_base.notifications"]._send_sms(user_id,phone_number,notification_details)
        #Change status 
        today = date.today()
        return self.write({'date_allocated': today, 'status': 'assigned_researcher'})


    #Feedback Given
    def action_feedback_given(self):
        if self.report == False:
            raise ValidationError(_('Please attach the Report!'))
        elif self.report_remarks == False:
            raise ValidationError(_('Please enter the Report Remarks!'))
        #Current loggedin user id
        userid = self.env.uid
        today = date.today()
        return self.write({'status': 'feedback_given', 'date_done': today, 'done_by': userid })

    #To Researcher
    def action_closed(self):
        #Check User Rights
        userid = self.env.uid
        user_rec = self.env['res.users'].search([('id', '=', userid)])
        if self.env.user.has_group ('blb_base.blb_survey_chief_surveyor') or self.env.user.has_group ('blb_base.blb_chief_planner') or self.env.user.has_group ('blb_base.blb_chief_valuer') or self.env.user.has_group ('blb_base.blb_head_pps'):
            #Close correspondence
            return self.write({'status': 'closed'})
        else:
            raise ValidationError(_('You do not have permission to close this Corresponse. Contact your Chief/Head!'))


