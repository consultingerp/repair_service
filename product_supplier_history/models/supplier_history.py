from odoo import api, fields, models, SUPERUSER_ID, _


class VendorInherit(models.Model):
    _inherit = 'res.partner'

    supplier_history = fields.One2many('supplier.history', 'supplier_history_id', string='History')


class SupplierHistory(models.Model):
    _name = "supplier.history"
    _order = 'id desc'

    supplier_history_id = fields.Many2one('res.partner', string='History ID')
    order_ref = fields.Many2one('purchase.order', string='Order Reference')
    date = fields.Datetime(string='Date')
    # supplier = fields.Many2one('res.partner', string='Supplier')
    price = fields.Float(string='Price')
    quantity = fields.Char(string='Quantity')


class PurchaseOrderInherit(models.Model):
    _inherit = "purchase.order"

    def button_confirm(self):
        res = super(PurchaseOrderInherit, self).button_confirm()
        for supplier in self.order_line:
            history = self.env['supplier.history'].sudo().create({
                'order_ref': self.id,
                'date': self.date_order,
                # 'supplier': self.partner_id.id,
                'price': supplier.price_unit,
                'quantity': supplier.product_qty
            })
            supplier_search = self.env['res.partner'].sudo().search([('id', '=', supplier.partner_id.id)], limit=1)
            if supplier_search:
                supplier_search.write({'supplier_history': [(4, history.id)]})
        return res


class SaleOrderInherit(models.Model):
    _inherit = "sale.order"

    def button_confirm(self):
        res = super(SaleOrderInherit, self).action_confirm()
        for supplier in self.order_line:
            history = self.env['supplier.history'].sudo().create({
                'order_ref': self.id,
                'date': self.date_order,
                # 'supplier': self.partner_id.id,
                'price': supplier.price_unit,
                'quantity': supplier.product_qty
            })
            supplier_search = self.env['res.partner'].sudo().search([('id', '=', supplier.partner_id.id)], limit=1)
            if supplier_search:
                supplier_search.write({'supplier_history': [(4, history.id)]})
        return res
