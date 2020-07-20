# -*- coding: utf-8 -*-
from socket import *
import datetime
import os
import traceback
import threading
import re
from os.path import join, getsize
import time
###################################
#393620170@qq.com
#用于接收syslog日志，并将日志存储为文本文件
#v0.7
#2019.01.17
###################################

#删除历史日志文件
def clear_histroy_logfile(logdir):
	while True:
		try:
			max=open('syslog.conf','r',encoding='UTF-8')
			max_file_volume=re.findall('max_file_volume:(\d+)',max.read())[0]
			size,fctime=getdirsize(logdir)
			if size>int(max_file_volume)*1024:
				print('当前日志文件夹已经超过设定'+max_file_volume+'G，建议进行日志清理，当前日志文件大小：'+str(size)+'MB')
				t=0
				k=''
				for k,c in fctime.items():
					if t==0 or t>c:
						t=c
						f=k
				print('删除文件：'+f)
				os.remove(f)
			else:
				print('当前日志文件夹文件大小：' + str(size)+'MB')
			time.sleep(60)
		except:
			traceback.print_exc(file=open('syslog_error.log', 'a+'))

#获取文件夹的大小
def getdirsize(dir):
	size = 0
	files_ctime = {}
	for root, dirs, files in os.walk(dir):
		size += sum([getsize(join(root, name)) for name in files])
		for filename in files:
			files_ctime [root+'/'+filename]=os.path.getctime(join(root, filename))
	return int(size/1024/1024),files_ctime
#接收日志
def write_logfile(s,log_file_type):
	while True:
		try:
			data,clentaddr=s.recvfrom(8092)
			if not os.path.exists('log'):
				os.mkdir('log')#创建log文件夹
			if not os.path.exists('log/'+clentaddr[0]):
				os.mkdir('log/'+clentaddr[0])#创建设备日志存放文件夹
			if log_file_type=='1':
				#5分钟一个日志文件
				min = int(datetime.datetime.now().strftime('%M')) // 5
				log_filename = datetime.datetime.now().strftime('%Y-%m-%d-%H')+'-'+str(5*min)
			elif log_file_type=='2':
				#30分钟一个日志文件
				min = int(datetime.datetime.now().strftime('%M')) // 30
				log_filename = datetime.datetime.now().strftime('%Y-%m-%d-%H') + '-' + str(30 * min)
			elif log_file_type=='3':
				log_filename=datetime.datetime.now().strftime('%Y-%m-%d-%H')
			else:
				log_filename=datetime.datetime.now().strftime('%Y-%m-%d')
			log=open('log/'+clentaddr[0]+'/'+log_filename+'.log','ab+')
			#if os.path.exists(log_filename+'.log'):
				#pass
			#else:
				#log_record=open('log/'+log_filename+'.log','ab+')
			log.write(data)
			log.write(b'\r\n')
			log.close()
			#get_log = open('log/' + clentaddr[0] + '/' + log_filename + '.log')
			#print('已接收日志：'+str(len(get_log.readlines()))+'条')
			loginfo='\n收到来自'+clentaddr[0]+'的日志，日志内容如下：'
			print(loginfo)
			print(data)
		except:
			traceback.print_exc(file=open('syslog_error.log','a+'))
			print('日志处理异常！忽略该日志。')



#程序开始
#读取配置文件
print('欢迎使用python syslog for window v0.8\n')
if os.path.exists('syslog.conf'):
	syslogconf=open('syslog.conf',encoding='UTF-8')
	print('读取配置文件...\n')
	for conf in syslogconf.readlines():
		conf_line=conf.split(':')

		if 'host' in conf:
			host = conf_line[1]
		if 'port' in conf:
			port=int(conf_line[1])
		if 'storage_mode' in conf:
			storage_mode=conf_line[1]
		if 'max_file_volume' in conf:
			max_file_volume=conf_line[1]
	if not storage_mode:
		storage_mode ='4'
	if not max_file_volume:
		max_file_volume='10'
else:
	host = input('输入服务侦听IP（默认为侦听所有网卡）：') or '0.0.0.0'
	port = input('服务侦听端口：') or  '514'
	print('\n#############################################\n')
	print('1：每5分钟保存一个日志文件;')
	print('2：每30分钟保存一个日志文件;')
	print('3：每小时保存一个日志文件(默认);')
	print('4：每天保存一个日志文件;')
	print('\n')
	storage_mode=input('请选择日志文件存储方式：') or '3'
	print('\n#############################################\n')
	max_file_volume=input('设置日志文件最大容量（G）：') or '2'
	print('\n#############################################\n')
	sysconf=open('syslog.conf','w',encoding='UTF-8')
	sysconf.write('#服务器侦听地址，默认为整体所有网卡\nhost:' + host + '\n')
	sysconf.write('#服务器侦听端口，默认是upd514\nport:' + port + '\n')
	sysconf.write('#日志存储方式：\n#1：每5分钟保存一个日志文件;\n#2：每30分钟保存一个日志文件;\n#3：每小时保存一个日志文件(默认);\n#4：每天保存一个日志文件;\nstorage_mode:' + storage_mode + '\n')
	sysconf.write('#日志存储容量，单位为GB\nmax_file_volume:' + max_file_volume + '\n')
	sysconf.close()

print('\n服务侦听端口:UDP ' + str(port) + '\n')
print('请将网络设备syslog配置指向到当前服务器！\n')
print('开始接收日志...\n')
try:
	addr=(host,int(port))
	s=socket(AF_INET,SOCK_DGRAM)
	s.bind(addr)
except:
	print('程序启动异常，请检查是否存在端口冲突。')
	traceback.print_exc(file=open('syslog_error.log', 'a+'))
	input('按任意键退出')
	exit()



#启动日志接收进程
t1=threading.Thread(target=write_logfile,args=(s,storage_mode))
t1.start()

#启动文件清理线程
t2=threading.Thread(target=clear_histroy_logfile,args=('log/',))
t2.start()

#清除错误日志
while True:
	try:
		time.sleep(3600)
		print('\n清除错误日志 syslog_error.log\n')
		os.remove('syslog_error.log')

	except:
		time.sleep(3600)
		continue
