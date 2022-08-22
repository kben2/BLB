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

class client(models.Model):
    _name = 'client.client'
    #_inherit = ['mail.thread', 'ir.needaction_mixin']
    _description = 'BLB Clients'
    _order = 'file_no asc'

    name = fields.Char(string="Client Details.", readonly=True, compute="_compute_name", store=True)
    temp_file_no = fields.Char(string="Temporary File No.", readonly=True)
    file_no = fields.Char(string="BLB File No.")
    client_name = fields.Char(string="Client Name", required=True)
    area_estimate_units = fields.Selection([
        ('Hectares', "Hectares"),
        ('Acres', "Acres"),
    ], string="Area Estimate Units")
    area_estimate = fields.Float(string="Area Estimate")
    area_estimate_hectares = fields.Char(string="Estimate Hectares", compute="_compute_area_estimate", store=True)
    area_estimate_acres = fields.Char(string="Estimate Acres", compute="_compute_area_estimate", store=True)
    location = fields.Char(string="Location", required=True)
    block = fields.Char(string="Block Number", compute="_compute_block", store=False)
    coordinates_system = fields.Many2one('layer.coordinates_system', string='Co-ordinates System')
    location_x = fields.Char(string="Location X Coordinates", compute="_compute_area_estimate", store=True)
    location_y = fields.Char(string="Location Y Coordinates", compute="_compute_area_estimate", store=True)
    state = fields.Selection([
        ('fileopen', 'File Opening Branch'),
        ('legal', 'Legal Office'),
        ('blbregistry', 'BLB Registry'),
        ('blbregistry_report', 'BLB Registry - Report Pending'),
        ('survey', 'Survey'),
        ('survey_rectify', 'Survey Rectification'),
        ('planning', 'Planning'),
        ('processing', 'Deed Plan Processing'),
        ('valuation', 'Valuation'),
        ('lease', 'Lease Committee'),
        ('title', 'Title Processing'),
        ('issue', 'Title Issued'),
        ('done', 'Completed'),
        ('cancel', 'Cancelled'),
        ], string='Status', readonly=True, copy=False, index=True, track_visibility='onchange', default='fileopen')

    check_wetland = fields.Char(string="Wetland", readonly=True)
    check_surveyed = fields.Char(string="Surveyed Kibanja", readonly=True)
    check_blbland = fields.Char(string="BLB Land", readonly=True)
    plot_geojson = fields.Char(string="GeoJSON", compute="_compute_area_estimate", store=True)

    remarks = fields.Text(string="Remarks")    
    created_by = fields.Many2one('res.users', string='Created by', store=True, readonly=True, default=lambda self: self.env.uid) 
    created_branch = fields.Many2one('client.branches', string='Created at', readonly=True, compute="_compute_created_branch", store=True)
    clearing_by = fields.Many2one('res.users', string='Cleared by', store=True, readonly=True)
    receipt_survey = fields.Char(string="Survey Receipt No.")
    
    type_survey = fields.Selection([
        ('Fresh Survey', "Fresh Survey"),
        ('Massive Survey', "Massive Survey"),
        ('Backlog Survey', "Backlog Survey"),
        ('Re-Survey', "Re-Survey"),
        ('Boundary Opening', "Boundary Opening"),
        ('Sub Division', "Sub Division"),
        ('Special Survey', "Special Survey"),
        ('Field Correspondence', "Field Correspondence"),
    ], string="Type of survey") 
    date_assigned_survey = fields.Date(string="Date Assigned for Survey")
    user_assigned_survey = fields.Many2one('res.users', string='Assigned Surveyor') 
    surveyed_by = fields.Many2one('res.users', string='Survey by', readonly=True)    
    date_survey = fields.Date(string="Date of Survey")
    date_worked_on = fields.Datetime('Coordinates upload date', required=False, readonly=False, select=True, default=lambda self: fields.datetime.now())

    planned_by = fields.Many2one('res.users', string='Planning Done by', readonly=True)
    date_planning = fields.Date(string="Date of Planning")
    remarks_planning = fields.Char(string="Remarks after Planning")

    processing_by = fields.Many2one('res.users', string='Processing Done by', readonly=True)
    date_start_processing = fields.Date(string="Date of Start Processing")
    date_end_processing = fields.Date(string="Date of End Processing")
    block_no = fields.Char(string="Block No.")
    plot_no = fields.Char(string="Plot No.")

    date_valuation = fields.Date(string="Date of Valuation")
    valuer = fields.Many2one('res.users', string='Valuer', readonly=True)
    receipt_valuation = fields.Char(string="Valuation Receipt No.")

    date_lease_committee = fields.Date(string="Date of Valuation")
    duration_lease = fields.Integer(string="Lease Duration (Years)")

    date_start_title_processing = fields.Date(string="Date of Start Title Processing")
    date_end_title_processing = fields.Date(string="Date of End Title Processing")

    date_issued = fields.Date(string="Date Issued")
    issued_by = fields.Many2one('res.users', string='Issued by', readonly=True)

    #Ownership
    plot_ownership_lines = fields.One2many('client.plot_ownership', 'file_no', string='Owners')

    #Plot Coordinates
    plot_coordinates = fields.One2many('client.plot_coordinates', 'file_no', string='Plot Co-ordinates')

    #Maps - Plots Surveyed
    clientmap_surveyed = fields.Html('Client Map HTML', compute='_get_map_details', sanitize=False, strip_style=False)
    all_clientsmap_surveyed = fields.Html('All Clients Map HTML', compute='_get_map_details', sanitize=False, strip_style=False)

    #Legal
    ownership_type = fields.Selection([
        ('Ownership - Purchase', "Ownership - Purchase"),
        ('Ownership - Inheritance', "Ownership - Inheritance"),
        ('Ownership - Donation', "Ownership - Donation"),
        ('Companies', "Companies"),
        ('Non-Goverment Organisations', "Non-Goverment Organisations"),
        ('Trusts', "Trusts"),
    ], string="Type of Ownership")
    legal_ownershippurchase = fields.One2many('client.legal_ownershippurchase', 'file_no', string='Purchase') #Documents Showing Acquistion/Ownership
    legal_ownershipinheritance = fields.One2many('client.legal_ownershipinheritance', 'file_no', string='Inheritance')
    legal_ownershipdonation = fields.One2many('client.legal_ownershipdonation', 'file_no', string='Donation')
    legal_companies = fields.One2many('client.legal_companies', 'file_no', string='Companies')
    legal_ngos = fields.One2many('client.legal_ngos', 'file_no', string='Non-Government Organisations')
    legal_trusts = fields.One2many('client.legal_trusts', 'file_no', string='Trusts')
    legal_remarks = fields.Text(string="Legal Remarks")

    _sql_constraints = [
        ('temp_file_no_unique',
         'UNIQUE(temp_file_no)',
         "The Temporary File No. must be unique")
    ]

    _sql_constraints = [
        ('file_no_unique',
         'UNIQUE(file_no)',
         "The File No. must be unique")
    ]

    # @api.multi
    # def name_get(self):
    #     result = []
    #     for clt in self:
    #         name = str(clt.client_name) + " (" + str(clt.file_no) + ")"
    #         result.append((clt.id, name))
    #     return result

    # @api.onchange('client_name')
    # def onchange_client_name(self):
    #     cname = ""
    #     if self.client_name:
    #         if self.file_no:
    #             cname = str(self.client_name) + " (" + str(self.file_no) + ")"
    #         else:
    #             cname = str(self.client_name)
    #     self.name = cname

    # @api.onchange('file_no')
    # def onchange_file_no(self):
    #     cname = ""
    #     if self.file_no:
    #         cname = str(self.client_name) + " (" + str(self.file_no) + ")"
    #     self.name = cname



    #Compute Name
    @api.multi
    @api.depends('client_name','file_no')
    def _compute_name(self):
        clientname = ""
        for rec in self:
            if rec.client_name and rec.file_no:
                clientname = str(rec.client_name) + " (" + str(rec.file_no) + ")"
            rec.name = clientname
        return clientname


    # #Compute Branch of Creation
    @api.multi
    @api.depends('created_by')
    def _compute_created_branch(self):
        the_branch = 0
        for rec in self:
            if rec.created_by:
                userid = rec.created_by.id
                user_rec = self.env['res.users'].search([('id', '=', userid)])
                user_branchid = user_rec.blb_branch.id
                the_branch = user_branchid
            rec.created_branch = the_branch
        return the_branch

    #Compute Location
    @api.multi
    @api.depends('location_x','location_y','coordinates_system')
    def _compute_location(self):
        location = ''
        for record in self:
            if record.location_x and record.location_y:
                if record.coordinates_system == False:
                    raise ValidationError(_('Please select the Coordinates System'))
                elif record.coordinates_system != False:
                    #Get code of Coordinates system
                    systemid = record.coordinates_system.id
                    coordinates_system_record = self.env['layer.coordinates_system'].search([('id', '=', systemid)])
                    system_srid = coordinates_system_record.srid
                    #Select Village Layers from DB
                    select_query = """SELECT villages_layer.name, villages_layer.geom FROM villages_layer WHERE ST_Contains (villages_layer.geom, (ST_SetSRID (ST_Point (%s, %s), %s)))""" %  (record.location_x, record.location_y, system_srid)
                    self._cr.execute(select_query)
                    result_query = self.env.cr.dictfetchall()
                    for row_dict in result_query:
                        village_name = row_dict['name']
        return True

    #Compute Block
    @api.multi
    @api.depends('location_x','location_y','coordinates_system')
    def _compute_block(self):
        block = ''
        for record in self:
            if record.location_x and record.location_y:
                if record.coordinates_system == False:
                    raise ValidationError(_('Please select the Coordinates System'))
                elif record.coordinates_system != False:
                    #Get code of Coordinates system
                    systemid = record.coordinates_system.id
                    coordinates_system_record = self.env['layer.coordinates_system'].search([('id', '=', systemid)])
                    system_srid = coordinates_system_record.srid
                    #Select Parish Layer from DB
                    select_query = """SELECT kla_blocks.number,kla_blocks.geom FROM kla_blocks WHERE ST_Contains (kla_blocks.geom, (ST_SetSRID (ST_Point (%s, %s), %s)))""" %  (record.location_x, record.location_y, system_srid)
                    self._cr.execute(select_query)
                    result_query = self.env.cr.dictfetchall()
                    if result_query:
                        for row_dicti in result_query:
                            block_name = row_dicti['number']
                    else:
                        block_name = 'No block here!'
            record.block = block_name         
        return block_name

    #Compute Area Estiamte - 
    @api.multi
    @api.depends('plot_coordinates')
    def _compute_area_estimate(self):
        #Get Area Estimate from Coordinates ........................
        are = ''
        hectares = ''
        acres = ''
        centroid_east =''
        centroid_nort =''
        geojson =''
        for record in self:
            # if record.area_estimate_units == 'Hectares' and record.area_estimate != False:
            #   acres = round((2.471 * record.area_estimate), 3)
            #   acres = str(acres)  + ' Acres'
            #   hectares = str(record.area_estimate) + ' Ha'
            # elif record.area_estimate_units == 'Acres' and record.area_estimate != False:
            #   hectares = round((record.area_estimate / 2.471), 2)
            #   hectares = str(hectares) + ' Ha'
            #   acres = str(record.area_estimate) + ' Acres'
            if len(record.plot_coordinates) >= 4:
                coordinates_list = []
                for coord_pair in record.plot_coordinates:
                    coord_list = [float(coord_pair.coordinate_x), float(coord_pair.coordinate_y)]
                    coordinates_list.append(coord_list)
                #Do all other Stuff here with the  coordinates_list ........................................
                last = (len(coordinates_list))
                # last = (len(coordinates_list))
                polygon =[]
                polygon.append(" ST_MakePolygon(ST_Makeline( ARRAY[")
                for i in range(last - 1): 
                    polygon.append( "ST_SetSRID(ST_MakePoint("+ str(coordinates_list[i][0]) +","+ str(coordinates_list[i][1]) + "), 21096),")
                polygon.append( "ST_SetSRID(ST_MakePoint("+ str(coordinates_list[last - 1][0]) + "," + str(coordinates_list[last - 1][1]) + "),21096),")
                polygon.append( "ST_SetSRID(ST_MakePoint("+ str(coordinates_list[0][0]) + "," + str(coordinates_list[0][1]) + "),21096)]))")

                sql_polygon = ("".join(polygon))

                sql = """with d as ( SELECT %s as geom)
                                        select ST_AsGeoJSON(geom) as k,round((ST_X(ST_Centroid(geom)))::numeric,3) as x,round((ST_Y(ST_Centroid(geom)))::numeric,3) as y,
                                        round(((ST_Area(geom)::numeric)/10000),3) as hectares,round(((ST_Area(geom)::numeric)/4046.856),2) as acres from d""" % (sql_polygon)

                print(sql)
                #Compute area in Hectares.
                select_query = """%s""" %  (sql)
                self._cr.execute(select_query)
                result_query = self.env.cr.dictfetchall()
                if result_query:
                    for row_dicti in result_query:
                            hec = row_dicti['hectares']
                            acr = row_dicti['acres']
                            cex = row_dicti['x']
                            cey = row_dicti['y']
                            geo = row_dicti['k']
                else:
                    raise ValidationError(_('Oops! Something went wrong.'))
                #raise ValidationError(_(are))
                acres = acr
                acres = str(acres)  + ' Acres'
                hectares = hec
                hectares = str(hectares) + ' Ha'
                centroid_east = cex
                centroid_nort = cey
                geojson = geo
            # record.area_estimate = are
            record.area_estimate_hectares = hectares
            record.area_estimate_acres = acres
            record.location_x = centroid_east
            record.location_y = centroid_nort
            record.plot_geojson = geojson
        return True


    #Check Plot Coordinates + Plot Map

    def action_check_points(self):
        check_wetland = ''
        check_surveyed = ''
        check_blbland = ''
        for record in self:
            #Select Wetland layer in which the said plot falls.
            select_query = """SELECT wetland2014.wetland201 FROM wetland2014 WHERE ST_Contains (wetland2014.geom, (ST_SetSRID (ST_Point (%s,%s), 21096)))""" %  (record.location_x,record.location_y)
            #Select Surveyed Kibanja in which this point falls.
            select_query_k = """SELECT plot.name FROM usa.plot WHERE ST_Contains (plot.geom, (ST_SetSRID (ST_Point (%s,%s), 21096)))""" %  (record.location_x,record.location_y)
            #Check Surveyed Kibanja in which this point falls.
            select_query_b = """SELECT blb_land.tenure FROM blb_land WHERE ST_Contains (blb_land.geom, (ST_SetSRID (ST_Point (%s,%s), 21096)))""" %  (record.location_x,record.location_y)
            self._cr.execute(select_query)
            result_query = self.env.cr.dictfetchall()
            if result_query:
                for row_dicti in result_query:
                    check_wetland = row_dicti['wetland201']
            else:
                check_wetland = 'No!'
            record.check_wetland = check_wetland
            self._cr.execute(select_query_k)
            result_query_k = self.env.cr.dictfetchall()
            if result_query_k:
                for row_dicti in result_query_k:
                    check_surveyed = row_dicti['name']
            else:
                check_surveyed = 'No!'
            record.check_surveyed = check_surveyed
            self._cr.execute(select_query_b)
            result_query_b = self.env.cr.dictfetchall()
            if result_query_b:
                for row_dicti in result_query_b:
                    check_blbland = 'Yes!'#row_dicti['tenure']
            else:
                check_blbland = 'No!'
            record.check_blbland = check_blbland          
        return True
        
    #FileOpen to Legal
    @api.multi
    def action_to_legal(self):
        if not self.location:
            raise ValidationError(_('Please enter the Location!'))
        return self.write({'state': 'legal'})

    #FileOpen to BLB Registry
    @api.multi
    def action_to_blbregistry(self):
        if not self.location:
            raise ValidationError(_('Please enter some Legal remarks!'))
        return self.write({'state': 'blbregistry'})

    #BLB Registry to Survey
    @api.multi
    def action_to_survey(self):
        if self.file_no == False:
            raise ValidationError(_('Please enter the File Number!'))
        elif self.receipt_survey == False:
            raise ValidationError(_('Please enter the Receipt Number for Surveying!'))
        #Current loggedin user id
        userid = self.env.uid
        return self.write({'state': 'survey', 'clearing_by': userid })

    #Survey to Physical Planning
    @api.multi
    def action_to_planning(self):
        if self.type_survey == False:
            raise ValidationError(_('Please select Type of Survey!'))
        elif self.date_assigned_survey == False:
            raise ValidationError(_('Please enter Date of Assigned Survey!'))
        #Get Survey Details from Database - After Uploding Survey Data
        fileno = self.file_no
        # select_query = """SELECT plot.file_number, plot.surveyor, plot.date_surveyed FROM usa.plot WHERE plot.file_number = '%s' ORDER BY gid DESC LIMIT 1""" % (fileno)
        # self._cr.execute(select_query)
        # result_query = self.env.cr.dictfetchall()
        # for row_dict in result_query:
            # surveyor = row_dict['surveyor']
            # date_surveyed = row_dict['date_surveyed']
        # #If Surveyor was not found
        # if surveyor:
            # user_rec = self.env['res.users'].search([('id', 'ilike', surveyor)])
            # userid = user_rec.id
        # else:
            # raise ValidationError(_('Survey for this File has not been completed!'))
        # #check for Date of Survey
        # if surveyor:
            # date_time_str = str(date_surveyed)
            # date_time_obj = datetime.strptime(date_time_str, '%d/%m/%Y')
            # datesurvey = date_time_obj.date()
        # else:
            # raise ValidationError(_('Survey Date not found!'))
        return self.write({'state': 'planning'})#, 'surveyed_by': userid, 'date_survey': datesurvey})

    #Planning Back to BLB Registry
    @api.multi
    def action_back_to_registry(self):
        if self.remarks_planning == False:
            raise ValidationError(_('Please enter Remarks!'))
        #Current loggedin user id
        today = date.today()
        userid = self.env.uid
        return self.write({'state': 'blbregistry_report', 'planned_by': userid,  'date_planning': today })
    
    #Planning Back to Survey
    @api.multi
    def action_back_to_survey(self):
        if self.remarks_planning == False:
            raise ValidationError(_('Please enter Remarks!'))
        #Current loggedin user id
        today = date.today()
        userid = self.env.uid
        return self.write({'state': 'survey_rectify', 'planned_by': userid,  'date_planning': today })

    #Planning to Processing
    @api.multi
    def action_to_processing(self):
        if self.remarks_planning == False:
            raise ValidationError(_('Please enter Remarks!'))
        #Current loggedin user id
        today = date.today()
        userid = self.env.uid
        return self.write({'state': 'processing', 'planned_by': userid,  'date_planning': today })

    #Processing to Valuation
    @api.multi
    def action_to_valuation(self):
        if self.date_start_processing == False:
            raise ValidationError(_('Please enter Date Start of Processing!'))
        elif self.date_end_processing == False:
            raise ValidationError(_('Please enter the Date End Processing!'))
        elif self.block_no == False:
            raise ValidationError(_('Please enter the Block No.!'))
        elif self.plot_no == False:
            raise ValidationError(_('Please enter the Plot No.!'))
        #Current loggedin user id
        userid = self.env.uid
        return self.write({'state': 'valuation', 'processing_by': userid })

    #Valuation to  Lease
    @api.multi
    def action_to_lease(self):
        if self.receipt_valuation == False:
            raise ValidationError(_('Please enter Receipt of Valuation!'))
        #Current loggedin user id
        today = date.today()
        userid = self.env.uid
        return self.write({'state': 'lease', 'valuer': userid, 'date_valuation': today })

    #Lease to Title
    @api.multi
    def action_to_title(self):
        if self.date_lease_committee == False:
            raise ValidationError(_('Please enter Date of Lease Committee!'))
        elif self.duration_lease == False:
            raise ValidationError(_('Please enter Lease Duration!'))
        #Current loggedin user id
        userid = self.env.uid
        return self.write({'state': 'title'})

    #Title to Issue
    @api.multi
    def action_to_issue(self):
        if self.date_start_title_processing == False:
            raise ValidationError(_('Please enter Date Start of Title Processing!'))
        elif self.date_end_title_processing == False:
            raise ValidationError(_('Please enter Date End of Title Processing!'))
        #Current loggedin user id
        userid = self.env.uid
        return self.write({'state': 'issue'})

    #Issued to Done
    @api.multi
    def action_to_done(self):
        #Current loggedin user id
        today = date.today()
        userid = self.env.uid
        return self.write({'state': 'done', 'issued_by': userid, 'date_issued': today })

    #Action Cancel
    @api.multi
    def action_cancel(self):
        return self.write({'state': 'cancel'})

    #Put together the temp_file_no
    @api.model
    def create(self, vals):
        #Sequence 
        seq = self.env['ir.sequence'].next_by_code('temp_fileno_sequence')      
        vals['temp_file_no'] = seq
        return super(client, self).create(vals)

    #Maps Details
    @api.depends('file_no')
    def _get_map_details(self):
        #Get Current Record Details
        if self.id and self.file_no:
            for rec in self:
                url = "http://192.168.1.8:8080/mm/trial.php?file_no=" + file_no
                #template = self.env.ref('client.clientmap_page_iframe')
                #rec.clientmap_surveyed = template.render({ 'url' : url })
                with tools.file_open(path, 'rb') as desc_file:
                    doc = desc_file.read()
                    html = lxml.html.document_fromstring(doc)
                    rec.clientmap_surveyed = tools.html_sanitize(lxml.html.tostring(html))

    #Get Client Map
    @api.model
    def get_clientmap(self,file_no):
        #Get Record
        client_rec = self.env['client.client'].search([('file_no', '=', file_no)])
        clientid = client_rec.id
        client_fileno = client_rec.file_no
        return client_fileno

    #Map View
    @api.multi
    def view_map(self):
        #Get Current Record ID
        if self.id:
            rec_id = self.id
            client_rec = self.env['client.client'].search([('id', '=', rec_id)])
            client_fileno = client_rec.file_no
            client_name = client_rec.client_name
        else:
            rec_id = 0
            client_fileno = ""
            client_name = ""
        #raise ValidationError(_(client_fileno))
        #Get Return - Maps Window
        view_id = self.env.ref('client.clients_maplist_form').id
        domain = ""
        context = context ="{'id': '%d', 'default_client_name': '%s', 'default_file_no': '%s'}" % (rec_id, client_name, client_fileno)
        return {
            'name':'Client Surveyed Plot',
            'view_type':'form',
            'view_mode':'form',
            'res_model':'client.client',
            'view_id': view_id,
            'type':'ir.actions.act_window',
            'target':'current',
            'context':context,
            'domain': domain
        }


