#a librry for all the utilities we need for scraping data from the web
import requests, re
from urllib.parse import urljoin, urlsplit
from bs4 import BeautifulSoup
from lxml.html import parse

class web_page:
  def __init__(self,url):
    self.url=url
    try: self.tld=urlsplit(url).netloc #not sure if it is TLD 
    except: self.tld=""
    self.all_text_items=[self.url,"_br_"] #add the page url and a line break at the beginning of the text items

    self.html_content=""
    self.title=""
    self.text=""
    self.status_code=None
    self.segs=[]
    self.clean_text=""
    self.all_links,self.internal_links,self.externl_links=[],[],[]
    self.meta_content=[]
    try:
      op=requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=5)
      self.status_code=op.status_code
      self.html_content=op.text
      self.html_content=self.html_content.replace("</p>","_br_</p>") #to put a line break at the end of paragraph elements
      self.html_content=self.html_content.replace("<p>","_br_<p>")
      self.html_content=self.html_content.replace("</li>","</li>_br_")
      
      self.html_content=re.sub('(</h\d>)',r'_br_\1',self.html_content) #to add line break at headings
      self.html_content=re.sub('(<h\d\b.*?>)',r'_br_\1',self.html_content)
      self.html_content=re.sub('(<p\b.*?>)',r'_br_\1',self.html_content) #and at paragraphs
      self.html_content=re.sub('(<li\b.*?>)',r'_br_\1',self.html_content) #and at lists
      self.html_content=self.html_content.replace("<br>","_br_")
      soup=BeautifulSoup(self.html_content)
      if soup==None: return
    except:
      return

    if soup.title: self.title=soup.title.string #Find the title
    self.all_text_items.append(self.title)
    self.all_text_items.append("_br_")


    for script in soup(["script", "style"]):
        script.decompose()
    self.strips = list(soup.stripped_strings)
    
    self.all_text_items.extend(self.strips) #add text strips from page HTML
    self.all_text_items.append("_br_")

    meta_content_found=re.findall('content="(.+?)"', self.html_content)
    self.meta_content=[]
    for mc in meta_content_found:
      if "=" in mc: continue
      self.meta_content.append(mc)
      self.all_text_items.append(mc)
      self.all_text_items.append("_br_")

    #self.all_text_items=[self.url,"_br_"]+self.all_text_items
    #self.all_text_items.append("_br_")

    self.text=" ".join([v for v in self.all_text_items if v])
    #self.text=self.text.replace("_br_","\n")
    self.clean_text=re.sub("[\r\n\r\s]+"," ",self.text).strip() #clean breaks and tabs
    self.clean_text=self.clean_text.replace("_br_","\n")
    self.segs=[v.strip() for v in self.clean_text.split("\n") if v.strip()]
    self.clean_text="\n".join(self.segs)
    self.links_text=[] #links with their text
    links_found=[]
    for link in soup.findAll('a'):
      link_str=link.string
      if link_str: link_str=link_str.strip()
      cur_href=link.get('href')
      if cur_href!=None: 
        links_found.append(cur_href)
        if link_str: self.links_text.append((cur_href,link_str))
    links_found=list(set(links_found))
    self.all_links=[]
    self.internal_links=[]
    self.external_links=[]
    for li in links_found:
      if li.endswith(".js"): continue
      if li.endswith(".css"): continue
      if li.endswith(".png"): continue
      if li.endswith(".pdf"): continue
      if li.startswith("http"): cur_link=li
      else: 
        cur_link=urljoin(self.url,li)
      self.all_links.append(cur_link)
      if self.tld in cur_link: self.internal_links.append(cur_link)
      else: self.external_links.append(cur_link)

# page_obj=web_page(url)
# #print(page_obj.title)
# #print(page_obj.meta_content)
# links=page_obj.all_links
# text=page_obj.clean_text