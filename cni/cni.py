from openerp.osv import fields, osv
import datetime
import time
import logging
from datetime import date, datetime, timedelta
from openerp.tools import ustr, DEFAULT_SERVER_DATE_FORMAT as DF
import json
import random
import dateutil
import urllib2
import math
import openerp
import openerp.addons.decimal_precision as dp
from openerp import SUPERUSER_ID, tools
from openerp.tools.translate import _

_logger = logging.getLogger(__name__)

class resource_calendar(osv.osv):
    """this is inheired to change the format from float to datetime for comparison of sign in and out time 
        mdul resource
    """
    _name = "resource.calendar"
    _inherit = "resource.calendar"
    _description = "Attendance inh"
    _columns = {
    }
    def unlink(self, cr, uid, ids, context=None):
            linesids = self.pool.get('resource.calendar.attendance').search(cr,uid,[('calendar_id','=',ids[0])])
            if linesids:

                for f in linesids:
                    _logger.info("=chiled ids========================================== : %r", f)
                    self.pool.get('resource.calendar.attendance').unlink(cr,uid,f)
            result = super(osv.osv, self).unlink(cr, uid, ids, context)
            return

class resource_calendar_attendance(osv.osv):
    """this is inheired to change the format from float to datetime for comparison of sign in and out time 
        mdul resource
    """
    _name = "resource.calendar.attendance"
    _inherit = "resource.calendar.attendance"
    _description = "Attendance inh"
    _columns = {
        'hour_from' : fields.float('Work from', required=True, help="Start and End time of working."),
        'hour_to' : fields.float("Work to", required=True),
    }

class hr_attendance(osv.osv):
    _name = "hr.attendance"
    _inherit = "hr.attendance"
    _description = "Attendance inh"
    _columns = {
    }

    def chk_constraints(self,cr, uid,current,employee_id,context = None):
        contract = self.pool.get('hr.contract').search(cr, uid, [('employee_id', '=', employee_id)])
        if contract:
            recontract = self.pool.get('hr.contract').browse(cr, uid, contract[0])
            parent_rsc_id = recontract.working_hours.id
            if not recontract.date_start or not recontract.date_end:
                raise osv.except_osv(('Improper contract setting'), (
                'Contract start and end date are not properly set, Contact your HR Manager to set proper dates for your contract'))
            else:

                current = current
                # current = datetime.now()
                # current = self.name
                cur_time = current.time()
                # cur_time = cur_time
                # raise osv.except_osv(('cur_time'),(cur_time))
                cur_date_obj = current.date()
                cur_date_string = current.date().strftime('%Y-%m-%d')
                contrect_start_date = recontract.date_start
                contract_end_date = recontract.date_end
                if cur_date_string < contrect_start_date or cur_date_string > contract_end_date:
                    raise osv.except_osv(('Date Out of contract'), ('Today date doesnot fall in your contract,'))
                else:
                    weekday_today_name = datetime.strptime(cur_date_string, '%Y-%m-%d').strftime('%A')
                    weekday_today_numb = datetime.strptime(cur_date_string, '%Y-%m-%d').strftime('%w')
                    weekday_today_numb_int = int(weekday_today_numb) - 1
                    if not recontract.working_hours:
                        raise osv.except_osv(('Working Schedule is not set in your job contract'), (
                        'Working schedule is not found for your attendance. Contact your HR Manager to define your working schedule on your contract'))
                    else:
                        rsc_id = self.pool.get('resource.calendar').browse(cr, uid, recontract.working_hours.id)
                        if not rsc_id.attendance_ids:
                            raise osv.except_osv(('Weekly timings are missing'), (
                            'Your Time schedule has been defined but your weekly working hours for each day are not set.'))
                        else:
                            week_days_ids = self.pool.get('resource.calendar.attendance').search(cr, uid, [
                                ('calendar_id', '=', rsc_id.id), ('dayofweek', '=', weekday_today_numb_int)])

                            if week_days_ids:
                                rec_weekday = self.pool.get('resource.calendar.attendance').browse(cr, uid,
                                                                                                   week_days_ids)
                                # signin_time = cur_time
                                signin_time = cur_time

                                num = rec_weekday.hour_from
                                split_num = str(num).split('.')
                                int_part = int(split_num[0])
                                if int_part > 23:
                                    raise osv.except_osv(('Wrong time Found'), (
                                    'Please enter a correct time in Work From field. Time should be in 24 hour format'))
                                decimal_part = int(split_num[1])
                                if decimal_part > 59:
                                    raise osv.except_osv(('Wrong time Found'), (
                                    'Please enter a correct time in Work From field. Time should be in 24 hour format'))
                                time_from = "%02d:%02d" % (int_part, decimal_part)
                                allowed_time_start = time_from
                                #                                 raise osv.except_osv((allowed_time_start),(signin_time))
                                num2 = rec_weekday.hour_to
                                split_num2 = str(num2).split('.')
                                int_part2 = int(split_num2[0])
                                if int_part2 > 23:
                                    raise osv.except_osv(('Wrong time Found'), (
                                    'Please enter a correct time in Work To field. Time should be in 24 hour format'))
                                decimal_part2 = int(split_num2[1])
                                if decimal_part2 > 59:
                                    raise osv.except_osv(('Wrong time Found'), (
                                    'Please enter a correct time in Work To field. Time should be in 24 hour format'))
                                time_to = "%02d:%02d" % (int_part2, decimal_part2)
                                allowed_time_end = time_to

                                if allowed_time_start and allowed_time_end:
                                    # so allowed time in and out on that day exists in table now comapare it
                                    # first extract time from date time store in db
                                    # if signin_time < dateutil.parser.parse(allowed_time_start).time() or signin_time >dateutil.parser.parse(allowed_time_end).time():
                                    if signin_time < datetime.strptime(allowed_time_start,
                                                                       '%H:%M').time() or signin_time > datetime.strptime(
                                            allowed_time_end, '%H:%M').time():

                                        _logger.info("Employee wants to sign on === : %r",
                                                     signin_time.strftime("%H:%M"))
                                        raise osv.except_osv(
                                            ('You are not allowed to sing in on ' + signin_time.strftime("%H:%M")), (
                                            'you allowed timiings on ' + str(weekday_today_name) + ' are (' + str(
                                                allowed_time_start) + ') To (' + str(allowed_time_end) + ')'))
                                    else:
                                        return True
                                        #                                         raise osv.except_osv(('you are cleared'),(''))
                                else:
                                    raise osv.except_osv(
                                        ('Allowed timings for ' + str(weekday_today_name) + ' missing'), (
                                        ' There is no start and end time avaialbe on this day. Contact Your HR Manager to Set start and clossing timings for mentioned day'))
                            else:

                                raise osv.except_osv(('No Work Schedule on ' + str(weekday_today_name)),
                                                     ('You are not allowed to punch attedance'))
        else:
            raise osv.except_osv(('No Contract Found'),
                                 ('Contact your HR Manager to create a job contract before punching your attendance'))

    def create(self, cr, uid, vals, context=None, check=True):
        employee_id = vals['employee_id']
        current = datetime.now()
        res = self.chk_constraints(cr, uid, current,employee_id, context)
        if res== True:
            result = super(osv.osv, self).create(cr, uid, vals, context)
            return result

    def write(self, cr, uid, ids, vals, context=None):
        obj = self.browse(cr, uid, ids, context=context)[0]
        employee_id = vals.get('employee_id')
        if not employee_id:
            employee_id = obj.employee_id.id

        current1 = vals.get('name')
        if not current1:
            current1 = obj.name
        current = datetime.strptime(current1, '%Y-%m-%d %H:%M:%S')

        res = self.chk_constraints(cr, uid,current,employee_id, context)
        if res== True:
            result = super(osv.osv, self).write(cr, uid, ids, vals, context)
            return result

class product_template(osv.osv):
    _name = "product.template"
    _inherit = "product.template"
    _columns = {
        'sku': fields.char('SKU', size=64, required=True),
        'dimension': fields.char('Dimension', size=64),
    }
product_template()   
    
class asset_requisition(osv.osv):
    """"Asset requisition or tools requisition are the same things"""
    
    def _get_defualt_value_material(self, cr, uid, context={}):
        if context:
            if 'project_id' in context:
                return context['project_id']
        return None
    
    def create(self, cr, uid, vals, context=None, check=True):
        result = super(osv.osv, self).create(cr, uid, vals, context)
        return result
    
    def send_request(self, cr, uid, ids, context=None):
        for f in self.browse(cr,uid,ids):
            tr_no = self.set_transaction_no(cr, uid, ids,'asset_requisition')
            update_state = self.write(cr, uid, ids, {'state':'Waiting','transaction_no':tr_no})
            if update_state:
                line_idss = self.pool.get('asset.requisition.lines').search(cr, uid, [('requisition_id','=',f.id)])
                if line_idss:
                    rec_lines = self.pool.get('asset.requisition.lines').browse(cr,uid,line_idss)
                    for line in rec_lines:
                        update_status = self.pool.get('asset.requisition.lines').write(cr,uid,line.id,{'state':'Waiting'})
                        _logger.info("=....................Sending Asset requistion request for asset lines id %d=", line.id)
                        
                        wh_state =  self.pool.get('asset.state').search(cr, uid, [('team','=',3),('name','=','Reserved')])
                        if wh_state:
                            update_wh = self.pool.get('asset.asset').write(cr,uid,line.name.id,{
                                                       'warehouse_state_id':wh_state[0],
                                                       'user_id':f.employee.id,
                                                       'reserved':True})
                        else:
                            raise osv.except_osv(('Asset State Not Defined'),("Need an Asset State in Asset State objects with the name Reserved. Please Define one"))
                                    
        return
    
    def _get_asset_state(self, cr, uid, team, internal_state):
        state_id = self.pool.get('asset.state').search(cr, uid, [('team','=',team),('name','=',internal_state)])
        if state_id:
            return state_id[0]
        else:
            return False
    
    def approve_request(self, cr, uid, ids, context=None):
        
        denied = ''
        for f in self.browse(cr, uid, ids, context):
            #update 
            line_ids = self.pool.get('asset.requisition.lines').search(cr, uid, [('requisition_id','=',f.id)])
            if line_ids:
                reconcile_rec = self.pool.get('asset.requisition.lines').browse(cr,uid,line_ids)
                for line in reconcile_rec:
                     
                    #first check if this tool is available
                    tool_id = self.pool.get('asset.asset').search(cr, uid,[('id','=',line.name.id)])
                    if tool_id:
                        tool_rec = self.pool.get('asset.asset').browse(cr,uid,tool_id[0])
                        if not tool_rec.issued:
                            #updae req lines state
                            update_status = self.pool.get('asset.requisition.lines').write(cr,uid,line.id,{'state':'Issued'})
                            #get wharhouse states
                            wh_state =  self.pool.get('asset.state').search(cr, uid, [('team','=',3),('name','=','Issued')])
                            _logger.info("=<(-_-)>.whare house state id %d=", wh_state)
                            if wh_state:
                                update_wh = self.pool.get('asset.asset').write(cr,uid,line.name.id,{
                                                           'warehouse_state_id':wh_state[0],
                                                           'user_id':f.employee.id,
                                                           'issued':True})
                                if update_wh:
                                     #if asset is updated, update asset requisition
                                     self.write(cr, uid, ids[0], {'state':'Approved','aprroved_by':uid})
    #                                             self.pool.get('asset.requisition.lines').write(cr, uid, line.id, {'state':'Issued'})
                            else:
                                raise osv.except_osv(('Error'),("No appropriate state found for Issuance, e.g, Issued"))
                        else:
                            denied += tool_rec.name +"\n" 
            
            else:       
                    
                raise osv.except_osv(('Error'),("Cannot approve with empty list of tools, go back and mention some tools"))
        
        if denied:
             raise osv.except_osv(('Tools not available,reclaim from previous technician and approve this request later on.'),(denied))
        return
        
    
        
    def _set_name(self, cr, uid, ids, name, args, context=None):
        result = {}
       
        for f in self.browse(cr, uid, ids, context=context):
            result[f.id] = " (" + f.employee.name+")"
        return result
    
    def set_transaction_no(self, cr, uid, ids,object):
        string = ""
        if object == 'daily_sale_reconciliation':
            substr = 'DS'
        elif  object == 'asset_requisition':
            substr = 'TR'
        elif object == 'get_client_stock':
            substr = 'CS'
        
        for f in self.browse(cr, uid, ids):
            sql = """SELECT max(id) FROM """+str(object)
            cr.execute(sql)
            numb = cr.fetchone()
            if numb[0] is not None or numb[0] > 0:
                numb = int(numb[0])+1
                
            else:
                numb = 1    
            string  = str(substr)+"-"+str(numb)
        return string
    
    def cancelled_request(self, cr, uid, ids, context=None):
        for f in self.browse(cr,uid,ids):
            self.write(cr, uid, f.id, {'state':'Cancel','aprroved_by':uid})
            if f.state =='Waiting':
                line_idss = self.pool.get('asset.requisition.lines').search(cr, uid, [('requisition_id','=',f.id)])
                if line_idss:
                    rec_lines = self.pool.get('asset.requisition.lines').browse(cr,uid,line_idss)
                    for line in rec_lines:
                        _logger.info("=....................Cancelling id %d=", line.id)
                        wh_state =  self.pool.get('asset.state').search(cr, uid, [('team','=',3),('name','=','Available')])
                        if wh_state:
                            update_wh = self.pool.get('asset.asset').write(cr,uid,line.name.id,{
                                                       'warehouse_state_id':wh_state[0],
                                                       'user_id':None,
                                                       'reserved':False})
                        else:
                            raise osv.except_osv(('Asset State (Available) Not Found'),("Cancelling a request must make tools available "))        
        return
    def set_draft(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids[0], {'state':'Draft'})
        return
    
    def onchange_project(self, cr, uid, ids, project_id):
        res =  {}
        res['value'] = {'employee': None}
        return res
    
    _name = "asset.requisition"
    _columns = {
        'name':fields.function(_set_name, method=True,  size=256, string='Required By',type='char'),
        'transaction_no':fields.char('No.',readonly = True,size = 50), 
        'project': fields.many2one('project.project', 'Project', required=True, ondelete='restrict'),
        'employee': fields.many2one('res.users', 'Required By',domain = [('work_on_task','=',True)], required=True, ondelete='restrict'),
        'date_requisted': fields.date('Date ',required=True),
        'date_returned': fields.date('Date Return',readonly=True),
        'aprroved_by': fields.many2one('res.users', 'Approved By',readonly = True),
        'returned_to': fields.many2one('res.users', 'Returned To',readonly = True),
        'date_approved': fields.date('Approved On', readonly = True,),
        'requisition_lines_ids': fields.one2many('asset.requisition.lines', 'requisition_id', 'Assets',required=True),
        'note': fields.text('Any Note'),
        'state': fields.selection([('Draft','Draft'),
                                   ('Waiting','Waiting'),
                                   ('Approved','Approved'),
                                   ('Cancel', 'Cancel'),
                                   ('Returned', 'Returned')
                                  ],
                                  'Status', required=True),
    }
    
    _defaults = {
                 'state':'Draft',
                 'project':  _get_defualt_value_material             
                 
    }
    
class asset_requisition_lines(osv.osv):
    """ Asset Requiston lines """
    
    def create(self, cr, uid, vals, context=None, check=True):
        result = super(osv.osv, self).create(cr, uid, vals, context)
        wh_state =  self.pool.get('asset.state').search(cr, uid, [('team','=',3),('name','=','Reserved')])
        if wh_state:
            update_wh = self.pool.get('asset.asset').write(cr,uid,vals['name'],{
                                                       'warehouse_state_id':wh_state[0],
                                                       'reserved':True})
  
     
    def write(self, cr, uid, ids, vals, context=None, check=True, update_check=True):
        result = super(osv.osv, self).write(cr, uid, ids, vals, context)
        return result
     
    def unlink(self, cr, uid, ids, context=None):
        result = super(osv.osv, self).unlink(cr, uid, ids, context)
        return result 
    
    def pickuplocation(self, cr, uid, ids, name, args, context=None):
        result = {}
        for f in self.browse(cr,uid,ids):
                
                result[f.id] = f.name.property_stock_asset.name
        return result
    
    
    def return_asset(self, cr, uid, ids, context=None):
        
        for f in self.browse(cr, uid, ids, context):
                    #get wharhouse states
            wh_state =  self.pool.get('asset.state').search(cr, uid, [('team','=',3),('name','=','Available')])
            if wh_state:
                _logger.info("=wh_state========================================== : %r", wh_state[0])
                self.pool.get('asset.asset').write(cr,uid,line.name.id,{
                                           'warehouse_state_id':wh_state[0],
                                           'user_id':False,
                                           'issued':False})
                #if asset is updated, update asset requisition
                self.write(cr, uid, ids[0], {'state':'Returned'})
            else:
                _logger.info("=No appropriate state found e.g Issued")
        return
    
    _name = 'asset.requisition.lines'
    _description = "This object store fee types"
    _columns = {
        'name': fields.many2one('asset.asset', 'Tool', required = True),      
        'product_qty': fields.float('Quantity',),
        'project_id':fields.related('requisition_id','project',type='many2one', relation = 'project.project', string='project', readonly=True),
        'asset_tag':fields.related('name','asset_number',type='char',  string='Asset Tag', readonly=True),
        'image':fields.related('name','image',type='binary',  string='Image', readonly=True),
        'requisition_id': fields.many2one('asset.requisition','Requisition'),
        'date_requisted': fields.related('requisition_id','date_requisted',type='date',  string='Required Date'),		
        'reserved_by': fields.related('requisition_id','employee',type='many2one',  relation = 'res.users', string='Reserved By'),
        'approved_by': fields.related('requisition_id','aprroved_by',type='many2one',  relation = 'res.users', string='Approved By'),
        'pickup_location': fields.char('PickUp Location',size = 150),
        'state':fields.selection([('Waiting','Waiting'),('Issued','Issued'),
                                   ('Not-Issued', 'NotIssued')
                                   ],string = 'Status'),
        'notes':fields.text('Notes'),
        'price_unit': fields.float('Unit Price'),
        'total':fields.float('Total'),
        
    }
    _sql_constraints = [  
        ('Duplicated', 'unique (name,requisition_id)', 'Tooles is already requested in this requisition')
    ] 
    _defaults = {
    }
asset_requisition_lines()


class return_tools_by_employee(osv.osv):
    
    def create(self, cr, uid, vals, context=None, check=True):
        process_exists = self.search(cr, uid, [('employee','=',vals['employee']),('state','in',['Draft','Display_Tools'])])
        if process_exists:
            rec = self.browse(cr,uid,process_exists[0])
            raise osv.except_osv(('A Return process No.'+str(rec[0].transaction_no)+' already exists:'+str(rec[0].state)),("You can not initiate multiple return process at the same time.\n Please Re-open "+str(rec[0].transaction_no)))
        else:    
            result = super(osv.osv, self).create(cr, uid, vals, context)
        return result
    
    def _set_name(self, cr, uid, ids, name, args, context=None):
        result = {}
       
        for f in self.browse(cr, uid, ids, context=context):
            result[f.id] = " (" + f.employee.name+")"
        return result
    
    def set_toolsreturn_no(self, cr, uid, ids,object):
        string = ""
        for f in self.browse(cr, uid, ids):
            sql = """SELECT max(id) FROM return_tools_by_employee """
            cr.execute(sql)
            numb = cr.fetchone()
            if numb[0] is not None or numb[0] > 0:
                numb = int(numb[0])+1
                
            else:
                numb = 1    
            string  = 'RT-'+"-"+str(numb)
        return string
    
    def show_tools(self, cr, uid, ids, context=None):
        for f in self.browse(cr,uid,ids):
            tr_no = self.set_toolsreturn_no(cr, uid, ids,'asset_requisition')
            self.write(cr, uid, ids, {'state':'Display_Tools','transaction_no':tr_no})
            line_ids = self.pool.get('asset.asset').search(cr, uid, [('user_id','=',f.employee.id)])
            if not line_ids:
                raise osv.except_osv(('Cannot Proceed'),("Seems "+str(f.employee.name) +"Has returned all tools"))
            else:
                for tool in line_ids:
                    _logger.info("=....................showing asset for be returned Asset %d=", tool)
                    self.pool.get('return.emp.tool.lines').create(cr,uid,{'name':tool,'parent_return_id':f.id})
        return
    
    def return_selected_tools(self, cr, uid, ids, context=None):
        for f in self.browse(cr,uid,ids):
            emty = True
            returned = self.write(cr, uid, ids, {'state':'Returned'})
            if returned:
                line_ids = self.pool.get('return.emp.tool.lines').search(cr, uid, [('parent_return_id','=',f.id)])
                if line_ids:
                    rec_assetlines = self.pool.get('return.emp.tool.lines').browse(cr,uid,line_ids)
                    for tool in rec_assetlines:
                        if tool.return_this_tool:
                            emty = False
                            _logger.info("=....................Returning Asset %d=", tool)
                            #update requsition lines with status returned
                            wh_state =  self.pool.get('asset.state').search(cr, uid, [('team','=',3),('name','=','Available')])
                            if wh_state:
                               _logger.info("=wh_state========================================== : %r", wh_state[0])
                               self.pool.get('asset.asset').write(cr,uid,tool.name.id,{
                                                       'warehouse_state_id':wh_state[0],
                                                       'user_id':False,
                                                       'issued':False,
                                                       'reserved':False})
            if emty:
                raise osv.except_osv(('Select Tool'),("select at least 1 tools to return"))
        return
    
    def default_emo(self, cr, uid, ids):
        return uid
    
    _name = 'return.tools.by.employee'
    _columns = {
        'name':fields.function(_set_name, method=True,  size=256, string='Required By',type='char'),
        'transaction_no':fields.char('No.',readonly = True,size = 50), 
        #'project': fields.many2one('project.project', 'Project', required=True, ondelete='restrict'),
        'employee': fields.many2one('res.users', 'Employee',domain = [('work_on_task','=',True)],readonly=True, required=True, ondelete='restrict'),
        'date_returned': fields.date('Date Return',readonly=True),
        'returned_to': fields.many2one('res.users', 'Returned To',readonly = True),
        'return_lines_ids': fields.one2many('return.emp.tool.lines', 'parent_return_id', 'Assets'),
        'note': fields.text('Any Note'),
        'state': fields.selection([('Draft','Draft'),('Display_Tools','To be returned'),
                                   ('Returned', 'Returned')
                                  ],
                                  'Status', required=False),
    }
    
    _defaults = {
                 'state':'Draft',
                 'employee':default_emo,
                 
    }
return_tools_by_employee()

class return_emp_tool_lines(osv.osv):
    _name = 'return.emp.tool.lines'
    _description = "This object store fee types"
    _columns = {
        'name': fields.many2one('asset.asset', 'Tool'),      
        'product_qty': fields.float('Quantity',),
        'project_id':fields.many2one('project.project', 'Project'),
        'date_issued': fields.date('Date Issued',readonly=True),
        'return_this_tool':fields.boolean('Return This Tool'),
        'parent_return_id': fields.many2one('return.tools.by.employee','Parent Form'),
        
    }
    _sql_constraints = [  
        ('Duplicated', 'unique (name,parent_return_id)', 'Tooles is already added in this return process')
    ] 
    _defaults = {
    }
return_emp_tool_lines()


class daily_material_reconciliation(osv.osv):
    """This object store main business process of consumable products sale and its reconciliation"""
    
    def dispatch_product(self, cr, uid, ids, context=None):
        tr_no = self.pool.get('asset.requisition').set_transaction_no(cr, uid, ids,'daily_sale_reconciliation')
        self.write(cr, uid, ids[0], {'state':'Dispatched','dispatched_by':uid,'transaction_no':tr_no})
        return
    
    def approve_request(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids[0], {'state':'Confirmed','confirmed_by':uid,'date_confirmed':date.today()})
    
        #update status in sales lines
        reconcile_ids = self.pool.get('material.reconcile.lines').search(cr, uid, [('dispatch_id','=',ids[0])])
                
        if reconcile_ids:
            reconcile_rec = self.pool.get('material.reconcile.lines').browse(cr,uid,reconcile_ids)
            for line in reconcile_rec:
                self.pool.get('material.reconcile.lines').write(cr,uid,line.id,{'state':'Confirmed'})
                #also populate the same material tab in billing tab of project
                project_matr = self.pool.get('prj.billing.materials').create(cr,uid,{
                                                    'product':line.name.id,
                                                    'dispatch_qty':line.dispatch_qty, 
                                                    'dispatch_id':ids[0],
                                                     })
                
        return
    
    def set_to_draft(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids[0], {'state':'Draft','dispatched_by':uid})
        #update project tabe
        reconcile_ids = self.pool.get('material.reconcile.lines').search(cr, uid, [('dispatch_id','=',ids[0])])
                
        if reconcile_ids:
            reconcile_rec = self.pool.get('prj.billing.materials').search(cr, uid, [('dispatch_id','=',ids[0])])
            for line in reconcile_rec:
                self.pool.get('prj.billing.materials').unlink(cr,uid,line.id,line)
                                                    
        return
    
    def cancel_sale(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids[0], {'state':'Cancel','confirmed_by':uid})
        #update status in sales lines
        reconcile_ids = self.pool.get('material.reconcile.lines').search(cr, uid, [('dispatch_id','=',ids[0])])
        if reconcile_ids:
            for prd_id in reconcile_ids:
                self.pool.get('material.reconcile.lines').write(cr,uid,prd_id,{'state':'Cancel,',})
        return
    
    def _calculate_saleline_netsum(self, cr, uid, ids, name, args, context=None):
        result = {}
        sum = 0
        for f in self.browse(cr,uid,ids):
            reconcile_ids = self.pool.get('material.reconcile.lines').search(cr, uid, [('dispatch_id','=',ids[0])])
            if reconcile_ids:
                rec_sale_lines = self.pool.get('material.reconcile.lines').browse(cr, uid, reconcile_ids)
                for amount in rec_sale_lines:
                    sum = sum + amount.total
                result[f.id] = sum
        return result
    
    
    def onchange_project(self, cr, uid, ids, project_id):
        res =  {}
        res = {'domain': {'task_id': [('project_id', '=',project_id)]}}
        res['value'] = {'task_id': None, 'employee': None }
        return res
    
    def _get_defualt_value_consumable_material(self, cr, uid, context={}):
        if context:
            if 'project_id' in context:
                return context['project_id']
        return None
    
    _name = "daily.material.reconciliation"
    _columns = {
        'name': fields.function(_calculate_saleline_netsum,string = 'Total Amount.',type = 'char',size = 150,method = True),
        'transaction_no':fields.char('No.',readonly = True,size = 50),
        'project':  fields.many2one('project.project', 'Project', required=True, ondelete='restrict'),
        'task_id':  fields.many2one('project.task', 'Task', required=False, ondelete='restrict'),
        'employee':  fields.many2one('res.users', 'Technician',required=True, domain = [('work_on_task','=',True)], ondelete='restrict'),
        'date_dispatched':  fields.date('Required Date',required=True),
        'date_confirmed':  fields.date('Date Confirm',readonly=True),
        'dispatched_by':  fields.many2one('res.users', 'Dispatch By',readonly=True),
        'confirmed_by':  fields.many2one('res.users', 'Confirm By',readonly=True),
        'client_ref': fields.char('Client Ref #',size = 160,readonly=False),        
		'sale_reconcile_lines_ids': fields.one2many('material.reconcile.lines', 'dispatch_id', 'Products'),
        'note': fields.text('Special Note'),
        'state': fields.selection([('Draft','Draft'),
                                   ('Dispatched','Open'),
                                   ('Confirmed','Confirmed'),
                                   ('Cancel', 'Cancel'),
                                  ],
                                  'Status', required=True),
    }
    
    _defaults = {
                 'state':'Draft',
                'project':_get_defualt_value_consumable_material,
                 
    }
    
class material_reconcile_lines(osv.osv):
    """This object store main business process of consumable products sale and its reconciliationlines """
    
    def create(self, cr, uid, vals, context=None, check=True):
        result = super(osv.osv, self).create(cr, uid, vals, context)
        
        return result
  
     
    def write(self, cr, uid, ids, vals, context=None, check=True, update_check=True):
        result = super(osv.osv, self).write(cr, uid, ids, vals, context)
        return result
     
    
    
    def unlink(self, cr, uid, ids, context=None):
        result = super(osv.osv, self).unlink(cr, uid, ids, context)
        return result 
    
    def gsku(self, cr, uid, ids, field_name, arg, context=None):
        result = {}
        product = self.pool.get('product.product')
        for f in self.browse(cr,uid,ids):
            result[f.id] = product.browse(cr,uid,f.name.id).product_tmpl_id.sku
        return result
    
        
    _name = 'material.reconcile.lines'
    _description = "This object store sale reconcile"
    _columns = {
        'name': fields.many2one('product.product', 'Product'),  
        'sku':fields.function(gsku ,method = True, type='char', string="SKU",),    
        'image':fields.related('name','image',type='binary',  string='Image', readonly=True),
        'dispatch_qty': fields.float('Quantity', required=True),
        'dispatch_id': fields.many2one('daily.material.reconciliation','Material Request ID'),
        'date_dispatched': fields.related('dispatch_id','date_dispatched',type='date',  string='Required Date'),		
        'client_ref': fields.related('dispatch_id','client_ref',type='char',  string='Client Ref #'),		
        'project_id':fields.related('dispatch_id','project',type='many2one', relation = 'project.project', string='project', readonly=True),
        'inventory_location': fields.related('name','product_tmpl_id','property_stock_inventory',type='many2one', relation = 'stock.location', string='Pick Up Location', readonly=True),
        'prod_desc': fields.related('name','product_tmpl_id','description',type='text', string='Descrpition', readonly=True),
        'source': fields.many2one('product.supplierinfo', string='Source'),
        'pickup_location':  fields.char('PickUp Location',size = 160),
        'notes':  fields.text('Notes'),
		'total':fields.float('Total'),
        'state': fields.selection([('Draft','Draft'),
                                   ('Dispatched','Waiting'),
                                   ('Confirmed','Approved'),
                                   ('Cancel', 'Cancel'),
                                  ],
                                  'Status', required=True),
        
        
    }
   
    _defaults = {'state':'Draft'}
material_reconcile_lines()

#--------------------------------------- Clinets sotckable ----------------------------------------------------

class get_client_stock(osv.osv):
    
    def add_to_stock(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, {'state':'Waiting'})
        return
    
    def get_transaction_no(self, cr, uid, team, internal_state):
        return False
    
    def confirm_add_to_stock(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, {'state':'In_Stock'})
        return
    def stock_out(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, {'state':'Waiting_Stockout'})
        return
    
    def confirm_stock_out(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, {'state':'Waiting_Stockout'})
        return
    
    def cancelled_stock_reception(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids[0], {'state':'Cancel'})
        return
    
    def _calculate_stock_netsum(self, cr, uid, ids, name, args, context=None):
        result = {}
        sum = 0
        for f in self.browse(cr,uid,ids):
            reconcile_ids = self.pool.get('material.reconcile.lines').search(cr, uid, [('dispatch_id','=',ids[0])])
            if reconcile_ids:
                rec_sale_lines = self.pool.get('material.reconcile.lines').browse(cr, uid, reconcile_ids)
                for amount in rec_sale_lines:
                    sum = sum + amount.total
                result[f.id] = sum
        return result
    
    def onchange_project(self, cr, uid, ids, project_id):
        res =  {}
        rec_project =  self.pool.get('project.project').browse(cr, uid, project_id)
        res = {'domain': {'partner_id': [('id', '=',rec_project.partner_id.id)]}}
        res['value'] = {'partner_id':rec_project.partner_id.id }
        return res
    
       
    _name = "get.client.stock"
    _columns = {
        'name': fields.char('Name', size=64),
        'project':  fields.many2one('project.project', 'Project', required = True, ondelete='restrict'),
        'partner_id': fields.many2one('res.partner', 'Client',readonly = True),
        'date_received':  fields.date('Date',required=True),
        'location_id': fields.many2one('stock.location', 'Warehouse', required=True, domain=[('usage','<>','view')]),
        'aprroved_by':  fields.many2one('res.users', 'Approved By' ,readonly = True),
        'stock_lines_ids': fields.one2many('client.stock.lines', 'stock_parent_id', 'Stock Lines'),
        'note': fields.text('Any Note'),
        'state': fields.selection([('Draft','New'),
                                   ('Waiting','Waiting'),
                                   ('In_Stock','In Stock'),
                                    ('Waiting_Stockout','Waiting Stockout'),
                                    ('Stockout','Stockout'),
                                   ('Cancel', 'Cancel'),
                                  ],
                                  'State', required=True),
    }
    
    _defaults = {
                 'state':'Draft'
                 
    }
    
