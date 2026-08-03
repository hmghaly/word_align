import os, json, sys, shelve
from itertools import groupby

cur_lib_path=os.path.split(__file__)[0]
sys.path.append(cur_lib_path)


import web_lib, general

#pip install tldextract
import tldextract

#31 July 2026
def tld_proc(url,params={}):
    special_domains=params.get("special_domains",["com","net","org"])  #domains with so many websites
    n_chars_suffix_key=params.get("n_chars_suffix_key",2) #number of characters at the end of domain name to be added to suffix to balance
    tld_obj=tldextract.extract(url)
    suffix=tld_obj.suffix
    domain=tld_obj.domain
    suffix_split=suffix.split(".")
    #if domain is 2-letter, it gets added to the suffix
    if len(suffix_split)>2: 
        suffix,domain= ".".join(suffix_split[-2:]) , suffix_split[-3] 
    http_part=url.split("://")[0] #http or https
    main_domain=f"{domain}.{suffix}" #just the key for the main domain and its suffix
    full_domain=f"{http_part}://{main_domain}"
    suffix_key=suffix
    main_original=web_lib.get_main_url(url) #original with subdomains
    main_original_no_http=main_original.split("://")[-1] #we just need the key, to store it in shelves and avoiding duplication

    if suffix in special_domains: 
        suffix_key=domain[-n_chars_suffix_key:]+"."+suffix
    url_tld_dict={"full": full_domain,"main_key":main_domain,"original_key": main_original_no_http,"domain":domain,"suffix":suffix,"suffix_key":suffix_key}
    return url_tld_dict

#process URL by identifying the base/normalized url, without subdomains and anything after the actual domain
#reverting back to the input domain if 
class url_proc:
    def __init__(self,url,content=None,params={}):
        #start with analyzing the input url
        self.keyed_url_results=[] #url with its staus and corresponding links (together with url keys and suffix keys)
        use_base_url=True #main url without subdomains https://sites.google.com.eg >>> https://google.com.eg
        self.input_url_tld_dict=tld_proc(url,params=params)
        input_full_domain_url=self.input_url_tld_dict["full"] 
        self.content_dict=web_lib.get_page_info(input_full_domain_url,content=content,read_method="",params=params)
        self.status_code=self.content_dict.get("status_code")
        
        cur_obj={"url":input_full_domain_url,"status_code": self.status_code, "suffix_key":self.input_url_tld_dict["suffix_key"],"main_key":self.input_url_tld_dict["main_key"]}
        self.keyed_url_results.append(cur_obj)
        #maybe we also need to add the redirect/final url info
        #multiple levels of checking
        #checking using normalized/base url instead of url with subdomain  http://ws.nawd.co.au >>> http://nawd.co.au
        #checking if the finalized url is different from normalized url    http://nawd.co.au >>> http://new-awd.co.au
        #keep track of all these variations to avoid duplications, while keeping only the most final url and its keys


        # #if the main/normalized url is not accessible and it's different from the input url which has subdomains
        # if status_code0!="200" and input_url_tld_dict["main_key"]!=input_url_tld_dict["original_key"]: 
        #     content_dict=web_lib.get_page_info(url,read_method="")
        #     status_code0=content_dict.get("status_code")

        self.final_url=self.content_dict.get("final_url",input_full_domain_url)
        final_url_tld_dict=tld_proc(self.final_url,params=params)
        #results.append(cur_obj)
        self.raw_external_links=self.content_dict.get("external_links",[]) #links before processing against final url
        self.raw_external_links=list(set(self.raw_external_links))
        self.final_external_links=[]
        #self.final_external_links_with_keys=[] #cleaning by the final base/normalized link without subdomains
        used_links_dict={input_full_domain_url:True}
        for ex0 in self.raw_external_links:
            ex_tld_dict=tld_proc(ex0,params=params)
            ex_full_link=ex_tld_dict["full"]
            if used_links_dict.get(ex_full_link,False)==True: continue
            used_links_dict[ex_full_link]=True
            self.final_external_links.append(ex_full_link)
            self.keyed_url_results.append({"url":ex_full_link,"suffix_key":ex_tld_dict["suffix_key"],"main_key":ex_tld_dict["main_key"]})



