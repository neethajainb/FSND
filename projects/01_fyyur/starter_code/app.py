#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import json
import dateutil.parser
import babel
from flask import Flask, render_template, request, Response, flash, redirect, url_for
from flask_moment import Moment
from sqlalchemy import func
from flask_sqlalchemy import SQLAlchemy
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from forms import *

#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
db = SQLAlchemy(app)

#----------------------------------------------------------------------------#
# Models.
#----------------------------------------------------------------------------#
class SeekingTalent(db.Model):
    __tablename__ = 'seekingtalent'
    id = db.Column(db.Integer, primary_key=True)
    venue_id = db.Column(db.Integer, db.ForeignKey('venue.id'), nullable=False)
    seeking_description = db.Column(db.String)
    seeking_talent = db.Column(db.String)

#TODO add website
#"website": "https://www.themusicalhop.com",
#TODO ADD GENRES
class Venue(db.Model):
    __tablename__ = 'venue'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    address = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    website_link = db.Column(db.String(300))
    # TODO: implement any missing fields, as a database migration using Flask-Migrate

class Artist(db.Model):
    __tablename__ = 'artist'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    genres = db.Column(db.String(120))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))

    # TODO: implement any missing fields, as a database migration using Flask-Migrate

class Show(db.Model):
    __tablename__ = 'shows'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    venue_id = db.Column(db.Integer, db.ForeignKey('venue.id'), nullable=False)
    artist_id = db.Column(db.Integer, db.ForeignKey('artist.id'), nullable=False)
    start_time = db.Column(db.DateTime, nullable=False)

#print("One Time Only")
db.create_all()

# TODO Implement Show and Artist models, and complete all model relationships and properties, as a database migration.

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
  # TODO: num_shows should be aggregated based on number of upcoming shows per venue.

  all_areas = Venue.query.with_entities(func.count(Venue.id), Venue.city, Venue.state).group_by(Venue.city, Venue.state).all()
  data = []

  for area in all_areas:
    area_venues = Venue.query.filter_by(state=area.state).filter_by(city=area.city).all()
    venue_data = []
    for venue in area_venues:
      venue_data.append({
        "id": venue.id,
        "name": venue.name,
        "num_upcoming_shows": len(db.session.query(Show).filter(Show.venue_id==1).filter(Show.start_time>datetime.now()).all())
      })
    data.append({
      "city": area.city,
      "state": area.state,
      "venues": venue_data
    })

  return render_template('pages/venues.html', areas=data);

@app.route('/venues/search', methods=['POST'])
def search_venues():
  search_term = request.form.get('search_term', '')
  search_result = db.session.query(Venue).filter(Venue.name.ilike(f'%{search_term}%')).all()
  data = []

  for result in search_result:
    data.append({
      "id": result.id,
      "name": result.name,
      "num_upcoming_shows": len(db.session.query(Show).filter(Show.venue_id == result.id).filter(Show.start_time > datetime.now()).all()),
    })
  # TODO: implement search on artists with partial string search. Ensure it is case-insensitive.
  # seach for Hop should return "The Musical Hop".
  # search for "Music" should return "The Musical Hop" and "Park Square Live Music & Coffee"
  response={
    "count": len(search_result),
    "data": data
  }
  return render_template('pages/search_venues.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/venues/<int:user_provided_venue_id>')
def show_venue(user_provided_venue_id):
  venue = Venue.query.get(user_provided_venue_id)

  if not venue:
    return render_template('errors/404.html')

  past_shows_db = db.session.query(Show, Artist).filter(Show.venue_id==user_provided_venue_id).filter(Show.start_time<datetime.now()).join(Artist,Show.artist_id == Artist.id).all()
  past_shows = []

  for result in past_shows_db:
    past_shows.append({
      "artist_id": result.Artist.id,
      "artist_image_link": result.Artist.image_link,
      "artist_name": result.Artist.name,
      "start_time": result.Show.start_time.strftime('%Y-%m-%d %H:%M:%S')
    })


  upcoming_shows_db = db.session.query(Show, Artist).filter(Show.venue_id==user_provided_venue_id).filter(Show.start_time>datetime.now()).join(Artist,Show.artist_id == Artist.id).all()
  upcoming_shows = []

  for result in upcoming_shows_db:
    upcoming_shows.append({
      "artist_id": result.Artist.id,
      "artist_name": result.Artist.name,
      "artist_image_link": result.Artist.image_link,
      "start_time": result.Show.start_time.strftime("%Y-%m-%d %H:%M:%S")
    })

  view_data = {
    "id": venue.id,
    "name": venue.name,
    "genres": "",
    "address": venue.address,
    "city": venue.city,
    "state": venue.state,
    "phone": venue.phone,
    "website": "",
    "facebook_link": venue.facebook_link,
    "image_link": venue.image_link,
    "past_shows": past_shows,
    "upcoming_shows": upcoming_shows,
    "past_shows_count": len(past_shows),
    "upcoming_shows_count": len(upcoming_shows),
  }

  all_talents_db =  db.session.query(SeekingTalent).filter(SeekingTalent.venue_id==user_provided_venue_id).all()
  for result in all_talents_db:
    view_data["seeking_talent"] = result.seeking_talent
    view_data["seeking_description"] = result.seeking_description

  view_data = list(filter(lambda d: d['id'] == user_provided_venue_id, [view_data]))[0]
  return render_template('pages/show_venue.html', venue=view_data)

