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
    price = ndb.FloatProperty(indexed=False)
    date = ndb.DateTimeProperty(auto_now_add=True)

class Cart(ndb.Model):
    """Sub model to represent cart contents"""
    #id = ndb.StringProperty(indexed=True)
    title = ndb.StringProperty(indexed=False)
    artist_name = ndb.StringProperty(indexed=False)
    album_name = ndb.StringProperty(indexed=False)
    price = ndb.FloatProperty(indexed=False)
    quantity = ndb.IntegerProperty(indexed=False)
    date = ndb.DateTimeProperty(auto_now_add=True)
	
class PurchaseHistory(ndb.Model):
    """Sub model to represent cart contents"""
    #id = ndb.StringProperty(indexed=True)
    #artist_name = ndb.StringProperty()
    title = ndb.StringProperty(indexed=False)
    artist_name = ndb.StringProperty(indexed=False)
    album_name = ndb.StringProperty(indexed=False)
    price = ndb.FloatProperty(indexed=False)
    quantity = ndb.IntegerProperty(indexed=False)
    date = ndb.DateTimeProperty(auto_now_add=True)
	
# [START greeting]
class Author(ndb.Model):
    """Sub model for representing an author."""
    identity = ndb.StringProperty(indexed=False)
    email = ndb.StringProperty(indexed=False)

'''
class Greeting(ndb.Model):
    """A main model for representing an individual Guestbook entry."""
    author = ndb.StructuredProperty(Author)
    content = ndb.StringProperty(indexed=False)
    date = ndb.DateTimeProperty(auto_now_add=True)'''
# [END greeting]


# [START main_page]
class MainPage(webapp2.RequestHandler):

    def get(self):
        genre_name = self.request.get('genre_name', DEFAULT_GENRE)
       
        cookie_id = self.request.cookies.get('key')
        if cookie_id == None:
            #cookie_id = str(uuid.uuid4())
            cookie_id = str(random.randint(1000000000, 9999999999))

        user = users.get_current_user()
        if user:
            url = users.create_logout_url('/')
            nickname = user.nickname()
            url_linktext = 'Logout'
        else:
            url = users.create_login_url('/')
            nickname = ''
            url_linktext = 'Login'
         
        template_values = {
            'user': nickname,
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
        
        is_not_float = False
        try:
            song.price = float(self.request.get('price'))
        except:
            is_not_float = True       
         
        if song.artist_name == '' or song.title == '' or song.price == '' or is_not_float:
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
            ancestor=genre_key(genre_name.lower()))
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
        genre_query = Song.query(ancestor=genre_key(genre_name.lower()))
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
        logging.info("IN GET ADDTOCART")
        user = users.get_current_user()
        user_name = 'false'
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
                    if cart.title == song.title and cart.artist_name == song.artist_name and cart.album_name == song.album_name and float(cart.price) == float(song.price):
                        cart.quantity += 1
                        logging.info("Adding to quantity IN GET ADDTOCART")
                    else:
                        logging.info("Adding first song of its kind IN GET ADDTOCART")
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
            total += float(item.price) * float(item.quantity)   
		
        template_values = {
            #'artist_name':cart.artist_name,
            #'title': cart.title,
            #'price': cart.price,
            'cart': cart_bucket,
            'user_name': user_name,
            'total': total,
        }
        
        template = JINJA_ENVIRONMENT.get_template('cart.html')
        self.response.write(template.render(template_values))

    def post(self):
        logging.info("IN POST ADDTOCART")
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
                    if cart.title == song.title and cart.artist_name == song.artist_name and cart.album_name == song.album_name and float(cart.price) == float(song.price):
                        cart.quantity += 1
                        logging.info("Adding to quantity IN POST ADDTOCART")
                    else:
                        logging.info("Adding first song of its kind IN POST ADDTOCART")
                        cart.title = song.title
                        cart.artist_name = song.artist_name
                        cart.album_name = song.album_name
                        cart.price = song.price
                        cart.quantity = 1
                    cart.put()
                    song.key.delete()  
				
        song_add = self.request.get('song')
        is_incr = 0
        #cart_query = Cart.query(ancestor=cart_key(user))
        
        if song_add:            		
            tokens = song_add.split('&&')
            song_title = tokens[0]
            song_artist = tokens[1]
            song_album = tokens[2]
            song_price = tokens[3]
            logging.info("Add song button pressed")
            cart = Cart.query(ancestor=cart_key(user))
            for item in cart:
                logging.info("**********************************************************")
                if item.title == song_title and item.artist_name == song_artist and item.album_name == song_album and float(item.price) == float(song_price):
                    item.quantity += 1
                    is_incr = 1
                    logging.info("Adding to quantity IN POST ADDTOCART 2")
                    item.put()
                    break
                '''else:
                    logging.info("Adding first song of its kind IN POST ADDTOCART 2")
                    cart.title = song_title  
                    cart.artist_name = song_artist
                    cart.album_name = song_album
                    cart.price = int(song_price)
                    cart.quantity = 1
                    cart.put()'''
            #logging.info(cart.title)
            #logging.info(cart.artist_name)
            #logging.info(cart.album_name)
            #logging.info(cart.price)
            
            if is_incr == 0:
                cart = Cart(parent=cart_key(user))
                logging.info("Adding first song of its kind IN POST ADDTOCART 2")
                cart.title = song_title  
                cart.artist_name = song_artist
                cart.album_name = song_album
                cart.price = float(song_price)
                cart.quantity = 1
                cart.put()
        
        self.redirect('/addtocart?' + urllib.urlencode({'user': user}))


