
# ................................. Importing Library And Directives ...................................................

from datetime import datetime, timedelta

from odoo import api, fields, models, SUPERUSER_ID, _
from odoo.exceptions import UserError, ValidationError
import logging
import base64

from odoo.fields import Datetime
from odoo.modules import get_module_resource
from odoo.tools import formataddr

_logger = logging.getLogger(__name__)

# ................................... End Of Importing Library And Directives ..........................................

# .............................. Class For Car Repair Diagnosis ........................................................


class CarRepair(models.Model):
    _name = "car.repair"
    _inherit = ['mail.thread']
    _description = "Car Repair"
    _rec_name = 'subject'
    _order = 'id desc'
    _check_company_auto = True

    def _default_employee(self):
        return self.env.context.get('default_employee_id') or self.env['hr.employee'].search([('user_id', '=', self.env.uid)], limit=1)

    state = fields.Selection([('diagnosis', 'Car Diagnosis'), ('send_quotation', 'Send Quotation'),
                              ('inventory_move', 'Inventory Move'), ('work_order', 'Work Order'),
                              ('inspections','Inspections'), ('invoice', 'Invoice')],
                             'Status', readonly=True, default='diagnosis')

    subject = fields.Char(string='Subject')
    # receiving_tech = fields.Many2one('hr.employee', string='Receiving Technician',  default=lambda self: self.env.user)
    receiving_tech = fields.Many2one('hr.employee', string='Receiving Technician',  default=_default_employee)
    priority = fields.Selection([('0', 'Not urgent'), ('1', 'Normal'), ('2', 'Urgent'), ('3', 'Very Urgent')],
                                'Priority',
                                readonly=True, default='1')
    receipt_date = fields.Date(string='Date Of Receipt', default=lambda self: fields.Datetime.now())
    scheduled_service_date = fields.Date(string='Scheduled Service Date')
    rma_number = fields.Integer(string='RMA Number')

    client = fields.Many2one('res.partner', string='Client')
    contacts_name = fields.Many2one('res.partner', string='Contact Name')
    email = fields.Char(string='Email')
    phone = fields.Char(string='Phone')
    mobile = fields.Char(string='Mobile')
    contact_no = fields.Char(string='Contact No')

    description = fields.Text('Note')

    multi_image = fields.Many2many('repair.image',  string='Images')

    note = fields.Text(string='Descriptions/Remark')
    multi_select = fields.Html('Multi Select Faults')

    digital_signature = fields.Binary('Signature')

    task_line = fields.One2many('repair.task.line', 'repair_id')

    part_line = fields.One2many('repair.part.line', 'part_line')

    service_line = fields.One2many('repair.service.line', 'service_line')

    assign_technicians = fields.Many2many('hr.employee', string='Technicians')

    sale_order_id = fields.Char('Sale Order ID')

    work_order_id = fields.Char('Work Order Id')


    # repair_count = fields.Integer(compute='_compute_repair_count', string='Repair Count')

    # d = fields.Binary(compute='_compute_image',string='Repair Im')

    # def _compute_image(self):
    #     for employee in self:
    #         if employee.multi_image.tp:
    #             employee.d = employee.multi_image.tp

    # def _compute_repair_count(self):
    #     for employee in self:
    #         employee.repair_count = len(employee.id)
    #         a=10

    @api.onchange('contacts_name')
    def _compute_client_info(self):
        """
        Trigger the recompute of the client information.
        """
        for repair in self:
            repair.phone = self.contacts_name.phone
            repair.mobile =self.contacts_name.mobile
            repair.email = self.contacts_name.email
# ........................................... Function for Inventory Move Button .......................................

    def action_view_inventory_move(self):
        view = self.env.ref('stock.view_picking_form')
        trees = self.env.ref('stock.vpicktree')
        res = {
            'name': 'Inventory Move',
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'stock.picking',
            'views': [(trees.id, 'tree'), (view.id, 'form')],
            'view_id': view.id,
            'target': 'current',
            'context': {'search_default_origin': self.sale_order_id},
        }
        return res

# ............................................. End of Function for Inventory Move Button ..............................

# ........................................... Function for Work Order Button ...........................................

    def action_view_work_order(self):
        view = self.env.ref('repair_service.view_work_order_form')
        trees = self.env.ref('repair_service.work_order_tree')
        res = {
            'name': 'Work Order',
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'work.order',
            'views': [(trees.id, 'tree'), (view.id, 'form')],
            'view_id': view.id,
            'target': 'current',
            'domain': [('work_order', '=', self.id)]
        }
        return res

