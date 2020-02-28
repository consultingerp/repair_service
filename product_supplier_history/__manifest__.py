# -*- coding: utf-8 -*-

{
    'name': 'Car Repair - Product/Supplier History',
    'version': '1.3',
    'category': 'Repairs',
    'summary': 'This module shows you the history of a particular product and history of a particular Supplier.',
    'description': """
This module have new customization of New Car Repair Service .
    """,
    'depends': ['base', 'stock', 'sale', 'product', 'mail', 'purchase', 'fleet'],
    'data': [
        'security/ir.model.access.csv',
        # 'views/product_history_view.xml',
        'views/currency_rates_view.xml',
        'views/supplier_history_view.xml',
        'views/sale_order_view.xml',
    ],
    'demo': [
    ],
    'qweb': [
    ],
    'installable': True,
    'auto_install': False
}