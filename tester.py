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

import sys
from time import *
import math
from datetime import timedelta, datetime
from gslurmcommons import *
import getopt
sys.path.append(r'greenavailability/')
import model,setenv


setenv.init()

# aug-09-10 average		09-08-2010	110.54	178.52	212.81
# aug-23-10 best for us		23-08-2010	73.12	57.98	146.67
# sep-06-10 worst for us	06-09-2010	
# may-31-10 most energy		31-05-2010	

# jan-24-11 less energy		24-01-2011	
# mar-07-11 			07-03-2011	

format = "%d-%m-%Y"
dateWorst =   datetime(2011, 1, 24, 9, 0, 0) # Less energy OK
dateWorstUs = datetime(2010, 9, 6, 9, 0, 0) # Worst for us
#dateWorstUs = datetime(2010, 03, 07, 9, 0, 0) # For testing
dateBest =    datetime(2010, 5, 31, 9, 0, 0) # More energy
dateAverage = datetime(2010, 8, 9, 9, 0, 0) # Average TODO
sleeptime = .1


BASE_DATE = dateWorstUs
MAX_POWER = 2300
BASE_POWER = 1347
useCache = True
textOutput =  False
#actuaData = {dateWorst: "data/solarpower-24-01-2011", dateWorstUs: "data/solarpower-23-08-2010", dateBest: "data/solarpower-31-05-2010", dateBestUs: "data/solarpower-01-11-2010", dateAverage: "data/solarpower-11-10-2010"}

commonOptions="b:CTs:"

opts, args = getopt.getopt(sys.argv[1:], commonOptions)

for o,a in opts:
	if o == '-b':
		a = a.strip()
		d = datetime.strptime(a,format)
		BASE_DATE = datetime(d.year,d.month,d.day, 9)
	elif o == '-C':
		useCache = False
	elif o == '-T':
		textOutput = True
	elif o == '-s':
		sleeptime = float(a)
# Get the available green power
def readGreenAvailFile(filename):
	greenAvailability = []
	file = open(filename, 'r')
	for line in file:
		if line != '' and line.find("#")!=0 and line != '\n':
			lineSplit = line.strip().expandtabs(1).split(' ')
			t=lineSplit[0]
			p=float(lineSplit[1])
			greenAvailability.append(TimeValue(t,p))
	file.close()
	return greenAvailability


actuaData = "data/solarpower-%s"%(BASE_DATE.strftime(format))
# Get actual from file
greenAvailabilityActual = readGreenAvailFile(actuaData)

# Predictor
if useCache:
	ep = model.CachedEnergyPredictor(BASE_DATE,predictionHorizon=TOTALTIME/3600,path='./greenavailability',threshold=2, scalingFactor=MAX_POWER,scalingBase=BASE_POWER) # Threshold = 2hour; Capacity=2037W
else:
	ep = model.EnergyPredictor('./greenavailability', 2, MAX_POWER,scalingBase=BASE_POWER) # Threshold = 2hour; Capacity=2037W



# Array
greenAvailArray = []
greenAvailArrayActual = []
for i in range(0, numSlots):
	greenAvailArray.append(0)
	greenAvailArrayActual.append(0)