class client_stock_lines(osv.osv):
    """ Clinets stock lines """
    
    def create(self, cr, uid, vals, context=None, check=True):
        result = super(osv.osv, self).create(cr, uid, vals, context)
        return result
  
     
    def write(self, cr, uid, ids, vals, context=None, check=True, update_check=True):
        result = super(osv.osv, self).write(cr, uid, ids, vals, context)
        return result
     
    def unlink(self, cr, uid, ids, context=None):
        result = super(osv.osv, self).unlink(cr, uid, ids, context)
        return result 
    
    def onchange_qty(self, cr, uid, ids, qty,price):
        vals =  {}
        vals['total'] = qty * price
        return {'value':vals}
    
    def onchange_returned_product(self, cr, uid, ids,return_qty):
        vals = {}
        for f in self.browse(cr,uid,ids):
            disp_qty = f.dispatch_qty
            vals['total'] = disp_qty *f.price
            update_lines = self.pool.get('client.stock.lines').write(cr, uid, ids, {
                       'net_qty':vals['net_qty'],
                       'total':vals['total'],
                       }) 
        return {'value':vals}
    
    _name = 'client.stock.lines'
    _description = "Clint stock lines"
    _columns = {
        'name': fields.many2one('product.product', 'Tool',domain = [('type','=','product')]),      
        'product_qty': fields.float('Quantity'),
        'stock_parent_id': fields.many2one('get.client.stock','Requisition'),
        'price_unit': fields.float('Unit Price'),
        'total':fields.float('Total'),
        
    }
   
    _defaults = {
                 
    }
client_stock_lines()
#-------------------------------------------------------------------------------------------------------------------------------

class project_state_color(osv.osv):
    """ 
    Model for project states.
    """
    _name = 'project.state.color'
    _description = 'State of Asset'
    _order = "sequence"

    STATE_COLOR_SELECTION = [
    ('0', 'Red'),
    ('1', 'Green'),
    ('2', 'Blue'),
    ('3', 'Yellow'),
    ('4', 'Magenta'),
    ('5', 'Cyan'),
    ('6', 'Black'),
    ('7', 'White'),
    ('8', 'Orange'),
    ('9', 'SkyBlue')
]
    
    

    _columns = {
        'name': fields.char('State', size=64, required=True, translate=True),
        'sequence': fields.integer('Sequence', help="Used to order states."),
        'state_color': fields.selection(STATE_COLOR_SELECTION, 'State Color'),
        'object': fields.selection([ ('0', 'Project'),('1', 'Task'),('2', 'Work Activity')], 'Target Object'),
    }

    _defaults = {
        'sequence': 1,
    }
    
    def change_color(self, cr, uid, ids, context=None):
        state = self.browse(cr, uid, ids[0], context=context)
        color = int(state.state_color) + 1
        if (color>9): color = 0
        return self.write(cr, uid, ids, {'state_color': str(color)}, context=context)

#----------------------table as db fields for projects ---------------------------------------------------------------------------

class project_jobtype(osv.osv):
    _name = 'project.jobtype'
    _columns = {'name':fields.char('Code',size = 100),'code_value':fields.char('Value',size = 100)}
    _sql_constraints = [  
        ('Duplicated', 'unique (name)', 'Job Type already Exists')
    ] 
project_jobtype()


class project_product_category(osv.osv):
    _name = 'project.product.category'
    _columns = {'name':fields.char('Code',size = 100),'code_value':fields.char('Value',size = 100)}
    _sql_constraints = [  
        ('Duplicated', 'unique (name)', 'Category must be unique')
    ] 
project_product_category()

class project_priority(osv.osv):
    _name = 'project.priority'
    _columns = {'name':fields.char('Priority',size = 100)}
    _sql_constraints = [  
        ('Duplicated', 'unique (name)', 'Priority Already Exists')
    ] 

project_priority()

class workforce_segment(osv.osv):
    _name = 'workforce.segment'
    _columns = {'name':fields.char('WorkForce Segment',size = 100)}
    _sql_constraints = [  
        ('Duplicated', 'unique (name)', 'Work force Segment Already Exists')
    ] 

workforce_segment()

class project_product_technology(osv.osv):
    _name = 'project.product.technology'
    _columns = {'code':fields.char('Code',size = 100),'name':fields.char('Value',size = 100)}
    _sql_constraints = [  
        ('Duplicated', 'unique (name)', 'Product Technology Already Exists')
    ] 

project_product_technology()

class serviceidentification_no(osv.osv):
    _name = 'serviceidentification.no'
    _columns = {'name':fields.char('Type',size = 100),'text':fields.char('Text',size = 100)}
    _sql_constraints = [  
        ('Duplicated', 'unique (name)', 'SIN Already Exists')
    ] 

serviceidentification_no()

class workorder_attribute_list(osv.osv):
    _name = 'workorder.attribute.list'
    _columns = {'name':fields.char('Type',size = 100),'text':fields.char('Text',size = 100)}
    _sql_constraints = [  
        ('Duplicated', 'unique (name)', 'WOA List Already Exists')
    ] 

workorder_attribute_list()

class workorder_details_list(osv.osv):
    _name = 'workorder.details.list'
    _columns = {'name':fields.char('Type',size = 100),'text':fields.char('Text',size = 100)}
    _sql_constraints = [  
        ('Duplicated', 'unique (name)', 'WO Details List Already Exists')
    ] 

workorder_details_list()

class cust_location_type(osv.osv):
    _name = 'cust.location.type'
    _columns = {
                'name':fields.char('Type',size = 100),
                }
cust_location_type()

class cust_phone_location(osv.osv):
    _name = 'cust.phone.location'
    _columns = {
                'name':fields.char('Phone Location',size = 100),
                }
cust_phone_location()

class cust_contactlist(osv.osv):
    _name = 'cust.contactlist'
    _columns = {
                'project_id':fields.many2one('project.project','Project'),
                'name':fields.char('Name',size = 100),
                'typeCd':fields.many2one('cust.location.type','Type'),
                'phoneNumberTxt':fields.char('Phone',size = 100),
                'phoneLocationCd':fields.many2one('cust.phone.location','Phone Location'),
                'parent_project':fields.many2one('project_id', 'Project', invisible=True)
                }
                
    _sql_constraints = [  
        ('Duplicated', 'unique (name)', 'Contact Already Exists')
    ] 

cust_contactlist()

class client_contact_list(osv.osv):
    
    
    def cust_sub(self, cr, uid, ids,field_names, context=None, check=True):
        """ Read the 'address' functional fields. """
        result = {}
        part_obj = self.pool.get('res.partner')
        for f in self.browse(cr, uid, ids, context=context):
            result[f.id] = {}
            if type(field_names) is not list:
                field_names = [field_names]
            for key_str in field_names:
                result[f.id][key_str] = '--'
            cust_id = self.pool.get('res.partner').search(cr, uid, [('id','=',f.subpartner_id.id)])
            if cust_id:
                obj = part_obj.browse(cr,uid,cust_id[0])
            
                if 'name' in field_names:
                    result[f.id]['name'] = obj.name 
                if 'phoneNumberTxt' in field_names:
                    result[f.id]['phoneNumberTxt'] = obj.phone
                if 'cellNumberTxt' in field_names:
                    result[f.id]['cellNumberTxt'] = obj.mobile
                if 'emailTxt' in field_names:
                    result[f.id]['emailTxt'] = obj.email
                if 'address' in field_names:
                    result[f.id]['address'] = str(obj.street or '-')+','+str(obj.street2 or '')+','+str(obj.city or '')+','+str(obj.state_id.name or '')+','+str(obj.zip or '')+','+str(obj.country_id.name or '')
                # if 'streetTxt' in field_names:
                    # result[f.id]['streetTxt'] = obj.street
                # if 'street2Txt' in field_names:
                    # result[f.id]['street2Txt'] = obj.street2
                # if 'cityTxt' in field_names:
                    # result[f.id]['cityTxt'] = obj.city
                # if 'state_idTxt' in field_names:
                    # result[f.id]['state_idTxt'] = obj.state_id
                # if 'zipTxt' in field_names:
                    # result[f.id]['zipTxt'] = obj.zip
                # if 'country_idTxt' in field_names:
                    # result[f.id]['country_idTxt'] = obj.country_id
        _logger.info("==============dictionary of customer locations and information================= : %s",result)
        return result
			
    _name = 'client.contact.list'
    _columns = {
                'name':fields.function(cust_sub,multi='analytic', store=False,  method=True, string='Name',type='char'),
                'phoneNumberTxt':fields.function(cust_sub,multi='analytic', store=False,  method=True, string='Phone',type='char'),
                'cellNumberTxt':fields.function(cust_sub,multi='analytic', store=False,  method=True, string='Mobile#',type='char'),
                'emailTxt':fields.function(cust_sub,multi='analytic', store=False,  method=True, string='Email',type='char'),
                # 'streetTxt':fields.function(cust_sub,multi='analytic', store=False,  method=True, string='Street',type='char'),
                # 'street2Txt':fields.function(cust_sub,multi='analytic', store=False,  method=True, string='Street Line 2',type='char'),
                # 'cityTxt':fields.function(cust_sub,multi='analytic', store=False,  method=True, string='City',type='char'),
                # 'state_idTxt':fields.function(cust_sub,multi='analytic', store=False,  method=True, string='State',type='char'),
                # 'zipTxt':fields.function(cust_sub,multi='analytic', store=False,  method=True, string='Zip',type='char'),
                # 'country_idTxt':fields.function(cust_sub,multi='analytic', store=False,  method=True, string='Country',type='char'),
                'address':fields.function(cust_sub,multi='analytic', store=False,  method=True, string='Address',type='char'),
				'parent_project':fields.many2one('parent_project', 'Project', invisible=True),
                'subpartner_id':fields.many2one('res.partner', 'Partner', invisible=True),
                }
                
    _sql_constraints = [  
        ('Duplicated', 'unique (name)', 'Contact Already Exists')
    ] 

client_contact_list()

class cust_location(osv.osv):
    _name = 'cust.location'
    _columns = {
                'name':fields.char('Location ID',size = 100),
                'typeCode':fields.char('Type Code',size = 100),
                'dispatchLocationInd':fields.boolean('Dispatch Location'),
                'timezoneCd':fields.char('Time Zone',size = 100),
                'locationAddress':fields.one2many('cust.location.civic.address','parent_location','Location Address'),
                'geocodeAddress':fields.one2many('cust.location.geocode.address','parent_location','Geo Code Address'),
                'regionHierarchy':fields.one2many('cust.location.region.hierarchy','parent_location','Region Hierarchy'),
                'parent_project':fields.many2one('project.project','Project', invisible=True)
                }
                
    _sql_constraints = [  
        ('Duplicated', 'unique (name)', 'Location Already Exists')
    ] 

cust_location()


class cust_location_civic_address(osv.osv):
    _name = 'cust.location.civic.address'
    _columns = {
                'name':fields.char('Civic Number',size = 100),
                'parent_location':fields.many2one('cust.location','Customer Location', readonly = True),
                'streetName':fields.char('Street Name',size = 100),
                'streetNamePostTypeCode':fields.char('Street Name Post Type Code',size = 100),
                'municipalityCode':fields.char('Municipality Code',size = 100),
                'provinceStateCode':fields.char('Province State Code',size = 100),
                'countryCode':fields.char('Country Code',size = 100),
                'postalCode':fields.char('Postal Code',size = 100),
                }
cust_location_civic_address()
class cust_location_geocode_address(osv.osv):
    _name = 'cust.location.geocode.address'
    _columns = {
                'name':fields.char('Match Code',size = 100),
                'latitude':fields.char('Latitude',size = 100),
                'longitude':fields.char('Longitude',size = 100),
                'parent_location':fields.many2one('cust.location','Customer Location', readonly = True),
                }
cust_location_geocode_address()

class cust_location_region_hierarchy(osv.osv):
    _name = 'cust.location.region.hierarchy'
    _columns = {
                'name':fields.char('Province Code',size = 100),
                'provinceName':fields.char('Province Name',size = 100),
                'provinceLocationId':fields.char('Province Location Id',size = 100),
                'regionName':fields.char('Region Name',size = 100),
                'regionLocationId':fields.char('Region Location Id',size = 100),
                'districtName':fields.char('District Name',size = 100),
                'districtLocationId':fields.char('District Location Id',size = 100),
                'serviceAreaName':fields.char('Service Area Name',size = 100),
                'serviceAreaCLLICd':fields.char('Service Areas CLLI',size = 100),
                'serviceAreaLocationId':fields.char('Service Area Location Id',size = 100),
                'parent_location':fields.many2one('cust.location','Customer Location', readonly = True),
                }
cust_location_region_hierarchy()

class project_customer_type(osv.osv):
    _name = 'project.customer.type'
    _columns = {'name':fields.char('Type',size = 100)}
    _sql_constraints = [  
        ('Duplicated', 'unique (name)', 'Customer Type Already Exists')
    ] 

project_customer_type()

class project_classification(osv.osv):
    _name = 'project.classification'
    _columns = {'name':fields.char('Classification',size = 100)}
    _sql_constraints = [  
        ('Duplicated', 'unique (name)', 'Classification must be unique')
    ] 

project_classification()

class project_serviceclass(osv.osv):
    _name = 'project.serviceclass'
    _columns = {'name':fields.char('Code',size = 100),'code':fields.char('Value',size = 100)}
    _sql_constraints = [  
        ('Duplicated', 'unique (name)', 'Name must be unique')
    ] 

project_serviceclass()

class project_workforce_segment(osv.osv):
    _name = 'project.workforce.segment'
    _columns = {'name':fields.char('Name',size = 100)}
    _sql_constraints = [  
        ('Duplicated', 'unique (name)', 'Name must be unique')
    ] 

project_workforce_segment()

class project_order_action(osv.osv):
    _name = 'project.order.action'
    _columns = {'name':fields.char('Name',size = 100)}
    _sql_constraints = [  
        ('Duplicated', 'unique (name)', 'Name must be unique')
    ] 

project_order_action()

class project_onto_service(osv.osv):
    _name = 'project.onto.service'
    _columns = {'name':fields.char('Name',size = 100)}
    _sql_constraints = [  
        ('Duplicated', 'unique (name)', 'Name must be unique')
    ] 

project_onto_service()

class partner_acknowledge(osv.osv):
    _name = 'partner.acknowledge'
    _columns = {'name':fields.char('Name',size = 100)}
    _sql_constraints = [  
        ('Duplicated', 'unique (name)', 'Name must be unique')
    ] 

partner_acknowledge()

class project_work_location(osv.osv):
    _name = 'project.work.location'
    _columns = {
				'name':fields.char('Street',size = 100),
				'street2':fields.char('Street2',size = 100),
				'city':fields.char('City',size = 100),
				'state_id': fields.many2one("res.country.state", 'Province', ondelete='restrict'),
				'postal': fields.char('Postal Code',size = 100),
				'country_id': fields.many2one('res.country', 'Country', ondelete='restrict'),
				'description':fields.html('Description'),
				}
    _sql_constraints = [  
        ('Duplicated', 'unique (name)', 'Work Location must be unique')
    ] 

project_work_location()

class project_type(osv.osv):
    _name = "project.type"
    _columns = {
        'name': fields.char('Project Type',size = 100),
        'desc': fields.char('Description',size = 150),
            }
    _sql_constraints = [
        ('Duplicated', 'unique (name)', 'Project Type, Already exists')
    ]

project_type()
class data_source(osv.osv):
    _name = "data.source"
    _columns = {
        'name': fields.char('Data Source',size = 100),
        'desc': fields.char('Description',size = 150),
            }
    _sql_constraints = [
        ('Duplicated', 'unique (name)', 'Data Source, Already exists')
    ]

data_source()
class modify_data_source(osv.osv):
    _name = "modify.data.source"
    _columns = {
        'name': fields.char('Data Source',size = 100),
        'desc': fields.char('Description',size = 150),
            }
    _sql_constraints = [
        ('Duplicated', 'unique (name)', 'Data Source, Already exists')
    ]

modify_data_source()
#----------------------------------- inherited project.project------------------------------------------------------------------

class project_project(osv.osv):
    """Extended project.project through inheritance"""
    
#     def map_tasks(self, cr, uid, old_project_id, new_project_id, context=None):
#         """ copy and map tasks from old to new project """
#         if context is None:
#             context = {}
#         map_task_id = {}
#         task_obj = self.pool.get('project.task')
#         work_obj = self.pool.get('project.task.work')
#         proj = self.browse(cr, uid, old_project_id, context=context)
#         for task in proj.tasks:
#             # preserve task name and stage, normally altered during copy
#             defaults = {'stage_id': task.stage_id.id,
#                         'name': task.name}
#             map_task_id[task.id] =  task_obj.copy(cr, uid, task.id, defaults, context=context)
#             
#             map_workid = {}
#             task_id = task.id
#             task_rec = task_obj.browse(cr, uid, task_id, context=context)
#             for work in task_rec.work_ids:
#                 work_defaults = {}
#                 map_workid[work.id] =  work_obj.copy(cr, uid, work.id, work_defaults, context=context)
#             work_obj.write(cr, uid, [map_workid], {'work_ids':[(6,0, map_task_id.values())]})
            #work_obj.duplicate_task(cr, uid, map_workid, context=context)
            
#         self.write(cr, uid, [new_project_id], {'tasks':[(6,0, map_task_id.values())]})
#         task_obj.duplicate_task(cr, uid, map_task_id, context=context)
#         return True
    
    def load_tasks_and_activities(self,cr,uid,proj_id,project_gen_type):
        """Loads for bell projects only"""
        rec_project_template = self.pool.get('project.generic.template').browse(cr, uid,project_gen_type)
        res = self.pool.get('project.project').browse(cr, uid, proj_id)
        default_task_id = self.pool.get('project.tasks.default').search(cr, uid, [('project_template_id','=',project_gen_type)])
        project_hours = 0
        if default_task_id:
            rec_default_task = self.pool.get('project.tasks.default').browse(cr, uid,default_task_id)
           
            for d_task in rec_default_task:
                repitition  = d_task.repitition
                for i in range(0,repitition):
                    #now create task record in project.task
                    task_id = self.pool.get('project.task').create(cr,uid,{
                                                    'name':d_task.name,
                                                    'project_id':proj_id, 
                                                    'planned_hours':d_task.planned_hours_task,
                                                    'user_id':rec_project_template.default_users.id,
                                                    'date_deadline':res.date
                                                     })
#                    project_hours = project_hours + d_task.planned_hours
                    if task_id:
                        #search default_work activities of task using default task id
                        activity_ids = self.pool.get('project.task.work.default').search(cr, uid, [('task_id','=',d_task.id)])
                        if activity_ids:
                             rec_default_task = self.pool.get('project.task.work.default').browse(cr, uid,activity_ids)
                             for activity in rec_default_task:
                                 activity_repitition = activity.repitition
		                         
                                 for j in range(0,activity_repitition):
	
        	        			    #now create task activities
			                        self.pool.get('project.task.work').create(cr,uid,{
                    		                    'name':activity.name,
                        		                'task_id':task_id, 
                                		        'user_id':rec_project_template.default_users.id,
                                         		 'activity_time':activity.hours,
	                                           	 'hours':0
        		                                })
        return  project_hours 
   
    
    def add_followers(self,cr,uid,proj_id,members):
        uid =1
        for mrmber in members[0][2]:
            _logger.info("project memeber users ids %s",members[0][2])
            rec = self.pool.get('res.users').browse(cr,uid,mrmber)
            _logger.info("Adding Memners to prject member id: %s",mrmber)
            
            exists = self.pool.get('mail.followers').search(cr,uid,[('res_model','=','project.project'),('res_id','=',proj_id),('partner_id','=',rec.partner_id.id)])
            _logger.info("member already esists: %s",len(exists))
            if len(exists) ==0: 
                self.pool.get('mail.followers').create(cr,1,{'res_model':'project.project','res_id':proj_id,'partner_id':rec.partner_id.id})
                # Now also display message in emplyee ubbox
                # may be this code ire replace from here to the even where project is addined to employee
                new_msg = self.pool.get('mail.message').create(cr,1,{
                                                    'subtype_id':11,
                                                    'subject':'You are assigned to new project', 
                                                    'date':datetime.now(),
                                                    'type':'notification',
                                                    'body':'Project Name:'+str(self.pool.get('project.project').browse(cr,uid,proj_id).name),
                                                    'partner_ids':[rec.partner_id.id],
                                                    'model':'project.project',
                                                    'notified_partner_ids':[rec.partner_id.id],
                                                     })
                if new_msg:
                    notif = self.pool.get('mail.mail').create(cr,1,{
                                                    'mail_message_id':new_msg,
                                                    'state':'exception', 
                                                    'recipient_ids':[rec.partner_id.id],
                                                     })
                    new_mail = self.pool.get('mail.notification').create(cr,1,{
                                                    'partner_id':rec.partner_id.id,
                                                    'message_id':new_msg
                                                     })
                    
        return
    
    def create(self, cr, uid, vals, context=None, check=False):
        state_id = self.pool.get('asset.state').search(cr, uid, [('name','=','Draft'),('team','=',5)])
        _logger.info("inside create method of project:::::::::::::::::::::::::::::::::: vals %s",vals)
        _logger.info("===========99999999999999999999999999999999999999999:")
        if state_id:
            rec = self.pool.get('asset.state').browse(cr,uid,state_id[0])
            vals['maintenance_state_id'] = rec.id
        else:
            raise osv.except_osv(('state not found-> Draft'),("Ask your administrator to configure default process states"))
        result = super(project_project, self).create(cr, uid, vals, context)
        for f in self.browse(cr,uid,result):
           
            # Create threee entries in project line summary of matric tab
            self.pool.get('project.pl.display.summary').create(cr,uid,{'name':f.id,'pl_summary':'TOTAL PROJECT REVENUES'})
            self.pool.get('project.pl.display.summary').create(cr,uid,{'name':f.id,'pl_summary':'TOTAL PROJECT COSTS'})
            self.pool.get('project.pl.display.summary').create(cr,uid,{'name':f.id,'pl_summary':'NET PROJECT MARGIN'})
           
            # firs find target value for cTotal Project Cost
#             trgt =  self.pool.get('project.pl.cost.summary').computtrgt(cr,uid,f.id)
            self.pool.get('project.pl.rev.summary').create(cr,uid,{'name':f.id,'pl_summary':'TOTAL PROJECT REVENUES'})
            self.pool.get('project.pl.cost.summary').create(cr,uid,{'name':f.id,'pl_summary':'TOTAL PROJECT COSTS'})
            self.pool.get('project.net.margin').create(cr,uid,{'project_id':f.id,'name':'NET PROJECT MARGIN'})
            #self.pool.get('project.pl.summary').create(cr,uid,{'name':f.id,'pl_summary':'NET PROJECT MARGIN'})
            #add flwrs
            
            if 'members' in vals:
                foll = self.add_followers(cr,uid,f.id,vals['members'])
            if 'project_type_template' in vals:
                if vals['project_type_template']:
                    project_hours = self.load_tasks_and_activities(cr,uid,f.id,f.project_type_template.id)
                    vals['template_loaded'] = True
        #create contact_info
        if vals['partner_id']:
            pids = self.pool.get('res.partner').search(cr,uid,[('parent_id','=',vals['partner_id'])])
            if pids:
                rec = self.pool.get('res.partner').browse(cr,uid,pids)
                for pr in rec:
                    _logger.info("inside create method of project:::::::::::::::::::::::::::::::::: partner.-d %d",pr.id)
                    self.pool.get('client.contact.list').create(cr,uid,{'parent_project':result,'subpartner_id':pr.id}) 
             
            

        return result
   
     
    def write(self, cr, uid, ids, vals, context=None, check=True, update_check=True):
        
        for f in self.browse(cr,uid,ids):
            _logger.info("data sources >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> %s",f.data_sources)
            #add flwrs
            if 'members' in vals:
                foll = self.add_followers(cr,uid,f.id,vals['members'])
            # set to open if due_date in 
            if 'date' in vals:
                if vals['date']:
                    self.pool.get('project.project').set_open(cr,uid,f.id)
            
            if 'project_manager' in vals:
                 # now update project issue if any
                ptrid = self.pool.get('res.users').browse(cr,uid,vals['project_manager']) 
                issue_ids = self.pool.get('project.issue').search(cr,uid,[('project_id','=',f.id)])
                if issue_ids:
                    for issue in issue_ids:
                        self.pool.get('project.issue').write(cr,uid,issue,{'partner_id':ptrid.partner_id.id})
                
            if 'partner_id' in vals: 
                
                
                if vals['partner_id']!= f.partner_id.id:
                    
        
                    lids = self.pool.get('client.contact.list').search(cr,uid,[('parent_project','=',f.id)])
                    for list_id in lids:
                        self.pool.get('client.contact.list').unlink(cr,uid,list_id)
                    pids = self.pool.get('res.partner').search(cr,uid,[('parent_id','=',vals['partner_id'])])
                    if pids:
                        rec = self.pool.get('res.partner').browse(cr,uid,pids)
                        for pr in rec:
                            _logger.info("inside create method of project:::::::::::::::::::::::::::::::::: partner.-d %d",pr.id)
                            self.pool.get('client.contact.list').create(cr,uid,{'parent_project':f.id,'subpartner_id':pr.id}) 
                           
        
        
                
            if 'project_planned_hours' in vals or 'planned_expense' in vals:
                vals['modifier'] = uid 
                vals['modified_date'] = datetime.now()
            
            if 'project_type_template' in vals:
                if vals['project_type_template']:
                    self.load_tasks_and_activities(cr,uid,f.id,vals['project_type_template'])
                    vals['template_loaded'] = True
            
            #update task end date
            
#             analytic_rec = self.pool.get('account.analytic.account').searh(cr,uid,[('id','=',f.analytic_account_id.id)])
            if 'date' in vals:
                vals['modifier'] = uid 
                vals['modified_date'] = datetime.now()
                task_ids = self.pool.get('project.task').search(cr,uid,[('project_id','=',f.id)])
                if task_ids:
                    for task in task_ids:
                        self.pool.get('project.task').write(cr, uid, task, {'date_end':vals['date'],'date_deadline':vals['date']})
            
            #create project logs
            for k, v in vals.iteritems():
                self.create_transactional_logs(cr,uid,'Project',k,v,'Update',f) 
            
            # jo status logs maintinace and update pubsub
            reason = 'N/A'
            remarks  = 'N/A'
            if 'statuscd' in vals:
                if vals['statuscd'] == 'ACCEPTED':
                    if 'acceptremarktxt' in vals: 
                        remarks = vals['acceptremarktxt']
                    
                    vals['acceptDateTime'] = datetime.now()
                elif vals['statuscd'] == 'REJECTED':
                    remarks = vals['rejectremarktxt']
                    vals['rejectdatetime'] = datetime.now()
                    if 'rejectreasoncd' in vals:
                        reason = vals['rejectreasoncd']
                elif vals['statuscd'] == 'EN_ROUTE':
                    
                    remarks = vals['enrouteremarktxt']
                    vals['enrouteDateTime'] = datetime.now()
                    reason = 'N/A'
                elif vals['statuscd'] == 'ON_SITE':
                    if 'onsiteremarktxt' in vals:
                        remarks = vals['onsiteremarktxt']
                    vals['onsitedatetime'] = datetime.now()
                    reason = 'N/A'
                elif vals['statuscd'] == 'COMPLETE':
                    if 'completeremarktxt' in vals:
                        remarks = vals['completeremarktxt']
                    vals['completetatetime'] = datetime.now()
                    reason = 'N/A'
                elif vals['statuscd'] == 'INCOMPLETE':
                    if 'incompleteremarktxt' in vals:
                        remarks = vals['incompleteremarktxt']
                    if 'incompletereasoncd' in vals:
                        reason = vals['incompletereasoncd']
                    vals['incompletedatetime'] = datetime.now()
                elif vals['statuscd'] == 'DISPATCHED':
                    remarks = 'N/A'
                    vals['dispatcheddatetime'] = datetime.now()
                    reason = 'N/A'
                elif vals['statuscd'] == 'TENTATIVE':
                    remarks = 'N/A'
                    vals['tentativedatetime'] = datetime.now()
                    reason = 'N/A'
                
                #raise osv.except_osv((remarks),(vals['enrouteremarktxt']))
                set_log = self.pool.get('project.task.handling.logs').update_task_log(cr,uid,f.id,vals['statuscd'],remarks,reason)
                
                if 'statuscd'in vals:
                    
                    data = {
                             "JobId":f.id ,
                             "TeamWorkerId": f.requiredteamworkerlist,
                             "UserId": "CNI",
                             "SystemSourceCd": "16733",
                             "Remarks":vals['statuscd'],
                             "JobAssignmentId": f.jobassignmentid,
                             "StatusCode": vals['statuscd']
                         }
                    #error seems to be in remote method,
                    #req = urllib2.Request('https://pubsub.cninet.ca/api/Job/UpdateJob/')
                    #req.add_header('Content-Type', 'application/json')
#                     urllib2.urlopen(req, json.dumps(data))
                       
            # update client business unit and client dispatch sector and time zone on contact info tab
            woi = self.pool.get('project.workorder').search(cr,uid,[('project_id','=',f.id)])