class branches(models.Model):
    _name = 'client.branches'
    #_inherit = ['mail.thread', 'ir.needaction_mixin']
    _description = 'BLB Branches'
    _order = 'name asc'

    name = fields.Char(string="Branch Name", required=True)

    _sql_constraints = [
        ('name_unique',
         'UNIQUE(name)',
         "The Branch name must be unique")
    ]


class client_plots(models.Model):
    _name = 'client.client_plots'
    _description = 'BLB Clients Plots Data'
    _order = 'file_number asc'

    file_number = fields.Char(string="BLB File No.")
    date_surveyed = fields.Date(string='Date Surveyed')
    surveyor = fields.Char(string="Surveyor")
    geom = fields.Text(string="Geometry")

class legal_ownershippurchase(models.Model):
    _name = 'client.legal_ownershippurchase'
    _description = 'Legal Ownership Purchase'
    _order = 'name asc'

    name = fields.Char(string="Name", required=True)
    file_no = fields.Many2one('client.client', string='Client', required=True)

class legal_ownershipinheritance(models.Model):
    _name = 'client.legal_ownershipinheritance'
    _description = 'Legal Ownership Inheritance'
    _order = 'name asc'

    name = fields.Char(string="Name", required=True)
    file_no = fields.Many2one('client.client', string='Client', required=True)


