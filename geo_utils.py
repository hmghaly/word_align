import json
import numpy as np
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