import os
import re
import cgi
import StringIO
import wsgiref.handlers
import urllib
import urlparse
from google.appengine.ext.webapp import template
from google.appengine.api import urlfetch 
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.ext import db
from google.appengine.api import images
from google.appengine.ext.db import GqlQuery

__author__ = 'Roberto Breve' 

class Main(webapp.RequestHandler):
	def get(self):
		path = os.path.join(os.path.dirname(__file__), 'templates/main.html')
		self.response.out.write(template.render(path, None))



class List(webapp.RequestHandler):
	def get(self):
		images=Image.all()
		path = os.path.join(os.path.dirname(__file__), 'all.html')
		template_values={
		'images': images
		}
		self.response.out.write(template.render(path, template_values))

class TinyImage(webapp.RequestHandler):
	def get(self, name):
		images = GqlQuery("SELECT * FROM Image WHERE name = :1", name)
		image = images.get()
		if image:
			mime="jpeg"
			self.response.headers['Content-Type'] = "image/%s" % mime
			self.response.out.write(image.thumb)
			self.response.out.write(image.content)
		else:
			self.error(404)
			self.redirect("/static/nopic.png")
			

class Thumbnail(webapp.RequestHandler):
	def get(self):
		image_url = self.request.get('image_url')
		width = int(self.request.get('width'))
		name=self.request.get('name')
		
		
		savedimages = GqlQuery("SELECT * FROM Image WHERE url = :1 and width = :2", image_url, width)
		image = savedimages.get()
		if image:
			image_url=image.url
			tinyname=image.name
		else:
			import random
			import string
			image_re = re.compile(r'http://([\w\d\_\=\?\-\.\/\&\;\%]+)')
			if image_re.search(image_url):
				domain=image_re.search(image_url).group(0)
				ext = domain[-3:].lower()
				if ext == "jpg" or ext == "png" or ext == "gif":
					mime=ext
					if ext=="jpg":
						mime="jpeg"
					parts=domain.split("/")
					filename=parts[len(parts)-1]
					#get image 
					image_content = urlfetch.fetch(image_url).content
					thumb = images.resize(image_content, width, width)
					tinyname= ''.join(random.sample(string.letters*2, 10)) 

					if thumb:
						image=Image()
						image.url=image_url
						image.width=width
						image.name=tinyname
						image.content = db.Blob(image_content)
						image.thumb = db.Blob(thumb)
						image.put()
						
		template_values={
			'image_url': image_url,
			'width': width,
			'name': tinyname
		}
		path = os.path.join(os.path.dirname(__file__), 'templates/thumbnails.html')
		self.response.out.write(template.render(path, template_values))
		

		
class Thumbler(webapp.RequestHandler):
	def post(self):
		import random
		import string	
		
		image_content = self.request.get("image")
		width=self.request.get('width')
		if width:
			width = int(self.request.get('width'))
		else:
			width=60
	
		thumb = images.resize(image_content, width, width)
		
		tinyname= ''.join(random.sample(string.letters*2, 10))+".jpg"
		#tinyname="abc"
		image=Image()
		image.ext="jpg"
		image.url="http://thumblerific.appspot.com/"+tinyname
		image.width=width
		image.name=tinyname
		image.content = db.Blob(image_content)
		image.thumb = db.Blob(thumb)
		image.put()
		self.redirect("/thumbnail?image_url=%s&width=%s" % (image.url, width))
		
	def get(self):
		import random
		import string
		
		image_url = self.request.get('image_url')

		width=self.request.get('width')
		if width:
			width = int(self.request.get('width'))
		else:
			width=60
	
		tinyname= ''.join(random.sample(string.letters*2, 10))
		
		if not width or (width < 10 or width > 1200):
			width = 90
		
		savedimages = GqlQuery("SELECT * FROM Image WHERE url = :1 and width = :2", image_url, width)
		
		image = savedimages.get()
		
		if image:
			ext=image.name[-3:]
			mime=ext
			if ext=="jpg":
				mime="jpeg"
			self.response.headers['Content-Type'] = "image/%s" % mime
			self.response.out.write(image.thumb)
			self.response.out.write(image.content)
			return
		
		image_re = re.compile(r'http://([\w\d\_\=\?\-\.\/\&\;\%]+)')
		
		if image_re.search(image_url):
			domain=image_re.search(image_url).group(0)
			ext = domain[-3:].lower()
			
			if ext == "jpg" or ext == "png" or ext == "gif":
				
				mime=ext
				if ext=="jpg":
					mime="jpeg"
				
				parts=domain.split("/")
				filename=parts[len(parts)-1]
	
				#get image 
				image_content = urlfetch.fetch(image_url).content
				thumb = images.resize(image_content, width, width)
	
				if thumb:
					image=Image()
					image.url=image_url
					image.width=width
					image.name=tinyname
					image.content = db.Blob(image_content)
					image.thumb = db.Blob(thumb)
					image.put()

					self.response.headers['Content-Type'] = "image/%s" % mime
					self.response.out.write(thumb)
				else:
					self.error(404)
		
		
		# path = os.path.join(os.path.dirname(__file__), 'index.html')
		# template_values={
		# 'filename': filename
		# }
		# self.response.out.write(template.render(path, template_values))
 
			
		



class Image(db.Model):
	name = db.StringProperty()
	width = db.IntegerProperty()
	url = db.LinkProperty()
	content = db.BlobProperty()
	thumb = db.BlobProperty()
	date = db.DateTimeProperty(auto_now_add=True)

application = webapp.WSGIApplication(
							[(r'/i/(\w+)', TinyImage),
							('/', Main), 
							('/t', Thumbler),
							('/thumbnail', Thumbnail),
							('/list', List)
							],
							debug=True)

def main():
	run_wsgi_app(application)
		
if __name__ == "__main__":
	main()