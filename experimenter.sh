#!/bin/bash

# GreenSlot makes SLURM aware of solar energy availability.
# http://www.research.rutgers.edu/~goiri/
# Copyright (C) 2012 Inigo Goiri, Rutgers University
# 
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>

# http://www.panic-lab.rutgers.edu/users/muhammed/predictions.html
# aug-09-10 average
# aug-23-10 best for us
# sep-06-10 worst for us
# may-31-10 most energy

# jan-24-11 less energy
# mar-07-11 

# 2010-8-23T09:00:00
DATE_BEST="2010-8-23T09:00:00"
SOLAR_BEST="data/solarpower-23-08-2010" # Best for us
BROWN_BEST="data/browncost-onoffpeak-summer.nj"

# 2010-11-1T09:00:00
# DATE_WORSTUS="2010-11-1T09:00:00"
# WORSTUS="data/solarpower-01-11-2010" # Worst for us TODO

# 2010-5-31T09:00:00
DATE_MOST="2010-5-31T09:00:00"
SOLAR_MOST="data/solarpower-31-05-2010" # Best energy
BROWN_MOST="data/browncost-onoffpeak-summer.nj"

# 2011-1-24T09:00:00
# DATE_WORST="2011-1-24T09:00:00"
# SOLAR_WORST="data/solarpower-24-01-2011" # Worst energy
# BROWN_WORST="data/browncost-onoffpeak-winter.nj"


# 2011-3-7T09:00:00
DATE_WORST="2011-3-7T09:00:00"
SOLAR_WORST="data/solarpower-07-03-2011"
BROWN_WORST="data/browncost-onoffpeak-winter.nj"

# DATE_WORSTUS="2010-9-6T09:00:00"
# SOLAR_WORSTUS="data/solarpower-06-09-2010" # Worst for us
# BROWN_WORSTUS="data/browncost-onoffpeak-summer.nj"


# 2010-7-12T09:00:00
DATE_AVG="2010-7-12T09:00:00"
SOLAR_AVG="data/solarpower-12-07-2010"
BROWN_AVG="data/browncost-onoffpeak-summer.nj"

# 2011-8-9T09:00:00
# DATE_AVG="2010-8-9T09:00:00"
# SOLAR_AVG="data/solarpower-09-08-2010"
# BROWN_AVG="data/browncost-onoffpeak-summer.nj"

DATE_NONE="-"
SOLAR_NONE="data/greenpower.none"

PEAK_WINTER=5.5884 # Winter October-May
PEAK_SUMMER=13.6136 # Summer June-Sep




# Brown energy
BROWN_VARIABLE_WINTER="data/browncost-onoffpeak-winter.nj"
BROWN_VARIABLE_SUMMER="data/browncost-onoffpeak-summer.nj"
BROWN_FIXED="data/browncost.nj"

# Workloads
WORKLOAD="workload/workload.genome"
WORKLOAD_SHORT="workload/workload-short.genome"
WORKLOAD_SPREAD="workload/workload-spread.genome"
WORKLOAD_BLOCK="workload/workload-parallel.genome"

WORKLOAD_SPREAD_0="workload/workload-spread-inaccurate+0.genome"
WORKLOAD_SPREAD_10="workload/workload-spread-inaccurate+10.genome"
WORKLOAD_SPREAD_m10="workload/workload-spread-inaccurate-10.genome"

WORKLOAD_15="workload/workload-inaccurate+15.genome"
WORKLOAD_m15="workload/workload-inaccurate-15.genome"
WORKLOAD_0="workload/workload-inaccurate+0.genome"
WORKLOAD_10="workload/workload-inaccurate+10.genome"
WORKLOAD_m10="workload/workload-inaccurate-10.genome"
WORKLOAD_20="workload/workload-inaccurate+20.genome"
WORKLOAD_m20="workload/workload-inaccurate-20.genome"

# Extra load
WORKLOADm1="workload/workload+1.genome"
WORKLOADm2="workload/workload+2.genome"
WORKLOADm3="workload/workload+3.genome"
WORKLOADm4="workload/workload+4.genome"
WORKLOADm5="workload/workload+5.genome"
WORKLOADm6="workload/workload+6.genome"
WORKLOADm7="workload/workload+7.genome"
WORKLOADm8="workload/workload+8.genome"
WORKLOADm9="workload/workload+9.genome"
WORKLOADm10="workload/workload+10.genome"
WORKLOADm11="workload/workload+11.genome"
WORKLOADm12="workload/workload+12.genome"
WORKLOADm13="workload/workload+13.genome"
WORKLOADm14="workload/workload+14.genome"


