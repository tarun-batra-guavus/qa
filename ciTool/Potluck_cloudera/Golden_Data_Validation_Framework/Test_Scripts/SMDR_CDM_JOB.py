import sys
import os
sys.path.insert(0, ("/").join(os.getcwd().split("/")[0:-1]) + "/" + "Modules")
new_version = sys.argv[1]

from core_module import RegressionModule

test_obj_run = RegressionModule()
test_obj_run.connectToMachine("root","root@123","192.168.113.188")

test_obj_run.configUpdateCare("care_smdr_cdm_properties.ini",new_version,"test_version_21","/opt/reflex/opt/care/cdm/smdr")

test_obj_run.runJob("care_cdm_smdr_job_config","SMDR_CDM_JOB",1475802900,new_version)
test_obj_run.verifyJobCompletion()


#test_obj_run.checkJobStatus()
test_obj_run.dumpTablesPhoenix(new_version)
test_obj_run.dumpTablesHive(new_version)

#test_obj_run.diffTable('/data/abhay/Golden_Data_Validation_Framework/Test_Reports/Test_Execution_Current_v20/SMDR_LDM_JOB/HIVE_db_dump_test_version_20','hive')
test_obj_run.diffTable('/data/abhay/Golden_Data_Validation_Framework/Test_Reports/Test_Execution_Current/SMDR_CDM_JOB/HBASE_db_dump_test_version_21','hbase')




#test_obj_run.cleanup()

