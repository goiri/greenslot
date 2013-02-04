#!/usr/bin/env python

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

from gslurmcommons import *

class WorkflowElement:
	def __init__(self, id, runtime, userruntime, nodes, cmd, deps):
		self.id = id
		self.runtime = runtime
		self.userruntime = userruntime
		self.nodes = nodes
		self.cmd = cmd
		self.pre = deps
		self.pos = []
		self.deadline = None

	def getRuntime(self):
		return int(math.floor(self.runtime * ((100.0+EXTRA_INACCURACY)/100.0)))

	def __str__( self ):
		return str(self.id)+" "+str(self.runtime)+" "+str(self.userruntime)+" "+str(self.deadline)+" "+str(self.nodes)+" "+str(self.pre)+" "+str(self.pos)+" "+str(self.cmd)

def readWorkflow(workflowName, deadline):
	works = {}
	# Read workflow
	file = open(workflowName, 'r')
	for line in file:
		if not line.startswith("#") and line != "\n":
			splitLine = line.replace("\t", " ").strip().split(" ")
			# Job info
			id = splitLine[0]
			runtime = parseTime(splitLine[1])
			userruntime = parseTime(splitLine[2])
			nodes = int(splitLine[3])
			# Command
			auxCmd = line.strip().split("\"")
			cmd = auxCmd[1]
			for i in range(2, len(auxCmd)-1):
				cmd += "\""+auxCmd[i]
			# Dependencies
			deps = auxCmd[len(auxCmd)-1].strip().split(" ")
			if deps[0] == "":
				deps = []
			works[id] = WorkflowElement(id, runtime, userruntime, nodes, cmd, deps)

	# Calculate dependencies
	for work in works.values():
		for dep in work.pre:
			works[dep].pos.append(work.id)
		work.deadline = deadline
	
	# Calculate start and end
	start = []
	end = []
	for work in works.values():
		if len(work.pre) == 0:
			start.append(work.id)
		if len(work.pos) == 0:
			end.append(work.id)
	
	# Calculate deadline
	for workId in end:
		calculateDeadline(workId, works, deadline)

	# Sort works
	workSorted = []
	addSorted(start, works, workSorted)
	
	return workSorted
	
def calculateDeadline(workId, works, deadline):
	work = works[workId]
	if deadline < work.deadline:
		work.deadline = deadline
	for workIdPre in work.pre:
		runtime = int(math.ceil(1.0*work.getRuntime()/SLOTLENGTH)*SLOTLENGTH)
		#print "ID="+str(workId)+" Pre="+str(workIdPre)+" Runtime="+str(runtime)+"Deadline="+str(deadline)
		calculateDeadline(workIdPre, works, deadline-runtime)

#def addSorted(workId, works, workSorted):
	#work = works[workId]
	#if work not in workSorted:
		#workSorted.append(work)
		#for workIdPos in work.pos:
			#addSorted(workIdPos, works, workSorted)
			
def addSorted(pre, works, workSorted):
	pos = []
	for workId in pre:
		work = works[workId]
		if work not in workSorted:
			# Check if all the dependencies are there
			all = True
			for preWorkId in work.pre:
				if works[preWorkId] not in workSorted:
					all = False
			if all:
				workSorted.append(work)
				for posWorkId in work.pos:
					pos.append(posWorkId)
	if len(pos)>0:
		addSorted(pos, works, workSorted)