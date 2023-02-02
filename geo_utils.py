import json
from itertools import groupby

try: import numpy as np
except: pass

def PolyArea(x,y):
    return 0.5*np.abs(np.dot(x,np.roll(y,1))-np.dot(y,np.roll(x,1)))

def get_xy_span(coordinate_list):
  min_x,max_x,min_y,max_y=None,None,None,None
  for x0,y0 in coordinate_list:
    if min_x==None or x0<min_x: min_x=x0
    if min_y==None or y0<min_y: min_y=y0
    if max_x==None or x0>max_x: max_x=x0
    if max_y==None or y0>max_y: max_y=y0
  x_span=(min_x,max_x)
  y_span=(min_y,max_y)
  return (x_span,y_span)

def get_avg_coord(coordinate_list):
  xs=[v[0] for v in coordinate_list]
  ys=[v[1] for v in coordinate_list]
  avg_x=sum(xs)/len(xs)
  avg_y=sum(ys)/len(ys)
  return avg_x,avg_y

def get_widths(x_span0,y_span0):
  #x_span0,y_span0=get_xy_span(coordinate_list)
  x_width=x_span0[1]-x_span0[0]
  y_width=y_span0[1]-y_span0[0]
  return x_width,y_width

def get_span_dist(span0,span1):
  if span0[0]>span1[0] or span0[1]>span1[1]: span0,span1=span1,span0
  return span1[0]-span0[1]

def get_el_dist(el0,el1):
  x_span0,y_span0=el0
  x_span1,y_span1=el1
  x_dist=get_span_dist(x_span0,x_span1)
  y_dist=get_span_dist(y_span0,y_span1)
  return x_dist,y_dist

def get_el_midpoint(el0):
  x_span0,y_span0=el0
  cur_x=(x_span0[0]+x_span0[1])/2
  cur_y=(y_span0[0]+y_span0[1])/2
  return cur_x,cur_y 

def get_area_ratio(area0,area1):
  return min(area0,area1)/max(area0,area1)

#===== Process the output data of Excel workbook to greate a geo dict
def group_2(list_2): #group a list with each element is of size 2, to group by first subelement and get only unique list of grouped subelement2 [("a",1),("a",2),("b",3)...] > a : [1,2], b : [3]
  out_dict={}
  list_2.sort(key=lambda x:x[0])
  grouped=[(key,[v[1] for v in list(group)]) for key,group in groupby(list_2,lambda x:x[0])]
  for key0,grp0 in grouped:
    out_dict[key0]=list(set(grp0))
  return out_dict

def get_geo_dict(wb_dict): #the wb has three sheets, "countries","Admin", and "cities"
  countries_data=wb_dict["countries"]
  admin_data=wb_dict["admin"]
  cities_data=wb_dict["cities"]

  geo_data_dict={}
  geo_data_dict["country"]={}
  geo_data_dict["admin"]={}
  geo_data_dict["city"]={}
  country_admin_list,admin_city_list=[],[]
  city_loc_dict={}

  for item0 in countries_data:
    key0=item0["id"]
    dict0=dict(item0)
    dict0.pop("id", None)
    geo_data_dict["country"][key0]=dict0
  for item0 in admin_data:
    #print(item0)
    key0=item0["id"]
    dict0=dict(item0)
    dict0.pop("id", None)
    geo_data_dict["admin"][key0]=dict0
  for item0 in cities_data:
    city_id=item0.get("id")
    if city_id==None: city_id=item0.get("city-id") #for consistency, the column should be "id", but for now we have it as "city-id"
    city_id=str(city_id)
    dict0=dict(item0)
    dict0.pop("id", None)
    dict0.pop("city-id", None)
    x0=dict0.get("x")
    y0=dict0.get("y")
    if x0!=None and y0!=None: city_loc_dict[city_id]=(x0,y0)
    geo_data_dict["city"][city_id]=dict0
    admin_id=str(dict0["admin-id"])
    country_id=str(dict0["country-id"])
    country_admin_list.append((country_id,admin_id))
    admin_city_list.append((admin_id,city_id))
  geo_data_dict["country-admin"]=group_2(country_admin_list)
  geo_data_dict["admin-city"]=group_2(admin_city_list)
  geo_data_dict["city-loc"]=city_loc_dict
  return geo_data_dict  

def get_geo_query_items(geo_dict,request_type="",country_id=None,admin_id=None,city_id=None,city_id_list=[],lang="en"): #generate lists of geo elements based on certain queries
  out_items=[]
  if request_type=="list_countries":
    cur_dict=geo_dict['country']
    for a,b in cur_dict.items(): 
      name_lang_key="name-"+lang
      name_en_key="name-en"
      name_val=b.get(name_lang_key)
      if name_val==None: name_val=b.get(name_en_key)
      if name_val==None: name_val="-"
      out_items.append((a,name_val))
  if request_type=="list_admin":
    cur_admin_ids=geo_dict['country-admin'].get(country_id,[])
    admin_dict=geo_dict['admin']
    for a in cur_admin_ids:
      tmp_admin_info_dict=admin_dict.get(a,{})
      name_lang_key="name-"+lang
      name_en_key="name-en"
      name_val=tmp_admin_info_dict.get(name_lang_key)
      if name_val==None: name_val=tmp_admin_info_dict.get(name_en_key)
      if name_val==None: name_val="-"
      out_items.append((a,name_val))
  if request_type=="list_cities":
    cur_city_ids=geo_dict['admin-city'].get(admin_id,[])
    city_dict=geo_dict['city']
    for a in cur_city_ids:
      tmp_city_info_dict=city_dict.get(a,{})
      name_lang_key="name-"+lang
      name_en_key="name-en"
      name_val=tmp_city_info_dict.get(name_lang_key)
      if name_val==None: name_val=tmp_city_info_dict.get(name_en_key)
      if name_val==None: name_val="-"
      out_items.append((a,name_val))
  if request_type=="list_city_info": #get the info 
    city_dict=geo_dict['city']
    for a in city_id_list:
      tmp_city_info_dict=city_dict.get(a,{})
      name_lang_key="name-"+lang
      name_en_key="name-en"
      name_val=tmp_city_info_dict.get(name_lang_key)
      if name_val==None: name_val=tmp_city_info_dict.get(name_en_key)
      if name_val==None: name_val="-"
      tmp_city_info_dict["name"]=name_val
      out_items.append((a,name_val,tmp_city_info_dict))

  out_items.sort(key=lambda x:x[1])
  return out_items  

def get_hs_list(hs_code0,hs_dict0,lang="en"):
  child_dict0=hs_dict0.get("child_dict",{})
  name_dict0=hs_dict0.get("name_dict",{})
  cur_children0=child_dict0.get(hs_code0,[])
  final_list=[]
  for ch0 in cur_children0: 
    ch_local_name_dict0=name_dict0.get(ch0,{})
    ch_name0=ch_local_name_dict0.get(lang)
    if ch_name0==None: ch_name0=ch_local_name_dict0.get("en")
    if ch_name0==None: ch_name0=str(ch0)
    final_list.append((ch0,ch_name0))
  return final_list  