function experiment {
	NAME=$1
	shift
	WEEK=$1
	shift
	FLAGS=$*

	echo "name="$NAME" week="$WEEK" flags="$FLAGS

	# Start
	./gslurmcleaner.py
	rm /tmp/gslurm
	rm -f logs/gslurm-jobs.log
	rm -f logs/gslurm-energy.log
	rm -f logs/gslurm-scheduler.log
	sleep 1
	./gslurmd $FLAGS

	# Save results
	mkdir -p logs/$NAME
	echo $NAME > logs/$NAME/$NAME-summary.log
	./gslurmparser.py logs/gslurm >> logs/$NAME/$NAME-summary.log
	./gslurmparserhtml.py $NAME logs/gslurm > logs/$NAME/$NAME.html

	mv logs/gslurm-jobs.log logs/$NAME/$NAME-jobs.log
	mv logs/gslurm-energy.log logs/$NAME/$NAME-energy.log
	mv logs/gslurm-scheduler.log logs/$NAME/$NAME-scheduler.log

	# Plot results
# 	echo "set term svg size 1280,600" > logs/$NAME/$NAME.plot
	echo "set term svg size 960,450" > logs/$NAME/$NAME.plot
	echo "set out \"logs/$NAME/$NAME-energy.svg\"" >> logs/$NAME/$NAME.plot
	echo "set ylabel \"Power (kW)\"" >> logs/$NAME/$NAME.plot
	echo "set yrange [0:1.8]" >> logs/$NAME/$NAME.plot

	echo "set y2label \"Brown energy price ($/kWh)\"" >> logs/$NAME/$NAME.plot
	echo "set y2range [0:0.3]" >> logs/$NAME/$NAME.plot
	echo "set y2tics" >> logs/$NAME/$NAME.plot
	echo "set ytics nomirror" >> logs/$NAME/$NAME.plot

	echo "set xdata time" >> logs/$NAME/$NAME.plot
	echo "set timefmt \"%s\"" >> logs/$NAME/$NAME.plot
	echo "set format x \"%a\n%R\"" >> logs/$NAME/$NAME.plot

	echo "set style fill solid" >> logs/$NAME/$NAME.plot
	echo "plot \"logs/$NAME/$NAME-energy.log\" using (\$1+(2*24*3600+9*3600)):(\$8/1000) lc rgb \"#808080\" w filledcurve title \"Brown consumed\",\\" >> logs/$NAME/$NAME.plot
	echo "\"logs/$NAME/$NAME-energy.log\" using (\$1+(2*24*3600+9*3600)):(\$6/1000) lc rgb \"#e6e6e6\" w filledcurve title \"Green consumed\",\\" >> logs/$NAME/$NAME.plot
# 	echo "plot \"logs/$NAME/$NAME-energy.log\" using (\$1+(2*24*3600+9*3600)):(\$8/1000) lc rgb \"brown\" w filledcurve title \"Brown consumed\",\\" >> logs/$NAME/$NAME.plot
# 	echo "\"logs/$NAME/$NAME-energy.log\" using (\$1+(2*24*3600+9*3600)):(\$6/1000) lc rgb \"green\" w filledcurve title \"Green consumed\",\\" >> logs/$NAME/$NAME.plot
	echo "\"logs/$NAME/$NAME-energy.log\" using (\$1+(2*24*3600+10*3600)):(\$3/1000) lw 2 lc rgb \"black\" w steps title \"Green predicted\",\\" >> logs/$NAME/$NAME.plot
# 	echo "\"$WEEK-plot\" using (\$1+(2*24*3600)):(\$2/1000) w steps lw 3 lc rgb \"#008000\" title \"Green availability\",\\" >> logs/$NAME/$NAME.plot
	#echo "\"$WEEK-plot\" using (\$1+(2*24*3600)):(\$2/1000) w steps lw 3 lc rgb \"black\" title \"Green availability\",\\" >> logs/$NAME/$NAME.plot
# 	echo "\"logs/$NAME/$NAME-energy.log\" using (\$1+(2*24*3600+9*3600)):4 axes x1y2 lw 2 lc rgb \"#3b0000\" w steps title \"Brown price\"" >> logs/$NAME/$NAME.plot
	echo "\"logs/$NAME/$NAME-energy.log\" using (\$1+(2*24*3600+9*3600)):4 axes x1y2 lw 2 lc rgb \"black\" w steps title \"Brown price\"" >> logs/$NAME/$NAME.plot

	gnuplot logs/$NAME/$NAME.plot
}

# experiment "22-bf-var-pred-avg-utilization+9" $SOLAR_AVG -d $DATE_AVG -b $BROWN_AVG --workload $WORKLOADm9

cp gslurm-outwindoweverything.py gslurm.py
experiment "22-outwindoweverythingnoworkflow-var-pred-avg-utilization+1" $SOLAR_AVG -d $DATE_AVG -b $BROWN_AVG --workload $WORKLOADm1 --green --brown --pred 2 --reverse
experiment "22-outwindoweverythingnoworkflow-var-pred-avg-utilization+2" $SOLAR_AVG -d $DATE_AVG -b $BROWN_AVG --workload $WORKLOADm2 --green --brown --pred 2 --reverse
experiment "22-outwindoweverythingnoworkflow-var-pred-avg-utilization+3" $SOLAR_AVG -d $DATE_AVG -b $BROWN_AVG --workload $WORKLOADm3 --green --brown --pred 2 --reverse
experiment "22-outwindoweverythingnoworkflow-var-pred-avg-utilization+4" $SOLAR_AVG -d $DATE_AVG -b $BROWN_AVG --workload $WORKLOADm4 --green --brown --pred 2 --reverse
experiment "22-outwindoweverythingnoworkflow-var-pred-avg-utilization+5" $SOLAR_AVG -d $DATE_AVG -b $BROWN_AVG --workload $WORKLOADm5 --green --brown --pred 2 --reverse
experiment "22-outwindoweverythingnoworkflow-var-pred-avg-utilization+6" $SOLAR_AVG -d $DATE_AVG -b $BROWN_AVG --workload $WORKLOADm6 --green --brown --pred 2 --reverse
experiment "22-outwindoweverythingnoworkflow-var-pred-avg-utilization+7" $SOLAR_AVG -d $DATE_AVG -b $BROWN_AVG --workload $WORKLOADm7 --green --brown --pred 2 --reverse
experiment "22-outwindoweverythingnoworkflow-var-pred-avg-utilization+8" $SOLAR_AVG -d $DATE_AVG -b $BROWN_AVG --workload $WORKLOADm8 --green --brown --pred 2 --reverse
experiment "22-outwindoweverythingnoworkflow-var-pred-avg-utilization+9" $SOLAR_AVG -d $DATE_AVG -b $BROWN_AVG --workload $WORKLOADm9 --green --brown --pred 2 --reverse
experiment "22-outwindoweverythingnoworkflow-var-pred-avg-utilization+10" $SOLAR_AVG -d $DATE_AVG -b $BROWN_AVG --workload $WORKLOADm10 --green --brown --pred 2 --reverse

