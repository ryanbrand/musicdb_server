#!/usr/bin/env python2.7

"""
Columbia's COMS W4111.001 Introduction to Databases
MusicDB Webserver

To run locally:

    python server.py

Go to http://localhost:8111 in your browser.

A debugger such as "pdb" may be helpful for debugging.
Read about it online.
"""

import os
import datetime
from sqlalchemy import *
from sqlalchemy.pool import NullPool
from flask import Flask, request, render_template, g, redirect, Response, session, current_app

tmpl_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
app = Flask(__name__, template_folder=tmpl_dir)

# Set URI used to connect to database server
DATABASEURI = "postgresql://rmb2208:4410@35.227.79.146/proj1part2"

# Create database engine using URI
engine = create_engine(DATABASEURI)

@app.before_request
def before_request():
  """
  This function is run at the beginning of every web request 
  (every time you enter an address in the web browser).
  We use it to setup a database connection that can be used throughout the request.

  The variable g is globally accessible.
  """
  try:
    g.conn = engine.connect()
  except:
    print "uh oh, problem connecting to database"
    import traceback; traceback.print_exc()
    g.conn = None

@app.teardown_request
def teardown_request(exception):
  """
  At the end of the web request, this makes sure to close the database connection.
  If you don't, the database could run out of memory!
  """
  try:
    g.conn.close()
  except Exception as e:
    pass

@app.route('/')
def index():
  """
  Render index template
  """
  return render_template("index.html")

@app.route('/new_user')
def new_user():
  """
  Render new user template
  """
  return render_template("new_user.html")

@app.route('/logout')
def logout():
  """
  Render index template upon logout
  """
  return render_template("index.html")

@app.route('/fail_new_user')
def fail_new_user():
  """
  Render fail_new_user template
  """
  return render_template("fail_new_user.html")

@app.route('/login_fail')
def login_fail():
  """
  Render login_fail template
  """
  return render_template("login_fail.html")

