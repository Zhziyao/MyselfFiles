#! /usr/bin/env python
import os
import sys
import shutil
import time,datetime
import smtplib
import string 
import subprocess
import threading
#from email.mine.text import MIMEText


BuilddirAndGit =  [['libva','https://github.com/01org/libva.git',''],
					['intel-vaapi-driver','https://github.com/01org/intel-vaapi-driver.git',''],
					['ffmpeg','git://source.ffmpeg.org/ffmpeg.git',''],
					['libyami','https://github.com/01org/libyami.git',''],
					['libyami-utils','https://github.com/01org/libyami-utils.git','']]

BuildCmd = [['./autogen.sh', 'VAAPI_PREFIX',   ' '],
			   ['./autogen.sh', 'VAAPI_PREFIX',   ' '],
 			   ['./configure',  'VAAPI_PREFIX',   ' '],
 			   ['./autogen.sh', 'LIBYAMI_PREFIX', '--enable-vp9dec --enable-vp8enc --enable-jpegenc --enable-h265enc --enable-h265dec --enable-vc1dec --enable-mpeg2dec'],
 			   ['./autogen.sh', 'LIBYAMI_PREFIX', '--enable-avformat']]

def cloneSources(aBuilddirAndGit):
	rootPath = os.getcwd();
	for aDirGit in aBuilddirAndGit:
		cloneCmd = 'git clone '
		pullCmd = 'git pull'
		if aDirGit[0] == 'ffmpeg':
			continue
		if not os.path.exists(aDirGit[0]):
			if aDirGit[2] =='':
				cloneCmd = cloneCmd + aDirGit[1]
				i = 0
				state = os.system(cloneCmd)
				while state != 0:
					state = os.system(cloneCmd)
					i = i + 1
					if i == 5:
						failCloneMessage = 'clone ' + aDirGit[0] + 'failed\n'
						print(failCloneMessage)
						break
		else:
			state = 0
			os.chdir(aDirGit[0])
			pullMessage = 'Update ' + aDirGit[0] + 'result \n'
			print(pullMessage)
			os.system(pullCmd)
			os.chdir(rootPath)



def build(aBuilddirAndGit, aBuildCmd):
	rootPath = os.getcwd()
	index = 0
	for acmd in aBuildCmd:
		os.chdir(aBuilddirAndGit[index][0])
		buildMessage = '######################' + 'Build ' + aBuilddirAndGit[index][0] + '######################'
		print(buildMessage)
		buildCmd = acmd[0] + ' --prefix=' + os.getenv(acmd[1]) + ' ' + acmd[2] + ' && make -j8 && make install'
		i = 0
		state = os.system(buildCmd)
		while state != 0:
			os.system('git clean -dxf')
			state = os.system(buildCmd)
			i = i + 1
			if i == 3:
				failMessage = 'Build ' + aBuilddirAndGit[index][0] + ' failed\n'
				print(failMessage)
				break
		buildMessage = '######################' + 'Build ' + aBuilddirAndGit[index][0] + 'Success' + '######################'
		print(buildMessage)
		os.chdir(rootPath)
		index = index + 1


cloneSources(BuilddirAndGit)

build(BuilddirAndGit, BuildCmd)