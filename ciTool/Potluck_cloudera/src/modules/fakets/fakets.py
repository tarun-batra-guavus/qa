#!/usr/bin/env python
################################################################################
#
# Purpose:
#     Generate netflows according to a simple IP network
#     Desired traffic flows are defined in a config file (in json format)
#     Supports IPv4 and IPv6
#
# Author: sandeep.nanda@guavus.com (Skype: snanda85)
#
# Modification History:
#     -           - Sandeep Nanda
#                   Initial Creation
#     22-Nov-2013 - Sandeep Nanda
#                   Support for IPv6 addresses
#     25-Nov-2013 - Sandeep Nanda
#                   Performance Improvements
#
################################################################################

import cProfile as profile
import time
import os
import socket
from socket import IPPROTO_UDP, IPPROTO_TCP, IPPROTO_ICMP
import signal
import sys
import json
from random import randint, choice, triangular
from datetime import datetime
from multiprocessing import Process, Queue
from Queue import Empty
from optparse import OptionParser, SUPPRESS_HELP
from threading import Thread

BASE_DIR = os.path.dirname(__file__)
MODULES_DIR = os.path.join(BASE_DIR, "modules")
sys.path.append(MODULES_DIR)

from dpkt.netflow import Netflow5, Netflow9
from ipaddr import IPNetwork

PROFILE = False

# Global config object
class CONFIG(object):
    verbose = True
    collectorIp = "127.0.0.1"
    pool_size = 3
    avg_pcount = 50
    avg_pkt_size = 1100     # Average 1100 bytes per packet
    packets_per_template = 500
    speedFactor = 1
    reverseFlows = False
    user_port_range = [10000, 65535]
    simDuration = 0
    # Port : Probability
    app_ports = {
        80 : 2,
        443 : 2,
        8080 : 2,
        23 : 6,
        55555 : 1,
        25 : 2,
        8443 : 2,
        22 : 3,
        21 : 3,
        520 : 2,
        53 : 2,
        5010 : 1,
        3689 : 1,
    }
    anomaly_pattern = "MEDIUM"

flows = []
processes = []

def recalc_prob_ports():
    global PROB_PORTS
    PROB_PORTS = [int(x) for x in CONFIG.app_ports for y in range(CONFIG.app_ports[x])]

def random_dport():
    return choice(PROB_PORTS)

def log(value, comment=''):
    if CONFIG.verbose == True:
        print "[DEBUG %s] %s" % (comment, value)

def sigBreak(signum, f):
    for process, queue in processes:
        queue.put("SHUTDOWN")

class BookKeeper(Thread):
    def __init__(self, nf_generator, *args, **kwargs):
        self.parent = nf_generator
        return super(BookKeeper, self).__init__(*args, **kwargs)

    def is_anomaly(self):
        anomaly_factor = {
            "HIGH" : 3,
            "MEDIUM" : 5,
            "LOW" : 9
        }.get(CONFIG.anomaly_pattern)
        return self.parent.simtime.hour % anomaly_factor == 0

    def anomaly_pkt_size(self):
        cur_time = self.parent.simtime

        cur_hour = cur_time.hour
        cur_day_factor = cur_time.isoweekday()

        # Multiplication factor taking hour into account
        factor = cur_hour % 4
        if factor == 0:
            factor = 1 

        if cur_hour % 2 != 0:
            min_bytes = abs(CONFIG.avg_pkt_size - (150 * factor)) + cur_day_factor
            pcount = CONFIG.avg_pcount - 20 + cur_day_factor
        else:
            min_bytes = CONFIG.avg_pkt_size + (100 * factor) + cur_day_factor
            pcount = CONFIG.avg_pcount + 20 + cur_day_factor

        max_bytes = min_bytes + 200
        return int(triangular(min_bytes, max_bytes)), pcount

    def avg_pkt_size(self):
        cur_day_factor = abs(self.parent.simtime.isoweekday() - 3) * 6
        min_bytes = CONFIG.avg_pkt_size - 100 + cur_day_factor
        max_bytes = min_bytes + 200
        return int(triangular(min_bytes, max_bytes))

    def run(self):
        while not self.parent._SHUTDOWN:
            # Wake and Update Book-keeping variables of parent
            self.parent.is_anomaly = self.is_anomaly()
            self.parent.anomaly_pkt_size, self.parent.anomaly_pcount = self.anomaly_pkt_size()
            self.parent.avg_pkt_size = self.avg_pkt_size()
            #log("SimDuration: %s. Required Duration: %s" % (self.parent.simDuration, CONFIG.simDuration))
            # Go back to sleep for 10 seconds
            time.sleep(10)
        log("Bookkeeper for '%s' shutdown.." % self.parent.name)

