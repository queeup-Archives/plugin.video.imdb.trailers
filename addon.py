# -*- coding: utf-8 -*-

# Imports
import hashlib
import os
import shutil
import tempfile
import time
import errno
import sys
import urllib
import urllib2
import base64
import simplejson
import xbmc
import xbmcgui
import xbmcplugin
import xbmcaddon

# DEBUG
DEBUG = False

__addon__ = xbmcaddon.Addon()
__plugin__ = __addon__.getAddonInfo('name')
__version__ = __addon__.getAddonInfo('version')
__icon__ = __addon__.getAddonInfo('icon')
__fanart__ = __addon__.getAddonInfo('fanart')
__cachedir__ = __addon__.getAddonInfo('profile')
__language__ = __addon__.getLocalizedString
__settings__ = __addon__.getSetting

CACHE_1MINUTE = 60
CACHE_1HOUR = 3600
CACHE_1DAY = 86400
CACHE_1WEEK = 604800
CACHE_1MONTH = 2592000

CACHE_TIME = CACHE_1HOUR

MAIN_URL = 'http://www.imdb.com'
CONTENT_URL = 'http://www.imdb.com/video/trailers/data/_ajax/adapter/shoveler?list=%s&debug=0'
DETAILS_PAGE = "http://www.imdb.com/video/imdb/%s/html5?format=%s"
# tormovies.org mailwarn
MAILWARN = "http://tormovies.org/frontend_dev.php/mailwarn/create"

# Fanart
xbmcplugin.setPluginFanart(int(sys.argv[1]), __fanart__)


