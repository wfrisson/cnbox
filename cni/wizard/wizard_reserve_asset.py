# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from openerp.osv import fields, osv
from openerp.tools.translate import _
import datetime

class wizard_reserve_asset(osv.osv_memory):
    
    def get_tool(self, cr, uid, ids):
        obj_asset = self.browse(cr, uid, ids['active_id'])
        return obj_asset.id
    
    _name = 'wizard.reserve.asset'
    _description = 'Reserve Assetfor employee'
    _columns = {
       'tool_id': fields.many2one('asset.asset', 'Tool', required=True, help="Tool"),
       'name': fields.many2one('hr.employee', 'Reserve For', required=True, help="Select an employee to reserve tool for him"),
       'from_date': fields.date('Date From',required=True),
       'to_date': fields.date('Date To',required=True),
    }

    _defaults = {
         'tool_id':get_tool,
           }

    def reserve_tool(self, cr, uid, ids, data):
        for f in self.browse(cr, uid, ids):
            
            #Get Current User
            user = self.pool.get('res.users').browse(cr,uid,uid).name
            user_date = user +" On "+str(datetime.date.today())
            
            
            self.pool.get('emp.tools.reservation').create(cr,uid,{
                'name':f.name.id,
                'tool_to_reserve':f.tool_id.id, 
                'date_from':f.from_date,                                               
                'date_to':f.to_date, 
                'reserved_by':user_date,
                'issued':False
                 })
        return

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
