"""
.. moduleauthor:: Tarun Batra <mail: tarun.batra@guavus.com> <skype: tarun2.batra>

This module provides the base methods to be used with node handles

Most of the methods are used internally by the framework.
View Source to take a look at all the methods.
"""
from potluck.nodes.Node import Node
from potluck.logging import logger
from potluck.nodes import CLI_MODES
import time
import re

class ReMixin(object):
    def configureREparams(self,time_str,rmt_config_file,periodicity=None):
        """Executes ``date d@time_str +'%Y-%m-%d %H:%M'`` command on the node and gets the system time in normal format
         configure RE Params
        """
        self.pushMode(CLI_MODES.config)
        self.sendCmd("pm process re terminate")
        specialChar = '%Y-%m-%d %H:%M'
        self.pushMode(CLI_MODES.shell)
        system_time = self.sendCmd("date -d@%s +'%s'" % (time_str,specialChar))
        year,month,day,hour,minutes = re.split(' |:|-',system_time)
        logger.info ("YEAR :%s MONTH :%s DAY :%s HOUR :%s  MINUTES : %s" % (year,month,day,hour,minutes))          
        if periodicity is not None:
            if int(hour) >  20 and int(periodicity) == 10800 :
                if int(day) ==30 and (int(month) in (4,6,9,11)):
                    minutes_final = int(minutes) + 1
                    hour_final = 0
                    day_final = 1
                    month_final = int(month) + 1
                    year_final = year
                    logger.info ("First Loop")
                elif int(day) == 31 and  (int(month) in (1,3,5,7,8,10)):
                    minutes_final = int(minutes) + 1
                    hour_final = 0
                    day_final = 1
                    month_final = int(month) + 1  
                    year_final = year
                    logger.info ("Second Loop") 
                elif int(day) == 28 and int(month) == 2 :
                    minutes_final = int(minutes) + 1
                    hour_final = 0
                    day_final = 1 
                    month_final = int(month) + 1      
                    year_final = year
                    logger.info ("Third Loop")  
                elif int(day) == 31 and int(month) == 12 :
                    minutes_final = int(minutes) + 1
                    hour_final = 0
                    day_final = 1
                    month_final = 1
                    year_final = int(year) + 1
                    logger.info ("Fourth Loop")
                else:
                    minutes_final = int(minutes) + 1
                    hour_final = 0
                    day_final = int(day) + 1 
                    month_final = int(month)
                    year_final = year
                    logger.info ("Fifth Loop")
            elif int(hour) ==  23 and int(periodicity) == 3600: 
                if int(day) ==30 and (int(month) in (4,6,9,11)):
                    minutes_final = int(minutes) + 1
                    hour_final = 0
                    day_final = 1
                    month_final = int(month) + 1
                    year_final = year
                    logger.info ("Sixth Loop")
                elif int(day) == 31 and  (int(month) in (1,3,5,7,8,10)):
                    minutes_final = int(minutes) + 1
                    hour_final = 0
                    day_final = 1
                    month_final = int(month) + 1
                    year_final = year
                    logger.info ("Seventh Loop")
                elif int(day) == 28 and int(month) == 2 :
                    minutes_final = int(minutes) + 1
                    hour_final = 0
                    day_final = 1
                    month_final = int(month) + 1
                    year_final = year
                    logger.info ("Eighth Loop")
                elif int(day) == 31 and int(month) == 12 :
                    minutes_final = int(minutes) + 1
                    hour_final = 0
                    day_final = 1
                    month_final = 1
                    year_final = int(year) + 1
                    logger.info ("Ninth Loop")
                else:
                    minutes_final = int(minutes) + 1
                    hour_final = 0
                    day_final = int(day) + 1
                    month_final = int(month)
                    year_final = year
                    logger.info ("Tenth Loop")
            else:
                hour_final = int(hour) + int(periodicity)/3600 
                minutes_final = int(minutes) + 1
                day_final = int(day)
                month_final = int(month)
                year_final = year
                logger.info ("Eleventh Loop") 
        else :
            hour_final = int(hour)
            minutes_final = int(minutes) + 1
            day_final = int(day)
            month_final = int(month)
            year_final = year    
            logger.info ("Twelve Loop")      


        if int(month_final) < 10 :
            month_final = "0" + str(month_final)
        if int(day_final) < 10 :
            day_final = "0" + str(day_final)
        if int(hour_final) < 10 :
            hour_final = "0" + str(hour_final)
        if int(minutes_final) < 10 :
            minutes_final = "0" + str(minutes_final)

        startTime = year + "-" + month + "-" + day + "T" + hour + ":" + str(minutes)
        endTime = str(year_final) + "-" + str(month_final) + "-" + str(day_final) + "T" + str(hour_final) + ":" + str(minutes_final)
        logger.info("Checking endTime" +endTime)
        timeRange = startTime + "/" + endTime
        logger.info("Checking timerange" +timeRange)
        re_Timerange_cmd = " pm process re launch params 2 %s" %timeRange
        self.pushMode(CLI_MODES.config)
        self.sendCmd("pm process re launch params 1 -p")
        self.sendCmd(re_Timerange_cmd)
        self.sendCmd(" pm process re launch params 3 -f")
        self.sendCmd(" pm process re launch params 4 %s" % rmt_config_file)
        self.sendCmd("wr mem")
        self.popMode()

        return system_time


    def getReStartTime(self, bviewDir):
        """ Find the latest timestamp from Bview Dir
        """
        self.pushMode(CLI_MODES.shell)
        specialChar = "\." 
        reStartTime = self.sendCmd ("ls -lrt %s | awk -F%s '{ print $2 }' | sort -n |grep -v ^$|head -1 " % (bviewDir,specialChar))
        self.popMode()
        return reStartTime

    def configureREincorrectparams(self,time_str,rmt_config_file):
        """Executes ``date d@time_str +'%Y-%m-%d %H:%M'`` command on the node and gets the system time in normal format
         configure RE Params incorrectly with separator as T instead of /
        """
        self.pushMode(CLI_MODES.config)
        self.sendCmd("pm process re terminate")
        specialChar = '%Y-%m-%d %H:%M'
        self.pushMode(CLI_MODES.shell)
        system_time = self.sendCmd("date -d@%s +'%s'" % (time_str,specialChar))
        year,month,day,hour,minutes = re.split(' |:|-',system_time)
        logger.info ("year :%s month :%s day :%s hour :%s  minutes : %s" % (year,month,day,hour,minutes))
        minutes_final = int(minutes) + 1

        if int(minutes_final) < 10 :
            minutes_final = "0" + str(minutes_final)

        startTime = year + "-" + month + "-" + day + "T" + hour + ":" + str(minutes)
        endTime = str(year) + "-" + str(month) + "-" + str(day) + "T" + str(hour) + ":" + str(minutes_final)
        logger.info("Checking endTime" +endTime)
        timeRange = startTime + "T" + endTime
        logger.info("Checking timerange" +timeRange)
        re_Timerange_cmd = " pm process re launch params 2 %s" %timeRange
        self.pushMode(CLI_MODES.config)
        self.sendCmd("pm process re launch params 1 -p")
        self.sendCmd(re_Timerange_cmd)
        self.sendCmd(" pm process re launch params 3 -f")
        self.sendCmd(" pm process re launch params 4 %s" % rmt_config_file)
        self.sendCmd("wr mem")
        self.popMode()

        return True



    def checkMplsDoneFile(self,doneFile,retryCount,doneFileSleep):
        """Check doneFile . In case it's not found , it will iterate for retryCount times with sleep doneFileSleep
        """
        self.pushMode(CLI_MODES.shell)
        i = 0
        result = 0
        while i < retryCount :
            logs = self.sendCmd("hdfs dfs -ls %s " % doneFile)
            logger.info("Logs show " +logs)
            if "no such file or directory" in logs.lower():
                result = 0
                i = i + 1
                time.sleep(doneFileSleep)
                continue
            else :
                result = 1
                break

        return result


    def checkSnmpDoneFile (self,snmpDoneFile,varLog):
        """Check snmpdoneFile  
        """
        result = 0
        self.pushMode(CLI_MODES.shell)
        pattern1 = self.sendCmd("grep -i 'Snmpwalk: Starting Snmpwalk service with startTime:' %s"  % varLog)
        pattern2 = self.sendCmd("grep -i 'SnmpWalk Service completed successfully' %s" % varLog)
        logs1 = self.sendCmd("hdfs dfs -ls %s " % snmpDoneFile)
        logger.info("pattern1: %s" % pattern1)
        logger.info("pattern2: %s" % pattern2)
        
#         if not "no such file or directory" in logs1.lower() and  pattern1 and pattern2:
        if not "no such file or directory" in logs1.lower():
            logger.info("Done file found")
            logger.info ("Snmp walk started and completed message found in logs and  snmpwalk done file also found ")
            result = 1
        else:
            logger.info("logs while searching the snmpDoneFile: %s" % logs1)
            result = 0

        return result 


class ReNode(ReMixin, Node):
    pass