exit 1

experiment "22-bf-var-pred-avg-utilization+1" $SOLAR_AVG -d $DATE_AVG -b $BROWN_AVG --workload $WORKLOADm1
experiment "22-bf-var-pred-avg-utilization+2" $SOLAR_AVG -d $DATE_AVG -b $BROWN_AVG --workload $WORKLOADm2
experiment "22-bf-var-pred-avg-utilization+3" $SOLAR_AVG -d $DATE_AVG -b $BROWN_AVG --workload $WORKLOADm3
experiment "22-bf-var-pred-avg-utilization+4" $SOLAR_AVG -d $DATE_AVG -b $BROWN_AVG --workload $WORKLOADm4
experiment "22-bf-var-pred-avg-utilization+5" $SOLAR_AVG -d $DATE_AVG -b $BROWN_AVG --workload $WORKLOADm5
experiment "22-bf-var-pred-avg-utilization+6" $SOLAR_AVG -d $DATE_AVG -b $BROWN_AVG --workload $WORKLOADm6
experiment "22-bf-var-pred-avg-utilization+7" $SOLAR_AVG -d $DATE_AVG -b $BROWN_AVG --workload $WORKLOADm7
experiment "22-bf-var-pred-avg-utilization+8" $SOLAR_AVG -d $DATE_AVG -b $BROWN_AVG --workload $WORKLOADm8
experiment "22-bf-var-pred-avg-utilization+9" $SOLAR_AVG -d $DATE_AVG -b $BROWN_AVG --workload $WORKLOADm9
experiment "22-bf-var-pred-avg-utilization+10" $SOLAR_AVG -d $DATE_AVG -b $BROWN_AVG --workload $WORKLOADm10


# experiment "00-greenvarprices-var-noenergy-avg" $SOLAR_NONE -d $DATE_NONE -b $BROWN_AVG --workload $WORKLOAD --brown --reverse
# experiment "00-bf-var-noenergy-avg" $SOLAR_NONE -d $DATE_NONE -b $BROWN_AVG --workload $WORKLOAD

# experiment "20-bf-var-pred-avg-inaccurate-10" $SOLAR_AVG -d $DATE_AVG -b $BROWN_AVG --workload $WORKLOAD_m10
# experiment "21-greenslot-var-pred-avg-inaccurate-10" $SOLAR_AVG -d $DATE_AVG -b $BROWN_AVG --workload $WORKLOAD_m10 --green --brown --pred 2 --reverse
# experiment "20-bf-var-pred-avg-inaccurate-20" $SOLAR_AVG -d $DATE_AVG -b $BROWN_AVG --workload $WORKLOAD_m20
# experiment "21-greenslot-var-pred-avg-inaccurate-20" $SOLAR_AVG -d $DATE_AVG -b $BROWN_AVG --workload $WORKLOAD_m20 --green --brown --pred 2 --reverse





# Extra load
# experiment "22-greenslot-var-pred-avg-utilization+1" $SOLAR_AVG -d $DATE_AVG -b $BROWN_AVG --workload $WORKLOADm1 --green --brown --pred 2 --reverse
# experiment "22-greenslot-var-pred-avg-utilization+3" $SOLAR_AVG -d $DATE_AVG -b $BROWN_AVG --workload $WORKLOADm3 --green --brown --pred 2 --reverse
# experiment "22-greenslot-var-pred-avg-utilization+2" $SOLAR_AVG -d $DATE_AVG -b $BROWN_AVG --workload $WORKLOADm2 --green --brown --pred 2 --reverse
# experiment "22-greenslot-var-pred-avg-utilization+4" $SOLAR_AVG -d $DATE_AVG -b $BROWN_AVG --workload $WORKLOADm4 --green --brown --pred 2 --reverse
# experiment "22-greenslot-var-pred-avg-utilization+5" $SOLAR_AVG -d $DATE_AVG -b $BROWN_AVG --workload $WORKLOADm5 --green --brown --pred 2 --reverse


# experiment "22-greenslot-var-pred-avg-utilization+5" $SOLAR_AVG -d $DATE_AVG -b $BROWN_AVG --workload $WORKLOADm5 --green --brown --pred 2 --reverse
# experiment "22-bf-var-pred-avg-utilization+5" $SOLAR_AVG -d $DATE_AVG -b $BROWN_AVG --workload $WORKLOADm5

# experiment "22-bf-var-pred-avg-utilization+8" $SOLAR_AVG -d $DATE_AVG -b $BROWN_AVG --workload $WORKLOADm8
# experiment "22-greenslot-var-pred-avg-utilization+7" $SOLAR_AVG -d $DATE_AVG -b $BROWN_AVG --workload $WORKLOADm7 --green --brown --pred 2 --reverse
# experiment "22-bf-var-pred-avg-utilization+7" $SOLAR_AVG -d $DATE_AVG -b $BROWN_AVG --workload $WORKLOADm7

# experiment "22-bf-var-pred-avg-utilization+4" $SOLAR_AVG -d $DATE_AVG -b $BROWN_AVG --workload $WORKLOADm4

