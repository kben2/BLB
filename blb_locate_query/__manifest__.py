# -*- coding: utf-8 -*-
{
    'name': "BLB - Locate Query",

    'summary': """
        BLB - Searching GIS data""",

    'description': """
        This Module handles BLB - Searching GIS Data
    """,

    'author': "Apsysis",
    'website': "http://www.apsysis.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/10.0/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'BLB',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base','web'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        #'security/user_groups.xml',
        'views/views.xml',
        #'views/dashboard_reports.xml',
        #'views/templates.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],

    # whether Module is installable
    'installable': True,
    'auto-install': False,
}