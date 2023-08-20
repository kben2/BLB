# -*- coding: utf-8 -*-

from odoo import models, fields, api, tools, _
from datetime import datetime
from datetime import date
from dateutil.relativedelta import relativedelta
from datetime import timedelta
from odoo.exceptions import Warning as UserError
from odoo.exceptions import ValidationError
from odoo.exceptions import AccessDenied, UserError


class type_appraisal(models.Model):
	_name = 'blb_appraisals.type_appraisal'
	_description = 'Type of Appraisal'
	_inherit = ['mail.thread', 'mail.activity.mixin']
	_order = 'name asc'
	
	name = fields.Char(string="Type of Appraisal", required=True)


class sections(models.Model):
	_name = 'blb_appraisals.sections'
	_description = 'Appraisal Sections'
	_inherit = ['mail.thread', 'mail.activity.mixin']
	_order = 'name asc'

	name = fields.Char(string="Name", compute="_compute_name", store=True) 
	type_section = fields.Selection([
		('Section A', 'Section A'),
		('Section B', 'Section B'),
		('Section C', 'Section C'),
		('Section D', 'Section D'),
		('Section E', 'Section E'),
		('Section F', 'Section F'),
		('Section G', 'Section G'),
		], string='Section', required=True)
	title = fields.Char(string='Title', required=True)
	description = fields.Text(string='Description', required=True)
	rating_ids = fields.One2many('blb_appraisals.ratings', 'section_id', string='Rating Lines')

	#Compute Name
	@api.depends('type_section','title')
	def _compute_name(self):
		the_name = ""    
		for rec in self:
			if rec.type_section and rec.title:
				the_name = str(rec.type_section) + ": " + str(rec.title)
			rec.name = the_name
		return the_name


class ratings(models.Model):
	_name = 'blb_appraisals.ratings'
	_description = 'Appraisal Ratings'
	_inherit = ['mail.thread', 'mail.activity.mixin']
	_order = 'score desc'
	
	name = fields.Char(string="Name", compute="_compute_name", store=True) 
	rating = fields.Char(string='Rating', required=True)
	particular = fields.Text(string='Particular', required=True)
	score = fields.Float(string='Score', required=True)
	section_id = fields.Many2one('blb_appraisals.sections', string='Section', ondelete='cascade')

	#Compute Name
	@api.depends('rating','score')
	def _compute_name(self):
		the_name = ""    
		for rec in self:
			if rec.rating and rec.score:
				the_name = str(rec.rating) + " (" + str(rec.score) + ")"
			rec.name = the_name
		return the_name


class activity_questions(models.Model):
	_name = 'blb_appraisals.activity_questions'
	_description = 'Appraisal Activity/Questions'
	_inherit = ['mail.thread', 'mail.activity.mixin']
	_order = 'section_id asc, activity_question asc'
	_rec_name = 'factor_objective'
	
	type_appraisal = fields.Many2one('blb_appraisals.type_appraisal', string='Type of Appraisal', required=True, ondelete='cascade')
	section_id = fields.Many2one('blb_appraisals.sections', string='Section', required=True, ondelete='cascade')
	factor_objective = fields.Text(string='Factor/Objective', required=True)
	activity_question = fields.Text(string='Activity/Question', required=True)
	target = fields.Char(string="Target") #, required=True
	weight = fields.Integer(string='Weight (%)')
	


