#!/bin/sh
for i in {1..3}
do
	dig $1
	sleep 10
done
