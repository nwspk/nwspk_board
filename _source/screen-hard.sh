#!/bin/sh
killall epiphany-browser
sleep 10
export DISPLAY=:0
if [ "$HOSTNAME" == "rpi-lounge" ]
then
	epiphany "http://127.0.0.1:5000/assign/?host=$HOSTNAME" &
else
	epiphany "http://192.168.1.58:5000/assign/?host=$HOSTNAME" &
fi
sleep 20
wmctrl -a "Newspeak Board"
xte 'key F11' -x:0