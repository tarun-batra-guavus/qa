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
running_jobs =[]
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



nodes_type = get_nodes_by_type("NAMENODE")
for node_alias in nodes_type:
    print node_alias
    node = connect(node_alias)
    node.setMode("shell")
    status = node.checkAzkaMaster()
    if status == "true":
        running_jobs = node.getRunningJobId(common["project"])
        running_jobs_id = running_jobs[0::2]
        running_jobs_name = running_jobs[1::2]
        logger.info("=====running jobs id===")
        logger.info(running_jobs_id)
        logger.info("=====running jobs name===")
        logger.info(running_jobs_name)
        if running_jobs_id:
            node.stopRunningJobs(running_jobs_id)
    else:
        continue
    
time.sleep(20)


#### Take backup of existing /etc/yum.repos.d and create new repo under /etc/yum.repos.d
for ip in nodes_type:
    node = connect(ip)
    node.setMode("shell")
    node.backup_create_repos(summary_handle,"namenode",common["image_url"],common["mode"].upper(),summary_var_dict)


time.sleep(20)




for node_alias in nodes_type:
    node = connect(node_alias)
    node.setMode("shell")
    status = node.checkAzkaMaster()
    if status == "true":
        if running_jobs_name:
           node.runJobAzkaCli(common["project"],running_jobs_name)
    else:
        continue

