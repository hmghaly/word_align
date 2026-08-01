import os, json, sys, shelve
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
        #print(suffix_split)
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
def process_url2external(url,params={}):
    results=[]
    input_url_tld_dict=tld_proc(url,params=params)
    input_full_domain_url=input_url_tld_dict["full"] #main url without subdomains https://sites.google.com.eg >>> https://google.com.eg

    content_dict=web_lib.get_page_info(input_full_domain_url,read_method="")
    status_code0=content_dict.get("status_code")
    
    #if the main/normalized url is not accessible and it's different from the input url which has subdomains
    if status_code0!="200" and input_url_tld_dict["main_key"]!=input_url_tld_dict["original_key"]: 
        content_dict=web_lib.get_page_info(url,read_method="")
        status_code0=content_dict.get("status_code")

    final_url=content_dict.get("final_url",input_full_domain_url)
    final_url_tld_dict=tld_proc(final_url,params=params)

    cur_obj={"url":final_url,"status_code":status_code0,"suffix_key":final_url_tld_dict["suffix_key"],"main_key":final_url_tld_dict["main_key"]}

    results.append(cur_obj)
    external_links=content_dict.get("external_links",[])
    external_links=list(set(external_links))
    used_links_dict={}
    for ex0 in external_links:
        ex_tld_dict=tld_proc(ex0,params=params)
        ex_full_link=ex_tld_dict["full"]
        if used_links_dict.get(ex_full_link,False)==True: continue
        used_links_dict[ex_full_link]=True
        results.append({"url":ex_full_link,"suffix_key":ex_tld_dict["suffix_key"],"main_key":ex_tld_dict["main_key"]})
    return results
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




def process_url_list_file(url_list_fpath,params={}):
    fopen=open(url_list_fpath)
    for line0 in fopen:
        url0=line0.strip()
        process_url(url0,params=params)
    fopen.close()

def create_scrape_dirs(main_dir):
    pass
