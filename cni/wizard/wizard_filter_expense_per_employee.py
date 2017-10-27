import time

from openerp.osv import fields, osv
from openerp.tools.translate import _

class hr_filter_employees_expenses(osv.osv_memory):
    _name = 'hr.filter.employees.expenses'
    _description = 'hr.filter.employees.open'
    
    def filter_users(self, cr, uid, ids, context=None):

        domain = ""
        value = {}
#         raise osv.except_osv(('called'),("d"))
        sql = """ SELECT res_users.id from res_users 
                    inner join res_groups_users_rel 
                    on res_groups_users_rel.uid  =res_users.id
                    inner join res_groups 
                    on res_groups.id = res_groups_users_rel.gid
                    where res_users.id = """+str(uid)+ """ 
                    and res_groups.name in ('CNI Administrator2') """

        cr.execute(sql)
        res = cr.fetchall()

        if context is None:
            context = {}
        view_type = 'form,tree'

        if len(res)>0:
            sql2 = """SELECT res_users.id from res_users 
                     inner join res_groups_users_rel on
                     res_groups_users_rel.uid = res_users.id
                    inner join res_groups on 
                    res_groups.id = res_groups_users_rel.gid
            where res_groups.name in ('CNI Admin') """
            cr.execute(sql2)
            users = cr.fetchall()
            
            if len(users) >1:
                list1 = self.pool.get('res.users').search(cr, uid, [('id','in',users)], context=context)
                domain = "[('id','not in',"+str(list1)+")]"
            elif len(users) == 1:
                list1 = self.pool.get('res.users').search(cr, uid, [('id','=',users[0])], context=context)
                domain = "[('id','!=',"+list1[0]+")]"
            view_type = 'tree,form'
            value = {
                    'domain': domain,
                    'name': _('Users'),
                    'view_type': 'form',
                    'view_mode': view_type,
                    'res_model': 'res.users',
                    'view_id': False,
                    'type': 'ir.actions.act_window'
                    }

            return value

    
    
    
    def open_current_employee(self, cr, uid, ids, context=None):
        
        ts = self.pool.get('hr.employee')
        if context is None:
            context = {}
        view_type = 'form,tree'

        user_ids = self.pool.get('hr.employee').search(cr, uid, [('user_id','=',uid)], context=context)
        if not len(user_ids):
            raise osv.except_osv(_('Error!'), _('You donot have employment record, only employees can submit expense request.'))
        ids = ts.search(cr, uid, [('user_id','=',uid)],context=context)
        if len(ids) > 1:
            view_type = 'tree,form'
            domain = "[('employee_id','in',["+','.join(map(str, ids))+"]),('user_id', '=', uid)]"
        elif len(ids)==1:
           domain = "[('employee_id','=',"+str(ids[0])+")]"
        else:
            domain =  "[('employee_id','=',"+str(ids[0])+")]"
        value = {
            'domain': domain,
            'name': _('My Expenses'),
            'view_type': 'form',
            'view_mode': view_type,
            'res_model': 'hr.expense.expense',
            'view_id': False,
            'type': 'ir.actions.act_window'
        }
        if len(ids) == 1:
            value['res_id'] = ids[0]
        return value

    def filter_projects(self, cr, uid, ids, context=None):
        
        view_type = 'kanban,tree,form,gantt'
        if context is None:
            context = {}
        user_ids = self.pool.get('hr.employee').search(cr, uid, [('user_id','=',uid)], context=context)
        if not len(user_ids):
            raise osv.except_osv(_('Error!'), _('You donot have employment record, You must be employee of the company.'))
        else:
            rec_hr = self.pool.get('hr.employee').browse(cr,uid,user_ids[0])
            if rec_hr.department_id.name == 'Telus':
                
                domain = "[('project_types','=','Telus')]"
             
            elif rec_hr.department_id.name == 'Pre-Assembly':
                    view_type = 'kanban,tree,form,gantt'
                    domain = "[('project_types','=','Pre-Assembly')]"
            else:
                domain = []
            value = {
                'domain': domain,
                'name': _('Projects'),
                'view_type': 'form',
                'view_mode': view_type,
                'res_model': 'project.project',
                'view_id': False,
                'type': 'ir.actions.act_window'
            }
        if len(user_ids) == 1:
            value['res_id'] = user_ids[0]
        return value


    def filter_tasks(self, cr, uid, ids, context=None):
            
            view_type = 'kanban,tree,form,gantt'
            if context is None:
                context = {}
    
            user_ids = self.pool.get('hr.employee').search(cr, uid, [('user_id','=',uid)], context=context)
            if not len(user_ids):
                raise osv.except_osv(_('Error!'), _('You donot have employment record, You must be employee of the company.'))
            else:
                rec_hr = self.pool.get('hr.employee').browse(cr,uid,user_ids[0])
                if rec_hr.department_id.name == 'Pre-Assembly':
                    
                    project_ids = self.pool.get('project.project').search(cr, uid, [('project_types','=','Pre-Assembly')], context=context)
                    if project_ids:
                        domain = "[('project_id','in',"+str(project_ids)+")]"
                    else:
                        domain = "[]"
                 
                elif rec_hr.department_id.name == 'Telus':
                        project_ids = self.pool.get('project.project').search(cr, uid, [('project_types','=','Telus')], context=context)
                        if project_ids:
                            domain = "[('project_id','in',"+str(project_ids)+")]"
                        else:
                            domain = "[]"
                else:
                    domain = "[]"
                value = {
                    'domain': domain,
                    'name': _('Task'),
                    'view_type': 'form',
                    'view_mode': view_type,
                    'res_model': 'project.task',
                    'view_id': False,
                    'type': 'ir.actions.act_window'
                }
            
            return value