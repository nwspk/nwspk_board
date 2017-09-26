# nwspk_board

The newspeak screens run on flask - using reveal.js to create the slideshow. 

This consists of two kinds of machine - one that runs the flask server and the rest that access that server. 

There are several difference possible screens, which are chosen randomly (but weighted) when a machine tries to connect. 

To send a flash message (or pin a longer message to a screen) use : http://rpi-lounge:5000/message/

This can force one or all screens to display text for a specificed number of seconds.  Messages are stored in memory and will not persist if server is reset.

The server restarts at 5 minutes past midnight and the rest at 10 past midnight. (in the sudo crontab).

All monitors will try and kill and restart their browsers once an hour (see crontab - could be adjusted to be less severe)

See setup.txt for instructions on creating a new machine (or just clone existing)

Machine names:

rpi-lounge (currently the server)
rpi-drawing
rpi-kitchen
rpi-pantry-1
rpi-pantry-2

All logic code stored in screen.py

If python and fabric are installed, code can be deployed to the machines using 'fab uploadcore' if changing code or 'fab upload' if changing additional files. 

To target a specific machine you can do 'fab target:rpi-lounge uploadcore'.