class legal_ownershipdonation(models.Model):
    _name = 'client.legal_ownershipdonation'
    _description = 'Legal Ownership Donation'
    _order = 'name asc'

    name = fields.Char(string="Name", required=True)
    file_no = fields.Many2one('client.client', string='Client', required=True)


class legal_companies(models.Model):
    _name = 'client.legal_companies'
    _description = 'Legal Companies'
    _order = 'name asc'

    name = fields.Char(string="Name", required=True)
    file_no = fields.Many2one('client.client', string='Client', required=True)


class legal_ngos(models.Model):
    _name = 'client.legal_ngos'
    _description = 'Legal Non-Goverment Organisation'
    _order = 'name asc'

    name = fields.Char(string="Name", required=True)
    file_no = fields.Many2one('client.client', string='Client', required=True)


class legal_trusts(models.Model):
    _name = 'client.legal_trusts'
    _description = 'Legal Trusts'
    _order = 'name asc'

    name = fields.Char(string="Name", required=True)
    file_no = fields.Many2one('client.client', string='Client', required=True)

class plot_ownership(models.Model):
    _name = 'client.plot_ownership'
    _description = 'Plot Ownership'
    _order = 'owner_name asc'

    owner_name = fields.Char(string="Owner Name", required=True)
    date_birth = fields.Date(string="Date of Birth", required=True)
    gender = fields.Selection([
        ('Male', "Male"),
        ('Female', "Female"),
    ], string="Gender", required=True)
    file_no = fields.Many2one('client.client', string='Client', required=True, ondelete='restrict')


class plot_coordinates(models.Model):
    _name = 'client.plot_coordinates'
    _description = 'Plot Co-ordinates'

    coordinate_x = fields.Char(string="X-Coordinate", required=True)
    coordinate_y = fields.Char(string="Y-Coordinate", required=True)
    file_no = fields.Many2one('client.client', string='Client', required=True, ondelete='restrict')


class allclients_map(models.TransientModel):
    _name = 'client.allclients_map'
    _description = 'All Clients Map'

    allclients = fields.Char(string="All Clients")


class blb_user_branches(models.Model):
    _inherit = 'res.users'
    
    #BLB Branches
    blb_branch = fields.Many2one('client.branches', string='BLB Branch', required=True)