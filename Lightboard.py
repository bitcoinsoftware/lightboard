import serial
import AlcatelWallboardSimulator
import subprocess
import time
import getopt
import urllib2
from urllib2 import Request

class Lightboard:
	rows = 2
	cols = 16
	device_address = "/dev/ttyUSB0"
	message_file_address = "/home/odroid/Desktop/lightboard/message.txt"
	url = "http://nice-idea.org/index.php/tablica/"
	network_details_save_url = "/var/www/index.html"
	baud = 9600
	timeout =1.0
	pause_between_messages = 3.0
	
	_current_row = 0;
	special_codes = ["<green>", "<red>", "<yellow>", "<orange>", "<light_red>", "<net_details>",
					 "<date>", "<endl>", "<time>", "<blink>", "<static>", "<clean>", "<pause>"]
	start_text_marker = "STARTTEXT"
	stop_text_marker  = "STOPTEXT"
	
	def __init__(self, simulation = False):
		if simulation:
			self.ser = AlcatelWallboardSimulator.AlcatellWalboardSimulator()
		else:
			self.ser = serial.Serial(self.device_address, self.baud, timeout=self.timeout)
		self.clean()
		
	def clean(self):
		self.ser.write("\x8E")
		
	def beep(self):
		self.ser.write("\x8D")
		
	def set_red_color(self):
		self.ser.write("\x80")
		
	def set_light_red_color():
		self.ser.write("\x81")
		
	def set_yellow_color(self):
		self.ser.write("\x82")
		
	def set_orange_color(self):
		self.ser.write("\x83")
		
	def set_green_color(self):
		self.ser.write("\x87")
		
	def set_bright_text(self):
		self.ser.write("\x84")
		
	def set_dimm_text(self):
		self.ser.write("\x85")
		
	def set_very_dim_text(self):
		self.ser.write("\x86")
		
	def go_to_first_row(self):
		self.ser.write("\x89")
		
	def go_to_second_row(self):
		self.ser.write("\x8A")
		
	def set_blinking_text(self):
		self.ser.write("\x8C")
		
	def set_static_text(self):
		self.ser.write("\x8B")
		
	def write_word(self, word):
		self.ser.write(word)
		
	def _change_row_and_screen(self):
		if self._current_row==0:
			self.go_to_second_row()
			self._current_row=1
		else:
			self.clean()
			self.go_to_first_row()
			self._current_row=0
			
	def _execute_special_code(self, code):
		if code=="<green>":
			self.set_green_color()
		elif code=="<red>":
			self.set_red_color()
		elif code=="<yellow>":
			self.set_yellow_color()
		elif code=="<orange>":
			self.set_orange_color()
		elif code=="<light_red>":
			self.set_light_red_color()
		elif code=="<blink>":
			self.set_blinking_text()
		elif code=="<static>":
			self.set_static_text()
		elif code=="<time>":
			time_str =  time.strftime("%H:%M", time.gmtime())
			self.write_word(time_str)
		elif code=="<date>":
			date_str = time.strftime("%m-%d", time.gmtime())
		elif code=="<endl>":
			self._change_row_and_screen()
		elif code =="<clean>":
			self.clean()
			self._current_row=0
		elif code =="<pause>":
			time.sleep(self.pause_between_messages)
		elif code =="<net_details>":
			pass # already executed in main loop

	def get_text(self):	
		text=""	
		try:
			req = Request(self.url)
			content = urllib2.urlopen(req, timeout=5).read()
			text_start_index = content.find(self.start_text_marker)+len(self.start_text_marker)
			text_stop_index = content.find(self.stop_text_marker)
			text = content[text_start_index:text_stop_index].replace('#', '<').replace('*', '>')
			if len(text)>0:
				storage_file = open(self.message_file_address, "w")
				storage_file.write(text)
				storage_file.close()
			#else:
				#raise ValueError('Got empty text from webpage')
		except:
			print "connection problem"
			try:
				f = open(self.message_file_address)
				text = f.read()
			except:
				text = "could not read file"
		return text
		
	def save_network_details(self):
		details =""
		try:
			det = subprocess.Popen("ifconfig", stderr=subprocess.STDOUT, stdout=subprocess.PIPE).communicate()
			for word in det[0].split():
				i = word.find("addr:")
				if i!=-1 and len(word)>i+1:
					details += (word[i:]+ " ")
		except:
			pass

		try:
			det = subprocess.Popen("iwconfig", stderr=subprocess.STDOUT, stdout=subprocess.PIPE).communicate()
			for word in det[0].split():
				i = word.find("ESSID:")
				if i !=-1:
					details += (word[i:]+ " ")
					break
		except:
			pass
		try:	
			with open(self.network_details_save_url, "w") as f:
				f.write(str(details).replace("\n", "<br>"))
		except:
			pass
		return details
		
	def write_dynamic_text (self,  pause_beetween_words = 0.9, print_to_stdout = False):
		while 1:
			try:
				
				text = self.get_text()
				if text.find("<net_details>")!=-1:
					net_details = self.save_network_details()
					text = text.replace("<net_details>", net_details)
					text = text.replace("addr:" ,"")
					text = text.replace("127.0.0.1" ,"")
				
				splited_text = text.split()
				letter_count=0
				for i in range(len(splited_text)):
					word = splited_text[i].strip()
					if word in self.special_codes:
						self._execute_special_code(word)
					else:
						if len(word)<=16:
							if letter_count + len(word)>16:
								self._change_row_and_screen()
								letter_count=0
							if letter_count + len(word)<=16:
								letter_count += len(word)
								self.write_word(word)
								if letter_count < 16:
									self.write_word(" ")
									time.sleep(pause_beetween_words)
						else:
							splited_text.pop(i)
							part1 = word[:14]+"-"
							part2 = word[15:]
							splited_text.insert(i, part1)
							splited_text.insert(i, part2)
							
				self.clean()
			except:
				print "There was an error"

if __name__ == "__main__":
	l = Lightboard()
	l.write_dynamic_text(print_to_stdout = True)
					
										
		