# ............................................. End of Function for Work Order Button ..............................

# .............................................. Function for Confirm Diagnosis And Send Quotation .....................
    def send_quotation(self):
        sale_order = self.env['sale.order'].sudo().create({
            'partner_id': self.client.id,
            'repair_id': self.id
        })
        sales_order_line = []
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

        # for i in self.assign_technicians:
        #     partner = self.env['hr.employee'].search([('id','=',i.id)])
        #     if partner:
        #         body = "Hello, You have been assigned to Repair Service. Please check"
        #         pa = self.env['res.partner'].search([('name','=',i.name)]).id
        #         pas = self.env['res.partner'].search([('name','=',self.receiving_tech.name)]).id
        #         ids = []
        #         ids.append(pas)
        #         ids.append(pa)
        #         channel_search = self.env['mail.channel'].search(['&',('channel_last_seen_partner_ids.partner_id','=',pa),('channel_last_seen_partner_ids.partner_id','=',pas)])
        #         li = []
        #         for x in channel_search:
        #             li.append(x.id)
        #         if not channel_search:
        #             channel_search = self.env['mail.channel'].create({
        #                 'name': '',
        #                 'channel_last_seen_partner_ids': [(0, 0, {'partner_id': ids})]
        #             })
        #         message = self.env['mail.message'].create({
        #             'date' : Datetime.now(),
        #             'model': 'mail.channel',
        #             'res_id': self.id,
        #             'message_type': 'notification',
        #             'body': body,
        #             'moderation_status': 'accepted',
        #             'record_name' : self.env['res.partner'].search([('name','=',i.name)]).name,
        #             'author_id': pas,
        #             'email_from': formataddr((self.receiving_tech.name, self.receiving_tech.private_email)),
        #             'subtype_id': self.env['mail.message.subtype'].search([('name', '=', 'Discussions')]).id,
        #             # 'partner_ids': [(6, 0, [self.env['res.partner'].search([('name','=',i.name)]).id])],
        #             'channel_ids': [(6, 0, li)],
        #         })

        return True

    def action_view_partner_invoices(self):
        for i in self.assign_technicians:
            partner = self.env['hr.employee'].search([('id','=',i.id)])
            if partner:
                body = "Hello, You have been assigned to Repair Service. Please check"
                pa = self.env['res.partner'].search([('name','=',i.name)]).id
                pas = self.env['res.partner'].search([('name','=',self.receiving_tech.name)]).id
                ids = []
                ids.append(pas)
                ids.append(pa)
                channel_search = self.env['mail.channel'].search(['&',('channel_last_seen_partner_ids.partner_id','=',pa),('channel_last_seen_partner_ids.partner_id','=',pas)])
                li = []
                for x in channel_search:
                    li.append(x.id)
                if not channel_search:
                    channel_search = self.env['mail.channel'].create({
                        'name': '',
                        'channel_last_seen_partner_ids': [(0, 0, {'partner_id': ids})]
                    })
                message = self.env['mail.message'].create({
                    'date' : Datetime.now(),
                    'model': 'mail.channel',
                    'res_id': self.id,
                    'message_type': 'notification',
                    'body': body,
                    'moderation_status': 'accepted',
                    'record_name' : self.env['res.partner'].search([('name','=',i.name)]).name,
                    'author_id': pas,
                    'email_from': formataddr((self.receiving_tech.name, self.receiving_tech.private_email)),
                    'subtype_id': self.env['mail.message.subtype'].search([('name', '=', 'Discussions')]).id,
                    # 'partner_ids': [(6, 0, [self.env['res.partner'].search([('name','=',i.name)]).id])],
                    'channel_ids': [(6, 0, li)],
                })
                return True

    def done_inspection(self):
        self.update({'state': 'invoice'})
        return True

# ............................... End of Function Confirm Diagnosis And Send Quotation .................................

# ................................ End Of Class Car Repair .............................................................


# ................................ Class For Repair Task List ..........................................................

class RepairTaskLine(models.Model):
    _name = "repair.task.line"
    _description = "Repair Task"
    _order = 'id desc'
    _check_company_auto = True

    # image = fields.Binary('Image Field')

    remark = fields.Char('Remark')
    document = fields.Binary('Document')
    repair_id = fields.Many2one('car.repair', 'Repair ID')
    task = fields.Many2one('task.name', 'Task')

    def download_files(self):
        a=10
        doc=self.document
        return self.document
        # return {
        #     'type': 'ir.actions.act_url',
        #     'target': 'self',
        #     'url': self.document,
        # }

