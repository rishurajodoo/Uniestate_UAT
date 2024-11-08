odoo.define("employee_activity_portal.attendance_datetime", function (require) {
    "use strict";

    var ajax = require("web.ajax");
    var time = require('web.time');
    var publicWidget = require("web.public.widget");

    publicWidget.registry.Attendance = publicWidget.Widget.extend({
        selector: ".portal_attendance_configuration",

        init: function () {
            this._super.apply(this, arguments);
            // datetime picker (for custom field)
            if (!$.fn.datetimepicker) {
                ajax.loadJS("/web/static/lib/tempusdominus/tempusdominus.js");
            }
             this.datetimepickers_options = {
                calendarWeeks: true,
                icons: {
                    time: "fa fa-clock-o",
                    date: "fa fa-calendar",
                    up: "fa fa-chevron-up",
                    down: "fa fa-chevron-down",
                    previous: "fa fa-chevron-left",
                    next: "fa fa-chevron-right",
                    today: "fa fa-calendar-check-o",
                    clear: "fa fa-delete",
                    close: "fa fa-times",
                },
                locale: moment.locale(),
                allowInputToggle: true,
                buttons: {
                    showToday: true,
                    showClose: true,
                },
                format: time.getLangDatetimeFormat(),
                keyBinds: null,
            };
        },

        start: function () {
            var self = this;
            var def = this._super.apply(this, arguments);
            var attendance_datetimes = this.$('.portal_attendance_datetimepicker').parent()
           _.each(attendance_datetimes, function (attendance_datetime) {
                $(attendance_datetime).datetimepicker(
                    self.datetimepickers_options
                );
            });
            
            return def;
        },

	});
    return publicWidget.registry.Attendance;
});
