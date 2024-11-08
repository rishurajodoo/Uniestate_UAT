{
    "name": "Employee Activity Portal",
    "version": "17.0",
    "category": "Generic",
    "depends": ["portal", "hr_attendance", "hr", "hr_holidays"],
    "website": "",
    "assets": {
        "web.assets_frontend": [
            "employee_activity_portal/static/src/scss/employee_activity_portal.scss",
            "employee_activity_portal/static/src/js/attendance_datetime.js",
        ],
    },
    "data": [
        "security/ir.model.access.csv",
        "security/employee_activity_portal_security.xml",
        "views/portal_attendance_views.xml",
        "views/portal_employee_views.xml",
        "views/menu_employee_activity_portal.xml",
        "views/portal_attendance_templates.xml",
        # "data/portal_employee_templates.xml",
        "views/hr_employee_views.xml",
        "views/portal_timeoff_templates.xml",
        "views/portal_timeoff_request_templates.xml",
        "data/portal_emp_reg_edit_templates.xml",
    ],
    "installable": True,
    "application": False,
}
