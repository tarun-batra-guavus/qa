import sys
import os
sys.path.insert(0, ("/").join(os.getcwd().split("/")[0:-1]) + "/" + "Modules")
new_version = sys.argv[1]
old_version = "test_v54"
tc_title =  "ENRC = OFF, Data Input TIme = 15 jULY 2017"

from core_module import RegressionModule

test_obj_run = RegressionModule(new_version)
test_obj_run.connectToMachine("root","root@123","192.168.113.188")


#test_obj.getCommandOutput(hdfs dfs -put ......)

test_obj_run.configUpdateCare("care_cdr_cdm_properties.ini",new_version,"test_v54","/opt/reflex/opt/care/cdm/cdr")

test_obj_run.runJob("care_cdr_cdm_job_config","CDR_CDM_JOB","1475824500",new_version,old_version,tc_title)
test_obj_run.verifyJobCompletion()


#test_obj_run.checkJobStatus()
test_obj_run.dumpTablesPhoenix(new_version,"SUC",4)
test_obj_run.dumpTablesHive(new_version,"suc",40)

#test_obj_run.diffTable('/data/abhay/Golden_Data_Validation_Framework/Test_Reports/Test_Execution_Current_Old/wrapper/HIVE_db_dump_test_v10','hive')
#test_obj_run.diffTable('/data/abhay/Golden_Data_Validation_Framework/Test_Reports/Test_Execution_Current/wrapper/HBASE_db_dump_test_v22','hbase')

test_obj_run.cleanup()

#test_obj_run.cleanup.parsereport_mail()
