#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import datetime, sys
import json
from tkinter.tix import TCL_ALL_EVENTS
import dateutil.parser
import babel
from flask import Flask, render_template, request, Response, flash, redirect, url_for, abort
from flask_moment import Moment
import logging
from logging import Formatter, FileHandler
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import Form
from forms import *
import collections
collections.Callable = collections.abc.Callable
from models import Venue, Show, Artist, db
from flask_migrate import Migrate

#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
db.init_app(app)
migrate = Migrate(app, db)

#----------------------------------------------------------------------------#
# Models.
#----------------------------------------------------------------------------#

#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
  date = dateutil.parser.parse(value)
  if format == 'full':
      format="EEEE MMMM, d, y 'at' h:mma"
  elif format == 'medium':
      format="EE MM, dd, y h:mma"
  return babel.dates.format_datetime(date, format, locale='en')

app.jinja_env.filters['datetime'] = format_datetime

#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#

@app.route('/')
def index():
  return render_template('pages/home.html')


#  Venues
#  ----------------------------------------------------------------

@app.route('/venues')
def venues():
  data = []
  city_state = Venue.query.with_entities(Venue.city, Venue.state).distinct().all()
  print(city_state)
  for i in city_state:
    d = {}
    venues = Venue.query.filter_by(city=i.city, state=i.state).all()
    d['city'] = i.city
    d['state'] = i.state
    d['venues'] = venues
    data.append(d)
  return render_template('pages/venues.html', areas=data)

