from __future__ import print_function
import pexpect
import math
import time
from slackclient import SlackClient

SLACK_BOT_TOKEN='xoxb-o523368551824-524049843923-PPDJEdHMX5Ss3LXEUbvH08xk'
CHANNEL='DFE1FQXD1'

username = 'nasa2finalpj'
password = 'nasa2017'
unable = ['B1-B02-1', 'B1-B02-2']
keywords = ['215', 'core', 'Core', 'CORE', 'CSIE', 'csie', 'Csie']
special = ['B1-B02-1', 'B1-B02-2', '215Core', 'CSIE-Private', 'wireless-OLD', 'wireless-NEW']
threshold = 1.3
history = dict()

def call_slack(bot_msg):
	slack_client.api_call("chat.postMessage", channel=CHANNEL, text=bot_msg)

def average(lst):
	return sum(lst)/len(lst)

def standard_deviation(lst):
	return math.sqrt(sum(map(lambda x: x*x, lst))/len(lst) - average(lst) ** 2)

def print_report(id):
	print('Report #' + str(id))
	for key in sorted(history):
		if key.isdigit():
			print('Floor ' + key + ':')
		elif key[0] != 'V':
			print('Cabinet ' + key + ':')
		else:
			print(key + ':')
		cur_rate, avg_rate = history[key][-1], average(history[key])
		std_dev = standard_deviation(history[key])
		print('\tcurrent rate: ' + str(cur_rate))
		print('\taverage rate: ' + str(avg_rate))
		print('\tstandard deviation: ' +  str(std_dev))
		print('\tstatus: ', end = '')
		if len(history[key]) > 3 and cur_rate > max(2000, avg_rate + threshold * std_dev):
			print('strange')
		else:
			print('normal')
	return

def analyze(context):
	pre = False
	ret = 0
	for line in context.split('\n')[1:]:
		line = line[:-1]
		if 'Description' in line:
			for keyword in keywords:
				if keyword in line:
					pre = True
					break
		elif '5 minute output rate' in line:
			if pre == True:
				numbers = []
				for word in line.split(' '):
					if(word.isdigit()):
						numbers.append(int(word))
				ret += numbers[1]
				pre = False
	return ret

def analyze2(context):
	pre = False
	ret = dict()
	for line in context.split('\n')[1:]:
		line = line[:-1]
		if 'Vlan' in line:
			pre = True
			for word in line.split(' '):
				if 'Vlan' in word:
					vlan_id = word
					break
		elif '5 minute' in line:
			if pre == True:
				numbers = []
				for word in line.split(' '):
					if(word.isdigit()):
						numbers.append(int(word))
				ret[vlan_id] = numbers[1]
				if '5 minute output' in line:
					pre = False
	return ret

def monitor(id, ssh_list):
	rate_map = dict()
	with open('list.txt') as switchlist:
		for line in switchlist:
			ip, name = line.split(' ')
			name = name[:-1]
			if name in special:
				continue
			ssh = SSH[name]
			if ssh is None:
				continue
			'''
			ssh = pexpect.spawn('/usr/bin/ssh ' + username + '@' + ip)
			ssh.expect('assword:')
			ssh.sendline(password)
			try:
				ssh.expect('#', timeout = 10)
			except:
				print(name + ' timeout')
				continue
			'''
			if name == 'CSIE-Core':
				msg = 'show int | inc Vlan|5 minute'
			else:
				msg = 'show int | inc Description|5 minute output'
			ssh.sendline(msg)
			output = ''
			while ssh.expect(['--More--', name + '#']) == 0:
				output += ssh.before.decode('ascii')
				ssh.send(' ')
			output += ssh.before.decode('ascii')
			if name != 'CSIE-Core':
				output_rate = analyze(output)
			else:
				output_rate = analyze2(output)
			#print(name + ': ' + str(output_rate))
			if name != 'CSIE-Core':
				rate_map[name[0]] = rate_map.get(name[0], 0) + output_rate
			else:
				for key, val in output_rate.items():
					rate_map[key] = rate_map.get(key, 0) + val
	
	for key, val in rate_map.items():
		print(key, val)
		history[key] = history.get(key, []) + [val]
		if len(history[key]) > 1000:
			history[key].pop(0)
	print_report(id)

SSH = dict()
with open('list.txt') as switchlist:
	for line in switchlist:
		ip, name = line.split(' ')
		name = name[:-1]
		if name in special:
			continue
		ssh = pexpect.spawn('/usr/bin/ssh ' + username + '@' + ip)
		ssh.expect('assword:')
		ssh.sendline(password)
		try:
			ssh.expect('#', timeout = 10)
		except:
			print(name + ' timeout')
			SSH[name] = None
			continue
		SSH[name] = ssh

slack_client = SlackClient(SLACK_BOT_TOKEN)
if slack_client.rtm_connect(with_team_state=False):
	print("Starter Bot connected and running!")
else:
	print("Connection failed. Exception traceback printed above.")
	exit()

t = 1
while(1):
	monitor(t, SSH)
	t += 1
	time.sleep(10)
