# -*- coding: utf-8 -*-

# Debug
Debug = True

# Imports
import sys, urllib, urllib2, base64, simplejson, BeautifulSoup
import hashlib, os, shutil, tempfile, time, errno
import xbmc, xbmcgui, xbmcplugin, xbmcaddon

__addon__ = xbmcaddon.Addon(id='plugin.video.imdb.trailers')
__info__ = __addon__.getAddonInfo
__plugin__ = __info__('name')
__version__ = __info__('version')
__icon__ = __info__('icon')
__fanart__ = __info__('fanart')
__cachedir__ = __info__('profile')
__language__ = __addon__.getLocalizedString
__settings__ = __addon__.getSetting

CACHE_1MINUTE = 60
CACHE_1HOUR = 3600
CACHE_1DAY = 86400
CACHE_1WEEK = 604800
CACHE_1MONTH = 2592000

CACHE_TIME = CACHE_1HOUR

TRAILERS = "http://www.imdb.com/features/video/trailers"
CONTENT_URL = "http://www.imdb.com/video/trailers/data/_json?list=%s"
DETAILS_PAGE = "http://www.imdb.com/video/imdb/%s/html5?format=%s"
# tormovies.org mailwarn
MAILWARN = "http://tormovies.org/frontend_dev.php/mailwarn/create"

# Fanart
xbmcplugin.setPluginFanart(int(sys.argv[1]), __fanart__)

