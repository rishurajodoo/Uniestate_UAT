import datetime

from odoo import fields, models, api, _
from odoo.fields import Command

from odoo.exceptions import UserError, ValidationError
from dateutil.relativedelta import relativedelta


class TenancyContract(models.Model):
    _name = "tenancy.contract"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Tenancy Contract"
    name = fields.Char(string='Reference', copy=False, readonly=True,
                       default=lambda self: _('New'))
    state = fields.Selection([
        ('new', 'New'),
        ('renew', 'Renew'),
        ('open', 'In Progress'),
        ('closed', 'Closed'),
    ], string='State', default='new')
    start_date = fields.Date(string="Start Date")
    end_date = fields.Date(string="End Date")
    project_id = fields.Many2one('project.project', string='Project')
    building_id = fields.Many2one('property.building', string='Building', domain="[('project_id', '=', project_id)]")
    floor_id = fields.Many2one("property.floor", string="Floor", domain='[("building_id", "=", building_id)]')
    unit_id = fields.Many2many("product.product", string="Unit",
                               domain="[('state', '=', 'available'), ('floor_id', '=', floor_id)]")
    order_id = fields.Many2one("sale.order", 'Order')
    amount = fields.Float('Amount')
    partner_id = fields.Many2one("res.partner", string="Customer")
    show_refund_close_tab = fields.Boolean(string="Show Refund and Close Tab", default=False)
    show_standard_close_tab = fields.Boolean(string="Show Standard Close Tab", default=False)
    approve_by = fields.Many2one(comodel_name='res.users', string='Closed BY', readonly=True, copy=False)
    # , readonly = True
    approve_stage = fields.Selection([
        ('sent', 'Sent for Approval'),
        ('approved', 'Closed'),
    ], string='Closed Stage', widget='badge', readonly=True, default='')
    approve_date = fields.Date(string="Closed On", readonly=True, )

    req_approve_by = fields.Many2one(comodel_name='res.users', string='Approved BY', readonly=True, copy=False)
    # , readonly = True
    req_approve_stage = fields.Selection([
        ('sent', 'Sent for Approval'),
        ('approved', 'Approved'),
    ], string='Approval Stage', widget='badge', readonly=True, default='')
    req_approve_date = fields.Date(string="Aprroval On", readonly=True, )
    # Cron job/ Schedule action function which check the start date of
    # Tenancy contract if start date is occure then the state will go to open/In Progress

    deferred_revenue_amount = fields.Float(string='Deferred Revenue Amount', compute='_compute_deferred_revenue_amount')
    outstanding_amount = fields.Float(string='Outstanding Amount', compute='_compute_invoice_amount')
    payable_amount = fields.Float(string='Payable Amount')
    maintenance_request_amount = fields.Float(string='Maintenance Request Amount', compute='_compute_invoice_amount',
                                              store=True)
    early_termination_period = fields.Selection([
        ('01', '1'),
        ('02', '2'),
        ('03', '3'),
        ('04', '4'),
        ('05', '5'),
        ('06', '6'),
        ('07', '7'),
        ('08', '8'),
        ('09', '9'),
        ('10', '10'),
        ('11', '11'),
        ('12', '12')], string='Early Termination Period', default='01')
    early_termination_penalty_amount = fields.Float(string='Early Termination Penalty Amount',
                                                    compute='_compute_penalty_amount')
    refundable_amount = fields.Float(string='Refundable Amount', compute='_compute_refundable_amount')
    security_deposit_amount = fields.Float(string='Security Deposit Amount')

    # @api.depends('')
    def _compute_deferred_revenue_amount(self):
        for rec in self:
            deferred_revenue_id = self.env['deffered.revenue'].search(
                [('order_id', '=', rec.order_id.id)])
            account_move_id = deferred_revenue_id.depreciation_move_ids.filtered(lambda l: l.state == 'draft')
            rec.deferred_revenue_amount = sum(account_move_id.mapped('amount_total_signed'))

    @api.depends('order_id', 'amount')
    def _compute_invoice_amount(self):
        if self.order_id:
            invoice_ids = self.order_id.invoice_ids
            total_amount = 0
            for moves in invoice_ids:
                if moves.state == 'draft' or moves.payment_state != 'paid':
                    total_amount += moves.amount_total
            request_id = self.env['maintenance.request'].search([('tenancy_id', '=', self.id)], limit=1)
            self.outstanding_amount = total_amount
            self.maintenance_request_amount = request_id.invoice_amount
            # self.early_termination_penalty_amount = (self.amount / (self.end_date - self.start_date).days*12)*int(self.early_termination_period)
        else:
            self.outstanding_amount = 0.00
            self.maintenance_request_amount = 0.00
            # self.early_termination_penalty_amount = 0.00
        pass

    def create_invoice(self):
        maintenance_req = self.env['maintenance.request'].search([('tenancy_id', '=', self.id)])
        inv_lines = []
        for line in self.project_id.early_termination_product:
            inv_lines.append((
                0,
                0,
                {
                    'product_id': line.id,
                    'quantity': 1,
                    'product_uom_id': line.uom_id.id,
                    'price_unit': self.early_termination_penalty_amount,
                    'tax_ids': False,
                },
            )
            )
        for line in self.unit_id:
            inv_lines.append((
                0,
                0,
                {
                    'product_id': line.id,
                    'quantity': 1,
                    'product_uom_id': line.uom_id.id,
                    'price_unit': self.payable_amount,
                    'tax_ids': False,
                },
            )
            )
        for line in maintenance_req.unit_id:
            inv_lines.append((
                0,
                0,
                {
                    'product_id': line.id,
                    'quantity': 1,
                    'product_uom_id': line.uom_id.id,
                    'price_unit': self.early_termination_penalty_amount,
                    'tax_ids': False,
                },
            )
            )

        inv_vals = {
            'partner_id': self.order_id.partner_id.id,
            'invoice_date': self.start_date or datetime.today().date(),
            # 'invoice_date_due': date.today(),
            'invoice_date_due': self.start_date or datetime.today().date(),
            'invoice_payment_term_id': self.order_id.payment_term_id.id,
            'invoice_line_ids': inv_lines,
            'move_type': 'out_invoice',
            'so_ids': self.order_id.id,
            'state': 'draft',
            'project': self.project_id.id,
            'building': self.building_id.id,
            'floor': self.floor_id.id,
            'unit': self.unit_id.ids,
            'invoice_origin': self.name,
            # 'unit': installment.order_id.unit.id,
        }
        self.env['account.move'].create(inv_vals)

    @api.depends('early_termination_period')
    def _compute_penalty_amount(self):
        if self.end_date and self.start_date:
            if (self.end_date - self.start_date).days >= 30:
                self.early_termination_penalty_amount = self.amount / round(
                    (self.end_date - self.start_date).days % 370 / 30) * int(self.early_termination_period)
            else:
                self.early_termination_penalty_amount = 0.00
        else:
            self.early_termination_penalty_amount = 0.00

    @api.depends('early_termination_penalty_amount', 'deferred_revenue_amount', 'maintenance_request_amount',
                 'security_deposit_amount')
    def _compute_refundable_amount(self):
        for rec in self:
            if rec.early_termination_penalty_amount:
                rec.refundable_amount = rec.security_deposit_amount + rec.deferred_revenue_amount - rec.early_termination_penalty_amount - rec.maintenance_request_amount
            else:
                rec.refundable_amount = 0.00

    @api.model
    def _update_state_cron(self):
        records_to_update = self.search([('start_date', '=', fields.Date.today())])

        for record in records_to_update:
            record.state = 'open'

    # Cron job/ Schedule action function which check the end date of
    # Tenancy contract if end date is less than or equal to today date + 3 months state will go to renew/Renew

    @api.model
    def _update_contract_state_cron(self):
        # Find contracts ending within the next 3 months
        end_date_limit = fields.Date.today() + relativedelta(months=3)
        contracts_to_renew = self.search([
            ('end_date', '<=', end_date_limit),
            ('state', '!=', 'renew')
        ])

        # Create activities for contracts that need renewal
        for contract in contracts_to_renew:
            # Check if an activity already exists for this contract
            existing_activity = self.env['mail.activity'].search([
                ('res_id', '=', contract.id),
                ('res_model', '=', 'tenancy.contract'),
                ('activity_type_id', '=', self.env.ref('mail.mail_activity_data_todo').id)
            ], limit=1)

            if not existing_activity:
                contract.message_subscribe(partner_ids=[self.env.user.partner_id.id])
                # Create a new activity assigned to the current user
                activity_data = {
                    'res_id': contract.id,
                    'res_model': 'tenancy.contract',
                    'res_model_id': self.env['ir.model']._get('tenancy.contract').id,
                    'activity_type_id': self.env.ref('mail.mail_activity_data_todo').id,
                    'note': 'Renew Tenancy Contract',
                    'date_deadline': end_date_limit,  # Set the deadline to the contract's end date
                    'user_id': self.env.user.id,
                }
                self.env['mail.activity'].create(activity_data)

            # Update the contract state to 'renew'
            contract.state = 'renew'

    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code('tenancy.contract.seq') or _('New')
        res = super(TenancyContract, self).create(vals)
        if res.order_id:
            res.order_id.tenancy = res.id
            res.order_id.tenancy_state = res.state
            res.order_id.start_date = res.start_date
            res.order_id.end_date = res.end_date
        if res.unit_id:
            res.unit_id.tenancy_id = res.id
            res.unit_id.tenancy_state = res.state
            res.unit_id.start_date = res.start_date
            res.unit_id.end_date = res.end_date
        return res

    def action_show_so(self):
        return {
            'name': _('Sale Order'),
            'view_mode': 'tree,form',
            'res_model': 'sale.order',
            'domain': [('tenancy', '=', self.name)],
            'context': {
                'default_unit': self.unit_id.id,
                'default_floor': self.unit_id.floor_id.id,
                'default_building': self.unit_id.building.id,
                'default_project': self.unit_id.project.id,
                'create': False
            },
            'type': 'ir.actions.act_window',
        }

    def action_open(self):
        for rec in self:
            rec.write({
                'state': 'open'
            })
            if rec.order_id:
                rec.order_id.tenancy_state = 'open'
            if rec.unit_id:
                rec.unit_id.tenancy_state = 'open'

    def action_close_one(self):
        for rec in self:
            deposit_lines = self.order_id.order_line.filtered(
                lambda x: x.product_id.is_sec == True)
            if deposit_lines:
                rec.security_deposit_amount = sum(deposit_lines.mapped('price_subtotal'))
            else:
                rec.security_deposit_amount = 0.0
            if rec.show_standard_close_tab == True:
                raise ValidationError("Tenancy Contract Already Close")
            else:
                rec.show_refund_close_tab = True
            # rec.write({
            #     'state': 'closed'
            # })
            # if rec.order_id:
            #     rec.order_id.tenancy_state = 'closed'
            # if rec.unit_id:
            #     rec.unit_id.tenancy_state = 'open'

    def action_close_two(self):
        for rec in self:
            if rec.show_refund_close_tab == True:
                raise ValidationError("Tenancy Contract Already Close")
            else:
                rec.show_standard_close_tab = True
            # rec.write({
            #     'state': 'closed'
            # })
            # if rec.order_id:
            #     rec.order_id.tenancy_state = 'closed'
            # if rec.unit_id:
            #     rec.unit_id.tenancy_state = 'open'

    def action_reset(self):
        asset_rec = self.env['account.asset'].search([('order_id', '=', self.order_id.id)])
        for rec in self:
            req_rec = self.env['maintenance.request'].search([('tenancy_id', '=', rec.id)])
            rec.state = 'open'
            rec.show_refund_close_tab = False
            rec.show_standard_close_tab = False
            if rec.req_approve_stage:
                rec.req_approve_stage = ''
            if rec.req_approve_by:
                rec.req_approve_by = None
            if rec.req_approve_date:
                rec.req_approve_date = ''

            if rec.approve_stage:
                rec.approve_stage = ''
            if rec.approve_by:
                rec.approve_by = None
            if rec.approve_date:
                rec.approve_date = ''

            if asset_rec.approve_stage:
                asset_rec.approve_stage = ''
            if asset_rec.approve_by:
                asset_rec.approve_by = None
            if asset_rec.approve_date:
                asset_rec.approve_date = ''

            if req_rec.approve_stage:
                req_rec.approve_stage = ''
            if req_rec.approve_by:
                req_rec.approve_by = None
            if req_rec.approve_date:
                req_rec.approve_date = ''

    def action_renew(self):
        for rec in self:
            if rec.order_id:
                # Duplicate the selected sale order using copy_data
                duplicated_order_data = rec.order_id.copy_data()[0]

                # Remove the IDs from rent_plan_ids and rent_installment_ids
                duplicated_order_data.pop('rent_plan_ids', None)
                duplicated_order_data.pop('rent_installment_ids', None)

                # Update the name for the duplicated order
                duplicated_order_data['name'] = rec.order_id.name + ' (Renew)'
                duplicated_order_data['is_renewed'] = True
                price_amount = 0.0
                if rec.project_id.renewal_charges:
                    if rec.project_id.renewal_charges == 'renewal_fixed_amount':
                        price_amount = rec.project_id.renewal_fixed_amount
                    else:
                        unit_amount = sum(line.price_unit if line.product_id in self.unit_id else 0 for line in
                                          rec.order_id.order_line)
                        price_amount = unit_amount * rec.project_id.renewal_percentage / 100

                # Create a new sale order using the duplicated data
                renewal_product = self.project_id.renewal_changes_item
                if renewal_product:
                    duplicated_order_data.get('order_line').append(Command.create(
                        {'product_id': renewal_product.id, 'product_uom_qty': 1.0, 'price_unit': price_amount}))

                duplicated_order = self.env['sale.order'].create(duplicated_order_data)

                for rent_plan in rec.order_id.rent_plan_ids:
                    if not rent_plan.milestone_id.is_invoice:
                        if rent_plan.milestone_id.is_post_cheque:
                            rent_data = duplicated_order.rent_plan_ids.filtered(
                                lambda l: l.milestone_id.is_post_cheque == True)
                            # rent_data.create_inv()
                            rent_data.move_id.so_ids = duplicated_order.id

    def unlink(self):
        for rec in self:
            if rec.order_id:
                rec.order_id.tenancy = False
                rec.order_id.tenancy_state = False
            if rec.unit_id:
                rec.unit_id.tenancy_id = False
                rec.unit_id.tenancy_state = False
                rec.unit_id.start_date = False
                rec.unit_id.end_date = False
            return super(TenancyContract, self).unlink()

    def tc_open_scheduler(self):
        print('Tenancy contract open Scheduler')
        for tc in self.env['tenancy.contract'].search([('state', '=', 'new')]):
            print(tc)
            if tc.start_date:
                if tc.start_date <= datetime.date.today():
                    tc.state = 'open'
                    print(f'Tenancy Contract: {tc.name} status changed')
        data_dict = []
        for tc in self.env['tenancy.contract'].search([('state', '=', 'open')]):
            if tc.end_date:
                if tc.end_date <= datetime.date.today():
                    data_dict.append(tc.name)
                    print(f'Tenancy Contract: {tc.name} status Closed')
                    subject = 'Your Tenancy Contract has been Closed'
                    body = f'Dear {tc.partner_id.name},\n\nYour Tenancy Contract has been Expired please Renew it ASAP'
                    mail_values = {
                        'subject': subject,
                        'body_html': body,
                        'email_to': tc.partner_id.email,
                    }
                    if mail := self.env['mail.mail'].sudo().create(mail_values):
                        mail.sudo().send()
        for renew_tc in self.env['tenancy.contract'].search([('state', 'in', ['renew'])]):
            if renew_tc.end_date:
                if renew_tc.end_date < datetime.date.today():
                    renew_tc.state = 'closed'

    def action_request(self):
        for rec in self:
            req_rec = self.env['maintenance.request'].search([('tenancy_id', '=', rec.id)])
            # if not rec.req_approve_stage:
            #     rec.req_approve_stage = 'sent'
            #     if req_rec:
            #         req_rec.approve_stage = rec.req_approve_stage
            if req_rec:
                raise ValidationError("Request already exist")
            else:
                return {
                    'name': _('Request'),
                    'res_model': 'maintenance.request',
                    'view_mode': 'form',
                    'context': {
                        'default_project_id': rec.project_id.id,
                        'default_unit_id': rec.unit_id.ids[0] if rec.unit_id else False,
                        'default_building_id': rec.building_id.id,
                        'default_floor_id': rec.floor_id.id,
                        'default_tenancy_id': rec.id,
                        'default_start_date': rec.start_date,
                        'default_end_date': rec.end_date,
                        'default_tenancy_state': rec.state,
                        'default_is_ecr': True
                    },
                    'domain': [],
                    # ('asset_id', '=', self.id), ('name', '=', self.name)
                    # 'targert': 'current',
                    'type': 'ir.actions.act_window',
                }

    # def action_show_differed(self):
    #     for rec in self:
    #         return {
    #             'name': _('Deffered Revenues'),
    #             'res_model': 'account.asset',
    #             'view_mode': 'tree,form',
    #             'view_id': self.env.ref('account_asset.view_account_asset_sale_tree').id,
    #             'context': {'asset_type': 'sale', 'default_asset_type': 'sale'},
    #             # 'domain': [('order_id', '=', rec.order_id.id)],
    #             'domain': [('order_id', '=', rec.order_id.id), ('asset_type', '=', 'sale'), ('state', '!=', 'model'), ('parent_id', '=', False)],
    #                    # ('asset_id', '=', self.id), ('name', '=', self.name)
    #             'targert': 'current',
    #             'type': 'ir.actions.act_window',
    #         }

    def action_show_differed(self):
        for rec in self:
            return {
                'name': _('Deffered Revenues'),
                'res_model': 'account.asset',
                'views': [
                    (self.env.ref('account_asset.view_account_asset_sale_tree').id, 'tree'),
                    (self.env.ref('account_asset.view_account_asset_revenue_form').id, 'form'), ],
                'context': {'asset_type': 'sale', 'default_asset_type': 'sale'},
                # 'domain': [('order_id', '=', rec.order_id.id)],
                'domain': [('order_id', '=', rec.order_id.id), ('asset_type', '=', 'sale'), ('state', '!=', 'model'),
                           ('parent_id', '=', False)],
                # ('asset_id', '=', self.id), ('name', '=', self.name)
                'target': 'current',
                'type': 'ir.actions.act_window',
            }

    def action_show_invoice(self):
        for rec in self:
            return {
                'name': _('Invoice'),
                'res_model': 'account.move',
                'view_mode': 'tree,form',
                'context': {},
                'domain': [('so_ids', '=', rec.order_id.id)],
                'target': 'current',
                'type': 'ir.actions.act_window',
            }

    def action_submit_ref_close(self):
        for rec in self:
            if rec.req_approve_stage == 'approved' and rec.approve_stage == 'approved':
                if rec.state != 'closed':
                    rec.state = 'closed'
                else:
                    raise ValidationError("Already closed")
            else:
                raise ValidationError("You need to approve Maintenance Request and Differed")

    def action_submit_stand_close(self):
        for rec in self:
            sale_order_id = rec.order_id
            for unit in self.unit_id:
                unit.state = 'available'
            invoices = self.env['account.move'].search([
                ('invoice_origin', '=', sale_order_id.name),
                ('state', '=', 'draft')
            ])
            # Cancel draft invoices
            for invoice in invoices:
                # invoice.button_cancel()
                invoice.state = 'cancel'
            sale_order_id._action_cancel()
            self.state = 'closed'

    def action_show_pdc(self):
        for rec in self:
            return {
                'name': _('PDC'),
                'res_model': 'pdc.payment',
                'view_mode': 'tree,form',
                'context': {},
                'domain': [('order_id', 'in', rec.order_id.ids)],
                # 'domain': [('id', '=', rec.order_id.rent_installment_ids.pdc_payment_id.id)],
                # 'domain': [('id', 'in', rec.order_id.rent_installment_ids.mapped('pdc_payment_id.id'))],
                'target': 'current',
                'type': 'ir.actions.act_window',
            }

    def action_show_request(self):
        for rec in self:
            return {
                'name': _('Request'),
                'res_model': 'maintenance.request',
                'view_mode': 'tree,form',
                'context': {},
                'domain': [('tenancy_id', '=', rec.id)],
                # ('id', '=', rec.order_id.rent_installment_ids.pdc_payment_id.id)
                'target': 'current',
                'type': 'ir.actions.act_window',
            }

    def action_show_deffered_revenue(self):
        for rec in self:
            return {
                'name': _('Deffered Revenue'),
                'res_model': 'deffered.revenue',
                'view_mode': 'tree,form',
                'context': {},
                'domain': [('order_id', '=', rec.order_id.id)],
                # ('id', '=', rec.order_id.rent_installment_ids.pdc_payment_id.id)
                'target': 'current',
                'type': 'ir.actions.act_window',
            }

    def action_sent_approve(self):
        for rec in self:
            asset_rec = self.env['account.asset'].search([('order_id', '=', self.order_id.id)])
            if rec.req_approve_stage != 'approved':
                raise ValidationError("You need to approve first Mantinance Request")
            else:
                if not rec.approve_stage:
                    rec.approve_stage = 'sent'
                    if asset_rec:
                        asset_rec.approve_stage = rec.approve_stage
                    group_users = self.env['res.users'].search(
                        [('groups_id', 'in', self.env.ref('marquespoint_overall.group_differed_approval').id)])

                    # Send notification to users in the group
                    display_msg = "Differed approval has been sent. Please review and approve."
                    for user in group_users:
                        post = self.env.user.partner_id.message_post(body=display_msg, message_type='notification',
                                                                     subtype_xmlid='mail.mt_comment',
                                                                     author_id=self.env.user.partner_id.id)

                        if post:
                            notification_ids = [
                                (0, 0, {'res_partner_id': user.partner_id.id, 'mail_message_id': post.id})]
                            post.write({'notification_ids': notification_ids})
                elif rec.approve_stage == 'sent':
                    raise ValidationError("Already Sent for Approval")
                else:
                    raise ValidationError("Already Approved")
