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


class productTemplateInherit(models.Model):
    _inherit = "product.template"

    product_history_tmpl = fields.One2many('product.history', 'product_history_id_tmpl')


# .....................,..................... New Class For Product History ............................................

class productHistory(models.Model):
    _name = "product.history"
    _order = 'id desc'

    product_history_id = fields.Many2one('product.product', string='Product Variants History ID', invisible=True)
    product_history_id_tmpl = fields.Many2one('product.template', string='Product Template History ID', invisible=True)
    order_ref = fields.Char(string='Order Reference')
    date = fields.Datetime(string='Date')
    supplier = fields.Many2one('res.partner', string='Supplier')
    price = fields.Float(string='Price')
    quantity = fields.Char(string='Quantity')


# ........................................... Class For Inheriting Product  ............................................

class PurchaseOrderInherit(models.Model):
    _inherit = "purchase.order"

    def button_confirm(self):
        res = super(PurchaseOrderInherit, self).button_confirm()
        for product in self.order_line:
            history = self.env['product.history'].sudo().create({
                'order_ref': self.name,
                'date': self.date_order,
                'supplier': self.partner_id.id,
                'price': product.price_unit,
                'quantity': product.product_qty
            })
            product_search = self.env['product.product'].sudo().search([('id', '=', product.product_id.id)], limit=1)
            product_search_tmpl = self.env['product.template'].sudo().search([('id', '=', product_search.product_tmpl_id.id)], limit=1)
            if product_search:
                product_search.write({'product_history': [(4, history.id)]})
            if product_search_tmpl:
                product_search_tmpl.write({'product_history_tmpl': [(4, history.id)]})
        return res


class SaleOrderInherit(models.Model):
    _inherit = 'sale.order'

    def action_confirm(self):
        res = super(SaleOrderInherit, self).action_confirm()
        for product in self.order_line:
            history = self.env['product.history'].sudo().create({
                'order_ref': self.name,
                'date': self.date_order,
                'supplier': self.partner_id.id,
                'price': product.price_unit,
                'quantity': product.product_uom_qty
            })
            product_search = self.env['product.product'].sudo().search([('id', '=', product.product_id.id)], limit=1)
            product_search_tmpl = self.env['product.template'].sudo().search([('id', '=', product_search.product_tmpl_id.id)], limit=1)
            if product_search:
                product_search.write({'product_history': [(4, history.id)]})
            if product_search_tmpl:
                product_search_tmpl.write({'product_history_tmpl': [(4, history.id)]})
        return res
