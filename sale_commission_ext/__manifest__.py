{
    "name": "Sales commissions Extension",
    "version": "17.0.1.0.2",
    "category": "Sales Management",
    "license": "AGPL-3",
    "depends": [
        "sale",
        "marquespoint_overall",
        "project_customization",
    ],
    "data": [
        "security/ir.model.access.csv",
        "views/sale_order_view.xml",
        "views/project_project.xml",
        "views/res_partner.xml",
        "views/account_move.xml",
        "views/commission_settlement.xml",
        "views/unit.xml",
        "views/timeoff.xml",
        "views/hr_contract.xml",
        "views/config.xml",
        "wizard/commission_make_settlement.xml"
    ],
    "installable": True,
}
