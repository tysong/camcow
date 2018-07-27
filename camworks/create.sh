#!/bin/bash

## This will spin up a new experiment and then dump the CLI output into exp_ids.txt
## It will also generate results.sh, which you can use to download the results data 


EXP=$(monroe create camcow/camworks --nodecount 1 --duration 3200 --traffic 50 --storage 30)
echo "$EXP" >> exp_ids.txt

EXP_ID=$(echo $EXP | sed 's/[^0-9]*//g')
echo "monroe results $EXP_ID" > results.sh