#            self.pool.get('project.pl.display.summary').write(cr,uid,ids,{'name':f.id,'pl_summary':'TOTAL PROJECT REVENUES'})
#            self.pool.get('project.pl.display.summary').write(cr,uid,ids,{'name':f.id,'pl_summary':'TOTAL PROJECT COSTS'})
#            self.pool.get('project.pl.display.summary').write(cr,uid,ids,{'name':f.id,'pl_summary':'NET PROJECT MARGIN'})
#            self.pool.get('project.pl.rev.summary').write(cr,uid,ids,{'name':f.id,'pl_summary':'TOTAL PROJECT REVENUES'})
#            self.pool.get('project.pl.cost.summary').write(cr,uid,ids,{'name':f.id,'pl_summary':'TOTAL PROJECT COSTS'})
#            self.pool.get('project.net.margin').write(cr,uid,ids,{'project_id':f.id,'name':'NET PROJECT MARGIN'})
            if woi:
                rec = self.pool.get('project.workorder').browse(cr,uid,woi)
                vals['srv_cls_cs'] = rec[0].serviceClassCd.name or None
            #update cusotmer 
            cutlocation_id = self.pool.get('cust.location').search(cr,uid,[('parent_project','=',f.id)])
            if cutlocation_id:
                rec = self.pool.get('cust.location').browse(cr,uid,cutlocation_id)
                rng_hrch = rec[0].regionHierarchy[0]
                vals['client_dispatchsec'] = rng_hrch.serviceAreaName
                vals['custtimezone'] =  rec[0].timezoneCd
           
        result = super(project_project, self).write(cr, uid, ids, vals, context)
        return result
    
    
    def get_fds(self,cr,uid,model,field):
        """returns object fields desc"""
        mdl_id = self.pool.get('ir.model').search(cr,uid,[('model','=',model)])[0]
        _logger.info("===========model id: %d",mdl_id)
        fields = self.pool.get('ir.model.fields').search(cr,uid,[('model_id','=',mdl_id),('name','=',field)])
        _logger.info("===========result of search fields: %s",fields)
        if fields:
            recfields = self.pool.get('ir.model.fields').browse(cr,uid,fields[0])
            return  recfields.field_description
        else:
            return False
    def is_m2o(self,cr,uid,model,field,field_value):
        """returns m2o object if m2o only"""
        _logger.info("*******inside is_m2o***********field: %s",field)
        _logger.info("*******inside is_m2o***********field_value: %s",field_value)
        
        mdl_id = self.pool.get('ir.model').search(cr,uid,[('model','=',model)])[0]
        _logger.info("===========model id: %d",mdl_id)
        fields = self.pool.get('ir.model.fields').search(cr,uid,[('model_id','=',mdl_id),('name','=',field)])
        _logger.info("===========result of search fields: %s",fields)
        if fields:
            recfields = self.pool.get('ir.model.fields').browse(cr,uid,fields[0])
            if recfields.ttype == 'many2one':
                _logger.info("===========yes type is m20")
                table = recfields.relation
                table =table.replace(".","_")
                if field_value:
                    if table =='res_users':
                        return 
                        sql = "SELECT partner_id FROM """+str(table)+""" WHERE id="""+str(field_value)
                        cr.execute(sql)
                        partner_id = cr.fetchone()[0]
                        sql1 = "SELECT name FROM res_partner WHERE id="""+str(partner_id)
                        cr.execute(sql1)
                        value = cr.fetchone()[0]
                        return value
                    elif table == 'project_project':
                        return
                    else:
                            
                        sql = "SELECT name FROM """+str(table)+""" WHERE id="""+str(field_value)
                        cr.execute(sql)
                        value = cr.fetchone()[0]
                        _logger.info("==========retruning value of m2o field :%s",value)
                        return value
                else:
                    return '--'
            else:
                return field_value
            
    def view_init(self, cr , uid , fields, context=None):
        _logger.info("^^^^^^^^^^^^^ this is view init: %s",fields)
        return
    
    
    def create_transactional_logs(self, cr, uid,obj, column ,post_value,operation,brow):
        """ this method creates transactional logs for project,tasks and work
        will be called from write method of project, task and work """
        _logger.info("===========1:called method create_transactional_logs, cloumn: %s",column)
        _logger.info("===========1:called method create_transactional_logs, cloumn new value: %s",post_value)
        if obj == "Project":
            if column == 'maintenance_state_id':
                return
            elif column == 'members':
                #this portion will handle member changed log see sms
                return
            elif column == 'consumeable_items':
                return
            elif column == 'reservation_lines':
                return
            else:    
                pre =None
                task_id = None
                project_id = brow.id
                work_id = None
                fds = self.get_fds(cr,uid,'project.project',column)
                if column =='date':
                    pre = self.browse(cr,uid,brow.id).date
                elif column =='date_start':
                    pre = self.browse(cr,uid,brow.id).date_start
                elif column =='name':
                    pre = self.browse(cr,uid,brow.id).analytic_account_id.name
                elif column =='priorityCd':
                    pre = self.browse(cr,uid,brow.id).priorityCd.name
                elif column =='data_sources':
                    pre = self.browse(cr,uid,brow.id).data_sources.name
                elif column =='modify_data_sources':
                    pre = self.browse(cr,uid,brow.id).modify_data_sources.name
                elif column =='attached_docs':
                    return
                elif column =='project_tasks_work':
                    return
                elif column =='srv_cls_cs':
                    return
                elif column =='client_dispatchsec':
                    return
                elif column =='custtimezone':
                    return
                elif column =='project_task':
                    return
                elif column =='invoice_ids':
                    return
                elif column =='client_contacts_list':
                    return					 
                elif column =='project_project':
                    return	
                elif column =='tasks':
                    return   
                elif column =='project_expenses_lines2':
                    return 				 
                elif column == 'project_work_order_ids':
                    return
                elif column == 'project_billing_material':
                    return
                elif column == 'pl_summary_revenue_ids':
                    return
                elif column == 'pl_summary_cost_ids':
                    return
                elif column == 'project_pl_display_summary_ids':
                    return
                elif column == 'net_project_margins_ids':
                    return
                else:
                    
                    sql="""select project_project."""+str(column)+""" from project_project where id="""+str(brow.id)
                    cr.execute(sql)
                    pre = cr.fetchone()[0]
                   
                
                _logger.info("&&&&&&&&&&&&&&& actual pre=======is_pre_m2o, cloumn: %s",pre)
                _logger.info("================== before callin is_m2o, cloumn pre val: %s",pre)
                _logger.info("================== before callin is_m2o, cloumn post val: %s",post_value)
                is_pre_m2o = self.is_m2o(cr,uid,'project.project',column,pre)
                is_post_m2o = self.is_m2o(cr,uid,'project.project',column,post_value)
                _logger.info("===returned back to main method========is_pre_m2o, cloumn: %s",is_pre_m2o)
        elif obj == 'Task':
            task_id = brow.id
            project_id = brow.project_id.id
            work_id = None
            fds = self.get_fds(cr,uid,'project.task',column)
            if column == 'sequence':
                return
            elif column == 'stage_id':
                pre = brow.stage_id.id
                is_pre_m2o = self.is_m2o(cr,uid,'project.task',column,pre)
                _logger.info("===returned back to main method========is_pre_m2o, cloumn: %s",is_pre_m2o)
            else:
                pre = self.pool.get('project.task').read(cr,uid, brow.id,[column])
                is_pre_m2o = self.is_m2o(cr,uid,'project.task',column,pre[column])
            _logger.info("===returned back to main method========is_pre_m2o, cloumn: %s",is_pre_m2o)
            is_post_m2o = self.is_m2o(cr,uid,'project.task',column,post_value)
            
            _logger.info("===returned back to main method========is_pre_m2o, cloumn: %s",is_pre_m2o)
        elif obj == 'Work':
            task_id = brow.task_id.id
            project_id = brow.task_id.project_id.id
            work_id = brow.id
            fds = self.get_fds(cr,uid,'project.task.work',column)
            pre = self.pool.get('project.task.work').read(cr,uid, brow.id,[column])
            is_pre_m2o = self.is_m2o(cr,uid,'project.task.work',column,pre[column])
            is_post_m2o = self.is_m2o(cr,uid,'project.task.work',column,post_value)
            _logger.info("===returned back to main method========is_pre_m2o, cloumn: %s",is_pre_m2o)
            _logger.info("===========Ourput of read: %s",pre[column])
        
        if fds == 'Last Message Date':
            return
        else:
            result = self.pool.get('project.transactional.log').create(cr,uid,{
                                                        'object_name': obj+"("+str(brow.name)+")",
                                                        'pre_value': is_pre_m2o,
                                                        'post_value': is_post_m2o,
                                                        'operation':operation,
                                                        'column_name':fds,
                                                        'project_id':project_id,
                                                        'task_id':task_id,
                                                        'work_id':work_id,
                                                        'event_date': datetime.now(),
                                                        'event_by': uid,
                                                         }) 

        return result
    
    def unlink(self, cr, uid, ids, context=None):
        result = False
        # admin = self.check_user_group(cr,uid,'CNI Admin')
        # if admin:
        result = super(project_project, self).unlink(cr, uid, ids, context)
        # else:
        #     raise osv.except_osv(('Not Allowed'),("You are not authorized to delete project, Contact your service provider."))
        return result
    
    def onchange_projecttype(self, cr, uid, ids,type):
        vals = {}
        if type=='Pre-Assembly':
            partner = self.pool.get('res.partner').search(cr, uid, [('name','=','BELL'),])
            if partner:
                vals['partner_id'] = partner[0]
            return { 'value':vals  }
        else:
            return {} 
    
    def get_project_charged_expenses(self, cr, uid, ids, context={}, arg=None, obj=None):
        result = {}
        for f in self.browse(cr, uid,ids): 
            sql="""select  COALESCE(sum(amount),0) from hr_expense_expense where project_id="""+str(f.id)+""" and state = 'accepted'"""
            cr.execute(sql)
            res=cr.fetchone()
            result[f.id] = float(res[0])
        return result
    def get_net_expenses(self, cr, uid, ids, context={}, arg=None, obj=None):
        result = {}
        for f in self.browse(cr, uid,ids): 
            net_exp = float(f.planned_expense-f.expense_charged)
            result[f.id] = net_exp
        return result
   
    def get_client_dsptimezone(self, cr, uid, ids, context={}, arg=None, obj=None):
        result = {}
        for f in self.browse(cr, uid,ids): 
            cutlocation_id = self.pool.get('cust.location').search(cr,uid,[('parent_project','=',f.id)])
            if cutlocation_id:
                rec = self.pool.get('cust.location').browse(cr,uid,cutlocation_id)
                result[f.id] = rec[0].timezoneCd
        return result
    
    def getclient_disoatchsec(self, cr, uid, ids, context={}, arg=None, obj=None):
        result = {}
        for f in self.browse(cr, uid,ids): 
            cutlocation_id = self.pool.get('cust.location').search(cr,uid,[('parent_project','=',f.id)])
            if cutlocation_id:
                rec = self.pool.get('cust.location').browse(cr,uid,cutlocation_id)
                rng_hrch = rec[0].regionHierarchy[0]
                result[f.id] = rng_hrch.serviceAreaName
        return result
    
    def servclasscd(self, cr, uid, ids, context={}, arg=None, obj=None):
        result = {}
        for f in self.browse(cr, uid,ids): 
            woi = self.pool.get('project.workorder').search(cr,uid,[('project_id','=',f.id)])
            if woi:
                rec = self.pool.get('cust.location').browse(cr,uid,woi[0])
                srv_cls_cd = rec[0].serviceClassCd.name
                result[f.id] = srv_cls_cd
        return result
    
    def get_net_hours(self, cr, uid, ids, context={}, arg=None, obj=None):
        result = {}
        
        for f in self.browse(cr, uid,ids): 
            net_hours = float(f.project_planned_hours-f.hours_charged)
            result[f.id] = net_hours
        return result
    
    def update_hours_remain_for_kanban(self, cr, uid, ids, context={}, arg=None, obj=None):
        """this mehod is explactily called by all events that effect project hours, called by create method of project_work,"""
        net_hours = float(00.0)
        for f in self.browse(cr, uid,ids): 
            net_hours = float(f.project_planned_hours-f.hours_charged)
        return net_hours
    
    
    
    def get_charged_hours(self, cr, uid, ids, context={}, arg=None, obj=None):
        result = {}
        for f in self.browse(cr, uid,ids): 
            sql = """ select COALESCE(sum(hours),0) from project_task_work
            inner join project_task
            on project_task.id = project_task_work.task_id
            inner join project_project on
            project_project.id = project_task.project_id 
            where project_project.id ="""+str(f.id)
            cr.execute(sql)
            res=cr.fetchone()
            result[f.id] = res[0]
        return result
    
    def check_user_group(self, cr, uid,required_group):
        sql="""select id
                from res_groups 
                inner join res_groups_users_rel
                on res_groups.id=res_groups_users_rel.gid
                where res_groups_users_rel.uid="""+str(uid)+""" and res_groups.name = '"""+str(required_group)+"""'"""
        cr.execute(sql)
        res=cr.fetchone()
        if res:
            return res[0]
        else:
            return False
    
    def is_access_restricted(self, cr, uid, ids, context={}, arg=None, obj=None):
        result = {}
        records = self.browse(cr, uid, ids)
        sql="""select res_users.id from res_users
                 inner join res_groups_users_rel
                 on res_groups_users_rel.uid = res_users.id
                 inner join res_groups
                on res_groups.id=res_groups_users_rel.gid
                where res_groups_users_rel.uid="""+str(uid)+""" and res_groups.name in ('Group CNI Technician')"""
        cr.execute(sql)
        res=cr.fetchone()

        for f in records:
            if res:
                result[f.id] = True
            else:
                result[f.id] = False
        

        return result
  
    
    def get_progress(self,cr,uid,ids,context = {},args = None,obj = None):
        result = {}
        for f in self.browse(cr,uid,ids):
            progress = 0
            planned_hours = 0
            completed_hours = 0
            planned_hours = f.project_planned_hours
            completed_hours = f.hours_charged
            
            
            if not planned_hours or planned_hours ==0:
                result[f.id] = 0
            else:
                progress = (completed_hours * 100)/planned_hours
            result[f.id] = progress
        return result
#    def get_progress(self,cr,uid,ids,context = {},args = None,obj = None):
#           result = {}
#           for f in self.browse(cr,uid,ids):
#	   	planned_hours = 0
#		task_ids = self.pool.get('project.task').search(cr,uid,[('project_id','=',f.id,)])
#		if task_ids:
#			rec_tasks = self.pool.get('project.task').browse(cr,uid,task_ids)
#			for task in rec_tasks:
#				planned_hours = planned_hours + task.planned_hours	
#
#		if not planned_hours or planned_hours == 0:
#			planned_hours = 1
#		effective_hours = f.effective_hours
#		progress = (effective_hours * 100)/planned_hours
#		result[f.id] = progress
#	   return result
    
    def get_color_state_id(self,cr,uid,ids,context = {},args = None,obj = None):
        result = {}
        
        for f in self.browse(cr,uid,ids):
            state_id = self.pool.get('asset.state').search(cr, uid, [('name','=',f.state),('team','=',5)])
            if state_id:
                rec = self.pool.get('asset.state').browse(cr,uid,state_id[0])
                result[f.id] = rec.id
        return result
        
   
    STATE_COLOR_SELECTION = [
    ('0', 'Red'),
    ('1', 'Green'),
    ('2', 'Blue'),
    ('3', 'Yellow'),
    ('4', 'Magenta'),
    ('5', 'Cyan'),
    ('6', 'Black'),
    ('7', 'White'),
    ('8', 'Orange'),
    ('9', 'SkyBlue')]
    def _closed_issue_count(self, cr, uid, ids, field_name, arg, context=None):
        result = {}
        counted = 0
        Issue = self.pool['project.issue']
        for f in self.browse(cr,uid,ids):
            ids_issues = Issue.search(cr,uid, [('stage_id.fold', '=', False),('project_id', '=', f.id)])
            if ids_issues:
                rec_issues = Issue.browse(cr,uid,ids_issues)
                for issue in rec_issues:
                    stage_id = issue.stage_id.name
                    if stage_id == 'Closed':
                        counted = counted + 1
        result[f.id] = counted
        return result
    
    def _open_issue_count(self, cr, uid, ids, field_name, arg, context=None):
        result = {}
        counted = 0
        Issue = self.pool['project.issue']
        for f in self.browse(cr,uid,ids):
            ids_issues = Issue.search(cr,uid, [('stage_id.fold', '=', False),('project_id', '=', f.id)])
            if ids_issues:
                rec_issues = Issue.browse(cr,uid,ids_issues)
                for issue in rec_issues:
                    stage_id = issue.stage_id.name
                    if stage_id == 'Open':
                        counted = counted + 1
        result[f.id] = counted
        return result
    
    def kanban_state_display(self, cr, uid, ids, field_name, arg, context=None):
        result = {}
        counted = 0
        Issue = self.pool['project.issue']
        for f in self.browse(cr,uid,ids):
