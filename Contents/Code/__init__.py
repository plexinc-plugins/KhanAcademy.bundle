import re

####################################################################################################

VIDEO_PREFIX = '/video/khanacademy'
NAME         = 'Khan Academy'
ART          = 'art-default.jpg'
ICON         = 'icon-default.png'

BASE         = 'http://www.khanacademy.org'

####################################################################################################
def Start():

    Plugin.AddPrefixHandler(VIDEO_PREFIX, MainMenu, NAME, ICON, ART)
    Plugin.AddViewGroup("InfoList", viewMode="InfoList", mediaType="items")
    Plugin.AddViewGroup("List", viewMode="List", mediaType="items")

    ObjectContainer.title1 = NAME
    ObjectContainer.view_group = 'List'
    ObjectContainer.art = R(ART)
      
    DirectoryObject.thumb = R(ICON)
    DirectoryObject.art = R(ART)
    VideoClipObject.thumb = R(ICON)
    VideoClipObject.art = R(ART)

    HTTP.CacheTime = 3600

####################################################################################################
def MainMenu():
    oc = ObjectContainer()

    oc.add(DirectoryObject(key = Callback(ByCategory), title = 'Browse By Category...'))
    oc.add(DirectoryObject(key = Callback(AllCategories), title = 'All Categories'))
    oc.add(InputDirectoryObject(key = Callback(ParseSearchResults), title = 'Search...', prompt = 'Search for Videos'))

    return oc

####################################################################################################
def ByCategory(level = 1, title = ''):
    oc = ObjectContainer(title2 = title)
    
    if level > 1:
      parse_string = '/ul/li' * (level - 1) + '[contains(.,"' + title + '")]/ul/li' 
    else:
      parse_string = '/ul/li' * level

    page = HTML.ElementFromURL('http://www.khanacademy.org/')
    elements = page.xpath("//div[@id='browse-fixed']//nav[@class='css-menu']" + parse_string)
    
    for el in elements:
      if (el.text == None):
        link = el.xpath('.//a')[0]
        if '#' in link.get('href'):
          category = String.Unquote(link.get('href').replace('#',''))
          oc.add(DirectoryObject(key = Callback(Submenu, category = category), title = link.text.strip()))
        else:
          category = String.Unquote(link.get('href'))
          oc.add(DirectoryObject(key = Callback(Submenu, category = category, test_prep = True), title = link.text.strip()))
      else:
        title = el.text.strip()
        oc.add(DirectoryObject(key = Callback(ByCategory, title = title, level = level + 1), title = title))

    return oc

####################################################################################################
def AllCategories():
    oc = ObjectContainer()

    playlists = JSON.ObjectFromURL('http://www.khanacademy.org/api/playlists')
    for playlist in playlists:
      oc.add(DirectoryObject(
        key = Callback(Submenu, category = playlist['title'].lower().replace(' ','-'), api_url = playlist['api_url']), 
        title = playlist['title']))

    return oc

####################################################################################################
def ParseSearchResults(query = 'math'):
    oc = ObjectContainer()

    page = HTML.ElementFromURL('http://www.khanacademy.org/search?page_search_query=' + query)
    results = page.xpath("//li[@class='videos']")

    for video in results:
      url = BASE + video.xpath(".//a")[0].get('href')
      title = video.xpath(".//span/text()")[0]
      summary = video.xpath(".//p/text()")[0]
      oc.add(VideoClipObject(url = url, title = title, summary = summary))

    if len(oc) == 0:
      return MessageContainer("No Results", 'No video file could be found for the following query: ' + query)

    return oc

####################################################################################################
def Submenu(category, api_url = None, test_prep = False):
    oc = ObjectContainer()

    if test_prep == False:
      if api_url == None:
        page = HTML.ElementFromURL('http://www.khanacademy.org/')
        playlist_category = page.xpath("//div[@data-role='page' and @id='" + category + "']//h2")[0].text
        api_url = "http://www.khanacademy.org/api/playlistvideos?playlist=%s" % String.Quote(playlist_category)
      
      playlist = JSON.ObjectFromURL(api_url)
      
      for video in playlist:
        oc.add(VideoClipObject(
          url = video['youtube_url'],
          title = video['title'],
          summary = video['description'],
          originally_available_at = Datetime.ParseDate(video['date_added'].split('T')[0]),
          tags = [tag.strip() for tag in video['keywords'].split(',')]))
      
    else:
      if category == '/gmat':
        oc.add(DirectoryObject(key = Callback(Submenu, category = "GMAT Data Sufficiency"), title = "Data Sufficiency"))
        oc.add(DirectoryObject(key = Callback(Submenu, category = "GMAT: Problem Solving"), title = "Problem Solving"))
      if category == '/sat':
        oc.add(DirectoryObject(key = Callback(Submenu, category = "SAT Preparation"), title = "All SAT preperation courses"))
                
    return oc

