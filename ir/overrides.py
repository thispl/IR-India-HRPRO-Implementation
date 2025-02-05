from email import message
import frappe
from frappe import _
import datetime, math
from datetime import date, timedelta, datetime,time
import datetime as dt
from frappe.utils import time_diff_in_hours
from hrms.payroll.doctype.salary_slip.salary_slip import SalarySlip
from ir.ir.doctype.attendance_regularize.attendance_regularize import AttendanceRegularize

class CustomSalarySlip(SalarySlip):
    def get_date_details(self):
        ots = frappe.db.sql("""
            SELECT * FROM `tabOver Time Request`
            WHERE ot_date BETWEEN %s AND %s
            AND employee = %s AND docstatus = 1 and workflow_state ="Approved"
        """, (self.start_date, self.end_date, self.employee), as_dict=True)
        
        ots_od = frappe.db.sql("""
            SELECT *
            FROM `tabOver Time Request`
            WHERE od_date BETWEEN %s AND %s
            AND employee = %s AND docstatus = 1 and workflow_state ="Approved"
        """, (self.start_date, self.end_date, self.employee), as_dict=True)

        custom_ot_hours = 0
        for ot in ots:
            # frappe.errprint(ot.ot_hour)
            total_seconds = ot.ot_hour.total_seconds()
            ot_hr = total_seconds / 3600  
            custom_ot_hours += ot_hr
        for od in ots_od:
            total_seconds = od.ot_hour.total_seconds()
            od_hr = total_seconds / 3600  
            custom_ot_hours += od_hr
        self.custom_overtime = custom_ot_hours
                
        # if ots:
        #     if ots[0].employee_category == "Blue Collar":
        #         holiday_list = frappe.db.get_value('Company', 'Industrias Del Recambio India Private Limited', 'default_holiday_list')
        #         holidays = frappe.db.sql("""
        #             SELECT `tabHoliday`.holiday_date, `tabHoliday`.weekly_off 
        #             FROM `tabHoliday List`
        #             LEFT JOIN `tabHoliday` ON `tabHoliday`.parent = `tabHoliday List`.name 
        #             WHERE `tabHoliday List`.name = %s 
        #             AND holiday_date BETWEEN %s AND %s
        #         """, (holiday_list, self.start_date, self.end_date), as_dict=True)
                
        #         if holidays:
        #             custom_ot_hrs = 0
        #             for holiday in holidays:
        #                 ot_request = frappe.db.sql("""
        #                     SELECT * FROM `tabOver Time Request`
        #                     WHERE ot_date = %s AND employee = %s AND docstatus = 1
        #                 """, (holiday.holiday_date, self.employee), as_dict=True)
                        
        #                 ot_request = frappe.db.sql("""
        #                     SELECT * FROM `tabOver Time Request`
        #                     WHERE od_date = %s AND employee = %s AND docstatus = 1
       
        #                 """, (holiday.holiday_date, self.employee), as_dict=True)
        #                 if ot_request:
        #                     ot_request = ot_request[0]
        #                     # frappe.errprint(ot_request.ot_date)
        #                     # frappe.errprint(ot_request.ot_hour)

        #                     total_seconds = ot_request.ot_hour.total_seconds()
        #                     ot_hr = total_seconds / 3600
        #                     custom_ot_hrs += ot_hr
        #             self.custom_ot_on_holiday = custom_ot_hrs

        #             ots = frappe.db.sql("""
        #                 SELECT * FROM `tabOver Time Request`
        #                 WHERE ot_date BETWEEN %s AND %s
        #                 AND employee = %s AND docstatus = 1
        #             """, (self.start_date, self.end_date, self.employee), as_dict=True)
                    
        #             ots = frappe.db.sql("""
        #                 SELECT * FROM `tabOver Time Request`
        #                 WHERE od_date BETWEEN %s AND %s
        #                 AND employee = %s AND docstatus = 1
        #             """, (self.start_date, self.end_date, self.employee), as_dict=True)
                    
        #             custom_ot_hours = 0
        #             for ot in ots:
        #                 # frappe.errprint(ot.ot_hour)
        #                 total_seconds = ot.ot_hour.total_seconds()
        #                 ot_hr = total_seconds / 3600  
        #                 custom_ot_hours += ot_hr
        #             self.custom_overtime = custom_ot_hours - custom_ot_hrs
        #     else:
        #         ots = frappe.db.sql("""
        #             SELECT * FROM `tabOver Time Request`
        #             WHERE ot_date BETWEEN %s AND %s
        #             AND employee = %s AND docstatus = 1
        #         """, (self.start_date, self.end_date, self.employee), as_dict=True)
                
        #         ots = frappe.db.sql("""
        #             SELECT * FROM `tabOver Time Request`
        #             WHERE od_date BETWEEN %s AND %s
        #             AND employee = %s AND docstatus = 1
        #         """, (self.start_date, self.end_date, self.employee), as_dict=True)

                
            # frappe.errprint("IR")

        
        canteen = frappe.db.sql("""
            SELECT COUNT(status) AS present_days
            FROM `tabAttendance`
            WHERE attendance_date BETWEEN %s AND %s
            AND docstatus != 2 AND employee = %s
            AND status = 'Present'
        """, (self.start_date, self.end_date, self.employee), as_dict=True)
        attendance = frappe.db.sql("""
            SELECT attendance_date
            FROM `tabAttendance`
            WHERE attendance_date BETWEEN %s AND %s
            AND docstatus != 2 AND employee = %s
            AND status = 'Present'
        """, (self.start_date, self.end_date, self.employee), as_dict=True)
        # frappe.errprint(canteen)
        # frappe.errprint(canteen[0]['present_days'])

        if canteen[0]['present_days']:
            self.custom_present_days_holiday = canteen[0]['present_days'] 
        else:
            self.custom_present_days_holiday = 0

        holiday_list = frappe.db.get_value('Employee', {'name': self.employee}, 'holiday_list')

        holiday = frappe.db.sql("""
            SELECT `tabHoliday`.holiday_date, `tabHoliday`.weekly_off
            FROM `tabHoliday List`
            LEFT JOIN `tabHoliday` ON `tabHoliday`.parent = `tabHoliday List`.name 
            WHERE `tabHoliday List`.name = %s AND holiday_date BETWEEN %s AND %s
        """, (holiday_list, self.start_date, self.end_date), as_dict=True)

        doj = frappe.db.get_value("Employee", {'name': self.employee}, "date_of_joining")

        holiday_count = len(holiday)

        self.custom_holidays = holiday_count
        compoffdays = 0
        for i in holiday:
            for j in attendance:
                if i.holiday_date == j.attendance_date:
                    compoffdays += 1
        # frappe.errprint(compoffdays)
        custom_present_days=canteen[0]['present_days']+holiday_count-compoffdays
        if custom_present_days>0:
                
            self.custom_present_days=canteen[0]['present_days']+holiday_count-compoffdays
        else:
            self.custom_present_days=0


