#!/usr/bin/env python3
# -*- coding: utf-8 -*-"
""" HNGN001 Created on Tue Jun 11 08:34:11 2019
(two days before 190613) (1month before 190711)"""


s1="""HNGN1は、澄江さんが亡くなる2日前に書いたもの。輻射伝熱について勉強しようとしていた。
仏像を1000体彫るように、Pythonコードを1000作る\n """

s2="""
SN2_Blk2を運用する。
モータ（八下田さんの努力で）中華モータを動かす
ADCシールドを用いて圧力計測の桁数を上げる
＞＞
（HNGN208）をもとに
(HNGN242)Drying, 九大@H101 {220213}のADCシールドをつかう。
"""

s2_0="""
（運転シナリオ）
まず、計測できるようにすることと（温度を測り始める）
つぎに、最初にSN2を回したときは、タンクを温めた（上部タンクに到達を確かめるため）、でもこれは不必要だろう。
つぎに、圧力をかけて、タンクから液体を凹部タンクまで上げる。（こんどは窒素でやろうね）
圧力の制御は、あまりこだわらなくて、上部タンクでバブルが出ても水だからよいことにして、練習する、データをを取る。
つぎに、垂直ヒータを点灯して温度を制御してあげていく。そんなに高い温度にしない（せいぜい 50度くらい）
つぎに、
"""

import os
import time
import sys
import serial
import syslog
import matplotlib.pyplot as plt
import numpy as np
import RPi.GPIO as GPIO
import datetime
from read_shield_class import Shield  #{211128} chiba
import ADS1256                        #{211128} chiba
import pigpio
#import HNGN262_220313.py 

# GO/STOP control of this program {220128}
if not(os.path.exists('going.txt')):
	file1 = "going.txt"
	f=open(file1,"a+")

"""
Plot, plotting, プロット
"""
#xdata = []
#ydata1 = [] 
#ydata2= []
#plt.show()

#axes = plt.gca()
#axes.set_xlim(0, 1000)
#axes.set_ylim(2.9, 3.5)
#line1, = axes.plot(xdata, ydata1, 'r-')
#line2, = axes.plot(xdata, ydata2, 'b-')


#// Thermocouple reader (M5 based) of Yoshizawa of 0.1sec
def read_m5(port,speed):	
	#The following line is for serial over GPIO	
	ser = serial.Serial(port,speed)
	#>>
	# Serial read section
	line = ser.readline()
	line2=line.strip().decode('utf-8')
	data = [str(val) for val in line2.split(",")]
	return data

#// タイムスタンプの設定
#   time stamp 
def time_stamp():   #// 時刻、時間（unix time）のセットアップ
  dt_now = datetime.datetime.now()
  time_stamp_out=dt_now.strftime('%Y-%m-%d %H:%M:%S.%f')
  return time_stamp_out


# GPIOをセットアップする
GPIO.cleanup()
#
# setting_up GPIO nr, AD_DA_shield_pin_nr 
SSR1_GPIO_n = 5   #21       Heating bottom_drain_tank (bottom of bottom)
SSR2_GPIO_n = 6   #22       Valve_1 inlet to Capasiter tank 
SSR3_GPIO_n = 13  #23       Valve_2 relief/evacuation
SSR4_GPIO_n = 19  #24       Heating pipe (core simulation)
SSR5_GPIO_n = 26  #25       Cooling air blower
SSR6_GPIO_n = 20  #28       not used
SSR7_GPIO_n = 21  #29       not used

#
GPIO.setmode(GPIO.BCM)
GPIO.setup(SSR1_GPIO_n, GPIO.OUT)
GPIO.setup(SSR2_GPIO_n, GPIO.OUT)
GPIO.setup(SSR3_GPIO_n, GPIO.OUT)
GPIO.setup(SSR4_GPIO_n, GPIO.OUT)
GPIO.setup(SSR5_GPIO_n, GPIO.OUT)
GPIO.setup(SSR6_GPIO_n, GPIO.OUT)
GPIO.setup(SSR7_GPIO_n, GPIO.OUT)

