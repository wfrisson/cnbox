from openerp.osv import fields, osv
import datetime
import time
import logging
from datetime import date, datetime, timedelta
from openerp.tools import ustr, DEFAULT_SERVER_DATE_FORMAT as DF
import json
import random
import urllib2
import math
import openerp
import openerp.addons.decimal_precision as dp
from openerp import SUPERUSER_ID, tools
from openerp.tools.translate import _

_logger = logging.getLogger(__name__)

class issue_close_conclusion(osv.osv):
    _name = "issue.close.conclusion"
    _description = "Close Out Conclusion"
    _columns = {
        'name': fields.char('Conclusion',size = 100),
        'desc': fields.char('Description',size = 150),
            }
    _sql_constraints = [
        ('Duplicated', 'unique (name)', 'Conclusion, Already exists')
    ]

issue_close_conclusion ()

class issue_action_logs(osv.osv):


    _name = "issue.action.logs"
    _columns = {
        'name': fields.char('Action Required'),
        'dated':fields.date('Date'),
        'taken_by':fields.many2one('res.users','Taken by'),
        'updates': fields.text('Updates'),
        'done':fields.boolean('Done'),
        'issue_id':fields.many2one('project.issue','IssueID'),
            }
   
issue_action_logs()


class issue_transactional_log(osv.osv):
  
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
    _name = "issue.transactional.log"
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
        'project_id':fields.many2one('project.issue','IssueID'),
        'event_date': fields.datetime('Transaction Date'),
        'event_by': fields.many2one('res.users','Performed By'),
            }
   
issue_transactional_log()

class issue_type(osv.osv):
    _name = "issue.type"
    _columns = {
        'name': fields.char('Flag Type',size = 100),
        'desc': fields.char('Description',size = 150),
            }
    _sql_constraints = [
        ('Duplicated', 'unique (name)', 'Flag Type, Already exists')
    ]

issue_type()

class issue_category(osv.osv):
    _name = "issue.category"
    _columns = {
        'name': fields.char('Flag Category',size = 100),
        'desc': fields.char('Description',size = 150),
            }
    _sql_constraints = [
        ('Duplicated', 'unique (name)', 'Flag Category, Already exists')
    ]

issue_category()
class issue_resolution(osv.osv):
    _name = "issue.resolution"
    _columns = {
        'name': fields.char('Resolution',size = 100),
        'desc': fields.char('Description',size = 150),
            }
    _sql_constraints = [
        ('Duplicated', 'unique (name)', 'Resolution, Already exists')
    ]

issue_resolution()
class issue_classification(osv.osv):
    _name = "issue.classification"
    _columns = {
        'name': fields.char('Classification',size = 100),
        'desc': fields.char('Description',size = 150),
            }
    _sql_constraints = [
        ('Duplicated', 'unique (name)', 'Classification, Already exists')
    ]

issue_classification()
class issue_priority(osv.osv):
    _name = "issue.priority"
    _columns = {
        'name': fields.char('Priority',size = 100),
        'desc': fields.char('Description',size = 150),
            }
    _sql_constraints = [
        ('Duplicated', 'unique (name)', 'Priority, Already exists')
    ]

issue_priority()
class safety_safety(osv.osv):
    _name = "safety.safety"
    _columns = {
        'name': fields.char('Safety',size = 100),
        'desc': fields.char('Description',size = 150),
            }
    _sql_constraints = [
        ('Duplicated', 'unique (name)', 'Safety, Already exists')
    ]

safety_safety()
class facilities_facilities(osv.osv):
    _name = "facilities.facilities"
    _columns = {
        'name': fields.char('Facility',size = 100),
        'desc': fields.char('Description',size = 150),
            }
    _sql_constraints = [
        ('Duplicated', 'unique (name)', 'Facility, Already exists')
    ]

facilities_facilities()
class processes_processes(osv.osv):
    _name = "processes.processes"
    _columns = {
        'name': fields.char('Process',size = 100),
        'desc': fields.char('Description',size = 150),
            }
    _sql_constraints = [
        ('Duplicated', 'unique (name)', 'Process, Already exists')
    ]

processes_processes()

class project_issue(osv.osv):
    
    
    
    def case_escalate(self, cr, uid, ids, context=None):        # FIXME rename this method to issue_escalate
        for issue in self.browse(cr, uid, ids, context=context):
            data = {}
            esc_proj = issue.project_id
#             esc_proj = issue.project_id.project_escalation_id
            
