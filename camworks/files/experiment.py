#!/usr/bin/python
# -*- coding: utf-8 -*-

# Heavily inspired by https://github.com/MONROE-PROJECT/Experiments/blob/master/experiments/template/files/experiment.py

import os
import json
import zmq
import sys
import netifaces
import time
import threading
from subprocess import check_output
from multiprocessing import Process, Manager
import Queue
import subprocess32 as subprocess
import multiprocessing
import re
import mobile_codes

# Configuration
DEBUG = False
CONFIGFILE = '/monroe/config'

# Default values (overwritable from the scheduler)
# Can only be updated from the main thread and ONLY before any
# other processes are started
EXPCONFIG = {
	# The following value are specific to the monore platform
	"guid": "no.guid.in.config.file",  # Overridden by scheduler
	"storage": 104857600,  # Overridden by scheduler
	"traffic": 104857600,  # Overridden by scheduler
	"script": "jonakarl/experiment-template",  # Overridden by scheduler
	"zmqport": "tcp://172.17.0.1:5556",
	"nodeid": "fake.nodeid",
	"modem_metadata_topic": "MONROE.META.DEVICE.MODEM",
	"gps_metadata_topic": "MONROE.META.DEVICE.GPS",
	# Experiment specific config begins here	
	# "dataversion": 1,  #  Version of experiment
	# "dataid": "MONROE.EXP.JONAKARL.TEMPLATE",  #  Name of experiement
	"meta_grace": 120,  # Grace period to wait for interface metadata
	"exp_grace": 120,  # Grace period before killing experiment
	"exp_interval_check": 5,  # Interval to check if interface is up
	"verbosity": 3,  # 0 = "Mute", 1=error, 2=Information, 3=verbose
	"resultdir": "/monroe/results/",
	# These values are specic for this experiment
	"size": 3*1024,  # The maximum size in Kbytes to download
	"time": 3600,  # The maximum time in seconds for a download,
	"tool_targets": [],
	"middlebox_detection_target": "ec2-35-160-38-157.us-west-2.compute.amazonaws.com"
}

def run_exp(meta_info, expconfig, interface, interface_event):
	# import monroe_exporter here - import already creates state which we want to be per process
	# note the type in initalize - check monroe_exporter.py (!)
	import monroe_exporter
	#monroe_exporter.initalize(30)

	job_queue = Queue.Queue()
	for target in expconfig['tool_targets']:
		job = {
			'target': target,
		}
		job_queue.put(job)

	for _ in range(1):
		worker = threading.Thread(target=run_tools, args=(job_queue, interface, interface_event, expconfig, monroe_exporter, meta_info, ))
		worker.setDaemon(True)
		worker.start()

	job_queue.join()

def run_tools(job_queue, interface, interface_event, expconfig, monroe_exporter, meta_info):
	# wait for extra info
	while(True):
		try:
			meta_info['modem']['extra_ipaddress']
			meta_info['modem']['extra_imsi']
			meta_info['modem']['extra_location']
			break
		except KeyError:
			time.sleep(5)
			continue
	while(True):
		job = job_queue.get()
		run_ping(job, interface, interface_event, expconfig, monroe_exporter, meta_info)
		run_dig(job, interface, interface_event, expconfig, monroe_exporter, meta_info)
		run_traceroute(job, interface, interface_event, expconfig, monroe_exporter, meta_info)
		run_curl(job, interface, interface_event, expconfig, monroe_exporter, meta_info)
		run_curl_middlebox(job, interface, interface_event, expconfig, monroe_exporter, meta_info)
		job_queue.task_done()
		

def run_ping(job, interface, interface_event, expconfig, monroe_exporter, meta_info):
	cmd = ['fping', '-c', '5', '-I', interface, job['target']]
	timeout=False
	time_begin = int(time.time())
	p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
	try:
		stdout, stderr = p.communicate(timeout=None)
	except subprocess.TimeoutExpired:
		timeout=True
		p.kill()
		stdout, stderr = p.communicate()
	time_end = int(time.time())

    # To use monroe_exporter the following fields must be present
    # "DataId"
    # "DataVersion"
    # "NodeId"
    # "SequenceNumber"

	result_object = {
		'NodeId': "ping_" + job['target'] + "_" + expconfig['nodeid'],
		'DataId': interface,
		'DataVersion': 0,
		'Timestamp': time.time(),
		'SequenceNumber': -1,
		'IPAddress': meta_info['modem']['extra_ipaddress'],
		'ImsiMccMnc': meta_info['modem']['extra_imsi'],
		'Location': meta_info['modem']['extra_location'],
		'target': job['target'],
		'interface': interface,
		'measurement_begin': time_begin,
		'measurement_end': time_end,
		'timeout': timeout,
		'cmd': cmd,
		'stdout': stdout,
		'stderr': stderr,
	}

	monroe_exporter.save_output(result_object)