# ................................End of  Class Repair Task List .......................................................

# ................................ Class For Repair Task Name ..........................................................

class TaskName(models.Model):
    _name = "task.name"
    _description = "Task Name"
    _order = 'id desc'
    _check_company_auto = True

    name = fields.Char('Task Name')

# ................................End Of Class Repair Task Name ........................................................

# ................................ Class For Repair Part Line ..........................................................

class RepairPartLine(models.Model):
    _name = "repair.part.line"
    _description = "Repair Part"
    _order = 'id desc'
    _check_company_auto = True

    part_line = fields.Many2one('car.repair', 'Part')
    part = fields.Many2one('product.product', string='Part', domain=['|', ('type', '=', 'consu'),
                                                                     ('type', '=', 'product')])
    part_qty = fields.Float('Quantity')

# ................................End Of Class For Repair Part Line ....................................................

# ................................ Class For Repair Part Name ..........................................................

class PartName(models.Model):
    _name = "part.name"
    _description = "Part Name"
    _order = 'id desc'
    _check_company_auto = True

    name = fields.Char('Part Name')

# ................................End Of Class For Repair Part Name ....................................................

# ................................ Class For Repair Service Line .......................................................

class RepairServiceLine(models.Model):
    _name = "repair.service.line"
    _description = "Repair Service"
    _order = 'id desc'
    _check_company_auto = True

    service_line =fields.Many2one('car.repair', 'Service')
    service = fields.Many2one('product.product', 'Service', domain=[('type', '=', 'service')])
    service_qty = fields.Float('Quantity')

# ................................End Of Class For Repair Service Line .................................................

# ................................ Class For Repair Service Name .......................................................

class ServiceName(models.Model):
    _name = "service.name"
    _description = "Service Name"
    _order = 'id desc'
    _check_company_auto = True

    name = fields.Char('Service Name')

# ................................End Of Class Repair Service Name .....................................................

# ................................ Class For Adding Images In Repair Action ............................................

class RepairImage(models.Model):
    _name = "repair.image"
    _description = "Repair Image"
    # _order = 'id desc'
    # _check_company_auto = True

    image = fields.Binary('Select Image')
    fname = fields.Char(string="File Name")
    remark = fields.Text('Any Remark')

    dost = fields.Binary('Download This Image')

    @api.onchange('image')
    def onchnage_image(self):
        self.dost = self.image

# ............................. End Of Class For Adding Images In Repair Action.........................................


# ................................ Class For Work Order ............................................

class WorkOrder(models.Model):
    _name = "work.order"
    _description = "Work Order"
    _order = 'id desc'
    # _check_company_auto = True

    state = fields.Selection([('start', 'Start'), ('in_progress', 'In Progress'),
                              ('completed', 'Completed'), ('pause', 'Pause'), ('cancel', 'Cancel Task')],
                             'Status', readonly=True, default='start')

    work_order = fields.Many2one('car.repair', string='Repair Order')

    # subject = fields.Char(string='Subject')
    receiving_tech = fields.Many2one('hr.employee', string='Receiving Technician')


    receipt_date = fields.Date(string='Date Of Receipt', default=lambda self: fields.Datetime.now())

    start_time = fields.Datetime(string='Start Time')
    end_time = fields.Datetime(string='End Time')
    duration = fields.Char(string='Duration')
    hour_worked = fields.Char(string='Hour Worked')

    task_name = fields.Char('Task')


    def start_task(self):
        current_time = datetime.today()
        self.update({'state': 'in_progress','start_time': current_time})

    def complete_task(self):

        complete_time = datetime.today()

        dur = (datetime.today() - self.start_time)
        duration = dur.seconds//3600

        minutes = dur.seconds / 60
        min = round(minutes,2)

        self.update({'state': 'completed','end_time': complete_time,'duration': dur,'hour_worked': duration})

        work_count = self.env['work.order'].search_count([('work_order', '=', self.work_order.id)])

        work_obj = self.env['work.order'].search([('work_order', '=', self.work_order.id)])
        count = 0
        for x in work_obj:
            if x.state == 'completed':
                count += 1
        if work_count == count:
            repair_obj = self.env['car.repair'].search([('id', '=', self.work_order.id)])
            repair_obj.update({'state': 'inspections'})

# ............................. End Of Class For Work Order.............................................................
