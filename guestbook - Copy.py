#!/usr/bin/env python

# Copyright 2016 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# [START imports]
import os
import urllib
import logging
import numbers
import random
import uuid

from google.appengine.api import users
from google.appengine.ext import ndb

import jinja2
import webapp2

JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
    extensions=['jinja2.ext.autoescape'],
    autoescape=True)
# [END imports]

DEFAULT_GENRE = 'Classical'
DEFAULT_ERROR = 'false'
DEFAULT_FLAG = ''

# We set a parent key on the 'Greetings' to ensure that they are all
# in the same entity group. Queries across the single entity group
# will be consistent. However, the write rate should be limited to
# ~1/second.

	
def genre_key(genre_name=DEFAULT_GENRE):	
	return ndb.Key('Genre', genre_name.lower())
	
def cart_key(user):	
	return ndb.Key('User', user)

class Song(ndb.Model):
    """Sub model to represent a song"""
    #id = ndb.StringProperty(indexed=True)
    artist_name = ndb.StringProperty(indexed=True)
    title = ndb.StringProperty(indexed=False)
    album_name = ndb.StringProperty(indexed=False)
    price = ndb.IntegerProperty(indexed=False)
    date = ndb.DateTimeProperty(auto_now_add=True)

class Cart(ndb.Model):
    """Sub model to represent cart contents"""
    #id = ndb.StringProperty(indexed=True)
    #artist_name = ndb.StringProperty()
    title = ndb.StringProperty()
    artist_name = ndb.StringProperty()
    album_name = ndb.StringProperty(indexed=False)
    price = ndb.IntegerProperty()
    quantity = ndb.IntegerProperty()
    #date = ndb.DateTimeProperty()
	
# [START greeting]
class Author(ndb.Model):
    """Sub model for representing an author."""
    identity = ndb.StringProperty(indexed=False)
    email = ndb.StringProperty(indexed=False)


class Greeting(ndb.Model):
    """A main model for representing an individual Guestbook entry."""
    author = ndb.StructuredProperty(Author)
    content = ndb.StringProperty(indexed=False)
    date = ndb.DateTimeProperty(auto_now_add=True)
# [END greeting]


# [START main_page]
class MainPage(webapp2.RequestHandler):

    def get(self):
        genre_name = self.request.get('genre_name', DEFAULT_GENRE)
       
        cookie_id = self.request.cookies.get('key')
        if cookie_id == None:
            cookie_id = str(uuid.uuid4())

        user = users.get_current_user()
        if user:
            url = users.create_logout_url('/')
            url_linktext = 'Logout'
        else:
            url = users.create_login_url('/')
            url_linktext = 'Login'
         
        template_values = {
            'user': user,
            'genre_name': urllib.quote_plus(genre_name),
            'url': url,
            'url_linktext': url_linktext,			
        }

        template = JINJA_ENVIRONMENT.get_template('index.html')
        self.response.write(template.render(template_values))
        self.response.headers.add_header('Set-Cookie', 'key=%s' % str(cookie_id))  
# [END main_page]

# [START enter_page]
class EnterPage(webapp2.RequestHandler):

    def get(self):
        genre_name = self.request.get('genre_name', DEFAULT_GENRE)
        error = self.request.get('error', DEFAULT_ERROR)
		
        template_values = {
            'genre_name': urllib.quote_plus(genre_name),
            'error': urllib.quote_plus(error),
            
        }

        template = JINJA_ENVIRONMENT.get_template('enter.html')
        self.response.write(template.render(template_values))
# [END enter_page]



# [START Playlist]
class Playlist(webapp2.RequestHandler):

    def post(self):
        # We set the same parent key on the 'Greeting' to ensure each
        # Greeting is in the same entity group. Queries across the
        # single entity group will be consistent. However, the write
        # rate to a single entity group should be limited to
        # ~1/second.
        genre_name = self.request.get('genre_name',
                                          DEFAULT_GENRE)
        song = Song(parent=genre_key(genre_name.lower()))


        song.artist_name = self.request.get('artist_name')
        song.album_name = self.request.get('album_name')
        song.title = self.request.get('title')
		
        query_param1 = {'genre_name': genre_name}
        
        is_not_int = False
        try:
            song.price = int(self.request.get('price'))
        except:
            is_not_int = True       
         
        if song.artist_name == '' or song.title == '' or song.price == '' or is_not_int:
            query_param2 = {'error': 'true'}
            self.redirect('/enter?' + urllib.urlencode(query_param1) + '&' + urllib.urlencode(query_param2))
        else:
            song.put() # add song to the repo
            self.redirect('/enter?' + urllib.urlencode(query_param1))
