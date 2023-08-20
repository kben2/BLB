# -*- coding: utf-8 -*-
{
    'name': "Buganda Land Board - Valuation",

    'summary': """
        Buganda Land Board - Valuation Module""",

    'description': """
       This Module handles functionality related to the Buganda Land - Valuation Deparment Processes
    """,

    'author': "Apsysis",
    'website': "https://www.apsysis.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/10.0/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'BLB',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base','mail'],

    # always loaded
    'data': [
        #'data/blb_valuation.valuation_table.csv',
        # 'security/ir.model.access.csv',
        'views/views.xml',
        'views/valuation_table.xml',
        'views/templates.xml', 
        'report/report.xml',
        'report/report_groundrent_revision.xml',
        'report/report_valuation_calculator.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],

    # whether Module is installable
    'installable': True,
    'auto-install': False,
}