class Checkout(webapp2.RequestHandler):
    def post(self):
        btn_remove = self.request.get("remove")
        btn_checkout = self.request.get("checkout")
		
        if btn_checkout:
            logging.info("*********Checking out**********")
            user = users.get_current_user()
            if not user:
                url = users.create_login_url('/addtocart')
                self.redirect(url)              
            else:
                user = user.email()       
                cart_query = Cart.query(ancestor=cart_key(user))
                cart_bucket = cart_query.fetch(100)
                purchase_history = PurchaseHistory(parent=cart_key(user))
                for song in cart_bucket:
                    purchase_history = PurchaseHistory(parent=cart_key(user))
                    logging.info("song.title " + song.title+".")
                    logging.info("song.artist_name " + song.artist_name+".")
                    logging.info("song.album_name " + song.album_name+".")
                    logging.info("song.price ")
                    logging.info(song.price)
                    logging.info("song.quantity ")
                    logging.info(song.quantity)
                    purchase_history.artist_name = song.artist_name
                    purchase_history.album_name = song.album_name
                    purchase_history.price = song.price
                    purchase_history.title = song.title
                    purchase_history.quantity = song.quantity
                    purchase_history.put()
                    song.key.delete()
                query_param1 = {'checkout': 'true'}
                self.redirect('/addtocart?' + urllib.urlencode({'user': user}) + '&' + urllib.urlencode(query_param1))
                #self.redirect('/purchase-done' + urllib.urlencode({'user': user}))
        
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
                if item.title == song_title and item.artist_name == song_artist and item.album_name == song_album and float(item.price) == float(song_price):  # delete the book only once
                    logging.info("######Removing the following entries from the cart#######")
                    logging.info(item.title)
                    logging.info(item.artist_name)
                    logging.info(item.album_name)
                    logging.info(item.price)
                    item.key.delete()
                    break
            self.redirect('/addtocart?' + urllib.urlencode({'user': user}))
        
# [START app]

class Purchase(webapp2.RequestHandler):
    def get(self):
        user = users.get_current_user()
        if not user:
            user = self.request.cookies.get('key')
        else:
            user = user.email()
        genre_name = self.request.get('genre_name', DEFAULT_GENRE)
        purchase_history_query = PurchaseHistory.query(ancestor=cart_key(user))
        purchase_history = purchase_history_query.fetch(100)
        
        template_values = {
            'user' : user,
            'purchase_history': purchase_history,
        }

        template = JINJA_ENVIRONMENT.get_template('purchase.html')
        self.response.write(template.render(template_values))


app = webapp2.WSGIApplication([
    ('/', MainPage),
    ('/search', SearchPage),
    ('/enter', EnterPage),
    ('/playlist', Playlist),
    ('/display', DisplayPage),
    ('/addtocart', AddToCart),
    ('/cartcheckout', Checkout),
    ('/purchase', Purchase),
    #('/cart', DisplayCart)
], debug=True)
# [END app]