class blb_appraisal_wizard(models.TransientModel):
	_name = 'blb_appraisals.blb_appraisal_wizard'
	_description = 'BLB Appraisal Wizard'

	from_date = fields.Date(string="From Date", required=True)
	to_date = fields.Date(string="To Date", required=True)
	type_appraisal = fields.Many2one('blb_appraisals.type_appraisal', string='Type of Appraisal', required=True, ondelete='cascade')

	#Get selected Variables
	def get_selected_variables(self):
		#Get Selected variables
		from_date = self.from_date
		to_date = self.from_date
		type_appraisal = self.type_appraisal

		#Check dates
		if from_date > to_date:
			raise ValidationError(_( "From Date cannot be greater than To Date!" ))
		
		#Create Appraisal Record
		if from_date and to_date and type_appraisal:
			#Get Employee Details - Current loggedin user id
			userid = self.env.uid
			employee_rec = self.env['hr.employee'].search([('user_id', '=', userid)])
			employee_id = employee_rec.id
			job_title = employee_rec.job_title
			department_id = employee_rec.department_id.id
			blb_branch = employee_rec.blb_branch.id
			supervisor_employee_id = employee_rec.parent_id.id
			
			#Section Lines
			section_a_lines = []
			section_b_lines = []
			section_c_lines = []
			section_d_lines = []
			section_a = False
			section_b = False
			section_c = False
			section_d = False
			#Get the Questions
			activity_questions = self.env['blb_appraisals.activity_questions'].search([('type_appraisal', '=', type_appraisal.id)])
			for qn in activity_questions:
				if qn.section_id.type_section == 'Section A':
					section_a = True
					qnline_a = (0, 0, {'question_id': qn.id,
									'factor_objective': qn.factor_objective,
									'activity_question': qn.activity_question,
									'weight': int(qn.weight),
									'target': qn.target
								})
					section_a_lines.append(qnline_a)
				elif qn.section_id.type_section == 'Section B':
					section_b = True
					qnline_b = (0, 0, {'question_id': qn.id,
									'factor_objective': qn.factor_objective,
									'activity_question': qn.activity_question,
									'weight': int(qn.weight),
									'target': qn.target
								})
					section_b_lines.append(qnline_b)
				elif qn.section_id.type_section == 'Section C':
					section_c = True
					qnline_c = (0, 0, {'question_id': qn.id,
									'factor_objective': qn.factor_objective,
									'activity_question': qn.activity_question,
									'weight': int(qn.weight),
									'target': qn.target
								})
					section_c_lines.append(qnline_c)
				elif qn.section_id.type_section == 'Section D':
					section_d = True
					qnline_d = (0, 0, {'question_id': qn.id,
									'factor_objective': qn.factor_objective,
									'activity_question': qn.activity_question,
									'weight': int(qn.weight),
									'target': qn.target
								})
					section_d_lines.append(qnline_d)			
			#raise ValidationError(_( ">>" + str(section_b) + "-" + str(section_b_lines) ))
			#Create - Appraisal Record *****************************************************
			rec_create = self.env['blb_appraisals.blb_appraisals'].create({
				'employee_id': employee_id,
				'review_from': from_date,
				'review_to': to_date,
				'type_appraisal': type_appraisal.id,
				'status': 'added',
				'section_a': section_a,                        
				'section_b': section_b,  
				'section_c': section_c,  
				'section_d': section_d,  
				'section_a_lines': section_a_lines,
				'section_b_lines': section_b_lines,
				'section_c_lines': section_c_lines,
				'section_d_lines': section_d_lines
			})

		#Return - Action Window
		view_id = self.env.ref('blb_appraisals.blb_appraisals_kanban_view').id 
		domain = ""
		context =""
		return {
			'name':'All Appraisals',
			'view_type':'form',
			'view_mode':'kanban,tree,form',
			'res_model':'blb_appraisals.blb_appraisals',
			'view_id': False,
			'type':'ir.actions.act_window',
			'target':'current',
			'context':context,
			'domain': domain
		}


