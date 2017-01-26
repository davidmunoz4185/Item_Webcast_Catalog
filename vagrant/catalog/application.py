from flask import Flask
from flask import render_template
from flask import jsonify
from flask import request
from flask import redirect
from flask import url_for
from flask import flash
from flask import session as login_session
from sqlalchemy import create_engine
from sqlalchemy import asc
from sqlalchemy.orm import sessionmaker
from sqlalchemy import desc
from database_setup import Base
from database_setup import User
from database_setup import Category
from database_setup import Item
import random
import string
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
import json
from flask import make_response
import requests

app = Flask(__name__)

CLIENT_ID = json.loads(
    open('client_secrets.json', 'r').read())['web']['client_id']

APPLICATION_NAME = "CATALOG"

engine = create_engine('sqlite:///catalog.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()

def getCategories():
	categories = session.query(Category).all()
	return categories

@app.route('/login')
def showLogin():
    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for x in xrange(32))
    login_session['state'] = state
    # return "The current session state is %s" % login_session['state']
    return render_template('login.html', STATE=state)

@app.route('/gconnect', methods=['POST'])
def gconnect():
    # Validate state token
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    # Obtain authorization code
    code = request.data

    try:
        # Upgrade the authorization code into a credentials object
        oauth_flow = flow_from_clientsecrets('client_secrets.json', scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        response = make_response(
            json.dumps('Failed to upgrade the authorization code.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Check that the access token is valid.
    access_token = credentials.access_token
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'
           % access_token)
    h = httplib2.Http()
    result = json.loads(h.request(url, 'GET')[1])
    # If there was an error in the access token info, abort.
    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is used for the intended user.
    gplus_id = credentials.id_token['sub']
    if result['user_id'] != gplus_id:
        response = make_response(
            json.dumps("Token's user ID doesn't match given user ID."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is valid for this app.
    if result['issued_to'] != CLIENT_ID:
        response = make_response(
            json.dumps("Token's client ID does not match app's."), 401)
        print "Token's client ID does not match app's."
        response.headers['Content-Type'] = 'application/json'
        return response

    stored_access_token = login_session.get('access_token')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_access_token is not None and gplus_id == stored_gplus_id:
        response = make_response(json.dumps('Current user is already connected.'),
                                 200)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Store the access token in the session for later use.
    login_session['access_token'] = credentials.access_token
    login_session['gplus_id'] = gplus_id

    # Get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()

    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']

    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']
    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += ' " style = "width: 300px; height: 300px;border-radius: 150px;-webkit-border-radius: 150px;-moz-border-radius: 150px;"> '
    flash("WELCOME %s ..." % login_session['username'])
    print "done!"
    return output

@app.route('/gdisconnect')
def gdisconnect():
	access_token = login_session['access_token']
	print 'In gdisconnect access token is %s', access_token
	print 'User name is: ' 
	print login_session['username']
	if access_token is None:
		print 'Access Token is None'
		response = make_response(json.dumps('Current user not connected.'), 401)
		response.headers['Content-Type'] = 'application/json'
		return response
	url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % login_session['access_token']
	h = httplib2.Http()
	result = h.request(url, 'GET')[0]
	print 'result is '
	print result
	if result['status'] == '200':
		flash_message = "BYE BYE %s ..." % login_session["username"]
		del login_session['access_token'] 
		del login_session['gplus_id']
		del login_session['username']
		del login_session['email']
		del login_session['picture']
		flash(flash_message)
		return redirect(url_for("showCatalog"))
		response = make_response(json.dumps('Successfully disconnected.'), 200)
		response.headers['Content-Type'] = 'application/json'
		return response
	else:
		response = make_response(json.dumps('Failed to revoke token for given user.', 400))
		response.headers['Content-Type'] = 'application/json'
		return response

@app.route("/")
@app.route("/catalog")
def showCatalog():
	location = "/catalog"
	pageTitle = "Catalog App"
	categories = getCategories()
	category_names = {}
	if "username" not in login_session:
		user_id = ''
	else:
		user_id = login_session["username"]
	state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for x in xrange(32))
	login_session['state'] = state
	for category in categories:
		category_names[category.id] = category.name
	items = session.query(Item).order_by(desc(Item.date)).all()
	return render_template("showCatalog.html", 
							pageTitle = pageTitle,
							categories = categories,
							category_names = category_names,
							items = items,
							location = location,
							user_id = user_id,
							STATE = state)

@app.route("/catalog/<string:category_name>/items")
def showCategory(category_name):
	location = "/catalog/%s/items" % category_name
	if "username" not in login_session:
		user_id = ''
	else:
		user_id = login_session["username"]
	state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for x in xrange(32))
	login_session['state'] = state
	pageTitle = category_name
	categories = getCategories()
	categoryItem = session.query(Category).filter_by(name = category_name).one()
	items = session.query(Item).filter_by(cat_id = categoryItem.id).order_by(desc(Item.date)).all()
	return render_template("showCategory.html",
							pageTitle = pageTitle,
							categories = categories,
							categoryItem = categoryItem,
							items = items,
							location = location,
							user_id = user_id,
							STATE = state)

@app.route("/catalog/<string:category_name>/<string:item_title>")
def showItem(category_name, item_title):
	user_id = None
	if "email" in login_session:
		user_id = getUserId(login_session["email"])
	location = "/catalog/%s/%s" % (category_name,item_title)
	#if "username" not in login_session:
	#	user_id = ''
	#else:
	#	user_id = login_session["username"]
	state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for x in xrange(32))
	login_session['state'] = state
	pageTitle = item_title
	categoryItem = session.query(Category).filter_by(name = category_name).one()
	item = session.query(Item).filter_by(title = item_title).one()
	return render_template("showItem.html",
							pageTitle = pageTitle,
							categoryItem = categoryItem,
							item = item,
							location = location,
							user_id = user_id,
							STATE = state)

@app.route("/catalog/new", methods=['GET', 'POST'])
def newItem():
	pageTitle = "New Item"
	categories = getCategories()
	if "username" not in login_session:
		flash_message = "YOU NEED TO LOGIN FIRST ..."
		flash(flash_message)
		return redirect(url_for("showCatalog"))
	if request.method == "POST":
		user_id = getUserId(login_session["email"])
		if not user_id:
			user_id = createUser(login_session)
		login_session["user_id"] = user_id
		existingItems = session.query(Item).filter_by(title = request.form['title']).count()
		if existingItems > 0:
			flash_message = "ITEM " + request.form['title'] + " ALREADY EXISTS ..."
			flash(flash_message)
			return render_template("newItem.html",
									pageTitle = pageTitle,
									categories = categories)
		else:
			category = session.query(Category).filter_by(name = request.form["category"]).one()
			newItem = Item(title = request.form['title'], description = request.form['description'], cat_id = category.id, user_id = user_id)
			session.add(newItem)
			session.commit()
			flash_message = "ITEM " + newItem.title + " ADDED ..."
			flash(flash_message)
			return redirect(url_for("showCatalog"))
	else:
		return render_template("newItem.html",
								pageTitle = pageTitle,
								categories = categories)

@app.route("/catalog/<string:item_title>/edit", methods=['GET', 'POST'])
def editItem(item_title):
	user_id = getUserId(login_session["email"])
	print "user_id: %s" % user_id
	pageTitle = "Edit " + item_title	
	item = session.query(Item).filter_by(title = item_title).one()
	print "item user_id: %s" % item.user_id
	currentItem = Item(title = item.title, description = item.description, cat_id = item.cat_id)
	categories = getCategories()
	categoryItem = session.query(Category).filter_by(id = item.cat_id).one()
	if "username" not in login_session:
		flash_message = "YOU NEED TO LOGIN FIRST ..."
		flash(flash_message)
		return redirect(url_for("showItem", category_name = categoryItem.name, item_title = item_title))	
	if request.method == "POST":
		existingItems = session.query(Item).filter_by(title = request.form['title']).count()
		if existingItems > 0:
			existingItem = session.query(Item).filter_by(title = request.form['title']).one()	 
		if existingItems > 0 and existingItem.id != item.id:
			flash_message = "ITEM " + existingItem.title + " ALREADY EXISTS ..."
			flash(flash_message)
			return render_template("editItem.html",
									pageTitle = pageTitle,
									categories = categories,
									categoryItem = categoryItem,
									item = item,
									user_id = user_id)
		else:
			category = session.query(Category).filter_by(name = request.form["category"]).one()
			if request.form["title"] != item.title or request.form["description"] != item.description or category.id != item.cat_id:
				flash_message = "ITEM " + item.title + " UPDATED ..."
				item.title = request.form["title"]
				item.description = request.form["description"]
				item.cat_id = category.id
				session.add(item)
				session.commit()
				flash(flash_message)
			return redirect(url_for("showCatalog"))
	else:
		return render_template("editItem.html",
								pageTitle = pageTitle,
								categories = categories,
								categoryItem = categoryItem,
								item = item,
								user_id = user_id)

@app.route("/catalog/<string:item_title>/delete", methods=['GET', 'POST'])
def deleteItem(item_title):
	pageTitle = "Delete " + item_title
	item = session.query(Item).filter_by(title = item_title).one()
	categoryItem = session.query(Category).filter_by(id = item.cat_id).one()
	if "username" not in login_session:
		flash_message = "YOU NEED TO LOGIN FIRST ..."
		flash(flash_message)
		return redirect(url_for("showItem", category_name = categoryItem.name, item_title = item_title))

	if request.method == "POST":
		session.delete(item)
		session.commit()
		flash_message = "ITEM " + item.title + " DELETED ..."
		flash(flash_message)
		return redirect(url_for("showCatalog"))
	else:
		return render_template("deleteItem.html",
								pageTitle = pageTitle,
								categoryItem = categoryItem,
								item = item)

@app.route("/catalog.json")
def showJSON():
	categories = getCategories()
	items = session.query(Item).all()
	catalog = { "Category": [c.serialize for c in categories]}
	for c in catalog["Category"]:
		c["Item"] = [item.serialize for item in items if item.cat_id]
	return jsonify(catalog)

def getUserInfo(user_id):
	user = session.query(User).filter_by(id = user_id).one()
	return user

def getUserId(email):
	try:
		user = session.query(User).filter_by(email = email).one()
		return user.id
	except:
		return None

def createUser(login_session):
	newUser = User(name = login_session["username"], email = login_session["email"], picture = login_session["picture"])
	session.add(newUser)
	session.commit()
	user = session.query(User).filter_by(email = login_session["email"]).one()
	return user.id

if __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    app.debug = True
    app.run(host='0.0.0.0', port=8000)