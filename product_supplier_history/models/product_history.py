# ...................................... Importing Library And Directives ..............................................

from datetime import datetime, timedelta

from odoo import api, fields, models, SUPERUSER_ID, _
from odoo.exceptions import UserError, ValidationError
import logging

_logger = logging.getLogger(__name__)


# ...................................... End Of Importing Library And Directives .......................................

# .....................,..................... Class For Inheriting Product  ............................................

class productProductInherit(models.Model):
    _inherit = "product.product"

    product_history = fields.One2many('product.history', 'product_history_id')


# .....................,..................... New Class For Product History ............................................

class productHistory(models.Model):
    _name = "product.history"
    _order = 'id desc'

    product_history_id = fields.Many2one('product.product', string='History ID')
    order_ref = fields.Many2one('purchase.order', string='Order Reference')
    date = fields.Datetime(string='Date')
    supplier = fields.Many2one('res.partner', string='Supplier')
    price = fields.Float(string='Price')
    quantity = fields.Char(string='Quantity')


# ........................................... Class For Inheriting Product  ............................................

class purchaseOrderInherit(models.Model):
    _inherit = "purchase.order"

    def button_confirm(self):
        res = super(purchaseOrderInherit, self).button_confirm()
        for product in self.order_line:
            history = self.env['product.history'].sudo().create({
                'order_ref': self.id,
                'date': self.date_order,
                'supplier': self.partner_id.id,
                'price': product.price_unit,
                'quantity': product.product_qty
            })
            product_search = self.env['product.product'].sudo().search([('id', '=', product.product_id.id)], limit=1)
            if product_search:
                product_search.write({'product_history': [(4, history.id)]})
        return True
