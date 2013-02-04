#!/usr/bin/python

"""
GreenSlot makes SLURM aware of solar energy availability.
http://www.research.rutgers.edu/~goiri/
Copyright (C) 2012 Inigo Goiri, Rutgers University

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>
"""

import math
import time
import tempfile
import random
import os
from datetime import datetime,timedelta
from subprocess import call, PIPE, Popen

DEBUG=0

# Scheduling flags
SCHEDULE_GREEN = False
SCHEDULE_BROWN_PRICE = False
SCHEDULE_BROWN_PEAK = False

# Files
#GREEN_AVAILABILITY_FILE = None
#GREEN_AVAILABILITY_FILE = 'data/greenpower.none'
#GREEN_AVAILABILITY_FILE = 'data/greenpower.solar'
#GREEN_AVAILABILITY_FILE = 'data/greenpower9.solar'
#GREEN_AVAILABILITY_FILE = 'data/greenpower9-07-03-2011'
#GREEN_AVAILABILITY_FILE = 'data/greenpower9-07-03-2011-fake'
#GREEN_AVAILABILITY_FILE = 'data/greenpower9-14-06-2011'

#GREEN_AVAILABILITY_FILE = 'data/solarpower-31-05-2010' # More energy
#GREEN_AVAILABILITY_FILE = 'data/solarpower-23-08-2010' # Best for us
#GREEN_AVAILABILITY_FILE = 'data/solarpower-01-11-2010' # Worst for us
#GREEN_AVAILABILITY_FILE = 'data/solarpower-24-01-2011' # Less energy



#BROWN_PRICE_FILE = 'data/browncost.ryan'
#BROWN_PRICE_FILE = 'data/browncost9.ryan'
BROWN_PRICE_FILE = 'data/browncost.nj'
#BROWN_PRICE_FILE = 'data/browncost.none'
#BROWN_PRICE_FILE = 'data/browncost.zero'
#BROWN_PRICE_FILE = 'data/browncost.none'

WORKLOAD_FILE = 'workload/workload.genome'
#WORKLOAD_FILE = 'workload/workload.test'
#WORKLOAD_FILE = None

DUMMY_TASK = "/home/goiri/testscript"

# Base day
BASE_DATE = datetime(2010, 6, 18, 9, 0, 0) # 18/06/20110 9:00 AM


# Maximum scheduling period
TIME_LIMIT = (4*24+8)*3600
#TIME_LIMIT = 30*3600
#TIME_LIMIT = None
#SLOTLENGTH = 900
TOTALTIME = 2*24*60*60
#SLOTLENGTH = 10
#TOTALTIME = 15*60
SPEEDUP = 100
#SPEEDUP = 100
#SLOTLENGTH = 900
SLOTLENGTH = 900
#TOTALTIME = 36*60*60

#TOTALTIME = 80*SLOTLENGTH
#TOTALTIME = 48*60*60
#SLOTLENGTH = 3600
TESTAPP = True

EXTRA_INACCURACY = 20 # 20%

SCHEDULE_EVENT = False
SCHEDULE_SLOT = True
CYCLE_SLOT = True

WORKLOADGEN = True

#BASE_POWER = 1347*1000 # Watts
MAX_POWER = 2300 # Watts

# Maximum graphic size
MAXSIZE = 16

# SLA penalty: economic unit/(hour*node)
PENALTY = 100

#PENALTY = 0

# Price of the peak $/kW
PEAK_COST = 0
# PEAK_COST = 5.5884 # Winter
# PEAK_COST = 13.6136 # Summer

# Power of the Gslurm system
POWER_IDLE_GSLURM = 55+30 # Watts: switch + scheduler

# Maximum scheduling period
numSlots = int(math.ceil(TOTALTIME/SLOTLENGTH))


class Node:
	POWER_S3 = 8.6 # Watts
	POWER_IDLE = 65.0 # Watts
	POWER_AVERAGE = 105.0 # Watts
	POWER_FULL = 150.0 # Watts

