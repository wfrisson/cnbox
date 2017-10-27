import time

from openerp.osv import fields, osv
from openerp.tools.translate import _

class hr_filter_employees_open(osv.osv_memory):
    _name = 'hr.filter.employees.open'
    _description = 'hr.filter.employees.open'
    def open_current_employee(self, cr, uid, ids, context=None):
        
        ts = self.pool.get('hr.employee')
        if context is None:
            context = {}
        view_type = 'form,tree'

        user_ids = self.pool.get('hr.employee').search(cr, uid, [('user_id','=',uid)], context=context)
        if not len(user_ids):
            raise osv.except_osv(_('Error!'), _('Please create an employee and associate it with this user.'))
        ids = ts.search(cr, uid, [('user_id','=',uid)],context=context)
        if len(ids) > 1:
            view_type = 'tree,form'
            domain = "[('id','in',["+','.join(map(str, ids))+"]),('user_id', '=', uid)]"
        elif len(ids)==1:
            domain = "[('user_id', '=', uid)]"
        else:
            domain = "[('user_id', '=', uid)]"
        value = {
            'domain': domain,
            'name': _('Employees Structure'),
            'view_type': 'form',
            'view_mode': view_type,
            'res_model': 'hr.employee',
            'view_id': False,
            'type': 'ir.actions.act_window'
        }
        if len(ids) == 1:
            value['res_id'] = ids[0]
        return value