#            result[f.id] = f.maintenance_state_id.name.replace("_"," ")
            result[f.id] = f.maintenance_state_id.name
        return result
    
    def get_project_name(self, cr, uid, ids, field_name, arg, context=None):
        result = {}
        for f in self.browse(cr,uid,ids):
            acc = self.pool.get('account.analytic.account').browse(cr,uid,f.analytic_account_id.id)
            result[f.id] = acc.name
        return result 
    
    def project_has_issue(self, cr, uid, ids, context={}, arg=None, obj=None):
       
        
        result = {}
        for f in self.browse(cr,uid,ids):
            if f.date:
                import dateutil.parser
                due_date1 = dateutil.parser.parse(f.date).date()
                _logger.info("===========is project in jeopardy let see:=Project Name: %s",f.name)
                
                delta = due_date1- date.today()
                task_ids = self.pool.get('project.task').search(cr,uid,[('project_id','=',f.id)])
                
                    
                _logger.info("==========today: %s",date.today())
                _logger.info("==========project due date: %s",due_date1)

                # set to Jeopardy IF the current is exceeded the Project Due Date (Due Date Passed):

                if date.today() > due_date1 and f.state != 'Jeopardy' and f.state != 'close':
                    _logger.info("===========Project deadline is exceeded, setting project in jeopardy: project id",f.id)
                    self.set_jeopardy(cr,uid,f.id,'Deadline Exceeded','Jeopardy')
                    result[f.id] = True

				# set to Jeopardy IF the Project is Completed but not invoiced (Project Not Closed), Less then 10 days left:

                if delta.days<10 and f.state !='Completed' and f.state != 'close':
                    _logger.info("===========Although project deadline is not met, but current project has to be set to Jeopardy because >>. Days in closing are:%d ",delta.days)
                    self.set_jeopardy(cr,uid,f.id,'Behind Schedule, Less than 10 days left')

				# set to Jeopardy IF Over Budget [Eg. Hours Charged > 110% of Quoted Hours:

                if f.hours_charged > ((f.project_planned_hours)*1.10) and f.state != 'close':
                    _logger.info("===========Sending this project to Jeopardy:OverBudget",f.project_planned_hours)
                    self.set_jeopardy(cr,uid,f.id,'Over Budget, More than 110%')

				# set to Jeopardy IF Work Not Invoiced [Eg. date.today() - Completion date = delta , delta > 9 and Project not closed = Work Not invoiced]
                
                if delta.days <9 and f.state != 'close' and f.state =='Completed':
                    if f.hours_charged >0:
                        _logger.info("===========Sending this project to Jeopardy:it is not invoiced",f.project_planned_hours)
                        self.set_jeopardy(cr,uid,f.id,'Work Not Invoiced')

				# Remaining time is less than quoted hour remaining, this it is out of time [Delta: date.today() - due_date1.date() (6:00PM) =  Clock Time Remaining, Delta < Quoted Hours Remaining ]
                remainin_time = f.available_clock_time
                _logger.info("======............................=====Remaining clock time",remainin_time)
                _logger.info("=======............................====Remaining budget hours",f.hours_budget_remain)
                _logger.info("Total members %d",len(f.members))
                if float(remainin_time) < float(f.hours_budget_remain) and f.state != 'close':
                    self.set_jeopardy(cr,uid,f.id,'Out Of Time, Add more resources') 
                elif f.project_state_desc == 'Out Of Time, Add more resources' and f.state == 'Jeopardy':
                    self.pool.get('project.project').set_inprogress(cr, uid,f.id )
                     
                #at the end set project out of jeopardy if all conditions are met         for setting in open state  
        return result
    
    def available_clock_time(self,cr,uid,ids,context = {},args = None,obj = None):
        #available clock time in hrs till last date 6pm
        result = {} 
        for f in self.browse(cr,uid,ids):
            remainin_time = 0.0
            _logger.info("getting available_clock time in hrs : %s",f.data_sources)
            # get due date convetred into date object, then pass to conver date to dateitme
            if f.date:
                due_date1 =  datetime.strptime(f.date, '%Y-%m-%d %H:%M:%S')
                date_start1 =  datetime.strptime(f.date_start, '%Y-%m-%d %H:%M:%S')
                deadline =  datetime.now()
                if date_start1 > datetime.now():
					deadline =  date_start1
                _logger.info("Current time is  %r",  (deadline))
                _logger.info("due_date1  %r",  (due_date1))
                
               
                delta = due_date1 - deadline
                days = delta.days
                hours = delta.seconds//60
                
                _logger.info("Got Delta %r",  (delta))
                _logger.info("Got days %r",  (days))
                _logger.info("Got hours %r",  (hours))
    #             hours = divmod(delta.days * 24 + delta.seconds, 3600)   
    #             _logger.info("Got hourssssssssss %r",  (hours))
    #             hours, remainder = divmod(delta.seconds, 3600)
    #             
    #             remainin_time = ((int(delta.days)*24) +  hours)-6
                #raise osv.except_osv((remainin_time),((int(delta.days)-1)*24))
                #result[f.id] = ((int(delta.days)*24)+1) + int(delta.seconds//3600) + (len(f.members)*(int(delta.days)+1)*10)
                #result[f.id] = (len(f.members)*(int(delta.days)+1)*10)
                result[f.id] = (len(f.members)*((((float(delta.days)*24)) + float(delta.seconds//3600))/24)*10)
            else:
                result[f.id] = 0
        return result        
    
    def data_sources_values(self,cr,uid,ids,context = {},args = None,obj = None):
        result = {} 
        for f in self.browse(cr,uid,ids):
            _logger.info("Getting data source values >>>>>>>>>>>>>>>>>>>>>>>> : %s",f.data_sources)
            for this in f.data_sources:
                if this.name =='PubSub':
                    result[f.id] =str(this.name)
                else:
                    result[f.id] = None
        
        return result
    
    def get_project_total_hours(self,cr,uid,task_id,context = {},args = None,obj = None):
        result = {}
        
        
        for f in self.browse(cr,uid,task_id):
            hours = 0
            work_ids = self.pool.get('project.task').search(cr,uid,[('project_id','=',f.id)])
            if work_ids:
                rec_task = self.pool.get('project.task').browse(cr,uid,work_ids)
                for task in rec_task:
                    hours = hours + task.task_planned_hours
            result[f.id] = hours
        return result
    def get_create_date(self,cr,uid,ids,context = {},args = None,obj = None):
        result = {}
        for f in self.browse(cr,uid,ids):
            cdate =  datetime.strptime(f.create_date, "%Y-%m-%d %H:%M:%S")
            result[f.id] = datetime.strftime(cdate, "%Y-%m-%d")
        return result
    
    def pcreate_time(self,cr,uid,ids,context = {},args = None,obj = None):
        result = {}
        for f in self.browse(cr,uid,ids):
            cdate =  datetime.strptime(f.create_date, "%Y-%m-%d %H:%M:%S")
            result[f.id] = datetime.strftime(cdate, "%H:%M:%S")
        return result
    
    def pedittime(self,cr,uid,ids,context = {},args = None,obj = None):
        result = {}
        for f in self.browse(cr,uid,ids):
            cdate =  datetime.strptime(f.write_date, "%Y-%m-%d %H:%M:%S")
            result[f.id] = datetime.strftime(cdate, "%H:%M:%S")
        return result
    
    def peditdate(self,cr,uid,ids,context = {},args = None,obj = None):
        result = {}
        for f in self.browse(cr,uid,ids):
            cdate =  datetime.strptime(f.write_date, "%Y-%m-%d %H:%M:%S")
            result[f.id] = datetime.strftime(cdate, "%Y-%m-%d")
        return result
		
#     def default_get(self, cr, uid, fields, context=None):
#         if context is None:
#             context = {}
#         res = super(project_project, self).default_get(cr, uid, fields, context)
#         if context.get('default_state'):
#              state_id = self.pool.get('asset.state').search(cr, uid, [('name','=',context['default_state']),('team','=',5)])
#              if state_id:
#                 rec = self.pool.get('asset.state').browse(cr,uid,state_id[0])
#                 res['maintenance_state_id']= rec.id
#                 return res
#              else:
#                 raise osv.except_osv(('state not found->'+str(context['default_state'])),("Ask your administrator to configure default state for project"))
# when uncomment this code add the following one line code to cni_view.xml form view of project , on field project_types (context = " {'default_state':project_types}")
    
    def cempid(self, cr, uid, ids,a, context=None, check=True):
        result = {}
        for f in self.browse(cr,uid,ids):
            sql="""select id,create_uid
                from project_project where id="""+str(f.id)
            cr.execute(sql)
            res=cr.fetchone()
            ids = self.pool.get('hr.employee').search(cr,uid,[('user_id','=',res[1])])
            if ids:
                record = self.pool.get('hr.employee').browse(cr,uid,ids[0])
                result[f.id] = record.id
        return result 
    
    def wempid(self, cr, uid, ids,a, context=None, check=True):
        result = {}
        for f in self.browse(cr,uid,ids):
            sql="""select id,write_uid
                from project_project where id="""+str(f.id)
            cr.execute(sql)
            res=cr.fetchone()
            ids = self.pool.get('hr.employee').search(cr,uid,[('user_id','=',res[1])])
            if ids:
                record = self.pool.get('hr.employee').browse(cr,uid,ids[0])
                result[f.id] = record.id
        return result    
    
    def request_project_tools(self, cr, uid, ids, context=None):
        ctx = {}
        for f in self.browse(cr,uid,ids):
            ids = self.pool.get('hr.employee').search(cr,uid,[('user_id','=',uid)])
            if ids:
                record = self.pool.get('hr.employee').browse(cr,uid,ids[0])
            if not context:
                ctx = {
                'project_id':f.id,
                'employee':record.id,
                }
            else:
                ctx = context
                ctx['project_id'] = f.id
                ctx['employee'] = record.id,
        
        result = {
        'type': 'ir.actions.act_window',
        'name': 'Request Material',
        'res_model': 'asset.requisition',
        'view_type': 'form',
        'view_mode': 'form',
        'view_id': False,
        'nodestroy': True,
        'target': 'new',
        'context': ctx,
        }
        return result 
		
    def request_project_expense(self, cr, uid, ids, context=None):
        ctx = {}
        for f in self.browse(cr,uid,ids):
            ids = self.pool.get('hr.employee').search(cr,uid,[('user_id','=',uid)])
            if ids:
                record = self.pool.get('hr.employee').browse(cr,uid,ids[0])
            if not context:
                ctx = {
                'project_id':f.id,
                'employee':record.id,
                }
            else:
                ctx = context
                ctx['project_id'] = f.id
                ctx['employee'] = record.id,
        
        result = {
        'type': 'ir.actions.act_window',
        'name': 'Project Expense',
        'res_model': 'hr.expense.expense',
        'view_type': 'form',
        'view_mode': 'form',
        'view_id': False,
        'nodestroy': True,
        'target': 'new',
        'context': ctx,
        }
        return result 
    
    
    def attachment_tree_view(self, cr, uid, ids, context):
        partner_id = self.browse(cr,uid,ids)[0].partner_id.id
        task_ids = self.pool.get('project.task').search(cr, uid, [('project_id', 'in', ids)])
        domain = [
             '|',
             '&', ('res_model', '=', 'project.project'), ('res_id', 'in', ids),
             '&', ('res_model', '=', 'project.task'), ('res_id', 'in', task_ids)]
        res_id = ids and ids[0] or False
        return {
            'name': _('Attachments'),
            'domain': domain,
            'res_model': 'ir.attachment',
            'type': 'ir.actions.act_window',
            'view_id': False,
            'view_mode': 'kanban,tree,form',
            'view_type': 'form',
            'limit': 80,
            'context': "{'default_res_model': '%s','default_res_id': %d,'default_workorder': %r,'default_partner_id': %r}" % (self._name, res_id,True,partner_id)
        }
    
    def request_project_consumable_material(self, cr, uid, ids, context=None):
        ctx = {}
        for f in self.browse(cr,uid,ids):
            ids = self.pool.get('hr.employee').search(cr,uid,[('user_id','=',uid)])
            if ids:
                record = self.pool.get('hr.employee').browse(cr,uid,ids[0])
            if not context:
                ctx = {
                'project_id':f.id,
                'employee':record.id,
                }
            else:
                ctx = context
                ctx['project_id'] = f.id
                ctx['employee'] = record.id,
        
        result = {
        'type': 'ir.actions.act_window',
        'name': 'Request Material',
        'res_model': 'daily.material.reconciliation',
        'view_type': 'form',
        'view_mode': 'form',
        'view_id': False,
        'nodestroy': True,
        'target': 'new',
        'context': ctx,
        }
        return result 

    def get_fields_for_contact_info(self, cr, uid, ids,field_names, context=None, check=True):
        """ """
        result = {}
        for f in self.browse(cr, uid, ids, context=context):
            result[f.id] = {}
            if type(field_names) is not list:
                field_names = [field_names]
            for key_str in field_names:
                result[f.id][key_str] = '--'
            wo = self.pool.get('project.workorder').search(cr, uid, [('project_id','=',f.id)])
            if wo:
                obj = self.pool.get('project.workorder').browse(cr,uid,wo[0])
            
                if 'customer_name' in field_names:
                    result[f.id]['customer_name'] = obj[0].customer_name
                if 'customer_legal_name' in field_names:
                    result[f.id]['customer_legal_name'] = obj[0].customer_legal_name
                if 'customer_rating_cd' in field_names:
                    result[f.id]['customer_rating_cd'] = obj[0].customer_rating_cd
                    
                if 'customer_type_cd' in field_names:
                    result[f.id]['customer_type_cd'] = obj[0].customer_type_cd.name 
                if 'custtimezone' in field_names:
                    result[f.id]['custtimezone'] = 'Field Removed'
                if 'client_dispatchsec' in field_names: 
                    result[f.id]['client_dispatchsec'] = 'Field Removed'
                if 'srv_cls_cs' in field_names:
                    result[f.id]['srv_cls_cs'] = 'Field Removed'
#                if 'client_contacts_list_txt' in field_names:
#                    result[f.id]['client_contacts_list_txt'] = obj[0].client_contacts_list_txt
                    
                    
        _logger.info("==============Contact info tab, fields from ================= : %s",result)
        return result
    
    def prjmgr(self, cr, uid, ids,field_names, context=None, check=True):
        """ Read the 'address' functional fields. """
        result = {}
        part_obj = self.pool.get('hr.employee')
        for project in self.browse(cr, uid, ids, context=context):
            result[project.id] = {}
            if type(field_names) is not list:
                field_names = [field_names]
            for key_str in field_names:
                result[project.id][key_str] = '--'
            emp_id = part_obj.search(cr, uid, [('user_id','=',project.project_manager.id)])
            if emp_id:
                obj = part_obj.browse(cr,uid,emp_id[0])
            
                if 'prj_mgr_email' in field_names:
                    result[project.id]['prj_mgr_email'] = obj.work_email 
                if 'prj_mgr_phone' in field_names:
                    result[project.id]['prj_mgr_phone'] = obj.work_phone
                if 'prj_mgr_cell' in field_names:
                    result[project.id]['prj_mgr_cell'] = obj.mobile_phone
                if 'prj_mgr_ext' in field_names:
                    result[project.id]['prj_mgr_ext'] = obj.extenstion_no
        return result
    def _get_currency(self, cr, uid, ids, field, args, context=None):
        res = {}
        for sr in self.browse(cr, uid, ids, context=context):
            res[sr.id] = sr.partner_id.company_id.currency_id.id
        return res
    
    def alert_condition(self,cr,uid,ids,context = {},args = None,obj = None):
        result = {} 
        for f in self.browse(cr,uid,ids):
            if f.state == 'Jeopardy':
                result[f.id] = 'Jeopardy'
            else:
                result[f.id] = 'Normal'
                if not f.project_state_desc == 'Normal':
                    self.write(cr,uid,f.ids,{'project_state_desc':'Normal'})
        return result
    def open_map(self, cr, uid, ids, context=None):
        if context is None:
            context = {}

        address = self.browse(cr, uid, ids)
        url = "http://maps.google.com/maps?oi=map&q="
        if address[0].work_location.name:
            url += address[0].work_location.name.replace(' ','+')
        if address[0].work_location.street2:
            url += address[0].work_location.street2.replace(' ','+')
        if address[0].work_location.city:
            url += '+'+address[0].work_location.city.replace(' ','+')
        if address[0].work_location.state_id:
            url += '+'+address[0].work_location.state_id.name.replace(' ','+')
        if address[0].work_location.postal:
            url += '+'+address[0].work_location.postal.replace(' ','+')
        if address[0].work_location.country_id:
            url += '+'+address[0].work_location.country_id.name.replace(' ','+')

        return {
            'type': 'ir.actions.act_url',
            'url': url,
            'target': 'new'
        }
		
    _inherit ='project.project'
    _columns = {
    
    
    'project_manager':fields.many2one('res.users','Project Manager'),
    'client_business_unit':fields.many2one('res.users','Project Manager'),
    'display_project_manager': fields.related('project_manager','name', type='char', string='Project Manager'),# this field is added to add project manager on tab 'clients updates'
    'productcategorycd': fields.many2one('project.product.category','Product Category'), # String    The product category for the order (e.g. Business Internet, BVOIP)
    'client_contactlist': fields.many2one('res.partner', string='Contact'),
    'client_email': fields.related('client_contactlist','email', type='char', string='Email'),
    'date_close':fields.date('Date Closed'),
    'client_phone': fields.related('client_contactlist','phone', type='char', string='Phone'),
    'client_mobile': fields.related('client_contactlist','mobile', type='char', string='Mobile'),
    'client_ext': fields.related('client_contactlist','client_ext_no', type='char', string='Ext'),
    'client_contactlist_esclation': fields.many2one('res.partner', string='Contact'),
    'client_email_esclation': fields.related('client_contactlist_esclation','email', type='char', string='Email'),
    'client_phone_esclation': fields.related('client_contactlist_esclation','phone', type='char', string='Phone'),
    'client_mobile_esclation': fields.related('client_contactlist_esclation','mobile', type='char', string='Mobile'),
    'client_ext_esclation': fields.related('client_contactlist_esclation','client_ext_no', type='char', string='Ext'),
	'data_sources':fields.many2many('data.source',string ='Data Source'),
	'modify_data_sources':fields.many2many('modify.data.source',string ='Data Source'),
    'create_empid':fields.function(cempid, store=True,  method=True, string='employee_id_create',type='many2one',relation='hr.employee'),
    'write_empid':fields.function(wempid, store=True,  method=True, string='employee_id_write',type='many2one',relation='hr.employee'),
    'create_user_phone': fields.related('create_empid','work_phone', type='char', string='Contact#', readonly=True,),
    'prj_mgr_phone': fields.function(prjmgr,multi='analytic_analysis', store=False,  method=True, string='Project Manager Office#',type='char'),
    'prj_mgr_ext': fields.function(prjmgr,multi='analytic_analysis', store=False,  method=True, string='Project Manager Ext',type='char'),
    'prj_mgr_cell': fields.function(prjmgr,multi='analytic_analysis', store=False,  method=True, string='Project Manager Cell',type='char'),
    'prj_mgr_email': fields.function(prjmgr, store=False, multi='analytic_analysis', method=True, string='Project Manager Email',type='char'),
    'write_user_phone': fields.related('write_empid','work_phone', type='char', string='Contact#', readonly=True),                  
	'project_crete_date':fields.function(get_create_date, type='date', string="Date Created",),
    'project_create_time':fields.function(pcreate_time, type='char',size = 30, string="Date Created",),
    'project_edit_time':fields.function(pedittime,method = True ,type='date', string="Last Modified Date",),     
    'project_edit_date':fields.function(peditdate,method = True, type='char',size = 30, string="Last Modified"),      
    'closed_issue_count': fields.function(_closed_issue_count ,method = True, type='integer', string="Closed Issues",),
    'project_progress':fields.function(get_progress,method = True,string = 'Progress(%)',type = 'float'),
    'restrict_access':fields.function(is_access_restricted, method=True, string='Restrict Access',type='boolean'),
    'isinjeopardy':fields.function(project_has_issue, method=True, string='Has Issue',type='boolean'),
    'available_clock_time':fields.function(available_clock_time, method=True, string='Avaialbe clock time',type='float'),
    'desc': fields.html('Project Description'),
    'project_tasks_work': fields.one2many('project.task.work', 'project_id', 'Tasks Work'),
    'attached_docs': fields.one2many('ir.attachment', 'res_id', domain=[('res_model','=','project.project'),('attachment_soruce','=','Work_order')],readonly = True),
    'project_expenses': fields.one2many('project.expenses', 'project_id', 'Expenses'),
    # for displaying expenses on blling tab
    'project_expenses_lines2': fields.one2many('prj.billing.expenseline', 'project_id', 'Expenses2'),
    'quot_no': fields.char('Quote#', size=164),
    'work_location': fields.many2one('project.work.location', 'Work Location'),
    'billin_info': fields.integer('Billing'),
    'hours_charged': fields.function(get_charged_hours, method=True, string='Hours Charged',type='float'),
    'planned_expense': fields.float('Expenses Budget'),
    'expense_charged': fields.function(get_project_charged_expenses, method=True, string='Expense Charged',type='float'),
	'company_currency_id': fields.function(_get_currency, type='many2one', method=True, string='Currency', readonly=True, obj="res.currency"),
	'budget_remain': fields.function(get_net_expenses, method=True, string='Expense Budget Remain',type='float'),
    'hours_budget_remain': fields.function(get_net_hours, method=True, string='Hours Budget',type='float'),
    'hours_budget_remain_kanban': fields.float('Hours Budget.'),
    'open_issues': fields.integer('Open Issues'),
    'closed_issues': fields.integer('Closed Issues'),
    'excel_project': fields.boolean('Issued',readonly=True),
    'upload_file': fields.binary('File'),
    'date': fields.datetime('Due Date', select=True),
    'date_start': fields.datetime('Start Date', select=True),
    'project_planned_hours': fields.function(get_project_total_hours,method =True, string= "Quoted Hours", type ='float'),
    'billing': fields.float('Billing'),
    'project_types':fields.many2many('project.type',string ='Project Type'),
    'project_type_template':fields.many2one('project.generic.template', 'Type'),
    'modifier':fields.many2one('res.users', 'Edit by'),
    'modified_date':fields.datetime( 'Edit Datetime'),
    'consumable': fields.one2many('daily.material.reconciliation', 'project', 'Consumable'),
    'stockable': fields.one2many('get.client.stock', 'project', 'Stockable'),
    'tools_used': fields.one2many('asset.requisition', 'project', 'Tools'),
    'reservation_lines': fields.one2many('asset.requisition.lines', 'project_id', 'Tools'),
    'material_ids': fields.one2many('project.material', 'name', 'Material'),
    'invoice_ids': fields.one2many('project.invoice', 'name', 'Project Invoicing Summary'),
    'consumeable_items': fields.one2many('material.reconcile.lines', 'project_id', 'Material'),
    'project_billing_material': fields.one2many('prj.billing.materials', 'project_id', 'Materials'),
    'project_id': fields.char('Project ID', size=64),
    'priority': fields.char('Priority', size=64),
    'primevera_id': fields.char('PrimaveraID', size=64),
    'actv_desc': fields.char('Activity Desc', size=64),
    'network_id': fields.char('Network', size=64),
    'wbs': fields.char('WBS', size=64),
    'site_code': fields.date('Site Code'),
    'template_loaded':fields.boolean("Template Loaded"),
    'status': fields.char('SC Status', size=64),
    'priority_setting_source':fields.selection([
                                ('set_internally','Set Internally'),
                                ('set_externally','Set Externally')],'Priority Source'),
    'state': fields.selection([
                                ('Jeopardy','Jeopardy'),
                                ('draft','Draft'),
#                                ('template', 'Template'),
                                ('open','Open'),
                                ('in_progress','In Progress'),
                                ('OnHold','On Hold'),
                                ('cancelled', 'Cancelled'),
                                ('pending','Pending'),
                                ('Completed','Completed'),
                                ('close','Closed')],
                                  'Status', required=True, copy=False, track_visibility='onchange'),
    'project_state_desc': fields.char('State Desc', size=64),
    'alert_condition':fields.function(alert_condition, type='char',size = 30, string="Alert Condition",),
    'maintenance_state_id':fields.many2one('asset.state', 'State', domain=[('team','=','5')]),
    'maintenance_state_color': fields.related('maintenance_state_id', 'state_color', type="selection", selection=STATE_COLOR_SELECTION, string="Color", readonly=True),
    'project_work_order_ids':fields.one2many('project.workorder', 'project_id', 'Work Order'),
    'project_closing_logs':fields.one2many('project.starting.closding.logs', 'project_id', 'logs'),
    'project_transactional_logs': fields.one2many('project.transactional.log', 'project_id', 'Transactional Logs'),
    'issue_count': fields.function(_open_issue_count, type='integer', string="Issues"),    
    'maintenance_state_kanban_display': fields.function(kanban_state_display , type='char', string="sss"),     
    # -----------TELUS Fields-----------

	'priorityCd': fields.many2one('project.priority', 'Priority'), # String	 Priority of the job (1 is highest)	1-26
   
	# -----------Customer details-----------
    
    'customer_name':  fields.function(get_fields_for_contact_info,multi='for_contact_info', store=False,  method=True, string='Customer Name',type='char'),
    'customer_legal_name': fields.function(get_fields_for_contact_info,multi='for_contact_info', store=False,  method=True, string='Customer Legal Name',type='char'), # String	Legal name of the customer (if required)	Varies
	'customer_rating_cd': fields.function(get_fields_for_contact_info,multi='for_contact_info', store=False,  method=True, string='Customer Rating',type='char'), # String	Code specifying the monthly spend of the customer	Values are not known for reference only
    'customer_type_cd': fields.function(get_fields_for_contact_info,multi='for_contact_info', store=False,  method=True, string='Customer Type',type='char'), # String	Indicates the type of customer	CUSTOMER or INTERNAL
    'custtimezone': fields.function(get_fields_for_contact_info,multi='for_contact_info', store=False,  method=True, string='Client Dispatch Timezone',type='char'),
    'client_dispatchsec': fields.function(get_fields_for_contact_info,multi='for_contact_info', store=False,  method=True, string='Client Dispatch Sector',type='char'),
    'srv_cls_cs':fields.function(get_fields_for_contact_info,multi='for_contact_info', store=False,  method=True, string='Client Business Unit',type='char'),
    #'client_contacts_list_txt': fields.function(get_fields_for_contact_info,multi='for_contact_info', store=False,  method=True, string='Comments/remarks',type='char'),
    'client_contacts_list': fields.one2many('client.contact.list','parent_project','Contact List'), # Structure    List of customer contacts
    'client_contacts_list_txt': fields.text('Comments/Remarks'),
    
    # job status codes
    'jobassignmentid': fields.function(get_project_name, type='char', string="Job Assignment Id"),  
    'requiredteamworkerlist':fields.many2one('res.users', 'Required Team WorkerList', domain=[('work_on_task', '=',True)], select=True, track_visibility='onchange'),
    'preferredteamworkerlist':fields.many2one('res.users', 'Preferred Team WorkerList', domain=[('work_on_task', '=',True)], select=True, track_visibility='onchange'),
    'prohibitedteamworkerlist':fields.many2one('res.users', 'Prohibited Team WorkerList', domain=[('work_on_task', '=',True)], select=True, track_visibility='onchange'),
    'jobscheduledstartdate': fields.date('Job Scheduled Start Date'),
    'jobscheduledenddate': fields.date('Job Scheduled End Date'),
    'statuscd': fields.selection([('ACCEPTED', 'Accepted'),
                                    ('COMPLETE','Complete'),
                                    ('DISPATCHED','Dispatched'),
                                    ('EN_ROUTE','EnRoute'),
                                    ('ON_SITE', 'OnSite'),
                                    ('INCOMPLETE','In Complete'),
                                    ('REJECTED','Rejected'),
                                    ('TENTATIVE','Tentative')],
                                      'Status', copy=False),
        # 4.3    Job Status Codes
    
        # Code          Value
        # ACCEPTED      Accepted
        # COMPLETE      Complete
        # DISPATCHED    Dispatched
        # EN_ROUTE      En Route
        # ON_SITE       On Site
        # REJECTED      Rejected
        # TENTATIVE    
        
        'acceptremarktxt': fields.char('Remarks',size = 150),
        'enrouteremarktxt': fields.char('Remarks',size = 150),
        'onsiteremarktxt': fields.char('Remarks',size = 150),
        'completeremarktxt': fields.char('Remarks',size = 150),
        'incompleteremarktxt': fields.char('Remarks',size = 150),
        'rejectremarktxt': fields.char('Remarks',size = 150),
                
        'acceptdatetime': fields.datetime('Date Time',readonly = True),
        'enroutedatetime': fields.datetime('Date Time',readonly = True),
        'onsitedatetime': fields.datetime('Date Time',readonly = True),
        'completedatetime': fields.datetime('Date Time',readonly = True),
        'incompletedatetime': fields.datetime('Date Time',readonly = True),
        'rejectdatetime': fields.datetime('Date Time',readonly = True),
        'tentativedatetime': fields.datetime('Date Time',readonly = True),
        'dispatcheddatetime': fields.datetime('Date Time',readonly = True),
        
        'incompletereasoncd': fields.selection([('CUST_CANCEL', 'Customer Cancel'),
                                              ('CUST_NOT_READY','Customer Not Ready'),
                                              ('INCORRECT_CUST','Incorrect Customer Information'),
                                              ('MULTI_DAY_JOB','Multi Day Job'),
                                              ('NO_ACCESS', 'No Access'),
                                              ('PARTS','Parts'),
                                              ('SAFETY_CUST','Safety Customer Fault'),
                                              ('SAFETY_TELUS','Safety TELUS Resolution')],
                                              'Incomplete Reason', copy=False),
        # 4.6    Incomplete Reason Codes
    
        # Code              Value
        # CUST_CANCEL       Customer Cancel
        # CUST_NOT_READY    Customer Not Ready
        # INCORRECT_CUST    Incorrect Customer Information
        # MULTI_DAY_JOB     Multi-Day Job
        # NO_ACCESS         No Access
        # PARTS             Parts
        # SAFETY_CUST       Safety Customer Fault
        # SAFETY_TELUS      Safety TELUS Resolution    
        'rejectreasoncd': fields.selection([('CUST_CANCEL', 'Customer Cancel'),
                                            ('CUST_NOT_READY','Customer Not Ready'),
                                            ('DISPATCH','Dispatcher'),
                                            ('INCORRECT_CUST','Incorrect Customer Information'),
                                            ('NO_ACCESS', 'No Access'),
                                            ('PARTS','Parts'),
                                            ('TECH_SKILLS','Tech Additional Skills')],
                                            'Reject Reason',  copy=False),
        # 4.5    Reject Reason Codes
    
        # Code              Value
        # CUST_CANCEL       Customer Cancel
        # CUST_NOT_READY    Customer Not Ready
        # DISPATCH          Dispatcher
        # INCORRECT_CUST    Incorrect Customer Information
        # NO_ACCESS         No Access
        # PARTS             Parts
        # TECH_SKILLS       Tech Additional Skills
        
        'resolutioncode': fields.char('Resolution Code',size = 150),
        'handler_history': fields.one2many('project.task.handling.logs', 'project_id', 'Logs'),
	# -----------Metrics Corporate Loadings & Ratios-----------
        'met_average_tech_labour_rate': fields.float('Average tech labour rate',size = 150),
        'met_wsib_ei_overheads': fields.float('WSIB & EI Overheads',size = 150),
        'met_average_truck_roll_cost_km': fields.float('Average Truck Roll cost/hr ($)',size = 150),
        'met_group_benefits_loadings_rate': fields.float('Group Benefits loadings rate',size = 150),
        'met_non_productive_loadings': fields.float('Non-productive loadings',size = 150),
        'met_management_overheads': fields.float('Management Overheads',size = 150),
        'met_insurance_taxes': fields.float('Insurance & Taxes',size = 150),
        'met_fixed_overheads_loadings': fields.float('Fixed overheads loadings',size = 150),
        'met_dynamic_overheads_loadings': fields.float('Dynamic overheads loadings',size = 150),
        'met_shareholder_privilege': fields.float('Shareholder Privilege',size = 150),
		'pl_summary_revenue_ids': fields.one2many('project.pl.rev.summary', 'name', 'P and L Summary'),
        'pl_summary_cost_ids': fields.one2many('project.pl.cost.summary', 'name', 'P and L Summary'),
		'labour_hours_expended_ids': fields.one2many('project.labour.hours.expended', 'name', 'Labour Hours Expended'),
		'graph_area': fields.text('Graph Area'),
		'materials_consumed_ids': fields.one2many('project.materials.consumed', 'name', 'Materials Consumed'),
        'overhead_allocations_ids': fields.one2many('project.overhead.allocations', 'name', 'Overhead Allocations'),
        'expenses_incurred_ids': fields.one2many('project.expenses.incurred', 'name', 'Expenses Incurred'),
		'net_project_margins_ids': fields.one2many('project.net.margin', 'project_id', 'NET PROJECT MARGIN'),
        'project_pl_display_summary_ids': fields.one2many('project.pl.display.summary', 'name', 'PL Summary Display'),
        'data_sources_values': fields.function(data_sources_values,method =True, store={'project.project': (lambda self, cr, uid, ids, c={}: ids, [ 'data_sources'],1)}, string= "data_sources", type ='char'),

    }
    
    
    _defaults = {
                 'state':lambda *a:'draft',
                 'alert_condition':lambda *a:'Normal',
                 #'project_types':lambda *a:'Master',
                 'excel_project':lambda *a:False,
                 'privacy_visibility': 'followers',
                 'partnerAcknowledgeStatusCd':'ACKNOWLEDGED',
                 'met_average_tech_labour_rate':25.0,
                 'met_wsib_ei_overheads':15.0,
                 'met_average_truck_roll_cost_km':5.0,
                 'met_group_benefits_loadings_rate':8.0,
                 'met_non_productive_loadings':4.0,
                 'met_management_overheads':15.0,
                 'met_insurance_taxes':7.0,
                 'met_fixed_overheads_loadings':13.0,
                 'met_dynamic_overheads_loadings':3.0,
                 'met_shareholder_privilege':0.0,
                 'hours_budget_remain_kanban':0.0
    }
    
    
    def set_done(self, cr, uid, ids, context=None):
        #super(project_project, self).set_done(cr, uid, ids, context)
        for f in self.browse(cr,uid,ids):
            self.write(cr, uid, ids, {'state': 'close','date_close':date.today()}, context=context)
            self.pool.get('project.starting.closding.logs').update_project_status_log(cr,uid,f.id,'Project is closed') 

            state_id = self.pool.get('asset.state').search(cr, uid, [('name','=',f.state),('team','=',5)])
            if state_id:
                rec = self.pool.get('asset.state').browse(cr,uid,state_id[0])
                self.write(cr, uid, ids, {'maintenance_state_id': rec.id})
            else:
                raise osv.except_osv(('state not found ->'+str(f.state)),("Ask your administrator to configure process states"))
        return
    
    def set_open(self, cr, uid, ids,*args):
        super(project_project, self).set_open(cr, uid, ids)
        for f in self.browse(cr,uid,ids):
            self.pool.get('project.starting.closding.logs').update_project_status_log(cr,uid,f.id,'Project is Re-Opened')
            state_id = self.pool.get('asset.state').search(cr, uid, [('name','=',f.state),('team','=',5)])
            if state_id:
                rec = self.pool.get('asset.state').browse(cr,uid,state_id[0])
                self.write(cr, uid, ids, {'maintenance_state_id': rec.id})
               
            else:
                raise osv.except_osv(('state not found->'+str(f.state)),("Ask your administrator to configure process states"))
        return
    
    def set_pending(self, cr, uid, ids, context=None):
        super(project_project, self).set_pending(cr, uid, ids, context)
        for f in self.browse(cr,uid,ids):
            self.pool.get('project.starting.closding.logs').update_project_status_log(cr,uid,f.id,'Project is set to Pending')
            
            state_id = self.pool.get('asset.state').search(cr, uid, [('name','=',f.state),('team','=',5)])
            if state_id:
                rec = self.pool.get('asset.state').browse(cr,uid,state_id[0])
                self.write(cr, uid, ids, {'maintenance_state_id': rec.id})
            else:
                raise osv.except_osv(('state not found->'+str(f.state)),("Ask your administrator to configure process states"))
        return

    def set_onhold(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, {'state': 'OnHold'})
        for f in self.browse(cr,uid,ids):
            
            self.pool.get('project.starting.closding.logs').update_project_status_log(cr,uid,f.id,'Project set On-Hold')
            state_id = self.pool.get('asset.state').search(cr, uid, [('name','=',f.state),('team','=',5)])
            if state_id:
                rec = self.pool.get('asset.state').browse(cr,uid,state_id[0])
                self.write(cr, uid, ids, {'maintenance_state_id': rec.id}) 
            else:
                raise osv.except_osv(('state not found ->'+str(f.state)),("Ask your administrator to configure process states"))  
        return
    def set_inprogress(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, {'state': 'in_progress'})
        for f in self.browse(cr,uid,ids):
            
            self.pool.get('project.starting.closding.logs').update_project_status_log(cr,uid,f.id,'Project set In Progress')
            state_id = self.pool.get('asset.state').search(cr, uid, [('name','=',f.state),('team','=',5)])
            if state_id:
                rec = self.pool.get('asset.state').browse(cr,uid,state_id[0])
                self.write(cr, uid, ids, {'maintenance_state_id': rec.id}) 
            else:
                raise osv.except_osv(('state not found ->'+str(f.state)),("Ask your administrator to configure process states"))  
        return
    
    def set_jeopardy(self, cr, uid, ids, *args):
        if len(args) >0:
            reason = args[0]
        else:
            reason = 'Set To Jeopardy'
        
        
        self.write(cr, uid, ids, {'state': 'Jeopardy','project_state_desc':reason})
        for f in self.browse(cr,uid,ids):
            
            self.pool.get('project.starting.closding.logs').update_project_status_log(cr,uid,f.id,'Project placed in Jeopardy')
            state_id = self.pool.get('asset.state').search(cr, uid, [('name','=',f.state),('team','=',5)])
            if state_id:
                rec = self.pool.get('asset.state').browse(cr,uid,state_id[0])
                self.write(cr, uid, ids, {'maintenance_state_id': rec.id}) 
            else:
                raise osv.except_osv(('state not found ->'+str(f.state)),("Ask your administrator to configure process states"))  
        return
    
    
    def set_completed(self, cr, uid, ids, context=None):

        self.write(cr, uid, ids, {'state': 'Completed'})
        for f in self.browse(cr,uid,ids):
            
            self.pool.get('project.starting.closding.logs').update_project_status_log(cr,uid,f.id,'Project is marked as Completed')
            state_id = self.pool.get('asset.state').search(cr, uid, [('name','=',f.state),('team','=',5)])
            if state_id:
                rec = self.pool.get('asset.state').browse(cr,uid,state_id[0])
                self.write(cr, uid, ids, {'maintenance_state_id': rec.id})
            else:
                raise osv.except_osv(('state not found->'+str(f.state)),("Ask your administrator to configure process states")) 

        return
    
    def set_cancel(self, cr, uid, ids, context=None):
        super(project_project, self).set_cancel(cr, uid, ids, context)
        for f in self.browse(cr,uid,ids):
            
            self.pool.get('project.starting.closding.logs').update_project_status_log(cr,uid,f.id,'Project is Canceled') 
            state_id = self.pool.get('asset.state').search(cr, uid, [('name','=',f.state),('team','=',5)])
            if state_id:
                rec = self.pool.get('asset.state').browse(cr,uid,state_id[0])
                self.write(cr, uid, ids, {'state': 'cancelled','maintenance_state_id': rec.id}) 
            else:
                raise osv.except_osv(('state not found->'+str(f.state)),("Ask your administrator to configure process states"))
        return
    
    
project_project()


class project_starting_closding_logs(osv.osv):
  
    def update_project_status_log(self, cr, uid, project_id, log_statement):
        self.pool.get('project.starting.closding.logs').create(cr,uid,{
                                                        'name':log_statement,
                                                        'project_id':project_id, 
                                                        'event_date':datetime.now(),
                                                        'event_by':uid
                                                         }) 
        return
    _name = "project.starting.closding.logs"
    _description = "keeps track of project closing and staring details"
    _order = 'event_date DESC'
    _columns = {
        'name': fields.char('Log Statement'),
        'project_id':fields.many2one('project.project','Project'),
        'event_date': fields.datetime('Date Time'),
        'event_by': fields.many2one('res.users','Done By'),
            }
   
project_starting_closding_logs()

class project_workorder(osv.osv):
  
    _name = "project.workorder"
    _description = "work order project"
    _columns = {
        'project_id':fields.many2one('project.project','Project'),
        # -----------TELUS Fields-----------
	'job_created_date': fields.datetime('Created Date', size=64), # Pub Sub project created date
    'job_created_version': fields.char('#', size=64), # Pub Sub project version
    'jobTypeCd': fields.many2one('project.jobtype','Job Type'), # String    Indicates the type of job (e.g Managed LAN)
    # 4.4 Job Type Codes
 
    # Code                Value
    # BUS_LINE_INTERNET    Business Line Internet
    # BVOIP                BVOIP
    # CARRIER_ETHERNET    Carrier Ethernet
    # CENTRAL_OFFICE    Central Office
    # PACKET_SERVICE    Packet Service
    # PRE_STAGE            Pre-Stage
    # PREFIELD            Prefield
    # PRIVATE_LINE        Private Line
    # WAN_L2_L3            WAN L2/L3
 
     'productCategoryCd': fields.many2one('project.product.category','Product Category'), # String    The product category for the order (e.g. Business Internet, BVOIP)
    # 4.1    Product Categories
 
    # Code    Value
    # BUS_INTERNET        Business Internet
    # BVOIP                BVOIP
    # CES                CES (Carrier Ethernet Switched)
    # CI_DIRECT            CI Direct(Carrier Internet Direct)
    # CML3                CML3 (Customer Managed Layer 3)
    # DID                DID
    # DS0_DS1            DS (DS0, DS1)
    # DS3                DS3
    # EAS                EAS (Ethernet Access Service)
    # FRAME_RELAY        Frame Relay
    # IBL                IBL
    # OCN                OCN (Optical Carrier Networking)
    # OPTICAL_ETHERNET    Optical Ethernet
    # PRI_BRI            PRI/BRI
    # ROUTED_ETHERNET    Ethernet Routed
    # WAN_L2_L3            WAN L2/L3
 
    'priorityCd': fields.many2one('project.priority', 'Priority'), # String     Priority of the job (1 is highest)    1-26
    'externalJobGroupingId': fields.char('External Job Grouping ID', size=12), # String    Call ID in the TELUS dispatch system    12-digit number (e.g. 100000223668)
    'workOrderActionCd': fields.many2one('project.order.action','Work Order Action'), # String    Indicates if the job is an install, move, change, or repair    Varies based on source system (R, I, PV, etc.)
    'workforceSegmentCd': fields.many2one('workforce.segment', 'Workforce Segment'), # String    The segment of the workforce required for the job (e.g. data, cable repair, mass market)    DATA, MM
    'partnerAcknowledgeStatusCd': fields.selection([('ACKNOWLEDGED','ACKNOWLEDGED'),('DECLINED','DECLINED')],'Partner Acknowledgment Status'), # String    Indicates if the partner acknowledged or declined the job    ACKNOWLEDGED or DECLINED
    'partnerAcknowlegeStatusDateTime': fields.datetime('Acknowledgment DateTime Stamp', size=64), # DateTime    Date/Time (in UTC) the partner either acknowledged or declined the job
    'partnerAcknowledgeStatusRemarkTxt': fields.char('Partner Status Remarks', size=64), # String    Remarks entered when the parter acknowledged/declined the job.
    'classificationCd': fields.many2one('project.classification','Classification'), # String    Indicates the job classification    ORDER, TROUBLE, or MAINTENANCE
    # should be auto generated no
    'workGroupCd': fields.char('Work Group', size=64), # String    The workGroup required for the job    Typically used for certain trouble tickets
    #
    'productTechnologyCd': fields.many2one('project.product.technology','Product Technology'), # String    The technology used to provide the service (e.g. copper, fibre)    See appendix for values
    # 4.2    Technology Codes
 
    # Code            Value
    # COPPER        Copper
    # COPPER_BONDED    Copper Bonded
    # ETTS            ETTS
    # FIBRE            Fibre
    # GPON            GPON
    # SAT            Satellite
    # WIRELESS        Wireless
    'externalJobId': fields.integer('External Job ID'), # Integer    Task number in the TELUS dispatch system    Usually 0, but can be from 0-10 typically.
    'outofServiceInd': fields.boolean('Onto Service'), # Boolean    Indicates if the customer is out of service or not    True/False
    'serviceIdentification': fields.many2one('serviceidentification.no', 'Service Identification'), # Structure    Section indicating the service identifier for the customer
    # -----------Work order fields-----------
    
    'work_orderid': fields.char('Work Order (WO) ID', size=64), # String    Unique identifier for the work order    Often the same number as the Call ID, but can be different.
    'originating_systemid': fields.char('Originating System ID', size=64), # String    Unique identifier for the source system of the job    3259, 14184 and others
    'originating_systemwork_order_groupid': fields.char('Originating System Work Group ID', size=64), # String    Identifier if the job is part of a group of jobs    Known as the Solution ID, typically a 6-digit number
    'originating_systemwork_orderid': fields.char('Originating System WO ID', size=64), # String    Service order or trouble ticket number from the host system    Varies depending on the source
    'originating_system_work_order_internalid': fields.char('Originating System WO Internal ID', size=64), # String    Unique key of the service order or trouble ticket number from the host system    Varies depending on the source
    'originating_system_workorder_extension': fields.char('Originating System Work Extension', size=64), # String    Extension of the order or ticket number that can change with revisions    Typically A, B, C, etc. but not used for eastern operations
    'secondary_systemid': fields.char('Secondary System ID', size=64), # String    Unique identifier for the secondary system (when one system books, and the other provides the details)    Varies depending on the source
    'secondary_system_work_orderid': fields.char('Secondary System WO ID', size=64), # String    Secondary service order or trouble ticket number from the host system    Varies depending on the source
    'secondary_system_work_order_internalid': fields.char('Secondary System WO InternalID', size=64), # String    Unique key of the secondary service order or trouble ticket number from the host system    Varies depending on the source
    'work_order_duedate': fields.datetime('WO Due DateTime'), # DateTime    Date/Time (in UTC) when the job must be completed.
    'work_order_appointment_start_date': fields.datetime('WO Appionment Start DateTime'), # datetimeTime    datetime/Time (in UTC) of the start of the arrival window for the job
    'work_order_appointment_end_date': fields.datetime('WO Appionment End DateTime'), # DateTime    Date/Time (in UTC) of the end of the arrival window for the job
    'work_order_early_startdate': fields.datetime('WO Early Start DateTime'), # DateTime    Date/Time (in UTC) of the earliest time the job can be started (when there is no appointment window)
    'estimated_duration_num': fields.float('Estimated Duration No'), # Float    The estimated duration of the job    1.0, 3.5, etc.
    'estimated_duration_unitcd': fields.datetime('Estimated Duration Unit Cd', size=64), # String    The unit of measure for the estimated duration    HOURS
    'originating_system_work_order_createdate': fields.datetime('Originating System WO Creation DateTime'), # DateTime    The date/time (in UTC) the order or ticket was created in the originating system
    'work_order_attribute_list': fields.many2one('workorder.attribute.list','WO Attribute List'), # Structure    List of name/value pairs of various attributes
    'work_order_detail_ist': fields.many2one('workorder.details.list','WO Details List'),
   #customer details
    'customer_name': fields.char('Customer Name', size=64,required = False),
    'customer_legal_name': fields.char('Customer Legal Name', size=64), # String    Legal name of the customer (if required)    Varies
    'customer_rating_cd': fields.char('Customer Rating', size=64), # String    Code specifying the monthly spend of the customer    Values are not known for reference only
    'customer_type_cd': fields.many2one('project.customer.type','Customer Type'), # String    Indicates the type of customer    CUSTOMER or INTERNAL
    #'custtimezone': fields.char('Client Dispatch Timezone'),
    #'client_dispatchsec': fields.char('Client Dispatch Sector'),
    #'srv_cls_cs':fields.char('Client Business Unit'),
    'market_segment_cd': fields.char('Market Segment', size=64), # 
    'location': fields.many2one('cust.location','Location List'), # Structure Section indicating the location of the job     
    'customer_contact_list': fields.one2many('cust.contactlist','parent_project','Contact List'), # Structure    Section indicating the location of the job     
    'serviceClassCd': fields.many2one('project.serviceclass','Service Class'), # String    Service class of the job (residential, business, government, telco)    R, B, G or T   
    'accept_remark': fields.text('Accept Remarks', size=160), # 
    'enroute_remark': fields.text('En-Route Remarks', size=160), # 
    'onsite_remark': fields.text('On-Site Remarks', size=160), # 
    'incomplete_remark': fields.text('In Complete Remarks', size=160), # 
    'reject_remark': fields.text('Reject Remarks', size=160), # 
    'rejected_time_stamp': fields.datetime('Rejected Time Stamp'), # 
    'rejected_reason': fields.char('Rejected Reason', size=150), # 
    'rejected_by': fields.char('Rejected By', size=64), # 
    'accepted_time_stamp': fields.datetime('Accepted Time Stamp'), # 
    'en_route_time_stamp': fields.datetime('En-Route Time Stamp'), # 
    'onsite_time_stamp': fields.datetime('On-Site Time Stamp'), # 
    'complete_time_stamp': fields.datetime('Complete Time Stamp'), # 
    'incomplete_time_stamp': fields.datetime('In-Complete Time Stamp'), # 
    'incomplete_reason': fields.char('In-Complete Reason', size=150), # 
    'cancelled_time_stamp': fields.datetime('Cancelled Time Stamp'), # 
    'restore_date_time': fields.datetime('Restore Date Time'), # 
   
            }
    
    _defaults = {
                 'partnerAcknowledgeStatusCd':'ACKNOWLEDGED',
    }
   
project_workorder()
 
class ir_attachement(osv.osv):
    
    def create(self, cr, uid, vals, context=None, check=True):
        
        if 'issue_id' in vals:
            vals['attachment_soruce'] = 'Issue'
            vals['res_model'] = 'project.issue'
            vals['res_id'] = vals['issue_id']
        result = super(ir_attachement, self).create(cr, uid, vals, context)
        return result
  
    def empid(self, cr, uid, ids,a, context=None, check=True):
        result = {}
        for f in self.browse(cr,uid,ids):
            ids = self.pool.get('hr.employee').search(cr,uid,[('user_id','=',f.user_id.id)])
            if ids:
                record = self.pool.get('hr.employee').browse(cr,uid,ids[0])
                result[f.id] = record.id
            _logger.info(" >>>>>>>>>>>>>>>>>> insdie method empid (ir_attachement) empid %s",ids[0])
        return result
    
    def ptremail(self, cr, uid, ids,a, context=None, check=True):
        result = {}
        for f in self.browse(cr,uid,ids):
            ids = self.pool.get('res.partner').search(cr,uid,[('id','=',f.contact.id),('parent_id','=',f.partner_id.id)])
            if ids:
                record = self.pool.get('res.partner').browse(cr,uid,ids[0])
                if record.email:
                    email = record.email
                else:
                    email = ''
                result[f.id] = str(email)
        return result
    
    def ptrphone(self, cr, uid, ids,a, context=None, check=True):
        result = {}
        for f in self.browse(cr,uid,ids):
            ids = self.pool.get('res.partner').search(cr,uid,[('id','=',f.contact.id),('parent_id','=',f.partner_id.id)])
            if ids:
                record = self.pool.get('res.partner').browse(cr,uid,ids[0])
                if record.phone:
                    phone = record.phone
                else:
                    phone = ''
                result[f.id] = str(phone)
        return result
    
    def ptrmobile(self, cr, uid, ids,a, context=None, check=True):
        result = {}
        for f in self.browse(cr,uid,ids):
            ids = self.pool.get('res.partner').search(cr,uid,[('id','=',f.contact.id),('parent_id','=',f.partner_id.id)])
            if ids:
                record = self.pool.get('res.partner').browse(cr,uid,ids[0])
                if record.mobile:
                    mobile = record.mobile
                else:
                    mobile = ''
                result[f.id] = str(mobile)
        return result
    
    def onchange_workorder(self, cr, uid, ids, value):
        res =  {}
        if value =='Issue':
                res = {'domain': {'issue_id': [('issue_cate', '=','Projects')]}}
        return res
    
    _name = "ir.attachment"
    _inherit = 'ir.attachment'
    _description = "adding more fields"
    _columns = {
        'empid':fields.function(empid, store=True,  method=True, string='employee_id',type='many2one',relation='hr.employee'),
       # 'workorder':fields.selection([('Work_order','Work Order'), ('Issue','Issue'),('Other','Other')],'Source'),
       'attachment_soruce':fields.selection([('Work_order','Work Order'), ('Issue','Issue'),('Other','Other')],'Source'),
        'type': fields.selection( [ ('url','URL'), ('binary','Binary'),('static','Static') ],
                'Type', help="Binary File or URL", required=True, change_default=True),
        'user_email':fields.function(ptremail, method=True, string='Email',type='char'),
        'user_phone': fields.function(ptrphone, method=True, string='Phone',type='char'),
        'user_cellno':fields.function(ptrmobile, method=True, string='Mobile',type='char'),
        'contact': fields.many2one('res.partner', string='Source/Author Name'),
        'issue_id': fields.many2one('project.issue', string='Issue'),
        
            }
    _defaults = {
                 'attachment_soruce':lambda *a:'Work_order',
    }
   
ir_attachement()

class project_material(osv.osv):
    """This object is created for projecdt utility. will work only for pre assembly project, populate data from csv file using import"""
    _name = 'project.material'
    _columns = {
    'name': fields.many2one('project.project', 'Project'),
    'network_id': fields.char('Network', size=64),
    'item': fields.char('Item(H)', size=64),
    'activity_description': fields.char('Activity Description', size=64),
    'plant': fields.float('Plant'),
    'transaction_no': fields.integer('Transaction No.'),
    'mat_desc': fields.char('Matr Desc(W)', size=64),
    'req_quantiity':fields.integer('Required MtQuantity(AL)'),
    'shiping_date': fields.date('Shipping Date(R)'),
    'material_req_date': fields.date('Required MtDate(Q)'),
    'delivery_pa': fields.char('Delivery PA#(BL)', size=64),
    'delivery_date': fields.date('Delivery PA Date(BO)'),
    'pa_gi_doc': fields.char('PA-GI Document(BP)', size=64),
    'gr_doc_pa': fields.char('GR-Document-PA', size=64),
    'gi_date': fields.char('PA GI Date(BQ)', size=64),
    'po_pa': fields.char('PO(P-A)#(BS)', size=64),
    'remarks': fields.char('Remarks', size=64),
    }
    _defaults = {
    }
project_material()
class project_invoice(osv.osv):
    """Project Invoicing Summary"""
    _name = 'project.invoice'
    _columns = {
    'name': fields.many2one('project.project', 'PO/Client Reference No'),
    'invoice_no': fields.integer('Invoice #', size=6),
    'inv_prepared_by':fields.many2one('res.users','Prepared By'),
    'inv_approved_by':fields.many2one('res.users','Approved By'),
    'inv_date': fields.datetime('Date'),
    'inv_amount': fields.float('Amount'),
    'inv_issue_date': fields.datetime('Issue Date'),
    'inv_due_date': fields.datetime('Due Date'),
    'inv_remit_date': fields.datetime('Remit Date'),
    'inv_days': fields.integer('Days'),
    'inv_notes': fields.text('Notes'),
    }
    _defaults = {
    }
project_invoice()

class project_pl_rev_summary(osv.osv):
    """P&L Summary"""
    def computactual(self, cr, uid, ids, context={}, arg=None, obj=None):
        result = {}
        for f in self.browse(cr, uid, ids):
            sql="""select  COALESCE(sum(inv_amount),0) from project_invoice where name="""+str(f.name.id)
            cr.execute(sql)
            res=cr.fetchone()
            result[f.id] = float(res[0])
        return result
     
    def computdiff(self, cr, uid, ids, context={}, arg=None, obj=None):
        result = {}
        for f in self.browse(cr, uid, ids):
            result[f.id] = f.pl_actual - f.pl_target
        return result
    
    def computper(self, cr, uid, ids, context={}, arg=None, obj=None):
        result = {}
        for f in self.browse(cr, uid, ids):
            target = f.pl_target
            if target > 0:
                 result[f.id] = (f.pl_difference/f.pl_target)*100
            else:
                 result[f.id] = 0
        return result
    _name = 'project.pl.rev.summary'
    _columns = {
    'name': fields.many2one('project.project', 'Project ID'),
    'pl_summary': fields.char('P&L Summary', size=64),
    'pl_start_date':fields.related('name','date_start',type='datetime',  string='Start Date'), 
    'pl_end_date':fields.related('name','date_close',type='date',  string='End Date'),
    'pl_due_date': fields.related('name','date',type='datetime',  string='Due Date'), 
    'pl_target': fields.float('Target'),
    'pl_actual': fields.function(computactual, method=True, string='Actual',type='float'),
    'pl_difference': fields.function(computdiff, method=True, string='Dirrerence',type='float'),
    'pl_percentage': fields.function(computper, method=True, string='%',type='float'),
    'pl_metric': fields.float('Metric'),
    'pl_rate': fields.float('Rate'),
    }
    _defaults = {
    }
project_pl_rev_summary()

class project_pl_cost_summary(osv.osv):
    """P&L Summary"""
    def computtrgt(self, cr, uid, ids, context={}, arg=None, obj=None):
        result = {}
        for f in self.browse(cr, uid, ids):
            _logger.info("PL Cost target, project id >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>: %s",f.id)
            idss =  self.pool.get('project.labour.hours.expended').search(cr, uid, [('name','=',f.name.id)])
            lt = 0
            if idss:
                 rec = self.pool.get('project.labour.hours.expended').browse(cr,uid,idss)
                 for lth in rec:
                     lt = lt + lth.labour_target
            lh_extended = lt
            
#             sql2="""select  COALESCE(sum(materials_target),0) from project_materials_consumed where name="""+str(f.name.id)
#             cr.execute(sql2)
#             mt_consumed =cr.fetchone()
#            The above query was changed to orm method calling due to changes in the same tbl on date 7 june 2017
            
            matidss =  self.pool.get('project.materials.consumed').search(cr, uid, [('name','=',f.name.id)])
            mtc = 0
            if matidss:
                 matrec = self.pool.get('project.materials.consumed').browse(cr,uid,matidss)
                 for matc in matrec:
                     mtc = mtc + matc.materials_target
            
#             sql3="""select  COALESCE(sum(expenses_target),0) from project_expenses_incurred where name="""+str(f.name.id)
#             cr.execute(sql3)
#             exp_occur =cr.fetchone()
            
            expidss =  self.pool.get('project.expenses.incurred').search(cr, uid, [('name','=',f.name.id)])
            exp_occur = 0
            if expidss:
                 exprec = self.pool.get('project.expenses.incurred').browse(cr,uid,expidss)
                 for exp in exprec:
                     exp_occur = exp_occur + exp.expenses_target
            
            sql4="""select  COALESCE(sum(overhead_target),0) from project_overhead_allocations where name="""+str(f.name.id)
            cr.execute(sql4)
            overhd =cr.fetchone()
            
            
            result[f.id] = float(lh_extended) + float(mtc) + float(exp_occur) + float(overhd[0])
            
            
        return result
    
    def computactual(self, cr, uid, ids, context={}, arg=None, obj=None):
        result = {}
        for f in self.browse(cr, uid, ids):
            
            idss =  self.pool.get('project.labour.hours.expended').search(cr, uid, [('name','=',f.name.id)])
            la = 0
            if idss:
                 rec = self.pool.get('project.labour.hours.expended').browse(cr,uid,idss)
                 for lah in rec:
                     lt = la + lah.labour_actual
            lh_extended = la
            
#             sql1="""select  COALESCE(sum(labour_actual),0) from project_labour_hours_expended where name="""+str(f.name.id)
#             cr.execute(sql1)
#             lh_extended =cr.fetchone()
#             _logger.info("PL Cost computactual, lh_extended >: %s",lh_extended[0])
            
            idss2 =  self.pool.get('project.materials.consumed').search(cr, uid, [('name','=',f.name.id)])
            matc = 0
            if idss2:
                 rec2 = self.pool.get('project.materials.consumed').browse(cr,uid,idss2)
                 for mat in rec2:
                     matc = matc + mat.materials_actual
            mt_consumed = matc
            
#             sql2="""select  COALESCE(sum(materials_actual),0) from project_materials_consumed where name="""+str(f.name.id)
#             cr.execute(sql2)
#             mt_consumed =cr.fetchone()
#             _logger.info("PL Cost computactual > labour_actual > : %s",mt_consumed[0])
            
            sql3="""select  COALESCE(sum(expenses_actual),0) from project_expenses_incurred where name="""+str(f.name.id)
            cr.execute(sql3)
            exp_occur =cr.fetchone()
            _logger.info("PL Cost computactual > expenses_actual >: %s",exp_occur[0])
            
            
            sql4="""select  COALESCE(sum(overhead_actual),0) from project_overhead_allocations where name="""+str(f.name.id)
            cr.execute(sql4)
            overhd =cr.fetchone()
            _logger.info("PL Cost computactual > overhd > : %s",overhd[0])
            
            result[f.id] = float(lh_extended) + float(mt_consumed) + float(exp_occur[0]) +float(overhd[0])
        return result
            
    
    
    
    def comput_start_date(self, cr, uid, ids,  field_names, arg=None, obj=None):
        result = {}
        for f in self.browse(cr, uid, ids):
            result[f.id] = {}
            if type(field_names) is not list:
                field_names = [field_names]
            _logger.info("*<(-_-)>********* inside caluclating project total cost, start date for project_id== : %s",f.name.id)
            start_date = None
            greater_date = None
            sql="""select  date_confirmed from daily_material_reconciliation where project="""+str(f.name.id)
            cr.execute(sql)
            res=cr.fetchall()
            _logger.info("************************ inside matric field objects res1== : %s",res)
            for mat in res:
                _logger.info("************************ inside matric field objects found conrimation date from material22222== : %s",start_date)
                this = datetime.strptime(mat[0], '%Y-%m-%d')
                
                _logger.info("************************ inside matric field objects after convetring to date time3333== : %s",this)
                start_date = this
                greater_date = this
            
            sql2="""select  date_valid from hr_expense_expense where project_id="""+str(f.name.id)
            cr.execute(sql2)
            res=cr.fetchall()
            _logger.info("************************ inside matric field objects res2== : %s",res)
            for exp in res:
                _logger.info("************************ inside matric field objects found conrimation date from expense table 44444== : %s",start_date)
                this = datetime.strptime(exp[0], '%Y-%m-%d %H:%M:%S')
                _logger.info("found expense verification date= : %s",this)
                if start_date: 
                    if this < start_date:
                        start_date = this
                else:
                    start_date = this
                
                _logger.info("after setting expense date in start_date= : %s",start_date)
                if greater_date:
                    if this > greater_date:
                        greater_date = this
                else:
                    greater_date = this
                _logger.info("after setting expense end date(greater) in start_date= : %s",greater_date)
            sql3="""select project_task_work.date from project_task_work 
                     inner join project_task on project_task.id = project_task_work.task_id
                     where hours >0 
                     and project_task.project_id="""+str(f.name.id)
            cr.execute(sql3)
            res=cr.fetchall()
            _logger.info("************************ found work in query== : %s",res)
            for work in res:
                _logger.info("************************ calculating work== : %s",start_date)
                this = datetime.strptime(work[0], '%Y-%m-%d %H:%M:%S')
                if start_date:
                    if  this < start_date:
                        start_date = this
                else:
                    start_date = this
                
                if greater_date: 
                    if this > greater_date:
                        greater_date = this
                else:
                    greater_date = this
            if 'pl_start_date' in field_names:
                    result[f.id]['pl_start_date'] = start_date
            if 'pl_end_date' in field_names:
                    result[f.id]['pl_end_date'] = greater_date
            
            _logger.info("Yahoooooooooooooo, inside cost calculation , start date result== : %s",result)
        return result 
     
    def computdiff(self, cr, uid, ids, context={}, arg=None, obj=None):
        result = {}
        for f in self.browse(cr, uid, ids):
            result[f.id] = f.pl_actual - f.pl_target
        return result
    
    def onchange_costtarget(self, cr, uid, target,project_id):
        vals = {}
        if type=='Pre-Assembly':
            displayid = self.pool.get('project.pl.display.summary').search(cr, uid, [('pl_summary','=''TOTAL PROJECT COSTS'),('name','=',project_id)])
            if displayid:
                self.pool.get('project.pl.display.summary').write(cr,uid,displayid[0],{'pl_target':target})
            return { 'value':vals  }
        else:
            return {} 
    
    def computper(self, cr, uid, ids, context={}, arg=None, obj=None):
        result = {}
        for f in self.browse(cr, uid, ids):
            target = f.pl_target
            if target > 0:
                 result[f.id] = (f.pl_difference/f.pl_target)*100
            else:
                 result[f.id] = 0
        return result
    _name = 'project.pl.cost.summary'
    _columns = {
    'name': fields.many2one('project.project', 'Project ID'),
    'pl_summary': fields.char('P&L Summary', size=64),
    'pl_start_date':fields.function(comput_start_date,multi = 'calc_date', method=True, string='Start Date',type='date'),
    'pl_end_date':fields.function(comput_start_date,multi = 'calc_date', method=True, string='End Date',type='date'),
    'pl_due_date': fields.related('name','date_close',type='datetime',  string='Due Date'), 
    'pl_actual': fields.function(computactual, method=True, string='Actual',type='float'),
    'pl_target': fields.function(computtrgt, method=True, string='Target',type='float'),
    'pl_difference': fields.function(computdiff, method=True, string='Dirrerence',type='float'),
    'pl_percentage': fields.function(computper, method=True, string='%',type='float'),
    'pl_metric': fields.float('Metric'),
    'pl_rate': fields.float('Rate'),

    }
    _defaults = {
    }
project_pl_cost_summary()

###################
class project_net_margin(osv.osv):
    """Project Net Margin"""
    def computtrgt(self, cr, uid, ids, context={}, arg=None, obj=None):
        result = {}
        for f in self.browse(cr, uid, ids):
            target_costrec = 0
            target_revrec = 0
            target_rev = self.pool.get('project.pl.rev.summary').search(cr, uid, [('pl_summary','=','TOTAL PROJECT REVENUES'),('name','=',f.project_id.id)])
            if target_rev:
                target_revrec = self.pool.get('project.pl.rev.summary').browse(cr,uid,target_rev[0]).pl_target
            
            target_cost = self.pool.get('project.pl.cost.summary').search(cr, uid, [('pl_summary','=','TOTAL PROJECT COSTS'),('name','=',f.project_id.id)])
            if target_rev:
                target_costrec = self.pool.get('project.pl.cost.summary').browse(cr,uid,target_cost[0]).pl_target
                
            result[f.id] = target_revrec - target_costrec
            
        return result
    
    def computactual(self, cr, uid, ids, context={}, arg=None, obj=None):
        result = {}
        for f in self.browse(cr, uid, ids):
            actual_costrec = 0
            actual_revrec = 0
            target_rev = self.pool.get('project.pl.rev.summary').search(cr, uid, [('pl_summary','=','TOTAL PROJECT REVENUES'),('name','=',f.project_id.id)])
            if target_rev:
                actual_revrec = self.pool.get('project.pl.rev.summary').browse(cr,uid,target_rev[0]).pl_target
            
            target_cost = self.pool.get('project.pl.cost.summary').search(cr, uid, [('pl_summary','=','TOTAL PROJECT COSTS'),('name','=',f.project_id.id)])
            if target_rev:
                actual_costrec = self.pool.get('project.pl.cost.summary').browse(cr,uid,target_cost[0]).pl_target
                
            result[f.id] = actual_revrec - actual_costrec
        return result
    
     
    def computdiff(self, cr, uid, ids, context={}, arg=None, obj=None):
        result = {}
        for f in self.browse(cr, uid, ids):
            result[f.id] = f.pl_actual - f.pl_target
        return result
    
    def computper(self, cr, uid, ids, context={}, arg=None, obj=None):
        result = {}
        for f in self.browse(cr, uid, ids):
            target = f.pl_target
            if target > 0:
                 result[f.id] = (f.pl_difference/f.pl_target)*100
            else:
                 result[f.id] = 0
        return result
    _name = 'project.net.margin'
    _columns = {
    'name': fields.char('Name'),
    'project_id': fields.many2one('project.project', 'Project ID'),
    'pl_target': fields.function(computtrgt, method=True, string='Target',type='float'),
    'pl_actual': fields.function(computactual, method=True, string='Actual',type='float'),
    'pl_difference': fields.function(computdiff, method=True, string='Dirrerence',type='float'),
    'pl_percentage': fields.function(computper, method=True, string='%',type='float'),
    'pl_metric': fields.float('Metric'),
    'pl_rate': fields.float('Rate'),

    }
    _defaults = {
    }
project_net_margin()


#######
class project_pl_display_summary(osv.osv):
    """project_pl_display_summary"""
    def comput_start_date(self, cr, uid, ids, context={}, arg=None, obj=None):
        result = {}
        for f in self.browse(cr, uid, ids):
            start_date = None
            if f.pl_summary == 'TOTAL PROJECT REVENUES':
                _logger.info("==============insdie display TOTAL PROJECT REVENUES project id is   : %s",f.name.id)
                controller = self.pool.get('project.pl.rev.summary')
                domain = 'TOTAL PROJECT REVENUES'
                ids = controller.search(cr, uid, [('name','=',f.name.id),('pl_summary','=',domain)])
                if ids:
                    start_date = self.pool.get('project.pl.rev.summary').browse(cr,uid,ids[0]).pl_start_date
            elif f.pl_summary == 'TOTAL PROJECT COSTS':
                _logger.info("==============insdie display TOTAL PROJECT COSTS f.name.id : %s",f.name.id)
                controller = self.pool.get('project.pl.cost.summary')
                domain = 'TOTAL PROJECT COSTS'
                ids = controller.search(cr, uid, [('name','=',f.name.id),('pl_summary','=',domain)])
                if ids:
                    start_date = self.pool.get('project.pl.cost.summary').browse(cr,uid,ids[0]).pl_start_date
                    _logger.info("==============insdie display object start date is  : %s",start_date)
            
            elif f.pl_summary == 'NET PROJECT MARGIN':
                result[f.id]  = ' '
                return result
            if start_date:
                result[f.id] =   datetime.strftime(dateutil.parser.parse(start_date).date(), "%d-%b-%y")
            else:
                result[f.id] = ' '
                
                
        return result
    
    def comput_end_date(self, cr, uid, ids, context={}, arg=None, obj=None):
        result = {}
        for f in self.browse(cr, uid, ids):
            end_date = None
            if f.pl_summary == 'TOTAL PROJECT REVENUES':
                _logger.info("Searching ...............end date (Project Revnue > Display table):prj_id %s",f.name.id)
                _logger.info("display table id (Revune) %s",f.id)
                controller = self.pool.get('project.pl.rev.summary')
                domain = 'TOTAL PROJECT REVENUES'
                ids = controller.search(cr, uid, [('name','=',f.name.id),('pl_summary','=',domain)])
                if ids:
                    end_date = self.pool.get('project.pl.rev.summary').browse(cr,uid,ids[0]).pl_end_date
                    _logger.info("Found.................... end date (Project Revnue > Display table):end_date %s",end_date)
                    _logger.info("display table id (Revune) %s",f.id)
                else:
                    end_date = ''
            elif f.pl_summary == 'TOTAL PROJECT COSTS':
                _logger.info("Searching ...............end date (Project Cost > Display table):prj_id %s",f.name.id)
                _logger.info("display table id (Cost) %s",f.id)
                controller = self.pool.get('project.pl.cost.summary')
                domain = 'TOTAL PROJECT COSTS'
                ids = controller.search(cr, uid, [('name','=',f.name.id),('pl_summary','=',domain)])
                if ids:
                    end_date = self.pool.get('project.pl.cost.summary').browse(cr,uid,ids[0]).pl_end_date
                    _logger.info("Found.................... end date (Project Cost > Display table):end_date %s",end_date)
                    _logger.info("display table id (cost) %s",f.id)
            elif f.pl_summary == 'NET PROJECT MARGIN':
                result[f.id]  = ' '
                return result
            _logger.info("==============showing end date in summar final : %s",end_date)
            if end_date:
                result[f.id] = datetime.strftime(dateutil.parser.parse(end_date).date(), "%d-%b-%y")
            else:
                result[f.id] = str('')
                
        return result
    
    def comput_due_date(self, cr, uid, ids, context={}, arg=None, obj=None):
        result = {}
        for f in self.browse(cr, uid, ids):
            end_date = None
            if f.pl_summary == 'TOTAL PROJECT REVENUES':
                _logger.info("==============insdie display TOTAL PROJECT REVENUES project id is   : %s",f.name.id)
                controller = self.pool.get('project.pl.rev.summary')
                domain = 'TOTAL PROJECT REVENUES'
                ids = controller.search(cr, uid, [('name','=',f.name.id),('pl_summary','=',domain)])
                if ids:
                    end_date = self.pool.get('project.pl.rev.summary').browse(cr,uid,ids[0]).pl_due_date
            elif f.pl_summary == 'TOTAL PROJECT COSTS':
                _logger.info("==============insdie display TOTAL PROJECT COSTS f.name.id : %s",f.name.id)
                controller = self.pool.get('project.pl.cost.summary')
                domain = 'TOTAL PROJECT COSTS'
                ids = controller.search(cr, uid, [('name','=',f.name.id),('pl_summary','=',domain)])
                if ids:
                    end_date = self.pool.get('project.pl.cost.summary').browse(cr,uid,ids[0]).pl_due_date
                _logger.info("==============insdie display object end_date date is  : %s",end_date)
            elif f.pl_summary == 'NET PROJECT MARGIN':
                result[f.id]  =  ''
                return result
            if end_date:
                result[f.id] = datetime.strftime(dateutil.parser.parse(end_date).date(), "%d-%b-%y")
            else:
                result[f.id] = end_date
                
        return result
    
    def computtrgt(self, cr, uid, ids, context={}, arg=None, obj=None):
        result = {}
        for f in self.browse(cr, uid, ids):
            trgt = 0.0
            if f.pl_summary == 'TOTAL PROJECT REVENUES':
                _logger.info("==============insdie display TOTAL PROJECT REVENUES project id is   : %s",f.name.id)
                controller = self.pool.get('project.pl.rev.summary')
                domain = 'TOTAL PROJECT REVENUES'
                ids = controller.search(cr, uid, [('name','=',f.name.id),('pl_summary','=',domain)])
                if ids:
                    trgt = self.pool.get('project.pl.rev.summary').browse(cr,uid,ids[0]).pl_target
            elif f.pl_summary == 'TOTAL PROJECT COSTS':
                _logger.info("==============insdie display TOTAL PROJECT COSTS f.name.id : %s",f.name.id)
                controller = self.pool.get('project.pl.cost.summary')
                domain = 'TOTAL PROJECT COSTS'
                ids = controller.search(cr, uid, [('name','=',f.name.id),('pl_summary','=',domain)])
                if ids:
                    trgt = self.pool.get('project.pl.cost.summary').browse(cr,uid,ids[0]).pl_target
            _logger.info("==============insdie display object trgt is  : %s",trgt)
            result[f.id] = float(trgt)
                
        return result
    
    def computactual(self, cr, uid, ids, context={}, arg=None, obj=None):
        result = {}
        for f in self.browse(cr, uid, ids):
            actual = 0.0
            if f.pl_summary == 'TOTAL PROJECT REVENUES':
                _logger.info("==============insdie display TOTAL PROJECT REVENUES project id is   : %s",f.name.id)
                controller = self.pool.get('project.pl.rev.summary')
                domain = 'TOTAL PROJECT REVENUES'
                ids = controller.search(cr, uid, [('name','=',f.name.id),('pl_summary','=',domain)])
                if ids:
                    actual = self.pool.get('project.pl.rev.summary').browse(cr,uid,ids[0]).pl_actual
            elif f.pl_summary == 'TOTAL PROJECT COSTS':
                _logger.info("==============insdie display TOTAL PROJECT COSTS f.name.id : %s",f.name.id)
                controller = self.pool.get('project.pl.cost.summary')
                domain = 'TOTAL PROJECT COSTS'
                ids = controller.search(cr, uid, [('name','=',f.name.id),('pl_summary','=',domain)])
                if ids:
                    actual = self.pool.get('project.pl.cost.summary').browse(cr,uid,ids[0]).pl_actual
            _logger.info("==============insdie display object trgt is  : %s",actual)
            result[f.id] = float(actual)
                
        return result
    
    def write(self, cr, uid, ids, vals, context=None, check=True, update_check=True):
        result = False
        for f in self.browse(cr,uid,ids):
            if f.pl_summary =='TOTAL PROJECT COSTS' or f.pl_summary =='NET PROJECT MARGIN':
                vals['pl_target'] = f.pl_target
            elif f.pl_summary =='TOTAL PROJECT REVENUES':
                target_rev = self.pool.get('project.pl.rev.summary').search(cr, uid, [('pl_summary','=','TOTAL PROJECT REVENUES'),('name','=',f.name.id)])
                if target_rev:
                    self.pool.get('project.pl.rev.summary').write(cr,uid,target_rev[0],{'pl_target':vals['pl_target']})
                result = super(osv.osv, self).write(cr, uid, ids, vals, context)
            # create transactional logs for work
        return result
    
    def computdiff(self, cr, uid, ids, context={}, arg=None, obj=None):
        result = {}
        for f in self.browse(cr, uid, ids):
            if f.pl_summary =='TOTAL PROJECT REVENUES':
                target_rev = self.pool.get('project.pl.rev.summary').search(cr, uid, [('pl_summary','=','TOTAL PROJECT REVENUES'),('name','=',f.name.id)])
                if target_rev:
                    target_revrec = self.pool.get('project.pl.rev.summary').browse(cr,uid,target_rev[0])
                    result[f.id] = target_revrec.pl_difference
            elif  f.pl_summary =='TOTAL PROJECT COSTS':
                target_cost = self.pool.get('project.pl.cost.summary').search(cr, uid, [('pl_summary','=','TOTAL PROJECT COSTS'),('name','=',f.name.id)])
                if target_cost:
                    target_costrec = self.pool.get('project.pl.cost.summary').browse(cr,uid,target_cost[0])
                    result[f.id] = target_costrec.pl_difference
            elif  f.pl_summary =='NET PROJECT MARGIN':
                target_pm = self.pool.get('project.net.margin').search(cr, uid, [('name','=','NET PROJECT MARGIN'),('project_id','=',f.name.id)])
                if target_pm:
                    target_costrec = self.pool.get('project.net.margin').browse(cr,uid,target_pm[0])
                    result[f.id] = target_costrec.pl_difference
        return result
    def computper(self, cr, uid, ids, context={}, arg=None, obj=None):
        result = {}
        for f in self.browse(cr, uid, ids):
            if f.pl_summary =='TOTAL PROJECT REVENUES':
                target_rev = self.pool.get('project.pl.rev.summary').search(cr, uid, [('pl_summary','=','TOTAL PROJECT REVENUES'),('name','=',f.name.id)])
                if target_rev:
                    target_revrec = self.pool.get('project.pl.rev.summary').browse(cr,uid,target_rev[0])
                    result[f.id] = target_revrec.pl_percentage
            elif  f.pl_summary =='TOTAL PROJECT COSTS':
                target_cost = self.pool.get('project.pl.cost.summary').search(cr, uid, [('pl_summary','=','TOTAL PROJECT COSTS'),('name','=',f.name.id)])
                if target_cost:
                    target_costrec = self.pool.get('project.pl.cost.summary').browse(cr,uid,target_cost[0])
                    result[f.id] = target_costrec.pl_percentage
            elif  f.pl_summary =='NET PROJECT MARGIN':
                target_pm = self.pool.get('project.net.margin').search(cr, uid, [('name','=','NET PROJECT MARGIN'),('project_id','=',f.name.id)])
                if target_pm:
                    target_costrec = self.pool.get('project.net.margin').browse(cr,uid,target_pm[0])
                    result[f.id] = target_costrec.pl_percentage
        return result
    
    _name = 'project.pl.display.summary'
    _columns = {
    'name': fields.many2one('project.project', 'Project ID'),
    'pl_summary': fields.char('P&L Summary', size=64),
    'pl_start_date':fields.function(comput_start_date, method=True, string='Start Date',type='char',size=15),
    'pl_end_date':fields.function(comput_end_date, method=True, string='End Date',type='char',size=15),
    'pl_due_date': fields.function(comput_due_date, method=True, string='Due Date',type='char',size=15), 
    'pl_target': fields.float('Target'),
    'pl_actual': fields.function(computactual, method=True, string='Actual',type='char',size=15), 
    'pl_difference': fields.function(computdiff, method=True, string='Difference',type='float',), 
    'pl_percentage': fields.function(computper, method=True, string='%',type='float',),
#    'pl_percentage': fields.float('Target'),
    'pl_metric': fields.float('Metric'),
    'pl_rate': fields.float('Rate'),
    }
    _defaults = {
                 'target':computtrgt,
                 
    }
project_pl_display_summary()


class project_labour_hours_expended(osv.osv):
    """Labour Hours Expended"""
   
    def leadtech(self, cr, uid, ids, context={}, arg=None, obj=None):
        result = {}
        for f in self.browse(cr, uid, ids):
            user_id = f.labour_hours_expended.user_id.id
            ids = self.pool.get('hr.employee').search(cr,uid,[('user_id','=',user_id)])
            if ids:
                record = self.pool.get('hr.employee').browse(cr,uid,ids[0])
            result[f.id] = record.emp_srno_calc
        return result
    
    def lbrtrgt(self, cr, uid, ids, field_names, arg=None, obj=None):
        
        result = {}
        for f in self.browse(cr, uid, ids):
            result[f.id] = {}
            if type(field_names) is not list:
                field_names = [field_names]
            for key_str in field_names:
                result[f.id][key_str] = 0.0
            
            sql="""select  COALESCE(sum(hours),0) from project_task_work  where task_id="""+str(f.labour_hours_expended.id)
            cr.execute(sql)
            timespent=cr.fetchone()
            
            if 'labour_target' in field_names:
                    result[f.id]['labour_target'] = float(f.labour_hours_expended.task_planned_hours) * f.name.met_average_tech_labour_rate
            if 'labour_actual' in field_names:
                result[f.id]['labour_actual'] = timespent[0]*f.name.met_average_tech_labour_rate
            if 'labour_total_hours' in field_names:
                _logger.info("Computing Total hours on : labour hours:: : %s",timespent[0])
                result[f.id]['labour_total_hours'] = float(timespent[0])
            if 'labour_rate' in field_names:
                timespent = timespent[0]
                if timespent== 0:
                    timespent = 1
                _logger.info("Computing Total hours on : labour hours:: : %s",timespent)
                result[f.id]['labour_rate'] = (float(f.labour_hours_expended.task_planned_hours) / float(timespent))*100
            #raise osv.except_osv((f.labour_hours_expen*ded.planned_hours),(f.name.met_average_tech_labour_rate))
        return result
    
    def cmptdiff(self, cr, uid, ids,fields_names,  arg=None, obj=None):
        result = {}
        for f in self.browse(cr, uid, ids):
            _logger.info("Computing Difference in object: labour hours:: : %s",f.labour_target - f.labour_actual)
            result[f.id] = float(f.labour_target - f.labour_actual)
        return result
    
    def cmptdper(self, cr, uid, ids, fields_names, arg=None, obj=None):
        result = {}
        for f in self.browse(cr, uid, ids):
            budgt = f.labour_target
            if budgt <1:
                budgt = 1
            _logger.info("Computing Labour Percentage object: labour hours:: : %s",(f.labour_difference/budgt)*100)    
            result[f.id] = float((f.labour_difference/budgt)*100)
        return result
    
    def comptdates(self, cr, uid, ids,field_names, context=None, check=True):
        """ """
        result = {}
        for f in self.browse(cr, uid, ids, context=context):
            result[f.id] = {}
            if type(field_names) is not list:
                field_names = [field_names]
            for key_str in field_names:
                result[f.id][key_str] = ''
            
            if 'labour_start_date' in field_names:
                start_date = False
                start_date = f.name.date_start
                if start_date:
                    result[f.id]['labour_start_date'] = datetime.strftime(dateutil.parser.parse(start_date).date(), "%d-%b-%y")
                else:
                    result[f.id]['labour_start_date'] = ''
                
            if 'labour_end_date' in field_names:
                end_date = False
                end_date = f.labour_hours_expended.date_deadline
                if end_date:
                    result[f.id]['labour_end_date'] = datetime.strftime(dateutil.parser.parse(end_date).date(), "%d-%b-%y")
                else:
                    result[f.id]['labour_end_date'] = ''
                
               
        _logger.info("==============End of Method:calculates start and end dates for object labor hours extended================= : %s",result)
        return result
    
    _name = 'project.labour.hours.expended'
    _columns = {
    'name': fields.many2one('project.project', 'Project ID'),
    'labour_hours_expended':fields.many2one('project.task', 'Labour hours expended'),#text for column labour hours extended is acutally task name
    #start date is actually start date of porject task, but that is made hide by client, so we are keeping it related to project start date
    'labour_start_date':fields.function(comptdates,multi='dates', method=True, string='Start Date',type='char',size=15),
    'labour_end_date':fields.function(comptdates,multi='dates', method=True, string='End Date',type='char',size=15),
    'labour_lead_tech':fields.function(leadtech, method=True, string='Lead Tech',type='char'),
    'labour_target': fields.function(lbrtrgt,multi='hours', method=True, string='Target',type='float'),#if this fields didnot updated store value on change in intitially planned hours and met_average_tech_labour_rate (a column of project table), then we should modify its store=True property to soemting more special to be updated anyyime when vuels used in function are changed
    'labour_actual':  fields.function(lbrtrgt,multi='hours', method=True, string='Budget',type='float'),
    'labour_difference':  fields.function(cmptdiff,method=True, string='Difference',type='float'),
    'labour_percentage':  fields.function(cmptdper, method=True, string='%',type='float'),
    'labour_total_hours':  fields.function(lbrtrgt,multi='hours', method=True, string='Total Hours',type='float'),
    'labour_rate': fields.function(lbrtrgt,multi='hours', method=True, string='Rate',type='float'),
    }
    _defaults = {
    }


project_labour_hours_expended()


class project_materials_consumed(osv.osv):
    """Materials Consumed"""

    def getval(self, cr, uid, ids, field_names, context=None, check=True):
        """ """
        result = {}
        for f in self.browse(cr, uid, ids, context=context):
            result[f.id] = {}
            if type(field_names) is not list:
                field_names = [field_names]
            for key_str in field_names:
                result[f.id][key_str] = ''

            if 'materials_consumed' in field_names:

                mt_ids = self.pool.get('material.reconcile.lines').search(cr, uid, [('task_id', '=', task_id)])
                if start_date:
                    result[f.id]['materials_consumed'] = datetime.strftime(dateutil.parser.parse(start_date).date(),
                                                                           "%d-%b-%y")
                else:
                    result[f.id]['labour_start_date'] = ''

            if 'labour_end_date' in field_names:
                end_date = False
                end_date = f.labour_hours_expended.date_deadline
                if end_date:
                    result[f.id]['labour_end_date'] = datetime.strftime(dateutil.parser.parse(end_date).date(),
                                                                        "%d-%b-%y")
                else:
                    result[f.id]['labour_end_date'] = ''

        _logger.info(
            "==============End of Method:calculates start and end dates for object labor hours extended================= : %s",
            result)
        return result
    
    
    def compute_vals(self, cr, uid, ids,field_names, context=None, check=True):
        """ """
        result = {}
        for f in self.browse(cr, uid, ids, context=context):
            result[f.id] = {}
            if type(field_names) is not list:
                field_names = [field_names]
            for key_str in field_names:
                result[f.id][key_str] = 0
            
            if 'materials_target' in field_names:
                result[f.id]['materials_target'] = f.related_material_id.dispatch_qty * f.related_material_id.product.list_price or 1
            if 'materials_actual' in field_names:
                result[f.id]['materials_actual'] = (f.materials_target - 10)*(f.related_material_id.product.list_price)
            if 'materials_difference' in field_names:
                result[f.id]['materials_difference'] = f.materials_target - f.materials_actual
            if 'materials_percentage' in field_names:
                if f.materials_target >0:
                    
                    budget = f.materials_target
                else:
                    budget = 1
                result[f.id]['materials_percentage'] = (f.materials_difference / budget)*100
            
            if 'materials_rate' in field_names:
#                 sql="""select  COALESCE(sum(materials_actual),0) from project_materials_consumed where name="""+str(f.name.id)
#                 cr.execute(sql)
#                 res=cr.fetchone()
#                 allactual = float(res[0])
                matc = 0
                idss2 =  self.pool.get('project.materials.consumed').search(cr, uid, [('name','=',f.name.id)])
                matc = 0
                if idss2:
                     rec2 = self.pool.get('project.materials.consumed').browse(cr,uid,idss2)
                     for mat in rec2:
                         matc = matc + mat.materials_actual
                
                if matc >0:
                    net = f.materials_actual/matc
                else:
                    net = f.materials_actual/1
                result[f.id]['materials_percentage'] = net
        _logger.info("==============End of Method:calculated product cost price * qtry",result)
        return result
    def meterial_consumed(self, cr, uid,ids, field_name, arg, context=None):
        result = {}
        for f in self.browse(cr, uid, ids):
            if f.related_expence_id:
                result[f.id] = f.related_expence_id.expenseline_id.expense_id.name
            if f.related_material_id:
                result[f.id] = f.related_material_id.name
        return result

    def dispatch_date(self, cr, uid,ids, field_name, arg, context=None):
        result = {}
        for f in self.browse(cr, uid, ids):
            if f.related_expence_id:
                result[f.id] = f.related_expence_id.expenseline_id.expense_id.date
            if f.related_material_id:
                result[f.id] = f.related_material_id.date_dispatched
        return result
    def confirm_date(self, cr, uid,ids, field_name, arg, context=None):
        result = {}
        for f in self.browse(cr, uid, ids):
            if f.related_expence_id:
                result[f.id] = f.related_expence_id.expenseline_id.expense_id.date
            if f.related_material_id:
                result[f.id] = f.related_material_id.dispatch_id.date_confirmed
        return result
    def get_source(self, cr, uid,ids, field_name, arg, context=None):
        result = {}
        for f in self.browse(cr, uid, ids):
            if f.related_expence_id:
                result[f.id] = f.related_expence_id.expenseline_id.expense_id.name
            if f.related_material_id:
                result[f.id] = f.related_material_id.source.name
        return result
    
    #this table is automatically populated when a record is created in table prj_billing_materials line 4000, link with the table on column related_material_id
    _name = 'project.materials.consumed'
    _columns = {
    'name': fields.many2one('project.project', 'Project ID'),
    'materials_consumed':fields.function(meterial_consumed ,method = True, type='char',  string='Material Consumed', readonly=True),
    'materials_required':fields.function(dispatch_date ,method = True,type='datetime',  string='Required', readonly=True),
    'materials_delivered':fields.function(confirm_date ,method = True,type='datetime',  string='Delivered', readonly=True),
    'materials_source': fields.function(get_source ,method = True, type='char',  string='Source', readonly=True),
    'materials_target':fields.function(compute_vals,multi='target', method=True, string='Target',type='float'),
    'materials_actual':fields.function(compute_vals,multi='target1', method=True, string='Actual',type='float'),
    'materials_difference': fields.function(compute_vals,multi='target2', method=True, string='Difference',type='float'),
    'materials_percentage': fields.function(compute_vals,multi='target3', method=True, string='%',type='float'),
    'materials_metric':fields.function(compute_vals,multi='target2', method=True, string='Metric',type='float'),
    'materials_rate': fields.function(compute_vals,multi='target2', method=True, string='Rate',type='float'),
    'related_material_id':fields.many2one('prj.billing.materials','Related Material Table'),
    'related_expence_id':fields.many2one('prj.billing.expenseline','Related Expanse Table'),
    'hidden_source' : fields.char(string='Type'),
    }
    _defaults = {
    }
project_materials_consumed()
class project_expenses_incurred(osv.osv):
    """Expenses Incurred"""
    
    def compute_vals(self, cr, uid, ids,field_names, context=None, check=True):
        """ """
        result = {}
        for f in self.browse(cr, uid, ids, context=context):
            result[f.id] = {}
            if type(field_names) is not list:
                field_names = [field_names]
            for key_str in field_names:
                result[f.id][key_str] = 0
            
            if 'expenses_difference' in field_names:
                result[f.id]['materials_target'] = f.expenses_target - f.expenses_actual
            if 'expenses_percentage' in field_names:
                if f.expenses_target >0:
                    
                    budget = f.expenses_target
                else:
                    budget = 1
                result[f.id]['materials_percentage'] = (f.expenses_difference / budget)*100
            if 'expenses_rate' in field_names:
                idss = self.pool.get('project.expenses.incurred').search(cr,uid,[('name','=',f.name.id)])
                all_actual = 0
                for line in self.pool.get('project.expenses.incurred').browse(cr, uid, idss):
                    all_actual = all_actual + line.expenses_actual 
                if all_actual > 0:
                    rate = (f.expenses_actual/ all_actual)*100
                else:
                    rate = 1
                result[f.id]['expenses_rate'] = rate
                
        _logger.info("==============Calculated epenses differences, in table project_expenses_incured",result)
        return result

    
    _name = 'project.expenses.incurred'
    _columns = {
    'name': fields.many2one('project.project', 'Project ID'),
    'expenses_incurred': fields.related('related_expense_id','expenseline_id','name',type='char',  string='Expense Incured', readonly=True),
#     'dated_submit':fields.related('related_expense_id','expenseline_id','date',type='datetime',  string='Required'),
    'dated_delivered':fields.related('related_expense_id','date',type='date',  string='Delivered'),
    'expenses_soruce':fields.related('related_expense_id','expenseline_id','name',type='char',  string='Source', readonly=True),
    'expenses_target':fields.related('related_expense_id','net_bill',type='float',  string='Budget', readonly=True),
    'expenses_actual': fields.float('Actual'),
    'expenses_difference': fields.function(compute_vals,multi='target1', method=True, string='Difference',type='float'),
    'expenses_percentage':fields.function(compute_vals,multi='target2', method=True, string='%',type='float'),
    'expenses_metric': fields.float('Metric'),
    'expenses_rate': fields.function(compute_vals,multi='target3', method=True, string='%',type='float'),
    'related_expense_id':fields.many2one('prj.billing.expenseline','Related Material Table')
    }
    _defaults = {
    }
project_expenses_incurred()
class project_overhead_allocations(osv.osv):
    """Expenses Incurred"""
    _name = 'project.overhead.allocations'
    _columns = {
    'name': fields.many2one('project.project', 'Project ID'),
    'overhead_allocations': fields.char('Overhead Allocations', size=64),
    'overhead_smallest':fields.float('Smallest'),
    'overhead_largest':fields.float('Largest'),
    'overhead_average': fields.float('Average'),
    'overhead_target': fields.float('Target'),
    'overhead_actual': fields.float('Actual'),
    'overhead_difference': fields.float('Difference'),
    'overhead_percentage': fields.float('%'),
    'overhead_cost_hour': fields.float('Cost/Hour'),
    'overhead_percentage_of_total': fields.float('% of Total'),
    }
    _defaults = {
    }
project_overhead_allocations()

class project_work(osv.osv):
    
    def get_image_user(self, cr, uid, ids, context={}, arg=None, obj=None):
        result = {}
        records = self.browse(cr, uid, ids)
        for f in records:
            if f.user_id.image:
                result[f.id] = f.user_id.image
            else:
                result[f.id] = False
        
    
        return result
    
    def check_constrains(self, cr, uid, vals,task_id):
        rec_task = self.pool.get('project.task').browse(cr,uid,task_id)
        if 'date' in vals:
            deadline = rec_task.date_deadline
            if deadline:
                if vals['date'] > deadline:
                    raise osv.except_osv(('Not Allowed'),("Work date must be within Task deadline."))
        if rec_task.planned_hours:
            planned_hours = rec_task.planned_hours
        else:
            planned_hours = 0
        
        override_limit = False
        
        if 'override_hrs' in vals:
            if vals['override_hrs']:
                override_limit = True
        elif rec_task.override_hrs:
            override_limit = True
        if 'hours' in vals:
            #calculate all work time spent for this task i.e milestone
            work_ids = self.pool.get('project.task.work').search(cr, uid, [('task_id','=',task_id)])
            if work_ids:
                work_rec = self.pool.get('project.task.work').browse(cr,uid,work_ids)
                total_spent_hrs = 0
                for spent_hour in work_rec:
                    total_spent_hrs = total_spent_hrs + spent_hour.hours
                #compare
#                 if float(planned_hours - total_spent_hrs) < vals['hours'] and not override_limit:
#                     warning = "This Task has total hours "+str(planned_hours - total_spent_hrs)," (Out of  " +str(planned_hours)+") Avaible.\n Your work hours must be not greater than "+str(planned_hours - total_spent_hrs)+"\n"+str(vals['hours'])+"Can't be accumudated.  "
#                     raise osv.except_osv(('Work Hour Exceeds'),('Reset Spent Hours'))
#                 else:
#                     return True
        return True
    
    def create(self, cr, uid, vals, context=None, check=True):
        result = super(project_work, self).create(cr, 1, vals, context)
        for f in self.browse(cr,uid,result):
            check = self.check_constrains(cr, uid, vals,f.task_id.id)
            project_id = f.task_id.project_id.id
            rec_project = self.pool.get('project.project').browse(cr,uid,project_id)
            if rec_project.state == 'open':
                self.pool.get('project.project').set_open(cr, uid,project_id )
            #update remain hours for kanban view
            hours_remain = self.pool.get('project.project').update_hours_remain_for_kanban(cr,uid,project_id)
            self.pool.get('project.project').write(cr,uid,project_id,{'hours_budget_remain_kanban':float(hours_remain)})
        return result
  
     
    def write(self, cr, uid, ids, vals, context=None, check=True, update_check=True):
        result = False
        print "valsssssss",vals
        print "idssssssssssssssssss before self brow",ids
        for f in self.browse(cr,uid,ids):
            
            check = self.check_constrains(cr, uid, vals,f.task_id.id)
            if check:
                result = super(osv.osv, self).write(cr, uid, ids, vals)
            # create transactional logs for work
            #this code is commented on 12 oct 2017, it craetes problem in task work spent hours saving, this will be later on tested and sorted
            #for k, v in vals.iteritems():
             #   self.pool.get('project.project').create_transactional_logs(cr,uid,'Work',k,v,'Update',f)
            project_id = f.task_id.project_id.id
            rec_project = self.pool.get('project.project').browse(cr,uid,project_id)
            if rec_project.state == 'open':
                self.pool.get('project.project').set_inprogress(cr, uid,project_id)
            
            #update remain hours for kanban view
            hours_remain = self.pool.get('project.project').update_hours_remain_for_kanban(cr,uid,project_id)
            self.pool.get('project.project').write(cr,uid,project_id,{'hours_budget_remain_kanban':float(hours_remain)})
        result = super(osv.osv, self).write(cr, uid, ids, vals, context)
        return result
     
    def unlink(self, cr, uid, ids, context=None):
        
        #update remain hours for kanban view
        for f in self.browse(cr,uid,ids):
            project_id = f.task_id.project_id.id
            rec_project = self.pool.get('project.project').browse(cr,uid,project_id)
            hours_remain = self.pool.get('project.project').update_hours_remain_for_kanban(cr,uid,project_id)
            self.pool.get('project.project').write(cr,uid,project_id,{'hours_budget_remain_kanban':float(hours_remain)})
        result = super(osv.osv, self).unlink(cr, 1, ids, context)
        return result 
    
    
    def get_task_title(self, cr, uid, ids, context={}, arg=None, obj=None):
        result = {}
        for f in self.browse(cr, uid, ids):
            _logger.info("==============Task title is calculated for task work== : %s",f.task_id.name)
            result[f.id] = f.task_id.name
        return result
    
    def task_duedate(self, cr, uid, ids, context={}, arg=None, obj=None):
        result = {}
        for f in self.browse(cr, uid, ids):
            _logger.info("==============Task task_duedate is calculated for task work== : %s",f.task_id.date_deadline)
            result[f.id] = f.task_id.date_deadline
        return result
    def get_task_state(self, cr, uid, ids, context={}, arg=None, obj=None):
        result = {}
        for f in self.browse(cr, uid, ids):
            _logger.info("==============Task kanban state is calculated for task work== : %s",f.task_id.stage_id.name)
            result[f.id] = f.task_id.stage_id.name
        return result # project.task.type
    
    def task_progress(self, cr, uid, ids, context={}, arg=None, obj=None):
        result = {}
        for f in self.browse(cr, uid, ids):
            _logger.info("==============Task progress is calculated for task work== : %s",f.task_id.task_progress)
            result[f.id] = f.task_id.task_progress
        return result
    
    def task_start_date(self, cr, uid, ids, context={}, arg=None, obj=None):
        result = {}
        for f in self.browse(cr, uid, ids):
            _logger.info("==============Task progress is calculated for task work== : %s",f.task_id.task_progress)
            result[f.id] = f.project_id.date_start
        return result
    
    def parent_project(self, cr, uid, ids, context={}, arg=None, obj=None):
        result = {}
        for f in self.browse(cr, uid, ids):
            _logger.info("==============Task work parent project is for task work== : %s",f.task_id.project_id.id)
            result[f.id] = f.task_id.project_id.id
        return result
    
    def is_access_restricted(self, cr, uid, ids, context={}, arg=None, obj=None):
        result = {}
        records = self.browse(cr, uid, ids, context) 
        sql="""select id
                from inner res_groups_users_rel
                 inner res_groups
                on res_groups.id=res_groups_users_rel.gid
                where res_groups_users_rel.uid="""+str(uid)+""" and res_groups.name in ('Group CNI Technician')"""
        cr.execute(sql)
        res=cr.fetchone()
        for f in records:
            if res:
                result[f.id] = True
            else:
                result[f.id] = False
        return result

    
    
    _name = "project.task.work"
    _description = "Project Task Work"
    _inherit ='project.task.work'
    _columns = {
        'name': fields.char('Task Summary'),
        'activity_time': fields.float('Activity Time'),
        'user_id': fields.many2one('res.users', 'Done by', required=True, select="1"),
        'date_start': fields.function(task_start_date, method=True, string='Start Date',type='date'),
        'project_id':fields.function(parent_project,store =True, string='Project',type='many2one', relation='project.project'),
        'task_name':fields.function(get_task_title, method=True,  size=256, string='Restrict Access',type='char'),
        'task_due_date':fields.function(task_duedate, method=True, string='Duedate',type='date'),
        'task_state':fields.function(get_task_state, method=True,  size=256, string='State',type='char'),
        'task_progress':fields.function(task_progress, method=True,  size=256, string='Progress',type='float'),
        'restrict_access':fields.function(is_access_restricted, method=True,  size=256, string='Restrict Access',type='boolean'),
        'image':fields.related('user_id','image',type='binary',  string='Image',readonly=True),  
            }

project_work()

#----------------------------------------------------------------------------------------------------------
#-------------------------------------- inherited hr.employee-----------------------------------------------
class hr_employee(osv.osv):
    """Extended hr.employee through inheritance"""
    
    def calcemp(self,cr,uid,ids,context={},arg=None,obj=None):
        """Cancateniates emplyee name and id no"""
        result = {}
        for f in self.browse(cr,uid,ids):
            result[f.id] =  str(f.emp_srno or 'XXX')+"-"+str(f.name)
        return result
    def write(self, cr, uid, ids, vals, context=None, check=True, update_check=True):
         for f in self.browse(cr,uid,ids):
            pids = self.pool.get('project.project').search(cr,uid,[])
            if pids:
                rec = self.pool.get('project.project').browse(cr,uid,pids)
                for pr in rec:
                    state_id = self.pool.get('asset.state').search(cr, uid, [('name','=',pr.state),('team','=',5)])
                    if state_id:
                        rec = self.pool.get('asset.state').browse(cr,uid,state_id[0])
                        self.pool.get('project.project').write(cr, uid, pr.id, {'maintenance_state_id': rec.id})
            
            
            result = super(osv.osv, self).write(cr, uid, ids, vals, context)
         return result

    
    _name = 'hr.employee'
    _inherit ='hr.employee'
    _columns = {
    'tools_acquired': fields.one2many('asset.requisition', 'employee', 'Tools'),
    'project_assigned': fields.one2many('daily.material.reconciliation', 'project', 'Projects'),
    'hours_bank': fields.one2many('employee.hours.bank', 'description', 'Hours Bank'),
    'extenstion_no':fields.char('Ext'),
    'emp_srno':fields.char('Employee ID'),
    'emp_srno_calc':fields.function(calcemp, method=True,  size=256, string='Employee No',type='char'),
    }
hr_employee()
class res_partner(osv.osv):
    def open_map(self, cr, uid, ids, context=None):
        if context is None:
            context = {}

        partner = self.browse(cr, uid, ids[0], context=context)
        url = "http://maps.google.com/maps?oi=map&q="
        if partner.street:
            url += partner.street.replace(' ','+')
        if partner.city:
            url += '+'+partner.city.replace(' ','+')
        if partner.state_id:
            url += '+'+partner.state_id.name.replace(' ','+')
        if partner.country_id:
            url += '+'+partner.country_id.name.replace(' ','+')
        if partner.zip:
            url += '+'+partner.zip.replace(' ','+')

        return {
            'type': 'ir.actions.act_url',
            'url': url,
            'target': 'new'
        }
    def create(self, cr, uid, vals, context=None, check=True):
        result = super(res_partner, self).create(cr, uid, vals, context)
        if 'parent_id' in vals:
            if vals['parent_id']:
                pids = self.pool.get('project.project').search(cr,uid,[('partner_id','=',vals['parent_id'])])
                if pids:
                    rec = self.pool.get('project.project').browse(cr,uid,pids)
                    for pr in rec:
                        self.pool.get('client.contact.list').create(cr,uid,{'parent_project':pr.id,'subpartner_id':result}) 
        return result
    """Extended res.partner through inheritance"""
    _name = 'res.partner'
    _inherit ='res.partner'
    _columns = {
    'client_ext_no':fields.char('Ext'),
    'site_contact':fields.boolean('Site Contact',readonly=False)
    }
res_partner()
#------------------------------Asset Inherited--------------------------------------------------------------------
class asset_asset(osv.osv):
    """Extended asset.assete through inheritance"""
    _name = 'asset.asset'
    _inherit ='asset.asset'
    _columns = {
    'reserved': fields.boolean('Reserved',readonly=True),
    'asset_reservation_ids': fields.one2many('emp.tools.reservation', 'tool_to_reserve', 'Reservation'),
    }
asset_asset()


#----------------------------------------------------------------------------------------------------------
#-------------------------------------- Employee Tools Reservation-----------------------------------------------
class emp_tools_reservation(osv.osv):
    """This objects stores record of tools reserved by an employee"""
    _name = 'emp.tools.reservation'
    _columns = {
    'name': fields.many2one('hr.employee', 'Employee'),
    'tool_to_reserve': fields.many2one('asset.asset', 'Tool'),
    'date_from': fields.date('Date From'),
    'date_to': fields.date('Date To'),
    'reserved_by': fields.char('Reserved_by', size=64, readonly=True),
    'issued': fields.boolean('Issued',readonly=True),
    }
emp_tools_reservation()

#---------------------------------------------------------------------------------------------------------


#---------------------------------------------------------------------------------------------------------------------------------

class project_generic_template(osv.osv):
    """This stores generic project templates"""
    def get_total_hours_project(self,cr,uid,task_id,context = {},args = None,obj = None):
        result = {}
        
        for f in self.browse(cr,uid,task_id):
            
            hours = 0
            work_ids = self.pool.get('project.tasks.default').search(cr,uid,[('project_template_id','=',f.id)])
            if work_ids:
                rec_work = self.pool.get('project.tasks.default').browse(cr,uid,work_ids)
                for task in rec_work:
                    hours = hours + task.planned_hours_task
            
            result[f.id] = hours
        return result
    
    _name = 'project.generic.template'
    _columns = { 
    'name': fields.char(string = 'Name',size = 150, required =  True),
    'desc':fields.char(string = 'Desc',size = 150),
    'create_date': fields.datetime('Create Date', readonly=True, select=True),
    'default_task_ids':fields.one2many('project.tasks.default','project_template_id','Tasks'),
    'planned_hours': fields.function(get_total_hours_project,method =True, string= "Template Planned Hours", type ='float'),
    'default_users':fields.many2one('res.users','Default Worker',required = True)
    }
project_generic_template()




class project_tasks_default(osv.osv):
    
    """"""
    
    def check_hour_exceed(self, cr, uid, task_id,task_name,task_hours):
        
        work_hrs = 0
        work_ids = self.pool.get('project.task.work.default').search(cr, uid, [('task_id','=',task_id)])
        if work_ids:
            rec_w = self.pool.get('project.task.work.default').browse(cr, uid, task_id)
            for w in rec_w:
                work_hrs = work_hrs + w.hours
            if work_hrs > task_hours:
               raise osv.except_osv(('Hours Exceeds'),("Sum of work hours in  Task "+str(task_name)+" Exceeds than Task planed hours\n Go to Task " +str(task_name)+" and reset its activity hours."))
            else:
                return False
    
    
    def get_total_hours_task(self,cr,uid,task_id,context = {},args = None,obj = None):
        result = {}
        hours = 0
        
        for f in self.browse(cr,uid,task_id):
            work_ids = self.pool.get('project.task.work.default').search(cr,uid,[('task_id','=',f.id)])
            if work_ids:
                rec_work = self.pool.get('project.task.work.default').browse(cr,uid,work_ids)
                for work in rec_work:
                    hours = hours + work.hours
            
            result[f.id] = hours
        return result
    
    def write(self, cr, uid, ids, vals, context=None, check=True, update_check=True):
        result = super(osv.osv, self).write(cr, uid, ids, vals, context)
        return result
    
    def create(self, cr, uid, vals, context=None, check=True):
        result = super(osv.osv, self).create(cr, uid, vals, context)
#         hours_exceeds = self.check_hour_exceed(cr, uid, result,vals['name'],vals['planned_hours'])
        return result
    
    _name = 'project.tasks.default'
    _columns = {
    'name': fields.char('Task Name',size = 100,required = True),
    'planned_hours_task': fields.function(get_total_hours_task,method =True, store = True,string= "Initially Planned Hours", type ='float'),
    'project_template_id': fields.many2one('project.generic.template', 'Project'),
    'project_stage':fields.char('Stage',size = 150),
    'repitition':fields.integer('Quantity'),
    'project_task_work_ids': fields.one2many('project.task.work.default', 'task_id', 'Task Activity'),
    'user_id': fields.many2one('res.users', 'Done by'),
    }
    _defaults = {'repitition':1}
project_tasks_default()

class project_task_work_default(osv.osv):
    """This object stores project  tasks work activities, task are associated with task"""
    _name = 'project.task.work.default'
    _columns = {
    'task_id':fields.many2one('project.tasks.default', 'Task'),
    'repitition':fields.integer('Quantity'),
    'name':fields.char('Activity',size = 150,required=True),
    'user_id': fields.many2one('res.users', 'User'),
    'hours': fields.float('Budgeted Hours'),
    }
    _defaults = {'repitition':1}
project_task_work_default()

#-------------------------------------------------------------------------------------------------------------------------

class res_users(osv.osv):
    """This object inherited res_users adding a columns 'Can be assign milstone, this will filter this user'"""
    _name = "res.users"
    _description = "Project Task Work"
    _inherit ='res.users'
    _columns = {
        'work_on_task': fields.boolean('Can be assigned Tasks'),
            }

res_users()

class res_company(osv.osv):
    """This object inherited res_users adding a columns 'Can be assign milstone, this will filter this user'"""
    _name = "res.company"
    _description = "add pic"
    _inherit ='res.company'
    _columns = {
        'pic': fields.binary('Image'),
            }

res_company()

#-----------------------------------------------------------------------------------------------------------------------------


class prj_billing_expenseline(osv.osv):
   
    
    def gross_bill(self,cr,uid,ids,context={},arg=None,obj=None):
        """task total charged hours will be returned"""
        result = {}
        for f in self.browse(cr, uid,ids): 
            
            result[f.id] = f.quantity * f.amount
        return result
    
    def calc_taxes(self,cr,uid,ids,context={},arg=None,obj=None):
        """tax over gross billing"""
        result = {}
        for f in self.browse(cr, uid,ids): 
            
            result[f.id] = f.gross_bill 
        return result

    def net_bill(self,cr,uid,ids,context={},arg=None,obj=None):
        """net_bill"""
        result = {}
        for f in self.browse(cr, uid,ids): 
            
            result[f.id] = (f.gross_bill + f.adjustments) +f.taxes
        return result

    def create(self, cr, uid, vals, context=None, check=True):
        result = super(osv.osv, self).create(cr, uid, vals, context)
        rec = self.browse(cr,uid,result)
        for g in rec:
            if g.expenseline_id.expense_types.name == 'Material':
                self.pool.get('project.materials.consumed').create(cr, uid,
                                                                   {'related_expence_id': g.id,
                                                                    'name': g.project_id.id,
                                                                    'hidden_source': 'expense'})
        for f in rec:
            project_rec = self.pool.get('project.project').browse(cr,uid,f.project_id.id)
#             raise osv.except_osv(('project state'),(project_rec.state))
            if project_rec.state == 'draft':
                
                self.pool.get('project.project').set_open(cr,uid,f.project_id.id)

        return result 
    
    def billable_unit(self,cr,uid,ids,context={},arg=None,obj=None):
        """net_bill"""
        result = {}
        for f in self.browse(cr, uid,ids): 
            
            result[f.id] = 'Expense/'+str(f.expenseline_id.expense_types.name)+'/'+str(f.expenseline_id.name)
        return result   
    
    _name = "prj.billing.expenseline"
    _description = "Project Task Work"
    _columns = {
        #billinh fields
        'expenseline_id': fields.many2one('hr.expense.line'),
        'quantity':fields.float('Quantity'),
        'dated':fields.related('expenseline_id','date_value',type='date',  string='Date'),  
        'project_id':  fields.many2one('project.project'),
        'billable_unit':fields.function(billable_unit, method=True, string='billable_unit',type='char'),
        'amount':fields.related('expenseline_id','unit_amount',type='float',  string='Rate'),  
        'gross_bill':fields.function(gross_bill, method=True, string='Gross Billable',type='float'),
        'adjustments':fields.float('Adjustments'),
        'taxes':fields.related('expenseline_id','taxes_paid',type='float',  string='Taxes'),  
        'net_bill':fields.function(net_bill, method=True, string='Net Billable',type='float'),
        'comments':fields.text('Comments'),
        # ,,,,, New Fields
                    }
    _defaults = {'quantity' :1.00}

prj_billing_expenseline()
#--------------------
class prj_billing_materials(osv.osv):
   
    
    """This object use for project billable material"""
    
    def create(self, cr, uid, vals, context=None, check=True):
        result = super(osv.osv, self).create(cr, uid, vals, context)
        rec = self.browse(cr,uid,result)
#         raise osv.except_osv(('Input Hours Exceeds'),(rec.project_id[0]))
#        as the table prj_billing_materials and project.materials.consumed both appear as one2many to project, one in material tab
#        while other in metice tab, so when in first tble a record is created, it will also create a record in 2nd table
        self.pool.get('project.materials.consumed').create(cr,uid,{'related_material_id':rec.id,'name':rec.project_id.id,'hidden_source': 'material'})
        
        return result
  
     
    def write(self, cr, uid, ids, vals, context=None, check=True, update_check=True):
        result = super(osv.osv, self).write(cr, uid, ids, vals, context)
        return result
     
    def onchange_returned_product(self, cr, uid, ids,return_qty):
        vals = {}
        for f in self.browse(cr,uid,ids):
            disp_qty = f.dispatch_qty
            price = f.price_unit
            net_amount = (disp_qty - return_qty)*price
            vals['total'] = net_amount
            vals['net_qty'] = disp_qty - return_qty
            update_lines = self.pool.get('material.reconcile.lines').write(cr, uid, ids, {
                       'returned_qty':return_qty,
                       'net_qty':vals['net_qty'],
                       'total':vals['total'],
                       }) 
        return {'value':vals}
    
    def onchange_dispatch_qty(self, cr, uid, ids,dispatch_qty,sale_price):
        vals = {}
        total = dispatch_qty * sale_price
        vals['total'] = total
        vals['net_qty'] = dispatch_qty 
        return {'value':vals}
    
    def onchange_returned_qty(self, cr, uid, ids,return_qty,sale_price):
        vals = {}
        for f in self.browse(cr,uid,ids):
            total = (f.dispatch_qty -return_qty ) * sale_price
            vals['total'] = total
            vals['net_qty'] = f.dispatch_qty - return_qty 
            vals['returned_qty'] = return_qty
            update_lines = self.pool.get('material.reconcile.lines').write(cr, uid, ids, vals) 
        return {'value':vals}
    
    def onchange_product(self, cr, uid, ids,product):
        vals = {}
        rec_product = self.pool.get('product.product').browse(cr,uid,product)
        vals['price_unit'] = rec_product.list_price
        return {'value':vals}
    
    def unlink(self, cr, uid, ids, context=None):
        result = super(osv.osv, self).unlink(cr, uid, ids, context)
        return result 
    
    def gsku(self, cr, uid, ids, field_name, arg, context=None):
        result = {}
        product = self.pool.get('product.product')
        for f in self.browse(cr,uid,ids):
            result[f.id] = product.browse(cr,uid,f.product.id).product_tmpl_id.sku
        return result
    
    def product_name(self, cr, uid, ids, field_name, arg, context=None):
        result = {}
        product = self.pool.get('product.product')
        for f in self.browse(cr,uid,ids):
            product = self.pool.get('product.product').browse(cr,uid,f.product.id)
            result[f.id] = str(product.product_tmpl_id.sku)+"/"+str(product.name)
        return result
    
    def gross_bill(self,cr,uid,ids,context={},arg=None,obj=None):
        """gross bill for dispatchalble units"""
        result = {}
        for f in self.browse(cr, uid,ids): 
            
            result[f.id] = f.dispatch_qty * f.sale_price
        return result
    
    def calc_taxes(self,cr,uid,ids,context={},arg=None,obj=None):
        """tax over gross billing"""
        result = {}
        for f in self.browse(cr, uid,ids): 
            
            result[f.id] = f.total * 0.13
        return result

    def net_bill(self,cr,uid,ids,context={},arg=None,obj=None):
        """net_bill"""
        result = {}
        for f in self.browse(cr, uid,ids): 
            
            result[f.id] = (f.total + f.adjustments) +f.taxes
        return result
    
    _name = 'prj.billing.materials'
    _description = "This object store sale reconcile"
    _columns = {
        'product': fields.many2one('product.product', 'Product'),  
        'name':fields.function(product_name ,method = True, type='char', string="SKU",),  # Project BILLABLE Material 
        'sku':fields.function(gsku ,method = True, type='char', string="SKU",),    
        'image':fields.related('name','image',type='binary',  string='Image', readonly=True),
        'dispatch_qty': fields.float('Quantity', required=True), # Project BILLABLE Material
        'sale_price': fields.float('Rate'), # Project BILLABLE Material
        'dispatch_id': fields.many2one('daily.material.reconciliation','Sale Reconciliation'),
        'date_dispatched': fields.related('dispatch_id','date_dispatched',type='date',  string='Required Date'), # Project BILLABLE Material		
        'client_ref': fields.related('dispatch_id','client_ref',type='char',  string='Client Ref #'),		
        'project_id':fields.related('dispatch_id','project',type='many2one', relation = 'project.project', string='project', readonly=True), # Project BILLABLE Material
        'prod_desc': fields.related('name','product_tmpl_id','description',type='text', string='Descrpition', readonly=True),
        'source': fields.many2one('product.supplierinfo', string='Source'),
        'pickup_location':  fields.char('PickUp Location',size = 160),
        'notes':  fields.text('Notes'), # Project BILLABLE Material
        'total':fields.function(gross_bill, method=True, string='Gross Billable',type='float'), # Project BILLABLE Material
        'adjustments':fields.float('Adjustments'), # Project BILLABLE Material
        'taxes':fields.function(calc_taxes, method=True, string='Taxes',type='float'), # Project BILLABLE Material
        'net_bill':fields.function(net_bill, method=True, string='Net Billable',type='float'), # Project BILLABLE Material
        
    }
   
prj_billing_materials()
#--------------------


class project_task(osv.osv):
    """This object inherited res_users adding a columns 'Can be assign milstone, this will filter this user'"""
    
    def is_access_restricted(self, cr, uid, ids, context={}, arg=None, obj=None):
        result = {}
        records = self.browse(cr, uid, ids)
        sql="""select res_users.id from res_users
                     inner join res_groups_users_rel
                     on res_groups_users_rel.uid = res_users.id
                     inner join res_groups
                    on res_groups.id=res_groups_users_rel.gid
                    where res_groups_users_rel.uid="""+str(uid)+""" and res_groups.name in ('Group CNI Technician')"""
        cr.execute(sql)
        res=cr.fetchone()
    
        for f in records:
            if res:
                result[f.id] = True
            else:
                result[f.id] = False
        
    
        return result
   

    def write(self, cr, uid, ids, vals, context=None, check=True, update_check=True):
        controller  = self.pool.get('project.project')
        for f in self.browse(cr,uid,ids):
            print "task_id............................................................",f.id        
            #create logs for task updates
            for k, v in vals.iteritems():
                self.pool.get('project.project').create_transactional_logs(cr,uid,'Task',k,v,'Update',f)
        print "vals of task write method>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>", vals
        if len(vals) ==1:
            if 'work_ids'in vals:
                uid = 1
        else:
            uid = uid
        # if task stage is in progress set project to in progress
        if 'stage_id' in vals:
            navg = self.pool.get('project.task.type').browse(cr,uid,vals['stage_id']).name
            if navg == 'In Progress' or navg == 'In_progress':
                controller.set_inprogress(cr, uid,f.project_id.id)
        result = super(project_task, self).write(cr, uid, ids, vals, context)
 
        return result

    
    def get_task_progress(self,cr,uid,ids,context={},arg=None,obj=None):
        """Method used bt project_task"""
        result = {}
        for f in self.browse(cr,uid,ids):
            planned_hours  = f.task_planned_hours
            if not planned_hours or planned_hours == 0:
                planned_hours = 1
            spent_hours = 0
            progress = 0
            work_ids = self.pool.get('project.task.work').search(cr,uid,[('task_id','=',f.id)])
            if work_ids:
                rec_work  = self.pool.get('project.task.work').browse(cr,uid,work_ids)
                for work in rec_work:
                    spent_hours = spent_hours + work.hours
            progress = (spent_hours *100)/planned_hours	
            _logger.info("==============Calculated Task hours for task progress bar== : %d",progress)		
            result[f.id] =  progress
        return result
    
    def get_task_total_charged_hrs(self,cr,uid,ids,context={},arg=None,obj=None):
        """task total charged hours will be returned"""
        result = {}
        for f in self.browse(cr, uid,ids): 
            sql="""select  COALESCE(sum(hours),0) from project_task_work where task_id="""+str(f.id)
            cr.execute(sql)
            res=cr.fetchone()
            result[f.id] = float(res[0])
        return result
    
    def gross_bill(self,cr,uid,ids,context={},arg=None,obj=None):
        """task total charged hours will be returned"""
        result = {}
        for f in self.browse(cr, uid,ids): 
            
            result[f.id] = f.quantity * f.hour_rate
        return result
    
    def calc_taxes(self,cr,uid,ids,context={},arg=None,obj=None):
        """tax over gross billing"""
        result = {}
        for f in self.browse(cr, uid,ids): 
            
            result[f.id] = f.gross_bill * 0.13
        return result

    def net_bill(self,cr,uid,ids,context={},arg=None,obj=None):
        """net_bill"""
        result = {}
        for f in self.browse(cr, uid,ids): 
            
            result[f.id] = (f.gross_bill + f.adjustments) +f.taxes
        return result
    
    def task_plannedhrs(self,cr,uid,ids,context={},arg=None,obj=None):
        """calculated total planned hours from task work"""
        result = {}
        for f in self.browse(cr, uid,ids): 
            sql="""select  COALESCE(sum(activity_time),0) from project_task_work where task_id="""+str(f.id)
            cr.execute(sql)
            res=cr.fetchone()
            result[f.id] = float(res[0])
            
        return result
    
    def task_remhrs(self,cr,uid,ids,context={},arg=None,obj=None):
        """calculated total remainig hours from task work"""
        result = {}
        for f in self.browse(cr, uid,ids): 
            sql="""select  COALESCE(sum(hours),0) from project_task_work where task_id="""+str(f.id)
            cr.execute(sql)
            res=cr.fetchone()
            result[f.id] = float(f.task_planned_hours) - res[0]
            
        return result

    def create(self, cr, uid, vals, context=None, check=True):
        result = super(osv.osv, self).create(cr, uid, vals, context)
        rec = self.browse(cr,uid,result)
        for f in rec:
            project_rec = self.pool.get('project.project').browse(cr,uid,f.project_id.id)
            self.pool.get('project.labour.hours.expended').create(cr,uid,{
                                                        'labour_hours_expended':result,
                                                        'name':f.project_id.id
                                                         }) 
            
            if project_rec.state == 'draft':
                
                self.pool.get('project.project').set_open(cr,uid,f.project_id.id)
        return result	
    
    #def _code_get(self, cr, uid, context=None):
    #    type_obj = self.pool.get('project.task.type')
    #    ids = type_obj.search(cr, uid, [('stage_for','=','Task')])
    #    res = type_obj.read(cr, uid, ids, ['id', 'name'], context)
    #    return [(r['id'], r['name']) for r in res]
    
    def unlink(self, cr, uid, ids, context=None):
        
        for f in self.browse(cr,uid,ids):
            lh_ids = self.pool.get('project.labour.hours.expended').search(cr, uid, [('labour_hours_expended','=',f.id)])
            for g in lh_ids:
                self.pool.get('project.labour.hours.expended').unlink(cr,uid,g)
        result = super(project_task, self).unlink(cr, uid, ids, context)
            
        return result
    
    _name = "project.task"
    _description = "Project Task Work"
    _inherit ='project.task'
    _track = {
        'stage_id': {
            # this is only an heuristics; depending on your particular stage configuration it may not match all 'new' stages
            'project.mt_task_new': lambda self, cr, uid, obj, ctx=None: obj.stage_id and obj.stage_id.sequence <= 1,
        },
        'user_id': {
            'project.mt_task_assigned': lambda self, cr, uid, obj, ctx=None: obj.user_id and obj.user_id.id,
        },
        'kanban_state': {
            'project.mt_task_blocked': lambda self, cr, uid, obj, ctx=None: obj.kanban_state == 'blocked',
            'project.mt_task_ready': lambda self, cr, uid, obj, ctx=None: obj.kanban_state == 'done',
        },
    }

    _columns = {
        'user_id': fields.many2one('res.users', 'Assigned to', domain=[('work_on_task', '=',True)], select=True, track_visibility='onchange'),
        'override_hrs':fields.boolean('Override Task Hours'),
        'float':fields.float('Float'),
        #'stage_id': fields.many2one('project.task.type', 'Stage', track_visibility='onchange', select=True,
        #                domain="[('project_ids', '=', project_id),('stage_for', '=', 'Task')]", copy=False),
        'project_id': fields.many2one('project.project', 'Project', ondelete='set null', select=True, track_visibility='onchange', change_default=True),
        'task_planned_hours':fields.function(task_plannedhrs, method=True, string='Initialy Planned Hrs',type='float'),
        'task_rem_hours':fields.function(task_remhrs, method=True, string='Remaining Hours',type='float'),
        'task_progress':fields.function(get_task_progress, method=True, string='Progress',type='float'),
	    'consumable_products_ids': fields.one2many('daily.material.reconciliation', 'task_id', 'Stockables'),
        'restrict_access':fields.function(is_access_restricted, method=True, string='Restrict Access',type='boolean'),
        #billinh fields
        'quantity':fields.function(get_task_total_charged_hrs, method=True, string='Quantity',type='float'),
        'hour_rate':fields.float('Rate'),
        'gross_bill':fields.function(gross_bill, method=True, string='Gross Billable',type='float'),
        'adjustments':fields.float('Adjustments'),
        'taxes':fields.function(calc_taxes, method=True, string='Taxes',type='float'),
        'net_bill':fields.function(net_bill, method=True, string='Net Billable',type='float'),
        'comments':fields.text('Comments'),
        #stages are commented for the time being
        # it will be uncommened when task ans isues t
        # 'stages': fields.selection(_code_get, 'Stages'),
        # 'state': fields.selection([
        #                        ('Jeopardy','Jeopardy'),
        #                        ('draft','Draft'),
        #                        ('open','Open'),
        #                        ('in_progress','In Progress'),
        #                        ('OnHold','On Hold'),
        #                        ('cancelled', 'Cancelled'),
        #                        ('pending','Pending'),
        #                        ('Completed','Completed'),
        #                        ('close','Closed')]),
        # ,,,,, New Fields
                    }
   

project_task()

#------------------------ Task Handling history ---------------------------------------------------------------------
class project_task_handling_logs(osv.osv):
  
    def update_task_log(self, cr, uid, task_id,log_statement,remarks,reason):
        
        self.pool.get('project.task.handling.logs').create(cr,uid,{
                                                        'name':log_statement,
                                                        'project_id':task_id,
                                                        'remarks': remarks,
                                                        'reason': reason,
                                                        'event_date':datetime.now(),
                                                        'event_by':uid
                                                         }) 
        return
    _name = "project.task.handling.logs"
    _description = "maintains tasks logs"
    _columns = {
        'name': fields.selection([('ACCEPTED', 'Accepted'),
                                    ('COMPLETE','Complete'),
                                    ('DISPATCHED','Dispatched'),
                                    ('EN_ROUTE','EnRoute'),
                                    ('ON_SITE', 'OnSite'),
                                    ('INCOMPLETE','In Complete'),
                                    ('REJECTED','Rejected'),
                                    ('TENTATIVE','Tentative')],
                                      'Job Status'),
        'remarks': fields.char('Remarks'),
        'reason': fields.char('Reason'),
        'project_id':fields.many2one('project.project','Project'),#project id is stored here
        'event_date': fields.datetime('Date Time'),
        'event_by': fields.many2one('res.users','Worker'),
            }
   
project_task_handling_logs()

# Transactional logs

class project_transactional_log(osv.osv):
  
    def update_task_log(self, cr, uid, task_id,log_statement,remarks,reason):
        
        self.pool.get('project.task.handling.logs').create(cr,uid,{
                                                        'name':log_statement,
                                                        'task_id':task_id,
                                                        'remarks': remarks,
                                                        'reason': reason,
                                                        'event_date':datetime.now(),
                                                        'event_by':uid
                                                         }) 
        return
    _name = "project.transactional.log"
    _description = "maintains proect logs"
    _order = 'event_date DESC'
    _columns = {
        'operation': fields.selection([('Insert', 'Create'),
                                    ('Update','Update'),
                                    ('Unlink','Deleted'),
                                    ('Read','Read')],
                                      'Transaction'),
        'object_name': fields.char('Data Object Affected'),
        'pre_value': fields.char('Previous Data Value'),
        'post_value': fields.char('Post Data Value'),
        'column_name':fields.char('Column'),
        'project_id':fields.many2one('project.project','ProectID'),
        'task_id':fields.many2one('project.task','TaskID'),
        'work_id':fields.many2one('project.task.work','WordID'),
        'event_date': fields.datetime('Transaction Date'),
        'event_by': fields.many2one('res.users','Performed By'),
            }
   
project_transactional_log()




################



#---------------------------------- time sheeet --------------------------------------------------------------------------------------------------------

class hr_timesheet_sheet(osv.osv):
    #parent object in time sheet, 
    # its main chlid table >  hr.analytic.timesheet ,modified to add project, task and activit id
    _name = "hr_timesheet_sheet.sheet"
    _inherit = "hr_timesheet_sheet.sheet"
    _description="Timesheet"
    
    
    # Created by Shahid
    def adjust_timesheet_overtime_deficincies(self, cr,uid,bank_it,record_id):
        """ 
        Called by both create and write method of timesheet_sheet
        
        """
        result = True
        print "record id ",record_id
        print "bank it",bank_it
        for f in self.browse(cr,uid,record_id):
            debit = 0
            credit = 0
            description = ''
            overtime_status = ''
            overtime_check = (f.total_timesheet - f.schedule_shift) + f.over_under_time
            # Compare punched hours and calc overtime
            if f.total_timesheet > f.schedule_shift:
                
                if overtime_check <= f.schedule_shift and bank_it==True:
                    debit = f.total_timesheet - f.schedule_shift
                    credit = 0
                    remarks = 'Overtime'
                    if bank_it:
                        overtime_status = 'Banked'
                    else:
                        overtime_status = 'Encashed'
                
                    self.pool.get('employee.hours.bank').create(cr,uid,{'employee_id':f.employee_id.id,'debit':debit, 'credit': credit, 'description': description, 'timesheet_id': record_id})
                elif overtime_check > f.schedule_shift and bank_it==True:
                    raise osv.except_osv(('Maximum overtime reached'),('You reached maximum hours limit(40) in hours bank, please uncheck "Bank my Overtime"!'))      
            
            elif f.total_timesheet < f.schedule_shift:
                if bank_it:
                    raise osv.except_osv(('Invalid Entry'),('Your hours are less than required shift hours,please uncheck "Bank My Overtime" checkbox!'))
                else:
                    overtime_status = 'No-Overtime'
            
            elif f.total_timesheet == f.schedule_shift:
                overtime_status = 'No-Overtime'
            
            self.write(cr,uid,f.id,{'overtime_status':overtime_status})        
        return result
    
    
    # Created / Edited by Shahid
    def create(self, cr, uid, vals, context=None, check=True):
        result = super(osv.osv, self).create(cr, uid, vals, context)
        for f in self.browse(cr,uid,result):
            self.adjust_timesheet_overtime_deficincies(cr,uid,vals['bank_it'],result)
        return result


    # Edited by Obaid
    def write(self, cr, uid, ids, vals, context=None, check=True, update_check=True):
        
        for f in self.browse(cr,uid,ids):
            overtime_check = (f.total_timesheet - f.schedule_shift) + f.over_under_time
            adjustment_id = self.pool.get('attendance.adjustment.lines').search(cr,uid,[('timesheet_idd','=',f.id),('state','=','Deficiency')])
            if adjustment_id:
                adjustment_rec = self.pool.get('attendance.adjustment.lines').browse(cr,uid,adjustment_id)
                for adjustment in adjustment_rec:
                    
                    if adjustment.over_time_adjustemnt == 'Paid':
                        total_overtime = f.total_overtime
                        total_defc = abs(adjustment.over_under_time)
                        if total_defc > total_overtime:
                            raise osv.except_osv(('Insufficient Bank hours'),("You dont have enough bank hours to balance hours shortage. Earn more overtime then adjust your hours."))
           
            if 'bank_it' in vals:
                if vals['bank_it'] != True:
                        if f.total_timesheet > f.schedule_shift:
                            bank_ids = self.pool.get('employee.hours.bank').search(cr, uid, [('timesheet_id','=',f.id)])
                            for rec in bank_ids:
                                self.pool.get('employee.hours.bank').unlink(cr,uid,rec)
                else:
                        if f.total_timesheet > f.schedule_shift:
                            
                            if overtime_check <= f.schedule_shift:

                                debit = f.total_timesheet - f.schedule_shift
                                description = 'Overtime for current week is banked'
                                bank_ids = self.pool.get('employee.hours.bank').search(cr, uid, [('timesheet_id','=',f.id)])
                                if not bank_ids:
                                    self.pool.get('employee.hours.bank').create(cr,uid,{'employee_id':f.employee_id.id,'debit':debit, 'credit': 0, 'description': description, 'timesheet_id': f.id})
                            else:
                                raise osv.except_osv(('Maximum overtime reached'),('You reached maximum hours limit(40) in hours bank, please uncheck "Bank my Overtime"!'))        
                        elif f.total_timesheet < f.schedule_shift:
                            raise osv.except_osv(('Invalid Entry'),('Your hours are less than required shift hours,please uncheck "Bank My Overtime" checkbox!'))

                        else:
                            raise osv.except_osv(('No Extra Hours to Bank'),('You do not have additional hours to bank, please uncheck "Bank My Overtime" checkbox!'))
                
            else:
                    
                    if f.bank_it == True:
                        
                        if f.total_timesheet > f.schedule_shift:
                            
                            bank_ids = self.pool.get('employee.hours.bank').search(cr, uid, [('timesheet_id','=',f.id)])
                            
                            for b_id in bank_ids:
                                if 'unit_amount' in vals['timesheet_ids'][0][2]:
                                    print("--------------------- &&&& ---  Write method on Timesheet --- &&&& ------------------------ ",vals['timesheet_ids'][0][2]['unit_amount'])
                                    debit = vals['timesheet_ids'][0][2]['unit_amount'] - f.schedule_shift
                                    description = 'Overtime for current week is banked'
                                    self.pool.get('employee.hours.bank').write(cr,uid,b_id,{'debit':debit, 'credit': 0, 'description': description})
#             if 'total_hours_this_timesheet' in vals:
#                 if vals['bank_it'] == True:
#                     if vals['total_timesheet'] > f.total_timesheet:
#                         debit = f.total_timesheet - f.schedule_shift
#                         description = 'Overtime for current week is banked'
#                         bank_ids = self.pool.get('employee.hours.bank').search(cr, uid, [('timesheet_id','=',f.id)])
#                         if not bank_ids:
#                             self.pool.get('employee.hours.bank').create(cr,uid,{'employee_id':f.employee_id.id,'debit':debit, 'credit': 0, 'description': description, 'timesheet_id': f.id})
#                     elif vals['total_timesheet'] < f.total_timesheet:
#                             bank_ids = self.pool.get('employee.hours.bank').search(cr, uid, [('timesheet_id','=',f.id)])
#                             for rec in bank_ids:
#                                 self.pool.get('employee.hours.bank').unlink(cr,uid,rec)    
                                   
            result = super(osv.osv, self).write(cr, uid, ids, vals, context)
        return result
    
    
    # Created by Obaid
    def unlink(self, cr, uid, ids, context=None):
        
        for f in self.browse(cr,uid,ids):
            
            bank_ids = self.pool.get('employee.hours.bank').search(cr, uid, [('timesheet_id','=',f.id)])
            for rec in bank_ids:
                self.pool.get('employee.hours.bank').unlink(cr,uid,rec)
                
        result = super(osv.osv, self).unlink(cr, uid, ids, context)   
        return result
    
    
    # Created by Shahid
    def get_total_overtime(self, cr, uid, ids, name, args, context=None):
        result = {}
        for f in self.browse(cr, uid, ids, context):
            if f.total_timesheet > f.schedule_shift:
                result[f.id] = (f.total_timesheet - f.schedule_shift) - f.banked_hours
                if f.bank_it == True:
                    result[f.id] = 0.00    
        return result
    
    
    # Created by Shahid
    def get_net_hours_this_timesheet(self, cr, uid, ids, name, args, context=None):
        result = {}
        for f in self.browse(cr, uid, ids, context):
            this_timesheet = 0.00
            if f.total_timesheet > f.schedule_shift:
                this_timesheet =  f.schedule_shift + f.total_overtime 
            elif f.total_timesheet < f.schedule_shift:
                this_timesheet =  f.total_timesheet # also add hours adjusted by user in case of dificiency
            adjust_id = self.pool.get('attendance.adjustment.lines').search(cr, uid, [('timesheet_idd','=',f.id)])
            if adjust_id:
                rec_adjust = self.pool.get('attendance.adjustment.lines').browse(cr,uid,adjust_id[0])
                for adj in rec_adjust:
                    this_timesheet = this_timesheet + adj.input_hours
            result[f.id] = this_timesheet         
        return result
   
   # Created by Obaid
    def get_total_banked_overtime(self, cr, uid, ids, name, args, context=None):
        
        debit_value = {}
        total_balance = {}
        
        rec = self.browse(cr, uid, ids, context)
        
        debit_query = """select COALESCE(sum(debit),0) from employee_hours_bank where employee_id = """ + str(rec.employee_id.id) 
        cr.execute(debit_query)
        debit_value = cr.fetchone()
        debit_str = str(debit_value).replace('\'', '').replace(',', '').replace('(', '').replace(')','')
        credit_query = """select COALESCE(sum(credit),0) from employee_hours_bank where employee_id = """ + str(rec.employee_id.id) 
        cr.execute(credit_query)
        credit_value = cr.fetchone()
        credit_str = str(credit_value).replace('\'', '').replace('\'', '').replace(',', '').replace('(', '').replace(')','')
        
        
        total_balance[rec.id] = float(debit_str) - float(credit_str)
        print total_balance

        return total_balance   
    
    
    def load_attendance(self, cr, uid, ids, context=None):
        
        
        for f in self.browse(cr, uid, ids, context):
#                         
#             label_df = datetime.datetime.strptime(str(f.date_from), '%Y-%m-%d').strftime('%B-%d-%Y')
#             label_td = datetime.datetime.strptime(str(this_date), '%Y-%m-%d').strftime('%B-%d-%Y')
            if f.total_attendance == 40:
                over__under_time = 0
                state = 'Ok'
                regular_hrs = 40
            elif f.total_attendance > 40:
                over_under_time = f.total_attendance -40
                state =  'Overtime'
                regular_hrs = f.total_attendance - over_under_time
            elif f.total_attendance < 40:
                regular_hrs = f.total_attendance
                over_under_time = f.total_attendance - 40
                state =  'Deficiency'
                
            elif f.total_attendance == 0:
                regular_hrs = f.total_attendance
                over_under_time = 0- 40
                state =  'Deficiency'
                
            write = self.write(cr, uid,ids ,{
                   'total_hours': f.total_attendance,
                   'over_under_time':over_under_time,
                   'remarks':state,
                   }) 
                    
        return

    
    def onchange_date(self, cr, uid, ids, this_date,choice):
        """it received from amd to date from timesheet"""
        print "this date",this_date
        _logger.info("==============date from time today================ : %r",time.strftime("%x"))
        _logger.warning("=============selected date=============== : %r",this_date)
        vals = {}
        date_today = time.strftime('%Y-%m-%d')
        _logger.info("===========today formated============= : %r",date_today)
        if choice == 'compare_date_from':
            if this_date:
                if str(this_date) > date_today:
                    vals['date_from'] = None
        elif choice == 'compare_date_to':
            if this_date:
                if str(this_date) > date_today:
                    vals['date_to'] = None
        return {'value':vals}
    
    def _get_week_startdate(self,cr,uid,ids):
#		import time
		current_date = time.strftime('%Y-%m-%d')
		fdate = datetime.strptime(current_date,'%Y-%m-%d')
		start = fdate-timedelta(days=(fdate.weekday()+1))
		start2 = start.strftime('%Y-%m-%d')
		return start2


    def _get_week_enddate(self,cr,uid,ids):
		week_start = self._get_week_startdate(cr,uid,ids)
		fstart = datetime.strptime(week_start,'%Y-%m-%d')
		end = fstart + timedelta(days = 6)
		end_date = end.strftime('%Y-%m-%d')
		return end_date

    def get_week_no(self,cr,uid,ids,names,args,context = None):
		result = {}
		for f in self.browse(cr,uid,ids):
			sdate = datetime.strptime(f.date_from,'%Y-%m-%d')
			result[f.id]  =sdate.isocalendar()[1]
		return result
    
    
    # Created by Shahid    
    def get_diff(self,cr,uid,ids,names,args,context = None):
        result = {}
        
        for f in self.browse(cr,uid,ids):
            diff = float(f.total_timesheet) - float(f.schedule_shift)
#             adjust_id = self.pool.get('attendance.adjustment.lines').search(cr, uid, [('timesheet_idd','=',f.id)])
#             if adjust_id:
#                 rec_adjust = self.pool.get('attendance.adjustment.lines').browse(cr,uid,adjust_id[0])
#                 for adj in rec_adjust:
#                     diff = diff - adj.input_hours
                    
#             if float(f.total_timesheet) > float(f.schedule_shift):
#                 print "its overtime",diff
#                 diff = str(diff) + " (Overtime)"
#             elif f.total_timesheet < f.schedule_shift:
#                 diff = str(diff) + " (Below Schedule Shift)"
#                 print "below",diff
#             elif f.total_timesheet ==f.schedule_shift:
#                 diff = str(diff) + " (OK)"
#                 print "total hours = sc",diff
            result[f.id] = diff
        return result
    
    # Created by Shahid
    def get_banked_hours(self,cr,uid,ids,names,args,context = None):
        
        result = {}
        rec_adjust = {}
        for f in self.browse(cr,uid,ids):
            if float(f.total_timesheet) > float(f.schedule_shift) and f.bank_it:
                result[f.id] = float(f.total_timesheet) - float(f.schedule_shift)
                bank_value = result[f.id]
                adjust_id = self.pool.get('attendance.adjustment.lines').search(cr, uid, [('timesheet_idd','=',f.id)])
                if adjust_id:
                    rec_adjust = self.pool.get('attendance.adjustment.lines').browse(cr,uid,adjust_id[0])
                for adj in rec_adjust:
                    result[f.id] = bank_value - adj.input_hours
 
        return result
    
    _columns = { 
                'display_total_timesheet': fields.float('Total Timesheet'),
                'bank_it': fields.boolean('Bank My Overtime'),
               'adjustment_ids':fields.one2many('attendance.adjustment.lines','timesheet_idd','Adjustment'),
               'total_overtime':fields.function(get_total_overtime, method=True, string='Overtime',type='float'),
               'total_hours_this_timesheet':fields.function(get_net_hours_this_timesheet, method=True, string='Net Hours (This Timesheet)',type='float'),
               'hours_bank_ids':fields.one2many('employee.hours.bank','timesheet_id','Hours Bank'),
               'schedule_shift':fields.float('Scheduled Shift'),
               'over_under_time':fields.function(get_total_banked_overtime, method=True, string='Total Overtime',type='float'),
               'banked_hours':fields.function(get_banked_hours, method=True, string='Banked Hours',type='float'),
	           'week_no':fields.function(get_week_no,method=True, string = "Week",type= 'char'),
               'total_difference':fields.function(get_diff,method=True, string = "Difference",type= 'char'),
               'remarks':fields.selection([('Deficiency','Deficiency'),('Ok','Ok'),('Overtime','Overtime')],'State'),
               'overtime_status':fields.selection([('Banked','Banked'),('Encashed','Encashed'),('No-Overtime','No-Overtime')],'Overtime Status'),
        }
    _defaults = {
        'date_from':_get_week_startdate,
        'date_to': _get_week_enddate,
        'schedule_shift': 40.00,
    }

hr_timesheet_sheet()
  #-------------------------------------------------------------------------------------------------------------------------
  
class attendance_adjustment_lines(osv.osv):
    
    
    # Created by Obaid
    def create(self, cr, uid, vals, context=None, check=True):
        result = super(osv.osv, self).create(cr, uid, vals, context)
        rec = self.browse(cr,uid,result)
        rec_timesheet = self.pool.get('hr_timesheet_sheet.sheet').browse(cr,uid,rec.timesheet_idd.id)
        
#        if rec_timesheet.total_timesheet < rec_timesheet.schedule_shift:
            
        if rec_timesheet.over_under_time >= vals['input_hours']:
              
                adjustment_check = vals['input_hours'] + rec_timesheet.total_timesheet
                
                if adjustment_check >= rec_timesheet.schedule_shift: 
                    
#                    if adjustment_check > rec_timesheet.schedule_shift:
                        
 #                       raise osv.except_osv(('Hours Exceeded'),('you need to have hours equal to your schedule shift!'))
#                    else:
#                         rec_timesheet.total_timesheet = rec_timesheet.total_timesheet + rec.input_hours
                        self.pool.get('employee.hours.bank').create(cr,uid,{'employee_id':rec_timesheet.employee_id.id,'debit':0, 'credit': rec.input_hours, 'description': 'Deficiency Adjusted', 'timesheet_id': rec.timesheet_idd.id})
#                         adjust_id = self.pool.get('hr_timesheet_sheet.sheet.day').search(cr, uid, [('sheet_id','=',rec.timesheet_idd.id)])
#                         print("---------------------  YOUR REQUIRED ID is   --------------------- ", adjust_id)
#                         self.pool.get('hr_timesheet_sheet.sheet.day').write(cr,uid,adjust_id,{'total_timesheet':adjustment_check})
                        
#                         print("---------------------  YOUR REQUIRED ID is   --------------------- ", adjust_id)
#                         vals ['duration'] = rec_timesheet.date_from + " to "+rec_timesheet.date_to
#                         vals ['regular_hours'] = 40
# #                         vals ['over_under_time'] = rec_timesheet.over_under_time - vals['input_hours']
#                         vals ['state'] = rec_timesheet.remarks 
#                         self.write(cr, uid, result, vals)
                else:
                    raise osv.except_osv(('Add more Hours'),('you need to have hours equal to your schedule shift!'))
        else:
            raise osv.except_osv(('Not Enough Hours'),('You do not have hours in your hours bank!'))
#        else:
#            raise osv.except_osv(('No Need For Adjustment'),('You already have adequate hours in timesheet!'))









#         previous_input = 0
#         for timesheet in rec_timesheet:
#             previous_input = previous_input+ abs(timesheet.over_under_time)
#         for att in rec:
#             adjustment_input = rec.input_hours
#             if adjustment_input + previous_input > rec_timesheet.over_under_time:
#                 raise osv.except_osv(('Input Hours Exceeds'),('Your adjustment hours increase for total OT/UT.'))
#             if rec_timesheet.remarks == 'Deficiency':
#                 if vals['over_time_adjustemnt'] != 'adjust_from_bank':
#                     raise osv.except_osv(('Wrong Decision'),('You must adjust your hours from bank'))
#             elif rec_timesheet.remarks == 'Overtime' or rec_timesheet.remarks == 'Ok':
#                     if vals['over_time_adjustemnt'] == 'adjust_from_bank':
#                         raise osv.except_osv(('Wrong Decision'),('Your must Bank your hours, to get Paid.'))
#                 
#                 
       
        return vals
   
   
   
    def write(self, cr, uid, ids, vals, context=None, check=True, update_check=True):

        for f in self.browse(cr,uid,ids):
            adjustment_id = self.pool.get('hr_timesheet_sheet.sheet').search(cr,uid,[('id','=',f.timesheet_idd.id)])
            timesheet_rec = self.pool.get('hr_timesheet_sheet.sheet').browse(cr, uid, adjustment_id)
            if adjustment_id:
                bank_id = self.pool.get('employee.hours.bank').search(cr,uid,[('timesheet_id','=',f.timesheet_idd.id)])
                bank_adjustment = self.pool.get('employee.hours.bank').browse(cr,uid,bank_id)
                
                for adjustment in bank_adjustment:
                    print("--------------------- Adjusted Hours on Write method in Adjustment ------------------------ ", timesheet_rec.total_difference, vals['input_hours'])
                    if timesheet_rec.over_under_time >= vals['input_hours']:
                        print("--------------------- Adjusted Hours on Write method in Adjustment ------------------------ ", timesheet_rec.over_under_time, vals['input_hours'])
                        if adjustment.credit > 0:
                            self.pool.get('employee.hours.bank').write(cr,uid,adjustment.id,{'debit':0, 'credit': vals['input_hours']})
                    else:
                        raise osv.except_osv(('Not Enough Hours'),('You do not have enough hours in your hours bank for this Adjustment!'))   
                        
                adjustment_rec = self.pool.get('hr_timesheet_sheet.sheet').browse(cr,uid,adjustment_id)
                for adjustment in adjustment_rec:
                    
                    adjustment_check = adjustment.total_timesheet + vals['input_hours']
                    print("--------------------- Adjusted Hours on Write method in Adjustment ------------------------ ", adjustment_check, vals['input_hours'])
#                     if adjustment_check > adjustment.schedule_shift:
#                         raise osv.except_osv(('Hours Exceeded'),('you need to have hours equal to your schedule shift!'))
                    if adjustment_check < adjustment.schedule_shift:
                        raise osv.except_osv(('Add more Hours'),('you need to have hours equal to your schedule shift!'))
        vals ['duration'] = timesheet_rec.date_from + " to "+timesheet_rec.date_to
        vals ['regular_hours'] = 40
#                         vals ['over_under_time'] = rec_timesheet.over_under_time - vals['input_hours']
        vals ['state'] = timesheet_rec.remarks      
        result = super(osv.osv, self).write(cr, uid, ids, vals, context)
        return result
   
   
    # Created by Obaid
    def unlink(self, cr, uid, ids, context=None):
        
        for f in self.browse(cr,uid,ids):
            print("analytic_timesheet:deleting record= : %r", f.timesheet_idd.id)
            
            bank_ids = self.pool.get('employee.hours.bank').search(cr, uid, [('timesheet_id','=',f.timesheet_idd.id)])
            for rec in bank_ids:
                self.pool.get('employee.hours.bank').unlink(cr,uid,rec)
            timesheet_rec = self.pool.get('hr_timesheet_sheet.sheet').browse(cr, uid, f.timesheet_idd.id)
            print("Timesheet Record --------------------- ", timesheet_rec)
            display_timesheet = timesheet_rec.total_timesheet
            new_display_timesheet = display_timesheet - f.input_hours
            self.pool.get('hr_timesheet_sheet.sheet').write(cr,uid,f.timesheet_idd.id,{'total_timesheet': new_display_timesheet})
            
        result = super(osv.osv, self).unlink(cr, uid, ids, context)
            
        return result    
    
    
    
    def default_get(self, cr, uid, fields, context=None):
        if context is None:
            context = {}
        res = super(attendance_adjustment_lines, self).default_get(cr, uid, fields, context)
#         if context.get('parent_id'):
        parent_id = context.get('active_ids',[])
        if parent_id:
#              parent_id = context['parent_id']
             rec_ts = self.pool.get('hr_timesheet_sheet.sheet').browse(cr,uid,parent_id)
             res['duration'] = rec_ts.date_from + " to "+rec_ts.date_to
             res['regular_hours'] = 40
             res['over_under_time'] = rec_ts.total_attendance - 40
             res['timesheet_idd'] = rec_ts.id
             res['state'] = rec_ts.remarks
        return res
    
    def onchange_input_hours(self, cr, uid, timesheet_id1, input_hours):
        vals = {}
        rec_ts = self.pool.get('hr_timesheet_sheet.sheet').browse(cr,uid,timesheet_id1)
        child_ids = self.search(cr,uid,[('timesheet_idd','=',timesheet_id1)])
        if child_ids:
            total_input = 0
            rec_self = self.browse(cr,uid,child_ids)
            for att in rec_self:
                total_input = total_input + att.input_hours
            if input_hours > total_input:
                vals['input_hours'] = 0
        else:
             if input_hours > rec_ts.total_attendance:
                vals['input_hours'] = 0         
        return {'value':vals}
    
    def onchange_decision(self, cr, uid,ids, decision,state):
        vals = {}
        if state =='Overtime' or state =='Ok':
            if decision == 'adjust_from_bank':
                vals['over_time_adjustemnt'] =  None
        elif state =='Deficiency':
            if decision == 'Bank_vertime':      
                vals['over_time_adjustemnt'] =  None
            elif decision == 'Paid':  
                vals['over_time_adjustemnt'] =  None
        return {'value':vals}
    
    _name = "attendance.adjustment.lines"
    _columns = {
        'duration':fields.char('Duration',size = 100,readonly = True),
        'timesheet_idd': fields.many2one('hr_timesheet_sheet.sheet','Time Sheet',readonly = True),
        'regular_hours':fields.float('Regular'),
        'over_under_time':fields.float('OT/UT'),
        'input_hours':fields.float('Adjustment'),
        'over_time_adjustemnt':fields.selection([('Paid','Get Paid')], 'Decision', required=True),
        'state':fields.selection([('Deficiency','Deficiency'),('Ok','Ok'),('Overtime','Overtime')],'State'),
        'reconcile':fields.boolean('reconcile')
    }
    _defaults ={
        'over_time_adjustemnt': 'Paid',
    }
    
attendance_adjustment_lines()

class hr_expense_expense(osv.osv):
    
    def expense_accept(self, cr, uid, ids, context=None):
        super(hr_expense_expense, self).expense_accept(cr, uid, ids, context)
        for f in self.browse(cr,uid,ids):
            expenselines_ids = self.pool.get('hr.expense.line').search(cr, uid, [('expense_id','=',f.id)])
#             rec_expline =  self.pool.get('hr.expense.line').browse(cr,uid,f.id)
            if expenselines_ids:
                    
                #step 2 create entry in project expense lines table
                rec_expline =  self.pool.get('hr.expense.line').browse(cr,uid,expenselines_ids)
                for expline in rec_expline:
                    print "project in expense line",expline.project_id.id
#                     exists = self.pool.get('project.expenses').search(cr, uid, [('expense_id','=',f.id)])
#                     if not exists:
                    self.pool.get('project.expenses').create(cr,uid,{'expense_id':f.id,'project_id':expline.project_id.id})
                   
                    expline_id = self.pool.get('prj.billing.expenseline').create(cr,uid,{'expenseline_id':expline.id,'project_id':expline.project_id.id})

                    #step 3 also create record in another project expense table
                    self.pool.get('project.expenses.incurred').create(cr,uid,{'related_expense_id':expline_id,'name':expline.project_id.id})


        return self.write(cr, uid, ids, {'state': 'accepted', 'date_valid': time.strftime('%Y-%m-%d'), 'user_valid': uid}, context=context)
    
    def expense_canceled(self, cr, uid, ids, context=None):
        super(hr_expense_expense, self).expense_canceled(cr, uid, ids, context)
        for f in self.browse(cr,uid,ids):
            exists = self.pool.get('project.expenses').search(cr, uid, [('expense_id','=',f.id)])
            if  exists:
                for each_exp in exists:
                    
                    self.pool.get('project.expenses').unlink(cr,uid,each_exp)
            #step 2: delete from prj.billing.expenselines
            expenselines_ids = self.pool.get('hr.expense.line').search(cr, uid, [('expense_id','=',f.id)])
            if expenselines_ids:
                for expline in expenselines_ids:
                    deleting_ids = self.pool.get('prj.billing.expenseline').search(cr,uid,[('expenseline_id','=',expline)])
                    for this_id in deleting_ids:
                        self.pool.get('prj.billing.expenseline').unlink(cr,uid,this_id)
             
        
        return self.write(cr, uid, ids, {'state': 'cancelled'}, context=context)
    
    def unlink(self, cr, uid, ids, context=None):
        
        for f in self.browse(cr,uid,ids):
            exp_ids = self.pool.get('project.expenses').search(cr, uid, [('expense_id','=',f.id)])
            for g in exp_ids:
                self.pool.get('project.expenses').unlink(cr,uid,g)
        result = super(hr_expense_expense, self).unlink(cr, uid, ids, context)
            
        return result 
		
    def _amount(self, cr, uid, ids, field_name, arg, context=None):
        res= {}
        for expense in self.browse(cr, uid, ids, context=context):
            total = 0.0
            for line in expense.line_ids:
                total += line.unit_amount + line.taxes_paid
            res[expense.id] = total
        return res 
		
    def _get_expense_from_line(self, cr, uid, ids, context=None):
        return [line.expense_id.id for line in self.pool.get('hr.expense.line').browse(cr, uid, ids, context=context)]
    def _amount_tax(self, cr, uid, ids, field_name, arg, context=None):
        res= {}
        for expense in self.browse(cr, uid, ids, context=context):
            total = 0.0
            for line in expense.line_ids:
                total += line.taxes_paid
            res[expense.id] = total
        return res
	# at present we omitted calling this method because of a conflit with child object
    def onchange_rpjmanager(self, cr, uid, ids, project_id,dept_id):
        res =  {}
        _logger.info("%%%%%%%%%%%%%%%%%% expense onchange called project id : %s",project_id)
        
        if project_id:
            mgr = self.pool.get('project.project').browse(cr, uid,project_id).project_manager.id
            _logger.info("Project Manager : %s",mgr)
        elif dept_id:
             mgr = self.pool.get('hr.department').browse(cr, uid,dept_id).manager_id.id
             _logger.info("Department Manager: %s",mgr)
        else:
            mgr = None 
        _logger.info("final manager  %s",mgr)
        res['value'] = {'pro_manager': mgr}
        return res	
    
    def onchange_rpjmanager_dept(self, cr, uid, ids, project_id,dept_id):
        res =  {}
        _logger.info("%%%%%%%%%%%%%%%%%% onchange dept called departmen  id : %s",dept_id)
        
        if project_id:
            mgr = self.pool.get('project.project').browse(cr, uid,project_id).project_manager.id
            _logger.info("Project Manager : %s",mgr)
        elif dept_id:
             mgr = self.pool.get('hr.department').browse(cr, uid,dept_id).manager_id.id
             _logger.info("Department Manager: %s",mgr)
        else:
            mgr = None 
        _logger.info("final manager  %s",mgr)
        res['value'] = {'pro_manager': mgr}
        return res    
    
    def _get_expense_from_line_tax(self, cr, uid, ids, context=None):
        return [line.expense_id.id for line in self.pool.get('hr.expense.line').browse(cr, uid, ids, context=context)]
   
    def _reporting_office(self, cr, uid, ids,field_names, context=None, check=True):
        """ """
        result = {}
        for f in self.browse(cr, uid, ids, context=context):
                    street = f.employee_id.address_id.street or ''
                    city =  f.employee_id.address_id.city or ''
                    zip =  f.employee_id.address_id.zip
                    result[f.id] = str(street)+" "+str(city)+" "+str(zip)+","+str(f.employee_id.address_id.country_id.name or None)
        return result
    def onchange_address_id(self, cr, uid, ids, address, context=None):
        if address:
            address = self.pool.get('res.partner').browse(cr, uid, address, context=context)
            return {'value': {'work_phone': address.phone, 'mobile_phone': address.mobile}}
        return {'value': {}}
    
    def default_get(self, cr, uid, fields, context=None):
        if context is None:
            context = {}
        res = super(hr_expense_expense, self).default_get(cr, uid, fields, context=context)
        if 'employee_id' in fields:
            manager = self.pool.get('hr.employee').browse(cr,uid,res['employee_id']).parent_id.id
            res.update({'pro_manager': manager})
        return res
   
    _name = 'hr.expense.expense'
    _inherit = "hr.expense.expense"
    _columns = {
    'reporting_office':fields.many2one('res.partner',string='Reporting Office', readonly=False),
    #'reporting_office':fields.function(_reporting_office,  method=True, string='Reporting Office',type='char'), 
	'pro_manager':fields.many2one('hr.employee', string='Expense Manager'),
	'date': fields.datetime('Date', select=True, readonly=True, states={'draft':[('readonly',False)], 'confirm':[('readonly',False)]}),
    'date_valid': fields.datetime('Validation Date', select=True, copy=False, help="Date of the acceptation of the sheet expense. It's filled when the button Accept is pressed."),
    'amount': fields.function(_amount, string='Total Amount', digits_compute=dp.get_precision('Account'), 
        store={
            'hr.expense.line': (_get_expense_from_line, ['unit_amount','taxes_paid'], 10)
        }),
    'amount_tax': fields.function(_amount_tax, string='Total Taxes', digits_compute=dp.get_precision('Account'), 
        store={
            'hr.expense.line': (_get_expense_from_line_tax, ['taxes_paid'], 10)
        })
	}
    _defaults ={
        'date':datetime.now(),
        
    }
hr_expense_expense()

class budget_tag(osv.osv):
    _name = "budget.tag"
    _columns = {
        'name': fields.char('Budget Tag',size = 100),
        'desc': fields.char('Description',size = 150),
            }
    _sql_constraints = [
        ('Duplicated', 'unique (name)', 'Budget Tag, Already exists')
    ]

budget_tag()

class expense_type(osv.osv):
    _name = "expense.type"
    _columns = {
        'name': fields.char('Expense Type Name',size = 100),
        'desc': fields.char('Description',size = 150),
            }
    _sql_constraints = [
        ('Duplicated', 'unique (name)', 'Expense Type Name, Already exists')
    ]

expense_type()

class ocl_hr_expense(osv.osv):
     
       
    def calc_amount(self, cr, uid, ids, name, args, context=None):
        result = {}
       
        for f in self.browse(cr, uid, ids, context=context):
            result[f.id] = (f.unit_amount + f.taxes_paid)
        return result
    
    def seteax(self, cr, uid, ids, name, args, context=None):
        result = {}
       
        for f in self.browse(cr, uid, ids, context=context):
            result[f.id] = (f.unit_amount * 0.13)
        return result
    _inherit = "hr.expense.line"
    _columns = {
#        'taxes_paid': fields.function(seteax, method=True, string='Taxes Paid By',type='float'),
        'project_id': fields.many2one('project.project'),
        'credit_card': fields.boolean('Credit Card'),
        'taxes_paid': fields.float('Taxes Paid'),
        'receipt_no': fields.char('Attached Receipt #'),
		'budget_tags':fields.many2many('budget.tag',string ='Budget Tag'),
		'expense_types':fields.many2one('expense.type',string ='Expense Type'),
        'total_amount': fields.function(calc_amount, string='Total', digits_compute=dp.get_precision('Account')),
        
		#taxes_paid = unit_amount * 0.13
		#total_amount = taxes_paid + unit_amount
    }

    _defaults ={
        'taxes_paid': 0.0
    }

ocl_hr_expense()

class project_expenses(osv.osv):
    
    def expense_heads(self, cr, uid, ids,field_names, context=None, check=True):
        """ """
        result = {}
        for f in self.browse(cr, uid, ids, context=context):
            result[f.id] = {}
            if type(field_names) is not list:
                field_names = [field_names]
            for key_str in field_names:
                result[f.id][key_str] = '0.0'
            expense = self.pool.get('hr.expense.expense').search(cr, uid, [('id','=',f.expense_id.id)])
            if expense:
                obj = self.pool.get('hr.expense.expense').browse(cr,uid,expense[0])
            
                if 'expensed_by' in field_names:
                    result[f.id]['expensed_by'] = obj.employee_id.name 
                if 'expdate' in field_names:
                    result[f.id]['expdate'] = obj.date
                if 'desc' in field_names:
                    result[f.id]['desc'] = obj.name
                
               
        _logger.info("==============Furbiushirng Expense Tab================= : %s",result)
        return result
    
    def expense_lines(self, cr, uid, ids,field_names, context=None, check=True):
        """ """
        result = {}
        for f in self.browse(cr, uid, ids, context=context):
            result[f.id] = {}
            if type(field_names) is not list:
                field_names = [field_names]
                
            
            total_amount = 0
            total_amount_taxed = 0
            exlines = self.pool.get('hr.expense.line').search(cr, uid, [('project_id','=',f.project_id.id)])
            if exlines:
                for key_str in field_names:
                    result[f.id][key_str] = 0.0

                if 'flight'  in field_names:
                    flightid =  self.pool.get('expense.type').search(cr, uid, [('name','=','Flight')])
                    print "found flight id..................................",flightid
                    if flightid:
                        flightines = self.pool.get('hr.expense.line').search(cr, uid, [('expense_types','=',flightid[0]),('project_id','=',f.project_id.id)])
                        if flightines:
                            flighttrec = self.pool.get('hr.expense.line').browse(cr,uid,flightines[0])
                            result[f.id]['flight'] = flighttrec.unit_amount
                            print "flight from dictionary", result[f.id]['flight']
                            print "project id",f.project_id.id
                            print "record id",flighttrec.id
                            total_amount = total_amount + int(flighttrec.unit_amount)
                #.................................................................................................................................................#
                if 'hotel'  in field_names:
                    hotelid =  self.pool.get('expense.type').search(cr, uid, [('name','=','Hotel')])
                    if hotelid:
                        hotelines = self.pool.get('hr.expense.line').search(cr, uid, [('expense_types','=',hotelid[0])])
                        if hotelines:
                            hoteltrec = self.pool.get('hr.expense.line').browse(cr,uid,hotelines[0])
                            result[f.id]['hotel'] = hoteltrec.unit_amount
                #.................................................................................................................................................#
                if 'meals'  in field_names:
                    
                    mealid =  self.pool.get('expense.type').search(cr, uid, [('name','=','Meals')])
                    print "found meallllllllllllllllllllllllllllls",mealid
                    mealid
                    if mealid:
                        meallines = self.pool.get('hr.expense.line').search(cr, uid, [ ('expense_types','=',mealid[0]),('project_id','=',f.project_id.id)])
                        if meallines:
                            mealtrec = self.pool.get('hr.expense.line').browse(cr,uid,meallines[0])
                            result[f.id]['meals'] = mealtrec.unit_amount
                            print "meal from dictionary",result[f.id]['meals']
                            print "project id",f.project_id.id
                            print "record id",mealtrec.id
                            total_amount = total_amount + int(mealtrec.unit_amount)
                #..................................................................................................................................................#
                if 'transport'  in field_names:
                    transportlid =  self.pool.get('expense.type').search(cr, uid, [('name','=','Transport')])
                    if transportlid:
                        transportllines = self.pool.get('hr.expense.line').search(cr, uid, [ ('expense_types','=',transportlid[0]),('project_id','=',f.project_id.id)])
                        if transportllines:
                            transportrec = self.pool.get('hr.expense.line').browse(cr,uid,transportllines[0])
                            result[f.id]['transport'] = transportrec.unit_amount
                #..................................................................................................................................................#
                if 'telecom'  in field_names:
                    telecomid =  self.pool.get('expense.type').search(cr, uid, [('name','=','Telecom')])
                    if telecomid:
                        telecomlines = self.pool.get('hr.expense.line').search(cr, uid, [ ('expense_types','=',telecomid[0]),('project_id','=',f.project_id.id)])
                        if telecomlines:
                            telecomtrec = self.pool.get('hr.expense.line').browse(cr,uid,telecomlines[0])
                            result[f.id]['telecom'] = telecomtrec.unit_amount
                #...................................................................................................................................................#
                if 'material'  in field_names:
                    materiallid =  self.pool.get('expense.type').search(cr, uid, [('name','=','Material')])
                    if materiallid:
                        materiallines = self.pool.get('hr.expense.line').search(cr, uid, [ ('expense_types','=',materiallid[0]),('project_id','=',f.project_id.id)])
                        if materiallines:
                            materialtrec = self.pool.get('hr.expense.line').browse(cr,uid,materiallines[0])
                            result[f.id]['material'] = materialtrec.unit_amount
                #....................................................................................................................................................#
                if 'tools'  in field_names:
                    toolslid =  self.pool.get('expense.type').search(cr, uid, [('name','=','Tools')])
                    if toolslid:
                        toolslines = self.pool.get('hr.expense.line').search(cr, uid, [ ('expense_types','=',toolslid[0]),('project_id','=',f.project_id.id)])
                        if toolslines:
                            toolstrec = self.pool.get('hr.expense.line').browse(cr,uid,toolslines[0])
                            result[f.id]['tools'] = toolstrec.unit_amount
                #...................................................................................................................................................#
                if 'fleet'  in field_names:
                    fleetid =  self.pool.get('expense.type').search(cr, uid, [('name','=','Fleet')])
                    if fleetid:
                        fleetlines = self.pool.get('hr.expense.line').search(cr, uid, [ ('expense_types','=',fleetid[0]),('project_id','=',f.project_id.id)])
                        if fleetlines:
                            fleettsrec = self.pool.get('hr.expense.line').browse(cr,uid,fleetlines[0])
                            result[f.id]['fleet'] = fleettsrec.unit_amount
                #..................................................................................................................................................#
                if 'parking'  in field_names:
                    parkingid =  self.pool.get('expense.type').search(cr, uid, [('name','=','Parking')])
                    if parkingid:
                        parkinglines = self.pool.get('hr.expense.line').search(cr, uid, [ ('expense_types','=',parkingid[0]),('project_id','=',f.project_id.id)])
                        if parkinglines:
                            parkingtrec = self.pool.get('hr.expense.line').browse(cr,uid,parkinglines[0])
                            result[f.id]['parking'] = parkingtrec.unit_amount
                #..................................................................................................................................................#
                if 'misc'  in field_names:
                    miscid =  self.pool.get('expense.type').search(cr, uid, [('name','=','Misc')])
                    if miscid:
                        misclines = self.pool.get('hr.expense.line').search(cr, uid, [ ('expense_types','=',miscid[0]),('project_id','=',f.project_id.id)])
                        if misclines:
                            misctrec = self.pool.get('hr.expense.line').browse(cr,uid,misclines[0])
                            result[f.id]['misc'] = misctrec.unit_amount
                #...................................................................................................................................................#
                if 'public'  in field_names:
                    publicid =  self.pool.get('expense.type').search(cr, uid, [('name','=','Public Transit & Tolls')])
                    if publicid:
                        publicidlines = self.pool.get('hr.expense.line').search(cr, uid, [ ('expense_types','=',publicid[0]),('project_id','=',f.project_id.id)])
                        if publicidlines:
                            misctrec = self.pool.get('hr.expense.line').browse(cr,uid,publicidlines[0])
                            result[f.id]['public'] = misctrec.unit_amount
                #...................................................................................................................................................#
                if 'travel'  in field_names:
                    travelid =  self.pool.get('expense.type').search(cr, uid, [('name','=','Travel Per Diem')])
                    if travelid:
                        travellines = self.pool.get('hr.expense.line').search(cr, uid, [ ('expense_types','=',travelid[0]),('project_id','=',f.project_id.id)])
                        if travellines:
                            misctrec = self.pool.get('hr.expense.line').browse(cr,uid,travellines[0])
                            result[f.id]['travel'] = misctrec.unit_amount
                #...................................................................................................................................................#
                if 'personal'  in field_names:
                    personalid =  self.pool.get('expense.type').search(cr, uid, [('name','=','Personal Car KMs usage')])
                    if personalid:
                        personallines = self.pool.get('hr.expense.line').search(cr, uid, [ ('expense_types','=',personalid[0]),('project_id','=',f.project_id.id)])
                        if personallines:
                            misctrec = self.pool.get('hr.expense.line').browse(cr,uid,personallines[0])
                            result[f.id]['personal'] = misctrec.unit_amount
                #...................................................................................................................................................#
                if 'mileage'  in field_names:
                    mileageid =  self.pool.get('expense.type').search(cr, uid, [('name','=','Mileage Reimbursement')])
                    if mileageid:
                        mileagelines = self.pool.get('hr.expense.line').search(cr, uid, [ ('expense_types','=',mileageid[0]),('project_id','=',f.project_id.id)])
                        if mileagelines:
                            misctrec = self.pool.get('hr.expense.line').browse(cr,uid,mileagelines[0])
                            result[f.id]['mileage'] = misctrec.unit_amount
                #...................................................................................................................................................#
                if 'cash'  in field_names:
                    cashid =  self.pool.get('expense.type').search(cr, uid, [('name','=','Cash Advance')])
                    if cashid:
                        cashlines = self.pool.get('hr.expense.line').search(cr, uid, [ ('expense_types','=',cashid[0]),('project_id','=',f.project_id.id)])
                        if cashlines:
                            misctrec = self.pool.get('hr.expense.line').browse(cr,uid,cashlines[0])
                            result[f.id]['cash'] = misctrec.unit_amount
                #...................................................................................................................................................#
                #...................................................................................................................................................#
#                if 'taxes'  in field_names:
#                    taxesid =  self.pool.get('expense.type').search(cr, uid, [('name','=','Taxes')])
#                    if taxesid:
#                        taxeslines = self.pool.get('hr.expense.line').search(cr, uid, [ ('expense_types','=',taxesid[0])])
#                        if taxeslines:
#                            taxestrec = self.pool.get('hr.expense.line').browse(cr,uid,taxeslines[0])
#                            result[f.id]['taxes'] = taxestrec.unit_amount
                if 'total'  in field_names:
                    result[f.id]['total'] = total_amount
                if 'taxes'  in field_names:
                    result[f.id]['taxes'] = total_amount_taxed
           
        _logger.info("==============Furbiushirng lines tab in project expense================= : %s",result)
        return result
    
    
    _name = "project.expenses"
    _columns = {
        'expense_id': fields.many2one('hr.expense.expense'),
        'expensed_by': fields.function(expense_heads,multi='expenses', store=False,  method=True, string='Expense By',type='char'),
        'project_id': fields.many2one('project.project'),
        'expdate': fields.function(expense_heads,multi='expenses', store=False,  method=True, string='Date',type='char'),
        'desc': fields.function(expense_heads,multi='expenses', store=False,  method=True, string='Description',type='char'),
        'telecom': fields.function(expense_lines,multi='expenseslines', store=False,  method=True, string='Communications',type='float'),
        'flight': fields.function(expense_lines,multi='expenseslines', store=False,  method=True, string='Flight',type='float'),
        'hotel': fields.function(expense_lines,multi='expenseslines', store=False,  method=True, string='Hotel',type='float'),
        'material': fields.function(expense_lines,multi='expenseslines', store=False,  method=True, string='Material',type='float'),
        'tools': fields.function(expense_lines,multi='expenseslines', store=False,  method=True, string='Tools',type='float'),
        'public': fields.function(expense_lines,multi='expenseslines', store=False,  method=True, string='Public Transit & Tolls',type='float'),
        'parking': fields.function(expense_lines,multi='expenseslines', store=False,  method=True, string='Parking',type='float'),
        'fleet': fields.function(expense_lines,multi='expenseslines', store=False,  method=True, string='Fleet Gas & Maintenance',type='float'),
        'transport': fields.function(expense_lines,multi='expenseslines', store=False,  method=True, string='Car Rental, Taxi & Fuel',type='float'),
        'travel': fields.function(expense_lines,multi='expenseslines', store=False,  method=True, string='Travel Per Diem',type='float'),
        'misc': fields.function(expense_lines,multi='expenseslines', store=False,  method=True, string='Miscellaneous',type='float'),
        'personal': fields.function(expense_lines,multi='expenseslines', store=False,  method=True, string='Personal Car KMs usage',type='float'),
        'mileage': fields.function(expense_lines,multi='expenseslines', store=False,  method=True, string='Mileage Reimbursement',type='float'),
        'meals': fields.function(expense_lines,multi='meals', store=False,  method=True, string='Meals & Entertainment',type='float'),
        'cash': fields.function(expense_lines,multi='expenseslines', store=False,  method=True, string='Cash Advance',type='float'),
        'taxes': fields.function(expense_lines,multi='expenseslines', store=False,  method=True, string='Taxes',type='float'),
        'total': fields.function(expense_lines,multi='expenseslines', store=False,  method=True, string='Total Charged',type='float'),
            }

project_expenses()



class form_underconstruction(osv.osv):
    
    def _get_week_startdate(self,cr,uid,ids):
        import time
        company = self.pool.get('res.users').browse(cr,uid,uid).company_id.id
        return company
    
    _name = 'form.underconstruction'
    _columns = {
                 'company':fields.many2one('res.company','Company'),
                 'pic': fields.related('company','pic',type='binary', string='image', readonly=True),
                
                }
    _defaults = {'company': _get_week_startdate}
    
form_underconstruction()

class project_task_type(osv.osv):
    _name = 'project.task.type'
    _description = 'Task Stage modified'
    _inherit = 'project.task.type'
    _columns = {
        'stage_for': fields.selection([('Task','Task'),
                                   ('Issues','Issues')
                                  ],
                                  'Stage For', required=True),
    }
    _defaults = {'case_default': True}

project_task_type() 

class hr_analytic_timesheet(osv.osv):
    #appeers as O2m to class hr_timesheet_sheet, this is modefied to add project,task and activity
   
    def on_change_unit_amount(self, cr, uid, id, prod_id, unit_amount, company_id, unit=False, journal_id=False, context=None):
        res = {}
        #res = super(hr_analytic_timesheet, self).on_change_unit_amount(cr, uid, id, prod_id, unit_amount, company_id, unit=False, journal_id=1, context=None)
        return res
    
    _name = "hr.analytic.timesheet"
    _table = 'hr_analytic_timesheet'
    _description = "Timesheet Line"
    _inherit = 'hr.analytic.timesheet'

    def onchange_task(self, cr, uid, ids, task_id):
        res =  {}
        res = {'domain': {'activity_id': [('task_id', '=',task_id)]}}
        return res

    def on_change_timesheet_project_id(self, cr, uid, ids, project_id):
        res =  {}
        rec_project = self.pool.get('project.project').browse(cr,uid,project_id)
        res = {'domain': {'task_id': [('project_id', '=', project_id)]}}
        res['value'] = {'account_id':rec_project.analytic_account_id.id}
        return res
        
        
        

    def create(self, cr, uid, vals, context=None, check=True):
        print vals['unit_amount']
        
        if 'unit_amount' in vals:
            hours = vals['unit_amount']
        else:
            hours = 0
            
        if 'activity_id' in vals:
            activity_id = vals['activity_id']
            activty_rec = self.pool.get('project.task.work').browse(cr, uid, activity_id)
            _logger.info("activity id............ %d",activity_id)
            existing_hours = int(activty_rec.hours)
            _logger.info("Exting hours............ %d",existing_hours)
            new_hours = existing_hours + int(hours)
            _logger.info("New hours............ %d",hours)
            _logger.info("resulting new hours........... %d",new_hours)
            self.pool.get('project.task.work').write(cr,uid,activity_id,{'hours':new_hours}) 
        result = super(hr_analytic_timesheet, self).create(cr, uid, vals, context)
        return result
    
    def write(self, cr, uid, ids, vals, context=None, check=True, update_check=True):
        for f in self.browse(cr, uid, ids, context=context):
            if 'unit_amount' in vals:
                act_hrs = f.activity_id.hours
                ts_old_hrs = f.unit_amount
                diff = vals['unit_amount'] - ts_old_hrs
                new_act_hrs = act_hrs + diff
                self.pool.get('project.task.work').write(cr,uid,f.activity_id.id,{'hours':new_act_hrs})
        result = super(osv.osv, self).write(cr, uid, ids, vals, context)
        return result
    
    def unlink(self, cr, uid, ids, context=None):
            for f in self.browse(cr,uid,ids):
                _logger.info("analytic_timesheet:deleting record= : %r", f.id)
                activty_rec = self.pool.get('project.task.work').browse(cr, uid, f.activity_id.id)
                existing_hours = int(activty_rec.hours)
                deleting_hours = f.line_id.unit_amount or 0
                new_hours = existing_hours - int(deleting_hours)
                self.pool.get('project.task.work').write(cr,uid,f.activity_id.id,{'hours':new_hours})
            result = super(osv.osv, self).unlink(cr, uid, ids, context)
            return

    def set_default_domin_project(self, cr, uid, ids):
        # sets domain on projects for current user during selections
        print "domain on defgaulter of projects................................"
        res =  {}
        sql = """SELECT project_id from project_user_rel where uid =  """+str(uid)
        cr.execute(sql)
        proj = cr.fetchall()
        projects = str(tuple(proj)).replace(',)', ')')
        print "found total:",str(tuple(proj)).replace(',)', ')')
        print "after formating",
        res = {'domain': {'project_id': [('id', 'in', projects)]}}
        return res
    
    """ Method for calcualtion of time difference for filling hours field in timesheet"""
    def set_onchange_endtime(self, cr, uid, ids, start_time, end_time):
        res = {}
        res['value'] = {'unit_amount': end_time - start_time}
        return res   
    
    
    _columns = {
                
        'project_id': fields.many2one('project.project', 'Project'),
        #project id is not used, instead project analytic account id is sued analytic_account_id is the column in project table, 
        # view of hr_analytic_timesheet will be inherited, so that onchange method is imposed on it, which will then set domains for task and actitivty
        'task_id': fields.many2one('project.task', 'Task'),
        'activity_id': fields.many2one('project.task.work', 'Activity'),
        'sheet_id': fields.many2one('hr_timesheet_sheet.sheet', 'Paren Time sheet'),
        'comments': fields.text('Notes'),
        'start_time': fields.float('Start Time'),
        'end_time': fields.float('End Time'),
    }
    _defaults = {
                 'project_id':  set_default_domin_project             
                 
    }
        
hr_analytic_timesheet()



class employee_hours_bank(osv.osv):
      
    _name = "employee.hours.bank"
    _description = "Timesheet Employee Hours"
#     _inherit = 'hr.analytic.timesheet' 
    _columns = {       
        'date_entered':fields.date('Date'),
        'description':fields.char('Description'),
        'timesheet_id':fields.many2one('hr_timesheet_sheet.sheet','Timesheet'),
        'employee_id':fields.many2one('hr.employee'),
        #week no is not needed, the m2o to timesheet id is returning the same label
        'week_num':fields.related('timesheet_id','week_no','Week No'),
        'debit':fields.float('Debit'),
        'credit':fields.float('Credit'),
        'balance':fields.float('Balance')
          
                }
    

employee_hours_bank()

