from collections import defaultdict
from dateutil.relativedelta import relativedelta
from odoo import api, fields, models, _


class PropertyPerformanceReportWizard(models.TransientModel):
    _name = 'property.performance.report.wizard'

    start_date = fields.Date('Date')
    end_date = fields.Date('End Date')
    project = fields.Many2many('project.project', string='Project')
    leasing_monthly_rental_income = fields.Boolean(string='Monthly Rental Income')
    leasing_monthly_cost_rental = fields.Boolean(string='Monthly Cost of Rental')
    general_account_id = fields.Many2many(
        'account.account',
        string='Costal Financial Account',
        ondelete='restrict',
        domain="[('deprecated', '=', False)]",
        store=True, readonly=False
    )

    def property_performance_report(self):
        self.ensure_one()
        projects_data = []
        analytic_data = []
        financial_account_set = set()
        total_unit_amount_sum = 0

        if self.project:
            project_ids = self.project
        else:
            project_ids = self.env['project.project'].search([])
        for project in project_ids:
            units = self.env['product.product'].search_count([
                ('project', '=', project.id),
                ('is_unit', '=', True)
            ])
            total_units = units
            rented_unit =  self.env['product.product'].search_count([
                ('project', '=', project.id),
                ('is_unit', '=', True),
                ('state', '=', 'rented')
            ])

            rented_unit_sum = self.env['product.product'].search([
                ('project', '=', project.id),
                ('is_unit', '=', True),
            ])
            unit_amount_sum = sum(rented_unit_sum.mapped('property_size'))
            unit_rent_sum = sum(rented_unit_sum.filtered(lambda z: z.state == 'rented').mapped('property_size'))

            contracts = self.env['tenancy.contract'].search([
                ('project_id', '=', project.id),
            ])
            monthly_counts = defaultdict(lambda: {'rent': 0, 'vac': 0, 'amount': 0, 'balance': 0, 'income': 0, 'cost':0,  'total_unit_price': 0, 'unit_rent':0, 'unit_cost':0, 'total_rent_unit':0, 'total_rented_unit_count': 0, 'total_unit_count': 0, 'total_cost_count': 0})
            for contract in contracts:
                if not contract.start_date or not contract.end_date:
                    continue
                contract_start = contract.start_date
                contract_end = contract.end_date
                current_month = contract_start.replace(day=1)
                while current_month <= contract_end:
                    if self.start_date <= current_month <= self.end_date:
                        year_month = current_month.strftime('%b')
                        monthly_counts[year_month]['rent'] += 1
                        monthly_counts[year_month]['amount'] += contract.amount_per_month
                        monthly_counts[year_month]['total_unit_price'] += unit_amount_sum
                        monthly_counts[year_month]['total_rent_unit'] += unit_rent_sum
                        monthly_counts[year_month]['total_rented_unit_count'] += rented_unit
                    current_month += relativedelta(months=1)
            if self.general_account_id:
                analytic_lines = self.env['account.analytic.line'].search([
                    ('general_account_id', 'in', self.general_account_id.ids),
                    ('analytic_account_id.unit_id.project', '=', project.id),
                    ('date', '>=', self.start_date),
                    ('date', '<=', self.end_date)
                ])
                for line in analytic_lines:
                    analytic_dict = {
                        'date': line.date or "",
                        'financial_account': line.general_account_id.name or "",
                        'balance': line.amount or 0,
                        'analytical_account': line.analytic_account_id.name or "",
                        'unit': line.analytic_account_id.unit_id.name or "",
                        'project': line.analytic_account_id.unit_id.project.name or ""
                    }
                    analytic_data.append(analytic_dict)
                    year_month = line.date.strftime('%b')
                    monthly_counts[year_month]['balance'] += line.amount
                    if total_unit_amount_sum > 0 and line.amount > 0:
                        monthly_counts[year_month]['cost'] = line.amount / total_unit_amount_sum
                    if line.general_account_id.name:
                        financial_account_set.add(line.general_account_id.name)
            for month, data in monthly_counts.items():
                if data['total_unit_price'] > 0:
                    data['income'] = data['amount'] /data['total_unit_price']
                    data['cost'] = data['balance'] /data['total_unit_price']
                else:
                    data['income'] = 0
                    data['cost'] = 0
                if data['total_rent_unit'] > 0:
                    data['unit_rent'] = data['amount'] / data['total_rent_unit']
                    data['unit_cost'] = data['balance'] / data['total_rent_unit']
                else:
                    data['unit_rent'] = 0
                    data['unit_cost'] = 0
                if data['total_rented_unit_count'] > 0:
                    data['total_unit_count'] = data['amount'] / data['total_rented_unit_count']
                    data['total_cost_count'] = data['balance'] / data['total_rented_unit_count']
                else:
                    data['total_unit_count'] = 0
                    data['total_cost_count'] = 0
            formatted_monthly_counts = {
                month: {
                    'rent': data['rent'],
                    'vac': data['vac'],
                    'amount': data['amount'],
                    'balance': data['balance'],
                    'income': data['income'],
                    'cost': data['cost'],
                    'unit_rent': data['unit_rent'],
                    'unit_cost': data['unit_cost'],
                    'total_unit_count': data['total_unit_count'],
                    'total_cost_count': data['total_cost_count']
                } for month, data in monthly_counts.items()
            }

            projects_data.append({
                'project': project.name,
                'total_units': total_units,
                'monthly_counts': formatted_monthly_counts,
            })

        financial_account = ', '.join(financial_account_set)
        data = {
            'start_date': self.start_date,
            'end_date': self.end_date,
            'projects_data': projects_data,
            'monthly_income': self.leasing_monthly_rental_income,
            'months': self.get_month_range(self.start_date, self.end_date),
            'analytic_data': analytic_data,
            'financial_income': self.leasing_monthly_cost_rental,
            'financial_account': financial_account
        }

        return self.env.ref('property_performance_report.property_performance_report_action').report_action(self, data=data)

    def get_month_range(self, start_date, end_date):
        months = []
        current_date = start_date
        while current_date <= end_date:
            months.append(current_date.strftime('%b'))
            current_date += relativedelta(months=1)
        return months