energyTot0=0
energyTot24=0
energyTot48=0
energyNum=0
for t in range(0, 4*24*3600/SLOTLENGTH):
	timeElapsed = t*SLOTLENGTH
	date = BASE_DATE + timedelta(seconds=timeElapsed)
	
	tini = datetime.now()
	greenAvail, flag = ep.getGreenAvailability(date, TOTALTIME/3600)
	tend = datetime.now()

	sleep(sleeptime)
	#greenAvail, flag = ep.getGreenAvailability(date, 24)
	
	# Manage data: put it in the green availability matrix
	greenAvailability = []
	print date
	for i in range(0, len(greenAvail)):
		d = date + timedelta(hours=i)
		if i>0:
			d = datetime(d.year, d.month, d.day, d.hour)
		time = toSeconds(d-date) + timeElapsed
		value = greenAvail[i]
		greenAvailability.append(TimeValue(time,value))
		#print " -> "+toTimeString(time)+" v="+str(value)
	

	# Convert into an array: prediction
	# Process input information: green and brown energy
	jG1 = jG2 = 0
	for i in range(0, numSlots):
		start = i*SLOTLENGTH + timeElapsed
		end = (i+1)*SLOTLENGTH + timeElapsed
		
		# Green: estimate average energy available
		while jG1+1 < len(greenAvailability) and (greenAvailability[jG1+1].t) <= start:
			jG1+=1
		while jG2+1 < len(greenAvailability) and (greenAvailability[jG2+1].t) <= end:
			jG2+=1
		if start>=greenAvailability[jG2].t:
			greenAvailArray[i] = greenAvailability[jG2].v
		else:
			greenV = 0.0
			for j in range(jG1, jG2+1):
				j1 = greenAvailability[j].t
				j2 = greenAvailability[j].t
				if j+1 < len(greenAvailability):
					j2 = greenAvailability[j+1].t
				if j2 > end:
					j2 = end
				if j1 > end:
					j1 = end
				if j1 < start:
					j1 = start
				greenV += (greenAvailability[j].v)*(j2-j1)
			greenAvailArray[i] = greenV/SLOTLENGTH


	# Convert into an array: actual
	jG1 = jG2 = 0
	for i in range(0, numSlots):
		start = i*SLOTLENGTH + timeElapsed
		end = (i+1)*SLOTLENGTH + timeElapsed
		
		# Green: estimate average energy available
		while jG1+1 < len(greenAvailabilityActual) and (greenAvailabilityActual[jG1+1].t) <= start:
			jG1+=1
		while jG2+1 < len(greenAvailabilityActual) and (greenAvailabilityActual[jG2+1].t) <= end:
			jG2+=1
		if start>=greenAvailabilityActual[jG2].t:
			greenAvailArrayActual[i] = greenAvailabilityActual[jG2].v
		else:
			greenV = 0.0
			for j in range(jG1, jG2+1):
				j1 = greenAvailabilityActual[j].t
				j2 = greenAvailabilityActual[j].t
				if j+1 < len(greenAvailabilityActual):
					j2 = greenAvailabilityActual[j+1].t
				if j2 > end:
					j2 = end
				if j1 > end:
					j1 = end
				if j1 < start:
					j1 = start
				greenV += (greenAvailabilityActual[j].v)*(j2-j1)
			greenAvailArrayActual[i] = greenV/SLOTLENGTH

	# Output


	print "Green energy available at "+str(date)+" after "+toTimeString(timeElapsed)+" CHANGED="+str(flag)+" ("+str(tend-tini)+")"
	if textOutput:
		for j in range(len(greenAvailArrayActual)):
			v = greenAvailArrayActual[j]-greenAvailArray[j]
			print "%f,%f,%f"%( greenAvailArrayActual[j],greenAvailArray[j],v)

	else:

		max = MAX_POWER
		for i in range(MAXSIZE,0,-1):
			out=""
			for v in greenAvailArray:
				if v > (1.0*(i-1)*max/MAXSIZE):
					out += bcolors.GREENBG+" "+bcolors.ENDC
				else:
					out += " "
			print out+" %.2fW" % (1.0*i*max/MAXSIZE)

		# Output
		print "Actual"
		for i in range(MAXSIZE,0,-1):
			out=""
			for v in greenAvailArrayActual:
				if v > (1.0*(i-1)*max/MAXSIZE):
					out += bcolors.GREENBG+" "+bcolors.ENDC
				else:
					out += " "
			print out+" %.2fW" % (1.0*i*max/MAXSIZE)
		
		
	# Output
	energy0 = greenAvailArrayActual[0]-greenAvailArray[0]
	if energy0<0:
		energy0 = -energy0
	energy24 = greenAvailArrayActual[4*24-1]-greenAvailArray[4*24-1]
	if energy24<0:
		energy24 = -energy24
	energy48 = greenAvailArrayActual[4*48-1]-greenAvailArray[4*48-1]
	if energy48<0:
		energy48 = -energy48
	energyNum += 1
	energyTot0 += energy0
	energyTot24 += energy24
	energyTot48 += energy48
	print "Difference (%.2f => %.2f %.2f %.2f):" % (greenAvailArrayActual[0]-greenAvailArray[0], energyTot0/energyNum, energyTot24/energyNum, energyTot48/energyNum)
	
	if not textOutput:

		for i in range(MAXSIZE,0,-1):
			out=""
			for j in range(0, len(greenAvailArrayActual)):
				v = greenAvailArrayActual[j]-greenAvailArray[j]
				auxColor=bcolors.REDBG
				if v<0:
					v = -v
					auxColor=bcolors.BLUEBG
				if v > (1.0*(i-1)*max/MAXSIZE):
					out += auxColor+" "+bcolors.ENDC
				else:
					out += " "
			#print out+" %.2f%%" % (100.0*(1.0*i*max/MAXSIZE)/max)
			print out+" %.2fW" % (1.0*i*max/MAXSIZE)


		# Output
		#print "Difference (%):"
		#max = 100
		#MAXSIZE=20
		#for i in range(MAXSIZE,0,-1):
			#out=""
			#for j in range(0, len(greenAvailArrayActual)):
				##v = 0
				##if greenAvailArrayActual[j] != 0:
					##v = 100.0*(greenAvailArrayActual[j]-greenAvailArray[j])/greenAvailArrayActual[j]
				##elif greenAvailArray[j]:
					##v = -100
				##if greenAvailArrayActual[j] != 0:
				#v = 100.0*(greenAvailArrayActual[j]-greenAvailArray[j])/MAX_POWER
				##elif greenAvailArray[j]:
					##v = -100
				#auxColor=bcolors.REDBG
				#if v<0:
					#v = -v
					#auxColor=bcolors.BLUEBG
				#if v > (1.0*(i-1)*max/MAXSIZE):
					#out += auxColor+" "+bcolors.ENDC
				#else:
					#out += " "
			#print out+" %.2f%%" % (100.0*(1.0*i*max/MAXSIZE)/max)