@app.route('/homepage')
def homepage():
  """
  Query database for relevant user data and render on homepage template
  """

  # Obtain user albums from database
  albums_result = g.conn.execute("SELECT album_title, artist_name FROM album_saved_by a, artists t WHERE a.userid=%s AND a.artistid=t.artistid;", current_app.user_id)
  album_titles = ''
  for a in albums_result:
    album_titles = album_titles + str(a['album_title']) + ' by ' + str(a['artist_name']) + '\n'
  albums_result.close()

  # Obtain user songs from database
  songs_result = g.conn.execute("SELECT song_title, album_title, artist_name FROM song_saved_by s, artists t WHERE s.userid=%s AND s.artistid=t.artistid;", current_app.user_id)
  song_titles = ''
  for s in songs_result:
    song_titles = song_titles + str(s['song_title']) + ' from ' + str(s['album_title']) + ' by ' + str(s['artist_name']) + '\n'
  songs_result.close()

  # Obtain user album ratings from database
  album_ratings_result = g.conn.execute("SELECT album_title, artist_name, album_rating FROM album_rated_by a, artists t WHERE a.userid=%s AND a.artistid=t.artistid ORDER BY album_rating DESC;", current_app.user_id)
  album_ratings = ''
  for a in album_ratings_result:
    album_ratings = album_ratings + str(a['album_rating']) + ': ' + str(a['album_title']) + ' by ' + str(a['artist_name']) + '\n'
  album_ratings_result.close()

  # Obtain user song ratings from database
  song_ratings_result = g.conn.execute("SELECT song_title, album_title, artist_name, song_rating FROM song_rated_by a, artists t WHERE a.userid=%s AND a.artistid=t.artistid ORDER BY song_rating DESC;", current_app.user_id)
  song_ratings = ''
  for a in song_ratings_result:
    song_ratings = song_ratings + str(a['song_rating']) + ': ' + str(a['song_title']) + ' from ' + str(a['album_title']) + ' by ' + str(a['artist_name']) + '\n'
  song_ratings_result.close()
 
  # Obtain user suggested songs
  suggested_result = g.conn.execute("SELECT song_title, album_title, artist_name, suggested_by FROM suggested_song s, artists t WHERE s.userid=%s AND s.artistid=t.artistid", current_app.user_id)
  song_suggestions = ''
  for a in suggested_result:
    song_suggestions = song_suggestions + str(a['suggested_by']) + ' suggests: ' + str(a['song_title']) + ' from ' + str(a['album_title']) + ' by ' + str(a['artist_name']) + '\n'
  suggested_result.close()
  
 
  # Obtain user playlists from database (private)
  priv_playlists_result = g.conn.execute("SELECT playlist_name FROM private_playlists p WHERE p.userid=%s;", current_app.user_id)
  priv_playlist_titles = ''
  for p in priv_playlists_result:
    priv_playlist_titles = priv_playlist_titles + str(p['playlist_name']) + '\n'
  priv_playlists_result.close()

  # Obtain user playlists from database (collaborative)
  coll_playlists_result = g.conn.execute("SELECT playlist_name FROM collaborative_playlists p WHERE p.userid=%s;", current_app.user_id)
  coll_playlist_titles = ''
  for p in coll_playlists_result:
    coll_playlist_titles = coll_playlist_titles + str(p['playlist_name']) + '\n'
  coll_playlists_result.close()

  # Obtain other playlists from database
  friend_playlists_result = g.conn.execute("SELECT playlist_name, user_name, userid FROM can_edit p, users u WHERE p.collaborator_userid=%s AND p.creator_userid=u.userid;", current_app.user_id)
  friend_playlist_titles = ''
  for p in friend_playlists_result:
    friend_playlist_titles = friend_playlist_titles + str(p['playlist_name']) + ' (Created by ' + str(p['user_name']) + ': ' + str(p['userid']) + ')\n'
  friend_playlists_result.close()

  # Obtain user ids and names of friends from database
  friends_result = g.conn.execute("SELECT userid_2, user_name FROM users u, are_friends f WHERE f.userid_1=%s AND f.userid_2=u.userid", current_app.user_id)
  friend_names = ''
  for f in friends_result:
    friend_names = friend_names + str(f['user_name']) + ' (' + str(f['userid_2']) + ')' + '\n'
  friends_result.close()  

  # Obtain user ids and names of users who have added logged in user as friend
  try:
    added_me_result = g.conn.execute("SELECT userid_1, user_name FROM users u, are_friends f WHERE f.userid_2=%s AND f.userid_1=u.userid", current_app.user_id)
    added_me_names = ''
    for a in added_me_result.fetchall():
      print '>>>>>>>>>>>>', a
      added_me_names = added_me_names + str(a['user_name']) + ' (' + str(a['userid_1']) + ')' + '\n'
  except Exception as e:
     print('^^^^^^^^^^',e)
     return render_template('index.html')
  context = dict(songs=song_titles, albums=album_titles, private_playlists=priv_playlist_titles, collaborative_playlists=coll_playlist_titles, friend_playlists=friend_playlist_titles, friends=friend_names, added_me=added_me_names, song_ratings=song_ratings, album_ratings=album_ratings,suggested_songs=song_suggestions)

  return render_template("homepage.html", **context)


