import socket
import psutil
import time


class Client:
	def __init__(self,  monitorServerIP=('192.168.0.111', 8181)):
		self.monitorServerIP = monitorServerIP


	def getInfo(self):
		temp = {}

		try:
			for coreInfo in psutil.sensors_temperatures()['via_cputemp']:
				status = 0 if coreInfo.high else 1
				if coreInfo.critical: status = 2

				temp[f"{coreInfo.label}"] = coreInfo.current
		except: pass

		try: cpuUsage = psutil.cpu_percent(interval=1)
		except: cpuUsage = 0

		try: memoryUsage = psutil.virtual_memory().percent
		except: memoryUsage = 0

		return str(temp).replace('\'', '"'), cpuUsage, memoryUsage


	def main(self):
		while True:
			sender = socket.socket()

			while True:
				try:
					sender.connect(self.monitorServerIP)
					break
				except Exception as error:
					time.sleep(1)


			while True:
				try:
					info = self.getInfo()
					jsonToSend = '{"temp": ' + str(info[0]) + ', "cpuUsage": ' + str(info[1]) + ', "memoryUsage": ' + str(info[2]) + '}'.replace('\'', '"')
					jsonToSend = jsonToSend.encode()

					sender.send(jsonToSend)
				except Exception as error:
					print(error)
					break

			sender.close()



if __name__ == '__main__': Client().main()
