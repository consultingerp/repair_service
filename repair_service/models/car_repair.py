
# ................................. Importing Library And Directives ....................................

from datetime import datetime, timedelta

from odoo import api, fields, models, SUPERUSER_ID, _
from odoo.exceptions import UserError, ValidationError
import logging
_logger = logging.getLogger(__name__)

# ................................... End Of Importing Library And Directives ...........................

# .............................. Class For Car Repair Diagnosis ......................................

class CarRepair(models.Model):
    _name = "car.repair"
    # _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin', 'utm.mixin']
    _description = "Car Repair"
    _rec_name = 'subject'
    # _order = 'date_order desc, id desc'
    _check_company_auto = True

    state = fields.Selection([('diagnosis', 'Car Diagnosis'), ('send_quotation', 'Send Quotation'),
                              ('inventory_move', 'Inventory Move'), ('work_order', 'Work Order'),
                              ('inspections','Inspections'), ('invoice', 'Invoice')], 'Status', readonly=True, default='diagnosis')



    subject = fields.Char(string='Subject')
    receiving_tech = fields.Many2one('res.users', string='Receiving Technician', default=lambda self: self.env.user)
    priority = fields.Selection([('0', 'Not urgent'), ('1', 'Normal'), ('2', 'Urgent'), ('3', 'Very Urgent')],
                                'Priority',
                                readonly=True, default='1')
    receipt_date = fields.Date(string='Date Of Receipt')
    scheduled_service_date = fields.Date(string='Scheduled Service Date')
    rma_number = fields.Integer(string='RMA Number')

    client = fields.Many2one('res.partner', string='Client')
    contact_name = fields.Char(string='Contact name')
    email = fields.Char(string='Email')
    phone = fields.Char(string='Phone')
    mobile = fields.Char(string='Mobile')
    contact_no = fields.Char(string='Contact No')

    description = fields.Text('Note')

    image = fields.Many2many('ir.attachment', string="Image")
    note = fields.Text(string='Descriptions/Remark for Pictures')
    digital_signature = fields.Binary('Signature')

    task_line = fields.One2many('repair.task.line', 'task')

    part_line = fields.One2many('repair.part.line', 'part_line')

    service_line = fields.One2many('repair.service.line', 'service_line')

    assign_technicians = fields.Many2many('res.users', string='Technicians')

    sale_order_id = fields.Char('Sale Order ID')

    # @api.model
    def action_view_inventory_move(self):
        view = self.env.ref('stock.view_picking_form')
        trees = self.env.ref('stock.vpicktree')
        # user = self.env['car.repair'].browse(self._context.get('active_ids'))
        # act = self.env.ref('repair_service.action_view_timecard')
        res = {
            'name': 'Inventory Move',
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'stock.picking',
            'views': [(trees.id, 'tree'), (view.id, 'form')],
            'view_id': view.id,
            'target': 'current',
            # 'res_id': self.timecard_many2o.id,
            'context': {'search_default_origin': self.sale_order_id},
        }
        return res



    def send_quotation(self):
        sale_order = self.env['sale.order'].sudo().create({
            'partner_id': self.client.id,
            'repair_id': self.id
        })
        part_and_service = []
        sales_order_line = []

        for x in self.part_line:
            a=x.part

        for part in self.part_line:
            product_obj = self.env['product.product'].sudo().search([('id', '=', part.part.product_variant_id.id)])
            vals_order_line = {
                'order_id': sale_order.id,
                'product_id': product_obj.id,
                'name': product_obj.name,
                'product_uom_qty': part.part_qty,
                'price_unit': product_obj.lst_price
            }
            orders_line = self.env['sale.order.line'].sudo().create(vals_order_line)
            sales_order_line.append(orders_line.id)
        for service in self.service_line:
            service_obj = self.env['product.product'].sudo().search([('id', '=', service.service.product_variant_id.id)])
            vals_order_line = {
                'order_id': sale_order.id,
                'product_id': service_obj.id,
                'name': service_obj.name,
                'product_uom_qty': service.service_qty,
                'price_unit': service_obj.lst_price
            }
            orders_line = self.env['sale.order.line'].sudo().create(vals_order_line)
            sales_order_line.append(orders_line.id)
        sale_order.write({'order_line': [(6, 0, sales_order_line)]})
        self.update({'state': 'send_quotation', 'sale_order_id':sale_order.name})
        return True



# ................................ End Of Class Car Repair ............................................


# ................................ Class For Repair Task List ..........................................

class RepairTaskLine(models.Model):
    _name = "repair.task.line"
    # _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin', 'utm.mixin']
    _description = "Repair Task"
    # _order = 'date_order desc, id desc'
    _check_company_auto = True

    remark = fields.Char('Remark')
    document = fields.Binary('Document')

    task = fields.Many2one('task.name', 'Task')

class TaskName(models.Model):
    _name = "task.name"
    # _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin', 'utm.mixin']
    _description = "Task Name"
    # _order = 'date_order desc, id desc'
    _check_company_auto = True

    name = fields.Char('Task Name')

class RepairPartLine(models.Model):
    _name = "repair.part.line"
    # _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin', 'utm.mixin']
    _description = "Repair Part"
    # _order = 'date_order desc, id desc'
    _check_company_auto = True

    part_line = fields.Many2one('car.repair', 'Part')
    part = fields.Many2one('product.product', string='Part', domain=['|', ('type', '=', 'consu'), ('type', '=', 'product')])
    # product_id = fields.Many2one(
    #     'product.product', string='Product')  # Unrequired company
    # product_template_id = fields.Many2one(
    #     'product.template', string='Product Template',
    #     related="product_id.product_tmpl_id")
    part_qty = fields.Float('Quantity')


class PartName(models.Model):
    _name = "part.name"
    # _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin', 'utm.mixin']
    _description = "Part Name"
    # _order = 'date_order desc, id desc'
    _check_company_auto = True

    name = fields.Char('Part Name')

class RepairServiceLine(models.Model):
    _name = "repair.service.line"
    # _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin', 'utm.mixin']
    _description = "Repair Service"
    # _order = 'date_order desc, id desc'
    _check_company_auto = True

    service_line =fields.Many2one('car.repair', 'Service')
    service = fields.Many2one('product.product', 'Service', domain=[('type', '=', 'service')])
    service_qty = fields.Float('Quantity')

class ServiceName(models.Model):
    _name = "service.name"
    # _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin', 'utm.mixin']
    _description = "Service Name"
    # _order = 'date_order desc, id desc'
    _check_company_auto = True

    name = fields.Char('Service Name')