# Job power
__powers = {'./01_bowtie.sh':140, './02_grep_chr.sh':90, 'R --slave --file=03_importR.R': 105, 'R --slave --file=04_join.R':102}
def getJobPower(cmd):
	power = 105
	for auxCmd in __powers.keys():
		if cmd.startswith(auxCmd):
			power = __powers[auxCmd]
			break
	return power

# Screen colors
class bcolors:
	HEADER = '\033[95m'
	OKBLUE = '\033[94m'
	OKGREEN = '\033[92m'
	WARNING = '\033[93m'
	FAIL = '\033[91m'
	WHITEBG = '\033[47m'
	BLUEBG = '\033[44m'
	GREENBG = '\033[42m'
	REDBG = '\033[41m'
	ENDC = '\033[0m'

	def disable(self):
		self.HEADER = ''
		self.OKBLUE = ''
		self.OKGREEN = ''
		self.WARNING = ''
		self.FAIL = ''
		self.WHITEBG = ''
		self.BLUEBG = ''
		self.GREENBG = ''
		self.ENDC = ''

# Clean screen
def clearscreen(numlines=100):
	import os
	if os.name == "posix":
		# Unix/Linux/MacOS/BSD/etc
		os.system('clear')
	elif os.name in ("nt", "dos", "ce"):
		# DOS/Windows
		os.system('CLS')
	else:
		# Fallback for other operating systems.
		print '\n' * numlines

# TimeValue
class TimeValue:
	def __init__(self):
		self.t = None
		self.v = None
		
	def __init__(self, t, v):
		self.t = parseTime(t)
		self.v = v
		
	def __lt__(self, other):
		return parseTime(self.t)<parseTime(other.t)
		
	def __str__(self):
		return str(self.t)+" => "+str(self.v)

# Job model
class Job:
	def __init__(self, id=-1, state="UNKNOWN", submit=None, start=None, nodes=1):
		self.id = id
		self.state = state
		self.submit = submit
		self.start = start
		self.end = None
		self.nodes = int(nodes)
		self.nodeList = None
		self.deadline = 0
		self.extradeadline = 0
		self.runtime = 0
		self.workflow = "-"
		self.prevJob = []
		self.cmd = None
		self.cost = 0
	
	def __lt__(self, other):
		if self.getDeadline()==0 and other.getDeadline()==0:
			return True
		elif self.getDeadline()==0:
			return False
		elif other.getDeadline()==0:
			return True
		else:
			return self.getExecTime() < other.getExecTime()
	
	def __str__(self):
		out = str(self.id)+"\t=> "+self.state+"\tN="+str(self.nodes)+"\tDL="+toTimeString(self.deadline)+"\tT="+toTimeString(self.getRuntime())+"\tSubmit="+str(self.submit)+"\tDL="+str(self.getExecTime())
		if self.end != None:
			out+=" End="+str(self.end)
		if self.workflow != "-":
			out+=" Workflow="+str(self.workflow)
		return out
		
	def getRuntime(self):
		return int(math.floor(self.runtime * ((100.0+EXTRA_INACCURACY)/100.0)))
		
	def getExecTime(self):
		a = int(math.ceil(1.0*((self.deadline-self.extradeadline)-self.getRuntime())/SPEEDUP))
		return self.submit + timedelta(seconds=a)
	
	def getDeadline(self):
		ret = self.deadline-self.extradeadline
		if ret<self.getRuntime():
			ret = self.getRuntime()
		return ret

