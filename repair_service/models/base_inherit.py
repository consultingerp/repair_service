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

    repair_id = fields.Many2one('car.repair', 'Repair Subject')

    # ........................................ Confirm Button In Sale Order.................................................

    def action_confirm(self):
        res = super(SaleOrders, self).action_confirm()
        car_repair = self.env['car.repair'].sudo().search([('sale_order_id', '=', self.name)])
        if car_repair:
            car_repair.update({'state': 'inventory_move'})
        stock_obj = self.env['stock.picking'].sudo().search([('origin', '=', self.name)])
        if stock_obj:
            for stock in stock_obj:
                stock.update({'car_obj': self.repair_id.id})
        return res

    # ...................................... Create Invoice Button In Sale Order............................................

    def create_invoices(self):

        res = super(SaleOrders, self).create_invoices()
        car_repair = self.env['car.repair'].sudo().search([('sale_order_id', '=', self.name)])
        if car_repair:
            car_repair.update({'state': 'invoice'})
        return res


# ...................................... End Of Class Inheriting Sales Modules .........................................

# ....................................... Class For Inheriting Partner Modules .........................................

class Partner_inherit(models.Model):
    _inherit = 'res.partner'

    drive = fields.Many2many('res.partner', 'res_partner_rel', 'count', 'name', string=' ')
    driver_bool = fields.Boolean('Driver')
    is_vendos = fields.Boolean('Is Vendor')
    count = fields.Integer('Vehicles', compute='set_count')


    @api.model_create_multi
    def create(self, vals_list):
        res = super(Partner_inherit, self).create(vals_list)
        _logger.info("--------------------------------res partner ------------------------------", res)
        if res.driver_bool == True:
            partner = self.env['res.partner'].search([('id', '=', res.parent_id.id)])
            if partner:
                partner.write({'drive': [(4, res.id)]})
        return res

    def show_service(self):
        return {
            'name': 'Repair Services',
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'car.repair',
            'domain': [('client', '=', self.id)]
        }

    def set_count(self):
        search_res_id = self.env['fleet.vehicle'].search([('driver_id', '=', self.id)])
        self.count = len(search_res_id)

    def show_vehicles(self):
        return {
            'name': 'Vehicles',
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'fleet.vehicle',
            'domain': [('driver_id', '=', self.id)]
        }


# ....................................... End Of Class Inheriting Partner Modules ......................................

# ....................................... Class For Inheriting Fleet Modules ...........................................

class FleetVehicles(models.Model):
    _inherit = 'fleet.vehicle'

    count = fields.Integer('Services', compute='set_count')
    so_count = fields.Integer('Services', compute='set_so_count')
    res_company = fields.Many2one('res.partner', string="Company")
    driver_ids = fields.Many2many('res.partner', 'rel_partner_fleet', 'fleet_id', 'partner_id', "Drivers")
    repair_ids = fields.Many2many('car.repair', 'rel_carrepair_fleet', 'fleet_id', 'car_id', "Repair Service ID")

    def name_get(self):
        result = []
        for record in self:
            result.append((record.id, '%s' % record.license_plate))
        return result

    # ........................................... Function for Sales Order Button .......................................

    def action_view_sale_order(self):
        repair_id = self.env['car.repair'].search([('subject', '=', self.repair_id.subject)])
        res = {
            'name': 'Sale Order',
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'sale.order',
            'res_id': sale_order_id.id,
            'target': 'current',
        }
        return res

        # ............................................. End of Function for Sales Order Button ..............................

        # ........................................... Function for Invoice Button .......................................

    def action_view_invoices(self):
        sale_order_id = self.env['sale.order'].search([('name', '=', self.sale_order_id)])
        account_inv = self.env['account.move'].search([('invoice_origin', '=', sale_order_id.name)])
        vals = []
        if account_inv:
            for rec in account_inv:
                vals.append(rec.id)

        res = {
            'name': 'Account Invoice',
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'account.move',
            'domain': [('id', '=', vals)],
            'target': 'current',
        }
        return res

        # ............................................. End of Function for Invoice Button ..............................

    @api.onchange('res_company')
    def on_change_company_driver(self):
        if self.res_company:
            search_driver = self.env['res.partner'].search(
                [('parent_id', '=', self.res_company.id), ('driver_bool', '=', True)])
            return {'domain': {'driver_ids': [('id', 'in', search_driver.ids)]}}
        else:
            return

    def set_count(self):
        search_res_id = self.env['car.repair'].search([('client', '=', self.driver_id.id)])
        self.count = len(search_res_id)

    def show_service(self):
        context = dict(self.env.context)
        context.update({
            'default_client': self.res_company.id,
            'default_contact_name': self.res_company.name,
            'default_email': self.res_company.email,
            'default_phone': self.res_company.phone,
            'default_mobile': self.res_company.mobile
        })
        return {
            'name': 'Repair Services',
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'car.repair',
            'domain': [('client', '=', self.driver_id.id)],
            "context": context

        }

    def set_so_count(self):
        search_res_id = self.env['sale.order'].search([('partner_id', '=', self.driver_id.id),
                                                       ('repair_id.client', '=', self.driver_id.id)])
        self.so_count = len(search_res_id)

    def show_so(self):
        return {
            'name': ('Sale Orders'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'sale.order',
            'domain': [('partner_id', '=', self.driver_id.id), ('repair_id.client', '=', self.driver_id.id)],
            "context": dict(self._context, create=False),
        }


# ................................ End Of Class Inheriting Fleet Modules ..............................................

# ....................................... Class For Inheriting Stock Picking Modules ...................................

class StockPickingRepair(models.Model):
    _inherit = 'stock.picking'

    car_obj = fields.Many2one('car.repair', 'Repair ID')

    def button_validate(self):
        res = super(StockPickingRepair, self).button_validate()
        car_repair = self.env['car.repair'].sudo().search([('id', '=', self.car_obj.id)])
        if car_repair:
            car_repair.update({'state': 'work_order'})

            for repair_task in car_repair.task_line:
                work_obj = self.env['work.order'].sudo().create({
                    'work_order': repair_task.repair_id.id,
                    'receiving_tech': repair_task.repair_id.receiving_tech.id,
                    'task_name': repair_task.task.name
                })
        return res

    def show_so(self):
        return {
            'name': ('Repair Services'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'sale.order',
            'domain': [('partner_id', '=', self.driver_id.id), ('repair_id.client', '=', self.driver_id.id)]
        }

# ................................ End Of Class Inheriting Stock Picking Modules .......................................
