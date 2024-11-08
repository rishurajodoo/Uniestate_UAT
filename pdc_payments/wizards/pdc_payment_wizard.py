from datetime import datetime

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class PDCPaymentWizard(models.TransientModel):
    _name = 'pdc.payment.wizard'
    _description = 'PDC Payment'

    partner_id = fields.Many2one('res.partner', string='Partner', )
    payment_amount = fields.Float(string='Payment Amount')
    # cheque_ref = fields.Char(string='Commercial Name')
    commercial_bank_id = fields.Many2one('pdc.commercial.bank', string='Commercial Bank Name', tracking=True)
    memo = fields.Char(string='Memo')
    destination_account_id = fields.Many2one('account.account', string='Bank')
    journal_id = fields.Many2one('account.journal', string='Journal', domain=[('type','in',['cash','bank'])])
    currency_id = fields.Many2one('res.currency', string='Currency')
    pdc_type = fields.Selection([('sent', 'Sent'),
                                 ('received', 'Received'),
                                 ], string='PDC Type', )

    date_payment = fields.Date(string=' Cheque Date')
    date_registered = fields.Date(string='Collection/Issue date')
    cheque_no = fields.Char()
    move_id = fields.Many2one('account.move', string='Invoice/Bill Ref')
    move_ids = fields.Many2many('account.move', string='Invoices/Bills Ref')
    unit_id = fields.Many2many('product.product', string='Unit')
    floor_id = fields.Many2one('property.floor', string='Floor')
    building_id = fields.Many2one('property.building', string='Building')
    project_id = fields.Many2one('project.project', string='Project')
    cheque_type_id = fields.Many2one('cheque.type', string='Cheque Type')
    order_id = fields.Many2one('sale.order', 'Sale Order', readonly=True)
    # compute="_compute_sale_id"
    pdc_payment_id = fields.Many2one('pdc.payment', string='PDC Payment')
    is_security = fields.Boolean(string="Is Security ?", related="cheque_type_id.is_security")


    @api.onchange('cheque_no', 'date_payment', 'order_id', 'cheque_type_id')
    def _get_memo(self):
        for rec in self:
            if not rec.memo:
                if rec.cheque_no and rec.order_id.unit and rec.cheque_type_id and rec.date_payment:
                    rec.memo = "Chq No " + str(rec.cheque_no) + " DT " + str(rec.date_payment) + " For " + str(
                        rec.order_id.unit.name) + " against " + str(rec.cheque_type_id.description)
                else:
                    rec.memo = rec.memo

    @api.onchange('journal_id')
    def _onchange_journal(self):
        for rec in self:
            if rec.journal_id:
                rec.destination_account_id = rec.journal_id.default_account_id.id

    def create_pdc_payments(self):
        # model = self.env.context.get('active_model')
        # rec = self.env[model].browse(self.env.context.get('active_id'))
        unit_lst = []
        for record in self:
            # if record.unit_id:
            #     for unit in record.unit_id:
            #         unit_lst.append((4, [unit.id]))
            if record.pdc_type == 'received':
                vals = {
                    'partner_id': record.partner_id.id,
                    'journal_id': record.journal_id.id,
                    # 'move_id': rec.id,
                    'move_ids': record.move_ids.ids,
                    'date_payment': record.date_payment,
                    'date_registered': record.date_registered,
                    # 'destination_account_id': record.journal_id.default_account_id.id,
                    'destination_account_id': record.destination_account_id.id,
                    'currency_id': record.currency_id.id,
                    'commercial_bank_id': record.commercial_bank_id.id,
                    'payment_amount': record.payment_amount,
                    'cheque_no': record.cheque_no,
                    'pdc_type': 'received',
                    'purchaser_id': record.purchaser_id.id,
                    'memo': record.memo,
                    # 'unit_id': [(6,0, record.unit_id.ids[0])],
                    # 'unit_id':unit_lst,
                    'floor_id': record.floor_id.id,
                    'building_id': record.building_id.id,
                    'project_id': record.project_id.id,
                    'cheque_type_id': record.cheque_type_id.id,
                    'order_id': record.order_id.id,
                }
                record = self.env['pdc.payment'].create(vals)
                if record.unit_id:
                    for unit in record.unit_id:
                        # unit_lst.append((4, [unit.id]))
                        # record.write({'unit_id': (4, unit.id)})
                        record.write({'unit_id': unit})
                if record:
                    if self.pdc_payment_id:
                        self.pdc_payment_id.write({'state': 'cancel'})
                        for rec in self.pdc_payment_id.get_jv:
                            rec.button_draft()
                            rec.button_cancel()
            elif record.pdc_type == 'sent':
                vals = {
                    'partner_id': record.partner_id.id,
                    'journal_id': record.journal_id.id,
                    # 'move_id': rec.id,
                    'move_ids': record.move_ids.ids,
                    'date_payment': record.date_payment,
                    'date_registered': record.date_registered,
                    'destination_account_id': record.journal_id.default_account_id.id,
                    'currency_id': record.currency_id.id,
                    'payment_amount': record.payment_amount,
                    'cheque_no': record.cheque_no,
                    'pdc_type': 'sent',
                    'memo': record.memo,
                    'purchaser_id': record.purchaser_id.id,
                    # 'unit_id': [(6,0, record.unit_id.ids[0])],
                    # 'unit_id':unit_lst,
                    'floor_id': record.floor_id.id,
                    'building_id': record.building_id.id,
                    'project_id': record.project_id.id,
                    'cheque_type_id': record.cheque_type_id.id,
                    'order_id': record.order_id.id,
                }
                record = self.env['pdc.payment'].create(vals)
                # record.write({'unit_id': unit_lst})
                if record.unit_id:
                    for unit in record.unit_id:
                        # unit_lst.append((4, [unit.id]))
                        record.write({'unit_id': unit.id})
                if record:
                    if self.pdc_payment_id:
                        self.pdc_payment_id.write({'state': 'cancel'})
                        for rec in self.pdc_payment_id.get_jv:
                            rec.button_draft()
                            rec.button_cancel()
            for r in self.move_ids:
                r.is_pdc_created = True

    # Purchaser Flow ----------------------------------------------------------------
    purchaser_ids = fields.Many2many(comodel_name='res.partner', compute="_compute_purchaser_ids")
    purchaser_id = fields.Many2one(comodel_name='res.partner', string='Purchaser',
                                   domain="[('id', 'in', purchaser_ids)]")
    is_invoice = fields.Boolean('Is invoice', compute="_compute_purchaser_ids")

    # @api.depends('move_ids')
    # def _compute_purchaser_ids(self):
    #     model = self.env.context.get('active_model')
    #     active_id = self.env[model].browse(self.env.context.get('active_id'))
    #     if active_id.purchaser_ids and active_id.move_type == 'out_invoice':
    #         self.is_invoice = True
    #         self.purchaser_ids = active_id.purchaser_ids.ids
    #     else:
    #         self.is_invoice = False
    #         self.purchaser_ids = []

    # @api.depends('move_ids')
    # def _compute_sale_id(self):
    #     model = self.env.context.get('active_model')
    #     active_id = self.env[model].browse(self.env.context.get('active_id'))
    #     print(active_id)
    #     if model == 'sale.order':
    #         saleid = active_id
    #         self.order_id = saleid if saleid else ''
    #     else:
    #         if self.env[model].browse(active_id)._name != 'pdc.recall.wizard':
    #             saleid = active_id.so_ids
    #             self.order_id = saleid if saleid else ''
    #         if not self.order_id and self.pdc_payment_id:
    #             self.order_id = self.pdc_payment_id.order_id.id
    # if not self.order_id:
    #     self.order_id = active_id

    @api.depends('move_ids')
    def _compute_purchaser_ids(self):
        model = self.env.context.get('active_model')
        active_id = self.env.context.get('active_id')

        if model and active_id and self.env[model].browse(active_id)._name != 'pdc.recall.wizard':
            active_id_record = self.env[model].browse(active_id)
            if active_id_record.purchaser_ids and active_id_record.move_type == 'out_invoice':
                self.is_invoice = True
                self.purchaser_ids = active_id_record.purchaser_ids.ids
            else:
                self.is_invoice = False
                self.purchaser_ids = []
        else:
            # Handle the case where 'active_model' or 'active_id' is not present in the context
            # You can log a warning or raise an exception based on your use case
            self.is_invoice = False
            self.purchaser_ids = []

    # -------------------------------------------------------------------------------