# experiment "22-greenslot-var-pred-avg-utilization+5" $SOLAR_AVG -d $DATE_AVG -b $BROWN_AVG --workload $WORKLOADm5 --green --brown --pred 2 --reverse
# experiment "22-bf-var-pred-avg-utilization+5" $SOLAR_AVG -d $DATE_AVG -b $BROWN_AVG --workload $WORKLOADm5

# experiment "22-bf-var-pred-avg-utilization+9" $SOLAR_AVG -d $DATE_AVG -b $BROWN_AVG --workload $WORKLOADm9
# experiment "22-greenslot-var-pred-avg-utilization+9" $SOLAR_AVG -d $DATE_AVG -b $BROWN_AVG --workload $WORKLOADm9 --green --brown --pred 2 --reverse
# 
# experiment "22-bf-var-pred-avg-utilization+10" $SOLAR_AVG -d $DATE_AVG -b $BROWN_AVG --workload $WORKLOADm10
# experiment "22-greenslot-var-pred-avg-utilization+10" $SOLAR_AVG -d $DATE_AVG -b $BROWN_AVG --workload $WORKLOADm10 --green --brown --pred 2 --reverse
# 
# experiment "22-bf-var-pred-avg-utilization+12" $SOLAR_AVG -d $DATE_AVG -b $BROWN_AVG --workload $WORKLOADm12
# experiment "22-greenslot-var-pred-avg-utilization+12" $SOLAR_AVG -d $DATE_AVG -b $BROWN_AVG --workload $WORKLOADm12 --green --brown --pred 2 --reverse
# 
# experiment "22-bf-var-pred-avg-utilization+14" $SOLAR_AVG -d $DATE_AVG -b $BROWN_AVG --workload $WORKLOADm14
# experiment "22-greenslot-var-pred-avg-utilization+14" $SOLAR_AVG -d $DATE_AVG -b $BROWN_AVG --workload $WORKLOADm14 --green --brown --pred 2 --reverse











# experiment "20-bf-var-pred-avg-inaccurate-10" $SOLAR_AVG -d $DATE_AVG -b $BROWN_AVG --workload $WORKLOAD_m10
# experiment "20-bf-var-pred-avg-inaccurate-20" $SOLAR_AVG -d $DATE_AVG -b $BROWN_AVG --workload $WORKLOAD_m20
# experiment "21-greenslot-var-pred-avg-inaccurate-20" $SOLAR_AVG -d $DATE_AVG -b $BROWN_AVG --workload $WORKLOAD_m20 --green --brown --pred 2 --reverse
# experiment "21-greenslot-var-pred-avg-inaccurate-10" $SOLAR_AVG -d $DATE_AVG -b $BROWN_AVG --workload $WORKLOAD_m10 --green --brown --pred 2 --reverse



# cp gslurm-outwindow.py gslurm.py




# # Backfilling, on/off prices, no peak power charges, exact runtimes, 4 weeks, regular workload
# # 1 
# experiment "01-bf-var-actual-most" $SOLAR_MOST -d $DATE_MOST -b $BROWN_MOST --workload $WORKLOAD
# # 2 
# experiment "02-bf-var-actual-best" $SOLAR_BEST -d $DATE_BEST -b $BROWN_BEST --workload $WORKLOAD
# # 3 
# experiment "03-bf-var-actual-worst" $SOLAR_WORST -d $DATE_WORST -b $BROWN_WORST --workload $WORKLOAD
# # 4 
# experiment "04-bf-var-actual-avg" $SOLAR_AVG -d $DATE_AVG -b $BROWN_AVG --workload $WORKLOAD


# # GreenOnly, on/off prices, no peak power charges, exact runtimes, 4 weeks, solar predictions, regular workload
# # 5
# experiment "05-greenonly-var-pred-most" $SOLAR_MOST -d $DATE_MOST -b $BROWN_MOST --workload $WORKLOAD --green --pred 2 --reverse
# # 6
# experiment "06-greenonly-var-pred-best" $SOLAR_BEST -d $DATE_BEST -b $BROWN_BEST --workload $WORKLOAD --green --pred 2 --reverse
# # 7
# experiment "07-greenonly-var-pred-worst" $SOLAR_WORST -d $DATE_WORST -b $BROWN_WORST --workload $WORKLOAD --green --pred 2 --reverse
# # 8
# experiment "08-greenonly-var-pred-avg" $SOLAR_AVG -d $DATE_AVG -b $BROWN_AVG --workload $WORKLOAD --green --pred 2 --reverse


# GreenOnly, on/off prices, no peak power charges, exact runtimes, 4 weeks, solar predictions, regular workload
# 9 
# experiment "09-greenonly-var-actual-most" $SOLAR_MOST -d $DATE_MOST -b $BROWN_MOST --workload $WORKLOAD --green --reverse
# 10 
# experiment "10-greenonly-var-actual-best" $SOLAR_BEST -d $DATE_BEST -b $BROWN_BEST --workload $WORKLOAD --green --reverse
# 11 
# experiment "11-greenonly-var-actual-worst" $SOLAR_WORST -d $DATE_WORST -b $BROWN_WORST --workload $WORKLOAD --green --reverse
# 12
# experiment "12-greenonly-var-actual-avg" $SOLAR_AVG -d $DATE_AVG -b $BROWN_AVG --workload $WORKLOAD --green --reverse


