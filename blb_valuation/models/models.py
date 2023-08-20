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
	value = fields.Integer(string='Value')
	description = fields.Text(string='Description')


class demand_note(models.Model):
	_name = 'blb_valuation.demand_note'
	_description = 'BLB Valuation - Demand Notes'
	_inherit = ['mail.thread', 'mail.activity.mixin']
	_order = 'status desc'

	file_no = fields.Many2one('blb_client.blb_client', string='Client', required=True, ondelete='cascade')
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
	currency_id = fields.Many2one('res.currency', 'Currency', required=True, ondelete='cascade', default=lambda self: self.env.user.company_id.currency_id.id)
	date_effective = fields.Date(string="Date Effective", default=fields.Date.today)
	remarks = fields.Text(string="Remarks") 
	revised_by = fields.Many2one('res.users', string='Revised by', store=True, readonly=True, ondelete='cascade')

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
	_inherit = ['mail.thread', 'mail.activity.mixin']
	_order = 'status desc'

	file_no = fields.Many2one('blb_client.blb_client', string='Client', required=True, ondelete='cascade')
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
	assessed_by = fields.Many2one('res.users', string='Assessed by', store=True, readonly=True, ondelete='cascade')

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

	file_no = fields.Many2one('blb_client.blb_client', string='Client', required=True, ondelete='cascade')
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
	assessed_by = fields.Many2one('res.users', string='Assessed by', store=True, readonly=True, ondelete='cascade')
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



##################################################################################################################################
## ***
## ***  Ground Rent Revision
## ***
##################################################################################################################################

