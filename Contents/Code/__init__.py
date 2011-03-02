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
    dir = MediaContainer(viewGroup = "List")

    dir.Append(Function(DirectoryItem(ByCategory,"Browse By Category...")))
    dir.Append(Function(DirectoryItem(AllCategories,"All Categories")))
    dir.Append(Function(InputDirectoryItem(ParseSearchResults,"Search ...","Search",thumb=R("icon-search.png"))))

    return dir

def ShowCategory(sender, category):
  dir = MediaContainer(viewGroup = "List")
  for video in HTML.ElementFromURL('http://www.khanacademy.org/').xpath("//h2[text()='%s']//following-sibling::ol[1]/li/a" % category):
    dir.Append(Function(VideoItem(PlayVideo,video.text),link = video.get("href")))
  return dir

def ByCategory(sender, parents=[]):
    dir = MediaContainer(viewGroup = "List")
    
    # Top level menu.
    menu = HTML.ElementFromURL('http://www.khanacademy.org/').xpath("//nav[@class='css-menu']")[0]
    
    # Get the right list.
    for index in parents:
      menu = menu.xpath('ul/li')[index]
      print "Got parent index", index, "of", menu
    
    # All all the items.
    i = 0
    for item in menu.xpath("ul/li"):
      if item.text:
        # Submenu.
        title = item.text.strip()
        dir.Append(Function(DirectoryItem(ByCategory, title), parents = parents + [i]))
      else:
        # Category.
        category = item.xpath('a')[0]
        title = category.text
        dir.Append(Function(DirectoryItem(ShowCategory, title), category = title))
      i += 1
      
    return dir

def AllCategories(sender):

    dir = MediaContainer(viewGroup="List")

    for cat in HTML.ElementFromURL('http://www.khanacademy.org/').xpath("//h2[@class='playlist-heading ']"):
      dir.Append(Function(DirectoryItem(Submenu,cat.text),category = cat.text))

    return dir


def ParseSearchResults(sender, query=None):
    cookies = HTTP.GetCookiesForURL('http://www.youtube.com/')
    dir = MediaContainer(viewGroup="InfoList", httpCookies=cookies)

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

    if TestPrep == False :
      html = HTTP.Request('http://www.khanacademy.org/').content.replace('></A>','>').replace('<div class="clear"></div>','</A>')
      videolist = HTML.ElementFromString(html).xpath("//a[@name='"+category+"']/ol//a")
    else:
      html = HTTP.Request('http://www.khanacademy.org'+category).content
      if category == '/gmat':
        videolist = HTML.ElementFromString(html).xpath("//center/table[@cellpadding=0]//a[@href!='#']")
      else:
        videolist = HTML.ElementFromString(html).xpath("//div[@id='accordion']//a[@href!='#']")
      
    for video in videolist:
      dir.Append(Function(VideoItem(PlayVideo,video.text),link = video.get("href")))
                 
    return dir
 
def GetYouTubeVideo(video_id):
  yt_page = HTTP.Request(YT_VIDEO_PAGE % (video_id), cacheTime=1).content

  fmt_url_map = re.findall('"fmt_url_map".+?"([^"]+)', yt_page)[0]
  fmt_url_map = fmt_url_map.replace('\/', '/').split(',')

  fmts = []
  fmts_info = {}

  for f in fmt_url_map:
    (fmt, url) = f.split('|')
    fmts.append(fmt)
    fmts_info[str(fmt)] = url

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

  url = fmts_info[str(fmt)]
  return url

def PlayVideo(sender,link):
    try:
      ytid = HTML.ElementFromURL(BASE+link).xpath("//option[@selected]")[0].get("value")
      url = GetYouTubeVideo(ytid)
    except:
      url = "http://www.archive.org/download/KhanAcademy_"+link[link.find("playlist=")+9:].replace("%20",'')+"/"+link[link.find("/video/")+7:link.find("?")]+".flv"

    return Redirect(url)