class url_repo:
    def __init__(self,scrape_dir,params={}):
        self.params=params
        if not os.path.exists(scrape_dir): os.makedirs(scrape_dir)
        self.url_list_dir_path=os.path.join(scrape_dir,"url_lists")
        self.url_shelve_dir_path=os.path.join(scrape_dir,"url_shelves")
        self.ranking_shelve_dir_path=os.path.join(scrape_dir,"ranking_shelves")

        self.error_list_dir_path=os.path.join(scrape_dir,"error_lists")
        self.cached_dir_path=os.path.join(scrape_dir,"cached")

        if not os.path.exists(self.url_list_dir_path): os.makedirs(self.url_list_dir_path)
        if not os.path.exists(self.ranking_shelve_dir_path): os.makedirs(self.ranking_shelve_dir_path)
        if not os.path.exists(self.url_shelve_dir_path): os.makedirs(self.url_shelve_dir_path)
        if not os.path.exists(self.error_list_dir_path): os.makedirs(self.error_list_dir_path)
        if not os.path.exists(self.cached_dir_path): os.makedirs(self.cached_dir_path)


    def add_url(self,url, content=None,new_params=None):
        if new_params!=None: cur_params=new_params #in case we need to have different params for this particular url
        else: cur_params=self.params
        url_proc_obj=url_proc(url=url,content=content,params=cur_params)
        res0=url_proc_obj.keyed_url_results
        res0.sort(key=lambda x:x["suffix_key"])
        grouped_by_suffix=[(key,list(group)) for key,group in groupby(res0,lambda x:x["suffix_key"])]
        for k0,grp0 in grouped_by_suffix:
            print(k0,grp0)
            shelve_fpath=os.path.join(self.url_shelve_dir_path,f"{k0}.shelve")
            list_fpath=os.path.join(self.url_list_dir_path,f"{k0}.txt")
            shelve_fopen=shelve.open(shelve_fpath)
            list_fopen=open(list_fpath,"a")
            for g0 in grp0:
                print(g0)
                g0_url,g0_main_key,g0_status_code=g0["url"],g0["main_key"],g0.get("status_code")
                visited=0
                if g0_status_code=="200": visited=1
                corr=shelve_fopen.get(g0_main_key)
                if corr==None:
                    list_fopen.write(g0_url+"\n")
                    shelve_fopen[g0_main_key]=visited


            list_fopen.close()
            shelve_fopen.close()

        

    def add_url_list(self,url_obj_list):
        pass

#main_scrape_dir
#main_scrape_dir\progress.shelve  | shelve[file_path]=seek_location
#main_scrape_dir\url_lists_dir\   | {suffix_key}.txt com.au.txt le.com.txt | url1 \n url2 ..etc
#main_scrape_dir\url_shelves_dir\ | {suffix_key}.shelve com.au.shelve le.com.shelve | shelve[url_key]=1 (visited)/ 0 (added - not visited) / -1 (with error)
#main_scrape_dir\errors\          | {status_code}


# def process_url2external(url,content=None,params={}):
#     results=[]
#     input_url_tld_dict=tld_proc(url,params=params)
#     input_full_domain_url=input_url_tld_dict["full"] #main url without subdomains https://sites.google.com.eg >>> https://google.com.eg

#     content_dict=web_lib.get_page_info(input_full_domain_url,content=content,read_method="",params=params)
#     status_code0=content_dict.get("status_code")
    
#     #if the main/normalized url is not accessible and it's different from the input url which has subdomains
#     if status_code0!="200" and input_url_tld_dict["main_key"]!=input_url_tld_dict["original_key"]: 
#         content_dict=web_lib.get_page_info(url,read_method="")
#         status_code0=content_dict.get("status_code")

