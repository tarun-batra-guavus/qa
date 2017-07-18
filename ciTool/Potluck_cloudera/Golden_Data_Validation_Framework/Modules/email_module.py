#! /usr/bin/python

import smtplib
import datetime
from email.mime.multipart import MIMEMultipart
from email.MIMEBase import MIMEBase
from email.mime.text import MIMEText
from email import Encoders
from email.Utils import COMMASPACE, formatdate
import sys
import os
from time import gmtime, strftime
import socket



class Reporting(object):

    def __init__(self):
        self.tooldir = ("/").join(os.getcwd().split("/")[0:-1])
        self.test_to_parse  = []
        self.counter = 1
        self.tmp_path = ("/").join(os.getcwd().split("/")[0:-1]) + "/Tmp/tmp_html_file"
        try:
            os.remove(self.tmp_path)
        except:
            print "tmp_html_file not present"
            

    def getCommandOutput(self,command):
        p = sub.Popen(command,stdout=subprocess.PIPE, shell=True)
        output, errors = p.communicate()
        #print output, errors
        return(output,errors)

    def parseReports(self,current_version,mail_to):
        log_files = []
        job_result = {}
        base_version = "not-available"
        files_to_parse = os.listdir(self.tooldir + "/Test_Reports/Test_Execution_Current")
        for file in  files_to_parse:
            if ".log" in file:
                log_files.append(file)
        for file in log_files:
            print file
            f = open(self.tooldir + "/Test_Reports/Test_Execution_Current/" + file,'r')
            self.test_to_parse = f.readlines()
            job_result["Connection Status with SUT(Server Under Test): "] = self.returnConnectionStatus()
            job_result["Job application ID/IDs: "] = self.returnAppId()
            job_result["Job/Jobs Execution Status: "] = self.returnAppIdStatus(self.returnAppId())
            job_result["Log parsing for Job: "] = self.returnException()
            job_result["Job logs and DB Dumps at: "] = str(socket.gethostbyname(socket.gethostname())) + ":/" + self.tooldir + "/Test_Reports/Test_Execution_Current/"

            if self.returnDiff("hive") != {}:
                job_result["Diff Result Hive: "] = self.returnDiff("hive")
            if self.returnDiff("hbase") != {}:
                job_result["Diff Result Hbase: "] = self.returnDiff("hbase")
            if self.returnDiff("impala") != {}:
                job_result["Diff Result Impala: "] = self.returnDiff("impala")
            custom_val = self.returnCustomValue()
            if custom_val != []:
                for value in custom_val:
                    if self.returnDiff("custom_" + value) != {}:
                        job_result["Diff Result " + value.strip() + ":"] = self.returnDiff("custom_" + value)
                    print job_result
            
            self.createHtmlReportFile(job_result,mail_to,file,self.returnBaseVersion(),current_version,self.returnTcTitle())
        self.createHtmlFooter()
        self.parsereportMail("dummyuser@dummydomain.com",mail_to,self.returnBaseVersion(),current_version)

    def returnBaseVersion(self):
        for line in self.test_to_parse:
            if "Base Version:" in line:
		print line.split("Base Version:")[1].strip()
                return(line.split("Base Version:")[1].strip())
        return("Base Version Not Found")
            
    def returnTcTitle(self):
        for line in self.test_to_parse:
            if "Test Case Title:" in line:
		print line.split("Test Case Title:")[1].strip()
                return(line.split("Test Case Title:")[1].strip())
        return("Test Case Title Not Found")

    def returnAppId(self):
        job_id = []
        for line in self.test_to_parse:
            if "Job Started with applicationID:" in line and "application_" in line:
                if line.split("Job Started with applicationID: ")[1].strip() not in job_id:
                    job_id.append(line.split("Job Started with applicationID: ")[1].strip())               
        return(job_id)

    def returnAppIdStatus(self,job_id):
        job_status = "not-found"
        job_dict = {}
        for line in self.test_to_parse:
            for job in job_id:
                if "Job Status for Application ID:" in line and job.strip() in line and "SUCCESS" in line:
                    job_dict[str(job)] = "SUCCESS"
                    break
                if "Job Status for Application ID:" in line and job.strip() in line and "FAILED" in line:
                    job_dict[str(job)] = "FAILED"
                    break
                
        return(str(job_dict))

    def returnConnectionStatus(self):
        conn_status = ""
        for line in self.test_to_parse:
            if "connection to" in line and "successful" in line:
                conn_status = "Connection to " + line.split("connection to ")[1].split(" ")[0] + " successful" 
                break
        return(conn_status)

    def returnDiff(self,dbtype):
        missing_tables = []
        db_dict = {}
        if "custom" in dbtype:
            for line in self.test_to_parse:
                if "File Not found in New DB" in line and dbtype in line and "custom" in line:
                    missing_tables.append(line.split(":")[-2].strip().split(".txt")[0])
                if "Stats for Diff - Table :" in line and dbtype in line and "custom" in line:
                    print line
                    db_dict[line.split("diff result: ")[0].split(":")[-1].split(".txt")[0]] = line.split("diff result: ")[1].strip()
                    print "key" + line.split("diff result: ")[0].split(":")[-1].split(".txt")[0]
                    print "value" + line.split("diff result: ")[1].strip()
            if missing_tables != []:
                db_dict["missing_tables"] = missing_tables
            return(db_dict)
                
        if "custom" not in dbtype:
            for line in self.test_to_parse:
                if "File Not found in New DB" in line and dbtype in line and "custom" not in line:
                    missing_tables.append(line.split(":")[-2].strip().split(".txt")[0])
                if "Stats for Diff - Table :" in line and dbtype in line and "custom" not in line:
                    print line
                    db_dict[line.split("diff result: ")[0].split(":")[-1].split(".txt")[0]] = line.split("diff result: ")[1].strip()
                    print "key" + line.split("diff result: ")[0].split(":")[-1].split(".txt")[0]
                    print "value" + line.split("diff result: ")[1].strip()
            if missing_tables != []:
                db_dict["missing_tables"] = missing_tables
            return(db_dict)
        


    def returnCustomValue(self):
        custom_val = []
        for line in self.test_to_parse:
            if "Stats for Diff - Table :" in line and "custom" in line:
                value = line.split("custom_")[1].split(" ")[0]
                if value not in custom_val:
                    custom_val.append(value)
                print value
        return(custom_val)
                

    def returnException(self):
        exception_trace_list = []
        for line in self.test_to_parse:
            if "xception trace seen:" in line:
                exception_trace_list.append(line.split("Error/Exception trace seen:")[1].strip())
        return(exception_trace_list)

    def parsereportMail(self,send_from,send_to,base_version,current_version):

        # Create message container - the correct MIME type is multipart/alternative.
        msg = MIMEMultipart('alternative')
        msg['Subject'] = "Regression Execution Summary [Generated at: " +  strftime("%Y-%m-%d %H:%M:%S", gmtime()) + "]" + " versions compared " + base_version + " v/s " + current_version  
        msg['From'] = send_from
        msg['To'] = send_to
        msg['Date'] = formatdate(localtime=True)
        send_to_list = []
        server = '192.168.104.25'
        dict_report = {}
        rollup_type = ""                 
        attachment_files = []
        report_mail = {}
        rollup_list = []
        if "," in send_to:
            send_to_list = send_to.split(',') 
        else:
            send_to_list.append(send_to)
        html = self.readFileAsText(("/").join(os.getcwd().split("/")[0:-1]) + '/Tmp/tmp_html_file')
        part1 = MIMEText(html, 'html')
        msg.attach(part1)
            
        for f in attachment_files:
            part = MIMEBase('application', "octet-stream")
            part.set_payload( open(f,"rb").read() )
            Encoders.encode_base64(part)
            part.add_header('Content-Disposition', 'attachment; filename="%s"' % os.path.basename(f))
            msg.attach(part)
    
        smtp = smtplib.SMTP(server)
        smtp.sendmail(send_from, send_to_list, msg.as_string())
        smtp.close()
        # sendmail function takes 3 arguments: sender's address, recipient's address
        # and message to send - here it is sent as one string.
            
           
    def createHtmlReportFile(self,html_report_dict,req_id,Test_Case,base_version,current_version,tc_title):

        if self.counter != 1:
            f = open(("/").join(os.getcwd().split("/")[0:-1]) + '/Tmp/tmp_html_file','a')
            f.write("Test Script Executed: " + Test_Case.split(".log")[0].strip() + ".py" + "<br>")
            f.write("\n")
            f.write("Test Scenario: " + tc_title + "<br>")
            f.write("\n")
            f.write("<htm><body><table border=\"5\">")
            f.write("\n")
            f.write("<th bgcolor=\"#BDBDBD\">Steps Automated</th>")
            f.write("\n")
            f.write("<th bgcolor=\"#BDBDBD\">Results</th>")
            f.write("\n")
            for item in html_report_dict:
                f.write("<tr><td>" + str(item) + "   " + "</td><td>" + str(html_report_dict[item]) + "      ")
                f.write("\n")
                f.write("</td></tr>")
                f.write("\n")
            f.write("</table>\n")
            f.write("</p>")
            f.write("\n")
            f.write("\n")
            f.close()
            
        if self.counter == 1:
            
            f = open(("/").join(os.getcwd().split("/")[0:-1]) + '/Tmp/tmp_html_file','w')
            f.write("<p>Hi,\n<br>")
            f.write("\n")
            f.write("\n")
            f.write("\n")
            f.write("Below is the Regression Execution report requested by : " + req_id + "<br>")
            f.write("\n")
            f.write("\n")

            f.write("Version Detail:<br>")
            f.write("<htm><body><table border=\"5\">")
            f.write("\n")
            f.write("<th bgcolor=\"#BDBDBD\">Base Version</th>")
            f.write("\n")
            f.write("<th bgcolor=\"#BDBDBD\">Current Version</th>")
            f.write("\n")            
            f.write("</p>")
            f.write("\n")
            f.write("<tr><td>" + str(base_version) + "   " + "</td><td>" + str(current_version) + "      ")
            f.write("\n")
            f.write("</td></tr>")
            f.write("\n")
            f.write("</table>\n")
            f.write("</p>")
            f.write("\n")
            f.write("Test Script Executed: " + Test_Case.split(".log")[0].strip() + ".py" + "<br>")
            f.write("\n")
            f.write("Test Scenario: " + tc_title + "<br>")
            f.write("\n")
            f.write("<htm><body><table border=\"5\">")
            f.write("\n")
            f.write("<th bgcolor=\"#BDBDBD\">Steps Automated</th>")
            f.write("\n")
            f.write("<th bgcolor=\"#BDBDBD\">Results</th>")
            f.write("\n")
            for item in html_report_dict:
                f.write("<tr><td>" + str(item) + "   " + "</td><td>" + str(html_report_dict[item]) + "      ")
                f.write("\n")
                f.write("</td></tr>")
                f.write("\n")
            f.write("</table>\n")
            f.write("</p>")
            f.write("\n")
            f.write("\n")
            f.close()        
            self.counter = self.counter + 1


    def createHtmlFooter(self):
        f = open(("/").join(os.getcwd().split("/")[0:-1]) + '/Tmp/tmp_html_file','a')
        f.write("<p>Automated System generated mail, do not reply on this thread.<br>")
        f.write("\n")
        f.write("<p>Regards<br>")
        f.write("\n")
        f.close()
        
    def readFileAsText(self,filepath):
        try:
            f = open(filepath,'r')
            content_text = f.read()
            f.close()
            return(content_text)
        except IOError:
            print "File Not found"


def main():
    obj = Reporting()
    obj.parseReports("version_test_28","abhay.pathak@guavus.com")
    

if __name__ == '__main__':
  main()