@app.route('/view_friend', methods=['POST'])
def view_friend():
  """
  Query database for relevant user data and render on homepage template
  """
  friendid = request.form['friend_id']
  try:
    result = g.conn.execute("SELECT * FROM are_friends f WHERE f.userid_1=%s AND f.userid_2=%s", friendid, current_app.user_id)
    print(current_app.user_id)
    if len(list(result)) != 0:
      # Obtain user albums from database
      albums_result = g.conn.execute("SELECT album_title, artist_name FROM album_saved_by a, artists t WHERE a.userid=%s AND a.artistid=t.artistid;", friendid)
      album_titles = ''
      for a in albums_result:
        album_titles = album_titles + str(a['album_title']) + ' by ' + str(a['artist_name']) + '\n'
      albums_result.close()

      # Obtain user songs from database
      songs_result = g.conn.execute("SELECT song_title, album_title, artist_name FROM song_saved_by s, artists t WHERE s.userid=%s AND s.artistid=t.artistid;", friendid)
      song_titles = ''
      for s in songs_result:
        song_titles = song_titles + str(s['song_title']) + ' from ' + str(s['album_title']) + ' by ' + str(s['artist_name']) + '\n'
      songs_result.close()

      # Obtain user album ratings from database
      album_ratings_result = g.conn.execute("SELECT album_title, artist_name, album_rating FROM album_rated_by a, artists t WHERE a.userid=%s AND a.artistid=t.artistid ORDER BY album_rating DESC;", friendid)
      album_ratings = ''
      for a in album_ratings_result:
        album_ratings = album_ratings + str(a['album_rating']) + ': ' + str(a['album_title']) + ' by ' + str(a['artist_name']) + '\n'
      album_ratings_result.close()

      # Obtain user song ratings from database
      song_ratings_result = g.conn.execute("SELECT song_title, album_title, artist_name, song_rating FROM song_rated_by a, artists t WHERE a.userid=%s AND a.artistid=t.artistid ORDER BY song_rating DESC;", friendid)
      song_ratings = ''
      for a in song_ratings_result:
        song_ratings = song_ratings + str(a['song_rating']) + ': ' + str(a['song_title']) + ' from ' + str(a['album_title']) + ' by ' + str(a['artist_name']) + '\n'
      song_ratings_result.close()

      # Obtain user playlists from database (private)
      priv_playlists_result = g.conn.execute("SELECT playlist_name FROM private_playlists p WHERE p.userid=%s;", friendid)
      priv_playlist_titles = ''
      for p in priv_playlists_result:
        priv_playlist_titles = priv_playlist_titles + str(p['playlist_name']) + '\n'
      priv_playlists_result.close()

      # Obtain user playlists from database (collaborative)
      coll_playlists_result = g.conn.execute("SELECT playlist_name FROM collaborative_playlists p WHERE p.userid=%s;", friendid)
      coll_playlist_titles = ''
      for p in coll_playlists_result:
        coll_playlist_titles = coll_playlist_titles + str(p['playlist_name']) + '\n'
      coll_playlists_result.close()

      context = dict(songs=song_titles, albums=album_titles, personal_playlists=priv_playlist_titles, collaborative_playlists = coll_playlist_titles, song_ratings=song_ratings, album_ratings=album_ratings)
      return render_template('/homepage_friends.html', **context)
    else:
      return render_template('view_friend_fail.html')
  except Exception as e:
    return render_template('view_friend_fail.html')

@app.route('/add_new_user', methods=['POST'])
def add_new_user():
  """
  Add new user to database
  """
  name = request.form['name']
  userid = request.form['userid']
  password = request.form['password']
  try:
    g.conn.execute('INSERT INTO users VALUES (%s, %s, %s)', userid, name, password)
    return redirect('/')
  except Exception as e:
    return redirect('/fail_new_user')

@app.route('/login')
def login():
    abort(401)
    this_is_never_executed()

@app.route('/login2', methods=['POST'])
def login2():
  """
  Process attempted user login
  """
  userid = request.form['userid']
  password = request.form['password']
  result = g.conn.execute("SELECT pwd FROM users WHERE users.userid=%s;", userid)
  if(result.returns_rows):
    for row in result:
      if password == row['pwd']:
        current_app.user_id = userid
        print('set USERID to ' + current_app.user_id)
        print('Successful login')
        return redirect('/homepage')
      else:
        return redirect('/login_fail')
  return redirect('/login_fail')

@app.route('/search_artist', methods=['POST'])
def search_artist():
  """
  Search database for albums by requested artist
  """
  artist_name = request.form['artist_name']
  result = g.conn.execute("SELECT * FROM artists a, albums b WHERE a.artist_name=%s AND a.artistid=b.artistid ORDER BY b.release_date DESC;", artist_name)
  album_titles = ''
  for row in result:
    release_date = str(row['release_date'])
    album_title = str(row['album_title'])
    num_songs = str(row['num_songs'])
    album_titles = album_titles + '{}: released {}, {} tracks)\n'.format(album_title, release_date, num_songs)
    current_app.artist_id = str(row['artistid'])
  result.close()
    
  result2 = g.conn.execute("SELECT f.album_title, a.artist_name FROM features f, artists a WHERE f.featured_artistid=%s AND f.artistid=a.artistid", current_app.artist_id)
  album_titles2 = ''
  for row2 in result2:
    album_titles2 = album_titles2 + str(row2['album_title']) + ' by ' + str(row2['artist_name']) + '\n'
  result2.close()
      
  context = dict(artist_name=artist_name, albums=album_titles, albums_featured=album_titles2)
  return render_template("artist_results.html", **context)