# # GreenVarPrices, on/off prices, no peak power charges, exact runtimes, most solar, solar predictions, regular workload
# # 13
# experiment "13-greenvarprices-var-pred-most" $SOLAR_MOST -d $DATE_MOST -b $BROWN_MOST --workload $WORKLOAD --green --brown --pred 2 --reverse
# # GreenVarPrices, on/off prices, no peak power charges, exact runtimes, average solar, solar predictions, regular workload
# # 14
# experiment "14-greenvarprices-var-pred-avg" $SOLAR_AVG -d $DATE_AVG -b $BROWN_AVG --workload $WORKLOAD --green --brown --pred 2 --reverse
# experiment "14-greenvarprices-var-pred-best" $SOLAR_BEST -d $DATE_BEST -b $BROWN_BEST --workload $WORKLOAD --green --brown --pred 2 --reverse
# experiment "14-greenvarprices-var-pred-worst" $SOLAR_WORST -d $DATE_WORST -b $BROWN_WORST --workload $WORKLOAD --green --brown --pred 2 --reverse 


# # Impact of workload
# # Backfilling, on/off prices, no peak power charges, exact runtimes, average solar, parallel workload
# # 15
# experiment "15-bf-var-actual-avg-parallel" $SOLAR_AVG -d $DATE_AVG -b $BROWN_AVG --workload $WORKLOAD_BLOCK

# # GreenVarPrices, on/off prices, no peak power charges, exact runtimes, average solar, parallel workload
# # 16
# experiment "16-greenvarprices-var-pred-avg-parallel" $SOLAR_AVG -d $DATE_AVG -b $BROWN_AVG --workload $WORKLOAD_BLOCK --green --brown --pred 2 --reverse

# # Backfilling, on/off prices, no peak power charges, exact runtimes, average solar, staggered workload
# # 17 
# experiment "17-bf-var-actual-avg-staggered" $SOLAR_AVG -d $DATE_AVG -b $BROWN_AVG --workload $WORKLOAD_SPREAD

# # GreenVarPrices, on/off prices, no peak power charges, exact runtimes, average solar, staggered workload
# # 18
# experiment "18-greenvarprices-var-pred-avg-staggered" $SOLAR_AVG -d $DATE_AVG -b $BROWN_AVG --workload $WORKLOAD_SPREAD --green --brown --pred 2 --reverse

# Scheduling for solar energy, brown energy prices, and peak brown power charges
# GreenSlot, on/off prices, no peak power charges, exact runtimes, average solar, staggered workload
# 19
# experiment "19-greenslot-var-pred-avg-staggered" $SOLAR_AVG -d $DATE_AVG -b $BROWN_AVG --workload $WORKLOAD_SPREAD --green --brown --pred 2 --reverse




# # Impact of runtime mispredictions
# # 20 
# Backfilling, on/off prices, peak power charges, exact runtimes, average solar, staggered workload, inaccurate
# experiment "20-bf-var-actual-avg-inaccurate" $SOLAR_AVG -d $DATE_AVG -b $BROWN_AVG --workload $WORKLOAD_0
# experiment "20-bf-var-pred-avg-inaccurate+10" $SOLAR_AVG -d $DATE_AVG -b $BROWN_AVG --workload $WORKLOAD_10
# experiment "20-bf-var-pred-avg-inaccurate-10" $SOLAR_AVG -d $DATE_AVG -b $BROWN_AVG --workload $WORKLOAD_m10
# experiment "20-bf-var-pred-avg-inaccurate-20" $SOLAR_AVG -d $DATE_AVG -b $BROWN_AVG --workload $WORKLOAD_m20
# experiment "20-bf-var-pred-avg-inaccurate+20" $SOLAR_AVG -d $DATE_AVG -b $BROWN_AVG --workload $WORKLOAD_20
# experiment "20-bf-var-pred-avg-inaccurate-10" $SOLAR_AVG -d $DATE_AVG -b $BROWN_AVG --workload $WORKLOAD_m10




# # 21
# # GreenSlot, on/off prices, peak power charges, exact runtimes, average solar, staggered workload, inaccurate
# experiment "21-greenslot-var-pred-avg-inaccurate" $SOLAR_AVG -d $DATE_AVG -b $BROWN_AVG --workload $WORKLOAD_0 --green --brown --pred 2 --reverse

# experiment "21-greenslot-var-pred-avg-inaccurate" $SOLAR_AVG -d $DATE_AVG -b $BROWN_AVG --workload $WORKLOAD_0 --green --brown --pred 2 --reverse
# experiment "21-greenslot-var-pred-avg-inaccurate+10" $SOLAR_AVG -d $DATE_AVG -b $BROWN_AVG --workload $WORKLOAD_10 --green --brown --pred 2 --reverse
# experiment "21-greenslot-var-pred-avg-inaccurate-20" $SOLAR_AVG -d $DATE_AVG -b $BROWN_AVG --workload $WORKLOAD_m20 --green --brown --pred 2 --reverse
# experiment "21-greenslot-var-pred-avg-inaccurate-10" $SOLAR_AVG -d $DATE_AVG -b $BROWN_AVG --workload $WORKLOAD_m10 --green --brown --pred 2 --reverse
# experiment "21-greenslot-var-pred-avg-inaccurate+20" $SOLAR_AVG -d $DATE_AVG -b $BROWN_AVG --workload $WORKLOAD_20 --green --brown --pred 2 --reverse
# experiment "21-greenslot-var-pred-avg-inaccurate-10" $SOLAR_AVG -d $DATE_AVG -b $BROWN_AVG --workload $WORKLOAD_m10 --green --brown --pred 2 --reverse