# Interacting with SLURM
# Get all the jobs
def getJobs():
	ret = {}
	pipe=Popen(["scontrol", "-o", "show", "jobs"], stdout=PIPE)
	text = pipe.communicate()[0]
	for line in text.split('\n'):
		if line != "" and not line.startswith('No jobs'):
			job = Job()
			# Read attributes
			splitLine = line.split(' ')
			for i in range(0, len(splitLine)):
				if splitLine[i].startswith("JobId="):
					job.id = splitLine[i][splitLine[i].index('=')+1:]
				elif splitLine[i].startswith("JobState="):
					job.state = splitLine[i][splitLine[i].index('=')+1:]
				elif splitLine[i].startswith("SubmitTime="):
					job.submit = datetime.strptime(splitLine[i][splitLine[i].index('=')+1:], "%Y-%m-%dT%H:%M:%S")
				elif splitLine[i].startswith("StartTime="):
					if splitLine[i][splitLine[i].index('=')+1:] != 'Unknown':
						job.start = datetime.strptime(splitLine[i][splitLine[i].index('=')+1:], "%Y-%m-%dT%H:%M:%S")
				elif splitLine[i].startswith("NumNodes="):
					nodes = splitLine[i][splitLine[i].index('=')+1:]
					if nodes.find('-')>=0:
						job.nodes = int(nodes[0:nodes.index('-')])
					else:
						job.nodes = int(nodes)
				elif splitLine[i].startswith("EndTime="):
					if splitLine[i][splitLine[i].index('=')+1:] != 'Unknown':
						job.end = datetime.strptime(splitLine[i][splitLine[i].index('=')+1:], "%Y-%m-%dT%H:%M:%S")
				elif splitLine[i].startswith("NodeList="):
					if splitLine[i][splitLine[i].index('=')+1:] != '(null)':
						job.nodeList = splitLine[i][splitLine[i].index('=')+1:]
			# Store job info
			if job.id != -1:
				ret[job.id] = job
	# Read GSLURM information
	try:
		for line in open('/tmp/gslurm', 'r'):
			if line != '':
				if line.startswith("workflow"):
					lineSplit = line.strip().split(' ')
					id = lineSplit[1]
					if id in ret:
						workflowId = lineSplit[2]
						ret[id].workflow = workflowId
						for i in range(3, len(lineSplit)):
							auxId = lineSplit[i]
							ret[id].prevJob.append(auxId)
				elif line.startswith("increasedl"):
					lineSplit = line.strip().split(' ')
					id = lineSplit[1]
					if id in ret:
						ret[id].extradeadline += SLOTLENGTH
						#ret[id].deadline = ret[id].deadline-SLOTLENGTH
						#if ret[id].deadline<ret[id].runtime:
							#ret[id].deadline = ret[id].runtime
				else:
					lineSplit = line.strip().split(' ')
					id = lineSplit[0]
					if id in ret:
						deadline = parseTime(lineSplit[1])
						runtime = parseTime(lineSplit[2])
						ret[id].deadline = deadline
						ret[id].runtime = runtime
						cmd = ""
						for i in range(3, len(lineSplit)):
							cmd += lineSplit[i]+" "
						cmd = cmd.strip()
						if cmd != "":
							ret[id].cmd = cmd
	except IOError:
		open('/tmp/gslurm', 'w')

	return ret

def getJobsFast():
	ret = {}
	pipe=Popen(["scontrol", "-o", "show", "jobs"], stdout=PIPE)
	text = pipe.communicate()[0]
	for line in text.split('\n'):
		if line != "" and not line.startswith('No jobs'):
			job = Job()
			# Read attributes
			splitLine = line.split(' ')
			for i in range(0, len(splitLine)):
				if splitLine[i].startswith("JobId="):
					job.id = splitLine[i][splitLine[i].index('=')+1:]
				elif splitLine[i].startswith("JobState="):
					job.state = splitLine[i][splitLine[i].index('=')+1:]
				elif splitLine[i].startswith("SubmitTime="):
					job.submit = datetime.strptime(splitLine[i][splitLine[i].index('=')+1:], "%Y-%m-%dT%H:%M:%S")
				elif splitLine[i].startswith("StartTime="):
					if splitLine[i][splitLine[i].index('=')+1:] != 'Unknown':
						job.start = datetime.strptime(splitLine[i][splitLine[i].index('=')+1:], "%Y-%m-%dT%H:%M:%S")
				elif splitLine[i].startswith("NumNodes="):
					nodes = splitLine[i][splitLine[i].index('=')+1:]
					if nodes.find('-')>=0:
						job.nodes = int(nodes[0:nodes.index('-')])
					else:
						job.nodes = int(nodes)
				elif splitLine[i].startswith("EndTime="):
					if splitLine[i][splitLine[i].index('=')+1:] != 'Unknown':
						job.end = datetime.strptime(splitLine[i][splitLine[i].index('=')+1:], "%Y-%m-%dT%H:%M:%S")
				elif splitLine[i].startswith("NodeList="):
					if splitLine[i][splitLine[i].index('=')+1:] != '(null)':
						job.nodeList = splitLine[i][splitLine[i].index('=')+1:]
			# Store job info
			if job.id != -1:
				ret[job.id] = job
	return ret
	


