from fabric.api import *
import fabric.contrib.project as project
import os
import shutil
import sys
import SocketServer
import time

env.user = "pi"
env.password = "raspberry"


host_list = [
			'rpi-lounge',
			'rpi-drawing',
			'rpi-pantry-1',
			'rpi-pantry-2',
			'rpi-kitchen',
			]
			
env.hosts = host_list
	
def target(h):
	env.hosts = [h]

def restart():
	sudo("shutdown -r 0")

def start_browser():
	run("cd /home/pi/nwspk_board/_source && nohup bash screen.sh")

def start():
	run("cd /home/pi/nwspk_board/_source && nohup bash boot.sh")
	
def run_server():
	sudo("cd /home/pi/nwspk_board/_source && nohup bash run.sh")
	
def close_browser():
	sudo("killall epiphany-browser")

def createdir():
	sudo('mkdir /home/pi/nwspk_board')
	sudo('chmod 777 /home/pi/nwspk_board')
	
def upload():
	put('_source', '/home/pi/nwspk_board',use_sudo=True)
	
def uploadcore():
	put(r'_source\screen.py', '/home/pi/nwspk_board/_source/screen.py',use_sudo=True)
	put(r'_source\screen.sh', '/home/pi/nwspk_board/_source/screen.sh',use_sudo=True)
	put(r'_source\screen-hard.sh', '/home/pi/nwspk_board/_source/screen-hard.sh',use_sudo=True)
	put(r'_source\templates\index.html', '/home/pi/nwspk_board/_source/templates/index.html',use_sudo=True)