class Netflow_Generator(Process):
    def __init__(self, nw_list, simStartTime, queue, *args, **kwargs):
        super(Netflow_Generator, self).__init__(*args, **kwargs)
        self.nw_list = nw_list
        self.host = CONFIG.collectorIp
        #self.host = "192.168.112.124"
        self.queue = queue
        self._simStartTime = simStartTime
        self._actualStartTime = time.time()
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.records_sent = 0
        self.packets_sent = {}
        self.v9_template_counter = 0
        self.v9_template_ipv4 = Netflow9.NetflowTemplate(template_id=257)    # To be used by v9 flows
        self.v9_template_ipv6 = Netflow9.NetflowTemplate_ipv6(template_id=258)    # To be used by v9 flows
        self.snmp_indices = {}
        self.source_ids = {}
        self.is_anomaly = False     # To be update by book-keeping thread
        self.avg_pkt_size = 1000
        self.anomaly_pcount = 100
        self.anomaly_pkt_size = 500
        self._SHUTDOWN = False
        self._debug_stats = []
        self.DEBUG_STATS = False
 
    @property
    def simtime_secs(self):
        return int(self._simStartTime + self.simDuration)

    @property
    def simtime(self):
        return datetime.fromtimestamp(self.simtime_secs)

    @property
    def simDuration(self):
        return self.actualDuration * CONFIG.speedFactor

    @property
    def actualDuration(self):
        return time.time() - self._actualStartTime

    def debug(self, *args):
        if not self.DEBUG_STATS:
            return
        key = "\t".join(map(str, args))
        self._debug_stats.append(key)

    def dumpDebugStats(self, *args):
        if not self.DEBUG_STATS:
            return
        key = "\t".join(map(str, args))
        filename = "FakeTS_DEBUG_%s.log" % self.name
        with open(filename, "w") as fh:
            fh.write("\n".join(self._debug_stats))

    def shutdown(self):
        log("Shutting down netflow generator child process '%s'.." % self.name)
        self._SHUTDOWN = True
        fps = self.records_sent / self.actualDuration
        log("FPS: %d" % fps)
        self.bookkeeper.join()
        self.dumpDebugStats()
        log("Simtime: %s" % self.simtime.isoformat())
        log("Shutdown complete for netflow generator child process '%s'.." % self.name)

    def run(self):
        if PROFILE:
            return profile.runctx("self.actual_run()", globals(), locals())
        else:
            return self.actual_run()

    def actual_run(self):
        log("Start Netflow Generator child process %s ..." % self.name)
        self.bookkeeper = BookKeeper(self)
        self.bookkeeper.start()
        while True:
            try:
                message = self.queue.get_nowait()
                if message == "SHUTDOWN":
                    return self.shutdown()
            except Empty:
                pass

            if CONFIG.simDuration > 0 and self.simDuration >= CONFIG.simDuration:
                log("Simulation duration reached.")
                return self.shutdown()

            # Number of records to put in one packet
            num_records = randint(1, 18)

            for src_nets, dst_nets, exporters in self.nw_list:
                records = []
                # Gather netflow data for each record
                for index in range(num_records):
                    nf_data = self.netflow_data(src_nets, dst_nets)
                    records.append(nf_data)

                # Send same data in appropriate formats through each exporter
                for exporter in exporters:
                    exporter_name = exporter["name"]
                    if exporter["netflowVersion"] == 5:
                        packed_packet = self.netflow5_packet(records)
                    elif exporter["netflowVersion"] == 9:
                        packed_packet = self.netflow9_packet(records, exporter_name)

                    self.sock.sendto(packed_packet, (self.host, exporter["port"]))
                    self.packets_sent[exporter_name] = self.packets_sent.get(exporter_name, 0) + 1
                self.records_sent += (num_records * len(exporters))

    def snmp_intf(self, *args):
        try:
            return self.snmp_indices[args]
        except KeyError:
            if len(self.snmp_indices) == 0:
                self.snmp_indices[args] = 1
            else:
                max_index = max(self.snmp_indices.values()) + 1
                self.snmp_indices[args] = max_index
        return self.snmp_indices[args]

    def get_source_id(self, *args):
        try:
            return self.source_ids[args]
        except KeyError:
            self.source_ids[args] = randint(1, 65535)
        return self.source_ids[args]

    def netflow_data(self, src_nets, dst_nets):
        # Choose a random subnet
        src_net = choice(src_nets)
        dst_net = choice(dst_nets)

        # Choose any random IP from the subnets
        if src_net.numhosts > 2:
            sip = src_net[randint(1, src_net.numhosts-2)]
        else:
            sip = src_net[0]

        if dst_net.numhosts > 2:
            dip = dst_net[randint(1, dst_net.numhosts-2)]
        else:
            dip = dst_net[0]

        # Create snmp indices of interfaces
        in_intf = self.snmp_intf(src_net)
        out_intf = self.snmp_intf(dst_net)

        # Src and Dst Ports
        sport = randint(*CONFIG.user_port_range)
        dport = random_dport()
        ip_proto = choice((IPPROTO_ICMP, IPPROTO_TCP, IPPROTO_UDP))

        # Amount of data to show
        if self.is_anomaly:
            #min_pcount = self.anomaly_pcount - 10
            min_pcount = (dport % self.anomaly_pcount) + 1
            max_pcount = min_pcount + 40
            pcount = randint(min_pcount, max_pcount)
            bcount = self.anomaly_pkt_size * pcount
        else:
            #min_pcount = CONFIG.avg_pcount - 20
            min_pcount = (dport % CONFIG.avg_pcount) + 1
            max_pcount = min_pcount + 40
            pcount = randint(min_pcount, max_pcount)
            bcount = self.avg_pkt_size * pcount

        #self.debug(self.is_anomaly, min_pcount, max_pcount, self.anomaly_pkt_size, self.avg_pkt_size, pcount, bcount)

        # Figure out Start and End time in secs
        etime = randint(1, 30)
        stime = etime - randint(5, 15)
        if stime < 0:
            stime = 0

        # If reverseFlows are requested, then randomize Uplink/Downlink
        if CONFIG.reverseFlows and randint(0,2) == 1:
            #log("downlink")
            sip, dip = dip, sip
            sport, dport = dport, sport
            in_intf, out_intf = out_intf, in_intf
         # Else Always generate one sided flows

        mpls_label_1 = randint(4000,8000)
        mpls_label_2 = randint(8000,12000)

        # Create data dict
        nf_data = {
            "input_iface" : in_intf,
            "output_iface" : out_intf,
            "pkts_sent" : pcount,
            "bytes_sent" : bcount,
            "start_time" : stime * 1000,    # time in msec
            "end_time" : etime * 1000,  # time in msec
            "src_port" : sport,
            "dst_port" : dport,
            "ip_proto" : ip_proto,
            "mpls_label_1" : mpls_label_1,
            "mpls_label_2" : mpls_label_2,
        }
        # Simple validation
        if sip.version != dip.version:
            raise ValueError("Source and Dest IP addresses are not of same version")

        if sip.version == 4:
            nf_data["src_addr"] = int(sip)
            nf_data["dst_addr"] = int(dip)
        else:
            nf_data["src_addr_v6"] = int(sip)
            nf_data["dst_addr_v6"] = int(dip)
        return nf_data

    def netflow5_record(self, nf_data):
        return Netflow5.NetflowRecord(**nf_data)

    def netflow9_record(self, nf_data):
        if "src_addr_v6" in nf_data:
            return Netflow9.NetflowRecord_ipv6(**nf_data), 6
        else:
            return Netflow9.NetflowRecord(**nf_data), 4

    def netflow5_packet(self, data_records):
        records = [self.netflow5_record(record) for record in data_records]

        #log("%d records" % len(records))
        packet = Netflow5(version=5, sys_uptime=0, unix_sec=self.simtime_secs, data=records)
        try:
            packed_packet = packet.pack()
        except:
            log("Error in packing netflows")
            log("%r" % packet)
            for record in records:
                log("%r" % record)
            raise
        return packed_packet

    def netflow9_packet(self, data_records, exporter_name):
        # Send Template flowset once in 10000 packets
        flowsets = []
        if self.v9_template_counter == 0:
            template_set_ipv4 = Netflow9.NetflowFlowset(data=[self.v9_template_ipv4])
            template_set_ipv6 = Netflow9.NetflowFlowset(data=[self.v9_template_ipv6])
            flowsets.append(template_set_ipv4)
            flowsets.append(template_set_ipv6)

        self.v9_template_counter += len(data_records)
        if self.v9_template_counter >= CONFIG.packets_per_template:
            self.v9_template_counter = 0

        # Segregate IPv4 and IPv6 flows
        ipv4_records = []
        ipv6_records = []
        for record in data_records:
            nf_record, version = self.netflow9_record(record)
            if version == 4:
                ipv4_records.append(nf_record)
            else:
                ipv6_records.append(nf_record)

        # Add data to the flowset
        if ipv4_records:
            ipv4_data_set = Netflow9.NetflowFlowset(template=self.v9_template_ipv4, data=ipv4_records)
            flowsets.append(ipv4_data_set)

        if ipv6_records:
            ipv6_data_set = Netflow9.NetflowFlowset(template=self.v9_template_ipv6, data=ipv6_records)
            flowsets.append(ipv6_data_set)

        packet = Netflow9(sys_uptime=0, unix_sec=self.simtime_secs,
                            package_sequence=self.packets_sent.get(exporter_name, 0),
                            source_id=self.get_source_id(exporter_name),
                            data=flowsets)

        try:
            packed_packet = packet.pack()
        except:
            log("Error in packing netflows")
            log("%r" % packet)
            for record in ipv4_records:
                log("%r" % record)
            for record in ipv6_records:
                log("%r" % record)
            raise
        return packed_packet

