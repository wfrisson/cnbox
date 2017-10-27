from openerp.osv import fields, osv
from openerp.tools.translate import _
import datetime
import xlrd
import logging

_logger = logging.getLogger(__name__)

class cni_import_project_data(osv.osv_memory):
    """Use this wizard to Import Project Data from the excel file"""
    _name = "cni.import.project.data"
    _description = "Import Project Data From Excel"
    _columns = {
              'file_name': fields.char('File', size=300, required=True),
              'advanced': fields.boolean('Advanced Search'),
              'start_from': fields.integer('Start From'),
              'records': fields.integer('Number of Records'),
        }
    _defaults = {
        'file_name': '/home/odoo/data.xlsx',
        'start_from': 1,
        'records': 0,
    }
    
    def import_project_data(self, cr, uid, ids, context=None):
        current_obj = self.browse(cr, uid, ids, context=context)
        start_from = current_obj[0].start_from
        records = current_obj[0].records
        advanced = current_obj[0].advanced
        
        workbook = xlrd.open_workbook(current_obj[0].file_name)
        worksheet = workbook.sheet_by_name('data')
        
        rows = worksheet.nrows - 1
        cells = worksheet.ncols - 1
        row = 7
        
        if advanced:
            if start_from <= 0:
                raise osv.except_osv(_('Error!'), _('Please enter valid range'))
            
            if records <= 0:
                raise osv.except_osv(_('Error!'), _('Please enter valid range'))
    
            row = start_from + 6
            if rows < row:
                raise osv.except_osv(_('Error!'), _('Please enter valid range'))
            
            if rows > (records + row - 1) and records > 0:
                rows = records + row - 1
        
        w_counter = 0
        c_counter = 0
        
        while row <= rows:
            project_id_excel = str(worksheet.cell_value(row, 2))
            project_id_excel = project_id_excel.strip()
            
            if  (row-6) % 100 == 0:
                _logger.info("_______ %r out of %r_________", (row-6), (rows-6))
                _logger.info("_______ Created: %r__________ Edited: %r", c_counter, w_counter)
            
            if project_id_excel == "":
                row += 1    
                continue
            
            plant =  worksheet.cell_value(row, 20)
            p_a = str(worksheet.cell_value(row, 31))
            p_a = p_a.strip()

            if p_a == 'P-A' and (plant == 1020.0 or plant == 1050.0):
                project_exist = self.pool.get('project.project').search(cr, uid, [('project_id','=',project_id_excel)])
                if project_exist:
                    project_id = project_exist[0]
                    #_logger.info("_______________IF Project____________%r", project_id_excel)
            
                else:
                    
                    res_partner = self.pool.get('res.partner').search(cr, uid, [('name','=','Bell')])
                    if res_partner:
                        res_partner = res_partner[0]
                    
                    network = str(worksheet.cell_value(row, 4))
                    network = network.strip()

                    status = str(worksheet.cell_value(row, 10))
                    status = status.strip()

                    actv_desc = str(worksheet.cell_value(row, 6))
                    actv_desc = actv_desc.strip()

                    wbs = str(worksheet.cell_value(row, 11))
                    wbs = wbs.strip()
                    #_logger.info("_______________ Created ____________%r  %r  %r  %r  %r  %r  %r ", project_id_excel,network,res_partner,project_id_excel,status,actv_desc,wbs)

                    project_id = self.pool.get('project.project').create(cr, uid, {
                        'name': project_id_excel,
                        'network_id': network,
                        'excel_project': True,
                        'user_id': None,
                        'partner_id': res_partner,
                        'project_types': 'Pre-Assembly',
                        'project_id': project_id_excel,
                        'status': status,
                        'actv_desc': actv_desc,
                        'wbs': wbs,}, context=context)            
                    
                material_desc = str(worksheet.cell_value(row, 22))
                material_desc = material_desc.strip()
                
                
                activity_description =  str(worksheet.cell_value(row, 6))
                activity_description = activity_description.strip()
                        
                item = str(worksheet.cell_value(row, 7))
                item = item.strip()
                
                network = str(worksheet.cell_value(row, 4))
                network = network.strip()
                
                pa_gi_doc = str(worksheet.cell_value(row, 67))
                pa_gi_doc = pa_gi_doc.strip()
                
                gr_doc_pa = str(worksheet.cell_value(row, 72))
                gr_doc_pa = gr_doc_pa.strip()
                
                delivery_pa = str(worksheet.cell_value(row, 63))
                delivery_pa = delivery_pa.strip()

                po_pa = str(worksheet.cell_value(row, 70))
                po_pa = po_pa.strip()
                
                delivery_date = str(worksheet.cell_value(row,66))
                if delivery_date.strip() == "":
                    delivery_date = None
                else:
                    delivery_date = delivery_date.replace(".", "/")
                
                shiping_date = str(worksheet.cell_value(row,46))
                if shiping_date.strip() == "":
                    shiping_date = None
                else:
                    shiping_date = shiping_date.replace(".", "/")
                
                material_req_date = str(worksheet.cell_value(row, 16))
                if material_req_date.strip() == "":
                    material_req_date = None
                else:
                    material_req_date = material_req_date.replace(".", "/")
                
                gi_date = str(worksheet.cell_value(row, 68))
                if gi_date.strip() == "":
                    gi_date = None
                else:
                    gi_date = gi_date.replace(".", "/")
                
                
                material_exist = self.pool.get('project.material').search(cr, uid, [('network_id','=',network),('plant','=',plant),
                            ('activity_description','=',activity_description),('item','=',item),('gr_doc_pa','=',gr_doc_pa)])
                    
                if material_exist:
                    material_unchanged_exist = self.pool.get('project.material').search(cr, uid, [('network_id','=',network),
                            ('plant','=',plant),('delivery_date','=',delivery_date),('activity_description','=',activity_description),
                            ('item','=',item),('gr_doc_pa','=',gr_doc_pa),('material_req_date','=',material_req_date),
                            ('mat_desc','=',material_desc),('req_quantiity','=',worksheet.cell_value(row,37)),
                            ('shiping_date','=',shiping_date),('delivery_pa','=', delivery_pa),('gi_date','=',gi_date),
                            ('po_pa','=',po_pa),('pa_gi_doc','=',pa_gi_doc)])
                    
                    if not material_unchanged_exist:
                        material_id = material_exist[0]
                        w_counter = w_counter + 1
                        self.pool.get('project.material').write(cr, uid, material_id, {
                            'material_req_date': material_req_date,
                            'req_quantiity': worksheet.cell_value(row,37),
                            'shiping_date': shiping_date,
                            'delivery_pa': delivery_pa,
                            'gi_date': gi_date,
                            'po_pa': po_pa,
                            'pa_gi_doc': pa_gi_doc}, context=context)
                else:
                    c_counter = c_counter + 1
                    self.pool.get('project.material').create(cr, uid, {
                        'name': project_id,
                        'network_id': network,
                        'plant': plant,
                        'delivery_date': delivery_date,
                        'activity_description': activity_description,
                        'item': item,
                        'gr_doc_pa': gr_doc_pa,
                        'material_req_date': material_req_date,
                        'mat_desc': material_desc,
                        'req_quantiity': worksheet.cell_value(row,37),
                        'shiping_date': shiping_date,
                        'delivery_pa': delivery_pa,
                        'gi_date': gi_date,
                        'po_pa': po_pa,
                        'pa_gi_doc': pa_gi_doc}, context=context)            

            row += 1
        
        _logger.info("Completed: %r out of %r_________", (row-7), (rows-6))
        _logger.info("_______ Created: %r__________ Edited: %r", c_counter, w_counter)

        return {}

cni_import_project_data()

