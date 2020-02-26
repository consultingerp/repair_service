from odoo import api, fields, models, SUPERUSER_ID, _


class CurrencyRatePO(models.Model):
    _inherit = 'purchase.order'

    # currency_rates = fields.Char('res.currency.rates', related='currency_id.rate')

    def action_view_currency(self):
        action = self.env.ref('base.action_currency_all_form')
        result = action.read()[0]
        return result


class CurrencyRateINV(models.Model):
    _inherit = 'account.move'

    def action_view_currency(self):
        action = self.env.ref('base.action_currency_all_form')
        result = action.read()[0]
        return result