# Main
class Main:
  def __init__(self):
    if ("action=list" in sys.argv[2]):
      self.list_contents()
    elif ("action=play" in sys.argv[2]):
      self.play()
    elif ("action=couchpotato" in sys.argv[2]):
      self.couchpotato()
    elif ("action=_couchpotatoserver" in sys.argv[2]):
      self.couchpotatoserver()
    elif ("action=tormovies" in sys.argv[2]):
      self.tormovies()
    else:
      self.main_menu()

  def main_menu(self):
    if DEBUG:
      self.log('main_menu()')
    category = [{'title':__language__(30201), 'key':'recent'},
                {'title':__language__(30202), 'key':'top_hd'},
                {'title':__language__(30203), 'key':'popular'}]
    for i in category:
      listitem = xbmcgui.ListItem(i['title'], iconImage='DefaultFolder.png', thumbnailImage=__icon__)
      listitem.setProperty('fanart_image', __fanart__)
      parameters = '%s?action=list&key=%s' % (sys.argv[0], i['key'])
      xbmcplugin.addDirectoryItems(int(sys.argv[1]), [(parameters, listitem, True)])
    # Sort methods and content type...
    xbmcplugin.addSortMethod(handle=int(sys.argv[1]), sortMethod=xbmcplugin.SORT_METHOD_NONE)
    # End of directory...
    xbmcplugin.endOfDirectory(int(sys.argv[1]), True)

  def list_contents(self):
    if DEBUG:
      self.log('content_list()')
    try:
      contentUrl = self.arguments('next_page')
    except:
      contentUrl = CONTENT_URL % self.arguments('key')
    content = simplejson.loads(fetcher.fetch(contentUrl, CACHE_TIME))
    try:
      next_page_url = MAIN_URL + content['model']['next']
      next_page = True
    except:
      next_page = False
    for video in content['model']['items']:
      plot = video['overview']['plot']
      if not plot:
        plot = ''
      # Check how to genre list
      genres = video['overview']['genres'][0]
      mpaa = video['overview']['certificate']
      if not mpaa:
        mpaa = ''
      rating = video['overview']['user_rating']
      if not rating:
        rating = 0
      # Check empty and list director list
      directors = video['overview']['directors']
      if len(directors) > 1:
        directors = '%s, %s' % (directors[0], directors[1])
      elif len(directors) < 1:
        directors = ''
      else:
        directors = directors[0]
      stars = video['overview']['stars']
      duration = video['video']['duration']['string']
      fanart = video['video']['slateUrl']
      videoId = video['video']['videoId']
      title = video['display']['text']
      year = video['display']['year']
      imdbID = video['display']['titleId']
      poster = video['display']['poster']['url'].split('_V1._')[0] + '_V1._SY512_.jpg'

      listitem = xbmcgui.ListItem(title, iconImage='DefaultVideo.png', thumbnailImage=poster)
      listitem.setProperty('fanart_image', fanart)
      listitem.setInfo(type='video',
                       infoLabels={'title': title,
                                   'plot': plot,
                                   'genre': genres,
                                   'year': int(year),
                                   'rating': float(rating),
                                   'mpaa': mpaa,
                                   'duration': str(duration),
                                   'director': directors.encode('utf-8', 'ignore'),
                                   'cast': stars})
      # dummy context menu variable
      contextmenu = []
      if __settings__('couchpotato') == 'true':
        contextmenu += [(__language__(30101), 'XBMC.RunPlugin(%s?action=couchpotato&imdbid=%s&year=%s)' % (sys.argv[0], imdbID, year))]
      if __settings__('couchpotatoserver') == 'true':
        contextmenu += [(__language__(30108), 'XBMC.RunPlugin(%s?action=_couchpotatoserver&imdbid=%s)' % (sys.argv[0], imdbID))]
      if __settings__('tormovies') == 'true':
        contextmenu += [(__language__(30106), 'XBMC.RunPlugin(%s?action=tormovies&imdbid=%s)' % (sys.argv[0], imdbID))]
      listitem.addContextMenuItems(contextmenu, replaceItems=False)
      parameters = '%s?action=play&videoid=%s' % (sys.argv[0], videoId)
      xbmcplugin.addDirectoryItem(int(sys.argv[1]), parameters, listitem, False)
    # Sort methods and content type...
    if next_page:
      listitem = xbmcgui.ListItem(__language__(30204), iconImage='DefaultVideo.png', thumbnailImage=__icon__)
      listitem.setProperty('fanart_image', __fanart__)
      parameters = '%s?action=list&next_page=%s' % (sys.argv[0], urllib.quote_plus(next_page_url))
      xbmcplugin.addDirectoryItem(int(sys.argv[1]), parameters, listitem, True)
    xbmcplugin.setContent(int(sys.argv[1]), 'movies')
    xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_UNSORTED)
    xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_VIDEO_TITLE)
    xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_VIDEO_RUNTIME)
    xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_VIDEO_RATING)
    # End of directory...
    xbmcplugin.endOfDirectory(int(sys.argv[1]), True)

  def get_video_url(self):
    if DEBUG:
      self.log('get_video_url()')
    quality = __settings__("video_quality")
    detailsUrl = DETAILS_PAGE % (self.arguments('videoid'), quality)
    if DEBUG:
      self.log('detailsURL: %s' % detailsUrl)
    details = urllib2.urlopen(detailsUrl).read()
    index = details.find('mp4_h264')
    start = details.find('http', index)
    end = details.find("'", start)
    videoUrl = details[start:end]
    if DEBUG:
      self.log('videoURL: %s' % videoUrl)
    return videoUrl

  def play(self):
    if DEBUG:
      self.log('play()')
    title = unicode(xbmc.getInfoLabel("ListItem.Title"), "utf-8")
    thumbnail = xbmc.getInfoImage("ListItem.Thumb")
    plot = unicode(xbmc.getInfoLabel("ListItem.Plot"), "utf-8")
    # only need to add label, icon and thumbnail, setInfo() and addSortMethod() takes care of label2
    listitem = xbmcgui.ListItem(title, iconImage="DefaultVideo.png", thumbnailImage=thumbnail)
    # set the key information
    listitem.setInfo('video', {'title': title,
                               'label': title,
                               'plot': plot,
                               'plotOutline': plot})
    xbmc.Player().play(self.get_video_url(), listitem)

  def couchpotato(self):
    if DEBUG:
      self.log('couchpotato(): Adding to CouchPotato')
    # Quality Dialog
    dialog = xbmcgui.Dialog()
    ret = dialog.select('Choose a quality', ['1080p', '720p', 'BR-Rip', 'DVD-Rip', 'R5', 'Screener', 'DVD-R', 'Cam', 'TeleSync', 'TeleCine'])

    ip = __settings__('cpIP')
    port = __settings__('cpPort')
    u = __settings__('cpUser')
    p = __settings__('cpPass')

    header = {}
    if u and p:
      header = {'Authorization': 'Basic ' + base64.b64encode(u + ':' + p)}

    imdbID = self.arguments('imdbid')
    year = self.arguments('year')

    try:
      query_args = {'id': imdbID, 'year': year}
      post_args = {'quality': ret + 1, 'add': 'Add'}

      encoded_query_args = urllib.urlencode(query_args)
      encoded_post_args = urllib.urlencode(post_args)

      request = urllib2.Request('http://%s:%s/movie/imdbAdd/?%s' % (ip, port, encoded_query_args), encoded_post_args, header)
      add = urllib2.urlopen(request)

      if add.read().find('added!'):
        xbmc.executebuiltin("Notification(%s, %s)" % (__language__(30101).encode('utf-8', 'ignore'), __language__(30102).encode('utf-8', 'ignore')))
      else:
        xbmc.executebuiltin("Notification(%s, %s, 6000)" % (__language__(30101).encode('utf-8', 'ignore'), __language__(30103).encode('utf-8', 'ignore')))
    except urllib2.URLError, e:
      if e.code == 401:
        xbmc.executebuiltin("Notification(%s, %s, 6000)" % (__language__(30101).encode('utf-8', 'ignore'), __language__(30104).encode('utf-8', 'ignore')))
      else:
        xbmc.executebuiltin("Notification(%s, %s, 6000)" % (__language__(30101).encode('utf-8', 'ignore'), __language__(30105).encode('utf-8', 'ignore')))

  def couchpotatoserver(self):
    if DEBUG:
      self.log('couchpotatoserver(): Adding to CouchPotatoServer')

    ip = __settings__('cpsIP')
    port = __settings__('cpsPort')
    u = __settings__('cpsUser')
    p = __settings__('cpsPass')
    imdbID = self.arguments('imdbid')

    def get_api_key():
      if u and p:
        apikey_url = 'http://%s:%s/getkey/?p=%s&u=%s' % (ip, port, self.md5(p), self.md5(u))
      else:
        apikey_url = 'http://%s:%s/getkey/' % (ip, port)
      get_apikey = simplejson.load(urllib.urlopen(apikey_url))
      if get_apikey['success']:
        return get_apikey['api_key']
      else:
        self.log('Error on geting apikey!')

    query_args = {'identifier': imdbID}
    encoded_query_args = urllib.urlencode(query_args)
    request = urllib2.Request('http://%s:%s/api/%s/movie.add/?%s' % (ip, port, get_api_key(), encoded_query_args))
    add = urllib2.urlopen(request)
    if simplejson.load(add)['success']:
      xbmc.executebuiltin("Notification(%s, %s)" % (__language__(30108).encode('utf-8', 'ignore'), __language__(30109).encode('utf-8', 'ignore')))
    else:
      xbmc.executebuiltin("Notification(%s, %s, 6000)" % (__language__(30108).encode('utf-8', 'ignore'), __language__(30110).encode('utf-8', 'ignore')))

  def tormovies(self):
    if DEBUG:
      self.log('tormovies(): Adding to TorMovies Mail Warn')

    def _onoff(s):
      if s == 'true':
        return 'on'
      else:
        return 'off'

    query = {'mail_warn[id]': '',
             'mail_warn[movie_id]': self.arguments('imdbid'),
             'mail_warn[bdrip]': _onoff(__settings__('tm_bdrip')),
             'mail_warn[dvdrip]': _onoff(__settings__('tm_dvdrip')),
             'mail_warn[r5]': _onoff(__settings__('tm_r5')),
             'mail_warn[screener]': _onoff(__settings__('tm_screener')),
             'mail_warn[verified]': _onoff(__settings__('tm_verified')),
             'mail_warn[min_size]': __settings__('tm_min_size'),
             'mail_warn[max_size]': __settings__('tm_max_size'),
             'mail_warn[min_seeders]': __settings__('tm_min_seeders'),
             'mail_warn[email]': __settings__('tm_email'), }

    encoded_args = urllib.urlencode(query)
    send = urllib.urlopen(MAILWARN, encoded_args)
    if send.read().find('Success !'):
      xbmc.executebuiltin("Notification(%s, %s)" % (__language__(30106).encode('utf-8', 'ignore'), __language__(30107).encode('utf-8', 'ignore')))
    else:
      xbmc.executebuiltin("Notification(%s, %s, 6000)" % (__language__(30106).encode('utf-8', 'ignore'), __language__(30105).encode('utf-8', 'ignore')))

  def md5(self, _string):
    return hashlib.md5(str(_string)).hexdigest()

  def arguments(self, arg):
    _arguments = dict(part.split('=') for part in sys.argv[2][1:].split('&'))
    return urllib.unquote_plus(_arguments[arg])

  def log(self, description):
    xbmc.log("[ADD-ON] '%s v%s': %s" % (__plugin__, __version__, description), xbmc.LOGNOTICE)