# Test peak power
# experiment "19-greenslot-var-peak-actual-avg-staggered" $SOLAR_AVG -d $DATE_AVG -b $BROWN_AVG --workload $WORKLOAD_SPREAD --green --brown --peak $PEAK_SUMMER
# experiment "19-greenslotnoreverse-var-peak-actual-avg-staggered" $SOLAR_AVG -d $DATE_AVG -b $BROWN_AVG --workload $WORKLOAD_SPREAD --green --brown --peak $PEAK_SUMMER
# experiment "19-greenslotnoreverse-var-peak-pred0-avg-staggered" $SOLAR_AVG -d $DATE_AVG -b $BROWN_AVG --workload $WORKLOAD_SPREAD --green --brown --peak $PEAK_SUMMER --pred 0
# experiment "19-greenslotnoreverse-var-peak-pred1-avg-staggered" $SOLAR_AVG -d $DATE_AVG -b $BROWN_AVG --workload $WORKLOAD_SPREAD --green --brown --peak $PEAK_SUMMER --pred 1
# experiment "19-greenslotnoreverse-var-peak-pred2-avg-staggered" $SOLAR_AVG -d $DATE_AVG -b $BROWN_AVG --workload $WORKLOAD_SPREAD --green --brown --peak $PEAK_SUMMER --pred 2
# experiment "19-greenslot-var-peak-pred0-avg-staggered" $SOLAR_AVG -d $DATE_AVG -b $BROWN_AVG --workload $WORKLOAD_SPREAD --green --brown --peak $PEAK_SUMMER --pred 0 --reverse
# experiment "19-greenslot-var-peak-pred1-avg-staggered" $SOLAR_AVG -d $DATE_AVG -b $BROWN_AVG --workload $WORKLOAD_SPREAD --green --brown --peak $PEAK_SUMMER --pred 1 --reverse
# experiment "19-greenslot-var-peak-pred2-avg-staggered" $SOLAR_AVG -d $DATE_AVG -b $BROWN_AVG --workload $WORKLOAD_SPREAD --green --brown --peak $PEAK_SUMMER --pred 2 --reverse







# experiment "usreverse-var-pred1-avg" $SOLAR_AVG -d $DATE_AVG -b $BROWN_AVG --workload $WORKLOAD --green --brown --pred 1 --reverse
# experiment "us-var-pred1-avg" $SOLAR_AVG -d $DATE_AVG -b $BROWN_AVG --workload $WORKLOAD --green --brown --pred 1
# 
# experiment "us-var-pred2-avg" $SOLAR_AVG -d $DATE_AVG -b $BROWN_AVG --workload $WORKLOAD --green --brown --pred 2
# experiment "usreverse-var-pred2-avg" $SOLAR_AVG -d $DATE_AVG -b $BROWN_AVG --workload $WORKLOAD --green --brown --pred 2 --reverse
# 
# experiment "us-var-pred0-avg" $SOLAR_AVG -d $DATE_AVG -b $BROWN_AVG --workload $WORKLOAD --green --brown --pred 0
# experiment "usreverse-var-pred0-avg" $SOLAR_AVG -d $DATE_AVG -b $BROWN_AVG --workload $WORKLOAD --green --brown --pred 0 --reverse






# experiment "us-var-pred-best" $SOLAR_BEST -d $DATE_BEST -b $BROWN_BEST --workload $WORKLOAD --green --brown --pred

# experiment "bf-var-actual-datetest2" $SOLAR_TEST2 -d $DATE_TEST2 -b $BROWN_TEST2 --workload $WORKLOAD
# experiment "us-var-pred-datetest2" $SOLAR_TEST2 -d $DATE_TEST2 -b $BROWN_TEST2 --workload $WORKLOAD --green --brown --pred
# experiment "us-var-actual-datetest2" $SOLAR_TEST2 -d $DATE_TEST2 -b $BROWN_TEST2 --workload $WORKLOAD --green --brown

# experiment "bf-var-actual-best" $SOLAR_BEST -d $DATE_BEST -b $BROWN_BEST --workload $WORKLOAD
# experiment "bf-var-actual-worstus" $SOLAR_WORSTUS -d $DATE_WORSTUS -b $BROWN_WORSTUS --workload $WORKLOAD
# experiment "bf-var-actual-bestus" $SOLAR_BESTUS -d $DATE_BESTUS -b $BROWN_BESTUS --workload $WORKLOAD
# experiment "bf-var-actual-avg" $SOLAR_AVG -d $DATE_AVG -b $BROWN_AVG --workload $WORKLOAD
# 
# experiment "us-var-actual-best" $SOLAR_BEST -d $DATE_BEST -b $BROWN_BEST --workload $WORKLOAD --green --brown
# experiment "us-var-actual-worstus" $SOLAR_WORSTUS -d $DATE_WORSTUS -b $BROWN_WORSTUS --workload $WORKLOAD --green --brown
# experiment "us-var-actual-bestus" $SOLAR_BESTUS -d $DATE_BESTUS -b $BROWN_BESTUS --workload $WORKLOAD --green --brown
# experiment "us-var-actual-avg" $SOLAR_AVG -d $DATE_AVG -b $BROWN_AVG --workload $WORKLOAD --green --brown
# 
# experiment "us-var-pred-best" $SOLAR_BEST -d $DATE_BEST -b $BROWN_BEST --workload $WORKLOAD --green --brown --pred
# experiment "us-var-pred-worstus" $SOLAR_WORSTUS -d $DATE_WORSTUS -b $BROWN_WORSTUS --workload $WORKLOAD --green --brown --pred
# experiment "us-var-pred-bestus" $SOLAR_BESTUS -d $DATE_BESTUS -b $BROWN_BESTUS --workload $WORKLOAD --green --brown --pred
# experiment "us-var-pred-avg" $SOLAR_AVG -d $DATE_AVG -b $BROWN_AVG --workload $WORKLOAD --green --brown --pred