#             if not esc_proj:
#                 raise osv.except_osv(_('Warning!'), _('You cannot escalate this issue.\nThe relevant Project has not configured the Escalation Project!'))

            data['project_id'] = esc_proj.id
            if esc_proj.user_id:
                data['user_id'] = esc_proj.user_id.id
            data['escalated_by'] = uid
            data['escalated_on'] = datetime.now()
            issue.write(data)
            new_msg = self.pool.get('mail.message').create(cr,uid,{
                                                    'subtype_id':11,
                                                    'subject':'New Issue Escalated', 
                                                    'date':datetime.now(),
                                                    'type':'notification',
                                                    'body':'Issue:'+issue.name,
                                                    'partner_ids':[issue.partner_id.id],
                                                    'model':'project.issue',
                                                    'notified_partner_ids':[issue.partner_id.id],
                                                     })
                
            new_mail = self.pool.get('mail.notification').create(cr,uid,{
                                                    'partner_id':issue.partner_id.id,
                                                    'message_id':new_msg
                                                     })
            
            if issue.task_id:
                issue.task_id.write({'project_id': esc_proj.id, 'user_id': False})
        return True
     
    def create(self, cr, uid, vals, context=None, check=True):
        result = super(project_issue, self).create(cr, 1, vals, context)
        return result
    def create_transactional_logs(self, cr, uid,obj, column ,post_value,operation,brow):
        """ this method creates transactional logs for project,tasks and work
        will be called from write method of project, task and work """
        _logger.info("============================Starting Project Issue Logs===(Columns:)============================= %s",column)
        _logger.info("============================Starting Project Issue Logs===(Columns:)============================= %s",post_value)
        if obj == "Issue":
            if column == 'action_logs':
                return
            elif column == 'categ_ids':
                return
            elif column == 'close_conclusion':
                return
            elif column == 'issue_classifications':
                return
            elif column == 'issue_prioritys':
                return
         
        sql="""select project_issue."""+str(column)+""" from project_issue where id="""+str(brow.id)
        cr.execute(sql)
        pre = cr.fetchone()[0]
        
        is_pre_m2o = self.pool.get('project.project').is_m2o(cr,uid,'project.project',column,pre)
        is_post_m2o = self.pool.get('project.project').is_m2o(cr,uid,'project.project',column,post_value)
        
        result = self.pool.get('issue.transactional.log').create(cr,uid,{
                                                        'object_name': obj+"("+str(brow.name)+")",
                                                        'pre_value': is_pre_m2o,
                                                        'post_value': is_post_m2o,
                                                        'operation':operation,
                                                        'column_name':column,
                                                        'project_id':brow.id,
                                                        'event_date': datetime.now(),
                                                        'event_by': uid,
                                                         }) 
 
        return result
    
    def code_get(self, cr, uid, context=None):
        type_obj = self.pool.get('project.project')
        #raise osv.except_osv(('Error'),(context.get('active_ids')))
        inv= self.browse(cr, uid, context.get('active_ids'), context=context)
        for f in inv:    
            _logger.info("PROJECT ISSUE:GET DISPOSITION:READING SELF RECORD============================= %s",str(f.name))
            _logger.info("PROJECT Category field value============================= %s",inv.issue_cate.name)
            if f.issue_cate.name =='Projects':
                type_obj = self.pool.get('project.project')
            elif  inv.issue_cate.name =='Assets':
                type_obj = self.pool.get('asset.asset')
        ids = type_obj.search(cr, uid, [])
        res = type_obj.read(cr, uid, ids, ['id', 'name'])
        return [(r['id'], r['name']) for r in res]

     
     
    def write(self, cr, uid, ids, vals, context=None, check=True, update_check=True):
          
        for f in self.browse(cr,uid,ids):
            for k, v in vals.iteritems():
                    self.create_transactional_logs(cr,uid,'Issue',k,v,'Update',f) 
                 
        result = super(project_issue, self).write(cr, uid, ids, vals, context)
        return result
     
    def onchange_ct(self, cr, uid, ids, value):
        res =  {}
        rec = self.pool.get('issue.category').browse(cr,uid,value)
        res['value'] = {'hdn_issue_cate':rec.name }
        return res
    
    def default_get(self, cr, uid, fields, context=None):
        if context is None:
            context = {}
        res = super(project_issue, self).default_get(cr, uid, fields, context=context)
        if not context.has_key('active_ids'):
            partner_id = None
        else:
            _logger.info("******* inside defaulter_get of project_iisue.Acitve itds = %s",context.get('active_ids'))
            user_id = self.pool.get('project.project').browse(cr,uid,context.get('active_ids')[0]).project_manager.id or False
            if user_id:
                partner_id = self.pool.get('res.users').browse(cr,uid,user_id).partner_id.id
                _logger.info("******* partner id = %s",partner_id)
                if 'partner_id' in fields:
                    res.update({'partner_id': partner_id})
        return res
