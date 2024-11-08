from pytz import UTC, timezone
from datetime import datetime
from odoo import fields


def datetime_to_odoo(datetime_val, datetime_format=None, from_tz=False, to_utc=False):
    """return datetime in odoo's standard format
    datetime_val: string(have datetime in odoo's datetime format)/datetime object
    :datetime_format: format of date, default "%Y-%m-%d %H:%M:%S"
    :from_tz: Timezone of datetime_val
    :to_utc: True/False
    :return string
    """
    datetime_format = datetime_format or "%Y-%m-%d %H:%M:%S"
    datetime_val = datetime.strptime(datetime_val, datetime_format)
    if to_utc:
        return get_UTC_datetime(from_tz, datetime_val)
    return fields.Datetime.to_string(datetime_val)


def get_UTC_datetime(from_tz, datetime_val):
    """return UTC datetime by converting
    :from_tz: timezone of datetime_val
    :datetime_val: string(have datetime in odoo's datetime format)/datetime object
    :return: string
    """
    if not isinstance(datetime_val, datetime):
        datetime_val = fields.Datetime.from_string(datetime_val)

    # get timezone
    if not from_tz:
        from_tz = datetime_val.tzinfo
    else:
        from_tz = timezone(from_tz)

    # assumes datetime already in UTC
    if not from_tz:
        return datetime_val

    # convert datetime in UTC
    datetime_UTC = from_tz.localize(datetime_val).astimezone(UTC)
    datetime_UTC = fields.Datetime.to_string(datetime_UTC)
    return datetime_UTC