#     final_url=content_dict.get("final_url",input_full_domain_url)
#     final_url_tld_dict=tld_proc(final_url,params=params)

#     cur_obj={"url":final_url,"status_code":status_code0,"suffix_key":final_url_tld_dict["suffix_key"],"main_key":final_url_tld_dict["main_key"]}

#     results.append(cur_obj)
#     external_links=content_dict.get("external_links",[])
#     external_links=list(set(external_links))
#     used_links_dict={}
#     for ex0 in external_links:
#         ex_tld_dict=tld_proc(ex0,params=params)
#         ex_full_link=ex_tld_dict["full"]
#         if used_links_dict.get(ex_full_link,False)==True: continue
#         used_links_dict[ex_full_link]=True
#         results.append({"url":ex_full_link,"suffix_key":ex_tld_dict["suffix_key"],"main_key":ex_tld_dict["main_key"]})
#     return results
    # if url_tld_dict["main_key"]!=url_tld_dict["original_key"]: #check also the main domain without the subdomains
    #     content_dict_main=web_lib.get_page_info(url,read_method="")


    # root_dir=params.get("root_dir","scrape_root")
    
    # final_url_main=web_lib.get_main_url(final_url)
    # links=content_dict.get("links",[])
    # external_links=[v for v in links if not v[0].startswith(final_url_main)]
    # used_href_dict={}
    # for ex0 in external_links: 
    #     href0,anchor0=ex0
    #     main_href=web_lib.get_main_url(href0)
    #     if used_href_dict.get(main_href,False)==True: continue
    #     used_href_dict[main_href]=True
    #     print(main_href)    

#url2content
#content2info_dict
#url2info_dict
#scrape_crawl_single_url
#scrape_crawl_url_list
#distribute_new_urls_on_lists_and shelves

#no AI elements at this stage - possibly only simple classifieres to exclude harmful/useless content
#pages with errors, parked domains, forbidden ... etc
#harmful content: pornography, dark web ?

#read a url > identify its content if harmful or not > if not harmful, add it to the corresponding URL list, 
#add it to the shelve that it has been processed shelve[url]=1 (active/valid/accessible website), 
#if harmful/inaccessible shelve[url]=-1
#then extract basic information from page_info_dict (should we keep it?)
#also extract external links, and check if any of them was visited before, if not, add to the corresponding list
#also update backlink counter shelve, to see which websites are more important
#maybe make a distinction between harmful/inaccessible websites, and these that need to be visited by humans 
#possibly just add a list of websites to be added to human inspection list 
#this human inspection list will be prioritized by the backlink ranking? so we start by most backlinked

#directory structure
#input > any url/url list - specify root directory for storing lists and shelves
#create following subdirectories> url_lists, url_shelves, human_inspection (cached_human), back_links_shelves)
#create configuration file - create stat file
#identify the corresponding shelve for current URL (e.g. tld such as _.com or _ab.com)
#check if the url was visited before - status of the corresponding shelve: status=shelve.get(url,0) - if zero, proceed )
#if zero, attempt to read the url correponsing page, if inaccessible/harmful, assign status -1, and don't add to anything
#if valid content, assign status +1 (visited/valid), append to the corresponding list
#if content is restriected to humans only, assign status -1, add to human inspection list/shelve


#separate human flow - visiting most backlinked human inspection list, get content manually, input it along with the url
#and process it the same way as we do for any new url, except that we still add it even if its visised status is -1
#we add it to the lists


#iter_file_lines




# def process_url_list_file(url_list_fpath,params={}):
#     fopen=open(url_list_fpath)
#     for line0 in fopen:
#         url0=line0.strip()
#         process_url(url0,params=params)
#     fopen.close()

# def create_scrape_dirs(main_dir):
#     pass