# Get all the nodes
def getNodes():
	ret = {}
	pipe=Popen(["scontrol", "-o", "show", "nodes"], stdout=PIPE)
	text = pipe.communicate()[0]

	for line in text.split('\n'):
		if line != "":
			splitLine = line.split(' ')
			name = splitLine[0][splitLine[0].index('=')+1:]
			for i in range(0, len(splitLine)):
				if splitLine[i].startswith('State='):
					state = splitLine[i][splitLine[i].index('=')+1:]
					if state=='DOWN':
						ret[name] = False
					elif state=='DOWN*' or state=='IDLE*' or state=='0':
						ret[name] = None
					else:
						ret[name] = state
					break
	return ret

# Get a node status
def getNodeStatus(nodeId):
	ret = False
	pipe=Popen(["scontrol", "-o", "show", "nodes", nodeId], stdout=PIPE)
	text = pipe.communicate()[0]

	for line in text.split('\n'):
		if line != '':
			splitLine = line.split(' ')
			for i in range(0, len(splitLine)):
				if splitLine[i].startswith("State="):
					state = splitLine[i][splitLine[i].index('=')+1:]
					if state!='DOWN' and state!='DOWN*' and state!='IDLE*' and state!='0':
						ret= state
					break
	return ret

# Set a node status: turn on or off
def setNodeStatus(nodeId, running):
	current = getNodeStatus(nodeId)
	if running and not current:
		exit = call(["scontrol", "-o", "update", "NodeName="+str(nodeId), "State=IDLE"], stderr=PIPE)
	if not running and current:
		exit = call(["scontrol", "-o", "update", "NodeName="+str(nodeId), "State=DOWN"], stderr=PIPE)

# Set a job priority
def setJobPriority(jobId, priority):
	exit = call(["scontrol", "-o", "update", "JobId="+str(jobId), "Priority="+str(priority)], stderr=PIPE)

def suspendJob(jobId):
	exit = call(["scontrol", "suspend", str(jobId)], stderr=PIPE)
	
def resumeJob(jobId):
	exit = call(["scontrol", "resume", str(jobId)], stderr=PIPE)

# Cancel a job
def cancelJob(jobId):
	exit = call(["scancel", str(jobId)], stderr=PIPE)



# Submit a job
def submitJob(command, runtime, deadline, nodes=1):
	return submitJob(command, runtime, runtime, deadline, nodes)
	
def submitJob(command, runtime, userruntime, deadline, nodes=1):
	submitCommand = command
	if SPEEDUP == 1 and TESTAPP == False:
		submitCommand = createBatchScript(command)
	else:
		submitCommand = DUMMY_TASK+" "+str(int(math.floor(runtime/SPEEDUP)))
	cmd = ["sbatch", "-H", "-D", "/tmp", "-N", str(nodes)]
	for c in submitCommand.split(" "):
		cmd.append(c)
	pipe=Popen(cmd, stdout=PIPE)
	text = pipe.communicate()[0]
	aux = text.split('\n')[0].split(" ")
	if len(aux)>=4:
		jobId = aux[3]
	else:
		jobId = -1
	
	# Write data to file
	file = open("/tmp/gslurm", 'a')
	file.write(str(jobId)+" "+str(deadline)+" "+str(userruntime)+" "+command+"\n")
	file.close()
	return jobId

