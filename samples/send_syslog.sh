#!/bin/bash
# send_syslog.sh
# Sends a test Syslog message to the Fluent Bit collector.

HOST="127.0.0.1"
PORT="514"

echo "Sending Syslog message via UDP to $HOST:$PORT..."
echo "<14>$(date +'%b %d %H:%M:%S') mymachine test_app: event=\"TestSyslog\" src=\"10.0.0.5\" user=\"testuser\" reason=\"Testing UDP Syslog\"" | nc -w 1 -u $HOST $PORT

echo "Sending Syslog message via TCP to $HOST:$PORT..."
echo "<14>$(date +'%b %d %H:%M:%S') mymachine test_app: event=\"TestSyslog\" src=\"10.0.0.6\" user=\"testuser\" reason=\"Testing TCP Syslog\"" | nc -w 1 $HOST $PORT

echo "Done."