@app.route('/venues/search', methods=['POST'])
def search_venues():
  search_term = request.form['search_term']
  search_results = []
  num_search_results = 0
  query_string = f'%{search_term}%'
  answers = Venue.query.filter(Venue.name.ilike(query_string)).all()
  num_search_results = len(answers)
  for answer in answers:
    details = {}
    details['id'] = answer.id 
    details['name'] = answer.name
    search_results.append(details)
  response={
    "count": num_search_results,
    "data": search_results
  }
  return render_template('pages/search_venues.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
  venue = Venue.query.filter_by(id=venue_id).first()
  past_shows = []
  upcoming_shows = []
  # get past shows
  past_shows_query = db.session.query(Show).join(Venue).filter(Show.venue_id==venue_id).filter(Show.start_time<datetime.now()).all()   
  past_shows_count = len(past_shows_query)
  for show in past_shows_query:
    show_details = {}
    show_details['artist_id'] = show.artist.id
    show_details['artist_name'] = show.artist.name
    show_details['start_time'] = show.start_time.strftime("%Y-%m-%d %H:%M:%S")
    show_details['artist_image_link'] = show.artist.image_link
    past_shows.append(show_details)
  # get upcoming shows
  upcoming_shows_query = db.session.query(Show).join(Venue).filter(Show.venue_id==venue_id).filter(Show.start_time>datetime.now()).all()   
  upcoming_shows_count = len(upcoming_shows_query)
  for show in upcoming_shows_query:
    show_details = {}
    show_details['artist_id'] = show.artist.id
    show_details['artist_name'] = show.artist.name
    show_details['start_time'] = show.start_time.strftime("%Y-%m-%d %H:%M:%S")
    show_details['artist_image_link'] = show.artist.image_link
    upcoming_shows.append(show_details)
  # populate the data dictionary
  data = {}
  data['id'] = venue.id
  data['name'] = venue.name
  data['genres'] = venue.genres
  data['address'] = venue.address
  data['city'] = venue.city
  data['state'] = venue.state
  data['phone'] = venue.phone
  data['website_link'] = venue.website_link
  data['facebook_link'] = venue.facebook_link
  data['seeking_talent'] = venue.seeking_talent
  data['seeking_description'] = venue.seeking_description
  data['image_link'] = venue.image_link
  data['past_shows'] = past_shows
  data['upcoming_shows'] = upcoming_shows  
  data['past_shows_count'] = past_shows_count
  data['upcoming_shows_count'] = upcoming_shows_count
  
  return render_template('pages/show_venue.html', venue=data)


#  Create Venue
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
  form = VenueForm()
  return render_template('forms/new_venue.html', form=form)

@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
  form = VenueForm()
  if form.validate_on_submit():
    e = False
    body = {}
    try:
      name = request.form.get('name')
      city = request.form.get('city')
      state = request.form.get('state')
      address = request.form.get('address')
      phone = request.form.get('phone')
      genres = request.form.getlist('genres')
      facebook_link = request.form.get('facebook_link')
      website_link = request.form.get('website_link')
      seeking_t = request.form.get('seeking_talent')
      if seeking_t == 'y':
        seeking_talent = True
      else:
        seeking_talent = False
      
      venue = Venue(id=4,seeking_talent=seeking_talent,website_link=website_link,name=name,city=city,state=state,address=address,phone=phone,facebook_link=facebook_link, genres=genres)
      db.session.add(venue)
      db.session.commit()
      body['id'] = venue.id
      body['name'] = venue.name
      flash('Venue ' + request.form['name'] + ' was successfully listed!')
    except:
      e = True
      print(sys.exc_info())
      db.session.rollback()
      flash('Error: Venue ' + request.form['name'] + ' was not successfully listed!')
    finally:
      db.session.close()
    if e:
      abort(500)
    else:
      return render_template('pages/home.html')
  else:
    for field, message in form.errors.items():
      flash(field + ' - ' + str(message), 'danger')
  return render_template('forms/new_venue.html', form=form)

@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
  e = False
  try:
    venue = Venue.query.filter_by(id=venue_id).first()
    print(venue)
    db.session.delete(venue)
    db.session.commit()
    flash('Venue ' + venue.name + ' was successfully deleted!')

  except:
    e = True
    print('An error occured')
    print(sys.exc_info())
    db.session.rollback()
    flash('Venue ' + venue.name + ' could not be deleted. ')
  finally:
    db.session.close()
  if e:
    abort(500)
  else:
    return redirect(url_for('venues'))


#  ----------------------------------------------------------------
#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
  data = Artist.query.all()
  return render_template('pages/artists.html', artists=data)

@app.route('/artists/search', methods=['POST'])
def search_artists():
  search_term = request.form['search_term']
  search_results = []
  num_search_results = 0
  query_string = f'%{search_term}%'
  answers = Artist.query.filter(Artist.name.ilike(query_string)).all()
  num_search_results = len(answers)
  for answer in answers:
    details = {}
    details['id'] = answer.id
    details['name'] = answer.name
    search_results.append(details)
  response={
    "count": num_search_results,
    "data": search_results
  }
  return render_template('pages/search_artists.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
  artist = Artist.query.filter_by(id=artist_id).first()
  past_shows = []
  upcoming_shows = []
  # get past shows
  past_shows_query = db.session.query(Show).join(Artist).filter(Show.artist_id==artist_id).filter(Show.start_time<datetime.now()).all()   
  past_shows_count = len(past_shows_query)
  for show in past_shows_query:
    show_details = {}
    show_details['venue_id'] = show.venue_id
    show_details['venue_name'] = show.venue.name
    show_details['venue_image_link'] = show.venue.image_link
    show_details['start_time'] = show.start_time.strftime("%Y-%m-%d %H:%M:%S")
    show_details['artist_image_link'] = artist.image_link
    past_shows.append(show_details)
  # get upcoming shows
  upcoming_shows_query = db.session.query(Show).join(Venue).filter(Show.artist_id==artist_id).filter(Show.start_time>datetime.now()).all()   
  upcoming_shows_count = len(upcoming_shows_query)
  for show in upcoming_shows_query:
    show_details = {}
    show_details['venue_id'] = show.venue_id
    show_details['venue_name'] = show.venue.name
    show_details['venue_image_link'] = show.venue.image_link
    show_details['start_time'] = show.start_time.strftime("%Y-%m-%d %H:%M:%S")
    show_details['artist_image_link'] = artist.image_link
    upcoming_shows.append(show_details)
  # populate the data dictionary
  data = {}
  data['id'] = artist.id
  data['name'] = artist.name
  data['genres'] = artist.genres
  data['city'] = artist.city
  data['state'] = artist.state
  data['phone'] = artist.phone
  data['website_link'] = artist.website_link
  data['facebook_link'] = artist.facebook_link
  data['seeking_venue'] = artist.seeking_venue
  data['seeking_description'] = artist.seeking_description
  data['image_link'] = artist.image_link
  data['past_shows'] = past_shows
  data['upcoming_shows'] = upcoming_shows  
  data['past_shows_count'] = past_shows_count
  data['upcoming_shows_count'] = upcoming_shows_count
  
  return render_template('pages/show_artist.html', artist=data)
#  Update
#  ----------------------------------------------------------------

@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
  form = ArtistForm()
  artist = Artist.query.filter_by(id=artist_id).first()
  return render_template('forms/edit_artist.html', form=form, artist=artist)

@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
  try:
    artist = Artist.query.filter_by(id=artist_id).first()

    artist.name = request.form.get('name')
    artist.city = request.form.get('city')
    artist.state = request.form.get('state')
    artist.phone = request.form.get('phone')
    artist.genres = request.form.getlist('genres')
    artist.facebook_link = request.form.get('facebook_link')
    artist.seeking_description = request.form.get('seeking_description')
    artist.image_link = request.form.get('image_link')
    artist.website_link = request.form.get('website_link')
    seeking_v = request.form.get('seeking_venue')
    if seeking_v == 'y':
      artist.seeking_venue = True
    else:
      artist.seeking_venue = False

    db.session.add(artist)
    db.session.commit()
  except:
    db.session.rollback()
  finally:
    db.session.close()
  return redirect(url_for('show_artist', artist_id=artist_id))

@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
  form = VenueForm()
  venue = Venue.query.filter_by(id=venue_id).first()
  
  # TODO: populate form with values from venue with ID <venue_id>
  return render_template('forms/edit_venue.html', form=form, venue=venue)

@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
  try:
    venue = Venue.query.filter_by(id=venue_id).first()
    venue.name = request.form.get('name')
    venue.city = request.form.get('city')
    venue.state = request.form.get('state')
    venue.phone = request.form.get('phone')
    venue.genres = request.form.getlist('genres')
    venue.facebook_link = request.form.get('facebook_link')
    venue.seeking_description = request.form.get('seeking_description')
    venue.image_link = request.form.get('image_link')
    venue.website_link = request.form.get('website_link')
    seeking_t = request.form.get('seeking_talent')
    if seeking_t == 'y':
      venue.seeking_talent = True
    else:
      venue.seeking_talent = False

    db.session.add(venue)
    db.session.commit()
  except:
    db.session.rollback()
  finally:
    db.session.close()
  return redirect(url_for('show_venue', venue_id=venue_id))

#  Create Artist
#  ----------------------------------------------------------------

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
  form = ArtistForm()
  return render_template('forms/new_artist.html', form=form)

@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
  form = ArtistForm()
  if form.validate_on_submit():
    e = False
    body = {}
    try:
      name = request.form.get('name')
      city = request.form.get('city')
      state = request.form.get('state')
      phone = request.form.get('phone')
      genres = request.form.getlist('genres')
      facebook_link = request.form.get('facebook_link')
      image_link = request.form.get('image_link')
      seeking_description = request.form.get('seeking_description')
      seeking_v = request.form.get('seeking_venue')
      if seeking_v == 'y':
        seeking_venue = True
      else:
        seeking_venue = False
      website_link = request.form.get('website_link')
      
      artist = Artist(name=name,city=city,state=state,image_link=image_link,seeking_description=seeking_description,seeking_venue=seeking_venue,website_link=website_link,phone=phone,facebook_link=facebook_link, genres=genres)
      db.session.add(artist)
      db.session.commit()
      body['id'] = artist.id
      body['name'] = artist.name
      flash('Artist ' + request.form['name'] + ' was successfully listed!')
    except:
      e = True
      print(sys.exc_info())
      db.session.rollback()
      flash('Error: Artist ' + request.form['name'] + ' was not successfully listed!')
    finally:
      db.session.close()
    if e:
      abort(500)
    else:
      return render_template('pages/home.html')
  else:
    for field, message in form.errors.items():
      flash(field + ' - ' + str(message), 'danger')
  return render_template('forms/new_artist.html', form=form)

#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
  # displays list of shows at /shows
  # TODO: replace with real venues data.
 
  all_shows = Show.query.all()
  data = []
  for show in all_shows:
    
    artist_id = show.artist_id
    venue_id = show.venue_id
    show_artist = Artist.query.filter_by(id=artist_id).first()
    show_venue = Venue.query.filter_by(id=venue_id).first()
    show_details = {
      "artist_id": artist_id,
      "venue_id": venue_id,
      "start_time": show.start_time.strftime("%Y-%m-%d %H:%M:%S"),
      "artist_name": show_artist.name,
      "venue_name": show_venue.name,
      "artist_image_link": show_artist.image_link
    }
    data.append(show_details)
    
  return render_template('pages/shows.html', shows=data)

@app.route('/shows/create')
def create_shows():
  # renders form. do not touch.
  form = ShowForm()
  return render_template('forms/new_show.html', form=form)

@app.route('/shows/create', methods=['POST'])
def create_show_submission():
  e = False
  try:
    artist_id = request.form['artist_id']
    venue_id = request.form['venue_id']
    start_time = request.form['start_time']

    show = Show(artist_id=artist_id, venue_id=venue_id, start_time=start_time)
    db.session.add(show)
    db.session.commit()
    flash('Congrats! Your show has been listed.')
  except:
    e = True
    print(sys.exc_info())
    db.session.rollback()
    flash('Error: Could not add show.')
  finally:
    db.session.close()
  if e:
    abort(500)
  else:
    return render_template('pages/home.html')


@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500


if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')

#----------------------------------------------------------------------------#
# Launch.
#----------------------------------------------------------------------------#

# Default port:
if __name__ == '__main__':
    app.run()

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''
