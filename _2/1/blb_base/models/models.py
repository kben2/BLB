# -*- coding: utf-8 -*-

from odoo import models, fields, api, tools, _
from datetime import datetime
from datetime import date
from dateutil.relativedelta import relativedelta
from datetime import timedelta
from odoo.exceptions import Warning as UserError
from odoo.exceptions import ValidationError
from odoo.exceptions import AccessDenied, UserError
import smtplib
import subprocess



class blb_base(models.Model):
    _name = 'blb_base.blb_base'
    _description = 'BLB - Base Module'

    name = fields.Char()
    value = fields.Integer()
    value2 = fields.Float(compute="_value_pc", store=True)
    description = fields.Text()


class branches(models.Model):
    _name = 'blb_base.branches'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'BLB Branches'
    _order = 'name asc'

    name = fields.Char(string="Branch Name", required=True)
    active = fields.Boolean(default=True)

    _sql_constraints = [
        ('name_unique',
         'UNIQUE(name)',
         "The Branch name must be unique")
    ]

class blb_department(models.Model):
    _name = 'blb_base.blb_department'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'BLB - Departments'
    _order = 'name asc'

    name = fields.Char(string="Department", required=True)
    active = fields.Boolean(default=True)

    _sql_constraints = [
        ('name_unique',
         'UNIQUE(name)',
         "The Department name must be unique")
    ]


class blb_unit(models.Model):
    _name = 'blb_base.blb_unit'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'BLB - Units'
    _order = 'name asc'

    name = fields.Char(string="Unit", required=True)
    department_id = fields.Many2one('blb_base.blb_department', required=True, string='Department')
    active = fields.Boolean(default=True)

    _sql_constraints = [
        ('name_unique',
         'UNIQUE(name)',
         "The Unit name must be unique")
    ]


class blb_user_branches(models.Model):
    _inherit = 'res.users'
    
    #BLB Branches
    blb_branch = fields.Many2one('blb_base.branches', string='Branch', required=True)

    #BLB Department
    blb_department = fields.Many2many(
        comodel_name='blb_base.blb_department', 
        column1='user_department_id',
        column2='department_id',
        relation='user_departments_rel', string='Department')
    #BLB Unit
    blb_unit = fields.Many2many(
        comodel_name='blb_base.blb_unit', 
        column1='user_unit_id',
        column2='unit_id',
        relation='user_units_rel', string='Unit')
    #department_selected = fields.Boolean(string="Department Selected", default=False)
    blb_dept_unit = fields.Char(string='Department/Unit')

    #Check for Department
    @api.onchange('blb_department')
    def _onchange_blb_department(self):
        #Check if a blb_department is selected
        departments_list = []
        domain = ''
        for rec in self:
            if len(rec.blb_department) > 0:
                #rec.department_selected = True
                for dept in rec.blb_department:
                    deptid = str(dept.id)
                    deptid_list = deptid.split("_")
                    #raise ValidationError(_( str(deptid_list[1]) + "==" + str(dept.id) ))
                    departments_list.append(int(deptid_list[1]))
                #Domain for blb_unit
                domain = {'blb_unit':  [('department_id', 'in', departments_list)]}                
            #else:
                #rec.department_selected = False        
        return {'domain': domain}


class notifications(models.Model):
    _name = 'blb_base.notifications'
    _description = 'BLB Notifications'
    _order = 'id desc'

    user_id = fields.Many2one('res.users', string='BLB User', required=True)
    addressed_to = fields.Char(string='Addressed to', required=True)
    notification_subject = fields.Char(string='Subject', required=True)
    notification_details = fields.Text(string='Notification Details', required=True)  

    #Send SMS notification
    def test_send_sms(self):
        #Send SMS
        #os.system("php /var/www/html/SMSEmail/sms.php %s,%s" % (addressed_to, notification_details))
        addressed_to = '0703048397'
        notification_details = "Testing Msg for BLB!"
        subprocess.call(["php","-f","/var/www/html/SMSEmail/sms.php", addressed_to, notification_details])
        #Thats all ....

    #Send System notification 
    def _send_system_notification(self,user_id,notification_subject,notification_details):
        #Get User-Patner ID
        user_rec = self.env['res.users'].search([('id', '=', user_id)])        
        #raise ValidationError(_(user_rec.partner_id.id))
        #Send Direct Notification/Comment
        channel = self.env['mail.channel'].channel_get([user_rec.partner_id.id])
        channel_id = self.env['mail.channel'].browse(channel["id"])
        channel_id.message_post(body=(notification_details), message_type='notification', subtype_xmlid='mail.mt_comment')
        #Send Inbox Message
        #notification_ids = [(0, 0, { 'res_partner_id': user.partner_id.id, 'notification_type': 'inbox' }) for user in users if users]
        notification_ids = [(0, 0, { 'res_partner_id': user_rec.partner_id.id, 'notification_type': 'inbox' })]
        self.env['mail.message'].create({
            'message_type': "notification",
            'body': notification_details,
            'subject': notification_subject,
            'partner_ids': [(4, user_rec.partner_id.id)],
            'model': self._name,
            'res_id': self.id,
            'notification_ids': notification_ids,
            'author_id': self.env.user.partner_id and self.env.user.partner_id.id
        })

    #Send SMS notification
    def _send_sms(self,user_id,addressed_to,notification_details):
        #Send SMS
        subprocess.call(["php","-f","/var/www/html/SMSEmail/sms.php", addressed_to, notification_details])
        details = notification_details
        #Thats all ....

    #Send Email notification 
    def _send_email(self,user_id,addressed_to,notification_subject,notification_details):        
        #Send Email
        email_from = "BLB - LMIS"
        email_body = "\r\n".join((
            "From: %s" % email_from,
            "To: %s" % addressed_to,
            "Subject: %s" % notification_subject ,
            "",
            notification_details
        ))
        try:
            smtp_server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
            smtp_server.ehlo()
            smtp_server.login('kriptac2@gmail.com', 'Working2@2')
            smtp_server.sendmail('BLB - LMIS', addressed_to, email_body)
            smtp_server.close()
            print ("Email sent successfully!")
        except Exception as ex:
            print ("Something went wrong...", ex)