# experiment "usnobrown-var-actual-best" $SOLAR_BEST -d $DATE_BEST -b $BROWN_BEST --workload $WORKLOAD --green
# experiment "usnobrown-var-actual-worstus" $SOLAR_WORSTUS -d $DATE_WORSTUS -b $BROWN_WORSTUS --workload $WORKLOAD --green
# experiment "usnobrown-var-actual-bestus" $SOLAR_BESTUS -d $DATE_BESTUS -b $BROWN_BESTUS --workload $WORKLOAD --green
# experiment "usnobrown-var-actual-avg" $SOLAR_AVG -d $DATE_AVG -b $BROWN_AVG --workload $WORKLOAD --green
# experiment "usnobrown-var-actual-datetest" $SOLAR_TEST -d $DATE_TEST -b $BROWN_TEST --workload $WORKLOAD --green
# experiment "usnobrown-var-actual-datetest2" $SOLAR_TEST2 -d $DATE_TEST2 -b $BROWN_TEST2 --workload $WORKLOAD --green






# for i in `seq 1 10`; do
# # 	experiment "validation-accelerated-20-$i" $BEST -b $BROWN_VARIABLE_SUMMER --workload $WORKLOAD -g $BEST --green --brown
# 	#experiment "validation-accelerated-peak-opt-workloadshort-$i" $BEST -d $DATE_BEST -b $BROWN_VARIABLE_SUMMER --workload $WORKLOAD_SHORT --green --brown --peak $PEAK_SUMMER
# 	experiment "validation-accelerated-opt-workloadshort-$i" $BEST -d $DATE_BEST -b $BROWN_VARIABLE_SUMMER --workload $WORKLOAD_SHORT --green --brown
# done

# experiment "validation" $BEST -b $BROWN_VARIABLE_SUMMER --workload $WORKLOAD -g $BEST --green --brown
# experiment "validation-simulated" $BEST -b $BROWN_VARIABLE_SUMMER --workload $WORKLOAD -g $BEST --green --brown

# Peak
#experiment "bf-fixpeak-actual-best-spread" $BEST -b $BROWN_FIXED --workload $WORKLOAD_SPREAD -g $BEST --peak $PEAK_SUMMER
#experiment "us-fixpeak-actual-best-spread" $BEST -b $BROWN_FIXED --workload $WORKLOAD_SPREAD -g $BEST --green --peak $PEAK_SUMMER


#experiment "us-fix-actual-avg" $AVG -b $BROWN_FIXED --workload $WORKLOAD -g $AVG --green

#experiment "us-fix-actual-best-blocks" $BEST -b $BROWN_FIXED --workload $WORKLOAD_BLOCK -g $BEST --green


# Inaccuracy
# experiment "us+20-fix-actual-best" $BEST -b $BROWN_FIXED --workload $WORKLOAD -g $BEST --green
# experiment "us+20-fix-actual-best-inacc+0" $BEST -b $BROWN_FIXED --workload $WORKLOAD_0 -g $BEST --green
#experiment "us+20-fix-actual-best-inacc-15" $BEST -b $BROWN_FIXED --workload $WORKLOAD_m15 -g $BEST --green
# experiment "us+20-fix-actual-best-inacc+15" $BEST -b $BROWN_FIXED --workload $WORKLOAD_15 -g $BEST --green

# experiment "bf-fix-actual-best-inacc+0" $BEST -b $BROWN_FIXED --workload $WORKLOAD_0 -g $BEST
# experiment "us-fix-actual-best-inacc+0" $BEST -b $BROWN_FIXED --workload $WORKLOAD_0 -g $BEST --green

# experiment "bf-fix-actual-best-inacc-15" $BEST -b $BROWN_FIXED --workload $WORKLOAD_m15 -g $BEST
# experiment "bf-fix-actual-best-inacc+15" $BEST -b $BROWN_FIXED --workload $WORKLOAD_15 -g $BEST

# experiment "us-fix-actual-best-inacc-15" $BEST -b $BROWN_FIXED --workload $WORKLOAD_m15 -g $BEST --green
# experiment "us-fix-actual-best-inacc+15" $BEST -b $BROWN_FIXED --workload $WORKLOAD_15 -g $BEST --green

# Season: variable price
# experiment "bf-summer-actual-best" $BEST -b $BROWN_VARIABLE_SUMMER --workload $WORKLOAD -g $BEST
# experiment "usnobrown-summer-actual-best" $BEST -b $BROWN_VARIABLE_SUMMER --workload $WORKLOAD -g $BEST --green
# experiment "us-summer-actual-best" $BEST -b $BROWN_VARIABLE_SUMMER --workload $WORKLOAD -g $BEST --green --brown

# experiment "bf-winter-actual-worstus" $WORSTUS -b $BROWN_VARIABLE_WINTER --workload $WORKLOAD -g $WORSTUS
# experiment "us-winter-actual-worstus" $WORSTUS -b $BROWN_VARIABLE_WINTER --workload $WORKLOAD -g $WORSTUS --green --brown

# experiment "bf-summer-actual-bestus" $BESTUS -b $BROWN_VARIABLE_SUMMER --workload $WORKLOAD -g $BESTUS
# experiment "us-summer-actual-bestus" $BESTUS -b $BROWN_VARIABLE_SUMMER --workload $WORKLOAD -g $BESTUS --green --brown