class DiskCacheFetcher:
  def __init__(self, cache_dir=None):
    # If no cache directory specified, use system temp directory
    if cache_dir is None:
      cache_dir = tempfile.gettempdir()
    if not os.path.exists(cache_dir):
      try:
        os.mkdir(cache_dir)
      except OSError, e:
        if e.errno == errno.EEXIST and os.path.isdir(cache_dir):
          # File exists, and it's a directory,
          # another process beat us to creating this dir, that's OK.
          pass
        else:
          # Our target dir is already a file, or different error,
          # relay the error!
          raise
    self.cache_dir = cache_dir

  def fetch(self, url, max_age=CACHE_TIME):
    # Use MD5 hash of the URL as the filename
    filename = hashlib.md5(url).hexdigest()
    filepath = os.path.join(self.cache_dir, filename)
    if os.path.exists(filepath):
      if int(time.time()) - os.path.getmtime(filepath) < max_age:
        if DEBUG:
          print 'file exists and reading from cache.'
        return open(filepath).read()
    # Retrieve over HTTP and cache, using rename to avoid collisions
    if DEBUG:
      print 'file not yet cached or cache time expired. File reading from URL and try to cache to disk'
    data = urllib2.urlopen(url).read()
    fd, temppath = tempfile.mkstemp()
    fp = os.fdopen(fd, 'w')
    fp.write(data)
    fp.close()
    shutil.move(temppath, filepath)
    return data

fetcher = DiskCacheFetcher(xbmc.translatePath(__cachedir__))

if __name__ == '__main__':
  Main()