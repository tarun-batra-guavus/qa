"""
.. moduleauthor:: Sandeep Nanda <mail: sandeep.nanda@guavus.com> <skype: snanda85>

Implements Insta node specific APIs.

While defining an insta node in the testbed file, you can provide a `serviceport` parameter (Default value `11111`).
This parameter will be used to fetch the default the instance-id and cubes database from the machine.

Example::

    [INSTA1]
    type=Insta,Psql
    ip=192.168.117.87
    password=admin@123
    serviceport = 55555

"""

from Node import Node
from potluck.logging import logger

import re
import time

class InstaMixin(object):
    def __init__(self, node):
        super(InstaMixin, self).__init__(node)
        try:
            self.serviceport = node["serviceport"]
        except KeyError:
            raise ValueError("serviceport not defined in testbed for insta node %s" % self)


    def upgradeInfinidb(self, *args, **kwargs):
        """Upgrade or Install infinidb depending on its installed status

        This method should be used in upgrade scripts, after the TM node upgrade is complete.
        """
        logger.info("Upgrade/Install infinidb.")

        self.pushMode("config")
        self.sendCmd("pm process insta restart")

        logger.info("Sleeping for 2mins before installing/upgrading infinidb")
        time.sleep(120)
        cur_state = self.getInfinidbStatus()
        if cur_state["InstallStatus"] == "UNINIT":
            ret_val = self._installInfinidb()
        else:
            ret_val = self._upgradeInfinidb()

        if ret_val:
            for instance in self.getInfinidbStatus()["ServiceStatus"].keys():
                self.sendCmd("insta instance %s cube-schema-upgrade apply" % instance)
        self.popMode()
        return ret_val

    def _installInfinidb(self):
        logger.info("Installing Infinidb...")
        self.setMode("config")
        output = self.sendCmd("insta infinidb install")
        if "Installation Initiated" not in output:
            logger.error("Unable to initiate infinidb install")
            return False

        time.sleep(30)
        while "IN_PROGRESS" in self.getInfinidbStatus()["InstallStatus"]:
            logger.info("Infinidb Install in progress. Sleeping for 2mins ")
            time.sleep(120)
        logger.info("Infinidb Install complete.")
        return True

    def _upgradeInfinidb(self):
        logger.info("Upgrading Infinidb...")
        self.setMode("config")
        output = self.sendCmd("insta infinidb upgrade")
        if "Upgrade Initiated" not in output:
            logger.error("Unable to initiate infinidb upgrade")
            return False

        time.sleep(30)
        while "IN_PROGRESS" in self.getInfinidbStatus()["InstallStatus"]:
            logger.info("Infinidb Upgrade in progress. Sleeping for 2mins ")
            time.sleep(120)
        logger.info("Infinidb Upgrade complete.")
        return True

    def getInfinidbStatus(self):
        """Returns Infinidb's status as a dict.  
        Executes command ``insta infinidb get-status-info`` and parse its output to extract the values to return.  
        All the values in this dict are in upper case.

        **Returns:** A dict in the following format::

            {
                "InstallStatus" : "INSTALLED",
                "AdaptorStatus" : "ADAPTOR RUNNING",
                "InstancesConfigured" : 2,
                "ServiceStatus" : {
                    0 : "RUNNING",
                    1 : "CREATING_TABLES"
                }
            }
        """
        ret_dict = {
            "InstallStatus" : None,
            "AdaptorStatus" : None,
            "InstancesConfigured" : 0,
            "ServiceStatus" : {}
        }

        # Change the mode to config prompt
        self.pushMode("config")
        output = self.sendCmd("insta infinidb get-status-info")

        match = re.search(r"Infinidb Install status\s*:\s*([\w ]+)", output, re.I)
        if match:
            ret_dict["InstallStatus"] = match.group(1).strip().upper()
        
        match = re.search(r"Infinidb Adaptor status\s*:\s*([\w ]+)", output, re.I)
        if match:
            ret_dict["AdaptorStatus"] = match.group(1).strip().upper()
        
        match = re.search(r"Total instances configured\s*:\s*([\w ]+)", output, re.I)
        if match:
            ret_dict["InstancesConfigured"] = int(match.group(1).strip())
        
        
        for match in re.finditer(r"Insta instance (\d+) service status\s*:\s*([\w ]+)", output, re.I):
            instance_id = match.group(1)
            ret_dict["ServiceStatus"][instance_id] = match.group(2).strip().upper()

        logger.debug("Parsed InifiniDB status: %s" % ["%s => %s" % (key, value) for key, value in ret_dict.iteritems()])

        # Restore the mode
        self.popMode()
        return ret_dict

    def getInstanceId(self, serviceport=None):
        """Returns the instance id configured with a service port.

        :param serviceport: Service Port to be used to fetch the instance-id. If not given, the serviceport defined in the testbed is used.
        :rtype: Integer
        :returns: Instance id for the corresponding serviceport
        """
        if serviceport is None:
            serviceport = self.serviceport

        self.pushMode("shell")
        output = self.sendCmd("cli -m enable -t 'show run' | grep 'insta instance' | grep 'service-port %s' | awk '{print $3}'" % serviceport).strip()
        #output = self.sendCmd("cli -m enable -t 'show run' | grep 'insta instance' | grep 'service-port' | grep '\%s' | awk '{print $3}'" % serviceport)
        #output = self.sendCmd("cli -m enable -t 'show run' | grep 'insta instance' " )
        logger.debug("Instance id for service port %s: %s" % (serviceport, output))
        self.popMode()
        try:
            return int(output)
        except:
            logger.exception("Unable to extract a valid instance id for service port %s" % serviceport)
            raise ValueError("Unable to extract a valid instance id for service port %s" % serviceport)

    def getServicePort(self, instance):
        self.pushMode("shell")
        output = self.sendCmd("cli -m enable -t 'show run' | grep 'insta instance %s service-port' | awk '{print $NF}'" % instance).strip()
        logger.debug("Service port for instance %s: %s" % (instance, output))
        self.popMode()
        try:
            return int(output)
        except:
            logger.exception("Unable to extract a valid service port for instance %s" % instance)
            raise ValueError("Unable to extract a valid service port for instance %s" % instance)

    def getCubesDatabase(self):
        self.pushMode("shell")
        cubes_db = self.sendCmd("cli -m enable -t 'show run' | grep 'insta instance 1 cubes-database' | awk '{print $NF}'")
        logger.debug("Cubes database: %s" % cubes_db)
        self.popMode()
        return cubes_db

    def resetCubesDatabase(self):
        self._cubes_db = ""
        self.getCubesDatabase()

    def sql(self, query, db="", timeout=300):
        self.pushMode("shell")
        if db == "":
            db = self.getCubesDatabase()
        elif db == None:
            db = ""

        logger.debug("Executing sql query '%s'" % query)

        cmd = """idbmysql --skip-column-names -Be "%s" %s""" % (re.sub('"', r'\"', query), db)
        output = self.sendCmd(cmd, timeout=timeout)
        if re.search("Unrecognized command|command not found|Unknown database", output, re.I):
            logger.error("infinidb is not installed properly")
            output = ""
        elif re.search("You have an error in your SQL syntax", output, re.I):
            logger.error("Syntax Error in sql command")
            output = ""

        self.popMode()
        return output

class InstaNode(InstaMixin, Node):
    pass