@app.route('/search_genre', methods=['POST'])
def search_genre():
  """
  Search DB for albums and songs of this genre
  """

  genre = request.form['genre']
  result = g.conn.execute("SELECT album_title, artist_name FROM album_is_genre g, artists a WHERE g.artistid=a.artistid AND g.genre_name=%s", genre)
  album_titles = ''
  for r in result:
    title = r['album_title'].encode()
    artist = r['artist_name'].encode()
    album_titles = album_titles + title + ' by ' + artist + '\n'
  result.close()

  result2 = g.conn.execute("SELECT song_title, album_title, artist_name FROM song_is_genre g, artists a WHERE g.artistid=a.artistid AND g.genre_name=%s", genre)
  song_titles = ''
  for r in result2:
    song = r['song_title'].encode()
    album = r['album_title'].encode()
    artist = r['artist_name'].encode()
    song_titles = song_titles + song + ' from ' + album + ' by ' + artist + '\n'
  result2.close()

  context = dict(albums=album_titles, songs=song_titles)
  return render_template("genre_results.html", **context)
  
@app.route('/search_album', methods=['POST'])
def search_album():
  """
  Search database for songs from requested album
  """
  album_title = request.form['album_title']
  result = g.conn.execute("SELECT * FROM songs s WHERE s.artistid=%s AND s.album_title=%s;", current_app.artist_id, album_title)
  song_titles = ''
  current_app.album_title = album_title
  for row in result:
    track_number = str(row['track_num'])
    song_title = str(row['song_title'])
    song_length = str(datetime.timedelta(minutes=row['song_length'])).split(".")[0]
    song_titles = song_titles + '{}: {} ({})\n'.format(track_number, song_title, song_length)
  result.close()
  context = dict(album_title=album_title, songs=song_titles)
  return render_template("album_results.html", **context)

@app.route('/genre_album', methods=['POST'])
def genre_album():
  """
  Search database for songs from requested album
  """
  album_title = request.form['album']
  artist_name = request.form['artist']
  try:
    result = g.conn.execute("SELECT artistid FROM artists WHERE artists.artist_name=%s",artist_name)
    artist_id =''
    if(result.returns_rows):
      for r in result:
         artist_id = str(r['artistid'])
      current_app.artist_id = artist_id
      current_app.album_title = album_title
      result2 = g.conn.execute("SELECT * FROM songs s WHERE s.artistid=%s AND s.album_title=%s;", artist_id, album_title)
      song_titles = ''
      for row in result2:
        track_number = str(row['track_num'])
        song_title = str(row['song_title'])
        song_length = str(datetime.timedelta(minutes=row['song_length'])).split(".")[0]
        song_titles = song_titles + '{}: {} ({})\n'.format(track_number, song_title, song_length)
      result.close()
      context = dict(album_title=album_title, songs=song_titles)
      return render_template("album_results.html", **context)
    return render_template('album_fail.html')
  except Exception as e:
    return render_template('album_fail.html')


@app.route('/add_album', methods=['POST'])
def add_album():
  """
  Add album to current user's saved music
  """
  album_title = request.form['album_title']
  try:
    g.conn.execute('INSERT INTO album_saved_by VALUES (%s, %s, %s)', current_app.user_id, album_title, current_app.artist_id)
    return redirect('/homepage')
  except Exception as e:
    return render_template('album_fail.html')

@app.route('/rate_album', methods=['POST'])
def rate_album():
  album_title = request.form['album_title']
  rating = request.form['rating']

  try:
    g.conn.execute('INSERT INTO album_rated_by VALUES (%s, %s, %s, %s)', current_app.user_id, album_title, current_app.artist_id, rating)
    return redirect('/homepage')
  except Exception as e:
    return render_template('album_rate_fail.html')

@app.route('/delete_album', methods=['POST'])
def delete_album():
  """
  Remove album current user's saved music
  """
  album_title = request.form['album_title']
  try:
    g.conn.execute('DELETE FROM album_saved_by WHERE userid=%s AND album_title=%s AND artistid=%s;', current_app.user_id, album_title, current_app.artist_id)
    return redirect('/homepage')
  except Exception as e:
    return render_template('album_fail.html')

