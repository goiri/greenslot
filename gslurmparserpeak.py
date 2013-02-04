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

LOG_ENERGY = "gslurm-energy.log"
LOG_JOBS = "gslurm-jobs.log"

if len(sys.argv)>1:
	LOG_ENERGY = sys.argv[1]+"-energy.log"
	LOG_JOBS = sys.argv[1]+"-jobs.log"

# Energy file
prevLineSplit = None
totalEnergyGreen = 0.0
totalEnergyBrown = 0.0
totalEnergyTotal = 0.0
totalEnergyBrownCost = 0.0
powerPeak = 0.0
totalTime = 0

peakControlTime = []
peakControlPowe = []

ACCOUNTING_PERIOD=0.25 # hours

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
			
			peakControlTime.append(t)
			peakControlPowe.append(prevLineSplit[6])
			while sum(peakControlTime)>ACCOUNTING_PERIOD:
				peakControlTime.pop(0)
				peakControlPowe.pop(0)
			while peakControlTime[0] == 0 and len(peakControlTime)>1:
				peakControlTime.pop(0)
				peakControlPowe.pop(0)
			powerPeak = 0
			for i in range(0, len(peakControlTime)):
				powerPeak += (peakControlTime[i]/ACCOUNTING_PERIOD) * peakControlPowe[i]
			
			totalEnergyGreen += energyGreen
			totalEnergyBrown += energyBrown
			totalEnergyTotal += energyTotal
			totalEnergyBrownCost += energyBrownCost
			
			print str(t)+"\t"+str(energyBrown)+"Wh"+"\t"+str(prevLineSplit[6])+"W "+str(peakControlTime)+" "+str(peakControlPowe)+" =>" +str(powerPeak)
			
		prevLineSplit = lineSplit

# Print summary
print "Peak:  %.2f W" % (powerPeak)