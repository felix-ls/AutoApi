# -*- coding:utf-8 -*-
#@TIME : 2020/5/14 19:59
#@Author : Maple
#@File :index.py
#@Software : GitHub

import time
from urllib import parse
import re
import json
import base64
import requests
import smtplib
from email.mime.text import MIMEText
import datetime
'''============填入手机号与密码==========='''
user_info={
	'username':'17680519140',
	'password':'1956153654LZK',
	'email':'1956153654@qq.com',
	'address':'自己的地址'  #Server酱的SCKEY   可以不用填写这个
}
'''================End==================='''

'''==========第三方SMTP服务(勿修改)========='''
mail_host = "smtp.qq.com"
mail_user = "453797581@qq.com"  #此处为发件邮箱，用来发送签到完毕的信息
mail_pass = "psuwcppvubgxbgfb"   #此处为发件邮箱的密钥，请勿更改
sender = '453797581@qq.com' #此处为发件邮箱
'''================End==================='''
#login
Login_API="http://passport2.chaoxing.com/fanyalogin"
#course
Course_API="http://mooc1-api.chaoxing.com/mycourse/backclazzdata?view=json&rss=1"
#course activate
Acticate_API="https://mobilelearn.chaoxing.com/ppt/activeAPI/taskactivelist?courseId="
#sign-in
#Sign_API = "https://mobilelearn.chaoxing.com/pptSign/stuSignajax?activeId={}&uid={}&clientip=127.0.0.1&latitude=-1&longitude=-1&appType=15&fid={}"
Sign_API = "https://mobilelearn.chaoxing.com/pptSign/stuSignajax"
#upload picture
UploadPic_API = "http://pan-yz.chaoxing.com/upload?_token=410f360978c4d7ee1398035f530c4155"
'''================End==================='''


