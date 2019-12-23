# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Repair Service',
    'version': '1.1',
    'category': 'Repairs',
    'summary': 'Car Diagnosis Machinery',
    'description': """
This module will create Car Diagnosis and Assign Technicians for it.
    """,
    'depends': ['base','stock','sale','product'],
    'data': [
        'security/repair_security.xml',
        'security/ir.model.access.csv',
        'views/car_repair_view.xml',
        'views/vehicle_form.xml',
        'views/digital_sign_view.xml',
    ],
    'demo': [
        # 'data/sale_demo.xml',
        # 'data/product_product_demo.xml',
    ],
    'qweb': [
        "static/src/xml/digital_sign.xml",
    ],
    'installable': True,
    'auto_install': False
}