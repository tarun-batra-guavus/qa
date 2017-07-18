import sys
import os
sys.path.insert(0, ("/").join(os.getcwd().split("/")[0:-1]) + "/" + "Modules")
new_version = sys.argv[1]
old_version = "test_v28"
tc_title = "ENRC = OFF, Data Inpiut TIme = 15 jULY 2017"

from core_module import RegressionModule

test_obj_run = RegressionModule(new_version)
test_obj_run.connectToMachine("root","root@123","192.168.113.188")

#test_obj_run.connectToMachine("root","root@123","192.168.194.166")

#test_obj.getCommandOutput(hdfs dfs -put ......)

#test_obj_run.configUpdateCare("care_cdr_ldm_properties.ini",new_version,"/cdr_daily_data_aggregation1_dir/cdr_daily_data_aggregation1/","/opt/reflex/opt/care/ldm/cdr")


topic_list = ["/cdr_daily_data_aggregation1_dir/cdr_daily_data_aggregation1","/cdr_daily_data_aggregation1_dir/cdr_daily_data_aggregation2","/cdr_daily_data_aggregation1_dir/cdr_daily_data_aggregation6","/cdr_daily_data_aggregation1_dir/cdr_daily_data_aggregation9"]
epoch = 1475824500
num_iterations = 4
for x in range(num_iterations):
	print "----------------------------Running CDR_LDM job for timestamp ::: " + str(epoch) + "----------------------------" 
	test_obj_run.configUpdateCare("care_cdr_ldm_properties.ini",new_version,topic_list[x],"/opt/reflex/opt/care/ldm/cdr")
	test_obj_run.runJob("care_cdr_ldm_job_config","CDR_LDM_JOB",str(epoch),new_version,old_version,tc_title)
	test_obj_run.verifyJobCompletion()
	epoch += 900


#test_obj_run.checkJobStatus() #### Not using 
test_obj_run.dumpTablesPhoenix(new_version,"",5)
test_obj_run.dumpTablesHive(new_version,"timestamp,subscriberid",40)


#test_obj_run.diffTable('/data/abhay/Golden_Data_Validation_Framework/Test_Reports/Test_Execution_Current_v28/CDR_LDM_JOB/HIVE_db_dump_test_v28','hive')
#test_obj_run.diffTable('/data/abhay/Golden_Data_Validation_Framework/Test_Reports/Test_Execution_Current_v28/CDR_LDM_JOB/HBASE_db_dump_test_v28','hbase')

test_obj_run.cleanup()

#test_obj_run.cleanup.parsereport_mail()
