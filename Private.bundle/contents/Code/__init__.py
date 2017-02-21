import urllib
import urllib2 as urllib
from cStringIO import StringIO
from datetime import datetime
from PIL import Image

CONSTS = {
    'SearchUrl': 'http://www.private.com/search.php?query='
}
def posterAlreadyExists(posterUrl,metadata):
    pUrl = posterUrl.lower().split("?")[0]
    for p in metadata.posters.keys():
        if p.lower() == pUrl:
            Log("Found " + posterUrl + " in posters collection")
            return True

    for p in metadata.art.keys():
        if p.lower() == pUrl:
            return True
    return False
  
def Start():
  HTTP.CacheTime = CACHE_1DAY
  HTTP.SetHeader('User-agent', 'Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 6.2; Trident/4.0; SLCC2; .NET CLR 2.0.50727; .NET CLR 3.5.30729; .NET CLR 3.0.30729; Media Center PC 6.0)')

class ADEAgent(Agent.Movies):
  name = 'Private'
  languages = [Locale.Language.English]
  primary_provider = True


  def search(self, results, media, lang):
    
    Log("SEARCH CALLED")
    title = media.name
    if media.primary_metadata is not None:
      title = media.primary_metadata.title

    year = media.year
    if media.primary_metadata is not None:
      year = media.primary_metadata.year

    if "http://" not in title:
        encodedTitle = title.replace(" ","+").replace(",","%2C")
        searchResults = HTML.ElementFromURL(CONSTS["SearchUrl"] + encodedTitle)
        Log(HTML.StringFromElement(searchResults))
        for s in searchResults.xpath('//h3/a'):

            itemTitle = s.text_content().strip()
            itemLink = s.get("href").replace("/","_")
            score = 100 - Util.LevenshteinDistance(title.lower(), itemTitle.lower())
            results.Append(MetadataSearchResult(id = itemLink, name = itemTitle, score = score, lang = lang))

    else:
        results.Append(MetadataSearchResult(id = title.replace("/","_"), name = title, score = 100, lang = lang))
    

  def update(self, metadata, media, lang):
    Log("UPDATE CALLED")
    url = metadata.id
    detailsPageElements = HTML.ElementFromURL(url.replace("_","/"))
    metadata.summary = detailsPageElements.xpath('//div[contains(@class,"content-desc")]/div/p')[0].text_content()
    metadata.title = detailsPageElements.xpath('//h1')[0].text_content()
    metadata.tagline = "Private.com"
    date = detailsPageElements.xpath('//p[contains(@class,"date_scene")]')[0].text_content().replace("Added: ","")
    date_object = datetime.strptime(date, '%m/%d/%Y')
    metadata.originally_available_at = date_object
    metadata.year = metadata.originally_available_at.year

    metadata.roles.clear()
    metadata.collections.clear()

    starring = detailsPageElements.xpath('//ul[contains(@class,"scene-models-list")]//a')
    for s in starring:
        role = metadata.roles.new()
        role.name = s.text_content().strip()
        metadata.collections.add(role.name)

    for g in detailsPageElements.xpath('//ul[contains(@class,"scene-tags")]//a'):
        metadata.genres.add(g.text_content().strip())

    covers = detailsPageElements.xpath('//img[contains(@src,"pictureThumbs")]')
    for cover in covers:
        thumb = cover.get("src")
        fullSize = cover.get("src").replace("pictureThumbs","Fullwatermarked")
        img_file = urllib.urlopen(fullSize)
        im = StringIO(img_file.read())
        resized_image = Image.open(im)
        width, height = resized_image.size

        p=0
        a=0
        
        if(width < height):
            if not posterAlreadyExists(fullSize,metadata):
                metadata.posters[fullSize] = Proxy.Preview(HTTP.Request(thumb, headers={'Referer': 'http://www.google.com'}).content, sort_order = p)
                p=p+1
        else:
            if not posterAlreadyExists(fullSize,metadata):
                metadata.art[fullSize] = Proxy.Preview(HTTP.Request(thumb, headers={'Referer': 'http://www.google.com'}).content, sort_order = a)
                a=a+1
            
