from odoo import api, fields, models, SUPERUSER_ID, _


class PartnerInherit(models.Model):
    _inherit = 'res.partner'

    partner_history = fields.One2many('partner.history', 'partner_history_id', string='History')


class PartnerHistory(models.Model):
    _name = "partner.history"
    _order = 'id desc'

    partner_history_id = fields.Many2one('res.partner', string='History ID', invisible=True)
    order_ref = fields.Char(string='Order Reference')
    date = fields.Datetime(string='Date')
    price = fields.Float(string='Price')
    quantity = fields.Char(string='Quantity')


class PurchaseOrderInherit(models.Model):
    _inherit = "purchase.order"

    def button_confirm(self):
        res = super(PurchaseOrderInherit, self).button_confirm()
        for supplier in self.order_line:
            history = self.env['partner.history'].sudo().create({
                'order_ref': self.name,
                'date': self.date_order,
                'price': supplier.price_unit,
                'quantity': supplier.product_qty
            })
            supplier_search = self.env['res.partner'].sudo().search([('id', '=', supplier.partner_id.id)], limit=1)
            if supplier_search:
                supplier_search.write({'partner_history': [(4, history.id)]})
        return res


class SaleOrderInherit(models.Model):
    _inherit = "sale.order"

    def action_confirm(self):
        res = super(SaleOrderInherit, self).action_confirm()
        for supplier in self.order_line:
            history = self.env['partner.history'].sudo().create({
                'order_ref': self.name,
                'date': self.date_order,
                'price': supplier.price_unit,
                'quantity': supplier.product_uom_qty
            })
            supplier_search = self.env['res.partner'].sudo().search([('id', '=', supplier.order_partner_id.id)], limit=1)
            if supplier_search:
                supplier_search.write({'partner_history': [(4, history.id)]})
        return res