def startGenerator():
    # start processes
    # new
    global processes
    num_flows = len(flows)

    log("Networks: %r" % flows)

    if num_flows <= CONFIG.pool_size:
        # Assign same networks to multiple processes
        for i in xrange(0, CONFIG.pool_size):
            if i >= num_flows:
                j = i - num_flows * (i/num_flows)
            else:
                j = i
            flow = flows[j]
            exporter_str = ",".join(r["name"] for r in flow[2])
            log("Creating child process for %s -> %s (Exporters: %s)" % (flow[0], flow[1], exporter_str))
            q = Queue()
            thr_netflow_generator = Netflow_Generator([flow], CONFIG.simStartTime, q)
            processes.append((thr_netflow_generator, q))
    else:
        # Assign multiple networks to same process
        network_list = []
        for i in xrange(0, CONFIG.pool_size):
            network_list.append([])

        i = 1
        for flow in flows:
            network_list[i-1].append(flow)
            if i >= CONFIG.pool_size:
                i = 1
            else:
                i += 1

        for nw_list in network_list:
            q = Queue()
            # Dirty way of printing the flows
            log("Creating child process for flows:\n%s" % "\n".join("%s -> %s (Exporting Routers: %s)" % (nw[0], nw[1], ", ".join(r["name"] for r in nw[2])) for nw in nw_list))
            thr_netflow_generator = Netflow_Generator(nw_list, CONFIG.simStartTime, q)
            processes.append((thr_netflow_generator, q))

    for process, queue in processes:
        #log("Starting child process %s" % process.name)
        process.start()

    # Wait for a signal
    #signal.pause()

    for process, queue in processes:
        # Wait till the processes completes
        process.join()