@app.route('/genre_add_album', methods=['POST'])
def genre_add_album():
  """
  Add album to current user's saved music
  """
  album_title = request.form['album']
  artist_name = request.form['artist']
  try:
    result = g.conn.execute("SELECT artistid FROM artists WHERE artists.artist_name=%s",artist_name)
    artist_id =''
    if(result.returns_rows):
      for r in result:
         artist_id = str(r['artistid'])
      g.conn.execute('INSERT INTO album_saved_by VALUES (%s, %s, %s)', current_app.user_id, album_title, artist_id)
      return redirect('/homepage')
    return render_template('album_fail.html')
  except Exception as e:
    return render_template('album_fail.html')


@app.route('/add_song', methods=['POST'])
def add_song():
  """
  Add song to current user's saved music
  """
  song_title = request.form['song_title']
  try:
    g.conn.execute('INSERT INTO song_saved_by VALUES (%s, %s, %s, %s)', current_app.user_id, song_title, current_app.album_title, current_app.artist_id)
    return redirect('/homepage')
  except Exception as e:
    return render_template('song_fail.html')

@app.route('/rate_song', methods=['POST'])
def rate_song():
  """
  Add song to current user's saved music
  """
  song_title = request.form['song']
  rating = request.form['rating']
  try:
    g.conn.execute('INSERT INTO song_rated_by VALUES (%s, %s, %s, %s, %s)', current_app.user_id, song_title, current_app.album_title, current_app.artist_id, rating)
    return redirect('/homepage')
  except Exception as e:
    return render_template('song_rating_fail.html')


@app.route('/suggest_song', methods=['POST'])
def suggest_song():
  """
  Add song to current user's saved music
  """
  song_title = request.form['song']
  user = request.form['user']
  try:
    g.conn.execute('INSERT INTO suggested_song VALUES (%s, %s, %s, %s, %s)', song_title, current_app.album_title, current_app.artist_id, user, current_app.user_id)
    return redirect('/homepage')
  except Exception as e:
    return render_template('song_suggest_fail.html')


@app.route('/delete_song', methods=['POST'])
def delete_song():
  """
  Delete song from current user's saved music
  """
  song_title = request.form['song_title']
  try:
    g.conn.execute('DELETE FROM song_saved_by WHERE userid=%s AND song_title=%s AND album_title= %s AND artistid=%s;', current_app.user_id, song_title, current_app.album_title, current_app.artist_id)
    return redirect('/homepage')
  except Exception as e:
    return render_template('song_fail.html')


@app.route('/genre_add_song', methods=['POST'])
def genre_add_song():
  """
  Add song to current user's saved music
  """
  song_title = request.form['song']
  album_title = request.form['album']
  artist_name = request.form['artist']
  print '@@@@@@@@@@', song_title, album_title, artist_name
  try:
    result = g.conn.execute("SELECT artistid FROM artists WHERE artists.artist_name=%s",artist_name)
    artist_id =''
    if(result.returns_rows):
      for r in result:
        artist_id = str(r['artistid'])
      print '@@@@@@@@@@', artist_id, current_app.user_id
      g.conn.execute('INSERT INTO song_saved_by VALUES (%s, %s, %s, %s)', current_app.user_id, song_title, album_title, artist_id)
      return redirect('/homepage')
    return render_template('song_fail.html')
  except Exception as e:
    return render_template('song_fail.html')

@app.route('/add_song_to_playlist', methods=['POST'])
def add_song_to_playlist():
  """
  Add song to specified playlist
  """
  song_title = request.form['song_title']
  playlist_name = request.form['playlist_name']
  try:
    result = g.conn.execute('INSERT INTO in_playlist VALUES (%s, %s, %s, %s, %s)', song_title, current_app.album_title, current_app.artist_id, playlist_name, current_app.user_id)
    return redirect('/homepage')
  except Exception as e:
     return render_template('playlist_fail.html') 

@app.route('/remove_song_from_playlist', methods=['POST'])
def remove_song_from_playlist():
  """
  Remove song from specified playlist
  """
  song_title = request.form['song_title']
  playlist_name = request.form['playlist_name']
  try:
    result = g.conn.execute('DELETE FROM in_playlist WHERE song_title=%s AND album_title= %s AND artistid=%s AND playlist_name=%s AND userid=%s;', song_title, current_app.album_title, current_app.artist_id, playlist_name, current_app.user_id)
    return redirect('/homepage')
  except Exception as e:
     return render_template('playlist_fail.html') 

