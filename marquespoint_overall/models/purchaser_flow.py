from odoo import fields, models, api, _


class AccountMove(models.Model):
    _inherit = 'account.move'

    purchaser_ids = fields.Many2many(comodel_name='res.partner', string='Purchaser', compute='_compute_purchaser_ids')

    @api.depends('so_ids')
    def _compute_purchaser_ids(self):
        for move in self:
            if move.so_ids:
                purchasers = [
                    (6, 0, move.mapped("so_ids.purchaser_ids.purchase_individual").ids)
                ]
                move.purchaser_ids = purchasers
            else:
                move.purchaser_ids = []

    def new_button_action(self):
        return


class PaymentWizardInherit(models.TransientModel):
    _inherit = "account.payment.register"

    writeoff_is_exchange_account = fields.Char()
    qr_code = fields.Char()

    purchaser_ids = fields.Many2many(comodel_name='res.partner', compute="_compute_purchaser_ids")
    purchaser_id = fields.Many2one(comodel_name='res.partner', string='Purchaser',
                                   domain="[('id', 'in', purchaser_ids)]")
    is_invoice = fields.Boolean('Is invoice', compute="_compute_purchaser_ids")



    order_id = fields.Many2one( comodel_name='sale.order',string='Sale Order ID', compute="_compute_purchaser_ids" )

    # @api.model
    # def create(self, values):
    #     # Check if 'order_id' is not provided in the values
    #     if 'order_id' not in values:
    #         # Get the 'so_id' from the related 'account.move'
    #         account_move_id = self.env['account.move'].browse(values.get('so_id'))
    #         so_id = account_move_id.so_ids.id if account_move_id.so_ids else False

    #         # Set 'order_id' with the default value
    #         values['order_id'] = so_id

    #     # Call the original create method
    #     return super(PaymentWizardInherit, self).create(values)
    @api.depends('communication')
    def _compute_purchaser_ids(self):
        model = self.env.context.get('active_model')
        if model == 'account.move.line':
            model = 'account.move'
        active_id = self.env[model].browse(self.env.context.get('active_id'))
        saleid = active_id.so_ids
        print(f"-------------------------------------------------------{active_id.so_ids}")
        
        self.order_id = saleid if saleid else ''
        if active_id.purchaser_ids and active_id.move_type == 'out_invoice':
            self.is_invoice = True
            self.purchaser_ids = active_id.purchaser_ids.ids
        else:
            self.is_invoice = False
            self.purchaser_ids = []
            
    def _create_payment_vals_from_wizard(self, batch_result):
        vals = super(PaymentWizardInherit, self)._create_payment_vals_from_wizard(batch_result)
        vals.update({
            'purchaser_id': self.purchaser_id.id,
            'order_id': self.order_id.id
        })
        return vals

    def _create_payment_vals_from_batch(self, batch_result):
        vals = super(PaymentWizardInherit, self)._create_payment_vals_from_batch(batch_result)
        vals.update({
            'purchaser_id': self.purchaser_id.id,
            'order_id': self.order_id.id
        })
        return vals


class AccountPayment(models.Model):
    _inherit = 'account.payment'

    purchaser_id = fields.Many2one(comodel_name='res.partner', string='Purchaser')