#  Create Venue
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
  form = VenueForm()
  return render_template('forms/new_venue.html', form=form)

@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
  eroor = False
  # TODO: insert form data as a new Venue record in the db, instead
  # TODO: modify data to be the data object returned from db insertion
  try:
    name = request.form['name']
    city = request.form.get('city', '')
    state = request.form.get('state', '')
    addr = request.form.get('address', '')
    phone = request.form.get('phone', '')
    image_link = request.form.get('image_link', '')
    facebook_link = request.form.get('facebook_link', '')
    website_link = request.form.get('website_link', '')
    venue = Venue(name=name,city=city,state=state,address=addr,phone=phone,facebook_link=facebook_link,image_link=image_link,website_link=website_link)
    db.session.add(venue)
    db.session.commit()
    flash('Venue ' + name + ' was successfully listed!')
  except Exception as e:
    print('Failed to list a venue: '+ str(e))
    db.session.rollback()
    flash('An error occurred. Venue ' + name + ' could not be listed.')
  finally:
    db.session.close()
  return render_template('pages/home.html')

@app.route('/venues/<venue_id>/delete', methods=['GET'])
def delete_venue(venue_id):
   error = False
   try:
    venue = Venue.query.get(venue_id)
    db.session.delete(venue)
    db.session.commit()
   except:
     error = True
     db.session.rollback()
   finally:
     db.session.close()
   if error:
     flash(f'An error occurred. Venue {venue_id} could not be deleted.')
   if not error:
     flash(f'Venue {venue_id} was successfully deleted.')

   return render_template('pages/home.html')

@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
  form = VenueForm()
  venue_db = Venue.query.get(venue_id)
  if not venue_db:
   return render_template('errors/404.html')

  venue={
    "id": venue_db.id,
    "name": venue_db.name,
    #TODO add genres
    #"genres": venue_db.genres,
    "address": venue_db.address,
    "city": venue_db.city,
    "state": venue_db.state,
    "phone": venue_db.phone,
    "facebook_link": venue_db.facebook_link,
    # TODO add seeking_talent,
    #"seeking_talent": True,
    #"seeking_description": "We are on the lookout for a local artist to play every two weeks. Please call us.",
    "image_link": venue_db.image_link
  }
  # TODO: populate form with values from venue with ID <venue_id>
  return render_template('forms/edit_venue.html', form=form, venue=venue)

@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
  eroor = False
  # TODO: insert form data as a new Venue record in the db, instead
  # TODO: modify data to be the data object returned from db insertion
  try:
    venue_db = Venue.query.get(venue_id)
    #venue_db = Venue.query.filter(Venue.id == venue_id).first()
    if not venue_db:
     return render_template('errors/404.html')

    venue_db.name = request.form['name']
    venue_db.city = request.form.get('city', '')
    venue_db.state = request.form.get('state', '')
    venue_db.address = request.form.get('address', '')
    venue_db.phone = request.form.get('phone', '')
    venue_db.image_link = request.form.get('image_link', '')
    venue_db.facebook_link = request.form.get('facebook_link', '')

    db.session.commit()
    flash('Venue ' + venue_db.name + ' was successfully updated!')
  except Exception as e:
    print('Failed to update a venue: '+ str(e))
    db.session.rollback()
    flash('An error occurred. Venue ' + data.name + ' could not be updated.')
  finally:
    db.session.close()

  # TODO: take values from the form submitted, and update existing
  # venue record with ID <venue_id> using the new attributes
  return redirect(url_for('show_venue', user_provided_venue_id = venue_id))

