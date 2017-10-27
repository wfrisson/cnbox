from openerp.osv import fields, osv
import datetime
from datetime import datetime,timedelta
import xlwt
import socket
# import fcntl
import struct
import urllib
import os
import calendar 




class print_technician_hours(osv.osv_memory):

#     def _get_employee(self, cr, uid, ids):
#        
#         stdobj = self.browse(cr, uid, ids['active_id'])
#         std_id =  stdobj.id
#         return std_id
   
    _name = "print.technician.hours"
    _description = ""
    _columns = {
              'employee': fields.many2one('hr.employee', 'Employee', required=True),
              'date_from': fields.date('From'),
              'date_to': fields.date('To'),
               }
    _defaults = {
         'from_date': lambda * a: (datetime.now()-timedelta(30)).strftime('%Y-%m-%d'),
         'to_date': lambda * a: datetime.now().strftime('%Y-%m-%d'),
           }
   
    def proceed_with_print(self, cr, uid, ids, data):

        book=xlwt.Workbook()
        sheet1=book.add_sheet('Sheet 1',cell_overwrite_ok=True)
        title="""CNI Title"""
        
        
        for f in self.browse(cr, uid, ids):
        
            timesheet_ids = self.pool.get('hr_timesheet_sheet.sheet').search(cr,uid,[('employee_id','=',f.employee.id)])
            if timesheet_ids:
                timesheet_ids.sort()
                rec_timesheet = self.pool.get('hr_timesheet_sheet.sheet').browse(cr,uid,timesheet_ids)
                
                day_row = 8
                date_row = 9
                data_row = 10
                for timesheet in rec_timesheet:
                    
                    sheet1.row(6).height_mismatch = True
                    sheet1.row(6).height = 256*3
                    sheet1.write_merge(r1=6, c1=2, r2=6, c2=6, label=timesheet.employee_id.name)
                   

                    sheet1.row(day_row).height_mismatch = True
                    sheet1.row(day_row).height = 256*2
                    
                    sheet1.row(date_row).height_mismatch = True                    
                    sheet1.row(date_row).height = 256*2

                    sheet1.row(data_row).height_mismatch = True                    
                    sheet1.row(data_row).height = 256*2


                    DATE_FORMAT_HEADER = xlwt.Style.easyxf(
                                                 'font: bold 0, color black, name Tahoma, height 300;'
                                                 'align: vertical center, horizontal center, wrap on;'
                                                 'borders: left thin, right thin, bottom thick;'
                                                 'pattern: pattern solid, fore_colour white;'
                                                 )
                    
                    DAY_FORMAT_HEADER = xlwt.Style.easyxf(
                                                 'font: bold 0,color red, name Tahoma, height 300;'
                                                 'align: vertical center, horizontal center, wrap on;'
                                                 'borders: left thin, right thin,  top thick;'
                                                 'pattern: pattern solid, fore_colour white;'
                                                 ) 
                    DATA_FORMAT_HEADER = xlwt.Style.easyxf(
                                                 'font: bold 0,color green, name Tahoma, height 280;'
                                                 'align: vertical center, horizontal center, wrap on;'
                                                 'borders: left thin, right thin, bottom thick;'
                                                 'pattern: pattern solid, fore_colour white;'
                                                 )                    

                    
                    anal_timesheet_ids = self.pool.get('hr.analytic.timesheet').search(cr,uid,[('sheet_id','=',timesheet.id)])
                    if anal_timesheet_ids:
                        #rec_anal_timesheet = self.pool.get('hr.analytic.timesheet').browse(cr,uid,anal_timesheet_ids)
                        #sheet1.row(data_row).write(1, rec_anal_timesheet, DATA_FORMAT_HEADER)
                        print "posted"
                    
                    start_date = datetime.strptime(timesheet.date_from,'%Y-%m-%d') 
                    end_date = datetime.strptime(timesheet.date_to,'%Y-%m-%d')
                    
                    date_col = sheet1.col(3)
                    sheet1.col(2).width = 256 * 20
                    column_index = 3
                    date_generated = [start_date + timedelta(days=x) for x in range(0, (end_date-start_date).days)]


                    week_no  = start_date.isocalendar()[1]
                    sheet1.row(day_row).write(2, "Week "+str(week_no), DAY_FORMAT_HEADER)
                    sheet1.row(data_row).write(2, '', DATE_FORMAT_HEADER)

                    for date in date_generated:
                        this_date = date.strftime("%d-%m-%Y")
                        date_col.width = 256 * 18
                        date_col = sheet1.col(column_index)
                        this_day = datetime.strptime(str(this_date), '%d-%m-%Y').strftime('%A')

                        sheet1.row(date_row).write(column_index, this_date, DATE_FORMAT_HEADER)
                        sheet1.row(day_row).write(column_index, this_day, DAY_FORMAT_HEADER)
                        sheet1.row(data_row).write(column_index, timesheet.total_timesheet, DATA_FORMAT_HEADER)
                        
                        column_index = column_index + 1
                                      
                    
                    day_row  =  day_row + 4
                    date_row = date_row + 4
                    data_row = data_row + 4

                sheet1.write_merge(r1=1, c1=0, r2=1, c2=4, label=title)
            else:
                raise osv.except_osv(('Time Sheet Not found'),("No found for "+str(f.employee.name)))
        
        path = os.path.join(os.path.expanduser('~'),'Documents','reports','file.xls')
#         location="/home/user/Documents/reports/"
        
#         filename= title + ".xls" 
#         self.file_name=filename
#         strs=str(location)+str(filename)
        book.save(path)
        
        
        company_obj = self.pool.get('res.company').browse(cr, uid, 1)
        
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
#         ip = socket.inet_ntoa(fcntl.ioctl(
#             s.fileno(),
#             0x8915,  # SIOCGIFADDR
#             struct.pack('256s', str(company_obj[0].network_connection_interface)[:15])
#         )[20:24])
#         filename = urllib.quote(filename)
#         url = 'http://'+ip+'/excel2/'+str(filename)       
#         
#         return {
#         'type': 'ir.actions.act_url',
#         'url':url,
#         'target': 'new'
#         }

        return
        
        
        
print_technician_hours()

# vim:expandtab:+-smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
