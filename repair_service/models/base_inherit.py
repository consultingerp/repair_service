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

    repair_count = fields.Integer('Repair Count', compute='_repair_count')
    sale_count = fields.Integer('Sale Order Count', compute='_sale_order_count')
    inv_count = fields.Integer('Invoice Count', compute='_count_invoices')
    res_company = fields.Many2one('res.partner', string="Company")
    driver_ids = fields.Many2many('res.partner', 'rel_partner_fleet', 'fleet_id', 'partner_id', "Drivers")
    repair_ids = fields.Many2many('car.repair', 'rel_carrepair_fleet', 'fleet_id', 'car_id', "Repair Service ID", store=True, readonly=True)

    def name_get(self):
        result = []
        for record in self:
            result.append((record.id, '%s' % record.license_plate))
        return result

    def _repair_count(self):
        if self.repair_ids:
            for record in self.repair_ids:
                repair_search = self.env['car.repair'].search([('subject', '=', record.display_name)])
                if repair_search:
                    self.repair_count = len(self.repair_ids)
                else:
                    self.repair_count = 00
        else:
            self.repair_count = 00

    def _sale_order_count(self):
        sale_vals = []
        if self.repair_ids:
            for record in self.repair_ids:
                repair_search = self.env['car.repair'].search([('subject', '=', record.display_name)])
                for rec in repair_search:
                    sale_order = self.env['sale.order'].search([('repair_id', '=', rec.id)])
                    if sale_order:
                        sale_vals.append(sale_order.id)
                        self.sale_count = len(sale_vals)
                    else:
                        self.sale_count = 00
        else:
            self.sale_count = 00

    def _count_invoices(self):
        vals = []
        if self.repair_ids:
            for record in self.repair_ids:
                repair_search = self.env['car.repair'].search([('subject', '=', record.display_name)])
                for rec in repair_search:
                    sale_order = self.env['sale.order'].search([('repair_id', '=', rec.id)])
                    if sale_order:
                        for recs in sale_order:
                            account_inv = self.env['account.move'].search([('invoice_origin', '=', recs.name)])
                            if account_inv:
                                for records in account_inv:
                                    vals.append(records.id)
                                self.inv_count = len(vals)
                            else:
                                self.inv_count = 00
                    else:
                        self.inv_count = 00
        else:
            self.inv_count = 00

    def action_repair_service(self):
        vals = []
        for record in self.repair_ids:
            repair_search = self.env['car.repair'].search([('subject', '=', record.display_name)])
            for car_id in repair_search:
                vals.append(car_id.id)
                self.repair_count = len(self.repair_ids)

        res = {
            'name': 'Repair Services',
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'car.repair',
            'domain': [('id', '=', vals)],
            'target': 'current',
        }
        return res

    def action_sale_order(self):
        sale_vals = []
        for record in self.repair_ids:
            repair_search = self.env['car.repair'].search([('subject', '=', record.display_name)])
            for rec in repair_search:
                sale_order = self.env['sale.order'].search([('repair_id', '=', rec.id)])
                sale_vals.append(sale_order.id)
                self.sale_count = len(sale_vals)

        res = {
            'name': 'Sale Order',
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'sale.order',
            'domain': [('id', '=', sale_vals)],
            'target': 'current',
        }
        return res

    def action_view_invoices(self):
        vals = []
        if self.repair_ids:
            for record in self.repair_ids:
                repair_search = self.env['car.repair'].search([('subject', '=', record.display_name)])
                for rec in repair_search:
                    sale_order = self.env['sale.order'].search([('repair_id', '=', rec.id)])
                    if sale_order:
                        for recs in sale_order:
                            account_inv = self.env['account.move'].search([('invoice_origin', '=', recs.name)])
                            if account_inv:
                                for records in account_inv:
                                    vals.append(records.id)
                            else:
                                self.inv_count = 00
                    else:
                        self.inv_count = 00
        else:
            self.inv_count = 00

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

    @api.onchange('res_company')
    def on_change_company_driver(self):
        if self.res_company:
            search_driver = self.env['res.partner'].search(
                [('parent_id', '=', self.res_company.id), ('driver_bool', '=', True)])
            return {'domain': {'driver_ids': [('id', 'in', search_driver.ids)]}}
        else:
            return

    # def set_count(self):
    #     search_res_id = self.env['car.repair'].search([('client', '=', self.driver_id.id)])
    #     self.count = len(search_res_id)

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

    # def set_so_count(self):
    #     search_res_id = self.env['sale.order'].search([('partner_id', '=', self.driver_id.id),
    #                                                    ('repair_id.client', '=', self.driver_id.id)])
    #     self.so_count = len(search_res_id)

    def show_so(self):
        return {
            'name': 'Sale Orders',
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