#     _name = 'project.issue'
    _inherit = 'project.issue'
    _track = {
        'stage_id': {
            # this is only an heuristics; depending on your particular stage configuration it may not match all 'new' stages
            'project_issue.mt_issue_new': lambda self, cr, uid, obj, ctx=None: obj.stage_id and obj.stage_id.sequence <= 1,
            'project_issue.mt_issue_stage': lambda self, cr, uid, obj, ctx=None: obj.stage_id and obj.stage_id.sequence > 1,
        },
        'user_id': {
            'project_issue.mt_issue_assigned': lambda self, cr, uid, obj, ctx=None: obj.user_id and obj.user_id.id,
        },
        'kanban_state': {
            'project_issue.mt_issue_blocked': lambda self, cr, uid, obj, ctx=None: obj.kanban_state == 'blocked',
            'project_issue.mt_issue_ready': lambda self, cr, uid, obj, ctx=None: obj.kanban_state == 'done',
        },
        'escalated_on':{
            'project_issue.mt_issue_escalated': lambda self, cr, uid, obj, ctx=None: obj.escalated_on,
            }
    }
    
    _columns = {
        'project_id': fields.many2one('project.project', 'Project', track_visibility='always', select=True),
        'kanban_state': fields.selection([('normal', 'Normal'),('blocked', 'Blocked'),('done', 'Ready for next stage')], 'Kanban State',
                                         track_visibility='always',
                                         help="A Issue's kanban state indicates special situations affecting it:\n"
                                              " * Normal is the default situation\n"
                                              " * Blocked indicates something is preventing the progress of this issue\n"
                                              " * Ready for next stage indicates the issue is ready to be pulled to the next stage",
                                         required=False),
        'stage_id': fields.many2one ('project.task.type', 'Stage',
                        track_visibility='always', select=True,
                        domain="[('project_ids', '=', project_id)]", copy=False),
        'user_id': fields.many2one('res.users', 'Assigned to', required=False, select=1, track_visibility='always'),
        'flag_types':fields.many2one('issue.type','Flag Type', track_visibility='always'),
        'issue_classifications':fields.many2many('issue.classification',string ='Classification'),
#        'issue_cate':fields.many2one('issue.category',string ='Category', required=False),
        'issue_cate': fields.selection([('Projects', 'Projects'),
                                    ('Assets','Assets'),
                                    ('Safety','Safety'),
                                    ('Employees','Employees'),
                                    ('Clients', 'Clients'),
                                    ('Venders','Venders'),
                                    ('Facilities','Facilities'),
                                    ('Material','Material'),
                                    ('Processes','Processes'),
                                    ('Other','Other')],
                                      'Category', copy=False),
        'hdn_issue_cate':fields.char('Hdn Issuecate'),
        'partner_id':fields.many2one('res.partner', 'Manager', select=1, track_visibility='always'),
        'disposition_asset':fields.many2one('asset.asset','Disposition'),
        'disposition_safety':fields.many2one('safety.safety','Disposition'),
        'disposition_employee':fields.many2one('hr.employee','Disposition'),
        'disposition_client':fields.many2one('res.partner','Disposition',domain=[('is_company','=',1)]),
        'disposition_vender':fields.many2one('res.partner','Disposition',domain=[('supplier','=',True)]),
        'disposition_facility':fields.many2one('facilities.facilities','Disposition'),
        'disposition_material':fields.many2one('product.template','Disposition'),
        'disposition_process':fields.many2one('processes.processes','Disposition'),
        'disposition_other':fields.char('Disposition'),
        'escalated_by':fields.many2one('res.users','Escalated by',track_visibility='onchange'),
        'escalated_on':fields.datetime('Escalated On'),
        'description':fields.html('Description'),
        'closed_on':fields.datetime('Closed on'),
        'closed_by':fields.many2one('res.users','Close by'),
        'close_conclusion':fields.many2many('issue.close.conclusion',string ='Conclusion'),
        'closeout_desc':fields.text('Description'),
        'approved_on':fields.datetime('Approved On'),
        'approved_by':fields.many2one('res.users','Approved by'),
        'resolution':fields.many2one('issue.resolution',string ='Resolution', required=False),
        'issue_prioritys':fields.many2one('issue.priority',string ='Priority', required=False),
        'attached_docs':fields.one2many('ir.attachment', 'issue_id', domain=[('res_model','=','project.issue'),('attachment_soruce','=','Issue')],readonly = True),
        'issue_transactional_logs':fields.one2many('issue.transactional.log', 'project_id', 'Issue Handling Logs'),
        'action_logs' :fields.one2many('issue.action.logs', 'issue_id','Action Logs'),
            
                }
    _defaults = {
        'issue_cate':'Projects',
    }
project_issue()