def init():
    parser = OptionParser()
    parser.add_option("-c", "--config", dest="config", help="Load Configure file (Mandatory)") 
    parser.add_option("-e", "--exportHost", dest="host", default="127.0.0.1", help="Collector Host IP (Default: 127.0.0.1)") 
    parser.add_option("-t", "--startTime", dest="startTime", type="float", help="Start time of simulation in epoch (Default: now)") 
    parser.add_option("-d", "--duration", dest="duration", default=0, type="float", help="Duration of simulation in seconds (Default: 0, means no end)") 
    parser.add_option("-s", "--speed", dest="speedFactor", type="float", default=1, help="Speed factor (Default: 1)") 
    parser.add_option("-r", "--reverse", dest="reverseFlows", action="store_true", help="Flag to generate reverse flows as well") 
    parser.add_option("-p", "--processPoolSize", dest="processPoolSize", type="int", default=5, help="Number of Child processes to spawn (Min:1, Max:24, Default: 5)") 
    parser.add_option("-q", "--quiet", action="store_false", dest="verbose", help="Debug options")
    (options, args) = parser.parse_args()

    global CONFIG
    global flows

    if options.verbose:
        CONFIG.verbose = True

    if not options.config:
        sys.stderr.write("-c/--config is mandatory argument\n")
        parser.print_help()
        sys.exit()

    if not (0 < options.processPoolSize <= 24):
        sys.stderr.write("Process Pool size should be between 1 and 24\n")
        parser.print_help()
        sys.exit()

    with open(options.config) as config_fh:
        config = json.load(config_fh)

    if options.startTime:
        CONFIG.simStartTime = options.startTime
    else:
        CONFIG.simStartTime = time.time()

    if options.duration < 0:
        sys.stderr.write("-d/--duration should be positive value\n")
        parser.print_help()
        sys.exit()
    else:
        CONFIG.simDuration = options.duration

    CONFIG.collectorIp = options.host
    CONFIG.speedFactor = options.speedFactor
    CONFIG.reverseFlows = options.reverseFlows
    CONFIG.pool_size = options.processPoolSize

    # Check if global app ports is present in config
    if "app_ports" in config:
        CONFIG.app_ports = config["app_ports"]
    recalc_prob_ports()

    # Check if global user ports are present in config
    if "user_port_range" in config:
        CONFIG.user_port_range = config["user_port_range"]

    # Check provided Anomaly pattern
    if config.get("variation") in ["HIGH", "MEDIUM", "LOW"] :
        CONFIG.anomaly_pattern = config["variation"]

    log("Exporting to: %s" % CONFIG.collectorIp)
    routers = {}
    for router in config["routers"]:
        router_name = router.get("name")
        router_port = router.get("port")
        router_nets = router.get("ipdests")
        router_nf_version = router.get("netflowVersion", 5)

        # Simple validations
        assert router_name, "Name of router not mentioned"
        assert router_port, "Exporter port not mentioned for %s" % router_name
        assert router_nets, "ipdests not mentioned for %s" % router_name
        assert router_nf_version in (5, 9), "Invalid netflow version for router %s" % router_name

        # Form the dictionary
        routers[router_name] = {
            "name" : router_name,
            "port" : router_port,
            "ipdests" : router_nets,
            "netflowVersion" : router_nf_version
        }

    for traffic in config["traffic"]:
        flow = map(lambda x: x.strip(), traffic["flow"].split("->"))
        src_nets = [IPNetwork(net) for net in routers[flow[0]]["ipdests"].split()]
        dst_nets = [IPNetwork(net) for net in routers[flow[-1]]["ipdests"].split()]

        if "exporters" not in traffic:
            # Take all routers as exporters
            #exporters = [routers[r]["port"] for r in flow]
            exporters = [routers[r] for r in flow]
        else:
            exporters = [routers[r] for r in traffic["exporters"] if r in flow]

        flows.append((src_nets, dst_nets, exporters))

if __name__ == "__main__":
    signal.signal(signal.SIGINT, sigBreak)
    signal.signal(signal.SIGTERM, sigBreak)

    # Data Struct Initialize
    init()

    # Netflow Generator
    startGenerator()
