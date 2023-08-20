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
	blb_branch = fields.Many2one('blb_base.branches', string='Branch', default=lambda self: self.env.user.blb_branch.id, ondelete='cascade')
	date_correspondence = fields.Date(string="Date Request Received", required=True, default=fields.Date.today)
	days_elapsed = fields.Integer(string="Days Elapsed", compute="_compute_days_elapsed", store=True, readonly=True) 
	type_client = fields.Selection([
		('BLB Client', 'BLB Client'),
		('Other', 'Other'),
		], string='Is a BLB Client?', required=True)
	client_file_no = fields.Many2one('blb_client.blb_client', string='Client/File No.', ondelete='cascade')
	client_other = fields.Char(string="Client")
	client_phone = fields.Char(string="Client Phone", required=True)
	client_email = fields.Char(string="Client Email")

	scanned_filetype= fields.Selection([
		('Image', 'Image'),
		('PDF', 'PDF'),
		], string='Scanned File Type?', required=True)
	correspondence = fields.Binary(string='PDF Scan')
	correspondence_image = fields.Binary(string='Image Scan')
	correspondence_name = fields.Char(string="Scanned Correspondence - Name")
	correspondence_description = fields.Text(string="Correspondence Description", required=True)
	status = fields.Selection([
		('incoming_correspondence', 'Incoming'),
		('forwarded_ceo', 'Forwarded to CEO'),
		('forwarded_chairboard', 'Forwarded to Chair Board'),
		('forwarded_head_pps', 'Forwarded to Head PPSR'),
		('forwarded_head_hrrm', 'Forwarded to Head HRRM'),
		('forwarded_head_ntb', 'Forwarded to Head NTB'),
		('forwarded_head_opbdca', 'Forwarded to Head OPBDCA'),
		('forwarded_head_faplmis', 'Forwarded to Head FAPLMIS'),
		('forwarded_dept', 'Forwarded to Department'),
		('feedback_given', 'Feedback Given'),
		('closed', 'Closed'),
		], string='Status', readonly=True, copy=False, index=True, track_visibility='onchange', default='incoming_correspondence')
	urgency_level = fields.Selection([('Urgent', 'Urgent'), ('Normal', 'Normal')], string='Level of Urgency', required=True)
	ceo_remarks = fields.Many2one('blb_correspondence.ceo_remarks', string='CEO Remarks', ondelete='cascade')
	ceo_instructions = fields.Text(string="Instructions")

	type_correspodence = fields.Selection([
		('PPSR Correspondence', 'PPSR Correspondence'),        
		('HRRM Correspondence', 'HRRM Correspondence'),
		('NTB Correspondence', 'NTB Correspondence'),
		('OPBD CA Correspondence', 'OPBD CA Correspondence'),
		('FAP LMIS Correspondence', 'FAP LMIS Correspondence'),     
		], string='Correspondence Type')
	type_correspodence_ids = fields.Many2many(
		comodel_name='blb_correspondence.type_correspodence', 
		column1='all_correspondence_id',
		column2='type_correspodence_id',
		relation='allcorrespondences_typecorrespodence_rel', string='Type of Correspondence')
	forwarded_to_ids = fields.Many2many(
		comodel_name='blb_correspondence.forwarded_to', 
		column1='all_correspondence_id',
		column2='forwarded_to_id',
		relation='allcorrespondences_forwardedto_rel', string='Forward To')
	type_correspodence_selected = fields.Boolean(string="Type of Correspondence Selected", default=False)

	date_forwared_dept = fields.Date(string="Date Forwarded", default=fields.Date.today, readonly=True)
	ppsr_request_id = fields.Many2one('blb_correspondence.blb_correspondence', string='PPSR Request ID', readonly=True, ondelete='cascade')
	hrrm_request_id = fields.Many2one('blb_correspondence.hrrm_correspondences', string='HRRM Request ID', readonly=True, ondelete='cascade')
	ntb_request_id = fields.Many2one('blb_correspondence.ntb_correspondences', string='NTB Request ID', readonly=True, ondelete='cascade')
	opbdca_request_id = fields.Many2one('blb_correspondence.opbdca_correspondences', string='OPBDCA Request ID', readonly=True, ondelete='cascade')
	faplmis_request_id = fields.Many2one('blb_correspondence.faplmis_correspondences', string='FAPLMIS Request ID', readonly=True, ondelete='cascade')

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

	#Check CEO Remarks
	@api.onchange('ceo_remarks')
	def _onchange_ceo_remarks(self):
		for rec in self:
			if rec.ceo_remarks:
				rec.ceo_instructions = rec.ceo_remarks.name

	#Check for Type Correspodences 
	@api.onchange('type_correspodence_ids')
	def _onchange_type_correspodence_ids(self):
		#Check if type_correspodence is selected
		types_correspodence_list = []
		domain = ''
		for rec in self:
			if len(rec.type_correspodence_ids) > 0:
				rec.type_correspodence_selected = True
				for type_correspodence in rec.type_correspodence_ids:
					typecorrespodence_id = str(type_correspodence.id)
					typecorrespodence_id_list = typecorrespodence_id.split("_")
					#raise ValidationError(_( str(typecorrespodence_id_list[1]) + "==" + str(type_correspodence.id) ))
					types_correspodence_list.append(int(typecorrespodence_id_list[1]))
				#Domain for user_dsitrict_ids
				domain = {'forwarded_to_ids':  [('type_correspodence_id', 'in', types_correspodence_list)]}                
			else:
				rec.type_correspodence_selected = False        
		return {'domain': domain}

	#Compute Days Elapsed
	def _compute_days_elapsed(self):
		#Get Correspondences not closed
		correspondences_recs = self.env['blb_correspondence.all_correspondences'].search([('status', '!=', 'closed')])
		for rec in correspondences_recs:
			if rec.date_forwared_dept:
				date_forwared_dept = str(rec.date_forwared_dept)
				today = date.today()
				today_date = today.strftime("%Y-%m-%d")
				d2 = datetime.strptime(date_forwared_dept, "%Y-%m-%d").date()
				d1 = datetime.strptime(today_date, "%Y-%m-%d").date()
				rd = relativedelta(d1, d2)
				duration = int(rd.days)
				#raise ValidationError(_(duration))
				#Update Days
				rec.update({ 'days_elapsed': duration })
		#Get PPRS Requests not closed
		ppsr_requests = self.env['blb_correspondence.blb_correspondence'].search([('status', '!=', 'closed')])
		for rec in ppsr_requests:
			if rec.date_request:
				date_request = str(rec.date_request)
				today = date.today()
				today_date = today.strftime("%Y-%m-%d")
				d2 = datetime.strptime(date_request, "%Y-%m-%d").date()
				d1 = datetime.strptime(today_date, "%Y-%m-%d").date()
				rd = relativedelta(d1, d2)
				duration = int(rd.days)
				#Update Days
				rec.update({ 'days_elapsed': duration })
		#Get HRRM Requests not closed
		hrrm_requests = self.env['blb_correspondence.hrrm_correspondences'].search([('status', '!=', 'closed')])
		for rec in hrrm_requests:
			if rec.date_request:
				date_request = str(rec.date_request)
				today = date.today()
				today_date = today.strftime("%Y-%m-%d")
				d2 = datetime.strptime(date_request, "%Y-%m-%d").date()
				d1 = datetime.strptime(today_date, "%Y-%m-%d").date()
				rd = relativedelta(d1, d2)
				duration = int(rd.days)
				#Update Days
				rec.update({ 'days_elapsed': duration })
		#Get NTB Requests not closed
		ntb_requests = self.env['blb_correspondence.ntb_correspondences'].search([('status', '!=', 'closed')])
		for rec in ntb_requests:
			if rec.date_request:
				date_request = str(rec.date_request)
				today = date.today()
				today_date = today.strftime("%Y-%m-%d")
				d2 = datetime.strptime(date_request, "%Y-%m-%d").date()
				d1 = datetime.strptime(today_date, "%Y-%m-%d").date()
				rd = relativedelta(d1, d2)
				duration = int(rd.days)
				#Update Days
				rec.update({ 'days_elapsed': duration })
		#Get OPBD CA Requests not closed
		opbdca_requests = self.env['blb_correspondence.opbdca_correspondences'].search([('status', '!=', 'closed')])
		for rec in opbdca_requests:
			if rec.date_request:
				date_request = str(rec.date_request)
				today = date.today()
				today_date = today.strftime("%Y-%m-%d")
				d2 = datetime.strptime(date_request, "%Y-%m-%d").date()
				d1 = datetime.strptime(today_date, "%Y-%m-%d").date()
				rd = relativedelta(d1, d2)
				duration = int(rd.days)
				#Update Days
				rec.update({ 'days_elapsed': duration })
		#Get FAP LMIS Requests not closed
		faplmis_requests = self.env['blb_correspondence.faplmis_correspondences'].search([('status', '!=', 'closed')])
		for rec in faplmis_requests:
			if rec.date_request:
				date_request = str(rec.date_request)
				today = date.today()
				today_date = today.strftime("%Y-%m-%d")
				d2 = datetime.strptime(date_request, "%Y-%m-%d").date()
				d1 = datetime.strptime(today_date, "%Y-%m-%d").date()
				rd = relativedelta(d1, d2)
				duration = int(rd.days)
				#Update Days
				rec.update({ 'days_elapsed': duration })

	#To CEO Office 
	def action_forward_ceo(self):
		#Send SMS to Client
		user_id = '';
		client_phone = self.client_phone
		if self.client_file_no:
			sms_client = "Dear BLB Client - " + str(self.client_file_no.file_no) + ", your letter Ref No.:" + str(self.reference_no) + " has been Received. We will get in touch with you very soon! For more information contact us on 0800140140"
		else:
			sms_client = "Dear BLB Client - " + str(self.client_other) + ", your letter Ref:" + str(self.reference_no) + " has been Received. We will get in touch with you very soon! For more information contact us on 0800140140"
		self.env["blb_base.notifications"]._send_sms(user_id,client_phone,sms_client)
		#Send Email to Client
		client_email = self.client_email
		notification_subject = "Buganda Land Board Letter - " + str(self.reference_no)
		if self.client_file_no:
			notification_details = "Dear BLB Client - " + str(self.client_file_no.file_no) + ", your letter Ref No.:" + " has been Received! We will get in touch with you very soon!"
		else:
			notification_details = "Dear BLB Client - " + str(self.client_other) + ", your letter Ref No.:" + " has been Received! We will get in touch with you very soon!"
		self.env["blb_base.notifications"]._send_email(user_id,client_email,notification_subject,notification_details)
		#Send system notification - Personal Assistant - CEO
		users_rec = self.env['res.users'].search([('groups_id', '=', self.env.ref("blb_base.blb_pa_ceo").id)])
		user_rec = users_rec[0]
		user_id = user_rec.id
		user_name = user_rec.name
		notification_subject = "BLB Correspondence - " + str(self.reference_no)
		notification_details = "BLB Correspondence - " + str(self.reference_no) + " has been forwarded to the CEO for action!"
		self.env["blb_base.notifications"]._send_system_notification(user_id,notification_subject,notification_details) 
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

	#To Chair Board
	def action_forwarded_chairboard(self):
		#Send SMS to Client
		user_id = '';
		client_phone = self.client_phone
		if self.client_file_no:
			sms_client = "Dear BLB Client - " + str(self.client_file_no.file_no) + ", your letter Ref No.:" + str(self.reference_no) + " has been Received. We will get in touch with you very soon! For more information contact us on 0800140140"
		else:
			sms_client = "Dear BLB Client - " + str(self.client_other) + ", your letter Ref:" + str(self.reference_no) + " has been Received. We will get in touch with you very soon! For more information contact us on 0800140140"
		self.env["blb_base.notifications"]._send_sms(user_id,client_phone,sms_client)
		#Send Email to Client
		client_email = self.client_email
		notification_subject = "Buganda Land Board Letter - " + str(self.reference_no)
		if self.client_file_no:
			notification_details = "Dear BLB Client - " + str(self.client_file_no.file_no) + ", your letter Ref No.:" + " has been Received! We will get in touch with you very soon!"
		else:
			notification_details = "Dear BLB Client - " + str(self.client_other) + ", your letter Ref No.:" + " has been Received! We will get in touch with you very soon!"
		self.env["blb_base.notifications"]._send_email(user_id,client_email,notification_subject,notification_details)
		#Send system notification - Chair Board
		users_rec = self.env['res.users'].search([('groups_id', '=', self.env.ref("blb_base.blb_chair_board").id)])
		user_rec = users_rec[0]
		user_id = user_rec.id
		user_name = user_rec.name
		notification_subject = "BLB Correspondence - " + str(self.reference_no)
		notification_details = "BLB Correspondence - " + str(self.reference_no) + " has been forwarded to you, Chairman Board of Directors for action!"
		self.env["blb_base.notifications"]._send_system_notification(user_id,notification_subject,notification_details) 
		#Send phone notification - Chair Board
		#Get phone details
		partner_id = user_rec.partner_id
		phone_number = partner_id.phone
		self.env["blb_base.notifications"]._send_sms(user_id,phone_number,notification_details)
		#Change status
		self.write({'status': 'forwarded_chairboard'})
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

	#Get Type of Request
	def _get_type_request(self,type_correspodence,forwarded_to):
		type_request = 'OPM Request'
		dept_status = 'pending_assignment'
		request_details = {}

		if type_correspodence == 'NTB Correspondence':
			type_request = 'OPM Request'
			dept_status = 'pending_assignment'	
		elif type_correspodence == 'HRRM Correspondence':
			type_request = 'HR Request'
			dept_status = 'pending_assignment'
		elif type_correspodence == 'FAP LMIS Correspondence':
			if forwarded_to == 'Registry Manager':
				type_request = 'Registry Request'
				dept_status = 'assigned_registry'
			elif forwarded_to == 'Finance Manager':
				type_request = 'Finance Request'
				dept_status = 'assigned_finance'
			elif forwarded_to == 'Accountant':
				type_request = 'Accounts Request'
				dept_status = 'assigned_accounts'
			elif forwarded_to == 'LMIS Manager':
				type_request = 'LMIS Request'
				dept_status = 'assigned_lmis'
			elif forwarded_to == 'Estates and Procument Manager':
				type_request = 'Estates and Procument Request'
				dept_status = 'assigned_estates'
		elif type_correspodence == 'OPBD CA Correspondence':
			if forwarded_to == 'Legal Manager':
				type_request = 'Legal Request'
				dept_status = 'assigned_legal'
			elif forwarded_to == 'Corporate Affairs Manager':
				type_request = 'Corporate Affairs Request'
				dept_status = 'assigned_corporate_affairs'
			elif forwarded_to == 'Sensitization Manager':
				type_request = 'Sensitization Request'
				dept_status = 'assigned_sensitization'
			elif forwarded_to == 'Communication Manager':
				type_request = 'Communication Request'
				dept_status = 'assigned_communication'
			elif forwarded_to == 'Land Banking Manager':
				type_request = 'Land Banking Request'
				dept_status = 'assigned_land_banking'
			elif forwarded_to == 'OPM - OPBDCA':
				type_request = 'OPM Request'
				dept_status = 'assigned_opm'
		elif type_correspodence == 'PPSR Correspondence':
			if forwarded_to == 'Chief Surveyor':
				type_request = 'Survey Request'
				dept_status = 'assigned_survey'
			elif forwarded_to == 'Chief Deed Processing':
				type_request = 'Deed Processing Request'
				dept_status = 'assigned_deedprocessing'
			elif forwarded_to == 'Chief Planner':
				type_request = 'Planning Request'
				dept_status = 'assigned_planning'
			elif forwarded_to == 'Chief Valuer':
				type_request = 'Valuation Request'
				dept_status = 'assigned_valuation'
			elif forwarded_to == 'OPM - PPS':
				type_request = 'OPM Request'
				dept_status = 'assigned_opm'
		#Return dict
		request_details = {
		  "type_request": type_request,
		  "dept_status": dept_status
		}
		return request_details


	#Forward to Heads
	def action_to_unit(self):
		#Check for fields
		if self.urgency_level == False:
			raise ValidationError(_('Please select Level of Urgency!'))
		elif self.ceo_instructions == False:
			raise ValidationError(_('Please enter Instructions!'))
		elif len(self.type_correspodence_ids) < 0:
			raise ValidationError(_('Please Select Type of Correspondence!'))
		elif len(self.forwarded_to_ids) < 0:
			raise ValidationError(_('Please Select Persons Forwarded To!'))
		#Status + Department record  
		status = 'incoming_correspondence'
		if self.status == 'incoming_correspondence':
			#Send SMS to Client
			user_id = '';
			client_phone = self.client_phone
			if self.client_file_no:
				sms_client = "Dear BLB Client - " + str(self.client_file_no.file_no) + ", your letter Ref No.:" + str(self.reference_no) + " has been Received. We will get in touch with you very soon! For more information contact us on 0800140140"
			else:
				sms_client = "Dear BLB Client - " + str(self.client_other) + ", your letter Ref No.:" + str(self.reference_no) + " has been Received. We will get in touch with you very soon! For more information contact us on 0800140140"
			self.env["blb_base.notifications"]._send_sms(user_id,client_phone,sms_client)
			#Send Email to Client
			client_email = self.client_email
			notification_subject = "Buganda Land Board Letter - " + str(self.reference_no)
			if self.client_file_no:
				notification_details = "Dear BLB Client - " + str(self.client_file_no.file_no) + ", your letter Ref No.:" + str(self.reference_no) + " has been Received! We will get in touch with you very soon!"
			else:
				notification_details = "Dear BLB Client - " + str(self.client_other) + ", your letter Ref No.:" + str(self.reference_no) + " has been Received! We will get in touch with you very soon!"
			self.env["blb_base.notifications"]._send_email(user_id,client_email,notification_subject,notification_details)

			# sms_client = "Your Buganda Land Board Request - " + str(self.reference_no) + " has been Received. You will be Notified with Feedback soon!"
			# self.env["blb_base.notifications"]._send_sms(user_id,client_phone,sms_client)
			# #Send Email to Client
			# client_email = self.client_email
			# notification_subject = "Buganda Land Board Request - " + str(self.reference_no)
			# notification_details = "Your Buganda Land Board Request with Reference No.: " + str(self.reference_no) + " has been Received! You will be Notified with Feedback soon!"
			# self.env["blb_base.notifications"]._send_email(user_id,client_email,notification_subject,notification_details)

		users_recs = []
		if len(self.type_correspodence_ids) > 0 and len(self.forwarded_to_ids) < 1:
			status = 'forwarded_dept'
			type_correspodence_ids = self.type_correspodence_ids
			for type_correspodence_id in type_correspodence_ids:
				type_correspodence = type_correspodence_id.name
				if type_correspodence == 'PPSR Correspondence':
					users_rec = self.env['res.users'].search([('groups_id', '=', self.env.ref("blb_base.blb_head_pps").id)])
					users_recs.append(users_rec[0])                    
				elif type_correspodence == 'HRRM Correspondence':
					users_rec = self.env['res.users'].search([('groups_id', '=', self.env.ref("blb_base.blb_head_hrrm").id)])
					users_recs.append(users_rec[0]) 
				elif type_correspodence == 'NTB Correspondence':
					users_rec = self.env['res.users'].search([('groups_id', '=', self.env.ref("blb_base.blb_head_ntb").id)])
					users_recs.append(users_rec[0]) 
				elif type_correspodence == 'OPBD CA Correspondence':
					users_rec = self.env['res.users'].search([('groups_id', '=', self.env.ref("blb_base.blb_head_opbdca").id)])
					users_recs.append(users_rec[0]) 
				elif type_correspodence == 'FAP LMIS Correspondence':
					users_rec = self.env['res.users'].search([('groups_id', '=', self.env.ref("blb_base.blb_head_faplmis").id)])
					users_recs.append(users_rec[0]) 
				#Create Departmental Request 
				correspondence_id = self.id
				type_correspodence = type_correspodence
				type_request = 'OPM Request'
				date_correspondence = self.date_correspondence
				correspondence_description = self.correspondence_description
				ceo_instructions = self.ceo_instructions
				type_client = self.type_client
				urgency_level = self.urgency_level
				scanned_filetype = self.scanned_filetype
				correspondence = self.correspondence
				correspondence_image = self.correspondence_image
				correspondence_name = self.correspondence_name
				client_id = ''
				if self.client_file_no:
					client_id = self.client_file_no.id
				client_other = ''
				if self.client_other:
					client_other = self.client_other
				self.action_create_deparmental_request(correspondence_id,type_correspodence,type_request,date_correspondence,correspondence_description,ceo_instructions,type_client,client_id,client_other,urgency_level,scanned_filetype,correspondence,correspondence_image,correspondence_name)
		elif len(self.forwarded_to_ids) > 0:
			status = 'forwarded_dept'
			forwarded_to_ids = self.forwarded_to_ids
			for forwarded_to in forwarded_to_ids:
				type_correspodence = forwarded_to.type_correspodence_id.name
				forwarded_to = forwarded_to.name
				if type_correspodence == 'PPSR Correspondence':
					users_rec = self.env['res.users'].search([('groups_id', '=', self.env.ref("blb_base.blb_opm_pps").id)])
					users_recs.append(users_rec[0])                    
				elif type_correspodence == 'HRRM Correspondence':
					users_rec = self.env['res.users'].search([('groups_id', '=', self.env.ref("blb_base.blb_head_hrrm").id)])
					users_recs.append(users_rec[0]) 
				elif type_correspodence == 'NTB Correspondence':
					users_rec = self.env['res.users'].search([('groups_id', '=', self.env.ref("blb_base.blb_head_ntb").id)])
					users_recs.append(users_rec[0]) 
				elif type_correspodence == 'OPBD CA Correspondence':
					users_rec = self.env['res.users'].search([('groups_id', '=', self.env.ref("blb_base.blb_opm_opbdca").id)])
					users_recs.append(users_rec[0]) 
				elif type_correspodence == 'FAP LMIS Correspondence':
					users_rec = self.env['res.users'].search([('groups_id', '=', self.env.ref("blb_base.blb_head_faplmis").id)])
					users_recs.append(users_rec[0]) 
				#Create Departmental Request
				correspondence_id = self.id
				type_correspodence = type_correspodence
				#Type request + Status
				request_details = self._get_type_request(type_correspodence,forwarded_to)
				type_request = request_details["type_request"]
				dept_status = request_details["dept_status"]

				date_correspondence = self.date_correspondence
				correspondence_description = self.correspondence_description
				ceo_instructions = self.ceo_instructions
				type_client = self.type_client
				urgency_level = self.urgency_level
				scanned_filetype = self.scanned_filetype
				correspondence = self.correspondence
				correspondence_image = self.correspondence_image
				correspondence_name = self.correspondence_name
				client_id = ''
				if self.client_file_no:
					client_id = self.client_file_no.id
				client_other = ''
				if self.client_other:
					client_other = self.client_other
				self.action_create_deparmental_request(correspondence_id,type_correspodence,type_request,dept_status,date_correspondence,correspondence_description,ceo_instructions,type_client,client_id,client_other,urgency_level,scanned_filetype,correspondence,correspondence_image,correspondence_name)

		#Send system notifications to users
		#raise ValidationError(_(users_recs))
		if len(users_recs) > 0:
			for user_rec in users_recs:
				user_name = user_rec.name
				user_id = user_rec.id
				notification_subject = "BLB Correspondence - " + str(self.reference_no)
				notification_details = "BLB Correspondence - " + str(self.reference_no) + " has been forwarded to the your department for action!"
				self.env["blb_base.notifications"]._send_system_notification(user_id,notification_subject,notification_details)

		#Update Status
		today = date.today()
		self.write({'status': status, 'date_forwared_dept': today})
		#Return - Action Window
		view_id = self.env.ref('blb_correspondence.all_correspondences_list').id 
		domain = "[('status','!=','closed')]"
		context =""
		return {
			'name':'All Correspondences',
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
	def action_create_deparmental_request(self, correspondence_id,type_correspodence,type_request,dept_status,date_correspondence,correspondence_description,ceo_instructions,type_client,client_id,client_other,urgency_level,scanned_filetype,correspondence,correspondence_image,correspondence_name):
		#Using Type of Request  
		if type_correspodence == 'PPSR Correspondence':
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
				'scanned_filetype': scanned_filetype,
				'correspondence': correspondence,
				'correspondence_image': correspondence_image,
				'correspondence_name': correspondence_name,
				'urgency_level': urgency_level,
				'type_request': type_request,
				'status': dept_status
			}) #'pending_assignment'
			request_id = int(request_create.id)
			#Update Correspondence
			correspondence_rec = self.env['blb_correspondence.all_correspondences'].search([('id', '=', correspondence_id)])
			correspondence_rec.update({ 'ppsr_request_id': request_id })
		elif type_correspodence == 'HRRM Correspondence':
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
				'type_request':forwarded_to,
				'scanned_filetype': scanned_filetype,
				'correspondence': correspondence,
				'correspondence_image': correspondence_image,
				'correspondence_name': correspondence_name,
				'urgency_level': urgency_level,
				'type_request': type_request,
				'status': dept_status
			})
			request_id = int(request_create.id)
			#Update Correspondence
			correspondence_rec = self.env['blb_correspondence.all_correspondences'].search([('id', '=', correspondence_id)])
			correspondence_rec.update({ 'hrrm_request_id': request_id })
		elif type_correspodence == 'NTB Correspondence':
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
				'type_request':forwarded_to,
				'scanned_filetype': scanned_filetype,
				'correspondence': correspondence,
				'correspondence_image': correspondence_image,
				'correspondence_name': correspondence_name,
				'urgency_level': urgency_level,
				'type_request': type_request,
				'status': dept_status
			})
			request_id = int(request_create.id)
			#Update Correspondence
			correspondence_rec = self.env['blb_correspondence.all_correspondences'].search([('id', '=', correspondence_id)])
			correspondence_rec.update({ 'ntb_request_id': request_id })
		elif type_correspodence == 'OPBD CA Correspondence':
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
				'type_request':forwarded_to,
				'scanned_filetype': scanned_filetype,
				'correspondence': correspondence,
				'correspondence_image': correspondence_image,
				'correspondence_name': correspondence_name,
				'urgency_level': urgency_level,
				'type_request': type_request,
				'status': dept_status
			})
			request_id = int(request_create.id)
			#Update Correspondence
			correspondence_rec = self.env['blb_correspondence.all_correspondences'].search([('id', '=', correspondence_id)])
			correspondence_rec.update({ 'opbdca_request_id': request_id })
		elif type_correspodence == 'FAP LMIS Correspondence':
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
				'type_request':forwarded_to,
				'scanned_filetype': scanned_filetype,
				'correspondence': correspondence,
				'correspondence_image': correspondence_image,
				'correspondence_name': correspondence_name,
				'urgency_level': urgency_level,
				'type_request': type_request,
				'status': dept_status
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

	#Feedback Given - Department
	def action_dept_feedback_given(self, correspondence_id, feedback_given, date_feedback_given):
		#Get Correspondence
		correspondence_rec = self.env['blb_correspondence.all_correspondences'].search([('id', '=', correspondence_id)])
		#Send SMS to Client
		user_id = '';
		client_phone = correspondence_rec.client_phone
		if correspondence_rec.client_file_no:
			sms_client = "Dear BLB Client - " + str(correspondence_rec.client_file_no.file_no) + ", your letter/reuest Ref No.:" + str(correspondence_rec.reference_no) + " has been handled! Visti our head offices any BLB Branch to collect it. Thank you for reaching out to us. For more information contact us on 0800140140"
		else:
			sms_client = "Dear BLB Client - " + str(correspondence_rec.client_other) + ", your letter/reuest Ref No.:" + str(correspondence_rec.reference_no) + " has been handled! Visti our head offices any BLB Branch to collect it. Thank you for reaching out to us. For more information contact us on 0800140140"
		self.env["blb_base.notifications"]._send_sms(user_id,client_phone,sms_client)
		#Send Email to Client
		client_email = correspondence_rec.client_email
		notification_subject = "Feedback for Buganda Land Board Request - " + str(correspondence_rec.reference_no)
		if correspondence_rec.client_file_no:
			notification_details = "Dear BLB Client - " + str(correspondence_rec.client_file_no.file_no) + ", your letter/reuest Ref No.:" + str(correspondence_rec.reference_no) + " has been handled! Visti our head offices any BLB Branch to collect it. Thank you for reaching out to us."
		else:
			sms_client = "Dear BLB Client - " + str(correspondence_rec.client_other) + ", your letter/reuest Ref No.:" + str(correspondence_rec.reference_no) + " has been handled! Visti our head offices any BLB Branch to collect it. Thank you for reaching out to us."
		self.env["blb_base.notifications"]._send_email(user_id,client_email,notification_subject,notification_details)
		#Update Correspondence Feedback
		if self.feedback_given == False or self.feedback_given == '':
			feedback = feedback_given
		else:
			feedback = self.feedback_given + ".  " + feedback_given
		correspondence_rec.update({'feedback_given': feedback, 'date_feedback_given': date_feedback_given, 'status': 'feedback_given'})
		#return self.write({'feedback_given': feedback_given, 'date_feedback_given': date_feedback_given, 'status': 'closed'})   

	#Close
	def action_closed(self):
		#Update Client File State
		type_client = self.type_client
		if type_client == 'BLB Client':
			client_id = self.client_file_no.id
			client_rec = self.env['blb_client.blb_client'].search([('id', '=', client_id)])
			if client_rec:
				client_rec.update({'state': 'blbregistry'})
		#Close Correspondence
		self.write({'status': 'closed'})

	#Send notification
	def _notify_client_management(self, reference_no):
		#Send system notification - Client Mgt
		user_recs = self.env['res.users'].search([('groups_id', '=', self.env.ref("blb_base.blb_customercare_user").id)])
		for user_rec in user_recs:
			user_id = user_rec.id
			user_name = user_rec.name
			notification_subject = "BLB Correspondence - " + str(reference_no)
			notification_details = "BLB Correspondence - " + str(reference_no) + " from Branch has been created/forwarded for your Action!"
			self.env["blb_base.notifications"]._send_system_notification(user_id,notification_subject,notification_details)

	#Put together the Reference No Sequence
	@api.model
	def create(self, vals):
		#Sequence
		seq = self.env['ir.sequence'].next_by_code('reference_no_sequence')
		vals['reference_no'] = seq
		#Check if Branch User created Correspondence
		if self.env.user.has_group ('blb_base.blb_branch_user'):
			#Notify Client Mgt
			reference_no = seq
			self._notify_client_management(reference_no)
		#Update Client File State
		type_client = vals['type_client']
		if type_client == 'BLB Client':
			client_id = vals['client_file_no']
			client_rec = self.env['blb_client.blb_client'].search([('id', '=', client_id)])
			if client_rec:
				client_rec.update({'state': 'with_correspondence'})
		res = super(all_correspondences, self).create(vals)
		return res