def All_shutdown():
	GPIO.output(SSR1_GPIO_n, False)
	GPIO.output(SSR2_GPIO_n, False)
	GPIO.output(SSR3_GPIO_n, False)
	GPIO.output(SSR4_GPIO_n, False)
	GPIO.output(SSR5_GPIO_n, False)
	GPIO.output(SSR6_GPIO_n, False)
	GPIO.output(SSR7_GPIO_n, False)
	return


def OnOff(i,j,k,i1,i2,i3,i4,i5,i6,i7,i1f,i2f,i3f,i4f,i5f,i6f,i7f): 
	"""
	version = {220104}
   Here On/Off period is set in fixed cycle (eg., 0 to 99).
	"""
	if (i==i1):GPIO.output(SSR1_GPIO_n, True)
	if (i==i2):GPIO.output(SSR2_GPIO_n, True) #set on by j
	if (j==j3):GPIO.output(SSR3_GPIO_n, True)
	if (i==i4):GPIO.output(SSR4_GPIO_n, True)
	if (i==i5):GPIO.output(SSR5_GPIO_n, True) 
	if (i==i6):GPIO.output(SSR6_GPIO_n, True) 
	if (i==i7):GPIO.output(SSR7_GPIO_n, True) 
	#
	if (i==i1f):GPIO.output(SSR1_GPIO_n, False)
	if (i==i2f):GPIO.output(SSR2_GPIO_n, False) #set off by i 
	if (i==i3f):GPIO.output(SSR3_GPIO_n, False)
	if (i==i4f):GPIO.output(SSR4_GPIO_n, False)
	if (i==i5f):GPIO.output(SSR5_GPIO_n, False)
	if (i==i6f):GPIO.output(SSR6_GPIO_n, False) 
	if (i==i7f):GPIO.output(SSR7_GPIO_n, False)
	return 


#// 熱電対の温度を読んで、それをプリントしてファイルにも書き出す
#   read thermocouple and put file/recording

#温度を計るポートの設定
#port = sys.argv[1]    #for manual setup then use port = sys.argv[1]
port = "/dev/ttyUSB0"  #OBS! （２台以上つないでいるので）間違えないように確認のこと
speed = 19200

timetime0=time.time() #unix-time


#// 圧力の変化をファイルに保存する {210716}
#   read pressure change and put file/recording
#   Pressure gauge reasing プレッシャーゲージのデータを読む
shield=Shield()
def get_gas_Kpascal():
	#reading_pressure_meter
	#MPS-C35R-NCA  OBS! C35 not P35
	p_volts=shield.read_shield() #{211128} chiba {211222} kinoshita
	d1=data1=float(p_volts[2])
	d2=data2=float(p_volts[3])
	#1.4V = 0Kpascal
	tsec=time.time()-timetime0
	s2=f"""time={tsec},p_volts {d1},{d2} """
	print (s2)
	return tsec,d1,d2

# data-recording
job_subject="SN2_Blk2_Operation"
file1 = "LP_HNGN250_" + job_subject + "_P&T-220321A.txt"
f=open(file1,"a+")
s2=f"""job250_job {job_subject} start  {time_stamp()}"""
print(s2)
f.write(s2 + "\n") 


# (initial) setting parameters of ssr_contorol status
global i,j,k;i,j,k=0,0,0
global i1,i2,i3,i4,i5,i6,i7;i1,i2,i3,i4,i5,i6,i7=0,0,0,0,0,0,0
global i1f,i2f,i3f,i4f,i5f,i6f,i7f;i1f,i2f,i3f,i4f,i5f,i6f,i7f=0,0,0,0,0,0,0


