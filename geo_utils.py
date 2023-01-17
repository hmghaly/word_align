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
    geo_data_dict["city"][city_id]=dict0
    admin_id=str(dict0["admin-id"])
    country_id=str(dict0["country-id"])
    country_admin_list.append((country_id,admin_id))
    admin_city_list.append((admin_id,city_id))
  geo_data_dict["country-admin"]=group_2(country_admin_list)
  geo_data_dict["admin-city"]=group_2(admin_city_list)
  return geo_data_dict  