class groundrent_revision(models.Model):
	_name = 'blb_valuation.groundrent_revision'
	_description = 'BLB - Ground Rent Revision'
	_inherit = ['mail.thread', 'mail.activity.mixin']
	_order = 'client_no asc'

	name = fields.Char(string="Ground Rent Revision", readonly=True, compute="_compute_name", store=True)
	client_no = fields.Many2one('blb_client.blb_client', string='Client', required=True, ondelete='cascade')
	client_phone = fields.Char(string="Phone Number")
	date_lease_start = fields.Date(string="Lease Date Start", required=True, default=fields.Date.today)
	revision_term = fields.Selection([
		('5', '5'),
		('10', '10'),
		], string='Revision Term (Years)', required=True, default='5')
	revision_percentage = fields.Selection([
		('10', '10'),
		('20', '20'),
		], string='Revision Percentage (%)', required=True, default='10')
	status = fields.Selection([
		('pending_confirmation', 'Revision Pending Confirmation'),
		('revised', 'Revised'),
		('closed', 'Closed'),
		], string='Status', readonly=True, copy=False, index=True, track_visibility='onchange', default='pending_confirmation') #, default='closed'
	previous_ground_rent = fields.Monetary(string="Previous Ground Rent")
	current_ground_rent = fields.Monetary(string="Current Ground Rent", required=True)
	date_last_revision = fields.Date(string="Last Revision Date", required=True)
	date_last_payment = fields.Date(string="Last Date of Payment", required=True)
	date_next_revision = fields.Date(string="Next Revision Date", compute="_compute_next_revision_date", store=True)
	currency_id = fields.Many2one('res.currency', 'Currency', readonly=True, required=True, default=lambda self: self.env.user.company_id.currency_id.id)
	head_pps = fields.Many2one('res.users', string='Head PPS&R', compute="_compute_head_ppsr", store=True)
	revision_line_ids = fields.One2many('blb_valuation.groundrent_revision_lines', 'groundrent_revision_id', string='Revision Lines')

	_sql_constraints = [
		('client_no',
		 'UNIQUE(client_no)',
		 "The Client File No. should be Unique!")
	]

	#Compute Name
	@api.depends('client_no')
	def _compute_name(self):
		the_name = ""    
		for rec in self:
			if rec.client_no:
				the_name = str(rec.client_no.name)
			rec.name = the_name
		return the_name

	#Compute Name
	@api.depends('client_no')
	def _compute_head_ppsr(self):
		userid = 0    
		for rec in self:
			if rec.client_no:
				users_rec = self.env['res.users'].search([('groups_id', '=', self.env.ref("blb_base.blb_head_pps").id)])
				if users_rec:
					user_details = users_rec[0]
					userid = user_details.id
			rec.head_pps = userid
		return userid

	#Onchange client_no
	@api.onchange('client_no')
	def _onchange_client_no(self):
		for rec in self:			
			if rec.client_no:
				rec.client_phone = rec.client_no.contact_details

	#Compute Next Revision Date
	# @api.depends('date_last_payment')
	# def _compute_next_revision_date(self):
	# 	next_date = ''
	# 	for rec in self:
	# 		if rec.date_last_payment:
	# 			date_revision = rec.date_last_payment
	# 			term = int(rec.revision_term)
	# 			#Get Date Next Revision
	# 			the_date = datetime.strptime(str(date_revision), '%Y-%m-%d')
	# 			next_date = the_date + relativedelta(years=term)  
	# 		rec.date_next_revision = next_date
	# 	return next_date

	#Check Date last
	@api.onchange('date_last_payment')
	def _onchange_date_last_payment(self):
		for rec in self:			
			if len(rec.revision_line_ids) > 0:
				rec.write({'revision_line_ids': [(5, 0, 0)]})
				#raise ValidationError(_( len(rec.revision_line_ids) ))
			if rec.date_last_payment and rec.revision_term and rec.revision_percentage and rec.current_ground_rent:
				#Today - check if next revision is in future - and rec.date_next_revision
				revision_lines = []				
				today = date.today()
				today_date = today.strftime("%Y-%m-%d") 
				today_date = datetime.strptime(today_date, "%Y-%m-%d").date()

				term = int(rec.revision_term)
				percentage = (int(rec.revision_percentage) / 100)
				date_next = rec.date_last_payment
				date_next2 = datetime.strptime(str(date_next), "%Y-%m-%d").date()

				while(date_next2 < today_date):
					#Put together the new_ground_rent and Get Date Next Revision
					new_ground_rent = (rec.current_ground_rent * percentage) + rec.current_ground_rent					
					the_date = date_next.strftime("%Y-%m-%d")
					the_date = datetime.strptime(str(the_date), '%Y-%m-%d')
					new_date_next = the_date + relativedelta(years=term)
					#Create Revision Line
					revision_line = (0, 0, {'date_revision': date_next,
											'date_next_revision': new_date_next,
											'ground_rent': new_ground_rent
											})
					revision_lines.append(revision_line)
					#Update Record Date Last is the last date_next
					rec.previous_ground_rent = rec.current_ground_rent
					rec.current_ground_rent = new_ground_rent
					rec.date_last_revision = date_next
					rec.date_next_revision = new_date_next
					date_next = new_date_next
					date_next2 = date_next.strftime("%Y-%m-%d")
					date_next2 = datetime.strptime(str(date_next2), "%Y-%m-%d").date()
				#Next Revision date
				#rec.date_next_revision = date_next2
				rec.revision_line_ids = revision_lines


	#Do Revision ******************************************************
	def action_do_revision(self):
		for rec in self:
			#Get last revision
			groundrent_revision_id = rec.id
			revision_line = self.env['blb_valuation.groundrent_revision_lines'].search([('groundrent_revision_id', '=', groundrent_revision_id)], order="id desc", limit=1)  #date_next_revision desc
			if revision_line:
				term = int(rec.revision_term)
				percentage = (int(rec.revision_percentage) / 100)
				date_revision = revision_line.date_next_revision
				new_ground_rent = (revision_line.ground_rent * percentage) + revision_line.ground_rent
				#Get Date Next Revision
				the_date = datetime.strptime(str(date_revision), '%Y-%m-%d')
				next_date = the_date + relativedelta(years=term)                
				rec.update({
					'previous_ground_rent': ground_rent,
					'current_ground_rent': new_ground_rent,
					'date_last_revision': date_revision,
					'date_next_revision': next_date
				})
				#Create Revision Line
				rec_create = self.env['blb_valuation.groundrent_revision_lines'].create({
					'date_revision': date_revision,
					'date_next_revision': next_date,
					'ground_rent': new_ground_rent,
					'groundrent_revision_id': groundrent_revision_id,
				})
			else:
				term = int(rec.revision_term)
				percentage = (int(rec.revision_percentage) / 100)
				date_revision = rec.date_next_revision
				new_ground_rent = (rec.current_ground_rent * percentage) + rec.current_ground_rent
				#Get Date Next Revision
				the_date = datetime.strptime(str(date_revision), '%Y-%m-%d')
				next_date = the_date + relativedelta(years=term)                
				rec.update({
					'previous_ground_rent': current_ground_rent,
					'current_ground_rent': new_ground_rent,
					'date_last_revision': date_revision,
					'date_next_revision': next_date
				})
				#Create Revision Line
				rec_create = self.env['blb_valuation.groundrent_revision_lines'].create({
					'date_revision': date_revision,
					'date_next_revision': next_date,
					'ground_rent': new_ground_rent,
					'groundrent_revision_id': groundrent_revision_id
				})
		#Change Status
		self.write({'status': 'pending_confirmation'})


	#Revise Ground Rent
	def action_revise_groundrent(self):
		#Get All Records - due for Ground Rent Revision Today
		today = date.today()
		revision_recs = self.env['blb_valuation.groundrent_revision'].search([('date_next_revision', '<=', today),('status', '=' ,'closed')])
		for rec in revision_recs:
			#Get last revision
			groundrent_revision_id = rec.id
			revision_line = self.env['blb_valuation.groundrent_revision_lines'].search([('groundrent_revision_id', '=', groundrent_revision_id)], order="id desc", limit=1)  #date_next_revision desc
			if revision_line:
				term = int(rec.revision_term)
				percentage = (int(rec.revision_percentage) / 100)
				date_revision = revision_line.date_next_revision
				new_ground_rent = (revision_line.ground_rent * percentage) + revision_line.ground_rent
				#Get Date Next Revision
				the_date = datetime.strptime(str(date_revision), '%Y-%m-%d')
				next_date = the_date + relativedelta(years=term)                
				rec.update({
					'previous_ground_rent': ground_rent,
					'current_ground_rent': new_ground_rent,
					'date_last_revision': date_revision,
					'date_next_revision': next_date,
					'status': 'pending_confirmation'
				})
				#Create Revision Line
				rec_create = self.env['blb_valuation.groundrent_revision_lines'].create({
					'date_revision': date_revision,
					'date_next_revision': next_date,
					'ground_rent': new_ground_rent,
					'groundrent_revision_id': groundrent_revision_id
				})
			else:
				term = int(rec.revision_term)
				percentage = (int(rec.revision_percentage) / 100)
				date_revision = rec.date_next_revision
				new_ground_rent = (rec.current_ground_rent * percentage) + rec.current_ground_rent
				#Get Date Next Revision
				the_date = datetime.strptime(str(date_revision), '%Y-%m-%d')
				next_date = the_date + relativedelta(years=term)                
				rec.update({
					'previous_ground_rent': current_ground_rent,
					'current_ground_rent': new_ground_rent,
					'date_last_revision': date_revision,
					'date_next_revision': next_date,
					'status': 'pending_confirmation'
				})
				#Create Revision Line
				rec_create = self.env['blb_valuation.groundrent_revision_lines'].create({
					'date_revision': date_revision,
					'date_next_revision': next_date,
					'ground_rent': new_ground_rent,
					'groundrent_revision_id': groundrent_revision_id
				})

	#revised
	def action_to_revised(self):
		status = 'revised'
		self.write({'status': status})
		#Return - Action Window
		view_id = self.env.ref('blb_valuation.groundrent_revision_list').id 
		domain = "[('status','=','pending_confirmation')]"
		context =""
		return {
			'name':'BLB Valuation - Ground Rent Revision',
			'view_type':'form',
			'view_mode':'tree,form',
			'res_model':'blb_valuation.groundrent_revision',
			'view_id': False,
			'type':'ir.actions.act_window',
			'target':'current',
			'context':context,
			'domain': domain
		}

	#ICT or LIMS office closes
	def action_close(self):
		#Check User Rights
		userid = self.env.uid
		user_rec = self.env['res.users'].search([('id', '=', userid)])
		if not self.env.user.has_group ('blb_base.blb_lmis_ict'):
			ValidationError(_('You do not have permission to Close this Revision. Contact the Head LMIS/ICT!'))
		#Client Notifications   
		from_date = datetime.strptime(str(self.date_last_revision), '%Y-%m-%d') 
		from_date = from_date.strftime("%d/%b/%Y")
		to_date = datetime.strptime(str(self.date_next_revision), '%Y-%m-%d')
		to_date = to_date.strftime("%d/%b/%Y")
		#Send SMS to Client
		client_phone = self.client_phone
		sms_client = "Dear esteemed BLB Client " + str(client_no.file_no) + ", your Ground Rent has been revised from " + str(self.previous_ground_rent) + " to " + str(self.current_ground_rent) + " effective " + str(from_date) + " to " + str(to_date) + ". Thank you for your continued compliance."
		self.env["blb_base.notifications"]._send_sms(userid,client_phone,sms_client)
		#Send Email to Client
		client_email = self.client_no.contact_email
		notification_subject = "Buganda Land Board Ground Rent Revision - " + str(self.client_no)
		notification_details = "Dear esteemed BLB Client " + str(client_no.file_no) + ", your Ground Rent has been revised from " + str(self.previous_ground_rent) + " to " + str(self.current_ground_rent) + " effective " + str(from_date) + " to " + str(to_date) + ". Thank you for your continued compliance."
		self.env["blb_base.notifications"]._send_email(userid,client_email,notification_subject,notification_details)
		#Change status
		self.write({'status': 'closed'})
		#Return - Action Window
		view_id = self.env.ref('blb_valuation.groundrent_revision_list').id 
		domain = "[('status','=','revised')]"
		context =""
		return {
			'name':'BLB Valuation - Ground Rent Revision',
			'view_type':'form',
			'view_mode':'tree,form',
			'res_model':'blb_valuation.groundrent_revision',
			'view_id': False,
			'type':'ir.actions.act_window',
			'target':'current',
			'context':context,
			'domain': domain
		}


