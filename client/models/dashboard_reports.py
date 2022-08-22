# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from datetime import datetime
from datetime import date
from dateutil.relativedelta import relativedelta
from odoo.exceptions import Warning as UserError
from odoo.exceptions import ValidationError
import string
import random


class data_summary_wizard(models.TransientModel):
    _name = 'client.data_summary_wizard'
    _description = 'Data Summary Wizard'

    client_id = fields.Many2one('client.client', string='Client')

    #Send Details for Data Summary to Populate Window 
    #@api.multi
    def get_dashboard_view(self):
        #Get + Run Select function
        self.env["client.data_summary"]._get_summary_select()
        #Return - videos Window
        view_id = self.env.ref('client.datasummary_pivot').id
        domain = ""
        context =""
        return {
            'name':'Data Summary Report',
            'view_type':'form',
            'view_mode':'pivot,graph',
            'res_model':'client.data_summary',
            'view_id': False,
            'type':'ir.actions.act_window',
            'target':'current',
            'context':context,
            'domain': domain
        }
    

class data_summary(models.Model):
    _name = 'client.data_summary'
    _description = 'Data Summary'
    _order = 'id desc'

    blb_branch = fields.Many2one('client.branches', string='Branch', readonly=True)
    file_status = fields.Char(string='File Status', readonly=True)
    files_count = fields.Integer(string='Count', readonly=True)

    #Select Method to Do Select Computations
    def _get_summary_select(self):
        #Delete all record from model
        self._remove_datarows()
        #Add New Data to Model
        data_summary_recordset = self.env['client.data_summary']
        all_states = ['fileopen','legal', 'blbregistry', 'blbregistry_report','survey', 'survey_rectify','planning','processing', 'valuation', 'lease', 'title', 'issue', 'done', 'cancel']
        #Query Database
        for state in all_states:
            select_query = """
                SELECT Count(id) As files_count, created_branch As blb_branch, state
                FROM client_client 
                WHERE state = '%s' 
                GROUP BY created_branch, state""" % (state)
            self._cr.execute(select_query)
            result_query = self.env.cr.dictfetchall()
            statename = self._get_statename(state)
            for row_dict in result_query:
                add_record = data_summary_recordset.create({
                    'blb_branch': row_dict['blb_branch'],
                    'file_status': statename,
                    'files_count': row_dict['files_count']
                })

    #Delete Rows
    def _remove_datarows(self):
        sql = "DELETE FROM client_data_summary WHERE id > 0"
        self.env.cr.execute(sql)

    #Get File State Name
    def _get_statename(self, state):
        statename = ""
        if state == "fileopen":
            statename = "File Opening Branch"
        elif state == "legal":
            statename ="Legal Office"
        elif state == "blbregistry":
            statename = "BLB Registry"
        elif state == "blbregistry_report":
            statename = "BLB Registry - Report Pending"
        elif state == "survey":
            statename = "Survey"
        elif state == "survey_rectify":
            statename = "Survey Rectification"
        elif state == "planning":
            statename = "Planning"
        elif state == "processing":
            statename = "Deed Plan Processing"
        elif state == "valuation":
            statename = "Valuation"
        elif state == "lease":
            statename = "Lease Committee"
        elif state == "title":
            statename = "Title Processing"
        elif state == "issue":
            statename = "Title Issued"
        elif state == "done":
            statename = "Completed"
        elif state == "cancel":
            statename = "Cancelled"
        return statename



    #Send Details for Data Summary to Populate Window 
    #@api.multi
    def get_dashboard_view(self):
        #Get + Run Select function
        self._get_summary_select()
        #Return - videos Window
        view_id = self.env.ref('client.datasummary_pivot').id
        domain = ""
        context =""
        return {
            'name':'Data Summary Report',
            'view_type':'form',
            'view_mode':'pivot,graph',
            'res_model':'client.data_summary',
            'view_id': False,
            'type':'ir.actions.act_window',
            'target':'current',
            'context':context,
            'domain': domain
        }



class locate_query(models.TransientModel):
    _name = 'client.locate_query'
    _description = 'Locate Query'
    
    coordinate_x = fields.Char(string="X-Coordinate", required=True)
    coordinate_y = fields.Char(string="Y-Coordinate", required=True)
    check_wetland = fields.Char(string="Wetland", compute="compute_lo", store=True)
    check_surveyed = fields.Char(string="Surveyed Kibanja", compute="compute_lo", store=True)
    check_blbland = fields.Char(string="BLB Land", compute="compute_lo", store=True)

    #Compute layers - 
    # @api.multi
    # @api.depends('coordinate_x','coordinate_y')
    def compute_lo(self):
        check_wetland = ''
        check_surveyed = ''
        check_blbland = ''
        for record in self:
            #Select Wetland layer in which the said plot falls.
            select_query = """SELECT wetland2014.wetland201 FROM wetland2014 WHERE ST_Contains (wetland2014.geom, (ST_SetSRID (ST_Point (%s,%s), 21096)))""" %  (record.coordinate_x,record.coordinate_y)
            #Select Surveyed Kibanja in which this point falls.
            select_query_k = """SELECT plot.name FROM usa.plot WHERE ST_Contains (plot.geom, (ST_SetSRID (ST_Point (%s,%s), 21096)))""" %  (record.coordinate_x,record.coordinate_y)
            #Check Surveyed Kibanja in which this point falls.
            select_query_b = """SELECT blb_land.tenure FROM blb_land WHERE ST_Contains (blb_land.geom, (ST_SetSRID (ST_Point (%s,%s), 21096)))""" %  (record.coordinate_x,record.coordinate_y)
            self._cr.execute(select_query)
            result_query = self.env.cr.dictfetchall()
            if result_query:
                for row_dicti in result_query:
                    check_wetland = row_dicti['wetland201']
            else:
                check_wetland = 'No!'
            record.check_wetland = check_wetland
            # raise ValidationError(_(check_wetland))
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
    

