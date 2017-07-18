""""
Purpose
=======
    Check that hbase process is running on all hbase machines

Test Steps
==========
    1. Goto to shell
    2. Execute "ps -ef | grep -v grep "processname"" and check that hmaster and regionserver  process is in running state
"""

from potluck.nodes import connect, get_nodes_by_type
from potluck.logging import logger
from potluck.reporting import report
from potluck.parsing import parser
import sys
import os
import time
parser = parser()


#### Input files path
process_file = "userinput/process_file.txt"
job_file = "userinput/job_file.txt"
file_paths = "userinput/file_paths.txt"
config_file = "userinput/config.txt"
mop_file = "userinput/mop.txt"
rpm_info = "userinput/rpm_info.txt"
summary_file = "useroutput/SUMMARY/summary.log" 
dir_installer = "/home/CD/installer"
dir_backup = "/home/CD/backup"
dir_build_content = "/home/CD/release"

#### Temporary variables used
image_list=[]
common = {}
jobs_dict = {}
process_start_dict ={}
process_stop_dict ={}
summary_var_dict = {}
roles_list_job =[]
roles_list_process =[]
process_list =[]
roles_list_mop_command =[]
reverse_process_list = []
reverse_roles_list_process = []
roles_list_rpm_info = []
all_unique_roles = []
exit_flag_list = []
reverse_exit_flag_list =[]

#### Calling parser for config.txt file
common = parser.create_dict(config_file)


mandatory_files = [process_file,job_file,file_paths,config_file,rpm_info]
optional_files = [mop_file]


#### Opening summary file for reporting status of all actions
if common["mode"].upper() == "FRESH":
    summary_handle = open(summary_file,"w")
else:
    summary_var_dict = parser.create_dict_summary_file(summary_file)
    summary_handle = open(summary_file,"a")
    summary_handle.write("\n ==================\n RECOVERY MODE STARTED \n ==================\n") 



#### Check whether all mandatory files exist 
parser.check_file(mandatory_files)


#### Check whether all optional files exist
flag = parser.check_file(optional_files,"yes")


#### Calling parser for job_file.txt file 
jobs_dict,roles_list_job = parser.parse_file_1(job_file,common["delimiter"])


#### Calling parser for file paths
file_path_dict,roles_list_path = parser.parse_file_3(file_paths,common["delimiter"])



#### Calling parser for process_file.txt file
process_list,roles_list_process,exit_flag_list,process_stop_dict,process_start_dict = parser.parse_file(process_file,common["delimiter"])
reverse_process_list = process_list[::-1]
reverse_roles_list_process = roles_list_process[::-1]
reverse_exit_flag_list = exit_flag_list[::-1]



### Calling parser for rpm_info.txt file
roles_list_rpm_info = parser.parse_file_2(rpm_info,common["delimiter"])


#### Config parser for mop.txt file in case file is present

if flag == "true":
    roles_list_mop_command = parser.parse_file_2(mop_file,common["delimiter"])


#### Check whether any rpm installation is in progress on any of nodes
all_unique_roles = roles_list_rpm_info[0::3]
for each in list(set(all_unique_roles)):
    nodes_type = get_nodes_by_type(each)
    for ip in nodes_type:
        node = connect(ip)
        node.setMode("shell")
        node.check_process(summary_handle,each,"yum",common["mode"].upper(),summary_var_dict)
        


#### Stopping all jobs 
summary_handle.write("#Stopping all job on respective nodes\n#Jobname,command,node,role,status \n")
logger.info ("Stopping all jobs")
for each in roles_list_job:
    nodes_type = get_nodes_by_type(each)
    for ip in nodes_type:
        node = connect(ip)  
        node.setMode("shell")
        node.stop_job(summary_handle,each,jobs_dict[each],common["mode"].upper(),summary_var_dict)

logger.info ("All jobs are stopped successfully on all respective nodes")