def run_dig(job, interface, interface_event, expconfig, monroe_exporter, meta_info):
	cmd = ['dig.sh', job['target']]
	timeout=False
	time_begin = int(time.time())
	p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
	try:
		stdout, stderr = p.communicate(timeout=None)
	except subprocess.TimeoutExpired:
		timeout=True
		p.kill()
		stdout, stderr = p.communicate()
	time_end = int(time.time())

    # To use monroe_exporter the following fields must be present
    # "DatafId"
    # "DataVersion"
    # "NodeId"
    # "SequenceNumber"

	result_object = {
		'NodeId': "dig_" + job['target'] + "_" + expconfig['nodeid'],
		'DataId': interface,
		'DataVersion': 0,
		'Timestamp': time.time(),
		'SequenceNumber': -1,
		'IPAddress': meta_info['modem']['extra_ipaddress'],
		'ImsiMccMnc': meta_info['modem']['extra_imsi'],
		'Location': meta_info['modem']['extra_location'],
		'target': job['target'],
		'interface': interface,
		'measurement_begin': time_begin,
		'measurement_end': time_end,
		'timeout': timeout,
		'cmd': cmd,
		'stdout': stdout,
		'stderr': stderr,
	}

	monroe_exporter.save_output(result_object)


def run_traceroute(job, interface, interface_event, expconfig, monroe_exporter, meta_info):
	cmd = ['traceroute', job['target']]
	timeout=False
	time_begin = int(time.time())
	p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
	try:
		stdout, stderr = p.communicate(timeout=None)
	except subprocess.TimeoutExpired:
		timeout=True
		p.kill()
		stdout, stderr = p.communicate()
	time_end = int(time.time())
	
    # To use monroe_exporter the following fields must be present
    # "DataId"
    # "DataVersion"
    # "NodeId"
    # "SequenceNumber"

	result_object = {
		'NodeId': "traceroute_" + job['target'] + "_" + expconfig['nodeid'],
		'DataId': interface,
		'DataVersion': 0,
		'Timestamp': time.time(),
		'SequenceNumber': -1,
		'IPAddress': meta_info['modem']['extra_ipaddress'],
		'ImsiMccMnc': meta_info['modem']['extra_imsi'],
		'Location': meta_info['modem']['extra_location'],
		'target': job['target'],
		'interface': interface,
		'measurement_begin': time_begin,
		'measurement_end': time_end,
		'timeout': timeout,
		'cmd': cmd,
		'stdout': stdout,
		'stderr': stderr,
	}

	monroe_exporter.save_output(result_object)


def run_curl(job, interface, interface_event, expconfig, monroe_exporter, meta_info):
	cmd = ['curl.sh', job['target']]
	timeout=False
	time_begin = int(time.time())
	p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
	try:
		stdout, stderr = p.communicate(timeout=None)
	except subprocess.TimeoutExpired:
		timeout=True
		p.kill()
		stdout, stderr = p.communicate()
	time_end = int(time.time())

    # To use monroe_exporter the following fields must be present
    # "DataId"
    # "DataVersion"
    # "NodeId"
    # "SequenceNumber"

	result_object = {
		'NodeId': "curl_" + job['target'] + "_" + expconfig['nodeid'],
		'DataId': interface,
		'DataVersion': 0,
		'Timestamp': time.time(),
		'SequenceNumber': -1,
		'IPAddress': meta_info['modem']['extra_ipaddress'],
		'ImsiMccMnc': meta_info['modem']['extra_imsi'],
		'Location': meta_info['modem']['extra_location'],
		'target': job['target'],
		'interface': interface,
		'measurement_begin': time_begin,
		'measurement_end': time_end,
		'timeout': timeout,
		'cmd': cmd,
		'stdout': stdout,
		'stderr': stderr,
	}

	monroe_exporter.save_output(result_object)


