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

import sys
import math

from gslurmcommons import *

NAME = "Unknown"
LOG_ENERGY = "gslurm-energy.log"
LOG_JOBS = "gslurm-jobs.log"

if len(sys.argv)>1:
	NAME = sys.argv[1]

if len(sys.argv)>2:
	LOG_ENERGY = sys.argv[2]+"-energy.log"
	LOG_JOBS = sys.argv[2]+"-jobs.log"

# Energy file
prevLineSplit = None
totalEnergyGreen = 0.0
totalEnergyBrown = 0.0
totalEnergyTotal = 0.0
totalEnergyBrownCost = 0.0
powerPeak = 0.0
totalTime = 0

# Read energy file, line by line
for line in open(LOG_ENERGY, "r"):
	if not line.startswith("#") and line!="\n":
		lineSplit = line.split("\t")
		lineSplit[0] = int(lineSplit[0]) # Time
		lineSplit[1] = float(lineSplit[1]) # Green availability
		lineSplit[2] = float(lineSplit[2]) # Green prediction
		lineSplit[3] = float(lineSplit[3]) # Brown price
		lineSplit[4] = int(lineSplit[4]) # Nodes
		lineSplit[5] = float(lineSplit[5]) # Green use
		lineSplit[6] = float(lineSplit[6]) # Brown use
		lineSplit[7] = float(lineSplit[7]) # Total use
		
		if prevLineSplit != None:
			t = (lineSplit[0]-prevLineSplit[0])/3600.0
			
			if prevLineSplit[6]>powerPeak:
				powerPeak = prevLineSplit[6]
			if prevLineSplit[0]>totalTime:
				totalTime = prevLineSplit[0]
			
			energyGreen = t * prevLineSplit[5]
			energyBrown = t * prevLineSplit[6]
			energyTotal = t * prevLineSplit[7]
			energyBrownCost = (energyBrown/1000.0)*prevLineSplit[3]
			
			totalEnergyGreen += energyGreen
			totalEnergyBrown += energyBrown
			totalEnergyTotal += energyTotal
			totalEnergyBrownCost += energyBrownCost
			
		prevLineSplit = lineSplit


# Read job file, line by line
jobs = []
workflows = []
workflowsViolated = {}
workflowsStart = {}
workflowsEnd = {}
workflowsRun = {}
totalBadDeadline = 0 
totalPrepone = 0
totalPospone = 0
totalTimeViolated = 0
totalSlotViolated = 0
for line in open(LOG_JOBS, "r"):
	if not line.startswith("#") and line!="\n":
		lineSplit = line.split("\t")
		lineSplit[0] = int(lineSplit[0]) # Time
		work = int(lineSplit[2])
		start = int(lineSplit[4])
		end = int(lineSplit[5])
		run = int(lineSplit[10])
		surplus = int(lineSplit[12])
		
		jobs.append(lineSplit[1])
		if work not in workflows:
			workflows.append(work)
		# Store start
		if work not in workflowsStart:
			workflowsStart[work] = start
		if start<workflowsStart[work]:
			workflowsStart[work] = start
		# Store end
		if work not in workflowsEnd:
			workflowsEnd[work] = end
		if end>workflowsEnd[work]:
			workflowsEnd[work] = end
		# Store runtime
		if work not in workflowsRun:
			workflowsRun[work] = 0
		workflowsRun[work] += run
		# Surplus
		if surplus<0:
			totalTimeViolated += -surplus
			totalSlotViolated += int(math.ceil(-surplus/900.0))
			totalBadDeadline += 1
			if work not in workflowsViolated:
				workflowsViolated[work] = 0
			workflowsViolated[work] = -surplus
		# Pospone prepone
		totalPrepone += int(lineSplit[13])
		totalPospone += int(lineSplit[14])

totalWorkTimeViolated = 0
totalWorkSlotViolated = 0
for work in workflowsViolated.keys():
	#totalWorkTimeViolated += workflowsViolated[work]
	#totalWorkSlotViolated += int(math.ceil(workflowsViolated[work]/900.0))
	totalWorkTimeViolated += workflowsViolated[work]
	totalWorkSlotViolated += int(math.ceil(workflowsViolated[work]/900.0))

# Print summary
print "<html>"
print "<head>"
print "<title>"+str(NAME)+"</title>"
print "</head>"

print "<body>"
print "<h1>"+str(NAME)+"</h1>"
print "<img src=\""+str(NAME)+"-energy.svg\" width=\"800px\"/>"
print "<ul>"
print "  <li>Total cost: $%.2f + $%d</li>" % (totalEnergyBrownCost, int(totalWorkSlotViolated*(1.0*PENALTY*SLOTLENGTH/3600.0)))
print "  <li>Total used green energy: %.2f kWh</li>" % (totalEnergyGreen/1000.0)
print "  <li>Total brown energy used: %.2f kWh</li>" % (totalEnergyBrown/1000.0)
print "  <li>Total energy used: %.2f kWh</li>" % (totalEnergyTotal/1000.0)
print "  <li>Jobs deadline violated: %d/%d (%s %d slots)</li>" % (totalBadDeadline, len(jobs), toTimeString(totalTimeViolated), totalSlotViolated)
print "  <li>Workflows deadline violated: %d/%d (%s %d slots)</li>" % (len(workflowsViolated), len(workflows), toTimeString(totalWorkTimeViolated), totalWorkSlotViolated)
print "</ul>"

print "<h2>Logs</h2>"
print "<ul>"
print "  <li><a href=\""+str(NAME)+"-energy.log\">Energy</a></li>"
print "  <li><a href=\""+str(NAME)+"-jobs.log\">Jobs</a></li>"
print "  <li><a href=\""+str(NAME)+"-summary.log\">Summary</a></li>"
print "</ul>"

print "</body>"
print "</html>"
