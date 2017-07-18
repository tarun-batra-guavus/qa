import pexpect
import sys
import re
import time
import commands
import os
import datetime
from potluck import utils
from potluck.logging import logger
from potluck.reporting import report
from settings import USER_OUTPUT_DIR
import ConfigParser
list_keys_index = []
file_dict = {}
final_dict = {}
ignorelist = []
dict_dict = {}
ignore_file = "userinput/ignore.txt"
configfile = "userinput/healthcheck_config.txt"
class parser(object):

   def __init__(self):
        self.config_parser = ConfigParser.ConfigParser()
        self.common = {}
        self.COMMON_CONF = 'COMMON'


   def check_file(self,file_name_list,optional="no"):
        error_msg = []
        for each in file_name_list:
            if not os.path.isfile(each):
                error_msg.append(str(each))
        if error_msg and optional == "no" :
            report.fail ("Following mandatory input files are missing %s" %(error_msg))
        elif error_msg and optional == "yes" :
            logger.info ("Following optional input files are missing %s " %(error_msg))
            return "false"
        else:
            return "true"

   def parse_file(self,file_name,delimiter):
        list1 = []
        exit_flag_list = []
        list_roles = []
        tmpList = []
        dict1 = {}
        dict2 = {} 
        try:
            with open(file_name) as input:
                for line in input:
                    if line.startswith("#"):
                         continue
                    else:
                         tmpList = line.rstrip("\n").split(delimiter)
                         list1.append(tmpList[0])
                         list_roles.append(tmpList[3])
                         exit_flag_list.append(tmpList[4])
                         dict1[tmpList[0]] = tmpList[1]
                         dict2[tmpList[0]] = tmpList[2] 
            return list1,list_roles,exit_flag_list,dict1,dict2
        except:
            report.fail ("Error while performing operation on file with name %s" % (file_name))
            raise IOError("Error while performing operation on file with name %s" % (file_name))