class ceo_remarks(models.Model):
	_name = 'blb_correspondence.ceo_remarks'
	_description = 'BLB - Correspondences CEO Remarks'
	_inherit = ['mail.thread', 'mail.activity.mixin']
	_order = 'name desc'

	name = fields.Char(string="Remark", required=True) 

	_sql_constraints = [
		('name',
		 'UNIQUE(name)',
		 "The Remark should be Unique!")
	]


class type_correspodence(models.Model):
	_name = 'blb_correspondence.type_correspodence'
	_description = 'BLB - Type of Correspondence'
	_inherit = ['mail.thread', 'mail.activity.mixin']
	_order = 'name desc'

	name = fields.Char(string="Type of Correspondence", required=True) 

	_sql_constraints = [
		('name',
		 'UNIQUE(name)',
		 "The Type of Correspondence should be Unique!")
	]


class forwarded_to(models.Model):
	_name = 'blb_correspondence.forwarded_to'
	_description = 'BLB - Correspondence Forwarded To'
	_inherit = ['mail.thread', 'mail.activity.mixin']
	_order = 'name desc'

	type_correspodence_id = fields.Many2one('blb_correspondence.type_correspodence', string='Type of Correspondence', required=True)
	name = fields.Char(string="Forwaded To", required=True) 

	_sql_constraints = [
		('name',
		 'UNIQUE(name)',
		 "The Person Forwaded To should be Unique!")
	]






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
	_description = 'BLB - PPSR Correspondences'
	_inherit = ['mail.thread', 'mail.activity.mixin']
	_order = 'date_request desc'

	name = fields.Char(string="Name", compute="_compute_name", store=True) 
	correspondence_id = fields.Many2one('blb_correspondence.all_correspondences', string='Correspodence ID', ondelete='cascade')
	date_request = fields.Date(string="Date Request", required=True)
	days_elapsed = fields.Integer(string="Days Elapsed", readonly=True)
	type_client = fields.Selection([
		('BLB Client', 'BLB Client'),
		('Other', 'Other'),
		], string='Is a BLB Client?', required=True)
	client_file_no = fields.Many2one('blb_client.blb_client', string='Client/File No.', ondelete='cascade')
	client_other = fields.Char(string="Author From")
	type_request = fields.Selection([
		('OPM Request', 'OPM Request'),
		('Survey Request', 'Survey Request'),
		('Deed Processing Request', 'Deed Processing Request'),
		('Planning Request', 'Planning Request'),
		('Valuation Request', 'Valuation Request'),
		('Enforcer Request', 'Enforcer Request'),
		('Research Request', 'Research Request'),
		], string='Type of Request') #, required=True
	status = fields.Selection([
		('pending_assignment', 'Incoming'),
		('assigned_opm', 'Assigned to OPM'),
		('assigned_survey', 'Assigned to Survey Unit'),
		('assigned_surveyor', 'Assigned to Surveyor'),
		('assigned_deedprocessing', 'Assigned to Deed Processing Unit'),
		('assigned_deedprocessingofficer', 'Assigned to Deed Processing Officer'),
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
	ceo_instructions = fields.Text(string="Instructions", readonly=True)
	scanned_filetype= fields.Selection([
		('Image', 'Image'),
		('PDF', 'PDF'),
		], string='Scanned File Type?', readonly=True)
	correspondence = fields.Binary(string='PDF Scan', readonly=True)
	correspondence_image = fields.Binary(string='Image Scan', readonly=True)  
	correspondence_name = fields.Char(string="Scanned Correspondence - Name")
	remarks = fields.Text(string="Head Of Department Instructions")
	urgency_level = fields.Selection([('Urgent', 'Urgent'), ('Normal', 'Normal')], string='Level of Urgency', required=True)
	client_contact = fields.Char(string="Client Contact Details")
	date_fees_paid = fields.Date(string="Date Fees Paid", default=fields.Date.today)

	allocated_to = fields.Many2one('res.users', string='Allocated to', ondelete='cascade')
	date_allocated = fields.Date(string="Date Allocated", default=fields.Date.today, readonly=True)
	report = fields.Binary(string='Report')
	report_name = fields.Char(string="Report Name")
	report_remarks = fields.Text(string="Remarks") 
	done_by = fields.Many2one('res.users', string='Feedback given by', readonly=True, default=lambda self: self.env.user, ondelete='cascade')
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
		elif self.type_request == 'Deed Processing Request':
			status = 'assigned_deedprocessing'
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

	 #To Deed Processing 
	def action_assigned_deedprocessing(self):
		#raise ValidationError(_(self.allocated_to.id))     
		if self.allocated_to.id == False or self.allocated_to.id == '':
			raise ValidationError(_('Please select Deed Processing Officer!'))
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
		self.write({'date_allocated': today, 'status': 'assigned_deedprocessingofficer'})
		#Return - Action Window
		view_id = self.env.ref('blb_correspondence.blb_correspondence_list').id 
		domain = "[('type_request','=','Deed Processing Request')]"
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
			self.env["blb_correspondence.all_correspondences"].action_dept_feedback_given(correspondence_id, feedback_given, date_feedback_given)
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
	correspondence_id = fields.Many2one('blb_correspondence.all_correspondences', string='Correspodence ID', ondelete='cascade')
	date_request = fields.Date(string="Date Request", required=True)
	days_elapsed = fields.Integer(string="Days Elapsed", readonly=True)
	type_client = fields.Selection([
		('BLB Client', 'BLB Client'),
		('Other', 'Other'),
		], string='Is a BLB Client?', required=True)
	client_file_no = fields.Many2one('blb_client.blb_client', string='Client/File No.', ondelete='cascade')
	client_other = fields.Char(string="Author From")
	type_request = fields.Selection([
		('OPM Request', 'OPM Request'),
		('HR Request', 'HR Request'),
		], string='Type of Request')  #, required=True
	status = fields.Selection([
		('pending_assignment', 'Incoming'),
		('assigned_hr', 'Assigned to HR'),
		('feedback_given', 'Feedback Given'),
		('closed', 'Closed'),
		], string='Status', readonly=True, copy=False, index=True, track_visibility='onchange', default='pending_assignment')
	urgency_level = fields.Selection([('Urgent', 'Urgent'), ('Normal', 'Normal')], string='Level of Urgency', required=True)
	request = fields.Text(string="Request Description") #, required=True
	ceo_instructions = fields.Text(string="Instructions", readonly=True)
	scanned_filetype= fields.Selection([
		('Image', 'Image'),
		('PDF', 'PDF'),
		], string='Scanned File Type?', readonly=True)
	correspondence = fields.Binary(string='PDF Scan', readonly=True)
	correspondence_image = fields.Binary(string='Image Scan', readonly=True)
	correspondence_name = fields.Char(string="Scanned Correspondence - Name")

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

	#assigned_hr
	def action_to_unit(self):
		status = 'pending_assignment'
		if self.type_request == 'HR Request':
			status = 'assigned_hr'        
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
		if self.env.user.has_group ('blb_base.blb_head_hrrm'):
			#Update Correspondence and Inform Client
			correspondence_id = self.correspondence_id.id
			feedback_given = self.report_remarks
			date_feedback_given = self.date_done
			self.env["blb_correspondence.all_correspondences"].action_dept_feedback_given(correspondence_id, feedback_given, date_feedback_given)
			#Close PPSR Request
			self.write({'status': 'closed'})
		else:
			raise ValidationError(_('You do not have permission to Close this Corresponse. Contact your Head!'))
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
	correspondence_id = fields.Many2one('blb_correspondence.all_correspondences', string='Correspodence ID', ondelete='cascade')
	date_request = fields.Date(string="Date Request", required=True)
	days_elapsed = fields.Integer(string="Days Elapsed", readonly=True)
	type_client = fields.Selection([
		('BLB Client', 'BLB Client'),
		('Other', 'Other'),
		], string='Is a BLB Client?', required=True)
	client_file_no = fields.Many2one('blb_client.blb_client', string='Client/File No.', ondelete='cascade')
	client_other = fields.Char(string="Author From")
	type_request = fields.Selection([
		('OPM Request', 'OPM Request'),
		], string='Type of Request')  #, required=True
	status = fields.Selection([
		('pending_assignment', 'Incoming'),
		('assigned_opm', 'Assigned to OPM'),
		('feedback_given', 'Feedback Given'),
		('closed', 'Closed'),
		], string='Status', readonly=True, copy=False, index=True, track_visibility='onchange', default='pending_assignment')
	urgency_level = fields.Selection([('Urgent', 'Urgent'), ('Normal', 'Normal')], string='Level of Urgency', required=True)
	request = fields.Text(string="Request Description") #, required=True
	ceo_instructions = fields.Text(string="Instructions", readonly=True)
	scanned_filetype= fields.Selection([
		('Image', 'Image'),
		('PDF', 'PDF'),
		], string='Scanned File Type?', readonly=True)
	correspondence = fields.Binary(string='PDF Scan', readonly=True)
	correspondence_image = fields.Binary(string='Image Scan', readonly=True)
	correspondence_name = fields.Char(string="Scanned Correspondence - Name")

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
			self.env["blb_correspondence.all_correspondences"].action_dept_feedback_given(correspondence_id, feedback_given, date_feedback_given)
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
	correspondence_id = fields.Many2one('blb_correspondence.all_correspondences', string='Correspodence ID', ondelete='cascade')
	date_request = fields.Date(string="Date Request", required=True)
	days_elapsed = fields.Integer(string="Days Elapsed", readonly=True)
	type_client = fields.Selection([
		('BLB Client', 'BLB Client'),
		('Other', 'Other'),
		], string='Is a BLB Client?', required=True)
	client_file_no = fields.Many2one('blb_client.blb_client', string='Client/File No.', ondelete='cascade')
	client_other = fields.Char(string="Author From")
	type_request = fields.Selection([
		('OPM Request', 'OPM Request'),
		('Legal Request', 'Legal Request'),
		('Lease Request', 'Lease Request'),
		('Sensitization Request', 'Sensitization Request'),
		('Branch Request', 'Branch Request'),
		('Communication Request', 'Communication Request'),
		('Land Banking Request', 'Land Banking Request'),
		('Corporate Affairs Request', 'Corporate Affairs Request'),
		], string='Type of Request')   #, required=True
	status = fields.Selection([
		('pending_assignment', 'Incoming'),
		('assigned_opm', 'Assigned to OPM'),
		('assigned_lease', 'Assigned to Lease Manager'),
		('assigned_legal', 'Assigned to Legal'),
		('assigned_legal_officer', 'Assigned to Legal Officer'),
		('assigned_branch', 'Assigned to Branch'),
		('assigned_sensitization', 'Assigned to Sensitization'),		
		('assigned_communication', 'Assigned to Communication'),
		('assigned_land_banking', 'Assigned to Land Banking'),
		('assigned_corporate_affairs', 'Assigned to Corporate Affairs'),
		('feedback_given', 'Feedback Given'),
		('closed', 'Closed'),
		], string='Status', readonly=True, copy=False, index=True, track_visibility='onchange', default='pending_assignment')
	urgency_level = fields.Selection([('Urgent', 'Urgent'), ('Normal', 'Normal')], string='Level of Urgency', required=True)
	request = fields.Text(string="Request Description")   #, required=True
	ceo_instructions = fields.Text(string="Instructions", readonly=True)
	scanned_filetype= fields.Selection([
		('Image', 'Image'),
		('PDF', 'PDF'),
		], string='Scanned File Type?', readonly=True)
	correspondence = fields.Binary(string='PDF Scan', readonly=True)
	correspondence_image = fields.Binary(string='Image Scan', readonly=True)
	correspondence_name = fields.Char(string="Scanned Correspondence - Name")

	remarks = fields.Text(string="Head Of Department Instructions")
	allocated_to = fields.Many2one('res.users', string='Allocated to', ondelete='cascade')
	date_allocated = fields.Date(string="Date Allocated", default=fields.Date.today, readonly=True)
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
		users_rec = []
		if self.type_request == 'OPM Request':
			status = 'assigned_opm'
		elif self.type_request == 'Legal Request':
			status = 'assigned_legal'
			users_rec = self.env['res.users'].search([('groups_id', '=', self.env.ref("blb_base.blb_head_legal").id)])
		elif self.type_request == 'Lease Request':
			status = 'assigned_lease'
			users_rec = self.env['res.users'].search([('groups_id', '=', self.env.ref("blb_base.blb_lease_manager").id)])
		elif self.type_request == 'Sensitization Request':
			status = 'assigned_sensitization'
			users_rec = self.env['res.users'].search([('groups_id', '=', self.env.ref("blb_base.blb_head_sensitisation").id)])
		elif self.type_request == 'Branch Request':
			status = 'assigned_branch'
		elif self.type_request == 'Communication Request':
			status = 'assigned_communication'
			users_rec = self.env['res.users'].search([('groups_id', '=', self.env.ref("blb_base.blb_head_communications").id)])
		elif self.type_request == 'Land Banking Request':
			status = 'assigned_land_banking'
			users_rec = self.env['res.users'].search([('groups_id', '=', self.env.ref("blb_base.blb_head_land_banking").id)])
		elif self.type_request == 'Corporate Affairs Request':
			status = 'assigned_corporate_affairs'
			users_rec = self.env['res.users'].search([('groups_id', '=', self.env.ref("blb_base.blb_head_corporate_affairs").id)])

		#Check of requirements
		if self.remarks == False:
			raise ValidationError(_('Please enter the Remarks/Instructions!'))
		#Send system notification - Head
		if len(users_rec) > 0:
			user_rec = users_rec[0]
			user_id = user_rec.id
			user_name = user_rec.name       
			notification_subject = "Correspondence Allocation"
			notification_details = "You have been allocated a Correspondence: " + str(self.name)
			self.env["blb_base.notifications"]._send_system_notification(user_id,notification_subject,notification_details)

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

	#To Branch
	def action_assigned_branch(self):
		#raise ValidationError(_(self.allocated_to.id))     
		if self.allocated_to.id == False or self.allocated_to.id == '':
			raise ValidationError(_('Please select Branch Manager/Officer Allocated!'))
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
		self.write({'date_allocated': today, 'status': 'assigned_branch'})
		#Return - Action Window
		view_id = self.env.ref('blb_correspondence.opbdca_correspondences_list').id 
		domain = "[('type_request','=','Branch Request')]"
		context =""
		return {
			'name':'Branch Requests',
			'view_type':'form',
			'view_mode':'tree,form',
			'res_model':'blb_correspondence.opbdca_correspondences',
			'view_id': False,
			'type':'ir.actions.act_window',
			'target':'current',
			'context':context,
			'domain': domain
		}

	#To Legal Officer
	def action_assigned_legal_officer(self):
		#raise ValidationError(_(self.allocated_to.id))     
		if self.allocated_to.id == False or self.allocated_to.id == '':
			raise ValidationError(_('Please select Legal Officer!'))
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
		self.write({'date_allocated': today, 'status': 'assigned_legal_officer'})
		#Return - Action Window
		view_id = self.env.ref('blb_correspondence.opbdca_correspondences_list').id 
		domain = "[('type_request','=','Legal Request')]"
		context =""
		return {
			'name':'Legal Requests',
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
			self.env["blb_correspondence.all_correspondences"].action_dept_feedback_given(correspondence_id, feedback_given, date_feedback_given)
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
	correspondence_id = fields.Many2one('blb_correspondence.all_correspondences', string='Correspodence ID', ondelete='cascade')
	date_request = fields.Date(string="Date Request", required=True)
	days_elapsed = fields.Integer(string="Days Elapsed", readonly=True)
	type_client = fields.Selection([
		('BLB Client', 'BLB Client'),
		('Other', 'Other'),
		], string='Is a BLB Client?', required=True)
	client_file_no = fields.Many2one('blb_client.blb_client', string='Client/File No.', ondelete='cascade')
	client_other = fields.Char(string="Author From")
	type_request = fields.Selection([
		('OPM Request', 'OPM Request'),
		('Registry Request', 'Registry Request'),
		('Finance Request', 'Finance Request'),
		('Accounts Request', 'Accounts Request'),
		('LMIS Request', 'LMIS Request'),
		('Estates and Procument Request', 'Estates and Procument Request'),
		], string='Type of Request')   #, required=True
	status = fields.Selection([
		('pending_assignment', 'Incoming'),
		('assigned_registry', 'Assigned to Registry'),
		('assigned_finance', 'Assigned to Finance'),
		('assigned_accounts', 'Assigned to Accounts'),
		('assigned_lmis', 'Assigned to LMIS'),
		('assigned_estates', 'Assigned to Estates and Procument'),
		('feedback_given', 'Feedback Given'),
		('closed', 'Closed'),
		], string='Status', readonly=True, copy=False, index=True, track_visibility='onchange', default='pending_assignment')
	urgency_level = fields.Selection([('Urgent', 'Urgent'), ('Normal', 'Normal')], string='Level of Urgency', required=True)
	request = fields.Text(string="Request Description")  #, required=True
	ceo_instructions = fields.Text(string="Instructions", readonly=True)
	scanned_filetype= fields.Selection([
		('Image', 'Image'),
		('PDF', 'PDF'),
		], string='Scanned File Type?', readonly=True)
	correspondence = fields.Binary(string='PDF Scan', readonly=True)
	correspondence_image = fields.Binary(string='Image Scan', readonly=True)
	correspondence_name = fields.Char(string="Scanned Correspondence - Name")

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

	#assigned
	def action_to_unit(self):
		status = 'pending_assignment'
		users_rec = []
		if self.type_request == 'Registry Request':
			status = 'assigned_registry'
			users_rec = self.env['res.users'].search([('groups_id', '=', self.env.ref("blb_base.blb_head_registry").id)])
		elif self.type_request == 'Finance Request':
			status = 'assigned_finance'
			users_rec = self.env['res.users'].search([('groups_id', '=', self.env.ref("blb_base.blb_finance").id)])
		elif self.type_request == 'Accounts Request':
			status = 'assigned_accounts'
			users_rec = self.env['res.users'].search([('groups_id', '=', self.env.ref("blb_base.blb_accounts").id)])
		elif self.type_request == 'LMIS Request':
			status = 'assigned_lmis'   
			users_rec = self.env['res.users'].search([('groups_id', '=', self.env.ref("blb_base.blb_head_lmis_ict").id)])
		elif self.type_request == 'Estates and Procument Request':
			status = 'assigned_estates'  
			users_rec = self.env['res.users'].search([('groups_id', '=', self.env.ref("blb_base.blb_estates_procurement").id)])
		
		#Check of requirements
		if self.remarks == False:
			raise ValidationError(_('Please enter the Remarks/Instructions!'))
		#Send system notification - Head
		if len(users_rec) > 0:
			user_rec = users_rec[0]
			user_id = user_rec.id
			user_name = user_rec.name       
			notification_subject = "Correspondence Allocation"
			notification_details = "You have been allocated a Correspondence: " + str(self.name)
			self.env["blb_base.notifications"]._send_system_notification(user_id,notification_subject,notification_details)

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
		if self.env.user.has_group ('blb_base.blb_head_faplmis'):
			#Update Correspondence and Inform Client
			correspondence_id = self.correspondence_id.id
			feedback_given = self.report_remarks
			date_feedback_given = self.date_done
			self.env["blb_correspondence.all_correspondences"].action_dept_feedback_given(correspondence_id, feedback_given, date_feedback_given)
			#Close PPSR Request
			self.write({'status': 'closed'})
		else:
			raise ValidationError(_('You do not have permission to Close this Corresponse. Contact your Head!'))
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










