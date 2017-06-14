#!/bin/sh

case "$(pidof epiphany-browser | wc -w)" in

0)
sleep 10
export DISPLAY=:0
if [ "$HOSTNAME" == "rpi-kitchen" ]
then
	epiphany http://192.168.1.58:5000/random/ &
else
	epiphany http://127.0.0.1:5000/random/ &
fi
sleep 20
wmctrl -a "Newspeak Board"
xte 'key F11' -x:0
;;
1) echo "already running"
;;
esac