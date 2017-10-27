
from openerp import tools
from openerp.osv import fields,osv
from openerp.addons.decimal_precision import decimal_precision as dp

class hr_technician_hours_report(osv.osv):
    """
    Custom report
    """
    _name = "hr.technician.hours.report"
    _description = "Technician report"
    _auto = False
    _columns = {
        'empname': fields.char('Employee', size=64,readonly=True),
        'empno' : fields.char('EmpNo', size=64,readonly=True),
        'project_name' :fields.char('Project', size=64,readonly=True),
        'task_name' : fields.char('Task', size=64,readonly=True),
        'activity_name' : fields.char('Activity', size=64,readonly=True),
        'earningno':  fields.char('Earning#', size=64,readonly=True),
        'time_spent': fields.float('Time Spent', readonly=True, digits_compute=dp.get_precision('Account')),
        'buget_hours': fields.float('Budget time', readonly=True),  # TDE FIXME master: rename into time
    }

    def _select(self):
        select_str = """
             select min(account_analytic_account.id) as id,
                account_analytic_account.name as project_name,
                project_task.name as task_name,
                project_task_work.name as activity_name,
                project_task_work.activity_time as buget_hours,
                hr_employee.name_related as empname,
                        hr_employee.id as empno,
                        project_task.id as earningno,
                        project_task_work.hours as time_spent               
                
                        """
        return select_str

    def _from(self):
        from_str = """
                project_project
                left join project_task on project_project.id = project_task.project_id
                left join project_task_work on project_task.id = project_task_work.task_id
                left join res_users on res_users.id = project_task_work.user_id
                left join resource_resource on res_users.id = resource_resource.user_id
                left join hr_employee on resource_resource.id = hr_employee.resource_id
                inner join account_analytic_account on account_analytic_account.id = project_project.analytic_account_id
                 """
        return from_str

    def _group_by(self):
        group_by_str = """
            GROUP BY empno,
                empname,
                project_name,
                task_name,
                activity_name,
                earningno,
                time_spent,
                buget_hours
        """
        return group_by_str

    def init(self, cr):
        # self._table = hr_timesheet_report
        tools.drop_view_if_exists(cr, self._table)
        cr.execute("""CREATE or REPLACE VIEW %s as (
            %s
            FROM ( %s )
            %s
            )""" % (self._table, self._select(), self._from(), self._group_by()))

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