class blb_appraisals(models.Model):
	_name = 'blb_appraisals.blb_appraisals'
	_description = 'BLB Appraisals'
	_inherit = ['mail.thread', 'mail.activity.mixin']
	_order = 'name asc'

	name = fields.Char(string="Name", compute="_compute_name", store=True) 
	employee_id = fields.Many2one('hr.employee', string='Employee Name', required=True, domain=lambda self: [("user_id", "=",self.env.uid)], ondelete='cascade')
	job_title = fields.Char("Job Title", compute="_compute_employee_details", store=True) 
	department_id = fields.Many2one('hr.department', string='Department', compute="_compute_employee_details", store=True, ondelete='cascade')
	blb_branch = fields.Many2one('blb_base.branches', string='Branch', compute="_compute_employee_details", store=True, ondelete='cascade') 
	supervisor_employee_id = fields.Many2one('hr.employee', string='Supervisor', compute="_compute_employee_details", store=True, ondelete='cascade')
	supervisor_user_id = fields.Many2one('res.users', string='Supervisor UID', compute="_compute_employee_details", store=True, ondelete='cascade')
	review_from = fields.Date(string="From", required=True)
	review_to = fields.Date(string="To", required=True)
	type_appraisal = fields.Many2one('blb_appraisals.type_appraisal', string='Type of Appraisal', required=True, ondelete='cascade')
	status = fields.Selection([
		('added', 'Added'),
		('pending_supervisor_approval', 'Pending Supervisor Approval'),
		('pending_hr_approval', 'Pending HR Approval'),
		('closed', 'Closed'),
		], string='Status', readonly=True, copy=False, index=True, track_visibility='onchange', default='added') 
	section_a = fields.Boolean(string="Section A", default=False)
	section_b = fields.Boolean(string="Section B", default=False)
	section_c = fields.Boolean(string="Section C", default=False)
	section_d = fields.Boolean(string="Section D", default=False)
	section_a_lines = fields.One2many('blb_appraisals.section_a_lines', 'appraisal_id', string='Section A Lines')
	section_b_lines = fields.One2many('blb_appraisals.section_b_lines', 'appraisal_id', string='Section B Lines')
	section_c_lines = fields.One2many('blb_appraisals.section_c_lines', 'appraisal_id', string='Section C Lines')
	section_d_lines = fields.One2many('blb_appraisals.section_d_lines', 'appraisal_id', string='Section D Lines')
	created_by = fields.Many2one('res.users', string='Created by', readonly=True, default=lambda self: self.env.uid, ondelete='cascade')
	date_created = fields.Date(string="Date Created", default=fields.Date.today, readonly=True)
	date_approved_supervisor = fields.Date(string="Date Approved Supervisor", default=fields.Date.today, readonly=True)
	date_approved_hr = fields.Date(string="Date Approved HR", default=fields.Date.today, readonly=True)

	overall_assessment_a = fields.Float(string='Part A', compute="_compute_section_points", store=True)
	overall_assessment_b = fields.Float(string='Part B', compute="_compute_section_points", store=True)
	overall_assessment_c = fields.Float(string='Part C', compute="_compute_section_points", store=True)
	overall_assessment_d = fields.Float(string='Part D', compute="_compute_section_points", store=True)
	overall_assessment_total = fields.Float(string='Total - Overall Assessment', compute="_compute_section_points", store=True)
	total_score_points = fields.Char(string='Total Score Points/Assessment', compute="_compute_total_score_points", store=True)
	comments_employee = fields.Text(string='Comments by Employee')
	comments_supervisor = fields.Text(string='Comments by Supervisor')
	recommendations_supervisor = fields.Text(string='Recommendations by Supervisor on Employee Performance/Career Development')
	recommendations_hod = fields.Text(string='Recommendations by Head of Department')


	#Compute Name
	@api.depends('employee_id','review_from','review_to')
	def _compute_name(self):
		the_name = ""    
		for rec in self:
			if rec.employee_id and rec.review_from and rec.review_to:
				the_name = str(rec.employee_id.name) + " (" + str(rec.review_from) + " - " + str(rec.review_to)  + ")"
			rec.name = the_name
		return the_name

	#Compute Name
	@api.depends('employee_id')
	def _compute_employee_details(self):
		for rec in self:
			if rec.employee_id:
				#Get Employee Details
				#employee_rec = self.env['hr.employee'].search([('user_id', '=', rec.created_by.id)])
				rec.employee_id = rec.employee_id.id
				rec.job_title = rec.employee_id.job_title
				rec.department_id = rec.employee_id.department_id.id
				rec.blb_branch = rec.employee_id.blb_branch.id
				rec.supervisor_employee_id = rec.employee_id.parent_id.id
				rec.supervisor_user_id = rec.employee_id.user_id.id

	#Section Details
	@api.onchange('type_appraisal')
	def _onchange_type_appraisal(self):
		for rec in self:
			section_a_lines = []
			section_b_lines = []
			section_c_lines = []
			section_d_lines = []

			if rec.type_appraisal:
				#Get the Questions
				activity_questions = self.env['blb_appraisals.activity_questions'].search([('type_appraisal', '=', rec.type_appraisal.id)])
				#Clear Section Lines
				if len(rec.section_a_lines) > 0:
					rec.write({'section_a_lines': [(5, 0, 0)]})
				if len(rec.section_b_lines) > 0:
					rec.write({'section_b_lines': [(5, 0, 0)]})
				if len(rec.section_c_lines) > 0:
					rec.write({'section_c_lines': [(5, 0, 0)]})
				if len(rec.section_d_lines) > 0:
					rec.write({'section_d_lines': [(5, 0, 0)]})

				for qn in activity_questions:					
					target = qn.target
					weight = int(qn.weight)
					question_id = int(qn.id)
					factor_obj = qn.factor_objective
					activity_qn = qn.activity_question

					if qn.section_id.type_section == 'Section A':
						rec.section_a = True
						qnline_a = (0, 0, {'question_id': question_id,
										'factor_objective': factor_obj,
										'activity_question': activity_qn,
										'weight': weight,
										'target': target
									})
						section_a_lines.append(qnline_a)
					elif qn.section_id.type_section == 'Section B':
						rec.section_b = True
						qnline_b = (0, 0, {'question_id': question_id,
										'factor_objective': factor_obj,
										'activity_question': activity_qn,
										'weight': weight,
										'target': target
									})
						section_b_lines.append(qnline_b)
					elif qn.section_id.type_section == 'Section C':
						rec.section_c = True
						qnline_c = (0, 0, {'question_id': question_id,
										'factor_objective': factor_obj,
										'activity_question': activity_qn,
										'weight': weight,
										'target': target
									})
						section_c_lines.append(qnline_c)
					elif qn.section_id.type_section == 'Section D':
						rec.section_d = True
						qnline_d = (0, 0, {'question_id': question_id,
										'factor_objective': factor_obj,
										'activity_question': activity_qn,
										'weight': weight,
										'target': target
									})
						section_d_lines.append(qnline_d)			
				#raise ValidationError(_( ">>" + str(rec.section_b) + "-" + str(section_b_lines) ))
				#Set Lines
				rec.write({'section_a_lines': section_a_lines})
				rec.write({'section_b_lines': section_b_lines})
				#rec.section_a_lines = section_a_lines
				#rec.section_b_lines = section_b_lines
				rec.section_c_lines = section_c_lines
				rec.section_d_lines = section_d_lines

	#Compute section_points
	@api.depends('section_a_lines','section_b_lines','section_c_lines','section_d_lines')
	def _compute_section_points(self):
		assessment_a = 0.0 
		assessment_b = 0.0 
		assessment_c = 0.0 
		assessment_d = 0.0 
		assessment_total = 0.0
		for rec in self:
			if len(rec.section_a_lines) > 0:
				for line in rec.section_a_lines:
					assessment_a = assessment_a + line.weighted_rating if line.weighted_rating else assessment_a + line.appraiser_rating
			if len(rec.section_b_lines) > 0:
				for line in rec.section_b_lines:
					assessment_b = assessment_b + line.weighted_rating if line.weighted_rating else assessment_b + line.appraiser_rating
			if len(rec.section_c_lines) > 0:
				for line in rec.section_c_lines:
					assessment_c = assessment_c + line.weighted_rating if line.weighted_rating else assessment_c + line.appraiser_rating
			if len(rec.section_d_lines) > 0:
				for line in rec.section_d_lines:
					assessment_d = assessment_d + line.weighted_rating if line.weighted_rating else assessment_d + line.appraiser_rating
			#total
			assessment_total = assessment_a + assessment_b + assessment_c + assessment_d
			#update values
			rec.overall_assessment_a = assessment_a
			rec.overall_assessment_b = assessment_b
			rec.overall_assessment_c = assessment_c
			rec.overall_assessment_d = assessment_d
			rec.overall_assessment_total = assessment_total
		#return overall_assessment_total

	#Compute assessment
	@api.depends('overall_assessment_total')
	def _compute_total_score_points(self):
		assessment = ""    
		for rec in self:
			if rec.overall_assessment_total > 90.0:
				assessment = "Excellent (100 – 91)"
			elif rec.overall_assessment_total >= 76.0 and rec.overall_assessment_total <= 90.0:
				assessment = "Very Good (90 – 76)"
			elif rec.overall_assessment_total >= 60.0 and rec.overall_assessment_total <= 75.0:
				assessment = "Good (75 - 60)"
			elif rec.overall_assessment_total >= 50.0 and rec.overall_assessment_total <= 59.0:
				assessment = "Fair (59 - 50)"
			elif rec.overall_assessment_total >= 40.0 and rec.overall_assessment_total <= 49.0:
				assessment = "Below Average (49 - 40)"
			elif rec.overall_assessment_total < 40.0:
				assessment = "Poor < 40"
			rec.total_score_points = assessment
		return assessment

	#Update Section Lines - status
	def _update_sectionlines_status(self, status):
		for rec in self:
			if rec.section_a_lines:
				for line in rec.section_a_lines:
					line.update({'status': status})
			if rec.section_b_lines:
				for line in rec.section_b_lines:
					line.update({'status': status})
			if rec.section_c_lines:
				for line in rec.section_c_lines:
					line.update({'status': status})
			if rec.section_d_lines:
				for line in rec.section_d_lines:
					line.update({'status': status})

	#Forward to Supervisor
	def action_to_supervisor(self):
		#Update section lines
		self._update_sectionlines_status('pending_supervisor_approval')
		return self.write({'status': 'pending_supervisor_approval'})

	#Supervisor Approval
	def action_supervisor_approved(self):
		#Current loggedin user id
		today = date.today()
		userid = self.env.uid
		employee_rec = self.env['hr.employee'].search([('user_id', '=', userid)])
		#Check if supervisor
		if self.supervisor_employee_id.id != employee_rec.id:
			raise ValidationError(_('The Appraisal can only be Approved by the Employee Supervisor!'))
		#Update section lines
		self._update_sectionlines_status('pending_hr_approval')
		return self.write({'status': 'pending_hr_approval', 'date_approved_supervisor':today})

	#HR Approval
	def action_hr_approved(self):
		#Current loggedin user id
		today = date.today()
		userid = self.env.uid
		employee_rec = self.env['hr.employee'].search([('user_id', '=', userid)])
		#Check if HR
		if not self.env.user.has_group ('blb_base.blb_hr_officer'):
			ValidationError(_('You do not have permission to Approve and Close Appraisals!'))
		#Update section lines
		self._update_sectionlines_status('closed')
		return self.write({'status': 'closed', 'date_approved_hr':today})



