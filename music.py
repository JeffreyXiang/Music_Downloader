import os
import random
import requests
import json
import base64
from lxml import etree


class QQMusic:

	status=0

	def __init__(self,url):
		self.URL=url
		self.Check_URL();
		if self.status == 0:
			self.Get_songmid()
			self.Get_information()
			self.Get_guid()
			self.Get_param()

	def Check_URL(self):
		if 'https://y.qq.com/n/yqq/song/' not in self.URL or '.html' not in self.URL:
			print('Error: Illegal URL')
			self.status=-1

	def Get_songmid(self):
		self.songmid=self.URL[self.URL.rindex('/')+1:self.URL.rindex('.')]

	def Get_information(self):
		try:
			HTML=etree.HTML(requests.get(self.URL).content)
			self.songid=HTML.xpath('//a[@class="mod_btn js_more"]/@data-id')[0]
			url='https://u.y.qq.com/cgi-bin/musicu.fcg?data={"songinfo":{"method":"get_song_detail_yqq","param":{"song_type":0,"song_mid":"%s","song_id":%s},"module":"music.pf_song_detail_svr"}}' % (self.songmid,self.songid)
			response=json.loads(requests.get(url).content.decode())
			self.title=response['songinfo']['data']['track_info']['title']
			self.singer=response['songinfo']['data']['track_info']['singer'][0]['name']
			for i in range(1,len(response['songinfo']['data']['track_info']['singer'])):
				self.singer+="&"+response['songinfo']['data']['track_info']['singer'][i]['name']
			self.filename=self.singer+" - "+self.title
		except:
			print('Error: Failed to request information')
			self.status=-2

	def Get_guid(self):
		self.guid=random.randint(9000000000, 9999999999)

	def Get_param(self):
		url='https://u.y.qq.com/cgi-bin/musicu.fcg?data={"req_0":{"module":"vkey.GetVkeyServer","method":"CgiGetVkey","param":{"guid":"%s","songmid":["%s"],"songtype":[0],"uin":"0","loginflag":1,"platform":"20"}}}' % (self.guid,self.songmid)
		try:
			response=json.loads(requests.get(url).content.decode())
			self.vkey=response['req_0']['data']['testfile2g'].split('=')[2].split('&')[0]
			self.vkey2=response['req_0']['data']['midurlinfo'][0]['vkey']
		except:
			print('Error: Failed to request vkey')
			self.status=-3

	def Check_Quality(self,quality):
		if quality not in (0,1,2,3,4):
			print('Error: Illegal quality ID')
			self.status=-4
		else:
			self.quality_id=quality
			self.Set_Quality()

	def Set_Quality(self):
		self.quality=('C400','M500','M800','A000','F000')[self.quality_id]
		self.extension=('m4a','mp3','mp3','ape','flac')[self.quality_id]

	def Download_Song(self):
		url='http://streamoc.music.tc.qq.com/%s%s.%s?guid=%s&vkey=%s&uin=0&fromtag=58' % (self.quality,self.songmid,self.extension,self.guid,self.vkey)
		try:
			print('Downloading...')
			self.fullfilename=self.filename+'.'+self.extension
			if self.fullfilename in os.listdir(os.getcwd()+'\\music'):
				print(self.fullfilename+' already exists')
			else:
				print(self.fullfilename)
				data=requests.get(url).content
				with open('music/%s' % self.fullfilename, 'wb') as file:
					file.write(data)
				print('Done')
		except:
			print('Error: Failed to download the file')
			self.status=-5

	def Download_Lyric(self):
		try:
			print('Downloading...')
			header = {'user-agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/59.0.3071.115 Safari/537.36','referer':'https://y.qq.com/portal/playlist.html'}
			url='https://c.y.qq.com/lyric/fcgi-bin/fcg_query_lyric_new.fcg?songmid=%s&format=json' % self.songmid
			response=json.loads(requests.get(url,headers=header).content.decode())
			self.lyricfilename=self.filename+'.lrc'
			if self.lyricfilename in os.listdir(os.getcwd()+'\\lyric'):
				print(self.lyricfilename+' already exists')
			else:
				print(self.lyricfilename)
				data=base64.b64decode(response['lyric'].encode())
				with open('lyric/%s' % self.lyricfilename, 'wb') as file:
					file.write(data)
				print('Done')
		except:
			print('Error: Failed to download the file')
			self.status=-6

	def send_to_MagicMirror(self,type):
		try:
			if (type == 'song'):
				cmd='scp "' +os.getcwd()+'\\music\\'+self.fullfilename+'" pi@192.168.0.1:/home/pi/Documents/MagicMirror/music'
			elif (type == 'lyric'):
				cmd='scp "' +os.getcwd()+'\\lyric\\'+self.lyricfilename+'" pi@192.168.0.1:/home/pi/Documents/MagicMirror/lyric'
			os.system(cmd)
		except:
			print('Error: Failed to connect to the MagicMirror')
			self.status=-7


if __name__ == '__main__':
	while True:
		url=input('Input the URL:')
		Music=QQMusic(url)
		if Music.status == 0:
			while True:
				print(Music.filename)
				quality=int(input('Choose the quality:\n\t0:\tm4a (96Kbps)\n\t1:\tmp3 (128Kbps)\n\t2:\tmp3 (320Kbps)\n\t3:\tape\n\t4:\tflac\n'))
				Music.Check_Quality(quality);
				if Music.status == 0:
					Music.Download_Song()
					if Music.status == 0:
						while True:
							choice=input('Send the music file to the MagicMirror?(y/n)')
							if choice == 'y':
								Music.send_to_MagicMirror('song')
								break
							elif choice == 'n':
								break
							else:
								print('Error: Input not in (y/n)')
						while True:
							choice=input('Download the lyric?(y/n)')
							if choice == 'y':
								Music.Download_Lyric()
								break
							elif choice == 'n':
								break
							else:
								print('Error: Input not in (y/n)')
						if Music.status == 0:
							while True:
								choice=input('Send the lyric file to the MagicMirror?(y/n)')
								if choice == 'y':
									Music.send_to_MagicMirror('lyric')
									break
								elif choice == 'n':
									break
								else:
									print('Error: Input not in (y/n)')
						break
				Music.status=0
		print('Press Ctrl+C to exit.')