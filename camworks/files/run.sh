#!/bin/bash

echo -n "Container is starting at $START - "
date

set -e

google-chrome --version
firefox --version

# Here's a hack for fixing the problem with Chrome not starting in time
# See https://github.com/SeleniumHQ/docker-selenium/issues/87#issuecomment-250475864

PATH=$PATH:/etc/default/dbus

rm -f /var/lib/dbus/machine-id
mkdir -p /var/run/dbus
service dbus restart > /dev/null
service dbus status > /dev/null
export $(dbus-launch)
export NSS_USE_SHARED_DB=ENABLED

# Start adb server and list connected devices
if [ -n "$START_ADB_SERVER" ] ; then
   adb start-server
   adb devices
fi

# Inspired by docker-selenium way of shutting down
function shutdown {
  kill -s SIGTERM ${PID}
  wait $PID
}

cd /opt/monroe/
export PATH=$PATH:/opt/monroe/

#echo -n "Experiment starts using git version "
#cat VERSION

#ifconfig op0 mtu 1430

START=$(date +%s)

# The main experiment and the headless-browser
python experiment.py
echo -n "Finished experiment"
python browsertime.py
echo -n "Finished headless browser"

STOP=$(date +%s)
DIFF=$(($STOP - $START))

echo -n "Container is finished at $STOP - "
date

echo "Container was running for $DIFF seconds"