# experiment "bf-winter-actual-nosolar" $NONE_SOLAR -b $BROWN_VARIABLE_WINTER --workload $WORKLOAD -g $NONE_SOLAR
# experiment "us-winter-actual-nosolar" $NONE_SOLAR -b $BROWN_VARIABLE_WINTER --workload $WORKLOAD -g $NONE_SOLAR --green --brown

# experiment "bf-summer-actual-nosolar" $NONE_SOLAR -b $BROWN_VARIABLE_SUMMER --workload $WORKLOAD -g $NONE_SOLAR
# experiment "us-summer-actual-nosolar" $NONE_SOLAR -b $BROWN_VARIABLE_SUMMER --workload $WORKLOAD -g $NONE_SOLAR --green --brown

# experiment "bf-fix-actual-nosolar" $NONE_SOLAR -b $BROWN_FIXED --workload $WORKLOAD -g $NONE_SOLAR
# experiment "us-fix-actual-nosolar" $NONE_SOLAR -b $BROWN_FIXED --workload $WORKLOAD -g $NONE_SOLAR --green --brown

# experiment "bf-winter-actual-worst" $WORST -b $BROWN_VARIABLE_WINTER --workload $WORKLOAD -g $WORST
# experiment "us-winter-actual-worst" $WORST -b $BROWN_VARIABLE_WINTER --workload $WORKLOAD -g $WORST --green --brown

# Parallel jobs
# experiment "bf-fix-actual-best-blocks" $BEST -b $BROWN_FIXED --workload $WORKLOAD_BLOCK -g $BEST
# experiment "us-fix-actual-best-blocks" $BEST -b $BROWN_FIXED --workload $WORKLOAD_BLOCK -g $BEST --green

# Staggered
# experiment "bf-fix-actual-best-spread" $BEST -b $BROWN_FIXED --workload $WORKLOAD_SPREAD -g $BEST
# experiment "us-fix-actual-best-spread" $BEST -b $BROWN_FIXED --workload $WORKLOAD_SPREAD -g $BEST --green

# Regular
# experiment "bf-fix-actual-avg" $AVG -b $BROWN_FIXED --workload $WORKLOAD -g $AVG
# experiment "us-fix-actual-avg" $AVG -b $BROWN_FIXED --workload $WORKLOAD -g $AVG --green

# experiment "bf-fix-actual-best" $BEST -b $BROWN_FIXED --workload $WORKLOAD -g $BEST
# experiment "us-fix-actual-best" $BEST -b $BROWN_FIXED --workload $WORKLOAD -g $BEST --green

# experiment "bf-fix-actual-worstus" $WORSTUS -b $BROWN_FIXED --workload $WORKLOAD -g $WORSTUS
# experiment "us-fix-actual-worstus" $WORSTUS -b $BROWN_FIXED --workload $WORKLOAD -g $WORSTUS --green

# experiment "bf-fix-actual-worst" $WORST -b $BROWN_FIXED --workload $WORKLOAD -g $WORST
# experiment "us-fix-actual-worst" $WORST -b $BROWN_FIXED --workload $WORKLOAD -g $WORST --green

# experiment "bf-fix-actual-bestus" $BESTUS -b $BROWN_FIXED --workload $WORKLOAD -g $BESTUS
# experiment "us-fix-actual-bestus" $BESTUS -b $BROWN_FIXED --workload $WORKLOAD -g $BESTUS --green



# experiment "bf-fix-predicted-bestus" $BESTUS -b $BROWN_FIXED --workload $WORKLOAD -d $DATE_BESTUS 
# experiment "us-fix-predicted-bestus" $BESTUS -b $BROWN_FIXED --workload $WORKLOAD -d $DATE_BESTUS --green

# experiment "bf-fix-predicted-worst" $WORST -b $BROWN_FIXED --workload $WORKLOAD -d $DATE_WORST 
# experiment "us-fix-predicted-worst" $WORST -b $BROWN_FIXED --workload $WORKLOAD -d $DATE_WORST --green

# experiment "bf-fix-predicted-best" $BEST -b $BROWN_FIXED --workload $WORKLOAD -d $DATE_BEST
# experiment "us-fix-predicted-best" $BEST -b $BROWN_FIXED --workload $WORKLOAD -d $DATE_BEST --green


# experiment "bf-fix-actual-bestus" $BESTUS -b $BROWN_FIXED --workload $WORKLOAD -g $BESTUS
# experiment "us-fix-actual-bestus" $BESTUS -b $BROWN_FIXED --workload $WORKLOAD -g $BESTUS --green



# experiment "bf-fix-actual-worstus" $WORSTUS -b $BROWN_FIXED --workload $WORKLOAD -g $WORSTUS
# experiment "us-fix-actual-worstus" $WORSTUS -b $BROWN_FIXED --workload $WORKLOAD -g $WORSTUS --green

# experiment "bf-fix-actual-bestus-blocks" $BESTUS -b $BROWN_FIXED --workload $WORKLOAD_BLOCK -g $BESTUS
# experiment "us-fix-actual-bestus-blocks" $BESTUS -b $BROWN_FIXED --workload $WORKLOAD_BLOCK -g $BESTUS --green

# experiment "bf-fix-actual-best-spread" $BEST -b $BROWN_FIXED --workload $WORKLOAD_SPREAD -g $BEST
# experiment "us-fix-actual-best-spread" $BEST -b $BROWN_FIXED --workload $WORKLOAD_SPREAD -g $BEST --green





# experiment "us-fix-actual-best-spread" $BEST --green --date 2010-8-23T09:00:00