def run_curl_middlebox(job, interface, interface_event, expconfig, monroe_exporter, meta_info):
	cmd = ['curl', '-s', expconfig['middlebox_detection_target']+"?"+expconfig['nodeid']+"_"+interface+"_middlebox_test", '/dev/null']
	timeout=False
	time_begin = int(time.time())
	p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
	try:
		stdout, stderr = p.communicate(timeout=None)
	except subprocess.TimeoutExpired:
		timeout=True
		p.kill()
		stdout, stderr = p.communicate()
	time_end = int(time.time())

    # To use monroe_exporter the following fields must be present
    # "DataId"
    # "DataVersion"
    # "NodeId"
    # "SequenceNumber"

	result_object = {
		'NodeId': "curl_middlebox_" + expconfig['middlebox_detection_target'] + "_" + expconfig['nodeid'],
		'DataId': interface,
		'DataVersion': 0,
		'Timestamp': time.time(),
		'SequenceNumber': -1,
		'IPAddress': meta_info['modem']['extra_ipaddress'],
		'ImsiMccMnc': meta_info['modem']['extra_imsi'],
		'Location': meta_info['modem']['extra_location'],
		'target': job['target'],
		'interface': interface,
		'measurement_begin': time_begin,
		'measurement_end': time_end,
		'timeout': timeout,
		'cmd': cmd,
		'stdout': stdout,
		'stderr': stderr,
	}

	monroe_exporter.save_output(result_object)


def run_tcpdump(interface, meta_info):
	subprocess.Popen(['tcpdump', '-i', interface, '-e', '-v', '-w', '/monroe/results/tcpdump_'+interface+'_'+str(time.time())+'.pcap', ])


def metadata(meta_info, expconfig):
	"""Seperate process that attach to the ZeroMQ socket as a subscriber.

       Will listen forever to messages with topic defined in topic and update
       the meta_info dictionary (a Manager dict).
	"""
	context = zmq.Context()
	socket = context.socket(zmq.SUB)
	socket.connect(expconfig['zmqport'])
	socket.setsockopt(zmq.SUBSCRIBE, bytes(expconfig['modem_metadata_topic']))
	socket.setsockopt(zmq.SUBSCRIBE, bytes(expconfig['gps_metadata_topic']))

	while True:
		data = socket.recv()
		try:
			topic = data.split(" ", 1)[0]
			msg = json.loads(data.split(" ", 1)[1])
			if topic.startswith(expconfig['modem_metadata_topic']):
				if expconfig['verbosity'] > 2:
					print ("Got a modem message for {}, using interface {}").format(msg['Operator'], msg['InterfaceName'])
				# use iccid as unique identifier for the interface as interface names may change
				iccid = msg['ICCID']
				# store extra info in metadata

				try:
					meta_info['modem']['extra_ipaddress'] = msg['IPAddress']
					meta_info['modem']['extra_imsi'] = msg['IMSI']
					meta_info['modem']['extra_location'] = mobile_codes.mcc(meta_info['modem']['extra_imsi'][0:3])[0][0]
				except Exception:
					print("Could update extra information, appending instead: {}".format(e))
				# get internal interface from previous metadata update
				try:
					prev_internal_interface = meta_info['modems'][iccid]['internalinterface']
				except KeyError:
					prev_internal_interface = msg['internalinterface']
				
				internal_interface = msg['internalinterface']

				if check_modem_meta(msg) and internal_interface == prev_internal_interface:
					meta_info['interface_events'][internal_interface].set()
				else:
					print 'An interface has been remapped, killing %s and %s' % (internal_interface, prev_internal_interface)

					# clear previous internal interface
					try:
						meta_info['interface_events'][prev_internal_interface].clear()
					except KeyError:
						pass
					
					# clear new interface since a remapping has happened
					try:
						meta_info['interface_events'][internal_interface].clear()
					except KeyError:
						pass

				# store metadata in dictionary
				try:
					meta_info['modem'][iccid].update(msg)
				except KeyError:
					meta_info['modem'][iccid] = msg

			if topic.startswith(expconfig['gps_metadata_topic']):
				if expconfig['verbosity'] > 2:
					print ("Got a gps message with seq nr {}").format(msg["SequenceNumber"])
				meta_info['gps'].append(msg)

			if expconfig['verbosity'] > 2:
				print "zmq message", topic, msg
		
		except Exception as e:
			if expconfig['verbosity'] > 0:
				print ("Cannot get metadata in template container {}, {}").format(e, expconfig['guid'])
			pass

# Helper functions
def check_if(ifname):
	"""Checks if "internal" interface is up and have got an IP address.

	   This check is to ensure that we have an interface in the experiment
	   container and that we have a internal IP address.
	"""
	return (ifname in netifaces.interfaces() and netifaces.AF_INET in netifaces.ifaddresses(ifname))

