
# ...................................... Importing Library And Directives ..............................................

from datetime import datetime, timedelta

from odoo import api, fields, models, SUPERUSER_ID, _
from odoo.exceptions import UserError, ValidationError
import logging
_logger = logging.getLogger(__name__)

# ...................................... End Of Importing Library And Directives .......................................

# .....................,................ Class For Inheriting Sales Modules ............................................

class SaleOrders(models.Model):
    _inherit = "sale.order"

    repair_id = fields.Many2one('car.repair', 'Repair ID')

# ........................................ Confirm Button In Sale Order.................................................

    def action_confirm(self):
        res = super(SaleOrders, self).action_confirm()
        car_repair = self.env['car.repair'].sudo().search([('sale_order_id', '=', self.name)])
        if car_repair:
            car_repair.update({'state': 'inventory_move'})
        return True

# ...................................... Create Invoice Button In Sale Order............................................

    def create_invoices(self):

        res = super(SaleOrders, self).create_invoices()
        car_repair = self.env['car.repair'].sudo().search([('sale_order_id', '=', self.name)])
        if car_repair:
            car_repair.update({'state': 'invoice'})
        return True

# ...................................... End Of Class Inheriting Sales Modules .........................................

# ....................................... Class For Inheriting Partner Modules .........................................

class Partner_inherit(models.Model):
    _inherit='res.partner'

    res_aprt = fields.Many2one('res.partner', string='Driver Name')

    drive = fields.Many2many('res.partner','res_partner_rel','count', 'name',string='Drivers Name')
    # drive = fields.Many2many('res.partner', string='Drivers Name')

    is_vendos = fields.Boolean('Is Vendor')

    count=fields.Integer('Vehicles',compute='set_count')
    # repair_count=fields.Integer('Repair Services',compute='set_repair_count')

    # @api.model
    # def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
    #     res = super(Partner_inherit, self).fields_view_get(view_id, view_type, toolbar=toolbar, submenu=False)
    #     if self.env.context.get('supplier'):
    #         a = 10
    #     if self._context.get('supplier'):
    #         a=10
    #     if view_type == 'form' and res.get('toolbar', False):
    #         install_id = self.env.ref('base.action_server_module_immediate_install').id
    #         action = [rec for rec in res['toolbar']['action'] if rec.get('id', False) != install_id]
    #         res['toolbar'] = {'action': action}
    #     return res

    # def set_repair_count(self):
    #     search_res_id = self.env['car.repair'].search([('client','=',self.id)])
    #     self.repair_count = len(search_res_id)

    def show_service(self):
        return {
                'name': ('Repair Services'),
                'type': 'ir.actions.act_window',
                'view_type': 'form',
                'view_mode': 'tree,form',
                'res_model': 'car.repair',
                'domain': [('client', '=', self.id)]
                }

    def set_count(self):
        search_res_id = self.env['fleet.vehicle'].search([('driver_id','=',self.id)])
        self.count = len(search_res_id)

    def show_vehicles(self):
        return {
                'name': ('Vehicles'),
                'type': 'ir.actions.act_window',
                'view_type': 'form',
                'view_mode': 'tree,form',
                'res_model': 'fleet.vehicle',
                'domain': [('driver_id', '=', self.id)]
                }

# ....................................... End Of Class Inheriting Partner Modules ......................................

# ....................................... Class For Inheriting Fleet Modules ...........................................

class FleetVehicle(models.Model):
    _inherit='fleet.vehicle'

    count = fields.Integer('Services', compute='set_count')
    so_count = fields.Integer('Services', compute='set_so_count')

    def set_count(self):
        search_res_id = self.env['car.repair'].search([('client','=',self.driver_id.id)])
        self.count = len(search_res_id)

    def show_service(self):
        return {
                'name': ('Repair Services'),
                'type': 'ir.actions.act_window',
                'view_type': 'form',
                'view_mode': 'tree,form',
                'res_model': 'car.repair',
                'domain': [('client', '=', self.driver_id.id)]
                }

    def set_so_count(self):
        search_res_id = self.env['sale.order'].search([('partner_id','=',self.driver_id.id),
                                                       ('repair_id.client', '=', self.driver_id.id)])
        self.so_count = len(search_res_id)

    def show_so(self):
        return {
                'name': ('Repair Services'),
                'type': 'ir.actions.act_window',
                'view_type': 'form',
                'view_mode': 'tree,form',
                'res_model': 'sale.order',
                'domain': [('partner_id', '=', self.driver_id.id),('repair_id.client', '=', self.driver_id.id)]
                }

# ................................ End Of Class Inheriting Fleet Modules ..............................................