cs = 0
active = True
while cs < 120 and active:
	cs += 1
	print("第%s次检测"%cs)
	def sendmail(classname, mail, signtype):
		receivers = []  # 接收人邮箱
		content = "课程为："+classname+"\n签到名称为："+signtype+"\n签到时间为："+str(datetime.datetime.now())
		title = '超星自动签到系统'  # 邮件主题
		receivers.append(mail)
		message = MIMEText(content, 'plain', 'utf-8')  # 内容, 格式, 编码
		message['From'] = "{}".format(sender)
		message['To'] = ",".join(receivers)
		message['Subject'] = title

		try:
			smtpObj = smtplib.SMTP_SSL(mail_host, 465)  # 启用SSL发信, 端口一般是465
			smtpObj.login(mail_user, mail_pass)  # 登录验证
			smtpObj.sendmail(sender, receivers, message.as_string())  # 发送
			print('================================')
			print('||                            ||')
			print("||       Have send mail       ||")
			print('||                            ||')
			print('================================')
		except smtplib.SMTPException as e:
			print(e,"邮件发送失败")
			pass


	class sign():
		def __init__(self,user_info):
			'''initial the data of sign-in'''
			self.data = {'fid': -1, 'uname': user_info['username'], 'password': base64.b64encode(user_info['password'].encode()),
					'refer': 'http://fxlogin.chaoxing.com/findlogin.jsp?backurl=http://www.chaoxing.com/channelcookie','t': 'true'}
			self.header = {
				'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/77.0.3835.0 Safari/537.36',
				'Referer': 'https://passport2.chaoxing.com/login?fid=&newversion=true&refer=http://fxlogin.chaoxing.com/findlogin.jsp?backurl=http://www.chaoxing.com/channelcookie'}

			self.login()

		def login(self):
			self.session = requests.Session()
			self.r = self.session.post(Login_API, headers=self.header, data=self.data)
			if "HTTP Status 403" in self.r.text:
				print("该ip无法访问超星")
				exit(0)
			'''用作获取课程活动的'''
			self.uid = self.r.cookies.get_dict()['UID']
			self.fid = self.r.cookies.get_dict()['fid']

			#self.objectid=self.get_objectid(user_info['image'])

			Login_Status = json.loads(self.r.text)['status']
			if Login_Status == 'False':
				print('登录失败')
			else:
				print('登录成功，开始签到')
			#get user real name
			re_rule_name = r'<p class="personalName" title="(.*)" style='
			self.r = self.session.get("http://i.mooc.chaoxing.com/space/index")
			self.u_name = parse.quote(re.search(re_rule_name, self.r.text).group(1))
			self.start_sign()

		#get all course info
		def start_sign(self):
			try:
				'''api'''
				self.r = self.session.get(Course_API,headers=self.header)
				if "HTTP Status 403" in self.r.text:
					print("该ip无法访问超星")
					exit(0)
				else:
					try:
						self.course_data=[]
						self.course_info = json.loads(self.r.text)
						for temp in self.course_info['channelList']:
							coursename=temp['content']['course']['data'][0]['name']
							courseid=temp['content']['course']['data'][0]['id']
							classid=temp['content']['id']

							self.course_data.append((courseid,classid,coursename))

					except Exception as e:
						print("Json load course data failed")
						raise Exception
					if (self.course_info['result'] != 1):
						print("课程列表获取失败")
						raise Exception
					else:
						pass
			except:
				try:
					'''爬虫'''
					self.r = self.session.get(
						'http://mooc1-2.chaoxing.com/visit/interaction',
						headers=self.header)
					re_rule = r'<input .* name="courseId" value="(.*)" />[\s].*<input .* value="(.*)" />[\d\D]*?target="_blank" title="(.*)">*'
					self.course_data = re.findall(re_rule, self.r.text)
				except:
					pass
			for ctemp in self.course_data:
				task = self.get_activeid(ctemp[0],ctemp[1],ctemp[2])
				if task!=None:
					for task_ in task:
						params = {
							'name': '',
							'activeId': task_['activeid'],
							'address': user_info['address'],
							'objectId':'',
							'uid': self.uid,
							'clientip': '0.0.0.0',
							'latitude': '-2',
							'longitude': '-1',
							'fid': self.fid,
							'appType': '15',
							'ifTiJiao': '1'
						}
						sign_res = self.session.get(Sign_API,params=params)
						if sign_res.text=="success":
							print(task_['classname'],task_['sign_type'],"完成签到")
							sendmail(task_['classname'],user_info['email'],task_['sign_type'])
							active = False
                                                        


		def get_activeid(self,courseid,classid, classname):
			"""依旧两种方法"""
			"""访问任务面板获取课程的活动id"""
			re_rule = r'\((.*),2,null\)">[\d\D]*?qd qdhover[\d\D]*?shape="rect">(.*)</a>'

			r = self.session.get(
				'http://mobilelearn.chaoxing.com/widget/pcpick/stu/index?courseId={}&jclassId={}'.format(
					courseid, classid), headers=self.header, verify=False)
			#通常一门课程只会同时存在一个签到  但是不排除出现多个签到任务的可能   所以还需要处理多个签到任务的
			res = re.findall(re_rule, r.text)
			if res != []:  # 满足签到条件
				return_data = []
				for i in range(len(res)):
					return_data.append({
						'classid': classid,
						'courseid': courseid,
						'activeid': res[i][0],
						'classname': classname,
						'sign_type': res[i][1]
					})

				return return_data
			else:
				print(classname,"没有签到任务")


		#Upload picture for sign-in and get the picture id——objectid
		def get_objectid(self,filename):
			files = {"file": (user_info['image'], open("upload\\"+filename, "rb"))}
			s = self.session.post(UploadPic_API, headers=self.header, files=files, data={'puid': 56965724})
			objectId = json.loads(s.text)['objectId']
			return objectId



	me=sign(user_info)


	def main_handler(event,context):

	    me=sign(user_info)
	
	time.sleep(30)  #延迟30秒
	