class section_a_lines(models.Model):
	_name = 'blb_appraisals.section_a_lines'
	_description = 'Appraisal Section A'
	_inherit = ['mail.thread', 'mail.activity.mixin']
	_order = 'factor_objective asc'
	
	question_id = fields.Many2one('blb_appraisals.activity_questions', string='Question', required=True, ondelete='cascade')	
	factor_objective = fields.Text(string='Factor/Objective')
	factor_objective2 = fields.Text(string='Question ID')

	activity_question = fields.Text(string='Activity/Question')
	weight = fields.Integer(string='Weight (%)')
	target = fields.Char(string="Target") 
	actual_achievement = fields.Text(string='Actual Achievement (State what you have achieved in the period under review)')
	self_rating = fields.Selection(selection=lambda self: self.section_a_ratings(), string='Self Rating') #, required=True, selection=_get_status_list
	appraiser_rating = fields.Selection(selection=lambda self: self.section_a_ratings(), string='Appraiser Rating')
	self_rating_figure = fields.Float(string='Self Rating', compute="_compute_self_rating", store=True)
	appraiser_rating_figure = fields.Float(string='Appraiser Rating', compute="_compute_appraiser_rating", store=True)

	appraiser_comments = fields.Text(string='Appraiser Comments')
	weighted_rating = fields.Float(string='Appraiser Rating', compute="_compute_weighted_rating", store=True)
	status = fields.Char("Status", default='added')
	appraisal_id = fields.Many2one('blb_appraisals.blb_appraisals', string='Appraisal', ondelete='cascade')

	#self_rating 
	@api.depends('self_rating')
	def _compute_self_rating(self):	
		for rec in self:
			if rec.self_rating and rec.self_rating != '':
				rec.self_rating_figure = float(rec.self_rating)

	#appraiser_rating
	@api.depends('appraiser_rating')
	def _compute_appraiser_rating(self):	
		for rec in self:
			if rec.appraiser_rating and rec.appraiser_rating != '':
				rec.appraiser_rating_figure = float(rec.appraiser_rating)

	#Section A ratings
	def section_a_ratings(self):
		ratings = []
		#Get the Section
		section_rec = self.env['blb_appraisals.sections'].search([('type_section', '=', 'Section A')])
		if section_rec and len(section_rec.rating_ids) > 0:
			for rating in section_rec.rating_ids:
				score = (rating.score,rating.score)
				ratings.append(score)
		return ratings

	#Compute Weighted Rating
	@api.depends('weight','appraiser_rating')
	def _compute_weighted_rating(self):
		weight = 0.0  
		for rec in self:
			if rec.weight and rec.weight != 0 and rec.appraiser_rating:
				weight = float(rec.weight) * float(rec.appraiser_rating)
				rec.weighted_rating = weight
			else:
				weight = float(rec.appraiser_rating)
				rec.weighted_rating = weight
		#return weight