class groundrent_revision_lines(models.Model):
	_name = 'blb_valuation.groundrent_revision_lines'
	_description = 'BLB - Ground Rent Revision Lines'
	_inherit = ['mail.thread', 'mail.activity.mixin']
	_order = 'date_revision asc'
	_rec_name = 'date_revision'
	
	date_revision = fields.Date(string="Date of Revision", required=True)
	date_next_revision = fields.Date(string="Next Revision Date", required=True)
	ground_rent = fields.Monetary(string="Ground Rent", required=True)
	currency_id = fields.Many2one('res.currency', 'Currency', readonly=True, required=True, default=lambda self: self.env.user.company_id.currency_id.id)
	groundrent_revision_id = fields.Many2one('blb_valuation.groundrent_revision', string='Ground Rent Revision')





##################################################################################################################################
## ***
## ***  Valuation Calculator
## ***
##################################################################################################################################

class valuation_calculator(models.Model):
	_name = 'blb_valuation.valuation_calculator'
	_description = 'BLB Valuation - Valuation Calculator'
	_inherit = ['mail.thread', 'mail.activity.mixin']
	_order = 'name asc'

	name = fields.Char(string="Valuation Assessment", readonly=True, compute="_compute_name", store=True)
	date_assessment = fields.Char(string="Date Assessment", readonly=True, compute="_compute_date", store=True)
	client_no = fields.Many2one('blb_client.blb_client', string='Client', required=True, ondelete='cascade')
	location = fields.Char(string="Location", required=True)
	block_no = fields.Char(string="Block No.")
	plot_no = fields.Char(string="Plot No.")
	area_estimate_hectares = fields.Float(string="Estimate Hectares", required=True)
	area_estimate_acres = fields.Float(string="Estimate Acres", required=True)
	lease_term = fields.Selection([
		('49', '49 Year Lease'),
		('99', '99 Year Lease'),
		('Both', 'Both 49 and 99 Year Lease'),
		], string='Lease Term (Years)', required=True)
	status = fields.Selection([
		('added', 'Added'),
		('done', 'Done'),
	], string='Status', readonly=True, copy=False, index=True, track_visibility='onchange', default='added')

	valuation_id = fields.Many2one('blb_valuation.valuation_table', string='Valuation Location', required=True)
	landuse_valuation_id = fields.Many2one('blb_valuation.landuse_valuation', string='Land Use', required=True, domain="[('valuation_table_id', '=', valuation_id)]")
	possible_valuation = fields.Monetary(string="Possible Valuation", required=True) 
	lecard = fields.Monetary(string="LE Card", default=100000, required=True)
	valuationfees = fields.Monetary(string="Valuation Fees", default=300000, required=True)
	currency_id = fields.Many2one('res.currency', 'Currency', readonly=True, required=True, default=lambda self: self.env.user.company_id.currency_id.id)

	capital_value = fields.Monetary(string="Capital Value", compute="_compute_valuation", store=True)
	ground_rent = fields.Monetary(string="Ground Rent", compute="_compute_valuation", store=True)
	premium = fields.Monetary(string="Premium", compute="_compute_valuation", store=True)	
	title_charges = fields.Monetary(string="Title Charges", compute="_compute_valuation", store=True)
	le_card = fields.Monetary(string="LE Card", compute="_compute_valuation", store=True)
	legal_fees = fields.Monetary(string="Legal Fees", compute="_compute_valuation", store=True)
	valuation_fees = fields.Monetary(string="Valuation Fees", compute="_compute_valuation", store=True)
	total_valuation = fields.Monetary(string="Total Valuation", compute="_compute_valuation", store=True)

	premium_2 = fields.Monetary(string="Premium", compute="_compute_valuation", store=True)	
	title_charges_2 = fields.Monetary(string="Title Charges", compute="_compute_valuation", store=True)
	legal_fees_2 = fields.Monetary(string="Legal Fees", compute="_compute_valuation", store=True)
	total_valuation_2 = fields.Monetary(string="Total Valuation", compute="_compute_valuation", store=True)
	head_pps = fields.Many2one('res.users', string='Head PPS&R', compute="_compute_head_ppsr", store=True)
		

	_sql_constraints = [
		('client_no',
		 'UNIQUE(client_no)',
		 "The File No. should be Unique!")
	]

	#Compute Name
	@api.depends('client_no')
	def _compute_name(self):
		the_name = ""    
		for rec in self:
			if rec.client_no:
				the_name = str(rec.client_no.name)
			rec.name = the_name
		return the_name

	#Compute Name
	@api.depends('client_no')
	def _compute_head_ppsr(self):
		userid = 0    
		for rec in self:
			if rec.client_no:
				users_rec = self.env['res.users'].search([('groups_id', '=', self.env.ref("blb_base.blb_head_pps").id)])
				if users_rec:
					user_details = users_rec[0]
					userid = user_details.id
			rec.head_pps = userid
		return userid

	#Compute Name
	@api.depends('create_date')
	def _compute_date(self):
		the_date = ""    
		for rec in self:
			if rec.create_date:
				the_date = rec.create_date.strftime('%d-%b-%Y')
			rec.date_assessment = the_date
		return the_date

	#Possible Location from Clients DB
	@api.onchange('client_no')
	def _onchange_client_no(self):
		for rec in self:
			if rec.client_no:
				hectares = 0.0
				acres = 0.0
				if rec.client_no.area_estimate_hectares and rec.client_no.area_estimate_hectares != '':
					if ' ' in rec.client_no.area_estimate_hectares:
						hectares_list = rec.client_no.area_estimate_hectares.split(" ")
						hectares = hectares_list[0].strip()
						hectares = float(hectares)
						hectares = round(hectares, 2)
				if rec.client_no.area_estimate_acres and rec.client_no.area_estimate_acres != '':
					if ' ' in rec.client_no.area_estimate_acres:
						acres_list = rec.client_no.area_estimate_acres.split(" ")
						acres = acres_list[0].strip()
						acres = float(acres)
						acres = round(acres, 2)
				rec.location = rec.client_no.location
				rec.block_no = rec.client_no.block_no
				rec.plot_no = rec.client_no.plot_no
				rec.area_estimate_hectares = hectares
				rec.area_estimate_acres = acres

	#Compute Acres
	@api.onchange('area_estimate_hectares')
	def _onchange_area_estimate_hectares(self):
		for rec in self:
			if rec.area_estimate_hectares:
				acres = (float(rec.area_estimate_hectares) * 2.471)
				rec.area_estimate_acres = round(acres, 2)

	#Compute Hectares
	@api.onchange('area_estimate_acres')
	def _onchange_area_estimate_acres(self):
		for rec in self:
			if rec.area_estimate_acres:
				hectares = (float(rec.area_estimate_acres) / 2.471)
				rec.area_estimate_hectares = round(hectares, 2)

	#Possible Valuation is initially equal to the highest landuse_valuation
	@api.onchange('landuse_valuation_id')
	def _onchange_landuse_valuation_id(self):
		for rec in self:
			if rec.landuse_valuation_id:
				rec.possible_valuation = rec.landuse_valuation_id.to_range

	#Check whether possible_valuation is not less than the lowest landuse_valuation
	@api.onchange('possible_valuation')
	def _onchange_possible_valuation(self):
		for rec in self:
			if rec.possible_valuation:
				if rec.possible_valuation < rec.landuse_valuation_id.from_range:
					raise ValidationError(_( "Possible Valuation cannot be lower than the Land Use Valuation range: " + str(rec.landuse_valuation_id.name) ))


	#Compute Valuation ******************************************************
	@api.depends('possible_valuation','lease_term','area_estimate_acres')
	def _compute_valuation(self):
		for rec in self:
			if rec.possible_valuation and rec.lease_term and rec.area_estimate_acres:
				#Compute for 2 Lease Terms
				capital_value = rec.possible_valuation * float(rec.area_estimate_acres)
				ground_rent = (0.5 / 100) * capital_value
				le_card = rec.lecard
				valuation_fees = rec.valuationfees

				#For 49 Years ---------------------------------------	
				premium = (10 / 100) * capital_value			
				tcgh = (ground_rent * 49) + premium
				title_charges = ((1.5 / 100) * tcgh) + 850000  
				lgf = ((22.5 / 100) * ground_rent) + 100000
				if lgf < 300000:
					legal_fees = 300000
				else:
					legal_fees = lgf
				#Total valuation
				total_valuation = premium + ground_rent + title_charges + le_card + legal_fees + valuation_fees

				#For 99 Years ---------------------------------------
				premium_2 = (20.21 / 100) * capital_value
				tcgh_2 = (ground_rent * 99) + premium_2
				title_charges_2 = ((1.5 / 100) * tcgh_2) + 850000  
				lgf_2 = ((22.5 / 100) * ground_rent) + 100000
				if lgf_2 < 300000:
					legal_fees_2 = 300000
				else:
					legal_fees_2 = lgf_2
				#Total valuation
				total_valuation_2 = premium_2 + ground_rent + title_charges_2 + le_card + legal_fees_2 + valuation_fees
				
				#Update Record
				rec.update({
					'capital_value': capital_value,
					'premium': premium,
					'ground_rent': ground_rent,
					'title_charges': title_charges,
					'le_card': le_card,
					'legal_fees': legal_fees,
					'valuation_fees': valuation_fees,
					'total_valuation': total_valuation,
					'premium_2': premium_2,
					'title_charges_2': title_charges_2,
					'legal_fees_2': legal_fees_2,
					'total_valuation_2': total_valuation_2
				})

	#IAssessment Done
	def action_done(self):
		#Change status
		self.write({'status': 'done'})
		#Return - Action Window
		view_id = self.env.ref('blb_valuation.valuation_calculator_list').id 
		context =""
		return {
			'name':'BLB Valuation - Valuation Calculator',
			'view_type':'form',
			'view_mode':'tree,form',
			'res_model':'blb_valuation.valuation_calculator',
			'view_id': False,
			'type':'ir.actions.act_window',
			'target':'current',
			'context':context,
			'domain': domain
		}

	