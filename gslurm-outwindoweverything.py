#!/usr/bin/python

"""
GreenSlot makes SLURM aware of solar energy availability.
http://www.research.rutgers.edu/~goiri/
Copyright (C) 2012 Inigo Goiri and Ricardo Bianchini.
All rights reserved. Dept. of Computer Science, Rutgers University.

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

from subprocess import call, PIPE, Popen
from datetime import datetime, timedelta
from math import *

from gslurmcommons import *


# Get the time for the deadline
def getExecTimeDeadline(job):
	return job.submit + timedelta(seconds=job.getDeadline()) - timedelta(seconds=job.getRuntime())

# Get the available green power
def getGreenPowerAvailability():
	greenAvailability = []
	file = open('greenpower', 'r')
	for line in file:
		if line != '' and line.find("#")!=0:
			lineSplit = line.strip().expandtabs(1).split(' ')
			t=int(lineSplit[0])
			p=float(lineSplit[1])
			greenAvailability.append(TimeValue(t,p))
	file.close()
	return greenAvailability

# Get the cost of the brown energy
def getBrownPowerPrice():
	brownPrice = []
	file = open('browncost', 'r')
	for line in file:
		if line != '' and line.find("#")!=0:
			lineSplit = line.strip().expandtabs(1).split(' ')
			t=int(lineSplit[0])
			p=float(lineSplit[1])
			brownPrice.append(TimeValue(t,p))
	file.close()
	return brownPrice

# Reduce the deadline of the next jobs
#def increaseDeadlineJobs(job, jobs):
	#reduceJobs = getPreviousJobs(job, jobs)
	#print "NEW DEBUG: jobs to reduce deadline = "+str(reduceJobs)+"!!!!!!!!!!!!!!!!!!!!"
	#for jobId in reduceJobs:
		#increaseDeadline(jobId)
def increaseDeadlineJobs(jobs):
	#print "NEW DEBUG: jobs to reduce deadline = "+str(jobs)+"!!!!!!!!!!!!!!!!!!!!"
	for jobId in jobs:
		increaseDeadline(jobId)

# WORKS
#def getPreviousJobs(job, jobs):
	#prevJobs = [job.id]
	#for jobId in job.prevJob:
		#if jobId in jobs:
			#for jobIdToAdd in getPreviousJobs(jobs[jobId], jobs):
				#if jobIdToAdd not in prevJobs:
					#prevJobs.append(jobIdToAdd)
	#return prevJobs

def getPreviousJobs(job, jobs):
	#prevJobs = [job.id]
	prevJobs = []
	for jobId in job.prevJob:
		if jobId in jobs:
			jobToAdd = jobs[jobId]
			if jobId not in prevJobs:
				prevJobs.append(jobId)
			for jobIdToAdd in getPreviousJobs(jobToAdd, jobs):
				if jobIdToAdd not in prevJobs:
					prevJobs.append(jobIdToAdd)
	return prevJobs

# Schedule jobs.
# We first update the green energy predicted to be available based on the jobs that are already running.
# Then, for each job that is not yet running (in Least Slack Time First order), we find the cheapest set of slots for it to use.
# This set depends on the green energy predicted and the number of nodes left by previously running and already-scheduled jobs.
# The latest starting time is the deadline of the job minus its expected run time.
# The slack is the latest starting time minus the current time.
# To properly handle workflows, the scheduler does not start a job before the jobs that it depends on have completed.
def schedule(dateCurrent, timeElapsed, peakBrown, greenAvailArray, brownPriceArray, options=None):
	flagScheduleGreen = SCHEDULE_GREEN
	flagScheduleBrown = SCHEDULE_BROWN_PRICE
	flagScheduleReverse = False
	peakCost = PEAK_COST
	
	# Parse options
	if options != None:
		# Green availability
		if options.schedGreen == True:
			flagScheduleGreen = True
		elif options.schedGreen == False:
			flagScheduleGreen = False
		# Brown price
		if options.schedBrown == True:
			flagScheduleBrown = True
		elif options.schedBrown == False:
			flagScheduleBrown = False
		# Schedule peak price
		if options.peakCost != None:
			peakCost = options.peakCost
		# Reverse
		if options.schedReverse == True:
			flagScheduleReverse = True
		elif options.schedReverse == False:
			flagScheduleReverse = False

	# Current date
	timeNow = datetime.now()
	timeNow = datetime(timeNow.year, timeNow.month, timeNow.day, timeNow.hour, timeNow.minute, timeNow.second)

	# Calculate constants
	(sunrise, sunset) = getSunInfo(dateCurrent)

	# Generate schedule array
	nodes = getNodes()
	numNodes = 0
	for nodeStatus in nodes.values():
		if nodeStatus != None:
			numNodes+=1
	scheduleArray = []
	for i in range(0, numSlots):
		scheduleArray.append(numNodes)

	# Calculate idle power
	powerIdle = POWER_IDLE_GSLURM
	for i in range(0,numNodes):
		powerIdle += Node.POWER_S3

	# Copy green energy availability and initialize consumption arrays (including idle power)
	consumedBrown = []
	auxGreenAvailArray = []
	consumedGreen = []
	surplusGreen = []
	cheapPriceBrown = brownPriceArray[0]
	#availEnergyGreen = 0.0
	for i in range(0, numSlots):
		consumedBrown.append(0.0)
		consumedGreen.append(0.0)
		
		# Update consumptions
		if not flagScheduleGreen:
			auxGreenAvailArray.append(0.0)
			reqEnergySlot = powerIdle * SLOTLENGTH/3600.0 # Wh
			consumedBrown[i] += reqEnergySlot
			if consumedBrown[i]>peakBrown:
				peakBrown = consumedBrown[i]
		else:
			auxGreenAvailArray.append(greenAvailArray[i]*(SLOTLENGTH/3600.0))
			reqEnergySlot = powerIdle * SLOTLENGTH/3600.0 # Wh
			if auxGreenAvailArray[i]>reqEnergySlot:
				consumedGreen[i] += reqEnergySlot
				auxGreenAvailArray[i] = auxGreenAvailArray[i]-reqEnergySlot
			else:
				consumedGreen[i] += auxGreenAvailArray[i]
				consumedBrown[i] += reqEnergySlot-auxGreenAvailArray[i]
				if consumedBrown[i]>peakBrown:
					peakBrown = consumedBrown[i]
				auxGreenAvailArray[i] = 0.0
		surplusGreen.append(auxGreenAvailArray[i])
		
		# Get energy information
		if brownPriceArray[i]<cheapPriceBrown:
			# Get cheapest brown price
			cheapPriceBrown = brownPriceArray[i]
		#availEnergyGreen += greenAvailArray[i]*SLOTLENGTH/3600.0
	
	
	# Managing jobs
	# Reading submission information
	jobs = getJobs()
	if DEBUG >= 4:
		if len(jobs)>0:
			print "Jobs:"
			for id in jobs:
				print "  "+str(jobs[id])

	# Sort job queue: earliest deadline first
	jobQueue = sorted(jobs.values())
	jobRun = []
	todel = []
	for i in range(0, len(jobQueue)):
		job = jobQueue[i]
		if job.state != 'PENDING':
			todel.append(job)
			if job.state == 'RUNNING':
				jobRun.append(job)

	for job in todel:
		jobQueue.remove(job)

	# Define when a job should finish
	endJobs = {}
	
	# Get information from already running jobs
	for job in jobRun:
		remaining = job.getRuntime() - int(math.ceil(1.0*toSeconds(timeNow-job.start)*SPEEDUP))
		remainingSlots = int(math.ceil(1.0*remaining/SLOTLENGTH))
		if remainingSlots<1:
			remainingSlots = 1
		for i in range(0,remainingSlots):
			scheduleArray[i] = scheduleArray[i]-job.nodes
			reqEnergySlot = job.nodes * (Node.POWER_AVERAGE-Node.POWER_S3) * SLOTLENGTH/3600.0 # Wh
			if auxGreenAvailArray[i]>reqEnergySlot:
				consumedGreen[i] += reqEnergySlot
				auxGreenAvailArray[i] = auxGreenAvailArray[i]-reqEnergySlot
			else:
				consumedGreen[i] += auxGreenAvailArray[i]
				consumedBrown[i] += reqEnergySlot-auxGreenAvailArray[i]
				if consumedBrown[i]>peakBrown:
					peakBrown = consumedBrown[i]
				auxGreenAvailArray[i] = 0.0
		endJobs[job.id] = remainingSlots
	
	# Start scheduling jobs in the queue
	jobSchedule = []
	for i in range(0, numSlots):
		jobSchedule.append([])
	
	
	# Compute the energy that can be executed out of the window
	# Compute the total green energy
	#energyGreenOutWindow = availEnergyGreen
	#energyGreenOutWindow = getMaxEnergyDay(dateCurrent)*2
	numJobsGreenOutWindow = 0
	# Walk the queue reversely
	#for job in reversed(jobQueue):
		#runSlots = int(math.ceil(1.0*job.getRuntime()/SLOTLENGTH))
		#reqEnergy = job.nodes * (Node.POWER_AVERAGE-Node.POWER_S3) * SLOTLENGTH/3600.0 * runSlots # Wh
		#energyGreenOutWindow -= reqEnergy
		#if energyGreenOutWindow<0:
			#break
		#numJobsGreenOutWindow += 1
	
	# Schedule jobs in the jobQueue.
	# The queue is in earliest latest starting time order.
	# For each job, we fill a cost array, in which each entry i corresponds to the cost of starting the job at slot i.
	jobsIncreaseDeadline = []
	worksIncreaseDeadline = []
	scheduledNumJob = 0
	for job in jobQueue:
		# Calculate slots to run
		runSlots = int(math.ceil(1.0*job.getRuntime()/SLOTLENGTH))
		
		# Calculate deadline slot
		deadlineSlot = -1
		endDeadlineSlot = -1
		if getExecTimeDeadline(job) >= timeNow:
			#deadline = toSeconds( job.submit + timedelta(seconds=job.deadline) - timedelta(seconds=job.getRuntime()) - timeNow )
			#deadline = toSeconds(getExecTimeDeadline(job)-timeNow)
			deadline = toSeconds(job.submit-timeNow)*SPEEDUP + (job.getDeadline()-job.getRuntime())
			deadlineSlot = int(math.floor(1.0*deadline/SLOTLENGTH))
			endDeadline = toSeconds(job.submit-timeNow)*SPEEDUP + job.getDeadline()
			endDeadlineSlot = int(math.floor(1.0*endDeadline/SLOTLENGTH))
		# Calculate submit slot
		submit = toSeconds(job.submit-timeNow)*SPEEDUP
		submitSlot = int(math.ceil(1.0*submit/SLOTLENGTH))
		
		# Get the maximum end time of the previous jobs
		prevJobSlot = 0
		#for prev in job.prevJob:
			#if (prev in endJobs) and endJobs[prev]>prevJobSlot:
				#prevJobSlot = endJobs[prev]
		
		# Calculate cost to allocate job in each slot
		leftBestSlot = -1
		leftBestCost = None
		leftBestViol = None
		leftBestCheap = None
		rightBestSlot = -1
		rightBestCost = None
		rightBestViol = None
		rightBestCheap = None
		for currentSlot in range(prevJobSlot, numSlots):
			if currentSlot+runSlots > numSlots:
				# If this slot would cause the job to end beyond our horizon, cannot schedule it in this slot or in any later slots
				#jobCosts[currentSlot] = None
				break
			else:
				# Check if this slot is a cheap slot
				cheapSlot = True
				# Current peak power
				auxPeakBrown = peakBrown-500
				if auxPeakBrown<0:
					auxPeakBrown = 0
				# Calculate the total cost of executing the job starting at "slot"
				# Aggregate the cost in each slot (currentSlot+iSlot)
				cost = 0.0
				for iSlot in range(0, runSlots):
					# If there are not enough free nodes, discard the slot
					if scheduleArray[currentSlot+iSlot] < job.nodes:
						cost = -1
						break
					else:
						# Calculate the cost of running in slot "currentSlot+iSlot"
						#  Green energy is assumed to have 0 cost
						reqEnergySlot = job.nodes * (Node.POWER_AVERAGE-Node.POWER_S3) * SLOTLENGTH/3600.0 # Wh
						if auxGreenAvailArray[currentSlot+iSlot] < reqEnergySlot:
							# Energy -> Cost
							reqBrown = reqEnergySlot - auxGreenAvailArray[currentSlot+iSlot]
							price = brownPriceArray[currentSlot+iSlot]
							# Check if this is cheap energy
							if price>cheapPriceBrown and flagScheduleBrown:
								cheapSlot = False
							# Assign a fixed price if we don't schedule brown
							if not flagScheduleBrown:
								price = 0.02
							cost += reqBrown * price/1000.0 # kWh*cost/kWh
							# Add cost for new peak. PEAK_COST is a cost per KW
							newPower = (consumedBrown[currentSlot+iSlot] + reqBrown)/(SLOTLENGTH/3600.0)
							if newPower>auxPeakBrown and peakCost>0:
								cost += peakCost * (newPower-auxPeakBrown)/1000.0
								#print "Extra cost form "+str(peakCost * (newPower-auxPeakBrown)/1000.0)
								auxPeakBrown = newPower
								# If the peak changes, it's no cheap anymore
								cheapSlot = False
								
				#print str(job.id)+"@"+str(currentSlot)+"] cheap slot? " +str(cheapSlot)+" cost="+str(cost)
				
				# Assign cost to slot
				if cost>=0:
					# If this slot would make it impossible to meet the deadline, add penalty
					violated = False
					if currentSlot>deadlineSlot:
						pen = (1.0*PENALTY*SLOTLENGTH/3600.0) * job.nodes
						cost += pen*(currentSlot-deadlineSlot)
						violated = True
						
					if leftBestSlot<0 or cost<leftBestCost:
						leftBestSlot = currentSlot
						leftBestCost = cost
						leftBestViol = violated
						leftBestCheap = cheapSlot
						rightBestSlot = currentSlot
						rightBestCost = cost
						rightBestViol = violated
						rightBestCheap = cheapSlot

					if flagScheduleReverse:
						if (cost>0 and cost==rightBestCost):
							rightBestSlot = currentSlot
							rightBestCost = cost
							rightBestViol = violated
							rightBestCheap = cheapSlot
		
		#print str(job.id)+"@"+str(leftBestSlot)+"] $" +str(leftBestCost)+" cheap? "+str(leftBestCheap)
		
		# Evaluate left and right bestSlot
		bestSlot = -1
		bestCost = None
		bestViol = None
		bestCheap = None
		if leftBestCost==0 or leftBestSlot==rightBestSlot:
			# Schedule left
			bestSlot = leftBestSlot
			bestCost = leftBestCost
			bestViol = leftBestViol
			bestCheap = leftBestCheap
		else:
			# Schedule right
			bestSlot = rightBestSlot
			bestCost = rightBestCost
			bestViol = rightBestViol
			bestCheap = rightBestCheap
			
			# Calculate date start and end
			leftDateSlot = dateCurrent + timedelta(seconds=(leftBestSlot*SLOTLENGTH))
			rightDateSlot = dateCurrent + timedelta(seconds=((rightBestSlot+runSlots)*SLOTLENGTH))
			
			if leftDateSlot.hour>sunset and rightDateSlot.hour<sunrise:
				# Schedule left because the gap to run the job is during night
				bestSlot = leftBestSlot
				bestCost = leftBestCost
				bestViol = leftBestViol
				bestCheap = leftBestCheap
		
		# Increase deadline to avoid violation
		if bestSlot>0 and bestViol==True:
			if job.workflow not in worksIncreaseDeadline:
				worksIncreaseDeadline.append(job.workflow)
				prevJobs = getPreviousJobs(job, jobs)
				for jobId in prevJobs:
					if jobId not in jobsIncreaseDeadline:
						jobsIncreaseDeadline.append(jobId)
		
		# If the job cannot be scheduled, cost[i] == None for all i, bestSlot=-1
		scheduleJob = False
		if bestSlot<0:
			if submitSlot == 0:
				job.cancel = True
		elif endDeadlineSlot>numSlots and bestCost>0 and flagScheduleGreen:
			# If the job have to be executed in the window
			#if (scheduledNumJob<(len(jobQueue)-numJobsGreenOutWindow)) and  bestCheap:
				#print "    Schedulamos por que es el precio mas baratooooo "+str(job.id)
			scheduleJob = True
		else:
			# Otherwise
			scheduleJob = True
		
		if scheduleJob:
			jobSchedule[bestSlot].append(job)
			endJobs[job.id] = bestSlot+runSlots
			job.cost = bestCost
			for iSlot in range(0, runSlots):
				# Substract available nodes
				scheduleArray[bestSlot+iSlot] -= job.nodes
				# Substract green energy used
				reqEnergySlot = job.nodes * (Node.POWER_AVERAGE-Node.POWER_S3) * SLOTLENGTH/3600.0 # Wh
				if auxGreenAvailArray[bestSlot+iSlot] > reqEnergySlot:
					consumedGreen[bestSlot+iSlot] += reqEnergySlot
					auxGreenAvailArray[bestSlot+iSlot] -= reqEnergySlot
				else:
					consumedGreen[bestSlot+iSlot] += auxGreenAvailArray[bestSlot+iSlot]
					# Update brown
					consumedBrown[bestSlot+iSlot] += reqEnergySlot - auxGreenAvailArray[bestSlot+iSlot]
					auxGreenAvailArray[bestSlot+iSlot] = 0.0
					newPower = consumedBrown[bestSlot+iSlot]/(SLOTLENGTH/3600.0)
					if newPower > peakBrown:
						#print "%s] Peak goes from %.2f to %.2f (allocating %s)" % (toTimeString(timeElapsed), peakBrown, newPower, str(job.id))
						peakBrown = newPower
		else:
			endJobs[job.id] = numSlots
		# DEBUG
		#print str(job.id)+" -> "+str(bestSlot)+" => System nodes: "+str(scheduleArray)+"  costs="+str(jobCosts)+" green="+str(auxGreenAvailArray)
		scheduledNumJob += 1

	# Increase deadlines to jobs
	if len(jobsIncreaseDeadline)>0:
		increaseDeadlineJobs(jobsIncreaseDeadline)

	# Sort job queue according to scheduling
	jobQueue2 = []
	jobSchedule2 = {}
	notScheduled = []
	i=0
	for slotSchedule in jobSchedule:
		for job in sorted(slotSchedule):
			jobSchedule2[job.id] = i
			jobQueue2.append(job)
		i+=1
	for job in jobQueue:
		if job not in jobQueue2:
			notScheduled.append(job.id)
			#print "Job " + str(job.id) + " was not scheduled: R="+toTimeString(job.getRuntime())+" DL="+toTimeString(toSeconds(getExecTimeDeadline(job)-timeNow))

	# Output
	if DEBUG >=1:
		print "Energy usage: "+str(numNodes)+"x"+str(Node.POWER_FULL)+"W + "+str(POWER_IDLE_GSLURM)+"W"
		max = (numNodes * Node.POWER_FULL + POWER_IDLE_GSLURM) * SLOTLENGTH/3600.0 # Wh
		for i in range(MAXSIZE,0,-1):
			out=""
			for j in range(0, numSlots):
				if consumedGreen[j]>(1.0*(i-1)*max/MAXSIZE):
					out += bcolors.GREENBG+" "+bcolors.ENDC
				elif consumedGreen[j]+consumedBrown[j]>(1.0*(i-1)*max/MAXSIZE):
					out += bcolors.REDBG+" "+bcolors.ENDC
				elif surplusGreen[j]>(1.0*(i-1)*max/MAXSIZE):
					out += bcolors.WHITEBG+" "+bcolors.ENDC
				else:
					out += " "
			print out+" %.1fW" % ((1.0*i*max/MAXSIZE)*(3600.0/SLOTLENGTH))
		totalCost = 0
		totalGreen = 0
		totalBrown = 0
		for i in range(0, numSlots):
			totalGreen += consumedGreen[i]
			totalBrown += consumedBrown[i]
			totalCost += consumedBrown[i] * brownPriceArray[i]/1000.0 # Wh * $/kWh
		print "Green: "+str(totalGreen)+"Wh  Brown: "+str(totalBrown)+"Wh ($"+str(totalCost)+")  Peak: "+str(peakBrown)+"W ($"+str(peakBrown*peakCost/1000.0)+")"

	# Print job scheduling: running and queue
	if DEBUG >= 2:
		if len(jobRun)>0 or len(jobQueue)>0:
			print "Jobs ("+str(len(jobRun)+len(jobQueue))+"):"
		if len(jobRun)>0:
			print "R:",
			for job in jobRun:
				print job.id,
			print
		if len(jobQueue)>0:
			print "Q1:",
			for job in jobQueue:
				print job.id,
			print
		if len(jobQueue2)>0:
			print "Q2:",
			for job in jobQueue2:
				print job.id,
			print
		if len(notScheduled)>0:
			print "Wait:",
			for jobId in notScheduled:
				print jobId,
			print
			
		# Print running jobs
		totalCost = 0
		if len(jobRun)>0:
			for job in jobRun:
				remaining = job.getRuntime() - int(math.ceil(1.0*toSeconds(timeNow-job.start)*SPEEDUP))
				remainingSlots = int(math.ceil(1.0*remaining/SLOTLENGTH))
				deadline = toSeconds(job.submit-timeNow)*SPEEDUP + (job.getDeadline()) 
				deadlineSlot = int(math.floor(1.0*deadline/SLOTLENGTH))
				if remainingSlots<1:
					remainingSlots = 1
				out=""
				max = remainingSlots
				if deadlineSlot+1>max:
					max = deadlineSlot+1
				for i in range(0, min(numSlots, max)):
					if i==deadlineSlot:
						out+=bcolors.REDBG+"|"+bcolors.ENDC
					elif i<remainingSlots:
						if i<deadlineSlot:
							out+=bcolors.BLUEBG+" "+bcolors.ENDC
						else:
							out+=bcolors.REDBG+" "+bcolors.ENDC
					else:
						out+=" "
				for i in range(0, job.nodes):
					if i==0:
						info=" "+str(job.id)
						if DEBUG >= 3:
							#print " "+str(job.id)+":"+out+bcolors.REDBG+" "+bcolors.ENDC+"DL="+str(deadlineSlot)
							info += " N="+str(job.nodes)+" R="+str(remainingSlots)+" DL="+str(deadlineSlot)
							info += " (t R="+toTimeString(remaining)+" DL="+toTimeString(timeElapsed+(deadlineSlot*SLOTLENGTH))+")"
							info += " nodes="+str(job.nodeList)
							if job.workflow != None:
								info +=  "W="+job.workflow
							if len(job.prevJob)>0:
								info +=  " dep="+str(job.prevJob)
						print out+info
						totalCost += job.cost
					else:
						print out
		
		# Print jobs in queue
		if len(jobQueue)>0:
			for job in jobQueue:
				if job.id not in jobSchedule2:
					#print str(job.id)+" not scheduled"
					None
				else:
					#deadline = toSeconds((job.submit+timedelta(seconds=job.deadline))-timeNow)
					deadline = toSeconds(job.submit-timeNow)*SPEEDUP + (job.getDeadline()) 
					deadlineSlot = int(math.floor(1.0*deadline/SLOTLENGTH))
					runSlots = int(math.ceil(1.0*job.getRuntime()/SLOTLENGTH))
					out=""
					max = jobSchedule2[job.id]+runSlots
					if deadlineSlot+1>max:
						max = deadlineSlot+1
					for i in range(0, min(numSlots, max)):
						# Deadline
						if i==deadlineSlot:
							out += bcolors.REDBG+"|"+bcolors.ENDC
						# Queue
						elif i<jobSchedule2[job.id]:
							out += " "
						# Running
						elif i<jobSchedule2[job.id]+runSlots and job in jobSchedule[0]:
							if i<deadlineSlot:
								out+=bcolors.BLUEBG+" "+bcolors.ENDC
							else:
								out+=bcolors.REDBG+" "+bcolors.ENDC
						# Run time
						elif i<jobSchedule2[job.id]+runSlots:
							if i<deadlineSlot:
								out+=bcolors.WHITEBG+" "+bcolors.ENDC
							else:
								out+=bcolors.REDBG+" "+bcolors.ENDC
						else:
							out+=" "
					# Print bar and info
					for i in range(0, job.nodes):
						if i==0:
							info=" "+str(job.id)
							if DEBUG >= 3:
								info += " N="+str(job.nodes)+" Q="+str(jobSchedule2[job.id])+" R="+str(runSlots)+" DL="+str(deadlineSlot)
								info += " (t Q="+toTimeString(timeElapsed+(jobSchedule2[job.id]*SLOTLENGTH))
								info += " R="+toTimeString(job.getRuntime())
								info += " DL="+toTimeString(timeElapsed+(deadlineSlot*SLOTLENGTH))+")"
								if job.workflow != None:
									info += " W="+job.workflow
								if len(job.prevJob)>0:
									info +=  " dep="+str(job.prevJob)
								info += " "+str(job.cost)+"$"
							print out+info
						else:
							print out

	if DEBUG >= 1:
		# Pring node scheduling
		print "Nodes ("+str(numNodes-scheduleArray[0])+"):"
		for i in range(numNodes-1, -1, -1):
			aux = ""
			used = False
			for j in range(0, numSlots):
				if scheduleArray[j]<(numNodes-i):
					aux += bcolors.BLUEBG+" "+bcolors.ENDC
					used = True
				else:
					aux += " "
			if used or i==0:
				print aux+" "+str(i)
	
	return jobSchedule,scheduleArray,notScheduled


# Take actions
def dispatch(jobSchedule, scheduleArray):
	done = False
	# Job Scheduling
	# Changes priorities to job queue
	#if DEBUG>=3:
		#print 'Perform job scheduling:'
	#for job in getJobs().values():
		## Cancelling jobs which does not accomplish SLA
		#if job.deadline>0 and job.getExecTime()<datetime.now():
			#if job.state != 'CANCELLED' and job.state != 'COMPLETED':
				#if job.state == 'PENDING':
					#cancelJob(job.id)
					#done = True
					#if DEBUG>=1:
						#print "Cancel Job "+str(job.id)
	# Change priorities for jobs to submit
	p=200
	for job in jobSchedule[0]:
		# Start running jobs
		setJobPriority(job.id, p)
		done = True
		if DEBUG>=1:
			print "Start runnning Job "+str(job.id)+" nodes="+str(job.nodes)
		if DEBUG>=3:
			print "  "+str(job)+" "+str(job.getExecTime())+"\tPriority="+str(p)
		p=p-1
	
	#for i in range(0, len(jobSchedule)):
		#for job in jobSchedule[i]:
			#if i==0:
				## Start running jobs
				#setJobPriority(job.id, p)
				#done = True
				#if DEBUG>=1:
					#print "Start runnning Job "+str(job.id)+" nodes="+str(job.nodes)
				#if DEBUG>=3:
					#print "  "+str(job)+" "+str(job.getExecTime())+"\tPriority="+str(p)
				#p=p-1
			#else:
				## Keep jobs in the queue
				#setJobPriority(job.id, 0)

	# Turn on/off Nodes
	nodes = getNodes()
	numNodes = 0
	for nodeStatus in nodes.values():
		if nodeStatus != None:
			numNodes+=1
	reqNodes = numNodes-scheduleArray[0]
	onNodes = 0
	for nodeId in sorted(nodes.keys()):
		if nodes[nodeId] != False and nodes[nodeId] != None:
			onNodes += 1
	i=0
	if reqNodes>onNodes:
		# Turn on
		n=reqNodes-onNodes
		for nodeId in sorted(nodes.keys()):
			if i<n and nodes[nodeId]==False:
				setNodeStatus(nodeId, True)
				if DEBUG >= 1:
					print "Turn on "+nodeId
				i+=1
	elif reqNodes<onNodes:
		# Turn off
		n=onNodes-reqNodes
		for nodeId in sorted(nodes.keys()):
			if i<n and nodes[nodeId] == "IDLE":
				setNodeStatus(nodeId, False)
				if DEBUG >= 1:
					print "Turn off "+nodeId
				i+=1
	
	# Output
	if DEBUG>=3:
		print "Turning on/off nodes:"
		nodes = getNodes()
		for nodeId in sorted(nodes.keys()):
			if nodes[nodeId] == None:
				print " "+nodeId+" ??"
			elif nodes[nodeId] == False:
				print " "+nodeId+" OFF"
			else:
				print " "+nodeId+" ON"
	return done
	
if __name__ == "__main__":
	schedule()