##Service Name,Stop Command,Start Command,Role,exit_criterion



   def create_dict(self,file_name):
        global config_parser
        global common
        global mop
        self.config_parser.read(file_name)

     #Create dictinary for common variables
        self.common['image_url'] = self.config_parser.get(self.COMMON_CONF, 'image_url')
        self.common['delimiter'] = self.config_parser.get(self.COMMON_CONF, 'delimiter')
        self.common['mode'] = self.config_parser.get(self.COMMON_CONF, 'mode')
        self.common['project'] = self.config_parser.get(self.COMMON_CONF, 'project') 

        return self.common



   def create_dict_version(self,file_name):
        component_ver_dict = {}
        try:
            with open(file_name) as input:
                for eachline in input:
                    tmpList = eachline.rstrip().split("=")
                    component_ver_dict[tmpList[0]] = tmpList[1]
            return component_ver_dict
        except:
            report.fail("Error while performing operation on file with name %s" % (file_name))
            raise IOError("Error while performing operation on file with name %s" % (file_name))

   def create_dict_summary_file(self,file_name):
        summary_var_dict = {}
        try:
            with open(file_name) as input:
                for eachline in input:
                    tmpList = []
                    if eachline.startswith("#"):
                         continue
                    elif not eachline.strip():
                         continue 
                    else:
                         tmpList = eachline.rstrip().split(",")
                         dic_key = str1 = ''.join(str(e) for e in tmpList[:-1])
                         print dic_key
                         summary_var_dict[dic_key] = tmpList[-1].upper()
            return summary_var_dict
        except:
            report.fail("Error while performing operation on file with name %s" % (file_name))
            raise IOError("Error while performing operation on file with name %s" % (file_name))




   def parse_file_1(self,file_name,delimiter):
        val = []
        tmpList = []
        job_dict = {}
        roles_list =[]
        try:
            with open(file_name) as input:
                for line in input:
                    if line.startswith("#"):
                         continue
                    else:
                         tmpList = line.rstrip("\n").split(delimiter)
                         roles_list.append(tmpList[2])
                         if tmpList[2] in job_dict.keys():
                              val = job_dict[tmpList[2]] + [x for i,x in enumerate(tmpList) if i!=2]
                         else:
                              val = [x for i,x in enumerate(tmpList) if i!=2]
                         job_dict[tmpList[2]] = val
            return job_dict,list(set(roles_list))
        except:
            report.fail("Error while performing operation on file with name %s" % (file_name))
            raise IOError("Error while performing operation on file with name %s" % (file_name))




   def parse_file_2(self,file_name,delimiter):
        roles_list_command =[]
        tmpList = []
        try:
            with open(file_name) as input:
                for line in input:
                    if line.startswith("#"):
                         continue
                    else:
                         tmpList = line.rstrip("\n").split(delimiter)
                         roles_list_command+=tmpList[0:3]
            return roles_list_command
        except:
            report.fail("Error while performing operation on file with name %s" % (file_name))
            raise IOError("Error while performing operation on file with name %s" % (file_name))


   def parse_file_3(self,file_name,delimiter):
        val = []
        tmpList = []
        role_file_path_dict = {}
        roles_list =[]
        try:
            with open(file_name) as input:
                for line in input:
                    if line.startswith("#"):
                         continue
                    else:
                         tmpList = line.rstrip("\n").split(delimiter)
                         roles_list.append(tmpList[3])
                         if tmpList[3] in role_file_path_dict.keys():
                              val = role_file_path_dict[tmpList[3]] + [x for i,x in enumerate(tmpList) if i!=3]
                         else:
                              val = [x for i,x in enumerate(tmpList) if i!=3]
                         role_file_path_dict[tmpList[3]] = val
            return role_file_path_dict,list(set(roles_list))
        except:
            report.fail("Error while performing operation on file with name %s" % (file_name))
            raise IOError("Error while performing operation on file with name %s" % (file_name))




   def parse_config_file(self):
        tmpList = []
        config_dict = {}
        
        with open(configfile) as input:
               	for line in input:
                    if line.startswith("#"):
                         pass
                    else:
                         line = line.strip()
			 line = line.split(",")
    			 if line[0] in config_dict:
        			config_dict[line[0]].append(line[1])
    			 else:
        			config_dict[line[0]] = [line[1]]
        return(config_dict)


   def xmlParsing(self,file_name):
        dict_backup = {}
        tree = ET.parse(file_name)
        root = tree.getroot()
        for property in root.findall("property"):
            name = property.findtext("name")
            value = property.findtext("value")
            dict_backup[name] = value
        return dict_backup



   def xmlUpdate(self,file_name,list_keys_changed_values,dict_backup,dict_build):
        flag = 0
        infile = open(file_name,'r')
        file_name_updated = file_name + "_updated"
        outfile = open(file_name_updated,"w")
        for line in infile:
            list_element_found = next((s for s in list_keys_changed_values if s in line), None)
            if list_element_found:
                flag = 1
                flag_element = list_element_found
                outfile.write(line)
                continue
            else:
                if flag == 1:
                    var = ">" + dict_build[flag_element]
                    if line.find(var):
                        replace_var = ">" + dict_backup[flag_element]
                        outfile.write(line.replace(var,replace_var))
                        outfile.write("\n")
                        flag = 0
                        flag_element = ""
                    else:
                        outfile.write(line)
                else:
                    outfile.write(line)
        return "true"


   def createlist(self,file):
	f = open(file,"r")
	list = []
	lines = f.readlines()
	for line in lines:
        	line = line.strip()
        	if line.startswith("#") or line.strip() == '':
                	pass
        	else:
                	list.append(line)
	return list

   def createdict(self,file):
        f = open(file,"r")
        for line in f:
                if line.startswith('#') or line.strip() == '' or line.startswith('[') or line.startswith('\n'):
                        pass
                else:
			if '=' in line:
				line=line.rstrip("\n")
                       		line = line.split('=')
                        	key = line[0].strip(' ')
                        	value = line[1].strip(' ')
                        	file_dict[key]=value
			elif ' ' in line:
				line=line.rstrip("\n").lstrip(' ')
				line = line.split(' ')
				key = line[0].strip(' ')
				value = line[1:]
				file_dict[key]=value
	return file_dict

   def textParsing(self,file_name,delimiter):
        dict_backup = {}
        delimiter_string = "'" + delimiter + "'"
        tmpList =[]
        with open(file_name, 'r') as text_file:
            for eachline in text_file:
                line = eachline.rstrip()
                if line.startswith("#") or not (line):
                    continue
                else:
                    tmpList = line.split(delimiter)
                    dict_backup[tmpList[0]]=tmpList[1]
        return dict_backup

   def textUpdate(self,file_name,list_keys_changed_values,dict_backup,dict_build,delimiter):
        infile = open(file_name,'r')
        file_name_updated = file_name + "_updated"
        outfile = open(file_name_updated,"w")
        for line in infile:
            list_element_found = next((s for s in list_keys_changed_values if s in line), None)
            if list_element_found:
                old_value = r"%s\s*%s\s*%s" %(list_element_found,delimiter,dict_build[list_element_found])
                new_value = r"%s%s%s" %(list_element_found,delimiter,dict_backup[list_element_found])
                line = re.sub(old_value, new_value, line)
                outfile.write(line)
                continue
            else:
                outfile.write(line)

   def createxmldict(self,file):
	xml_dict = {}
	list = []
	counter = 0
	f = open(file,"r")
	lines = f.read().splitlines()
	for line in lines:
        	if line.strip().startswith('#') or line.strip() == '' or line.strip().startswith('<!--') or line.strip().startswith('<description') or line.strip().startswith('<property') or line.strip().startswith('<?'):
                	lines.remove(line)
	for line in lines:
        	counter = counter + 1
        	if "<name>" in line:
                	key = line.split("name>")[1].split("<")[0].strip()
                	value=lines[counter].split("value>")[1].split("<")[0].split(",")[0].strip()
                	xml_dict[key]=value	
	return xml_dict
   def comparedict(self,dict1,dict2,filename):
	list_keys = []
	for key,value in dict1.iteritems():
                if dict2.has_key(key):
                        if dict1[key] == dict2[key]:
                                pass
                        else:
				key = key + ":" + filename
				list_keys.append(key)
	return list_keys
   def comparedict1(self,dict1,dict2):
	list_keys = []
	for key,value in dict1.iteritems():
                if dict2.has_key(key):
                        if dict1[key] == dict2[key]:
                                pass
                        else:
				list_keys.append(key)
	return list_keys
   def comparelist(self,list1,list2,filename):
	list_keys = []
	global list_keys_index 
	if len(list1) == len(list2):
    		for i in range(len(list1)):
        		if list1[i] == list2[i]:
				pass
        		else:
				list_keys.append(list1[i].split(' ')[0] + ":" + filename)
				list_keys_index.append(i)
	return list_keys
   def checkIgnore(self,keys_list,ignore_file):
	f = open(ignore_file,"r")
	for line in f.readlines():
		if line.startswith('#'):
			pass
		else:
			line = line.rstrip("\n")
			ignorelist.append(line)
	logger.info("Parameters not to be considered while taking difference in config files are %s :" %ignorelist)
	for key in keys_list.copy():
		if key in ignorelist:
			keys_list.remove(key)
		else:
			pass
	return 	keys_list


   def dictparser1(self,dict_dict,key,filename,diff_result_file,f):
	#f = open(diff_result_file,"a")
	tmp_values = {}
	for dict in dict_dict:
		if filename in dict:
			tmp_values = dict_dict[dict]
			for k,v in tmp_values.iteritems():
				if k == key:
					f.write("Server:File: Key: value -->"  + dict.split("_")[1]  + "," + filename + "," + k + "," + v  + "\n")
        	        	else:
					pass
	return diff_result_file
 
   def listparser(self,dict_dict,key,filename,diff_result_file,f):
	tmp_list = []
	for dict in dict_dict:
		if filename in dict:
			tmp_list = dict_dict[dict]
			for element in tmp_list:
				index = tmp_list.index(element)
				k = element.split(' ')[0]
				v = element.split(' ')[1:]
				if k == key:
					if index in list_keys_index:
						f.write("Server:File: Key: value -->"  + dict.split("_")[1]  + "," + filename + "," + k + "," + str(v)  + "\n")
        	        	else:
					pass
	return diff_result_file
	
   def createfilelist(self,configdict,role):
	filelist = []
	for key in configdict:
		if key == role:
			for x in configdict[key]:
				filelist.append(x)
	return filelist

   def diff_func(self,filename,list_folder,node_type,base_folder):
        global dict_dict
	diff_list_keys = []
	diff_list = []
	logger.info('\n')
	logger.info("Finding difference in configfile %s....." %filename)
        for folder in sorted(list_folder):
                filename_tmp = USER_OUTPUT_DIR + "/" + node_type + "/" +  folder + "/" +   filename
		if os.stat(filename_tmp).st_size == 0:
                        report.fail(" %s File is empty.Please check" %filename_tmp)
		logger.info("Creating dict of file %s for node %s....." %(filename,folder))
                tmp_file_dict = self.createdict(filename_tmp)
		logger.info("Dict of file %s" %tmp_file_dict)
                dict_dict[node_type + "_" + folder + "_" + filename] = tmp_file_dict.copy()
                tmp_file_dict.clear()
	logger.info('\n')
	logger.info("Dict of file %s among all nodes :%s" %(filename,dict_dict))
        for folder in (list_folder):
			if folder <> base_folder:
                        	for element in (self.comparedict(dict_dict[node_type + "_" + base_folder + "_" + filename], dict_dict[node_type + "_" + folder + "_" + filename],filename)):
					diff_list.append(element)
				list_keys_unique = set(diff_list)
                        	if len(list_keys_unique) == 0:
					logger.info("No difference found in file (%s) between nodes (%s)(%s)....." %(filename,base_folder,folder))
					pass
                        	else:
					logger.info("Difference found in keys are %s:" %list_keys_unique)
                                	diff_list_keys = self.checkIgnore(list_keys_unique,ignore_file)
                                	folder_new = node_type + "_" + folder + "_" + filename
	logger.info("Difference found in %s parameters in %s file" %(diff_list_keys,filename))
 	return diff_list_keys

   def diff_func_text(self,filename,list_folder,node_type,base_folder):
        global dict_dict
	diff_list_keys = []
	diff_list = []
	logger.info('\n')
	logger.info("Finding difference in configfile %s....." %filename)
        for folder in sorted(list_folder):
                filename_tmp = USER_OUTPUT_DIR + "/" + node_type + "/" +  folder + "/" +   filename
		if os.stat(filename_tmp).st_size == 0:
			report.fail(" %s File is empty.Please check" %filename_tmp)
		logger.info("Creating dict of file %s for node %s....." %(filename,folder) + "\n")
                tmp_file_list = self.createlist(filename_tmp)
		logger.info("list of file %s" %tmp_file_list)
                dict_dict[node_type + "_" + folder + "_" + filename] = tmp_file_list
                tmp_file_list = []
	logger.info('\n')
	logger.info("Dict of file %s among all nodes :%s" %(filename,dict_dict))
        for folder in (list_folder):
			if folder <> base_folder:
                        	for element in (self.comparelist(dict_dict[node_type + "_" + base_folder + "_" + filename], dict_dict[node_type + "_" + folder + "_" + filename],filename)):
					diff_list.append(element)
				list_keys_unique = set(diff_list)
                        	if len(list_keys_unique) == 0:
					logger.info("No difference found in file (%s) between nodes (%s)(%s)....." %(filename,base_folder,folder))
					pass
                        	else:
					logger.info("Difference found in keys are %s:" %list_keys_unique)
                                	diff_list_keys = self.checkIgnore(list_keys_unique,ignore_file)
                                	folder_new = node_type + "_" + folder + "_" + filename
	logger.info("Difference found in %s parameters in %s file" %(diff_list_keys,filename))
 	return diff_list_keys
   def diff_func_xml(self,filename,list_folder,node_type,base_folder):
        global dict_dict
	diff_list_keys = []
	diff_list = []
	logger.info('\n')
	logger.info("Finding difference in configfile %s....." %filename)
        for folder in sorted(list_folder):
                filename_tmp = USER_OUTPUT_DIR + "/" + node_type + "/" +  folder + "/" +   filename
		if os.stat(filename_tmp).st_size == 0:
			report.fail(" %s File is empty.Please check" %filename_tmp)
		logger.info("Creating dict of file %s for node %s....." %(filename,folder))
                tmp_file_dict = self.createxmldict(filename_tmp)
		logger.info("Dict of file %s...." %tmp_file_dict)
                dict_dict[node_type + "_" + folder + "_" + filename] = tmp_file_dict.copy()
                tmp_file_dict.clear()
	logger.info('\n')
	logger.info("Dict of file %s among all nodes :%s...." %(filename,dict_dict))
        for folder in (list_folder):
			if folder <> base_folder:
				logger.info("Finding difference in file (%s) between nodes (%s)(%s)....." %(filename,base_folder,folder))
                        	for element in (self.comparedict(dict_dict[node_type + "_" + base_folder + "_" + filename], dict_dict[node_type + "_" + folder + "_" + filename],filename)):
					diff_list.append(element)
				list_keys_unique = set(diff_list)
                        	if len(list_keys_unique) == 0:
					logger.info("No difference found in file (%s) between nodes (%s)(%s)....." %(filename,base_folder,folder))
					pass
                        	else:
					logger.info("Difference found in keys are %s:" %list_keys_unique)
                                	diff_list_keys = self.checkIgnore(list_keys_unique,ignore_file)
                                	folder_new = node_type + "_" + folder + "_" + filename
	logger.info("Difference found in %s parameters in %s file" %(diff_list_keys,filename))
 	return diff_list_keys
   def printdiff(self,diff_list_keys,difffileappend):
	global dict_dict
	diff_result_file = USER_OUTPUT_DIR  + "/" + "difffile" + "_" + difffileappend
	f = open(diff_result_file,"w")
	logger.info("Writing the final difference in file %s" %diff_result_file)
	for keys in diff_list_keys:
		key = keys.split(":")[0]
		file_name = keys.split(":")[1]
        	result_file = self.dictparser1(dict_dict,key,file_name,diff_result_file,f)
	f.close()
	dict_dict.clear()
	return result_file
   def printdifftxt(self,diff_list_keys,difffileappend):
	global dict_dict
	global list_keys_index
	diff_result_file = USER_OUTPUT_DIR  + "/" + "difffile" + "_" + difffileappend
	f = open(diff_result_file,"w")
	for keys in diff_list_keys:
		key = keys.split(":")[0]
		file_name = keys.split(":")[1]
        	result_file = self.listparser(dict_dict,key,file_name,diff_result_file,f)
	f.close()
	dict_dict.clear()
	list_keys_index = []
	return result_file

   def checkreport(self,report_file):
    	f = open(report_file,"r")
   	report_dict = {}
    	ansi_escape_chars = re.compile(r'(?m)((\x1b[^m\r\n]*m)|(\x1b[^\r\n]+\x1b[=>]))')
    	for line in f.readlines():
        	line = line.lstrip(' ')
        	if re.match(r"^\d+.*$",line):
                	line = line.strip("\n")
                	line = line.split(":")
                	key = line[0]
                	value = ansi_escape_chars.sub('', line[1].strip(' '))
                	report_dict[key] = value
    	fail_counter = 0
    	for values in report_dict.values():
        	if 'FAILED' in str(values):
                	fail_counter = fail_counter + 1
	return fail_counter