class section_b_lines(models.Model):
	_name = 'blb_appraisals.section_b_lines'
	_description = 'Appraisal Section B'
	_inherit = ['mail.thread', 'mail.activity.mixin']
	_order = 'factor_objective asc'
	
	question_id = fields.Many2one('blb_appraisals.activity_questions', string='Question', required=True, ondelete='cascade')	
	factor_objective = fields.Text(string='Factor/Objective')
	factor_objective2 = fields.Text(string='Question ID')

	activity_question = fields.Text(string='Activity/Question')
	weight = fields.Integer(string='Weight (%)')
	target = fields.Char(string="Target") 
	actual_achievement = fields.Text(string='Actual Achievement (State what you have achieved in the period under review)')
	self_rating = fields.Selection(selection=lambda self: self.section_b_ratings(), string='Self Rating') 
	appraiser_rating = fields.Selection(selection=lambda self: self.section_b_ratings(), string='Appraiser Rating')
	self_rating_figure = fields.Float(string='Self Rating', compute="_compute_self_rating", store=True)
	appraiser_rating_figure = fields.Float(string='Appraiser Rating', compute="_compute_appraiser_rating", store=True)

	appraiser_comments = fields.Text(string='Appraiser Comments')
	weighted_rating = fields.Float(string='Appraiser Rating', compute="_compute_weighted_rating", store=True)
	status = fields.Char("Status", default='added')
	appraisal_id = fields.Many2one('blb_appraisals.blb_appraisals', string='Appraisal', ondelete='cascade')

	#self_rating 
	@api.depends('self_rating')
	def _compute_self_rating(self):	
		for rec in self:
			if rec.self_rating and rec.self_rating != '':
				rec.self_rating_figure = float(rec.self_rating)

	#appraiser_rating
	@api.depends('appraiser_rating')
	def _compute_appraiser_rating(self):	
		for rec in self:
			if rec.appraiser_rating and rec.appraiser_rating != '':
				rec.appraiser_rating_figure = float(rec.appraiser_rating)

	#Section Details
	# @api.model
	# def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False): 
	# 	if view_type == "form":
	# 		#execute your method here
	# 		#raise ValidationError(_( self.env.context.get('factor_objective') ))
	# 		self._compute_question_details()			
	# 	return super(section_b_lines, self).fields_view_get(view_id, view_type, toolbar, submenu)

	#Section B ratings
	def section_b_ratings(self):
		ratings = []
		#Get the Section
		section_rec = self.env['blb_appraisals.sections'].search([('type_section', '=', 'Section B')])
		if section_rec and len(section_rec.rating_ids) > 0:
			for rating in section_rec.rating_ids:
				score = (rating.score,rating.score)
				ratings.append(score)
		return ratings

	#Compute Weighted Rating
	@api.depends('weight','appraiser_rating')
	def _compute_weighted_rating(self):
		weight = 0.0  
		for rec in self:
			if rec.weight and rec.weight != 0 and rec.appraiser_rating:
				weight = float(rec.weight) * float(rec.appraiser_rating)
				rec.weighted_rating = weight
			else:
				weight = float(rec.appraiser_rating)
				rec.weighted_rating = weight
		#return weight

