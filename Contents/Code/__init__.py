NAME = 'Khan Academy'
BASE = 'http://www.khanacademy.org/library'
TOPIC = 'http://www.khanacademy.org/api/v1/topic/%s'
SEARCH = 'http://www.khanacademy.org/search?page_search_query='

####################################################################################################
def Start():

    ObjectContainer.title1 = NAME
    HTTP.CacheTime = CACHE_1HOUR

####################################################################################################
@handler('/video/khanacademy', NAME)
def MainMenu():

    oc = ObjectContainer()

    oc.add(DirectoryObject(key = Callback(ByCategory), title = 'Browse By Category'))
    oc.add(DirectoryObject(key = Callback(AllCategories), title = 'All Categories'))

    return oc

####################################################################################################
# This function gets the main category headings from the main page
@route('/video/khanacademy/bycategory')
def ByCategory():

	oc = ObjectContainer()
	page = HTML.ElementFromURL(BASE)
	showList = page.xpath('//span[@class="span12"]/ul/li/h2')

	for s in showList:
		
		topic_name = s.xpath('@class')[0].replace('domain-header ', '')
		show = s.xpath('a/text()')[0]

		oc.add(DirectoryObject(key = Callback(Topics, topic_name=topic_name, title=show), title = show))

	return oc

####################################################################################################
# This function either pulls the topic or video API
# The playlist API no longer works for these categories so you have to use the topic API
# There can be several layers of subtopics and the '/videos' extension will not work unless there are no more subtopic for that section 
# It would be nice if there were some way of knowing whether or not the next level will contain more topics or videos but there is not
# TRIED USING THE BROWSER FIELD WHICH SEEMED TO BE FALSE THE LEVEL BEFORE VIDEOS BUT THIS DOES NOT WORK WITH ALL
# They do not seem to mix videos and topics, so for now I check the first entry to see if it is of the kind Topic
@route('/video/khanacademy/topics')
def Topics(title, topic_name):

    oc = ObjectContainer(title2=title)
    playlists = JSON.ObjectFromURL(TOPIC %topic_name)
    render_type = playlists['render_type']
    Log('the value of render_type is %s' %render_type)


    if render_type != 'Tutorial':
        for child in playlists['children']:
            child_type = child['kind']
            if child_type == 'Topic':
                title = child['title']
                child_topic = child['id']
                # Found one that has a id but gives an error and the url for that one is 'http://www.khanacademy.org/None'
                # So this is a check to make sure there is a web page and videos for this subject
                child_url = child['url']
                if child_topic not in child_url:
                    continue
                oc.add(DirectoryObject(
                    key = Callback(Topics, topic_name = child_topic, title = title), 
                    title = title))
            else:
                pass
    else:
        playlists = JSON.ObjectFromURL(TOPIC %topic_name + '/videos')

        for video in playlists:
            oc.add(VideoClipObject(
                url = video['url'],
                title = video['title'],
                summary = video['description'],
                duration = video['duration'] * 1000,
                originally_available_at = Datetime.ParseDate(video['date_added'].split('Z')[0])
            ))

    return oc
####################################################################################################
@route('/video/khanacademy/allcategories')
def AllCategories():

    oc = ObjectContainer()
    playlists = JSON.ObjectFromURL('http://www.khanacademy.org/api/playlists')

    for playlist in playlists:
        oc.add(DirectoryObject(
            key = Callback(Submenu, category = playlist['title'].lower().replace(' ','-'), api_url = playlist['api_url']), 
            title = playlist['title']))

    return oc

####################################################################################################
@route('/video/khanacademy/submenu')
def Submenu(category, api_url = ''):

    oc = ObjectContainer()

    playlist = JSON.ObjectFromURL(api_url)

    for video in playlist:
        oc.add(VideoClipObject(
            url = video['youtube_url'],
            title = video['title'],
            summary = video['description'],
            originally_available_at = Datetime.ParseDate(video['date_added'].split('T')[0]),
            tags = [tag.strip() for tag in video['keywords'].split(',')]
        ))

    return oc