@app.route('/genre_add_to_playlist', methods=['POST'])
def genre_add_to_playlist():
  """
  Add song to specified playlist
  """
  song_title = request.form['song']
  album_title = request.form['album']
  artist_name = request.form['artist']
  playlist_name = request.form['playlist_name']
  try:
    result = g.conn.execute("SELECT artistid FROM artists WHERE artists.artist_name=%s",artist_name)
    artist_id =''
    if(result.returns_rows):
      for r in result:
        artist_id = str(r['artistid'])
      print '@@@@@@@@@@', artist_id, current_app.user_id
      g.conn.execute('INSERT INTO in_playlist VALUES (%s, %s, %s, %s, %s)', song_title, album_title, artist_id, playlist_name, current_app.user_id)
      return redirect('/homepage')
    return render_template('playlist_fail.html')
  except Exception as e:
    return render_template('playlist_fail.html')



@app.route('/show_playlist_songs', methods=['POST'])
def show_playlist_songs():
  """
  Display songs in specified playlist
  """
  playlist_name = request.form['playlist_name']
  result = g.conn.execute('SELECT artist_name, song_title, album_title FROM in_playlist p, artists a WHERE p.playlist_name=%s AND p.userid=%s AND a.artistid=p.artistid', playlist_name, current_app.user_id)
  song_titles = ''
  for row in result:
    song_title = str(row['song_title'])
    album_title = str(row['album_title'])
    artist_name = str(row['artist_name'])
    print '~~~~~~~~~~~', song_title, album_title, artist_name
    song_titles = song_titles + song_title  + " from " + album_title + " by " + artist_name + "\n"
  result.close()
     
  context = dict(songs=song_titles, playlist=playlist_name)
  return render_template('playlist_results.html', **context)

@app.route('/private_playlist_create', methods=['POST'])
def private_playlist_create():
  """
  Create a new private playlist
  """
  playlist_name = request.form['playlist_name']
  try:
    g.conn.execute('INSERT INTO playlists VALUES (%s, %s, %s)', playlist_name, str(datetime.date.today()), current_app.user_id)
    g.conn.execute('INSERT INTO private_playlists VALUES (%s, %s, %s)', True, playlist_name, current_app.user_id)
    return redirect('/homepage')
  except Exception as e:
    return render_template('playlist_fail.html')

@app.route('/collab_playlist_create', methods=['POST'])
def collab_playlist_create():
  """
  Create a new collaborative playlist
  """
  playlist_name = request.form['playlist_name']
  try:
    g.conn.execute('INSERT INTO playlists VALUES (%s, %s, %s)', playlist_name, str(datetime.date.today()), current_app.user_id)
    g.conn.execute('INSERT INTO collaborative_playlists VALUES (%s, %s)', playlist_name, current_app.user_id)
    return redirect('/homepage')
  except Exception as e:
    return render_template('playlist_fail.html')

@app.route('/add_new_friend', methods=['POST'])
def add_new_friend():
  """
  Add new friend
  """
  friend = request.form['friend_id']
  try:
    g.conn.execute('INSERT INTO are_friends VALUES (%s, %s, current_date)', current_app.user_id, friend)
    return redirect('/homepage')
  except Exception as e:
    return render_template('add_new_friend_fail.html') 

@app.route('/add_collaborator', methods=['POST'])
def add_collaborator():
  """
  Add collaborator to playlist
  """
  playlist_name = request.form['playlist_name']
  userid = request.form['userid']
  try:
    g.conn.execute('INSERT INTO can_edit VALUES (%s, %s, %s)', playlist_name, current_app.user_id, userid)
    return redirect('/homepage')
  except Exception as e:
    return render_template('add_collaborator_fail.html') 

if __name__ == "__main__":
  import click

  @click.command()
  @click.option('--debug', is_flag=True)
  @click.option('--threaded', is_flag=True)
  @click.argument('HOST', default='0.0.0.0')
  @click.argument('PORT', default=8111, type=int)
  def run(debug, threaded, host, port):
    """
    This function handles command line parameters.
    Run the server using:

        python server.py

    Show the help text using:

        python server.py --help

    """

    HOST, PORT = host, port
    print "running on %s:%d" % (HOST, PORT)
    app.run(host=HOST, port=PORT, debug=debug, threaded=threaded)


  run()