#### Stopping all processes
summary_handle.write("#Stopping all processes on respective nodes\n#Processname,command,node,role,status \n")
logger.info ("Stopping all process")
for i in range(len(process_list)):
    nodes_type = get_nodes_by_type(roles_list_process[i])
    for ip in nodes_type:
        node = connect(ip)
        node.setMode("shell")
        node.stop_process(summary_handle,roles_list_process[i],process_list[i],process_stop_dict[process_list[i]],exit_flag_list[i],common["mode"].upper(),summary_var_dict)
logger.info ("All process are successfully stopped on all nodes")




#### Taking backup of config files on respective servers
summary_handle.write("#Taking backup of config files on respective nodes\n#file_path,node,role,status \n")
logger.info ("Taking backup of config files")
for each in roles_list_path:
    nodes_type = get_nodes_by_type(each)
    for ip in nodes_type:  
        node = connect(ip)  
        node.setMode("shell") 
        node.createDirectory(summary_handle,dir_backup,common["mode"].upper(),each,summary_var_dict)
        node.files_backup(summary_handle,each,file_path_dict[each],dir_backup,common["mode"].upper(),summary_var_dict)



#### Create Installer directory that contains all build rps files  and build directory that contains all files(to be backed up) that are present after rpm is installed
logger.info ("Installing rpm")
for each in list(set(all_unique_roles)):
    nodes_type = get_nodes_by_type(each)
    for ip in nodes_type:
        node = connect(ip)
        node.setMode("shell")
        node.createDirectory(summary_handle,dir_installer,common["mode"].upper(),each,summary_var_dict)
        node.createDirectory(summary_handle,dir_build_content,common["mode"].upper(),each,summary_var_dict)
  
 


#### Installing RPM 
summary_handle.write("#Installing RPM on respective nodes\n#rpmname,node,role,status \n")
i = 0
logger.info ("Installing rpm")
while i < len(roles_list_rpm_info):
    nodes_type = get_nodes_by_type(roles_list_rpm_info[i])
    for ip in nodes_type:
        node = connect(ip)
        node.setMode("shell")
        node.upgrade(summary_handle,roles_list_rpm_info[i],roles_list_rpm_info[i+1],common["image_url"],dir_installer,roles_list_rpm_info[i+2],common["mode"].upper(),summary_var_dict)
    i+=3


logger.info ("All RPMs are applied successfully on all respective nodes")



#### Copy backup config file to original location on respective servers
summary_handle.write("#Copying backup file to original location on respective nodes\n#file_path,node,role,status \n")
for each in roles_list_path:
    nodes_type = get_nodes_by_type(each)
    for ip in nodes_type:
        node = connect(ip)
        node.setMode("shell")
        node.copy_backup_files(summary_handle,each,file_path_dict[each],dir_backup,dir_build_content,common["mode"].upper(),summary_var_dict)





#### Apply MOP
logger.info ("Applying MOP")
summary_handle.write("#Applying MOP on respective nodes\n#mop_command,node,role,status \n")
i = 0
while i < len(roles_list_mop_command):
    nodes_type = get_nodes_by_type(roles_list_mop_command[i])
    for ip in nodes_type:
        node = connect(ip)
        node.setMode("shell")
        node.apply_mop(summary_handle,roles_list_mop_command[i],roles_list_mop_command[i+1],roles_list_mop_command[i+2],common["mode"].upper(),summary_var_dict)
    i+=3


logger.info ("All MOPS are applied successfully on all respective nodes")





#### Starting all processes
summary_handle.write("#Starting all processes on respective nodes\n#Processname,command,node,role,status \n")
logger.info ("Starting all process")
logger.info (reverse_process_list)
for i in range(len(reverse_process_list)):
    nodes_type = get_nodes_by_type(reverse_roles_list_process[i])
    for ip in nodes_type:
        node = connect(ip)
        node.setMode("shell")
        node.start_process(summary_handle,reverse_roles_list_process[i],reverse_process_list[i],process_start_dict[reverse_process_list[i]],reverse_exit_flag_list[i],common["mode"].upper(),summary_var_dict)
logger.info ("All process are successfully started on all nodes")
summary_handle.close()