# [END Playlist]

# [START search_page]
class SearchPage(webapp2.RequestHandler):

    def get(self):
        genre_name = self.request.get('genre_name', DEFAULT_GENRE)
        #flag = self.request.get('flag', DEFAULT_FLAG)
											
        artist_name = self.request.get('artist_name', '\0')
        #artist_name = artist_name.lower() #make search case insensitive
        song_query = Song.query(
            ancestor=genre_key(genre_name.lower())).order(-Song.date)
        songs = song_query.fetch(100)
	    
        template_values = {
			#'flag' : flag,
            'songs' : songs,
            'genre_name': urllib.quote_plus(genre_name),
			'artist_name' : artist_name,  
            		
        }
		
        template = JINJA_ENVIRONMENT.get_template('search.html')
        self.response.write(template.render(template_values))
		
    def post(self):
	
        genre_name = self.request.get('genre_name', DEFAULT_GENRE)
        artist_name = self.request.get('artist_name', '\0')
        query_param1 = {'genre_name' : genre_name, 'artist_name' : artist_name}
        self.redirect('/search?' + urllib.urlencode(query_param1))
# [END search_page]

'''class SearchAction(webapp2.RequestHandler):
    def post(self):
        genre_name = self.request.get('genre_name', DEFAULT_GENRE)
        artist_name = self.request.get('artist_name')
        query_param1 = {'genre_name' : genre_name}
        query_param2 = {'artist_name' : artist_name}
        self.redirect('/search?')'''
		
class DisplayPage(webapp2.RequestHandler):
    def get(self):
        genre_name = self.request.get('genre_name', DEFAULT_GENRE)
        genre_query = Song.query(ancestor=genre_key(genre_name.lower())).order(-Song.date)
        songs = genre_query.fetch(100)
        
        template_values = {
            'songs': songs,
            'genre_name': genre_name,
        }

        template = JINJA_ENVIRONMENT.get_template('display.html')
        self.response.write(template.render(template_values))
# [START app]

class AddToCart(webapp2.RequestHandler):
    def get(self):
        user = users.get_current_user()
        if not user:
            user = self.request.cookies.get('key')
        else:  							# bring items from other carts from different unclosed sessions
            user = user.email()  
            user_name = user
            cookie_id = self.request.cookies.get('key')
            cart_temp = Cart.query(ancestor=cart_key(cookie_id))
            if cart_temp:  # merge the temporary cart with cart
                for song in cart_temp:
                    cart = Cart(parent=cart_key(user))
                    if cart.title == song.title and cart.artist_name == song.artist_name and cart.album_name == song.album_name and int(cart.price) == int(song.price):
                        cart.quantity += 1
                    else:
                        cart.title = song.title
                        cart.artist_name = song.artist_name
                        cart.album_name = song.album_name
                        cart.price = song.price
                        cart.quantity = 1
                    cart.put()
                    song.key.delete()  
			
        cart_query = Cart.query(ancestor=cart_key(user))
        cart_bucket = cart_query.fetch(100)
		
        total = 0
        
        for item in cart_bucket:
            #logging.info(item.title)
            #logging.info(item.artist_name)
            #logging.info(item.album_name)
            #logging.info(item.price)
            total += item.price   
		
        template_values = {
            #'artist_name':cart.artist_name,
            #'title': cart.title,
            #'price': cart.price,
            'cart': cart_bucket,
            'user': user,
            'total': total,
        }
        
        template = JINJA_ENVIRONMENT.get_template('cart.html')
        self.response.write(template.render(template_values))

    def post(self):
        user = users.get_current_user()
        if not user:
            user = self.request.cookies.get('key')
        else:  							# bring items from other carts from different unclosed sessions
            user = user.email()  
            user_name = user
            cookie_id = self.request.cookies.get('key')
            cart_temp = Cart.query(ancestor=cart_key(cookie_id))
            if cart_temp:  # merge the temporary cart with cart
                for song in cart_temp:
                    cart = Cart(parent=cart_key(user))
                    cart.title = song.title
                    cart.artist_name = song.artist_name
                    cart.album_name = song.album_name
                    cart.price = song.price
                    cart.put()
                    song.key.delete()  
				
        songs = self.request.get_all('song')
        for song in songs:
            cart = Cart(parent=cart_key(user))
            tokens = song.split('&&')
            song_title = tokens[0]
            song_artist = tokens[1]
            song_album = tokens[2]
            song_price = tokens[3]
            cart.title = song_title  
            cart.artist_name = song_artist
            cart.album_name = song_album
            cart.price = int(song_price)
            #logging.info(cart.title)
            #logging.info(cart.artist_name)
            #logging.info(cart.album_name)
            #logging.info(cart.price)
            cart.put()
			
        
        self.redirect('/addtocart?' + urllib.urlencode({'user': user}))