# =========================================================
# OBS! ==== set power-on/off at statements below  ==== OBS!
i1=0; i1f=0; i1f_set=i1f #Heating bottom_drain_tank (bottom of bottom)
i2=0; i2f=0; i2f_set=i2f #Valve_1 inlet to Capasiter tank
j3=0; i3f=3; i3f_set=i3f #Valve_2 evacuation 
i4=0; i4f=0; i4f_set=i4f #Heating pipe (core simulation)
i5=0; i5f=0; i5f_set=i5f #Cooling air blower
i6=0; i6f=0; i6f_set=i6f #not used
i7=0; i7f=0; i7f_set=i7f #not used

# もろもろのはじまり、まず電源を落としてから始める。
All_shutdown()

data_y=[0]*1000   # y axis
while os.path.exists('going.txt'):
	try:
		array=read_m5(port,speed) #reading thermo_cpuple, tc_reader 
		# cycles_control, where delta_time comes from tc_reader
		# memo, explanation ==>（588d1）

		if i==0: 
			#print Tc and time_stamp 
			s12=f""" {time_stamp()}, {array}"""
			print(s12)
			Tc= [float(array[1]),float(array[2]),float(array[3]),float(array[4]),float(array[5]),
			float(array[6]),float(array[7]),float(array[8]),float(array[9]),float(array[10])]
			s12b=f"""print Tc Tc={Tc}, and maxTc_meas={max(Tc)}"""
			#print(s12b)

			i_list=[i,i1,i2,i3,i4,i5,i6,i7,i1f,i2f,i3f,i4f,i5f,i6f,i7f]
			#test pressure
			tsec,d1,d2=get_gas_Kpascal()
			
			""" plotting """
			#plotting 
			plt.clf()
			time_x=range(0, 1000, 1) # x axis
			data_y.pop(-1)
			data_y.insert(0,d2)
			plt.title(str(tsec))  # title of plot as time
			plt.ylim(0,5)
			plt.plot(time_x,data_y)
			plt.pause(0.01)
		
		if i==0:  #print/write when j-cycle is over, which is independent of i-cycle
			# print pressure, P is changing very fast so that every one second data is necessary
			s13=f""" {time_stamp()}, P_Volt= {d2:.6f}"""
			s13f=f""" {time_stamp()}, P_Volt= {d2:.6f}, Tc= {Tc}, maxTc_meas={max(Tc)}, iL={i_list}"""
			print(s13)
			f.write(s13f + "\n") 
			print()

		# Drain_tank Pressure control by release valve
		d2_1=3.03
		d2_2=3.1
		d2_3=3.25

		"""
		if (d2>d2_1):
			i3f=0 #OBS! drain_tank is i3
		"""

		if (d2>d2_3):
			s13=f"""job_P2 exceeds limit {d1}, {d2}, do shutdowm""";print(s13);f.write(s13 + "\n")
		

		# Temperature control
		
		OnOff(i,j,k,i1,i2,i3,i4,i5,i6,i7,i1f,i2f,i3f,i4f,i5f,i6f,i7f)

		i+=1;j+=1;k+=1
		#set cycle time here:
		if i==9:i=0     #cycle time= 1 seconds by setting 9
		if j==99:j=0    #cycle time= 10 seconds by setting 99
		if k==999:k=0    #cycle time= 100 seconds by setting 999
	#
	except ValueError as e:
		print(e,"i=",i)
	except IndexError as e:
		print(e, "i=",i)
		s="""ファイルの最期に到達。"""
		print(s)
	except Exception as e:
		print('Exception:',i,e)
	except KeyboardInterrupt:
		print ('exiting by cntl-C')
		All_shutdown()
		GPIO.cleanup()
		break
print("job1 end of " + job_subject)
All_shutdown()
GPIO.cleanup()
f.write("job1 end of " + job_subject + "\n") 

# final process
pi.set_mode(gpio_pin0, pigpio.INPUT)
pi.stop()

sys.exit()
