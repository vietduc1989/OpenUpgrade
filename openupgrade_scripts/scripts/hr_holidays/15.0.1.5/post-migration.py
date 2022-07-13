import logging

from openupgradelib import openupgrade

from odoo import api
from odoo.exceptions import ValidationError

from odoo.addons.hr_holidays.models.hr_leave import HolidaysRequest

_logger = logging.getLogger(__name__)


@api.constrains("holiday_allocation_id")
def _check_allocation_id(self):
    """Don't raise ValidationError in _check_allocation_id method."""
    try:
        return HolidaysRequest._check_allocation_id._original_method(self)
    except ValidationError:
        _logger.warning(
            "Could not find an allocation of type %s for the time off with ID %s."
            "\nRequires allocation of this type is now set to 'No Limit'."
            "\nPlease review requires allocation of this type manually "
            "after the migration."
            % (self.holiday_status_id.mapped("display_name"), self.ids)
        )


_check_allocation_id._original_method = HolidaysRequest._check_allocation_id
HolidaysRequest._check_allocation_id = _check_allocation_id


def _fill_hr_leave_type_holiday_allocation_id(env):
    leaves = env["hr.leave"].search(
        [
            ("holiday_status_id.requires_allocation", "=", "yes"),
            ("date_from", "!=", False),
            ("date_to", "!=", False),
        ],
        order="date_to, id",
    )
    leaves._compute_from_holiday_status_id()


def _map_hr_leave_allocation_date_to(env):
    env.cr.execute(
        """
        SELECT id FROM hr_leave_allocation
        WHERE state = 'validate' AND %s IS NOT NULL
        """,
        (openupgrade.get_legacy_name("date_to"),),
    )
    allocation_ids = [d[0] for d in env.cr.fetchall()]
    allocations_to_update = env["hr.leave.allocation"]
    for hla in env["hr.leave.allocation"].browse(allocation_ids):
        leave_unit = "number_of_%s_display" % (
            "hours" if hla.holiday_status_id.request_unit == "hour" else "days"
        )
        if hla.max_leaves >= sum(hla.taken_leave_ids.mapped(leave_unit)):
            allocations_to_update |= hla

    hla_ids = str(tuple(allocations_to_update.ids)).replace(",)", ")")
    # Using SQL to update date_to
    openupgrade.logged_query(
        env.cr,
        """
        UPDATE hr_leave_allocation
        SET date_to = %s
        WHERE id IN %s
        """
        % (openupgrade.get_legacy_name("date_to"), hla_ids),
    )


@openupgrade.migrate()
def migrate(env, version):
    _fill_hr_leave_type_holiday_allocation_id(env)
    openupgrade.load_data(env.cr, "hr_holidays", "15.0.1.5/noupdate_changes.xml")
    _map_hr_leave_allocation_date_to(env)
