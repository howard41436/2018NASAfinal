import pexpect, math, time
username = 'nasa2finalpj'
password = 'nasa2017'
unable = ['B1-B02-1', 'B1-B02-2']
keywords = ['215', 'core', 'Core', 'CORE', 'CSIE', 'csie', 'Csie']
special = ['B1-B02-1', 'B1-B02-2', '215Core', 'CSIE-Private', 'CSIE-Core', 'wireless-OLD', 'wireless-NEW']
history = dict()
def average(lst):
	return sum(lst)/len(lst)
def standard_deviation(lst):
	return math.sqrt(sum(map(lambda x: x*x, lst))/len(lst) - average(lst) ** 2)
def print_report(id):
	print('report #' + str(id))
	for key in sorted(history):
		if key.isdigit():
			print('Floor ' + key + ':')
		else:
			print('Cabinet ' + key + ':')
		print('\tcurrent rate: ' + str(history[key][-1]))
		print('\taverage rate: ' + str(average(history[key])))
		print('\tstandard deviation: ' +  str(standard_deviation(history[key])))
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
def monitor(id):
	rate_map = dict()
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
				continue
			ssh.sendline('show int | inc Description|5 minute output')
			output = ''
			while ssh.expect(['--More--', name + '#']) == 0:
				output += ssh.before
				ssh.send(' ')
			output += ssh.before
			output_rate = analyze(output)
			#print(name + ': ' + str(output_rate))
			rate_map[name[0]] = rate_map.get(name[0], 0) + output_rate

	for key, val in rate_map.items():
		print(key, val)
		history[key] = history.get(key, []) + [val]
		if len(history[key]) > 1000:
			history[key].pop(0)
	print_report(id)

t = 1
while(1):
	monitor(t)
	t += 1
	time.sleep(10)