class section_c_lines(models.Model):
	_name = 'blb_appraisals.section_c_lines'
	_description = 'Appraisal Section C'
	_inherit = ['mail.thread', 'mail.activity.mixin']
	_order = 'factor_objective asc'
	
	question_id = fields.Many2one('blb_appraisals.activity_questions', string='Question', required=True, ondelete='cascade')	
	factor_objective = fields.Text(string='Factor/Objective')
	factor_objective2 = fields.Text(string='Question ID')

	activity_question = fields.Text(string='Activity/Question', related='question_id.activity_question', store=True)
	target = fields.Char(string="Target", related='question_id.target', store=True) 
	weight = fields.Integer(string='Weight (%)', related='question_id.weight', store=True)
	actual_achievement = fields.Text(string='Actual Achievement (State what you have achieved in the period under review)')
	self_rating = fields.Selection(selection=lambda self: self.section_c_ratings(), string='Self Rating') 
	appraiser_rating = fields.Selection(selection=lambda self: self.section_c_ratings(), string='Appraiser Rating')
	self_rating_figure = fields.Float(string='Self Rating', compute="_compute_self_rating", store=True)
	appraiser_rating_figure = fields.Float(string='Appraiser Rating', compute="_compute_appraiser_rating", store=True)

	appraiser_comments = fields.Text(string='Appraiser Comments')
	weighted_rating = fields.Float(string='Appraiser Rating', compute="_compute_weighted_rating", store=True)
	status = fields.Char("Status", default='added')
	appraisal_id = fields.Many2one('blb_appraisals.blb_appraisals', string='Appraisal', ondelete='cascade')

	#self_rating 
	@api.depends('self_rating')
	def _compute_self_rating(self):	
		for rec in self:
			if rec.self_rating and rec.self_rating != '':
				rec.self_rating_figure = float(rec.self_rating)

	#appraiser_rating
	@api.depends('appraiser_rating')
	def _compute_appraiser_rating(self):	
		for rec in self:
			if rec.appraiser_rating and rec.appraiser_rating != '':
				rec.appraiser_rating_figure = float(rec.appraiser_rating)

	#Section C ratings
	def section_c_ratings(self):
		ratings = []
		#Get the Section
		section_rec = self.env['blb_appraisals.sections'].search([('type_section', '=', 'Section C')])
		if section_rec and len(section_rec.rating_ids) > 0:
			for rating in section_rec.rating_ids:
				score = (rating.score,rating.score)
				ratings.append(score)
		return ratings

	#Compute Weighted Rating
	@api.depends('weight','appraiser_rating')
	def _compute_weighted_rating(self):
		weight = 0.0  
		for rec in self:
			if rec.weight and rec.weight != 0 and rec.appraiser_rating:
				weight = float(rec.weight) * float(rec.appraiser_rating)
				rec.weighted_rating = weight
			else:
				weight = float(rec.appraiser_rating)
				rec.weighted_rating = weight
		#return weight