#  ----------------------------------------------------------------
#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
  # TODO: replace with real data returned from querying the database
  all_artists = Artist.query.with_entities(Artist.id, Artist.name).all()
  data = []

  for artist in all_artists:
      data.append({
        "id": artist.id,
        "name": artist.name
      })

  return render_template('pages/artists.html', artists=data)

@app.route('/artists/search', methods=['POST'])
def search_artists():
  # TODO: implement search on artists with partial string search. Ensure it is case-insensitive.
  # seach for "A" should return "Guns N Petals", "Matt Quevado", and "The Wild Sax Band".
  # search for "band" should return "The Wild Sax Band".
  search_term = request.form.get('search_term', '')
  search_result = db.session.query(Artist).filter(Artist.name.ilike(f'%{search_term}%')).all()
  data = []

  for result in search_result:
    data.append({
      "id": result.id,
      "name": result.name,
      "num_upcoming_shows": len(db.session.query(Show).filter(Show.artist_id == result.id).filter(Show.start_time > datetime.now()).all()),
    })
  # TODO: implement search on artists with partial string search. Ensure it is case-insensitive.
  # seach for Hop should return "The Musical Hop".
  # search for "Music" should return "The Musical Hop" and "Park Square Live Music & Coffee"
  response={
    "count": len(search_result),
    "data": data
  }

  return render_template('pages/search_artists.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/artists/<int:user_provided_artist_id>')
def show_artist(user_provided_artist_id):
  artist = Artist.query.get(user_provided_artist_id)
  if not artist:
   return render_template('errors/404.html')

  past_shows_query = db.session.query(Show,Venue).filter(Show.artist_id==user_provided_artist_id).filter(Show.start_time<datetime.now()).join(Venue, Show.venue_id == Venue.id)
  past_shows_db = past_shows_query.all()
  past_shows = []

  #"venue_id": 1,
  #"venue_name": "The Musical Hop",
  #"venue_image_link": "https://images.unsplash.com/photo-1543900694-133f37abaaa5?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=400&q=60",
  #"start_time": "2

  for result in past_shows_db:
    past_shows.append({
      "venue_id": result.Venue.id,
      "venue_name": result.Venue.name,
      "venue_image_link": result.Venue.image_link,
      "start_time": result.Show.start_time.strftime('%Y-%m-%d %H:%M:%S')
    })

  upcoming_shows_db = db.session.query(Show,Venue).filter(Show.artist_id==user_provided_artist_id).filter(Show.start_time>datetime.now()).join(Venue, Show.venue_id == Venue.id).all()
  upcoming_shows = []

  for result in upcoming_shows_db:
    upcoming_shows.append({
      "venue_id": result.Venue.id,
      "venue_name": result.Venue.name,
      "venue_image_link": result.Venue.image_link,
      "start_time": result.Show.start_time.strftime('%Y-%m-%d %H:%M:%S')
    })


  data = {
    "id": artist.id,
    "name": artist.name,
    "genres": artist.genres,
    "city": artist.city,
    "state": artist.state,
    "phone": artist.phone,
    "facebook_link": artist.facebook_link,
    #TODO
    "seeking_venue": "False",
    "seeking_description": "TODO",
    "image_link": artist.image_link,
    "past_shows": past_shows,
    "upcoming_shows": upcoming_shows,
    "past_shows_count": len(past_shows),
    "upcoming_shows_count": len(upcoming_shows),
  }

  data = list(filter(lambda d: d['id'] == user_provided_artist_id, [data]))[0]
  return render_template('pages/show_artist.html', artist=data)

#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
  form = ArtistForm()

  artist_db = Artist.query.get(artist_id)
  if not artist_db:
   return render_template('errors/404.html')

  artist={
    "id": artist_db.id,
    "name": artist_db.name,
    "genres": artist_db.genres,
    "city": artist_db.city,
    "state": artist_db.state,
    "phone": artist_db.phone,
    "facebook_link": artist_db.facebook_link,
    # add
    # TODO add seeking_talent, website
    #"seeking_venue": True,
    #"seeking_description": "We are on the lookout for a local artist to play every two weeks. Please call us.",
    "image_link": artist_db.image_link
  }
  return render_template('forms/edit_artist.html', form=form, artist=artist)

