import socket
import json
import threading
import json
from flask import Flask, session, redirect, url_for, request, render_template
import random
import requests
import time


IP = '192.168.0.111'
IF_PROTECT = False

ONION_LINK = ''

proxies = {
    'http': 'socks5h://localhost:9050',
    'https': 'socks5h://localhost:9050'
}



class Main:
	def __init__(self, serverIP=(IP, 8181), onionLink=ONION_LINK):
		self.onionLink = ONION_LINK
		self.serverIP = serverIP
		self.connectedClients = {}
		self.clientData = {}

		self.onionServiceResponseTime = [0 for i in range(0, 30)]


	def clientFunc(self, client, clientIP):
		try: hostname = socket.gethostbyaddr(clientIP[0])
		except: hostname = clientIP

		self.clientData[hostname] = {
			'temp': [0 for i in range(0, 30)],
			'cpuUsage': [0 for i in range(0, 30)],
			'memoryUsage': [0 for i in range(0, 30)]
		}

		print(f'Client "{hostname}" has been connected.')

		while True:
			try:
				data = client.recv(2048).decode('utf-8')
				
				if data:
					data = json.loads(data)
					self.connectedClients[hostname] = data
					
					try: aTempData = sum([self.connectedClients[hostname]['temp'][cName] for cName in self.connectedClients[hostname]['temp']]) / len(self.connectedClients[hostname]['temp'])
					except: aTempData = 0

					if len(self.clientData[hostname]['temp']) > 30: self.clientData[hostname]['temp'] = self.clientData[hostname]['temp'][1:]
					self.clientData[hostname]['temp'].append(aTempData)

					if len(self.clientData[hostname]['cpuUsage']) > 30: self.clientData[hostname]['cpuUsage'] = self.clientData[hostname]['cpuUsage'][1:]
					self.clientData[hostname]['cpuUsage'].append(self.connectedClients[hostname]['cpuUsage'])				


					if len(self.clientData[hostname]['memoryUsage']) > 30: self.clientData[hostname]['memoryUsage'] = self.clientData[hostname]['memoryUsage'][1:]
					self.clientData[hostname]['memoryUsage'].append(self.connectedClients[hostname]['memoryUsage'])
			except:
				del self.clientData[hostname]
				del self.connectedClients[hostname]

				break



	def startGetter(self):
		self.server = socket.socket()

		self.server.bind(self.serverIP)
		self.server.listen()

		print('Getting server has been started.')

		while True:
			client, clientIP = self.server.accept()
			threading.Thread(target=self.clientFunc, args=(client, clientIP[0])).start()

	def getResponseTime(self):
		startTime = time.time()
		response = requests.get(self.onionLink, proxies=proxies)
		endTime = time.time()
		responseTime = endTime - startTime

		return responseTime


	def gettingResponseTime(self):
		while True:
			try:
				nowData = self.getResponseTime()
				if len(self.onionServiceResponseTime) > 30: self.onionServiceResponseTime = self.onionServiceResponseTime[1:] 

				self.onionServiceResponseTime.append(nowData)
			except: pass


	def run(self, correctPassword='passwordofpanel'):
		threading.Thread(target=self.gettingResponseTime).start()
		threading.Thread(target=self.startGetter, daemon=True).start()
		
		print(f'Monitoring panel password: "{correctPassword}".')


		app = Flask(__name__)
		app.secret_key = ''.join([str(random.randint(0, 9)) for i in range(0, 16)])

		@app.route('/')
		def index():
			if IF_PROTECT:
				if 'active' not in session:
					return '<script>var password = prompt("Enter a password: ", ""); window.location.href = "/login/" + password;</script>'

			toAdd = ''
			for name in self.clientData:
				toAdd += f'<a href="/servermonitor/{name}"><h4>{name}</h4></a>'

			aValue = sum(self.onionServiceResponseTime) / len(self.onionServiceResponseTime)
			return render_template('index.html', aValue=aValue, pingData=self.onionServiceResponseTime, toAdd=toAdd) + toAdd + '</body></html>'


		@app.route('/login/<path:password>')
		def login(password):
			if str(password) == str(correctPassword):
				session['active'] = '1'
				return '<script>window.location.href = "/";</script>'

			return ''

		@app.route('/servermonitor/<path:servername>')
		def serverMonitor(servername):
			if IF_PROTECT:
				if 'active' not in session:
					return '<script>var password = prompt("Enter a password: ", ""); window.location.href = "/login/" + password;</script>'

			try:
				aTempValue = sum(self.clientData[servername]['temp']) / len(self.clientData[servername]['temp'])

				return render_template(
						'servermonitor.html', 
						tempData = self.clientData[servername]['temp'],
						aTempValue = aTempValue,
						cpuData = self.clientData[servername]['cpuUsage'],
						memoryData = self.clientData[servername]['memoryUsage'],
						hostname=str(servername))
			except: return ''


		app.run(host=IP)


if __name__ == '__main__':
	Main().run(correctPassword=''.join([str(random.randint(0, 9)) for i in range(0, 16)]))
