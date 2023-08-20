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


####
# *******************************************************************************************************************
#  
#  All Correspondences - Starting at the Reception - CEO - Heads
#
# *******************************************************************************************************************
###
class all_correspondences(models.Model):
    _name = 'blb_correspondence.all_correspondences'
    _description = 'BLB - All Correspondences'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'date_correspondence desc'

    name = fields.Char(string="Name", compute="_compute_name", store=True) 
    reference_no = fields.Char(string="Reference No.", required=True, readonly=True)
    blb_branch = fields.Many2one('blb_base.branches', string='Branch', default=lambda self: self.env.user.blb_branch.id, readonly=True)
    date_correspondence = fields.Date(string="Date Request Received", required=True)
    days_elapsed = fields.Integer(string="Days Elapsed", compute="_compute_days_elapsed", store=True, readonly=True) 
    type_client = fields.Selection([
        ('BLB Client', 'BLB Client'),
        ('Other', 'Other'),
        ], string='Is a BLB Client?', required=True)
    client_file_no = fields.Many2one('blb_client.blb_client', string='Client/File No.')
    client_other = fields.Char(string="Client")
    client_phone = fields.Char(string="Client Phone", required=True)
    client_email = fields.Char(string="Client Email")
    correspondence = fields.Binary(string='Scanned Correspondence', required=True)
    correspondence_name = fields.Char(string="Scanned Correspondence - Name")
    correspondence_description = fields.Text(string="Correspondence Description", required=True)
    status = fields.Selection([
        ('incoming_correspondence', 'Incoming Correspondence'),
        ('forwarded_ceo', 'Forwarded to CEO'),
        ('forwarded_head_pps', 'Forwarded to Head PPSR'),
        ('forwarded_head_hrrm', 'Forwarded to Head HRRM'),
        ('forwarded_head_ntb', 'Forwarded to Head NTB'),
        ('forwarded_head_opbdca', 'Forwarded to Head OPBDCA'),
        ('forwarded_head_faplmis', 'Forwarded to Head FAPLMIS'),
        ('feedback_given', 'Feedback Given'),
        ('closed', 'Closed'),
        ], string='Status', readonly=True, copy=False, index=True, track_visibility='onchange', default='incoming_correspondence')
    urgency_level = fields.Selection([('Urgent', 'Urgent'), ('Normal', 'Normal')], string='Level of Urgency', required=True)
    ceo_instructions = fields.Text(string="CEO Instructions")

    type_correspodence = fields.Selection([
        ('PPSR Correspondence', 'PPSR Correspondence'),        
        ('HRRM Correspondence', 'HRRM Correspondence'),
        ('NTB Correspondence', 'NTB Correspondence'),
        ('OPBD CA Correspondence', 'OPBD CA Correspondence'),
        ('FAP LMIS Correspondence', 'FAP LMIS Correspondence'),     
        ], string='Type of Correspondence')
    date_forwared_dept = fields.Date(string="Date Forwarded", default=fields.Date.today, readonly=True)
    ppsr_request_id = fields.Many2one('blb_correspondence.blb_correspondence', string='PPSR Request ID', readonly=True)
    hrrm_request_id = fields.Many2one('blb_correspondence.hrrm_correspondences', string='HRRM Request ID', readonly=True)
    ntb_request_id = fields.Many2one('blb_correspondence.ntb_correspondences', string='NTB Request ID', readonly=True)
    opbdca_request_id = fields.Many2one('blb_correspondence.opbdca_correspondences', string='OPBDCA Request ID', readonly=True)
    faplmis_request_id = fields.Many2one('blb_correspondence.faplmis_correspondences', string='FAPLMIS Request ID', readonly=True)

    feedback_given = fields.Text(string="Feedback Given") 
    date_feedback_given = fields.Date(string="Date Feedback given", default=fields.Date.today, readonly=True)

    #Compute Name
    @api.depends('client_file_no','client_other','reference_no')
    def _compute_name(self):
        the_name = ""    
        for rec in self:
            if rec.client_file_no and rec.reference_no:
                the_name = str(rec.reference_no) + " - " + str(rec.client_file_no.name)
            elif rec.client_other and rec.reference_no:
                the_name = str(rec.reference_no) + " - " + str(rec.client_other)
            rec.name = the_name
        return the_name

    #Compute BLB Branch
    def _compute_blb_branch(self):
        user_branchid = 0
        #Current loggedin user id
        userid = self.env.uid
        user_rec = self.env['res.users'].search([('id', '=', userid)])
        user_branchid = user_rec.blb_branch.id
        rec.blb_branch = user_branchid
        return user_branchid

    #Compute Days Elapsed
    def _compute_days_elapsed(self):
        #Get Correspondences not closed
        correspondences_recs = self.env['blb_correspondence.all_correspondences'].search([('status', '!=', 'closed')])
        for rec in correspondences_recs:
            date_forwared_dept = str(rec.date_forwared_dept)
            today = date.today()
            today_date = today.strftime("%Y-%m-%d")
            d2 = datetime.strptime(date_forwared_dept, "%Y-%m-%d").date()
            d1 = datetime.strptime(today_date, "%Y-%m-%d").date()
            rd = relativedelta(d2, d1)
            duration = int(rd.days)
            #Update Days
            rec.update({ 'days_elapsed': duration })
        #Get PPRS Requests not closed
        ppsr_requests = self.env['blb_correspondence.blb_correspondence'].search([('status', '!=', 'closed')])
        for rec in ppsr_requests:
            date_request = str(rec.date_request)
            today = date.today()
            today_date = today.strftime("%Y-%m-%d")
            d2 = datetime.strptime(date_request, "%Y-%m-%d").date()
            d1 = datetime.strptime(today_date, "%Y-%m-%d").date()
            rd = relativedelta(d2, d1)
            duration = int(rd.days)
            #Update Days
            rec.update({ 'days_elapsed': duration })
        #Get HRRM Requests not closed
        hrrm_requests = self.env['blb_correspondence.hrrm_correspondences'].search([('status', '!=', 'closed')])
        for rec in hrrm_requests:
            date_request = str(rec.date_request)
            today = date.today()
            today_date = today.strftime("%Y-%m-%d")
            d2 = datetime.strptime(date_request, "%Y-%m-%d").date()
            d1 = datetime.strptime(today_date, "%Y-%m-%d").date()
            rd = relativedelta(d2, d1)
            duration = int(rd.days)
            #Update Days
            rec.update({ 'days_elapsed': duration })
        #Get NTB Requests not closed
        ntb_requests = self.env['blb_correspondence.ntb_correspondences'].search([('status', '!=', 'closed')])
        for rec in ntb_requests:
            date_request = str(rec.date_request)
            today = date.today()
            today_date = today.strftime("%Y-%m-%d")
            d2 = datetime.strptime(date_request, "%Y-%m-%d").date()
            d1 = datetime.strptime(today_date, "%Y-%m-%d").date()
            rd = relativedelta(d2, d1)
            duration = int(rd.days)
            #Update Days
            rec.update({ 'days_elapsed': duration })
        #Get OPBD CA Requests not closed
        opbdca_requests = self.env['blb_correspondence.opbdca_correspondences'].search([('status', '!=', 'closed')])
        for rec in opbdca_requests:
            date_request = str(rec.date_request)
            today = date.today()
            today_date = today.strftime("%Y-%m-%d")
            d2 = datetime.strptime(date_request, "%Y-%m-%d").date()
            d1 = datetime.strptime(today_date, "%Y-%m-%d").date()
            rd = relativedelta(d2, d1)
            duration = int(rd.days)
            #Update Days
            rec.update({ 'days_elapsed': duration })
        #Get FAP LMIS Requests not closed
        faplmis_requests = self.env['blb_correspondence.faplmis_correspondences'].search([('status', '!=', 'closed')])
        for rec in faplmis_requests:
            date_request = str(rec.date_request)
            today = date.today()
            today_date = today.strftime("%Y-%m-%d")
            d2 = datetime.strptime(date_request, "%Y-%m-%d").date()
            d1 = datetime.strptime(today_date, "%Y-%m-%d").date()
            rd = relativedelta(d2, d1)
            duration = int(rd.days)
            #Update Days
            rec.update({ 'days_elapsed': duration })

    #To CEO Office 
    def action_forward_ceo(self):
        #Send SMS to Client
        user_id = '';
        client_phone = self.client_phone
        sms_client = "Your Buganda Land Board Request - " + str(self.reference_no) + " has been Received. You will be Notified with Feedback soon!"
        self.env["blb_base.notifications"]._send_sms(user_id,client_phone,sms_client)
        #Send Email to Client
        client_email = self.client_email
        notification_subject = "Buganda Land Board Request - " + str(self.reference_no)
        notification_details = "Your Buganda Land Board Request with Reference No.: " + str(self.reference_no) + " has been Received! You will be Notified with Feedback soon!"
        self.env["blb_base.notifications"]._send_email(user_id,client_email,notification_subject,notification_details)
        #Change status
        self.write({'status': 'forwarded_ceo'})
        #Return - Action Window
        view_id = self.env.ref('blb_correspondence.all_correspondences_list').id 
        domain = ""
        context =""
        return {
            'name':'BLB - All Correspondences',
            'view_type':'form',
            'view_mode':'tree,form',
            'res_model':'blb_correspondence.all_correspondences',
            'view_id': False,
            'type':'ir.actions.act_window',
            'target':'current',
            'context':context,
            'domain': domain
        }

    #Forward to Heads
    def action_to_unit(self):
        #Check for fields
        if self.urgency_level == False:
            raise ValidationError(_('Please select Level of Urgency!'))
        elif self.ceo_instructions == False:
            raise ValidationError(_('Please enter the CEO Instructions!'))
        elif self.type_correspodence == False:
            raise ValidationError(_('Please Select Type of Correspondence!'))
        #Status
        status = 'incoming_correspondence'
        if self.type_correspodence == 'PPSR Correspondence':
            status = 'forwarded_head_pps'
        elif self.type_correspodence == 'HRRM Correspondence':
            status = 'forwarded_head_hrrm'
        elif self.type_correspodence == 'NTB Correspondence':
            status = 'forwarded_head_ntb'
        elif self.type_correspodence == 'OPBD CA Correspondence':
            status = 'forwarded_head_opbdca'
        elif self.type_correspodence == 'FAP LMIS Correspondence':
            status = 'forwarded_head_faplmis'        
        #Create Departmental Request
        correspondence_id = self.id
        type_correspodence = self.type_correspodence
        date_correspondence = self.date_correspondence
        correspondence_description = self.correspondence_description
        ceo_instructions = self.ceo_instructions
        type_client = self.type_client
        urgency_level = self.urgency_level
        client_id = ''
        if self.client_file_no:
            client_id = self.client_file_no.id
        client_other = ''
        if self.client_other:
            client_other = self.client_other
        self.action_create_deparmental_request(correspondence_id,type_correspodence,date_correspondence,correspondence_description,ceo_instructions,type_client,client_id,client_other,urgency_level)
        #Update Status
        today = date.today()
        self.write({'status': status, 'date_forwared_dept': today})
        #Return - Action Window
        view_id = self.env.ref('blb_correspondence.all_correspondences_list').id 
        domain = "[('status','=','forwarded_ceo')]"
        context =""
        return {
            'name':'Forwarded to CEO - Correspondences',
            'view_type':'form',
            'view_mode':'tree,form',
            'res_model':'blb_correspondence.all_correspondences',
            'view_id': False,
            'type':'ir.actions.act_window',
            'target':'current',
            'context':context,
            'domain': domain
        }


    #Create Customised Request for Each Department ***********************************
    #This is done in previous method    
    def action_create_deparmental_request(self, correspondence_id,type_correspodence,date_correspondence,correspondence_description,ceo_instructions,type_client,client_id,client_other,urgency_level):
        #Using Type of Request   
        if self.type_correspodence == 'PPSR Correspondence':
            #Create PPSR request
            ppsr_recordset = self.env['blb_correspondence.blb_correspondence']
            request_create = ppsr_recordset.create({
                'correspondence_id': correspondence_id,
                'date_request': date_correspondence,
                'request': correspondence_description,
                'ceo_instructions': ceo_instructions,
                'type_client': type_client,
                'client_file_no': client_id,
                'client_other': client_other,
                'urgency_level': urgency_level,
                'type_request': 'OPM Request',
                'status': 'pending_assignment'
            })
            request_id = int(request_create.id)
            #Update Correspondence
            correspondence_rec = self.env['blb_correspondence.all_correspondences'].search([('id', '=', correspondence_id)])
            correspondence_rec.update({ 'ppsr_request_id': request_id })
        elif self.type_correspodence == 'HRRM Correspondence':
            #Create HRRM request
            hrrm_recordset = self.env['blb_correspondence.hrrm_correspondences']
            request_create = hrrm_recordset.create({
                'correspondence_id': correspondence_id,
                'date_request': date_correspondence,
                'request': correspondence_description,
                'ceo_instructions': ceo_instructions,
                'type_client': type_client,
                'client_file_no': client_id,
                'client_other': client_other,
                'urgency_level': urgency_level,
                'type_request': 'OPM Request',
                'status': 'pending_assignment'
            })
            request_id = int(request_create.id)
            #Update Correspondence
            correspondence_rec = self.env['blb_correspondence.all_correspondences'].search([('id', '=', correspondence_id)])
            correspondence_rec.update({ 'hrrm_request_id': request_id })
        elif self.type_correspodence == 'NTB Correspondence':
            #Create NTB request
            ntb_recordset = self.env['blb_correspondence.ntb_correspondences']
            request_create = ntb_recordset.create({
                'correspondence_id': correspondence_id,
                'date_request': date_correspondence,
                'request': correspondence_description,
                'ceo_instructions': ceo_instructions,
                'type_client': type_client,
                'client_file_no': client_id,
                'client_other': client_other,
                'urgency_level': urgency_level,
                'type_request': 'OPM Request',
                'status': 'pending_assignment'
            })
            request_id = int(request_create.id)
            #Update Correspondence
            correspondence_rec = self.env['blb_correspondence.all_correspondences'].search([('id', '=', correspondence_id)])
            correspondence_rec.update({ 'ntb_request_id': request_id })
        elif self.type_correspodence == 'OPBD CA Correspondence':
            #Create OPBD CA request
            opbdca_recordset = self.env['blb_correspondence.opbdca_correspondences']
            request_create = opbdca_recordset.create({
                'correspondence_id': correspondence_id,
                'date_request': date_correspondence,
                'request': correspondence_description,
                'ceo_instructions': ceo_instructions,
                'type_client': type_client,
                'client_file_no': client_id,
                'client_other': client_other,
                'urgency_level': urgency_level,
                'type_request': 'OPM Request',
                'status': 'pending_assignment'
            })
            request_id = int(request_create.id)
            #Update Correspondence
            correspondence_rec = self.env['blb_correspondence.all_correspondences'].search([('id', '=', correspondence_id)])
            correspondence_rec.update({ 'opbdca_request_id': request_id })
        elif self.type_correspodence == 'FAP LMIS Correspondence':
            #Create FAP LMIS request
            faplmis_recordset = self.env['blb_correspondence.faplmis_correspondences']
            request_create = faplmis_recordset.create({
                'correspondence_id': correspondence_id,
                'date_request': date_correspondence,
                'request': correspondence_description,
                'ceo_instructions': ceo_instructions,
                'type_client': type_client,
                'client_file_no': client_id,
                'client_other': client_other,
                'urgency_level': urgency_level,
                'type_request': 'OPM Request',
                'status': 'pending_assignment'
            })
            request_id = int(request_create.id)
            #Update Correspondence
            correspondence_rec = self.env['blb_correspondence.all_correspondences'].search([('id', '=', correspondence_id)])
            correspondence_rec.update({ 'faplmis_request_id': request_id })

    #Feedback Given
    def action_feedback_given(self):
        if self.feedback_given == False:
            raise ValidationError(_('Please enter the Feedback Given!'))
        #Current loggedin user id
        feedback_given = self.feedback_given
        today = date.today()
        self.write({'status': 'feedback_given', 'feedback_given': feedback_given, 'date_feedback_given': today })
        #Return - Action Window
        view_id = self.env.ref('blb_correspondence.all_correspondences_list').id 
        domain = ""
        context =""
        return {
            'name':'BLB - All Correspondences',
            'view_type':'form',
            'view_mode':'tree,form',
            'res_model':'blb_correspondence.all_correspondences',
            'view_id': False,
            'type':'ir.actions.act_window',
            'target':'current',
            'context':context,
            'domain': domain
        }

    #Close Correspondence
    def action_closed(self, correspondence_id, feedback_given, date_feedback_given):
        #Get Correspondence
        correspondence_rec = self.env['blb_correspondence.all_correspondences'].search([('id', '=', correspondence_id)])
        #Send SMS to Client
        user_id = '';
        client_phone = correspondence_rec.client_phone
        sms_client = "Feedback for your Buganda Land Board Request - " + str(correspondence_rec.reference_no) + " has been given! Please contact them for details!"
        self.env["blb_base.notifications"]._send_sms(user_id,client_phone,sms_client)
        #Send Email to Client
        client_email = correspondence_rec.client_email
        notification_subject = "Feedback for Buganda Land Board Request - " + str(correspondence_rec.reference_no)
        notification_details = "Below is the Feedback for your Buganda Land Board Request with Ref No.: " + str(correspondence_rec.reference_no) + " \n\n " + str(feedback_given)
        self.env["blb_base.notifications"]._send_email(user_id,client_email,notification_subject,notification_details)
        #Update Correspondence status        
        correspondence_rec.update({'feedback_given': feedback_given, 'date_feedback_given': date_feedback_given, 'status': 'closed'})
        #return self.write({'feedback_given': feedback_given, 'date_feedback_given': date_feedback_given, 'status': 'closed'})

    #Put together the Reference No Sequence
    @api.model
    def create(self, vals):
        #Sequence
        seq = self.env['ir.sequence'].next_by_code('reference_no_sequence')
        vals['reference_no'] = seq
        res = super(all_correspondences, self).create(vals)
        return res











