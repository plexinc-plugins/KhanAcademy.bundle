import re

####################################################################################################

VIDEO_PREFIX = '/video/khanacademy'
NAME         = 'Khan Academy'
ART          = 'art-default.jpg'
ICON         = 'icon-default.png'

BASE         = "http://www.khanacademy.org"

# YouTube
YT_VIDEO_PAGE    = 'http://www.youtube.com/watch?v=%s'
YT_VIDEO_FORMATS = ['Standard', 'Medium', 'High', '720p', '1080p']
YT_FMT           = [34, 18, 35, 22, 37]

####################################################################################################

def Start():

    Plugin.AddPrefixHandler(VIDEO_PREFIX, VideoMainMenu, NAME, ICON, ART)

    Plugin.AddViewGroup("InfoList", viewMode="InfoList", mediaType="items")
    Plugin.AddViewGroup("List", viewMode="List", mediaType="items")

    MediaContainer.art = R(ART)
    MediaContainer.title1 = NAME
    DirectoryItem.thumb = R(ICON)
    VideoItem.thumb = R(ICON)

    HTTP.CacheTime = 3600

def VideoMainMenu():

    dir = MediaContainer(viewGroup="List")

    dir.Append(Function(DirectoryItem(ByCategory,"Browse By Category...")))
    dir.Append(Function(DirectoryItem(AllCategories,"All Categories")))
    dir.Append(Function(InputDirectoryItem(ParseSearchResults,"Search ...","Search",thumb=R("icon-search.png"))))

    return dir

def ByCategory(sender, MenuLevel = 1, title=''):

    dir = MediaContainer(viewGroup="List",title2=title)
    
    if MenuLevel>1:
      parseString = '/ul/li' * (MenuLevel-1) +'[contains(.,"'+title+'")]/ul/li' 
    else:
      parseString = '/ul/li' * MenuLevel
  
    Menu = HTML.ElementFromURL('http://www.khanacademy.org/').xpath("//div[@id='browse-fixed']//nav[@class='css-menu']"+parseString)
    
    for el in Menu:
      if (el.text == None):
        link = el.xpath('.//a')[0]
        if '#' in link.get('href'):
          dir.Append(Function(DirectoryItem(Submenu, link.text.strip()), category = String.Unquote(link.get('href').replace('#',''))))
        else:
          dir.Append(Function(DirectoryItem(Submenu, link.text.strip()), category = String.Unquote(link.get('href')),TestPrep = True))
      else:
        dir.Append(Function(DirectoryItem(ByCategory, el.text.strip()), MenuLevel = MenuLevel+1, title = el.text.strip()))
    return dir


def AllCategories(sender):

    dir = MediaContainer(viewGroup="List")

    for playlist in JSON.ObjectFromURL('http://www.khanacademy.org/api/playlists'):
      dir.Append(Function(DirectoryItem(Submenu,playlist['title']),category = playlist['title'].lower().replace(' ','-')))
    return dir


def ParseSearchResults(sender, query=None):
    cookies = HTTP.GetCookiesForURL('http://www.youtube.com/')
    dir = MediaContainer(viewGroup="List", httpCookies=cookies)

    results = HTML.ElementFromURL('http://www.khanacademy.org/search?page_search_query='+query).xpath("//section[@class='videos']//dt/a")

    if results == []:
        return MessageContainer('No Results','No video file could be found for the following query: '+query)

    for video in results:
      dir.Append(Function(VideoItem(PlayVideo,video.text),link = video.get("href")))

    return dir

def GetSummary(sender,link):
    try:
      summary = HTML.ElementFromURL(BASE+link).xpath("//nav[@class='breadcrumbs_nav']")[0].text
    except:
      summary = ""
    return summary

def Submenu(sender, category, TestPrep = False):
    cookies = HTTP.GetCookiesForURL('http://www.youtube.com/')
    dir = MediaContainer(viewGroup="List", httpCookies=cookies)

    if TestPrep == False:
      Log(category)
      Category = HTML.ElementFromURL('http://www.khanacademy.org/').xpath("//div[@data-role='page' and @id='"+category+"']//h2")[0].text
      Log(Category)
      Playlist = "http://www.khanacademy.org/api/playlistvideos?playlist=%s"% String.Quote(Category)
      videolist = JSON.ObjectFromURL(Playlist)
      
      for video in videolist:
        dir.Append(Function(VideoItem(PlayVideo,video['title']),link = video['youtube_id']))
      
    else:
      if category == '/gmat':
        dir.Append(Function(DirectoryItem(Submenu, "Data Sufficiency"), category = "GMAT Data Sufficiency"))
        dir.Append(Function(DirectoryItem(Submenu, "Problem Solving"), category = "GMAT: Problem Solving"))
      if category == '/sat':
         dir.Append(Function(DirectoryItem(Submenu, "All SAT preperation courses"), category = "SAT Preparation"))
                
    return dir
 
def GetYouTubeVideo(video_id):
  yt_page = HTTP.Request(YT_VIDEO_PAGE % (video_id), cacheTime=1).content

  fmt_url_map = re.findall('"url_encoded_fmt_stream_map".+?"([^"]+)', yt_page)[0]
  fmt_url_map = fmt_url_map.replace('\/', '/').split(',')

  fmts = []
  fmts_info = {}

  for f in fmt_url_map:
    map = {}
    params = f.split('\u0026')
    for p in params:
      (name, value) = p.split('=')
      map[name] = value
    quality = str(map['itag'])
    fmts_info[quality] = String.Unquote(map['url'])
    fmts.append(quality)

  index = YT_VIDEO_FORMATS.index(Prefs['yt_fmt'])
  if YT_FMT[index] in fmts:
    fmt = YT_FMT[index]
  else:
    for i in reversed( range(0, index+1) ):
      if str(YT_FMT[i]) in fmts:
        fmt = YT_FMT[i]
        break
      else:
        fmt = 5

  url = (fmts_info[str(fmt)]).decode('unicode_escape')
  return url


def PlayVideo(sender,link):
    try:
      url = GetYouTubeVideo(link)
    except:
      url = "http://www.archive.org/download/KhanAcademy_"+link[link.find("playlist=")+9:].replace("%20",'')+"/"+link[link.find("/video/")+7:link.find("?")]+".flv"

    return Redirect(url)