@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
  # TODO: take values from the form submitted, and update existing
  # artist record with ID <artist_id> using the new attributes
  eroor = False
  # TODO: insert form data as a new Venue record in the db, instead
  # TODO: modify data to be the data object returned from db insertion
  try:
    artist_db = Artist.query.get(artist_id)
    #venue_db = Venue.query.filter(Venue.id == venue_id).first()
    if not artist_db:
     return render_template('errors/404.html')

    artist_db.name = request.form['name']
    artist_db.city = request.form.get('city', '')
    artist_db.state = request.form.get('state', '')
    artist_db.address = request.form.get('address', '')
    artist_db.phone = request.form.get('phone', '')
    artist_db.image_link = request.form.get('image_link', '')
    artist_db.facebook_link = request.form.get('facebook_link', '')

    db.session.commit()
    flash('Venue ' + artist_db.name + ' was successfully updated!')
  except Exception as e:
    print('Failed to update a venue: '+ str(e))
    db.session.rollback()
    flash('An error occurred. Venue ' + data.name + ' could not be updated.')
  finally:
    db.session.close()

  return redirect(url_for('show_artist', user_provided_artist_id=artist_id))

#  Create Artist
#  ----------------------------------------------------------------

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
  form = ArtistForm()
  return render_template('forms/new_artist.html', form=form)

@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
  # called upon submitting the new artist listing form
  # TODO: insert form data as a new Venue record in the db, instead
  # TODO: modify data to be the data object returned from db insertion
  try:
    name = request.form['name']
    city = request.form.get('city', '')
    state = request.form.get('state', '')
    phone = request.form.get('phone', '')
    genres = request.form.get('genres', '')
    # TODO: genres multiple select not working
    image_link = request.form.get('image_link', '')
    facebook_link = request.form.get('facebook_link', '')
    artist = Artist(name=name,city=city,state=state,phone=phone,genres=genres,facebook_link=facebook_link,image_link=image_link)
    db.session.add(artist)
    db.session.commit()
    flash('Artist ' + request.form['name'] + ' was successfully listed!')
  except:
    db.session.rollback()
    flash('An error occurred. Artist ' + data.name + ' could not be listed.')
  finally:
    db.session.close()
  return render_template('pages/home.html')

  # on successful db insert, flash success

  # TODO: on unsuccessful db insert, flash an error instead.
  # e.g., flash('An error occurred. Artist ' + data.name + ' could not be listed.')

#TODO Use DELETE HTTP method instead of GET and remove /delete from URL
# REST semantics
@app.route('/artists/<artist_id>/delete', methods=['GET'])
def delete_artist(artist_id):
   error = False
   try:
    artist = Artist.query.get(artist_id)
    db.session.delete(artist)
    db.session.commit()
   except:
     error = True
     db.session.rollback()
   finally:
     db.session.close()
   if error:
     flash(f'An error occurred. Artist {artist_id} could not be deleted.')
   if not error:
     flash(f'Artist {artist.name} was successfully deleted.')

   return render_template('pages/home.html')


#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
  # displays list of shows at /shows
  # TODO: replace with real venues data.
  #       num_shows should be aggregated based on number of upcoming shows per venue.

  data = []
  all_shows = Show.query.all()
  for show in all_shows:
    shows_query = db.session.query(Show, Artist, Venue).filter(Show.id == show.id).join(Artist,Artist.id == Show.artist_id).join(Venue, Venue.id == Show.venue_id)
    result_set = shows_query.all()
    print(result_set)
    for result in result_set:
      data.append({
       "venue_id": result.Venue.id,
       "venue_name": result.Venue.name,
       "artist_id": result.Artist.id,
       "artist_name": result.Artist.name,
       "artist_image_link": result.Artist.image_link,
       "start_time": result.Show.start_time.strftime('%Y-%m-%d %H:%M:%S')
      })


  return render_template('pages/shows.html', shows=data)

@app.route('/shows/create', methods=['GET'])
def create_shows():
  # renders form. do not touch.
  form =  ShowForm()
  return render_template('forms/new_show.html', form=form)

@app.route('/shows/create', methods=['POST'])
def create_show_submission():
 try:
   name = request.form['name']
   artist_id = request.form['artist_id']
   venue_id = request.form.get('venue_id', '')
   start_time = request.form.get('start_time', '')
   show = Show(name=name,artist_id=artist_id,venue_id=venue_id,start_time=start_time)
   db.session.add(show)
   db.session.commit()
   flash('Show ' + name + ' was successfully listed!')
 except Exception as e: # work on python 2.x
   print('Failed to list a show: '+ str(e))
   db.session.rollback()
   flash('An error occurred. Show ' + name + ' could not be listed.')
 finally:
   db.session.close()
 return render_template('pages/home.html')

  # called to create new shows in the db, upon submitting new show listing form
  # TODO: insert form data as a new Show record in the db, instead

  # TODO: on unsuccessful db insert, flash an error instead.
  # e.g., flash('An error occurred. Show could not be listed.')
  # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/


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
