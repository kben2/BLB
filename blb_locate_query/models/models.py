# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
import psycopg2
from psycopg2 import connect
from datetime import datetime
from datetime import date
from dateutil.relativedelta import relativedelta
from odoo.exceptions import Warning as UserError
from odoo.exceptions import ValidationError
from odoo.exceptions import AccessDenied, UserError
from odoo.tools.parse_version import parse_version
from odoo.tools.misc import topological_sort
import string
import random
import csv
#from ezdxf.enums import TextEntityAlignment
#from ezdxf import zoom,units
import math


class locate_query(models.Model):
	_name = 'blb_client.locate_query'
	_description = 'Locate Query'
	
	latitude = fields.Char(string="X-Coordinate",compute='_compute_block', store=False)
	longitude = fields.Char(string="Y-Coordinate",compute='_compute_block', store=False)
	northings = fields.Char(string="Northings")
	eastings = fields.Char(string="Eastings")
	srs = fields.Selection([
		('21096', "UTM Zone 36N"),
		('21036', "UTM Zone 36S"),
		('4326', "WGS 84"),
		('32636', "ITRF Zone 36N"),
		('32736', "ITRF Zone 36S"),
	], string="Coordinate System")
	id = fields.Char(string="ID")
	name = fields.Char(string="Name")
	check_wetland = fields.Char(string="Wetland")
	check_blbland = fields.Char(string="BLB Land",compute='_compute_block', store=False)
	check_reserve = fields.Char(string="Reserve",compute='_compute_block', store=False)
	
	
	@api.depends('eastings','northings')
	def _compute_block(self):
		check_wetland = ''
		check_reserve = ''
		check_blbland = ''
		longitude = ''
		latitude = ''
		for rec in self:
			if rec.eastings and rec.northings:
				if rec.srs == False:
					raise ValidationError(_('Please select the Coordinates System'))
				elif rec.srs != False:
						# Establish a connection to the PostgreSQL database
					conn = psycopg2.connect(database="postgres", user="postgres", password="admin", host="127.0.0.1", port="5432")

					# Create a cursor object
					cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
					cur = conn.cursor()
					cur.execute("""SELECT id,ST_X((ST_Transform(ST_SetSRID(ST_MakePoint(%s,%s),%s), 4326))) as x,ST_Y((ST_Transform(ST_SetSRID(ST_MakePoint(%s,%s),%s), 4326))) as y
											FROM blbland
											WHERE ST_Contains((ST_Transform(geom, %s)), ST_SetSRID(ST_MakePoint(%s,%s),%s))
											""" %  (rec.eastings,rec.northings,rec.srs,rec.eastings,rec.northings,rec.srs,rec.srs,rec.eastings,rec.northings,rec.srs))
					result_query = cur.fetchall()
					if result_query:
						check_blbland = "This position is within BLB jurisdiction!" 
						latitude = result_query[0][2]
						longitude = result_query[0][1]
					else:
						check_blbland ="This search is outside our land!"
					cur.execute("""SELECT id
											FROM wetland
											WHERE ST_Contains((ST_Transform(geom, %s)), ST_SetSRID(ST_MakePoint(%s,%s),%s))
											""" %  (rec.srs,rec.eastings,rec.northings,rec.srs))
					result_query_r = cur.fetchall()
					if result_query_r:
						check_wetland = "This position falls in a wetland!"
					else:
						check_wetland ="This search is outside the wetland!"
			rec.check_blbland = check_blbland
			rec.check_wetland = check_wetland
			rec.latitude = latitude
			rec.longitude = longitude
		return True