class CustomAttendanceRegularize(AttendanceRegularize): 
    def on_submit(self):
        if self.corrected_shift or self.corrected_in or self.corrected_out or self.corrected_ot:
            att = frappe.db.exists('Attendance',{'employee':self.employee,'attendance_date':self.attendance_date})
            frappe.db.set_value('Attendance', att, 'shift', self.corrected_shift)
            frappe.db.set_value('Attendance', att, 'in_time', self.corrected_in)
            frappe.db.set_value('Attendance', att, 'out_time', self.corrected_out)
            attendance = frappe.db.get_all('Attendance',{'name':att},['*'])
            for att in attendance:
                if self.corrected_ot:
                    frappe.errprint("test")
                    frappe.db.set_value('Attendance', self.attendance_marked, 'custom_attendance_regularize', self.name)
                    frappe.db.set_value('Attendance', self.attendance_marked, 'custom_ot_hours', self.corrected_ot)
                    if frappe.db.exists("Over Time Request",{'employee':self.employee,'ot_date':self.attendance_date,'docstatus':['!=',2]}):
                        ot_req=frappe.db.get_value("Over Time Request",{'employee':self.employee,'ot_date':self.attendance_date,'docstatus':['!=',2]},['name'])
                        frappe.db.set_value('Over Time Request', ot_req, 'ot_hour', self.corrected_ot)
                        # ot_req.ot_hour=self.corrected_ot
                        frappe.db.commit()
                    else:
                        ot_req=frappe.new_doc("Over Time Request")
                        ot_req.employee = self.employee
                        ot_req.ot_date = self.attendance_date
                        ot_req.ot_hour = self.corrected_ot
                        # ot_req.planned_hour = time(0, 0, 0)
                        ot_req.save(ignore_permissions=True)
                        frappe.db.commit()
                if att.shift and att.in_time and att.out_time :
                    if att.in_time and att.out_time:
                        in_time = att.in_time
                        out_time = att.out_time
                    if isinstance(in_time, str):
                        in_time = datetime.strptime(in_time, '%Y-%m-%d %H:%M:%S')
                    if isinstance(out_time, str):
                        out_time = datetime.strptime(out_time, '%Y-%m-%d %H:%M:%S')
                    wh = time_diff_in_hours(out_time,in_time)
                    if wh > 0 :
                        if wh < 24.0:
                            time_in_standard_format = time_diff_in_timedelta(in_time,out_time)
                            frappe.db.set_value('Attendance', att.name, 'custom_total_working_hours', str(time_in_standard_format))
                            frappe.db.set_value('Attendance', att.name, 'working_hours', wh)
                            if att.docstatus == 1:
                                time_in_standard_format = time_diff_in_timedelta(in_time,out_time)
                                frappe.db.set_value('Attendance', att.name, 'custom_total_working_hours', str(time_in_standard_format))
                                frappe.db.set_value('Attendance', att.name, 'working_hours', wh)
                        else:
                            wh = 24.0
                            frappe.db.set_value('Attendance', att.name, 'custom_total_working_hours',"23:59:59")
                            frappe.db.set_value('Attendance', att.name, 'working_hours',wh)
                        if wh < 4:
                            frappe.db.set_value('Attendance',att.name,'status','Absent')
                        elif wh >= 4 and wh < 6:
                            frappe.db.set_value('Attendance',att.name,'status','Half Day')
                        elif wh >= 6:
                            frappe.db.set_value('Attendance',att.name,'status','Present')  
                        shift_st = frappe.get_value("Shift Type",{'name':att.shift},['start_time'])
                        shift_et = frappe.get_value("Shift Type",{'name':att.shift},['end_time'])
                        out_time = datetime.strptime(str(att.out_time),'%Y-%m-%d %H:%M:%S').time()
                        shift_et = datetime.strptime(str(shift_et), '%H:%M:%S').time()
                        ot_hours = None
                        hh = check_holiday(att.attendance_date,att.employee)
                        if not hh:
                            if shift_et < out_time:
                                difference = time_diff_in_timedelta_1(shift_et,out_time)
                                diff_time = datetime.strptime(str(difference), '%H:%M:%S').time()
                                if diff_time.hour > 0:
                                    if diff_time.minute >= 50:
                                        ot_hours = time(diff_time.hour+1,0,0)
                                    else:
                                        ot_hours = time(diff_time.hour,0,0)
                                elif diff_time.hour == 0:
                                    if diff_time.minute >= 50:
                                        ot_hours = time(1,0,0)
                                else:
                                        ot_hours = "00:00:00"			
                    else:
                        ot_hours = "00:00:00"
                    frappe.db.set_value("Attendance",att.name,"custom_ot_hours",ot_hours)
                    if ot_hours:
                        ftr = [3600,60,1]
                        hr = sum([a*b for a,b in zip(ftr, map(int,str(ot_hours).split(':')))])
                        ot_hr = round(hr/3600,1)
                    else:
                        ot_hr = '0.0'	
                    frappe.db.set_value("Attendance",att.name,"custom_over_time_hours",ot_hr)         
                        
                else:
                    frappe.db.set_value('Attendance',att.name,'custom_total_working_hours',"00:00:00")
                    frappe.db.set_value('Attendance',att.name,'working_hours',"0.0")
                    frappe.db.set_value('Attendance',att.name,'custom_extra_hours',"0.0")
                    frappe.db.set_value('Attendance',att.name,'custom_total_extra_hours',"00:00:00")
                    frappe.db.set_value('Attendance',att.name,'custom_total_overtime_hours',"00:00:00")
                    frappe.db.set_value('Attendance',att.name,'custom_over_time_hours',"0.0")
                hh = check_holiday(att.attendance_date,att.employee)
                if not hh:
                    if att.shift and att.in_time:
                        shift_time = frappe.get_value(
                            "Shift Type", {'name': att.shift}, ["start_time"])
                        shift_start_time = datetime.strptime(
                            str(shift_time), '%H:%M:%S').time()
                        start_time = dt.datetime.combine(att.attendance_date,shift_start_time)
                        
                        if att.in_time > datetime.combine(att.attendance_date, shift_start_time):
                            frappe.db.set_value('Attendance', att.name, 'late_entry', 1)
                            frappe.db.set_value('Attendance', att.name, 'custom_late_entry_time', att.in_time - start_time)
                        else:
                            frappe.db.set_value('Attendance', att.name, 'late_entry', 0)
                            frappe.db.set_value('Attendance', att.name, 'custom_late_entry_time', "00:00:00")
                    if att.shift and att.out_time:
                        shift_time = frappe.get_value(
                            "Shift Type", {'name': att.shift}, ["end_time"])
                        shift_end_time = datetime.strptime(
                            str(shift_time), '%H:%M:%S').time()
                        end_time = dt.datetime.combine(att.attendance_date,shift_end_time)
                        if att.out_time < datetime.combine(att.attendance_date, shift_end_time):
                            frappe.db.set_value('Attendance', att.name, 'early_exit', 1)
                            frappe.db.set_value('Attendance', att.name, 'custom_early_out_time', att.out_time - end_time)
                        else:
                            frappe.db.set_value('Attendance', att.name, 'early_exit', 0)
                            frappe.db.set_value('Attendance', att.name, 'custom_early_out_time',"00:00:00")
                else:
                    frappe.db.set_value('Attendance', att.name, 'late_entry', 0)
                    frappe.db.set_value('Attendance', att.name, 'custom_late_entry_time', "00:00:00")
                    frappe.db.set_value('Attendance', att.name, 'early_exit', 0)
                    frappe.db.set_value('Attendance', att.name, 'custom_early_out_time',  "00:00:00")
            frappe.db.set_value('Attendance', att.name, 'custom_regularize_marked', 1)
            frappe.db.set_value('Attendance', att.name, 'custom_attendance_regularize',self.name)
    def on_cancel(self): 
        # att = frappe.db.exists('Attendance',{'employee':self.employee,'attendance_date':self.attendance_date})
        frappe.db.set_value('Attendance', self.attendance_marked, 'custom_ot_hours', "00:00:00")  
        frappe.db.set_value('Attendance', self.attendance_marked, 'custom_attendance_regularize', "")
             
    
                
@frappe.whitelist()
def check_holiday(date,emp):
    holiday_list = frappe.db.get_value('Employee',{'name':emp},'holiday_list')
    holiday = frappe.db.sql("""select `tabHoliday`.holiday_date,`tabHoliday`.weekly_off from `tabHoliday List`
    left join `tabHoliday` on `tabHoliday`.parent = `tabHoliday List`.name where `tabHoliday List`.name = '%s' and holiday_date = '%s' """%(holiday_list,date),as_dict=True)
    doj= frappe.db.get_value("Employee",{'name':emp},"date_of_joining")
    if holiday :
        if doj < holiday[0].holiday_date:
            if holiday[0].weekly_off == 1:
                return "WW"     
            else:
                return "HH"  
@frappe.whitelist()           
def time_diff_in_timedelta_1(time1, time2):
    datetime1 = datetime.combine(datetime.min, time1)
    datetime2 = datetime.combine(datetime.min, time2)
    timedelta_seconds = (datetime2 - datetime1).total_seconds()
    diff_timedelta = timedelta(seconds=timedelta_seconds)
    return diff_timedelta
@frappe.whitelist()
def time_diff_in_timedelta(time1, time2):
        return time2 - time1