# Main
class Main:
  def __init__(self):
    if ("action=list" in sys.argv[2]):
      self.VideoList()
    elif ("action=play" in sys.argv[2]):
      self.Play()
    elif ("action=download" in sys.argv[2]):
      self.Download()
    elif ("action=couchpotato" in sys.argv[2]):
      self.CouchPotato()
    elif ("action=tormovies" in sys.argv[2]):
      self.TorMovies()
    else:
      self.MainMenu()

  def MainMenu(self):
    if Debug: self.LOG('MainMenu()')
    category = [{'title':__language__(30201), 'key':'top_hd'},
                {'title':__language__(30202), 'key':'recent'},
                {'title':__language__(30203), 'key':'popular'}]
    for i in category:
      listitem = xbmcgui.ListItem(i['title'], iconImage='DefaultFolder.png', thumbnailImage=__icon__)
      parameters = '%s?action=list&key=%s' % (sys.argv[0], i['key'])
      xbmcplugin.addDirectoryItems(int(sys.argv[1]), [(parameters, listitem, True)])
    # Sort methods and content type...
    xbmcplugin.addSortMethod(handle=int(sys.argv[1]), sortMethod=xbmcplugin.SORT_METHOD_NONE)
    # End of directory...
    xbmcplugin.endOfDirectory(int(sys.argv[1]), True)

  def VideoList(self):
    if Debug: self.LOG('VideoList()')
    try:
      token = self.Arguments('token')
    except:
      token = ''
    contentUrl = CONTENT_URL % self.Arguments('key') + '&token=%s' % token
    content = simplejson.loads(fetcher.fetch(contentUrl, CACHE_TIME))
    totalItems = content['video_count']
    for video in content['videos']:
      videoId = video['video']
      try:
        thumb = video['poster'].replace('_V1_', '_V1_SY380_')
      except:
        thumb = 'http://i.media-imdb.com/images/nopicture/large/film_hd-gallery.png'
      title = unicode(video['title_title'])
      imdbID = video['title']
      duration = video['duration']
      titleData = BeautifulSoup.BeautifulSoup(video['title_data'])
      summary = ''
      if len(titleData('div', 't-o-d-text-block t-o-d-plot')) > 0:
        summary = titleData('div', 't-o-d-text-block t-o-d-plot')[0].span.string
      rating = float('0.0')
      if len(titleData('span', 't-o-d-rating-value')) > 0:
        rating = float(titleData('span', 't-o-d-rating-value')[0].string)
      year = ''
      if len(titleData('span', 't-o-d-year')[0].string) > 0:
        year = titleData('span', 't-o-d-year')[0].string.replace('(', '').replace(')', '')
      director = ''
      if len(titleData('div', {'class':'t-o-d-text-block'})[0].a) > 0:
        director = titleData('div', {'class':'t-o-d-text-block'})[0].a.string

      listitem = xbmcgui.ListItem(title, iconImage='DefaultVideo.png', thumbnailImage=thumb)
      listitem.setInfo(type='video',
                       infoLabels={'title' : title,
                                   'plot' : summary,
                                   'year' : int(year),
                                   'rating' : rating,
                                   'duration' : str(duration),
                                   'director' : str(director)
                                   })
      # dummy context menu variable
      contextmenu = []
      if __settings__('couchpotato') == 'true':
        contextmenu += [(__language__(30101), 'XBMC.RunPlugin(%s?action=couchpotato&imdbid=%s&year=%s)' % (sys.argv[0], imdbID, year))]
      if __settings__('tormovies') == 'true':
        contextmenu += [(__language__(30106), 'XBMC.RunPlugin(%s?action=tormovies&imdbid=%s)' % (sys.argv[0], imdbID))]      
      listitem.addContextMenuItems(contextmenu, replaceItems=False)
      parameters = '%s?action=play&videoid=%s' % (sys.argv[0], videoId)
      xbmcplugin.addDirectoryItem(int(sys.argv[1]), parameters, listitem, False, totalItems)
    # Sort methods and content type...
    listitem = xbmcgui.ListItem(__language__(30204), iconImage='DefaultVideo.png', thumbnailImage=__icon__)
    parameters = '%s?action=list&key=%s&token=%s' % (sys.argv[0], self.Arguments('key'), content['next_token'])
    xbmcplugin.addDirectoryItem(int(sys.argv[1]), parameters, listitem, True)
    xbmcplugin.setContent(int(sys.argv[1]), 'movies')
    xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_UNSORTED)
    xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_VIDEO_TITLE)
    xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_VIDEO_RUNTIME)
    xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_VIDEO_RATING)
    # End of directory...
    xbmcplugin.endOfDirectory(int(sys.argv[1]), True)

  def getVideoURL(self):
    if Debug: self.LOG('getVideoURL()')
    getformat = __settings__("video_quality")
    if getformat == '0': format = '240p'
    if getformat == '1': format = '480p'
    if getformat == '2': format = '720p'
    detailsUrl = DETAILS_PAGE % (self.Arguments('videoid'), format)
    if Debug: self.LOG("DetailsURL:" + detailsUrl)
    details = urllib2.urlopen(detailsUrl).read()
    index = details.find('mp4_h264')
    start = details.find('http', index)
    end = details.find("'", start)
    videoUrl = details[start:end]
    if Debug: self.LOG("VideoURL:" + videoUrl)
    return videoUrl

  def Play(self):
    if Debug: self.LOG('Play()')
    title = unicode(xbmc.getInfoLabel("ListItem.Title"), "utf-8")
    thumbnail = xbmc.getInfoImage("ListItem.Thumb")
    plot = unicode(xbmc.getInfoLabel("ListItem.Plot"), "utf-8")
    # only need to add label, icon and thumbnail, setInfo() and addSortMethod() takes care of label2
    listitem = xbmcgui.ListItem(title, iconImage="DefaultVideo.png", thumbnailImage=thumbnail)
    # set the key information
    listitem.setInfo('video', {'title' : title,
                               'label' : title,
                               'plot' : plot,
                               'plotOutline' : plot })
    xbmc.Player().play(self.getVideoURL(), listitem)

  def Download(self):
    #title = unicode(xbmc.getInfoLabel("ListItem.Title"), "utf-8") + ' - [Trailer]'
    #self.getVideoURL()
    pass

  def CouchPotato(self):
    if Debug: self.LOG('CouchPotato(): Adding to CouchPotato')
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

    imdbID = self.Arguments('imdbid')
    year = self.Arguments('year')

    try:
      query_args = { 'id':imdbID, 'year':year }
      post_args = { 'quality':ret + 1, 'add':'Add' }

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

  def TorMovies(self):
    if Debug: self.LOG('TorMovies(): Adding to TorMovies Mail Warn')
    def _onoff(s):
      if s == 'true':
        return 'on'
      else:
        return 'off'
      
    query = { 'mail_warn[id]':'',  
              'mail_warn[movie_id]':self.Arguments('imdbid'),
              'mail_warn[bdrip]':_onoff(__settings__('tm_bdrip')),
              'mail_warn[dvdrip]':_onoff(__settings__('tm_dvdrip')),
              'mail_warn[r5]':_onoff(__settings__('tm_r5')),
              'mail_warn[screener]':_onoff(__settings__('tm_screener')),
              'mail_warn[verified]':_onoff(__settings__('tm_verified')),
              'mail_warn[min_size]':__settings__('tm_min_size'),
              'mail_warn[max_size]':__settings__('tm_max_size'),
              'mail_warn[min_seeders]':__settings__('tm_min_seeders'),
              'mail_warn[email]':__settings__('tm_email'),}
    
    encoded_args = urllib.urlencode(query)
    send = urllib.urlopen(MAILWARN, encoded_args)
    if send.read().find('Success !'):
      xbmc.executebuiltin("Notification(%s, %s)" % (__language__(30106).encode('utf-8', 'ignore'), __language__(30107).encode('utf-8', 'ignore')))
    else:
      xbmc.executebuiltin("Notification(%s, %s, 6000)" % (__language__(30106).encode('utf-8', 'ignore'), __language__(30105).encode('utf-8', 'ignore')))
  
  def Arguments(self, arg):
    Arguments = dict(part.split('=') for part in sys.argv[2][1:].split('&'))
    return urllib.unquote_plus(Arguments[arg])

  def LOG(self, description):
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
        if Debug: print 'file exists and reading from cache.'
        return open(filepath).read()
    # Retrieve over HTTP and cache, using rename to avoid collisions
    if Debug: print 'file not yet cached or cache time expired. File reading from URL and try to cache to disk'
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