# Increase deadline
def increaseDeadline(jobId):
	file = open("/tmp/gslurm", 'a')
	file.write("increasedl "+str(jobId)+"\n")
	file.close()


def createBatchScript(cmd):
	#file = tempfile.NamedTemporaryFile(prefix="gslurm-", mode='w')
	tmpName = "/tmp/gslurm-"+str(random.randint(1000,9999))
	while os.path.exists(tmpName):
		tmpName = "/tmp/gslurm-"+str(random.randint(1000,9999))
	file = open(tmpName, 'w')
	file.write("#!/bin/bash\n")
	file.write(cmd+"\n")
	file.close()
	return tmpName

# Aux function to parse a time data
def parseTime(time):
	ret = 0
	if isinstance(time, str):
		aux = time.strip()
		if aux.find('d')>=0:
			index = aux.find('d')
			ret += 24*60*60*int(aux[0:index])
			if index+1<len(aux):
				ret += parseTime(aux[index+1:])
		elif aux.find('h')>=0:
			index = aux.find('h')
			ret += 60*60*int(aux[0:index])
			if index+1<len(aux):
				ret += parseTime(aux[index+1:])
		elif aux.find('m')>=0:
			index = aux.find('m')
			ret += 60*int(aux[0:index])
			if index+1<len(aux):
				ret += parseTime(aux[index+1:])
		elif aux.find('s')>=0:
			index = aux.find('s')
			ret += int(aux[0:index])
			if index+1<len(aux):
				ret += parseTime(aux[index+1:])
		else:
			ret += int(aux)
	else:
		ret = time
	return ret

def toSeconds(td):
	ret = td.seconds
	ret += 24*60*60*td.days
	if td.microseconds > 500*1000:
		ret += 1
	return ret

# From time to string
def toTimeString(time):
	ret = ""
	# Day
	aux = time/(24*60*60)
	if aux>0:
		ret += str(aux)+"d"
		time = time - aux*(24*60*60)
	
	# Hour
	aux = time/(60*60)
	if aux>0:
		ret += str(aux)+"h"
		time = time - aux*(60*60)
		
	# Minute
	aux = time/(60)
	if aux>0:
		ret += str(aux)+"m"
		time = time - aux*(60)
		
	# Seconds
	if time>0:
		ret += str(time)+"s"
	
	if ret == "":
		ret = "0"
	
	return ret

def diffHours(dt1,dt2):
	sec1 = time.mktime(dt1.timetuple())	
	sec2 = time.mktime(dt2.timetuple())		

	return int((sec2-sec2)/3600)

def getSunInfo(date):
	sunrise = 7
	if (date.month>=3 and date.month<9):
		sunrise = 6
	sunset = 17
	if date.month>=2 and date.month<4:
		sunset = 18
	elif date.month>=4 and date.month<6:
		sunset = 19
	elif date.month>=6 and date.month<8:
		sunset = 20
	elif date.month>=8 and date.month<9:
		sunset = 19
	elif date.month>=9 and date.month<10:
		sunset = 18
	elif date.month>=10:
		sunset = 17
	#nightLength = 24-(sunset-sunrise)
	#return (nightLength, sunrise, sunset)
	return (sunrise, sunset)
	
def getMaxEnergyDay(date):
	energy = 16.5 # 
	
	# 11.58+6.49=18.07
	# vs
	# 14.7*2
	
	if date.month == 1:
		energy = 9.03
	elif date.month == 2:
		energy = 13.88
	elif date.month == 3:
		energy = 14.3
	elif date.month == 4:
		energy = 16.1
	elif date.month == 5:
		energy = 16.5
	elif date.month == 6:
		energy = 15.33
	elif date.month == 7:
		energy = 14.7
	elif date.month == 8:
		energy = 14.49
	elif date.month == 9:
		energy = 13.71
	elif date.month == 10:
		energy = 12.26
	elif date.month == 11:
		energy = 11.08
	elif date.month == 12:
		energy = 8.86
	
	# Scale down
	energy = 1000.0*(energy/2300.0)*MAX_POWER
	
	return energy