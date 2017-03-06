from flask import Flask, redirect, render_template, request, session, abort
import json, requests 
import mysql.connector
from config import dbconnect
import os

app = Flask(__name__)

db_config=dbconnect().db_config()

@app.route("/")
def index():
    return render_template('index.html')

@app.route("/callback")
def abc():
    return render_template('call.html')    

@app.route("/login")
def login():
	token = request.cookies.get('odauth')
	db = mysql.connector.connect(host=db_config['host'],database=db_config['database'],user=db_config['user'],password=db_config['password'])
	cursor = db.cursor()
	cursor.execute("SELECT driveid FROM user")
	data = cursor.fetchall()


	r=requests.get("https://api.onedrive.com/v1.0/drive",
		headers = {'Content-Type': 'application/json'},
		params={'access_token':token})
	
	rstr= str(r.text)
	rjson=json.loads(rstr)
	userdata = {
	    'driveid': rjson['id'],
  		'drivetype': rjson['driveType'],
  		'name': rjson['owner']['user']['displayName']  		
	}
	
	p=0
	for id in data:
		if id[0]==userdata['driveid']:
			p=1


	if p==0:		
		db = mysql.connector.connect(host=db_config['host'],database=db_config['database'],user=db_config['user'],password=db_config['password'])
		cursor = db.cursor()
		add_user = ("INSERT INTO user (driveid,drivetype,name) VALUES (%(driveid)s, %(drivetype)s, %(name)s)")
		cursor.execute(add_user, userdata)

		r=requests.get("https://api.onedrive.com/v1.0/drive/root:/share:/children",
			headers = {'Content-Type': 'application/json'},
			params={'access_token':token})
		rstr= str(r.text)
		rjson=json.loads(rstr)
		length=len(rjson['value'])
		for i in range(0,length):
			re=requests.get("https://api.onedrive.com/v1.0/drive/items/"+rjson['value'][i]['id']+"/thumbnails?select=c300x250_Crop",
			headers = {'Content-Type': 'application/json'},	
			params={'access_token':token})
			restr= str(re.text)
			rejson=json.loads(restr)
			
			p=rjson['value'][i]['name'].split('.', 1)[0]
			args = {}
			args['readkey'] = 'PCF36AxWZTnD'
			args['text'] = p
			args['output'] = 'json'
			args['version'] = '1.01'
			rp = requests.get(
					"http://uclassify.com/browse/uClassify/Topics/ClassifyText?%s",
					data = args)
			rpstr= str(rp.text)
			rpjson = json.loads(rpstr)
			list=['Arts','Business','Computers','Games','Health','Home','Recreation','Science','Society','Sports']
			x=''
			y=0
			for j in list:
				if(rpjson['cls1'][j]>y):
					y=rpjson['cls1'][j]
					x=j
			filedata={
				'driveid': rjson['value'][i]['createdBy']['user']['id'],
				'id':rjson['value'][i]['id'],
				'filename':rjson['value'][i]['name'],
				'size': 'SIZE:' + str(rjson['value'][i]['size']/1024)+'MB',
				'downloadurl':rjson['value'][i]['@content.downloadUrl'],
				'thumbnail':rejson['value'][0]['c300x250_Crop']['url'],
				'type':x
			}
			add_files = ("INSERT INTO files (driveid,id,filename,size,downloadurl,thumbnail,type) VALUES (%(driveid)s, %(id)s, %(filename)s, %(size)s,%(downloadurl)s,%(thumbnail)s,%(type)s)")
			cursor.execute(add_files, filedata)
			db.commit()
		
		cursor.execute("SELECT * FROM files")
		data = cursor.fetchall()
		
		return render_template('home.html',data=data)
	else:
		cursor.execute("SELECT * FROM files")
		data = cursor.fetchall()
		return render_template('home.html',data=data)



def User_Favourite(id):
	db = mysql.connector.connect(host=db_config['host'],database=db_config['database'],user=db_config['user'],password=db_config['password'])
	cursor = db.cursor()
	cursor.execute("SELECT driveid,type FROM files")

	data = cursor.fetchall()
	
	list=['Arts','Business','Computers','Games','Health','Home','Recreation','Science','Society','Sports']
	user_favourite_list={}
	user_favourite_tag=""

	for j in list:
		user_favourite_list[j]=0

	for i in range(len(data)):
		if data[i][0]==id:
			for j in list:
				if data[i][1]==j:
					user_favourite_list[j]=user_favourite_list[j]+1

	x=""
	y=0
	for key, value in user_favourite_list.iteritems():			
		if value>y :
			y=value
			x=key
	print(x+" "+str(y))
	return x



if __name__ == "__main__":
    app.run(debug=True)
