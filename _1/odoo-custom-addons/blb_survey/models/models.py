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



class blb_survey(models.Model):
    _name = 'blb_survey.blb_survey'
    _description = 'BLB Survey Unit'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'status desc'

    name = fields.Char(string="Name", compute="_compute_name", store=True) 
    client_file_no = fields.Many2one('blb_client.blb_client', string='Client', required=True)
    allocated_surveyor = fields.Many2one('res.users', string='Allocated Surveyor', required=True, domain=lambda self: [("groups_id", "=",self.env.ref("blb_base.blb_survey_surveyor").id)]) 
    date_allocation = fields.Date(string="Date Allocation", default=fields.Date.today, required=True)
    days_difference = fields.Integer(string='Days since Allocation', compute='_compute_days_difference')
    job_category = fields.Selection([
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
        ], string='Job Category', required=True)
    job_requirement_details = fields.Text(string="Job Requirements/Details") 
    urgency_level = fields.Selection([
        ('Urgent', 'Urgent'),
        ('Normal', 'Normal'),        
        ], string='Level of Urgency')
    status = fields.Selection([
        ('pending_allocation', 'Pending Allocation'),
        ('allocated', 'Allocated'),
        ('job_scheduled', 'Job Scheduled'),    
        ('pending_confirmation', 'Pending Job Form Confirmation'),
        ('job_done', 'Job Done'),
        ('overdue', 'Overdue'),
        ('forwarded_planning', 'Forwarded To Planning'),
        ], string='Status', readonly=True, copy=False, index=True, track_visibility='onchange', default='pending_allocation')
    #date_client_contacted = fields.Date(string="Date Client Contacted", default=fields.Date.today) 
    #date_work_scheduled = fields.Date(string="Date Work Scheduled", default=fields.Date.today)
    why_task_pending = fields.Char(string="Reason why Survey is pending")
    plot_number = fields.Char(string="Plot Number")
    block_number = fields.Char(string="Block Number")
    county = fields.Char(string="County")
    boundary_opening_purpose = fields.Selection([
        ('lease_application', 'Lease Application'),
        ('lease_extension', 'Lease Extension'),
        ('lease_renewal', 'Lease Renewal'),
        ('returned_estate', 'Weetukire'),
        ('dispute_resolution', 'Dispute Resolution'),
        ('other', 'Other'),        
        ], string='Purpose of Boundary Opening')
    correspondence_details = fields.Selection([
        ('trim_plot', 'Trim plot to planned road'),
        ('status_report', 'Write Status Report'),
        ('resurvey_letter', 'Write Resurvey Letter'),
        ('cancel_letter', 'Write Cancellation Letter'),
        ('client_response', 'Write Client Response'),
        ('jrj_location', 'Provide JRJ Address'),
        ('spray_corner', 'Provide Spray Corner'),
        ('file_results', 'File our results'),
        ('compile_jrj', 'Compile JRJ'),
        ('make_edits_revert', 'Make edits and revert'),
        ('discuss_this', 'Let us discuss this'),
        ('make_edits_final', 'Make edits and print final'),
        ('other', 'Other'),
        ], string='Correspondences Details')  #Office
    survey_job_form = fields.Binary(string='Survey Job Form')
    survey_jobform_name = fields.Char(string="Survey Job Form Name")
    index_diagram = fields.Binary("Index Diagram")
    index_diagram_name = fields.Char('Index Diagram Name')
    remarks_comments_wayforward = fields.Text(string="Remarks/Comments/Way Forward")
    date_completion = fields.Date(string="Date of completion", default=fields.Date.today)
    submitted_by = fields.Many2one('res.users', string='Submitted by', default=lambda self: self.env.user)

    #Compute Name
    @api.depends('client_file_no','job_category')
    def _compute_name(self):
        survey_task_name = ""    
        for rec in self:
            if rec.client_file_no and rec.job_category:
                #raise ValidationError(_(rec.client_file_no.name))
                survey_task_name = str(rec.client_file_no.name) + " - " + str(rec.job_category)
            rec.name = survey_task_name
        return survey_task_name

    #Compute Days Difference Allocation
    @api.depends('date_allocation')
    def _compute_days_difference(self):
        today = date.today()
        days_difference = 0
        for rec in self:           
            if rec.date_allocation and (rec.status == 'allocated' or rec.status == 'pending_confirmation'):
                #raise ValidationError(_( str(today) + "==" + str(rec.status) + "==" + str(rec.date_allocation) ))
                date_allocation = datetime.strptime(str(rec.date_allocation),'%Y-%m-%d').date()
                today_date = datetime.strptime(str(today),'%Y-%m-%d').date()
                days_difference = (today_date - date_allocation).days
                #raise ValidationError(_(days_difference))
                if days_difference > 14:
                    rec.write({ 'days_difference': days_difference, 'status': 'overdue'})
                else:
                    rec.write({ 'days_difference': days_difference })
            else:
                #raise ValidationError(_(today)) 
                return rec.write({ 'days_difference': False })

    
    #Allocated
    def action_to_allocated(self):
        if self.allocated_surveyor == False:
            raise ValidationError(_('Please select Allocated Surveyor!'))  
        elif self.date_allocation == False:
            raise ValidationError(_('Please select Date of Allocation!'))
        elif self.job_category == False:
            raise ValidationError(_('Please select Job Category!'))
        elif self.job_requirement_details == False:
            raise ValidationError(_('Please enter Job Requirements/Details!'))
        #Send notification/sms/email
        user_id = allocated_surveyor.id
        user_name = allocated_surveyor.name        
        notification_subject = "Survey Allocation"
        notification_details = "You have been allocated a Survey Task: " + str(self.name)
        self.env["blb_base.notifications"]._send_system_notification(user_id,notification_subject,notification_details) 
        #get email
        email_to = allocated_surveyor.login
        self.env["blb_base.notifications"]._send_email(user_id,email_to,notification_subject,notification_details)
        #Get phone details
        partner_id = allocated_surveyor.partner_id
        phone_number = partner_id.phone
        self.env["blb_base.notifications"]._send_sms(user_id,phone_number,notification_details)
        #Change status 
        return self.write({'status': 'allocated'})

    #Job Scheduled
    def action_job_scheduled(self):
        if self.date_client_contacted == False:
            raise ValidationError(_('Please select Date Client was Contacted!'))
        elif self.date_work_scheduled == False:
            raise ValidationError(_('Please select Date Work is Scheduled!'))
        return self.write({'status': 'job_scheduled'})

    #Pending Job Form Confirmation
    def pending_confirmation(self):
        if self.survey_job_form == False:
            raise ValidationError(_('Please attach the Survey Job Form!'))
        return self.write({'status': 'defer_comments'})

    #Job Not Satisfactorily Donw
    def back_to_surveyor(self):
        if self.remarks_comments_wayforward == False:
            raise ValidationError(_('Please enter Remarks/Comments!'))
        return self.write({'status': 'allocated'})

    #Mark Surveyor Job Done
    def action_mark_survey_job_done(self):
    	#If Non-field Job or Confirmation by Chief Surveyor
        if self.status == "allocated" or self.status == "pending_confirmation":
            if self.survey_job_form == False:
                raise ValidationError(_('Please attach the Survey Job Form!'))
            elif self.date_completion == False:
                raise ValidationError(_('Please select Date of Completion!'))
        elif self.status == "job_scheduled":
            if self.survey_job_form == False:
                raise ValidationError(_('Please attach the Survey Job Form!'))
            elif self.remarks_comments_wayforward == False:
                raise ValidationError(_('Please enter Remarks/Comments/Way Forward!'))
            elif self.date_completion == False:
                raise ValidationError(_('Please select Date of Completion!'))
        #Current loggedin user id
        userid = self.env.uid
        return self.write({'status': 'job_done', 'submitted_by': userid })


    ## **** MAIN/PRIMARY Flow *******************************************************
    ## **** Forward File to PLANNING
    def forward_toplanning(self):
        return self.write({'status': 'forwarded_planning'})

    

    #Write
    def write(self, vals):
        res = super(blb_survey, self).write(vals)
        return res
        # if self.env.user.has_group('blb_base.blb_survey_surveyor'):
        #     #Check if Surveyor has Overdue Tasks before working on new allocated task
        #     userid = self.env.uid
        #     overdue_allocated_tasks = self.env['blb_survey.blb_survey'].search([('status', '=', 'overdue'),('allocated_surveyor', '=', userid)])
        #     #If this Task is Overdue - proceed
        #     if self.status == "overdue":
        #         res = super(blb_survey, self).write(vals)       
        #         return res
        #     elif len(overdue_allocated_tasks) > 0 and self.status != "overdue":
        #         raise ValidationError(_('Please Work on your Overdue Tasks before attending to other Allocated Tasks!'))
        # else:
        #     res = super(blb_survey, self).write(vals)
        #     return res







