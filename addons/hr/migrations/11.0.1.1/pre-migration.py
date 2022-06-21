from openupgradelib import openupgrade


def _fill_employee_data(env):
    openupgrade.logged_query(env.cr, """
        ALTER TABLE hr_employee
        ADD COLUMN active BOOLEAN,
        ADD COLUMN name VARCHAR,
        ADD COLUMN user_id INTEGER
    """)
    openupgrade.logged_query(env.cr, """
        UPDATE hr_employee AS emp
        SET active = res.active,
            name = res.name,
            user_id = res.user_id
        FROM resource_resource res WHERE emp.resource_id = res.id
    """)

@openupgrade.migrate()
def migrate(env, version):
    _fill_employee_data(env)
