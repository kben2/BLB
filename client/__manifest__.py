# -*- coding: utf-8 -*-
{
    'name': "Buganda Land Board - Clients",

    'summary': """
        Buganda Land Board - Clients Module""",

    'description': """
        This Module handles functionality related to the Buganda Land Board Clients
    """,

    'author': "Apsysis",
    'website': "https://www.apsysis.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/10.0/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'BLB',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base','web','layer'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'security/user_groups.xml',
        'views/views.xml',
        'views/dashboard_reports.xml',
        'views/templates.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],

    # whether Module is installable
    'installable': True,
    'auto-install': False,
}