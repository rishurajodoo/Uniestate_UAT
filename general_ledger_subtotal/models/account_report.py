from odoo import models
import copy

class AccountReport(models.Model):
    _inherit = _inherit = 'account.report'



    def _get_lines(self, options, all_column_groups_expression_totals=None, warnings=None):
        res = super(AccountReport, self)._get_lines(options, all_column_groups_expression_totals=None,
                                                    warnings=warnings)
        # List to hold new entries
        test = copy.deepcopy(res)

        # Iterate backwards through the test list
        for idx in range(len(test) - 1, -1, -1):  # Start from the last index to 0
            line_dict = test[idx]

            if 'subtotal' in line_dict['id']:
                continue
            if 'total' in line_dict['id']:
                original_total = copy.deepcopy(line_dict)
                total_dict = line_dict
                total_id = total_dict['id']
                initial_id = total_id.replace("total", "initial")

                # Find initial_dict matching the replaced initial_id
                initial_dict = next((d for d in res if d['id'] == initial_id), None)

                initial_monetary_values = {'debit': 0, 'credit': 0, 'balance': 0}
                total_monetary_values = {'debit': 0, 'credit': 0, 'balance': 0}

                if initial_dict:
                    # Combine the logic to extract monetary values from both dicts
                    for initial_column, total_column in zip(initial_dict['columns'], total_dict['columns']):
                        if initial_column.get('figure_type') == 'monetary':
                            expression_label = initial_column['expression_label']

                            # Extract values from initial_dict
                            if 'debit' in expression_label:
                                initial_monetary_values['debit'] = initial_column.get('no_format', 0)
                            elif 'credit' in expression_label:
                                initial_monetary_values['credit'] = initial_column.get('no_format', 0)
                            elif 'balance' in expression_label:
                                initial_monetary_values['balance'] = initial_column.get('no_format', 0)

                            # Extract values from total_dict
                            if 'debit' in total_column['expression_label']:
                                total_monetary_values['debit'] = total_column.get('no_format', 0)
                            elif 'credit' in total_column['expression_label']:
                                total_monetary_values['credit'] = total_column.get('no_format', 0)
                            elif 'balance' in total_column['expression_label']:
                                total_monetary_values['balance'] = total_column.get('no_format', 0)

                    # Calculate subtotals if initial_dict is found
                    subtotal_debit = total_monetary_values['debit'] - initial_monetary_values['debit']
                    subtotal_credit = total_monetary_values['credit'] - initial_monetary_values['credit']
                    subtotal_balance = total_monetary_values['balance'] - initial_monetary_values['balance']

                    for column in total_dict['columns']:
                        if column['expression_label'] == 'debit':
                            column['name'] = f"{subtotal_debit:.2f} AED"
                            column['no_format'] = subtotal_debit
                        elif column['expression_label'] == 'credit':
                            column['name'] = f"{subtotal_credit:.2f} AED"
                            column['no_format'] = subtotal_credit
                        elif column['expression_label'] == 'balance':
                            column['name'] = f"{subtotal_balance:.2f} AED"
                            column['no_format'] = subtotal_balance

                # Update 'total' to 'subtotal' in the name
                total_dict['id'] = total_dict['id'].replace('total', 'subtotal')
                total_dict['name'] = total_dict['name'].replace('Total', 'Subtotal')

                subtotal_index = idx + 1  # The next index after the subtotal
                test.insert(subtotal_index, original_total)  # Inse

        return test