'''class DisplayCart(webapp2.RequestHandler):
    def get(self):
        user = users.get_current_user()
        if user:
            user = user.email()
        else:
            user = "Temporary"
	
        
        cart = Cart.query(ancestor=cart_key(user))
        logging.info("Inside Display Cart")
		
        total = 0
        songs = []
        for item in cart:  # count the total price
            song = Song.query(ancestor=genre_key(user))
            song.artist_name = item.artist_name
            song.title = item.title
            song.price = item.price
            total += item.price
            logging.info("Inside Display Loop")
            logging.info(song.title)
            logging.info(song.artist_name)
            logging.info(song.price)
            songs.extend(song)
		
        template_values = {
            #'artist_name':cart.artist_name,
            #'title': cart.title,
            #'price': cart.price,
            'cart': songs,
            'user': user,
            'total': total,
        }
        template = JINJA_ENVIRONMENT.get_template('cart.html')
        self.response.write(template.render(template_values))'''
        
class Checkout(webapp2.RequestHandler):
    def post(self):
        btn_remove = self.request.get("remove")
        btn_checkout = self.request.get("checkcout")
		
        if btn_checkout:
            user = users.get_current_user()
            if not user:
                url = users.create_login_url('/')
                self.redirect(url)              
            else:
                user = user.email()       
                cart_temp = Cart.query(ancestor=cart_key(user))
                for song in cart_temp:
                    song.key.delete()
                #self.redirect('/addtocart?' + urllib.urlencode({'user': user}))
                self.redirect('/addtocart?' + urllib.urlencode({'user': user}) + '&' + urllib.urlencode({'checkout': 'true'}))
        
        if btn_remove:
            user = users.get_current_user()
            if not user:
                user = self.request.cookies.get('key')
            else:
                user = user.email()
            
            tokens = btn_remove.split('&&')
            song_title = tokens[0]
            song_artist = tokens[1]
            song_album = tokens[2]
            song_price = tokens[3]
            
            cart = Cart.query(ancestor=cart_key(user))
            logging.warning("Button Pressed!!!!!")
            for item in cart: 
                '''logging.info("$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$")
                logging.info("item.title " + item.title+".")
                logging.info("song_title " + song_title+".")
                logging.info("item.artist_name " + item.artist_name+".")
                logging.info("song_artist " + song_artist+".")
                logging.info("item.album_name " + item.album_name+".")
                logging.info("song_album " + song_album+".")
                logging.info("item.price ")
                logging.info(item.price)
                logging.info("song_price ")
                logging.info(song_price)
                logging.info("$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$")'''
                if item.title == song_title and item.artist_name == song_artist and item.album_name == song_album and int(item.price) == int(song_price):  # delete the book only once
                    logging.info("######Removing the following entries from the cart#######")
                    logging.info(item.title)
                    logging.info(item.artist_name)
                    logging.info(item.album_name)
                    logging.info(item.price)
                    item.key.delete()
                    break
            self.redirect('/addtocart?' + urllib.urlencode({'user': user}))

# [START app]
app = webapp2.WSGIApplication([
    ('/', MainPage),
    ('/search', SearchPage),
    ('/enter', EnterPage),
    ('/playlist', Playlist),
    ('/display', DisplayPage),
    ('/addtocart', AddToCart),
    ('/cartcheckout', Checkout),
    #('/cart', DisplayCart)
], debug=True)
# [END app]