class section_d_lines(models.Model):
	_name = 'blb_appraisals.section_d_lines'
	_description = 'Appraisal Section D'
	_inherit = ['mail.thread', 'mail.activity.mixin']
	_order = 'factor_objective asc'
	
	question_id = fields.Many2one('blb_appraisals.activity_questions', string='Question', required=True, ondelete='cascade')	
	factor_objective = fields.Text(string='Factor/Objective')
	factor_objective2 = fields.Text(string='Question ID')

	activity_question = fields.Text(string='Activity/Question', related='question_id.activity_question', store=True)
	target = fields.Char(string="Target", related='question_id.target', store=True) 
	weight = fields.Integer(string='Weight (%)', related='question_id.weight', store=True)
	actual_achievement = fields.Text(string='Actual Achievement (State what you have achieved in the period under review)')
	self_rating = fields.Selection(selection=lambda self: self.section_d_ratings(), string='Self Rating') 
	appraiser_rating = fields.Selection(selection=lambda self: self.section_d_ratings(), string='Appraiser Rating')
	self_rating_figure = fields.Float(string='Self Rating', compute="_compute_self_rating", store=True)
	appraiser_rating_figure = fields.Float(string='Appraiser Rating', compute="_compute_appraiser_rating", store=True)

	appraiser_comments = fields.Text(string='Appraiser Comments')
	weighted_rating = fields.Float(string='Appraiser Rating', compute="_compute_weighted_rating", store=True)
	status = fields.Char("Status", default='added')
	appraisal_id = fields.Many2one('blb_appraisals.blb_appraisals', string='Appraisal', ondelete='cascade')

	#self_rating 
	@api.depends('self_rating')
	def _compute_self_rating(self):	
		for rec in self:
			if rec.self_rating and rec.self_rating != '':
				rec.self_rating_figure = float(rec.self_rating)

	#appraiser_rating
	@api.depends('appraiser_rating')
	def _compute_appraiser_rating(self):	
		for rec in self:
			if rec.appraiser_rating and rec.appraiser_rating != '':
				rec.appraiser_rating_figure = float(rec.appraiser_rating)

	#Section D ratings
	def section_d_ratings(self):
		ratings = []
		#Get the Section
		section_rec = self.env['blb_appraisals.sections'].search([('type_section', '=', 'Section D')])
		if section_rec and len(section_rec.rating_ids) > 0:
			for rating in section_rec.rating_ids:
				score = (rating.score,rating.score)
				ratings.append(score)
		return ratings

	#Compute Weighted Rating
	@api.depends('weight','appraiser_rating')
	def _compute_weighted_rating(self):
		weight = 0.0  
		for rec in self:
			if rec.weight and rec.weight != 0 and rec.appraiser_rating:
				weight = float(rec.weight) * float(rec.appraiser_rating)
				rec.weighted_rating = weight
			else:
				weight = float(rec.appraiser_rating)
				rec.weighted_rating = weight
		#return weight