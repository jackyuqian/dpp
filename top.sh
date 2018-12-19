#!/bin/bash
rm -f log
touch log
for ele in `ls res50_ac`
do
    fname="res50_ac/"$ele"/instr_ac.txt"
    cname=$ele
    ./analyze.py -f $fname -c $cname >> log
done
grep -r "Runtime" log
