import sys
import os
sys.path.insert(0, ("/").join(os.getcwd().split("/")[0:-1]) + "/" + "Modules")
new_version = sys.argv[1]
old_version = "test_v54"
tc_title = "ENRC = OFF, Data Input Time = 15 jULY 2017"

from core_module import RegressionModule

test_obj_run = RegressionModule(new_version)
test_obj_run.connectToMachine("root","root@123","192.168.113.188")


#test_obj.getCommandOutput(hdfs dfs -put ......)

test_obj_run.configUpdateCare("care_cdr_ldm_properties.ini",new_version,"/cdr_daily_data_aggregation1_dir/cdr_daily_data_aggregation1/","/opt/reflex/opt/care/ldm/cdr")

test_obj_run.runJob("care_cdr_ldm_job_config","CDR_LDM_JOB","1475824500",new_version,old_version,tc_title)
test_obj_run.verifyJobCompletion()


#test_obj_run.checkJobStatus()  #####-------Not using
test_obj_run.dumpTablesPhoenix(new_version,"",5)
test_obj_run.dumpTablesHive(new_version,"timestamp,subscriberid",40)


#test_obj_run.diffTable('/data/abhay/Golden_Data_Validation_Framework/Test_Reports/Test_Execution_Current_v54/CDR_LDM_JOB_only_diff/HIVE_db_dump_test_v54','hive')
#test_obj_run.diffTable('/data/abhay/Golden_Data_Validation_Framework/Test_Reports/Test_Execution_Current_v54/CDR_LDM_JOB_only_diff/HBASE_db_dump_test_v54','hbase')

#test_obj_run.diffTable('/data/abhay/Golden_Data_Validation_Framework/Test_Reports/Test_Execution_Current_v54_difftest/CDR_LDM_JOB_only_diff/HIVE_db_dump_test_v54','custom_hive','/data/abhay/Golden_Data_Validation_Framework/Test_Reports/Test_Execution_Current_v55_difftest/CDR_LDM_JOB_only_diff/HIVE_db_dump_test_v55/')
#test_obj_run.diffTable('/data/abhay/Golden_Data_Validation_Framework/Test_Reports/Test_Execution_Current_v54_difftest/CDR_LDM_JOB_only_diff/HBASE_db_dump_test_v54','custom_hbase','/data/abhay/Golden_Data_Validation_Framework/Test_Reports/Test_Execution_Current_v55_difftest/CDR_LDM_JOB_only_diff/HBASE_db_dump_test_v55/')

test_obj_run.cleanup()

#test_obj_run.cleanup.parsereport_mail()
