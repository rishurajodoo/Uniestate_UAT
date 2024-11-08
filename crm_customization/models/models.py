# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError


class CrmStage(models.Model):
    _inherit = 'crm.stage'

    is_lost = fields.Boolean(string="Is Lost ?")


class CrmLeadModelInherit(models.Model):
    _inherit = 'crm.lead'
    _description = 'Crm Lead Model Inherit'

    for_sale = fields.Boolean(default=False)
    for_rent = fields.Boolean(default=False)
    is_lost = fields.Boolean(string="Is Lost",default=False)

    def action_set_lost(self, **additional_values):
        """ Lost semantic: probability = 0 or active = False """
        lost_stage_id = self.env['crm.stage'].search([('is_lost', '=', True)])
        if additional_values:
            self.write({'stage_id': lost_stage_id.id,'is_lost':True})
            self.write(dict(additional_values))

            # self.write(dict(additional_values))
        # res = self.action_archive()
        # if additional_values:
        #     self.write(dict(additional_values))
        # return res

    @api.constrains('for_sale', 'for_rent')
    def _constrains_on_sale_selection(self):
        for rec in self:
            if rec.for_sale and rec.for_rent:
                raise UserError("You Can't be able to select both Sale and Rent on same time")

    @api.onchange('for_rent', 'for_sale')
    def onchange_sale_rent(self):
        lst = []
        if self.for_sale:
            ids = self.unit_id.sudo().search([
                ('for_sale', '=', True)
            ]).ids

            return {
                'domain': {
                    'unit_id': [('id', 'in', ids)],
                }
            }

        elif self.for_rent:
            ids = self.unit_id.sudo().search([
                ('for_rent', '=', True)
            ]).ids
            return {
                'domain': {
                    'unit_id': [('id', 'in', ids)],
                }
            }

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        unit = self.unit_id.browse(self.env.context.get('active_id'))
        if unit.for_rent:
            res['unit_id'] = [(6, 0, unit.ids)]
            res['floor_id'] = unit.floor_id.id
            res['building_id'] = unit.building.id
            res['project_id'] = unit.project.id
            res['for_rent'] = unit.for_rent
            res['for_sale'] = unit.for_sale
            res['expected_revenue'] = unit.rent_price
        if unit.for_sale:
            res['unit_id'] = [(6, 0, unit.ids)]
            res['floor_id'] = unit.floor_id.id
            res['building_id'] = unit.building.id
            res['project_id'] = unit.project.id
            res['for_rent'] = unit.for_rent
            res['for_sale'] = unit.for_sale
            res['expected_revenue'] = unit.property_price

        return res

    @api.constrains('expected_revenue')
    def _constrains_on_expected_revenue(self):
        for rec in self:
            if rec.for_sale:
                if rec.expected_revenue < sum(rec.unit_id.mapped('property_price')):
                    raise UserError("Expected revenue price is not less then sales price")
            elif rec.for_rent:
                if rec.expected_revenue < sum(rec.unit_id.mapped('rent_price')):
                    raise UserError("Expected revenue price is not less then rent price")