####
# ***************************************************************************************************************************************
#  
#  PPS Correspondences
#  These have a blb_correspondence.blb_correspondence name because we started with PPS correspondences
#
# ***************************************************************************************************************************************
###
class blb_correspondence(models.Model):
    _name = 'blb_correspondence.blb_correspondence'
    _description = 'BLB - PPS Correspondences'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'date_request desc'

    name = fields.Char(string="Name", compute="_compute_name", store=True) 
    correspondence_id = fields.Many2one('blb_correspondence.all_correspondences', string='Correspodence ID')
    date_request = fields.Date(string="Date Request", required=True)
    days_elapsed = fields.Integer(string="Days Elapsed", readonly=True)
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
        ], string='Type of Request') #, required=True
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

    request = fields.Text(string="Request Description") #, required=True
    ceo_instructions = fields.Text(string="CEO Instructions", readonly=True)
    remarks = fields.Text(string="Head Of Department Instructions")
    urgency_level = fields.Selection([('Urgent', 'Urgent'), ('Normal', 'Normal')], string='Level of Urgency', required=True)

    allocated_to = fields.Many2one('res.users', string='Allocated to')
    date_allocated = fields.Date(string="Date Allocated", default=fields.Date.today, readonly=True)
    report = fields.Binary(string='Report')
    report_name = fields.Char(string="Report Name")
    report_remarks = fields.Text(string="Remarks") 
    done_by = fields.Many2one('res.users', string='Feedback given by', readonly=True, default=lambda self: self.env.user)
    date_done = fields.Date(string="Date Feedback given", default=fields.Date.today, readonly=True)
    #current_user = fields.Many2one('res.users','Current User', default=lambda self: self.env.uid) 

    #Compute Name
    @api.depends('correspondence_id','client_file_no','client_other','type_request')
    def _compute_name(self):
        correspondence_name = ""    
        for rec in self:
            if rec.correspondence_id.id:
                correspondence_rec = self.env['blb_correspondence.all_correspondences'].search([('id', '=', rec.correspondence_id.id)])
                correspondence_name = correspondence_rec.name
            elif rec.client_file_no and rec.type_request:
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
            raise ValidationError(_('Please enter the Instructions/Remarks!'))
        self.write({'status': status})
        #Return - Action Window
        view_id = self.env.ref('blb_correspondence.blb_correspondence_list').id 
        domain = ""
        context =""
        return {
            'name':'BLB - PPS Correspondences',
            'view_type':'form',
            'view_mode':'tree,form',
            'res_model':'blb_correspondence.blb_correspondence',
            'view_id': False,
            'type':'ir.actions.act_window',
            'target':'current',
            'context':context,
            'domain': domain
        }

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
        self.write({'date_allocated': today, 'status': 'assigned_surveyor'})
        #Return - Action Window
        view_id = self.env.ref('blb_correspondence.blb_correspondence_list').id 
        domain = "[('type_request','=','Survey Request')]"
        context =""
        return {
            'name':'Survey Requests',
            'view_type':'form',
            'view_mode':'tree,form',
            'res_model':'blb_correspondence.blb_correspondence',
            'view_id': False,
            'type':'ir.actions.act_window',
            'target':'current',
            'context':context,
            'domain': domain
        }

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
        self.write({'date_allocated': today, 'status': 'assigned_planner'})
        #Return - Action Window
        view_id = self.env.ref('blb_correspondence.blb_correspondence_list').id 
        domain = "[('type_request','=','Planning Request')]"
        context =""
        return {
            'name':'Planning Requests',
            'view_type':'form',
            'view_mode':'tree,form',
            'res_model':'blb_correspondence.blb_correspondence',
            'view_id': False,
            'type':'ir.actions.act_window',
            'target':'current',
            'context':context,
            'domain': domain
        }

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
        self.write({'date_allocated': today, 'status': 'assigned_valuer'})
        #Return - Action Window
        view_id = self.env.ref('blb_correspondence.blb_correspondence_list').id 
        domain = "[('type_request','=','Valuation Request')]"
        context =""
        return {
            'name':'Valuation Requests',
            'view_type':'form',
            'view_mode':'tree,form',
            'res_model':'blb_correspondence.blb_correspondence',
            'view_id': False,
            'type':'ir.actions.act_window',
            'target':'current',
            'context':context,
            'domain': domain
        }

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
        self.write({'date_allocated': today, 'status': 'assigned_enforcer'})
        #Return - Action Window
        view_id = self.env.ref('blb_correspondence.blb_correspondence_list').id 
        domain = "[('type_request','=','Enforcer Request')]"
        context =""
        return {
            'name':'Enforcer Requests',
            'view_type':'form',
            'view_mode':'tree,form',
            'res_model':'blb_correspondence.blb_correspondence',
            'view_id': False,
            'type':'ir.actions.act_window',
            'target':'current',
            'context':context,
            'domain': domain
        }

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
        self.write({'date_allocated': today, 'status': 'assigned_researcher'})
        #Return - Action Window
        view_id = self.env.ref('blb_correspondence.blb_correspondence_list').id 
        domain = "[('type_request','=','Research Request')]"
        context =""
        return {
            'name':'Research Requests',
            'view_type':'form',
            'view_mode':'tree,form',
            'res_model':'blb_correspondence.blb_correspondence',
            'view_id': False,
            'type':'ir.actions.act_window',
            'target':'current',
            'context':context,
            'domain': domain
        }


    #Feedback Given
    def action_feedback_given(self):
        if self.report_remarks == False:
            raise ValidationError(_('Please enter the Report Remarks!'))
        #Current loggedin user id
        userid = self.env.uid
        today = date.today()
        self.write({'status': 'feedback_given', 'date_done': today, 'done_by': userid })
        #Return - Action Window
        view_id = self.env.ref('blb_correspondence.blb_correspondence_list').id 
        domain = "[('allocated_to','=', uid)]"
        context =""
        return {
            'name':'Allocated to Me',
            'view_type':'form',
            'view_mode':'tree,form',
            'res_model':'blb_correspondence.blb_correspondence',
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
        if self.env.user.has_group ('blb_base.blb_survey_chief_surveyor') or self.env.user.has_group ('blb_base.blb_chief_planner') or self.env.user.has_group ('blb_base.blb_chief_valuer') or self.env.user.has_group ('blb_base.blb_opm_pps') or self.env.user.has_group ('blb_base.blb_head_pps'):
            #Update Correspondence and Inform Client
            correspondence_id = self.correspondence_id.id
            feedback_given = self.report_remarks
            date_feedback_given = self.date_done
            self.env["blb_correspondence.all_correspondences"].action_closed(correspondence_id, feedback_given, date_feedback_given)
            #Close PPSR Request
            self.write({'status': 'closed'})
        else:
            raise ValidationError(_('You do not have permission to Close this Corresponse. Contact your Chief/Head!'))
        #Return - Action Window
        view_id = self.env.ref('blb_correspondence.blb_correspondence_list').id 
        domain = ""
        context =""
        return {
            'name':'BLB - PPS Correspondences',
            'view_type':'form',
            'view_mode':'tree,form',
            'res_model':'blb_correspondence.blb_correspondence',
            'view_id': False,
            'type':'ir.actions.act_window',
            'target':'current',
            'context':context,
            'domain': domain
        }







####
# ***************************************************************************************************************************************
#  
#  HRRM Correspondences
#
# ***************************************************************************************************************************************
###
class hrrm_correspondences(models.Model):
    _name = 'blb_correspondence.hrrm_correspondences'
    _description = 'BLB - HRRM Correspondences'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'date_request desc'

    name = fields.Char(string="Name", compute="_compute_name", store=True) 
    correspondence_id = fields.Many2one('blb_correspondence.all_correspondences', string='Correspodence ID')
    date_request = fields.Date(string="Date Request", required=True)
    days_elapsed = fields.Integer(string="Days Elapsed", readonly=True)
    type_client = fields.Selection([
        ('BLB Client', 'BLB Client'),
        ('Other', 'Other'),
        ], string='Is a BLB Client?', required=True)
    client_file_no = fields.Many2one('blb_client.blb_client', string='Client/File No.')
    client_other = fields.Char(string="Author From")
    type_request = fields.Selection([
        ('OPM Request', 'OPM Request'),
        ], string='Type of Request')  #, required=True
    status = fields.Selection([
        ('pending_assignment', 'Pending Assignment'),
        ('assigned_opm', 'Assigned to OPM'),
        ('feedback_given', 'Feedback Given'),
        ('closed', 'Closed'),
        ], string='Status', readonly=True, copy=False, index=True, track_visibility='onchange', default='pending_assignment')
    urgency_level = fields.Selection([('Urgent', 'Urgent'), ('Normal', 'Normal')], string='Level of Urgency', required=True)
    request = fields.Text(string="Request Description") #, required=True
    ceo_instructions = fields.Text(string="CEO Instructions", readonly=True)
    remarks = fields.Text(string="Head Of Department Instructions")
    report = fields.Binary(string='Report')
    report_name = fields.Char(string="Report Name")
    report_remarks = fields.Text(string="Remarks") 
    date_done = fields.Date(string="Date Feedback given", default=fields.Date.today, readonly=True)

    #Compute Name
    @api.depends('correspondence_id','client_file_no','client_other','type_request')
    def _compute_name(self):
        correspondence_name = ""    
        for rec in self:
            if rec.correspondence_id.id:
                correspondence_rec = self.env['blb_correspondence.all_correspondences'].search([('id', '=', rec.correspondence_id.id)])
                correspondence_name = correspondence_rec.name
            elif rec.client_file_no and rec.type_request:
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
        #Check of requirements
        if self.remarks == False:
            raise ValidationError(_('Please enter the Remarks/Instructions!'))
        self.write({'status': status})
        #Return - Action Window
        view_id = self.env.ref('blb_correspondence.hrrm_correspondences_list').id 
        domain = ""
        context =""
        return {
            'name':'BLB - HRRM Correspondences',
            'view_type':'form',
            'view_mode':'tree,form',
            'res_model':'blb_correspondence.hrrm_correspondences',
            'view_id': False,
            'type':'ir.actions.act_window',
            'target':'current',
            'context':context,
            'domain': domain
        }

    #Feedback Given
    def action_feedback_given(self):
        if self.report_remarks == False:
            raise ValidationError(_('Please enter the Report Remarks!'))
        #Current loggedin user id
        userid = self.env.uid
        today = date.today()
        self.write({'status': 'feedback_given', 'date_done': today})
        #Return - Action Window
        view_id = self.env.ref('blb_correspondence.hrrm_correspondences_list').id 
        domain = ""
        context =""
        return {
            'name':'BLB - HRRM Correspondences',
            'view_type':'form',
            'view_mode':'tree,form',
            'res_model':'blb_correspondence.hrrm_correspondences',
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
        if self.env.user.has_group ('blb_base.blb_opm_hrrm') or self.env.user.has_group ('blb_base.blb_head_hrrm'):
            #Update Correspondence and Inform Client
            correspondence_id = self.correspondence_id.id
            feedback_given = self.report_remarks
            date_feedback_given = self.date_done
            self.env["blb_correspondence.all_correspondences"].action_closed(correspondence_id, feedback_given, date_feedback_given)
            #Close PPSR Request
            self.write({'status': 'closed'})
        else:
            raise ValidationError(_('You do not have permission to Close this Corresponse. Contact your OPM/Head!'))
        #Return - Action Window
        view_id = self.env.ref('blb_correspondence.hrrm_correspondences_list').id 
        domain = ""
        context =""
        return {
            'name':'BLB - HRRM Correspondences',
            'view_type':'form',
            'view_mode':'tree,form',
            'res_model':'blb_correspondence.hrrm_correspondences',
            'view_id': False,
            'type':'ir.actions.act_window',
            'target':'current',
            'context':context,
            'domain': domain
        }







####
# ***************************************************************************************************************************************
#  
#  NTB Correspondences
#
# ***************************************************************************************************************************************
###
class ntb_correspondences(models.Model):
    _name = 'blb_correspondence.ntb_correspondences'
    _description = 'BLB - NTB Correspondences'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'date_request desc'

    name = fields.Char(string="Name", compute="_compute_name", store=True) 
    correspondence_id = fields.Many2one('blb_correspondence.all_correspondences', string='Correspodence ID')
    date_request = fields.Date(string="Date Request", required=True)
    days_elapsed = fields.Integer(string="Days Elapsed", readonly=True)
    type_client = fields.Selection([
        ('BLB Client', 'BLB Client'),
        ('Other', 'Other'),
        ], string='Is a BLB Client?', required=True)
    client_file_no = fields.Many2one('blb_client.blb_client', string='Client/File No.')
    client_other = fields.Char(string="Author From")
    type_request = fields.Selection([
        ('OPM Request', 'OPM Request'),
        ], string='Type of Request')  #, required=True
    status = fields.Selection([
        ('pending_assignment', 'Pending Assignment'),
        ('assigned_opm', 'Assigned to OPM'),
        ('feedback_given', 'Feedback Given'),
        ('closed', 'Closed'),
        ], string='Status', readonly=True, copy=False, index=True, track_visibility='onchange', default='pending_assignment')
    urgency_level = fields.Selection([('Urgent', 'Urgent'), ('Normal', 'Normal')], string='Level of Urgency', required=True)
    request = fields.Text(string="Request Description") #, required=True
    ceo_instructions = fields.Text(string="CEO Instructions", readonly=True)
    remarks = fields.Text(string="Head Of Department Instructions")
    report = fields.Binary(string='Report')
    report_name = fields.Char(string="Report Name")
    report_remarks = fields.Text(string="Remarks") 
    date_done = fields.Date(string="Date Feedback given", default=fields.Date.today, readonly=True)

    #Compute Name
    @api.depends('correspondence_id','client_file_no','client_other','type_request')
    def _compute_name(self):
        correspondence_name = ""    
        for rec in self:
            if rec.correspondence_id.id:
                correspondence_rec = self.env['blb_correspondence.all_correspondences'].search([('id', '=', rec.correspondence_id.id)])
                correspondence_name = correspondence_rec.name
            elif rec.client_file_no and rec.type_request:
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
        #Check of requirements
        if self.remarks == False:
            raise ValidationError(_('Please enter the Remarks/Instructions!'))
        self.write({'status': status})
        #Return - Action Window
        view_id = self.env.ref('blb_correspondence.ntb_correspondences_list').id 
        domain = ""
        context =""
        return {
            'name':'BLB - NTB Correspondences',
            'view_type':'form',
            'view_mode':'tree,form',
            'res_model':'blb_correspondence.ntb_correspondences',
            'view_id': False,
            'type':'ir.actions.act_window',
            'target':'current',
            'context':context,
            'domain': domain
        }

    #Feedback Given
    def action_feedback_given(self):
        if self.report_remarks == False:
            raise ValidationError(_('Please enter the Report Remarks!'))
        #Current loggedin user id
        userid = self.env.uid
        today = date.today()
        self.write({'status': 'feedback_given', 'date_done': today})
        #Return - Action Window
        view_id = self.env.ref('blb_correspondence.ntb_correspondences_list').id 
        domain = ""
        context =""
        return {
            'name':'BLB - NTB Correspondences',
            'view_type':'form',
            'view_mode':'tree,form',
            'res_model':'blb_correspondence.ntb_correspondences',
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
        if self.env.user.has_group ('blb_base.blb_opm_ntb') or self.env.user.has_group ('blb_base.blb_head_ntb'):
            #Update Correspondence and Inform Client
            correspondence_id = self.correspondence_id.id
            feedback_given = self.report_remarks
            date_feedback_given = self.date_done
            self.env["blb_correspondence.all_correspondences"].action_closed(correspondence_id, feedback_given, date_feedback_given)
            #Close PPSR Request
            self.write({'status': 'closed'})
        else:
            raise ValidationError(_('You do not have permission to Close this Corresponse. Contact your OPM/Head!'))
        #Return - Action Window
        view_id = self.env.ref('blb_correspondence.ntb_correspondences_list').id 
        domain = ""
        context =""
        return {
            'name':'BLB - NTB Correspondences',
            'view_type':'form',
            'view_mode':'tree,form',
            'res_model':'blb_correspondence.ntb_correspondences',
            'view_id': False,
            'type':'ir.actions.act_window',
            'target':'current',
            'context':context,
            'domain': domain
        }







####
# ***************************************************************************************************************************************
#  
#  OPBD CA Correspondences
#
# ***************************************************************************************************************************************
###
class opbdca_correspondences(models.Model):
    _name = 'blb_correspondence.opbdca_correspondences'
    _description = 'BLB - OPBD CA Correspondences'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'date_request desc'

    name = fields.Char(string="Name", compute="_compute_name", store=True) 
    correspondence_id = fields.Many2one('blb_correspondence.all_correspondences', string='Correspodence ID')
    date_request = fields.Date(string="Date Request", required=True)
    days_elapsed = fields.Integer(string="Days Elapsed", readonly=True)
    type_client = fields.Selection([
        ('BLB Client', 'BLB Client'),
        ('Other', 'Other'),
        ], string='Is a BLB Client?', required=True)
    client_file_no = fields.Many2one('blb_client.blb_client', string='Client/File No.')
    client_other = fields.Char(string="Author From")
    type_request = fields.Selection([
        ('OPM Request', 'OPM Request'),
        ], string='Type of Request')   #, required=True
    status = fields.Selection([
        ('pending_assignment', 'Pending Assignment'),
        ('assigned_opm', 'Assigned to OPM'),
        ('feedback_given', 'Feedback Given'),
        ('closed', 'Closed'),
        ], string='Status', readonly=True, copy=False, index=True, track_visibility='onchange', default='pending_assignment')
    urgency_level = fields.Selection([('Urgent', 'Urgent'), ('Normal', 'Normal')], string='Level of Urgency', required=True)
    request = fields.Text(string="Request Description")   #, required=True
    ceo_instructions = fields.Text(string="CEO Instructions", readonly=True)
    remarks = fields.Text(string="Head Of Department Instructions")
    report = fields.Binary(string='Report')
    report_name = fields.Char(string="Report Name")
    report_remarks = fields.Text(string="Remarks") 
    date_done = fields.Date(string="Date Feedback given", default=fields.Date.today, readonly=True)

    #Compute Name
    @api.depends('correspondence_id','client_file_no','client_other','type_request')
    def _compute_name(self):
        correspondence_name = ""    
        for rec in self:
            if rec.correspondence_id.id:
                correspondence_rec = self.env['blb_correspondence.all_correspondences'].search([('id', '=', rec.correspondence_id.id)])
                correspondence_name = correspondence_rec.name
            elif rec.client_file_no and rec.type_request:
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
        #Check of requirements
        if self.remarks == False:
            raise ValidationError(_('Please enter the Remarks/Instructions!'))
        self.write({'status': status})
        #Return - Action Window
        view_id = self.env.ref('blb_correspondence.opbdca_correspondences_list').id 
        domain = ""
        context =""
        return {
            'name':'BLB - OPBD CA Correspondences',
            'view_type':'form',
            'view_mode':'tree,form',
            'res_model':'blb_correspondence.opbdca_correspondences',
            'view_id': False,
            'type':'ir.actions.act_window',
            'target':'current',
            'context':context,
            'domain': domain
        }

    #Feedback Given
    def action_feedback_given(self):
        if self.report_remarks == False:
            raise ValidationError(_('Please enter the Report Remarks!'))
        #Current loggedin user id
        userid = self.env.uid
        today = date.today()
        self.write({'status': 'feedback_given', 'date_done': today})
        #Return - Action Window
        view_id = self.env.ref('blb_correspondence.opbdca_correspondences_list').id 
        domain = ""
        context =""
        return {
            'name':'BLB - OPBD CA Correspondences',
            'view_type':'form',
            'view_mode':'tree,form',
            'res_model':'blb_correspondence.opbdca_correspondences',
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
        if self.env.user.has_group ('blb_base.blb_opm_opbdca') or self.env.user.has_group ('blb_base.blb_head_opbdca'):
            #Update Correspondence and Inform Client
            correspondence_id = self.correspondence_id.id
            feedback_given = self.report_remarks
            date_feedback_given = self.date_done
            self.env["blb_correspondence.all_correspondences"].action_closed(correspondence_id, feedback_given, date_feedback_given)
            #Close PPSR Request
            self.write({'status': 'closed'})
        else:
            raise ValidationError(_('You do not have permission to Close this Corresponse. Contact your OPM/Head!'))
        #Return - Action Window
        view_id = self.env.ref('blb_correspondence.opbdca_correspondences_list').id 
        domain = ""
        context =""
        return {
            'name':'BLB - OPBD CA Correspondences',
            'view_type':'form',
            'view_mode':'tree,form',
            'res_model':'blb_correspondence.opbdca_correspondences',
            'view_id': False,
            'type':'ir.actions.act_window',
            'target':'current',
            'context':context,
            'domain': domain
        }







####
# ***************************************************************************************************************************************
#  
#  FAP LMIS Correspondences
#
# ***************************************************************************************************************************************
###
class faplmis_correspondences(models.Model):
    _name = 'blb_correspondence.faplmis_correspondences'
    _description = 'BLB - FAP LMIS Correspondences'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'date_request desc'

    name = fields.Char(string="Name", compute="_compute_name", store=True) 
    correspondence_id = fields.Many2one('blb_correspondence.all_correspondences', string='Correspodence ID')
    date_request = fields.Date(string="Date Request", required=True)
    days_elapsed = fields.Integer(string="Days Elapsed", readonly=True)
    type_client = fields.Selection([
        ('BLB Client', 'BLB Client'),
        ('Other', 'Other'),
        ], string='Is a BLB Client?', required=True)
    client_file_no = fields.Many2one('blb_client.blb_client', string='Client/File No.')
    client_other = fields.Char(string="Author From")
    type_request = fields.Selection([
        ('OPM Request', 'OPM Request'),
        ], string='Type of Request')   #, required=True
    status = fields.Selection([
        ('pending_assignment', 'Pending Assignment'),
        ('assigned_opm', 'Assigned to OPM'),
        ('feedback_given', 'Feedback Given'),
        ('closed', 'Closed'),
        ], string='Status', readonly=True, copy=False, index=True, track_visibility='onchange', default='pending_assignment')
    urgency_level = fields.Selection([('Urgent', 'Urgent'), ('Normal', 'Normal')], string='Level of Urgency', required=True)
    request = fields.Text(string="Request Description")  #, required=True
    ceo_instructions = fields.Text(string="CEO Instructions", readonly=True)
    remarks = fields.Text(string="Head Of Department Instructions")
    report = fields.Binary(string='Report')
    report_name = fields.Char(string="Report Name")
    report_remarks = fields.Text(string="Remarks") 
    date_done = fields.Date(string="Date Feedback given", default=fields.Date.today, readonly=True)

    #Compute Name
    @api.depends('correspondence_id','client_file_no','client_other','type_request')
    def _compute_name(self):
        correspondence_name = ""    
        for rec in self:
            if rec.correspondence_id.id:
                correspondence_rec = self.env['blb_correspondence.all_correspondences'].search([('id', '=', rec.correspondence_id.id)])
                correspondence_name = correspondence_rec.name
            elif rec.client_file_no and rec.type_request:
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
        #Check of requirements
        if self.remarks == False:
            raise ValidationError(_('Please enter the Remarks/Instructions!'))
        self.write({'status': status})
        #Return - Action Window
        view_id = self.env.ref('blb_correspondence.faplmis_correspondences_list').id 
        domain = ""
        context =""
        return {
            'name':'BLB - FAP LMIS Correspondences',
            'view_type':'form',
            'view_mode':'tree,form',
            'res_model':'blb_correspondence.faplmis_correspondences',
            'view_id': False,
            'type':'ir.actions.act_window',
            'target':'current',
            'context':context,
            'domain': domain
        }

    #Feedback Given
    def action_feedback_given(self):
        if self.report_remarks == False:
            raise ValidationError(_('Please enter the Report Remarks!'))
        #Current loggedin user id
        userid = self.env.uid
        today = date.today()
        self.write({'status': 'feedback_given', 'date_done': today})
        #Return - Action Window
        view_id = self.env.ref('blb_correspondence.faplmis_correspondences_list').id 
        domain = ""
        context =""
        return {
            'name':'BLB - FAP LMIS Correspondences',
            'view_type':'form',
            'view_mode':'tree,form',
            'res_model':'blb_correspondence.faplmis_correspondences',
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
        if self.env.user.has_group ('blb_base.blb_opm_faplmis') or self.env.user.has_group ('blb_base.blb_head_faplmis'):
            #Update Correspondence and Inform Client
            correspondence_id = self.correspondence_id.id
            feedback_given = self.report_remarks
            date_feedback_given = self.date_done
            self.env["blb_correspondence.all_correspondences"].action_closed(correspondence_id, feedback_given, date_feedback_given)
            #Close PPSR Request
            self.write({'status': 'closed'})
        else:
            raise ValidationError(_('You do not have permission to Close this Corresponse. Contact your OPM/Head!'))
        #Return - Action Window
        view_id = self.env.ref('blb_correspondence.faplmis_correspondences_list').id 
        domain = ""
        context =""
        return {
            'name':'BLB - FAP LMIS Correspondences',
            'view_type':'form',
            'view_mode':'tree,form',
            'res_model':'blb_correspondence.faplmis_correspondences',
            'view_id': False,
            'type':'ir.actions.act_window',
            'target':'current',
            'context':context,
            'domain': domain
        }










