from openerp import tools
from openerp.osv import fields, osv

from openerp.addons.decimal_precision import decimal_precision as dp


class hr_att_adjustment_report(osv.osv):
    _name = "hr.att.adjustment.report"
    _description = "Adjusteted attendance report analysis"
    _auto = False
    _columns = {
        'date_range': fields.char('Date ',size = 100, readonly=True),
        'create_date': fields.datetime('Creation Date', readonly=True),
        'employee_id': fields.many2one('hr.employee', "Employee's Name", readonly=True),
        'week':fields.many2one('hr.timesheet.sheet','Week', readonly=True), 
        'paid_hours':fields.float('Paid Hours', readonly=True,digits_compute=dp.get_precision('Account')), #will be later on converted to schedule hours 
        'bank_hours':fields.float('Bank hours', readonly=True,digits_compute=dp.get_precision('Account')), #will be later on converted to schedule hours
        'input_adjustment':fields.float('Hours Adjustment', readonly=True,digits_compute=dp.get_precision('Account')), #will be later on converted to schedule hours
        'over_time_adjustemnt':fields.selection([('Bank_vertime','Bank Overtime'),('Paid','Get Paid'),('adjust_from_bank','Adjust From Bank')], 'Decision', required=True),
        'daily_work_hours':fields.float('Daily Hours', readonly=True,digits_compute=dp.get_precision('Daily Work')), #will be later on converted to schedule hours
        'worked_hours':fields.float('Total Attendance', readonly=True,digits_compute=dp.get_precision('Account')), #will be later on converted to schedule hours
        'schedule_hours':fields.float('Schedule Hours', readonly=True,digits_compute=dp.get_precision('Account')), #will be later on converted to schedule hours
        'ot_ut':fields.float('OT/UT', readonly=True,digits_compute=dp.get_precision('Account')),
        'remarks':fields.selection([('Deficiency','Deficiency'),('Ok','Ok'),('Overtime','Overtime')],'State'),
        'state': fields.selection([
             ('new', 'New'),
            ('draft','Open'),
            ('confirm','Waiting Approval'),
            ('done','Approved')],
            'Status', readonly=True),
    }
    _order = 'create_date desc'
    def init(self, cr):
        tools.drop_view_if_exists(cr, 'hr_att_adjustment_report')
        cr.execute("""
            create or replace view hr_att_adjustment_report as (
                 select
                     aa.id,
                    aa.create_date,
                    aa.name,
                    aa.employee_id,
                    sum(aa.worked_hours) as daily_work_hours,
                    sum(ts.total_hours) as worked_hours,
                    sum(ts.over_under_time) as ot_ut,
                    sum(ln.input_hours) as input_adjustment
                    from hr_attendance aa
                    left join hr_timesheet_sheet_sheet ts
                    on aa.sheet_id = ts.id
                    left join attendance_adjustment_lines ln
                    on ln.timesheet_idd = ts.id
                    group by
                    aa.id,
                    aa.employee_id,
                    aa.create_date,
                    ts.state,
                    ts.total_hours,
                    ts.over_under_time,
                    ts.remarks,
                    ln.over_time_adjustemnt)
        """)