def check_modem_meta(info, graceperiod=None):
	"""Checks if "external" interface is up and has an IP adress.

	   This check ensures that we have a current (graceperiod) connection
	   to the Mobile network and an IP adress.
	   For more fine grained information DeviceState or DeviceMode can be used.
	"""
	return ("InternalInterface" in info and
			"Operator" in info and
			"ICCID" in info and
			"Timestamp" in info and
			"IPAddress" in info and
			(graceperiod is None or time.time() - info["Timestamp"] < graceperiod))

def create_and_run_meta_process(expconfig, interfaces):
	m = Manager()
	meta_info = {}
	meta_info['modem'] = m.dict()
	meta_info['gps'] = m.list()
	meta_info['interface_events'] = {}
	for interface in interfaces:
		meta_info['interface_events'][interface] = m.Event()
		meta_info['interface_events'][interface].clear()

	process = Process(target=metadata, args=(meta_info, expconfig, ))
	process.daemon = True
	process.start()
	return (meta_info, process)

def create_and_run_exp_process(meta_info, expconfig, interfaces):
	exp_processes = []

	# Create one process for each interface to orchestrate measurements
	for interface in interfaces:
		print(interface)
		tcpdump_process = Process(target=run_tcpdump, kwargs={'interface': interface, "meta_info": meta_info})
		tcpdump_process.daemon = True
		tcpdump_process.start()
		process = Process(target=run_exp, args=(meta_info, expconfig, interface, meta_info['interface_events'][interface]))
		process.daemon = True
		process.start()
		exp_processes.append(process)
		exp_processes.append(tcpdump_process) # Acceptable practice?

	return exp_processes

if __name__ == '__main__':
	"""The main thread control the processes (experiment/metadata))."""

	if not DEBUG:
		import monroe_exporter
		# Try to get the experiment config as provided by the scheduler
	else:
		# We are in debug state always put out all information
		EXPCONFIG['verbosity'] = 3

	try:
		with open(CONFIGFILE) as configfd:
			EXPCONFIG.update(json.load(configfd))
	except Exception as e:
		print "Cannot retrive expconfig {}".format(e)
		#sys.exit(1)

	# Short hand variables and check so we have all variables we need
	try:
		meta_grace = EXPCONFIG['meta_grace']
		exp_grace = EXPCONFIG['exp_grace'] + EXPCONFIG['time']
		exp_interval_check = EXPCONFIG['exp_interval_check']
		EXPCONFIG['guid']
		EXPCONFIG['modem_metadata_topic']
		EXPCONFIG['gps_metadata_topic']
		EXPCONFIG['zmqport']
		EXPCONFIG['verbosity']
		EXPCONFIG['resultdir']
	except Exception as e:
		print "Missing expconfig variable {}".format(e)
		sys.exit(1)

	# Alternative way to get the nodeid
	#nodefile = open("/nodeid", "r")
	#nodefile_contents = nodefile.read()
	#EXPCONFIG['nodeid'] = re.sub('[^0-9]','', nodefile_contents)

	# get available interfaces
	interfaces = []
	for interface in netifaces.interfaces():
		if interface.startswith("op") or interface.startswith("eth"):
			interfaces.append(interface)
	print "Got interfaces %s" % interfaces

	# Could have used a thread as well but this is true multiprocessing
	# Create a metdata process for getting modem and gps metadata
	print "Starting metadata process"
	meta_info, meta_process = create_and_run_meta_process(EXPCONFIG, interfaces)

	if EXPCONFIG['verbosity'] > 1:
		print "Starting experiment"

	start_time_exp = time.time()

	exp_processes = create_and_run_exp_process(meta_info, EXPCONFIG, interfaces)

	while (time.time() - start_time_exp < exp_grace and
		   any([exp_process.is_alive() for exp_process in exp_processes])):
		
		elapsed_exp = time.time() - start_time_exp
		if EXPCONFIG['verbosity'] > 1:
			print "Running Experiment for {} s".format(elapsed_exp)
		exp_processes_alive = [ exp_process for exp_process in exp_processes if exp_process.is_alive() ]
		exp_processes_alive[0].join(exp_interval_check)

	# Cleanup the processes
	if meta_process.is_alive():
		meta_process.terminate()
	
	for exp_process in exp_processes:
		kill = False
		if exp_process.is_alive():
			kill = True
			exp_process.terminate()
			if EXPCONFIG['verbosity'] > 0:
				print "Experiment took too long time to finish, please check results"
	
	if kill:
		sys.exit(1)

	elapsed = time.time() - start_time_exp

	if EXPCONFIG['verbosity'] > 1:
		print "Finished after {}".format(elapsed)
