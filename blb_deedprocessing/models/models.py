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


class blb_deedprocessing(models.Model):
    _name = 'blb_deedprocessing.blb_deedprocessing'
    _description = 'BLB - Deed Processing'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'urgency_level desc, status desc'

    name = fields.Char(string="Name", compute="_compute_name", store=True) 
    date_request = fields.Date(string="Date Request", required=True, default=fields.Date.today)
    client_file_no = fields.Many2one('blb_client.blb_client', string='Client File No.', required=True, ondelete='cascade')
    client_phone = fields.Char(string="Phone Number")  #, required=True
    blb_branch = fields.Many2one('blb_base.branches', string='Branch', required=True, ondelete='cascade')
    person_responsible = fields.Char(string="Person Responsible", required=True) 
    remarks_person_responsible = fields.Text(string="Remarks to Person Responsible")
    type_survey = fields.Many2one('blb_deedprocessing.survey_fees', string='Type of Survey', required=True, ondelete='cascade')
    survey_amount = fields.Integer(string="Survey Amount", compute="_compute_survey_amount", store=True, readonly=True)
    the_surveyor = fields.Many2one('res.users', string='Allocated Surveyor', ondelete='cascade', domain=lambda self: [("groups_id", "=",self.env.ref("blb_base.blb_survey_surveyor").id)])
    premium_amount = fields.Integer(string="Premium Amount Paid")
    jrj_location = fields.Char(string="JRJ Location/Address") 
    urgency_level = fields.Selection([
        ('Urgent', 'Urgent'),
        ('Normal', 'Normal'),        
        ], string='Level of Urgency', required=True)   
    status = fields.Selection([
        ('incoming_file', 'Incoming File'),
        ('processing_officer', 'Processing Officer'),
        ('team_lead_processing', 'Team Lead Processing'),
        ('pending_survey', 'Pending Survey'),
        ('pending_planning', 'Pending Planning'),
        ('survey_done', 'Survey Done'),
        ('planning_done', 'Planning Done'),
        ('problematic_file', 'Problematic File'),
        ('closed', 'Print Out'),
        ], string='Status', readonly=True, copy=False, index=True, track_visibility='onchange', default='incoming_file')
    the_processing_officer = fields.Many2one('res.users', string='Processing Officer', ondelete='cascade', domain=lambda self: [("groups_id", "=",self.env.ref("blb_base.blb_processing_user").id)])
    action_plan = fields.Text(string="Action Plan")
    amount_paid_po = fields.Integer(string="Amount Paid")
    date_allocated = fields.Date(string="Date Allocated", default=fields.Date.today, readonly=True)

    survey_comments = fields.Text(string="Survey Comments") 
    planning_comments = fields.Text(string="Planning Comments")
    plot_number = fields.Char(string="Plot Number", help="If Type of Survey is Sub-division, Please enter multiple Plot Numbers seperated by commas.")
    block_number = fields.Char(string="Block Number")
    area = fields.Char(string="Area")
    processing_comments = fields.Text(string="Processing Comments")
    date_closed = fields.Date(string="Date Closed", default=fields.Date.today, readonly=True)

    _sql_constraints = [
        ('clientfileno_typesurvey_unique',
         'UNIQUE(client_file_no,type_survey)',
         "The Client File No. and Type of Survey must be unique")
    ] 

    #Compute Name
    @api.depends('client_file_no','person_responsible')
    def _compute_name(self):
        request_name = ""    
        for rec in self:
            if rec.client_file_no and rec.person_responsible:
                #raise ValidationError(_(rec.client_file_no.name))
                request_name = str(rec.person_responsible) + " - " + str(rec.client_file_no.name) 
            rec.name = request_name
        return request_name

    #Onchange client_file_no
    @api.onchange('client_file_no')
    def _onchange_client_no(self):
        for rec in self:            
            if rec.client_file_no:
                rec.client_phone = rec.client_file_no.contact_details

    #Check if file Aready exists
    @api.onchange('type_survey')
    def _onchange_type_survey(self):
        if self.client_file_no and self.type_survey:
            #Search for file with same
            fileno = self.client_file_no.id
            typesurvey = self.type_survey.id
            deedprocessing_rec = self.env['blb_deedprocessing.blb_deedprocessing'].search([('client_file_no', '=', fileno),('type_survey', '=', typesurvey)])
            if deedprocessing_rec:
                #Request Exists
                raise ValidationError(_('Deed Processing Request for - "' + str(deedprocessing_rec.name) + '" already allocated to Processing Officer - "' + str(deedprocessing_rec.the_processing_officer.name) + '" on: ' + str(deedprocessing_rec.date_allocated) ))

    #Compute Survey Amount
    @api.depends('type_survey')
    def _compute_survey_amount(self):
        amount = ""    
        for rec in self:
            if rec.type_survey:
                amount = rec.type_survey.amount
            rec.survey_amount = amount
        return amount

    #Close 
    def action_recall(self):
        #Check User Rights
        userid = self.env.uid
        user_rec = self.env['res.users'].search([('id', '=', userid)])
        if self.env.user.has_group ('blb_base.blb_processing_lead'):
            #Close correspondence
            self.write({'status': 'incoming_file'})
        else:
            ValidationError(_('You do not have permission to Recall this Request. Contact the Team Lead Processing!'))
        #Return - Action Window
        view_id = self.env.ref('blb_deedprocessing.blb_deedprocessing_list').id 
        domain = ""
        context =""
        return {
            'name':'BLB - Deed Processing',
            'view_type':'form',
            'view_mode':'tree,form',
            'res_model':'blb_deedprocessing.blb_deedprocessing',
            'view_id': False,
            'type':'ir.actions.act_window',
            'target':'current',
            'context':context,
            'domain': domain
        }

    #Allocated to Processing Officer
    def action_to_processingofficer(self):
        if self.the_processing_officer.id == False or self.the_processing_officer.id == '':
            raise ValidationError(_('Please select Allocated Processing Officer!'))
        elif self.action_plan == False or len(self.action_plan) < 5:
            raise ValidationError(_('Please enter Action Plan!'))  
        elif self.amount_paid_po == False or self.amount_paid_po == 0:
            raise ValidationError(_('Please enter Amount Paid to Processing Officer!'))
        #Send notification/sms/email 
        user_id = self.the_processing_officer.id
        user_name = self.the_processing_officer.name        
        notification_subject = "Deed Processing Allocation"
        notification_details = "You have been allocated a Deed Processing Task: " + str(self.name)
        self.env["blb_base.notifications"]._send_system_notification(user_id,notification_subject,notification_details) 
        #get email
        email_to = self.the_processing_officer.login
        self.env["blb_base.notifications"]._send_email(user_id,email_to,notification_subject,notification_details)
        #Get phone details
        partner_id = self.the_processing_officer.partner_id
        phone_number = partner_id.phone
        self.env["blb_base.notifications"]._send_sms(user_id,phone_number,notification_details)
        #Change status 
        self.write({'status': 'processing_officer'})
        #Return - Action Window
        view_id = self.env.ref('blb_deedprocessing.blb_deedprocessing_list').id 
        domain = ""
        context =""
        return {
            'name':'BLB - Deed Processing',
            'view_type':'form',
            'view_mode':'tree,form',
            'res_model':'blb_deedprocessing.blb_deedprocessing',
            'view_id': False,
            'type':'ir.actions.act_window',
            'target':'current',
            'context':context,
            'domain': domain
        }

    #Forward to Team Lead Processing
    def action_to_team_leadprocessing(self):
        #Check for number of plots - split plot_number
        plotnumbers_list = []
        if self.plot_number:
            plotnumbers_list = self.plot_number.split(",")

        if self.plot_number == False or self.plot_number == '':
            raise ValidationError(_('Please enter Plot Number!'))
        elif self.block_number == False or self.block_number == '':
            raise ValidationError(_('Please enter Block Number!'))
        elif self.area == False or self.area == '':
            raise ValidationError(_('Please enter Area!'))
        elif self.type_survey == 'Subdivision' and len(plotnumbers_list) <= 1:
            raise ValidationError(_('Since Type of Submission is Subdivision, Please enter multiple Plot Numbers seperated by Commas!'))

        #Check if Plot/Block number exist
        for plot_number in plotnumbers_list:
            deedprocessing_rec = ''
            client_rec = ''
            deedprocessing_rec = self.env['blb_deedprocessing.blb_deedprocessing'].search([('plot_number', '=', plot_number),('block_number', '=', self.block_number)])
            client_rec = self.env['blb_client.blb_client'].search([('plot_no', '=', plot_number),('block_no', '=', self.block_number)])
            #raise ValidationError(_( str(deedprocessing_rec) + "==" + str(client_rec) ))
            #deedprocessing_rec for an unknow reason - returns the current record in the search - hence should be > 1
            if len(deedprocessing_rec) > 1 or len(client_rec) > 0:
                raise ValidationError(_('Block - ' + str(self.block_number) + ' and Plot Number - ' + str(plot_number) + ' already assigned to another Client!'))
            #raise ValidationError(_( str(plotnumbers_list) + '--' + str(self.block_number) + '--' + str(deedprocessing_rec) + '--' + str(client_rec)))        
        #Send notification/sms/email
        #Get Team Lead Processing ----
        users_rec = self.env['res.users'].search([('groups_id', '=', self.env.ref("blb_base.blb_processing_lead").id)])
        #raise ValidationError(_( users_rec ))
        user_rec = users_rec[0]
        user_id = user_rec.id
        user_name = user_rec.name
        notification_subject = "Deed Processing Done"
        notification_details = "Deed Processing Task Done: " + str(self.name)
        self.env["blb_base.notifications"]._send_system_notification(user_id,notification_subject,notification_details) 
        #get email
        email_to = user_rec.login
        self.env["blb_base.notifications"]._send_email(user_id,email_to,notification_subject,notification_details)
        #Get phone details
        partner_id = user_rec.partner_id
        phone_number = partner_id.phone
        self.env["blb_base.notifications"]._send_sms(user_id,phone_number,notification_details)
        #Change status 
        self.write({'status': 'team_lead_processing'})
        #Return - Action Summary Window
        view_id = self.env.ref('blb_deedprocessing.blb_deedprocessing_list').id 
        domain = "[('the_processing_officer','=', uid),('status','=','processing_officer')]"
        context =""
        return {
            'name':'Allocated to Me - For Processing',
            'view_type':'form',
            'view_mode':'tree,form',
            'res_model':'blb_deedprocessing.blb_deedprocessing',
            'view_id': False,
            'type':'ir.actions.act_window',
            'target':'current',
            'context':context,
            'domain': domain
        }


    #Mark as Problematic file
    def action_mark_problematicfile(self):
        if self.processing_comments == False or len(self.processing_comments) < 10:
            raise ValidationError(_('Please enter Processing Comments!'))
        #Send notification/sms/email 
        #Get Team Lead Processing -----
        users_rec = self.env['res.users'].search([('groups_id', '=', self.env.ref("blb_base.blb_processing_lead").id)])
        user_rec = users_rec[0]
        user_id = user_rec.id
        user_name = user_rec.name        
        notification_subject = "Deed Processing Marked Problematic"
        notification_details = "Deed Processing Task Marked Problematic: " + str(self.name)
        self.env["blb_base.notifications"]._send_system_notification(user_id,notification_subject,notification_details) 
        #get email
        email_to = user_rec.login
        self.env["blb_base.notifications"]._send_email(user_id,email_to,notification_subject,notification_details)
        #Get phone details
        partner_id = user_rec.partner_id
        phone_number = partner_id.phone
        self.env["blb_base.notifications"]._send_sms(user_id,phone_number,notification_details)
        #Change status 
        self.write({'status': 'problematic_file'})
        #Return - Action Summary Window
        view_id = self.env.ref('blb_deedprocessing.blb_deedprocessing_list').id 
        domain = "[('the_processing_officer','=', uid),('status','=','processing_officer')]"
        context =""
        return {
            'name':'Allocated to Me - All',
            'view_type':'form',
            'view_mode':'tree,form',
            'res_model':'blb_deedprocessing.blb_deedprocessing',
            'view_id': False,
            'type':'ir.actions.act_window',
            'target':'current',
            'context':context,
            'domain': domain
        }

    #Forward to Survey 
    def action_to_survey(self):
        if self.the_surveyor.id == False or self.the_surveyor.id == '':
            raise ValidationError(_('Please select Surveyor!'))
        #Send notification/sms/email 
        user_id = self.the_surveyor.id
        user_name = self.the_surveyor.name        
        notification_subject = "Deed Processing - Survey Needed"
        notification_details = "You have been allocated a Survey related to a Deed Processing Task: " + str(self.name)
        self.env["blb_base.notifications"]._send_system_notification(user_id,notification_subject,notification_details) 
        #get email
        email_to = self.the_surveyor.login
        self.env["blb_base.notifications"]._send_email(user_id,email_to,notification_subject,notification_details)
        #Get phone details
        partner_id = self.the_surveyor.partner_id
        phone_number = partner_id.phone
        self.env["blb_base.notifications"]._send_sms(user_id,phone_number,notification_details)
        #Change status 
        self.write({'status': 'pending_survey'})
        #Return - Action Window
        view_id = self.env.ref('blb_deedprocessing.blb_deedprocessing_list').id 
        domain = ""
        context =""
        return {
            'name':'BLB - Deed Processing',
            'view_type':'form',
            'view_mode':'tree,form',
            'res_model':'blb_deedprocessing.blb_deedprocessing',
            'view_id': False,
            'type':'ir.actions.act_window',
            'target':'current',
            'context':context,
            'domain': domain
        }

    #Forward to Planning
    def action_to_planning(self):
        #if self.the_surveyor == False:
        #    raise ValidationError(_('Please select Surveyor!'))
        #Send notification/sms/email
        users_rec = self.env['res.users'].search([('groups_id', '=', self.env.ref("blb_base.blb_chief_planner").id)])
        user_rec = users_rec[0]
        user_id = user_rec.id
        user_name = user_rec.name        
        notification_subject = "Deed Processing - Planning Needed"
        notification_details = "You have been allocated a Planning Task related to a Deed Processiing Task: " + str(self.name)
        self.env["blb_base.notifications"]._send_system_notification(user_id,notification_subject,notification_details) 
        #get email
        email_to = user_rec.login
        self.env["blb_base.notifications"]._send_email(user_id,email_to,notification_subject,notification_details)
        #Get phone details
        partner_id = user_rec.partner_id
        phone_number = partner_id.phone
        self.env["blb_base.notifications"]._send_sms(user_id,phone_number,notification_details)
        #Change status 
        self.write({'status': 'pending_planning'})
        #Return - Action Window
        view_id = self.env.ref('blb_deedprocessing.blb_deedprocessing_list').id 
        domain = ""
        context =""
        return {
            'name':'BLB - Deed Processing',
            'view_type':'form',
            'view_mode':'tree,form',
            'res_model':'blb_deedprocessing.blb_deedprocessing',
            'view_id': False,
            'type':'ir.actions.act_window',
            'target':'current',
            'context':context,
            'domain': domain
        }

    #Survey Done
    def action_survey_done(self):
        if self.survey_comments == False or len(self.survey_comments) < 5:
            raise ValidationError(_('Please enter Survey Comments!'))
        #Send notification/sms/email 
        #Get Team Lead Processing -----
        users_rec = self.env['res.users'].search([('groups_id', '=', self.env.ref("blb_base.blb_processing_lead").id)])
        user_rec = users_rec[0]
        user_id = user_rec.id
        user_name = user_rec.name        
        notification_subject = "Deed Processing - Survey Done"
        notification_details = "Survey work related to a Deed Processing Task has been completed: " + str(self.name)
        self.env["blb_base.notifications"]._send_system_notification(user_id,notification_subject,notification_details) 
        #get email
        email_to = user_rec.login
        self.env["blb_base.notifications"]._send_email(user_id,email_to,notification_subject,notification_details)
        #Get phone details
        partner_id = user_rec.partner_id
        phone_number = partner_id.phone
        self.env["blb_base.notifications"]._send_sms(user_id,phone_number,notification_details)
        #Change status 
        self.write({'status': 'survey_done'})
        #Return - Action Summary Window
        view_id = self.env.ref('blb_deedprocessing.blb_deedprocessing_list').id 
        domain = "[('status','=','pending_survey')]"
        context =""
        return {
            'name':'Allocated to Survey',
            'view_type':'form',
            'view_mode':'tree,form',
            'res_model':'blb_deedprocessing.blb_deedprocessing',
            'view_id': False,
            'type':'ir.actions.act_window',
            'target':'current',
            'context':context,
            'domain': domain
        }


    #Planning Done
    def action_planning_done(self):
        if self.planning_comments == False or len(self.planning_comments) < 5:
            raise ValidationError(_('Please enter Planning Comments!'))
        #Send notification/sms/email 
        #Get Team Lead Processing -----
        users_rec = self.env['res.users'].search([('groups_id', '=', self.env.ref("blb_base.blb_processing_lead").id)])
        user_rec = users_rec[0]
        user_id = user_rec.id
        user_name = user_rec.name        
        notification_subject = "Deed Processing - Planning Done"
        notification_details = "Planning work related to a Deed Processing Task has been completed: " + str(self.name)
        self.env["blb_base.notifications"]._send_system_notification(user_id,notification_subject,notification_details) 
        #get email
        email_to = user_rec.login
        self.env["blb_base.notifications"]._send_email(user_id,email_to,notification_subject,notification_details)
        #Get phone details
        partner_id = user_rec.partner_id
        phone_number = partner_id.phone
        self.env["blb_base.notifications"]._send_sms(user_id,phone_number,notification_details)
        #Change status 
        self.write({'status': 'planning_done'})
        #Return - Action Summary Window
        view_id = self.env.ref('blb_deedprocessing.blb_deedprocessing_list').id 
        domain = "[('status','=','pending_planning')]"
        context =""
        return {
            'name':'Allocated to Survey',
            'view_type':'form',
            'view_mode':'tree,form',
            'res_model':'blb_deedprocessing.blb_deedprocessing',
            'view_id': False,
            'type':'ir.actions.act_window',
            'target':'current',
            'context':context,
            'domain': domain
        }


    #Close 
    def action_closed(self):
        #Check User Rights
        userid = self.env.uid
        user_rec = self.env['res.users'].search([('id', '=', userid)])
        if self.env.user.has_group ('blb_base.blb_processing_lead'):
            #Update Client File - Block and Plot Number + state
            client_rec = self.client_file_no
            client_rec.update({'block_no': self.block_number, 'plot_no': self.plot_number, 'state': 'blbregistry'})
            #Close correspondence
            self.write({'status': 'closed'})
        else:
            ValidationError(_('You do not have permission to close this Request. Contact the Team Lead Processing!'))
        #Send SMS Details - Client
        #Send notification/sms/email       
        notification_subject = "Buganda Land Board - Deed Processing: " + str(self.client_file_no.name)
        notification_details = "Dear valued BLB Client, we are pleased to inform you that your Deed Prints, Ref: " + str(self.client_file_no.name) + " have been processed successfully. For more information contact us on 0800140140"
        #get email
        email_to = self.client_file_no.contact_email
        self.env["blb_base.notifications"]._send_email(userid,email_to,notification_subject,notification_details)
        #Get phone details
        phone_number = self.client_phone
        self.env["blb_base.notifications"]._send_sms(userid,phone_number,notification_details)
        
        #Return - Action Window
        view_id = self.env.ref('blb_deedprocessing.blb_deedprocessing_list').id 
        domain = ""
        context =""
        return {
            'name':'BLB - Deed Processing',
            'view_type':'form',
            'view_mode':'tree,form',
            'res_model':'blb_deedprocessing.blb_deedprocessing',
            'view_id': False,
            'type':'ir.actions.act_window',
            'target':'current',
            'context':context,
            'domain': domain
        }

    #Create 
    @api.model
    def create(self, vals):
        #Update Client File State
        client_id = vals['client_file_no']
        client_rec = self.env['blb_client.blb_client'].search([('id', '=', client_id)])
        if client_rec:
            client_rec.update({'state': 'processing'})
        res = super(blb_deedprocessing, self).create(vals)
        return res






class survey_fees(models.Model):
    _name = 'blb_deedprocessing.survey_fees'
    _description = 'BLB - Survey Fees'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'name'

    name = fields.Selection([
        ('Office Correspondence', 'Office Correspondence'),
        ('Fresh Survey', 'Fresh Survey'),
        ('Backlog Survey', 'Backlog Survey'),
        ('Field Correspondence', 'Field Correspondence'),        
        ('Massive Survey', 'Massive Survey'),
        ('Special Survey', 'Special Survey'),
        ('Site Revisit', 'Site Revisit'),
        ('Boundary Opening', 'Boundary Opening'),
        ('Re-Survey', 'Re-Survey'),
        ('Subdivision', 'Subdivision'),
        ('LAFI Survey', 'LAFI Survey'),
        ('Other', 'Other'),
        ], string='Type of Survey', required=True)
    amount = fields.Integer(string="Amount", required=True) 