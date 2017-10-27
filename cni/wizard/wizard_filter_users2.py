import time
from openerp.osv import fields, osv
from openerp.tools.translate import _


class filter_users_admin(osv.osv_memory):

    _name = 'filter.users.admin'
    _description = 'hr.filter.employees.open'

    def filter_users(self, cr, uid, ids, context=None):

        domain = ""
        value = {}
        raise osv.except_osv(('called'),("d"))
        sql = """ SELECT res_users.id from res_users 
                    inner join res_groups_users_rel 
                    on res_groups_users_rel.uid  =res_users.id
                    inner join res_groups 
                    on res_groups.id = res_groups_users_rel.gid
                    where res_users.id = """+str(uid)+ """ 
                    and res_groups.name in ('CNI Administrator') """

        cr.execute(sql)
        res = cr.fetchone()

        if context is None:
            context = {}
        view_type = 'form,tree'


        if len(res)>0:
            sql2 = """SELECT res_users.id from res_users 
            	inner join res_groups_users_rel on
                    res_groups_users_rel.uid = res_users.id
            	inner join res_groips on 
            	res_groups.id = res_groups_users_rel.gif
            where res_groups.name in ('GSS Support') """
            cr.execute(sql2)
            users = cr.fetchall()

            domain = "[('id','not in',["+','.join(map(str,users ))+"])"
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

