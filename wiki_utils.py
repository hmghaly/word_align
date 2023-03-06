#!pip3 install wikipedia-api

import wikipediaapi
wiki_wiki = wikipediaapi.Wikipedia('en')

def get_lang_pages(input_page_title, wiki_obj):
  output_dict={}
  page_py = wiki_obj.page(input_page_title)
  page_langs = page_py.langlinks
  for a,b in page_langs.items():
    lang_text=b.title
    output_dict[a]=lang_text
  return output_dict

# title0='Lebanon'
# out0=get_lang_pages(title0, wiki_wiki)  
# for a,b in out0.items():
#   print(a,b)
