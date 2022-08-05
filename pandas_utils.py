import pandas as pd

def get_sheet_list(sheet_obj,key_col0,val_col0): #pandas get conversion dicts
  #tmp_sheet_dict={}
  tmp_sheet_list=[]

  for i0,row0 in sheet_obj.iterrows():
    cur_key,cur_val=row0[key_col0],row0[val_col0]
    if cur_key=="" or cur_val=="": continue
    tmp_sheet_list.append((cur_key,cur_val))
    #tmp_sheet_dict[cur_key]=cur_val
  return tmp_sheet_list

def get_workbook_obj(path0):
  return pd.read_excel(path0, None,keep_default_na=False)

def get_sheet_obj(wb_obj,sheet):
  return wb_obj[sheet]

def get_wb_sheet_list(path1,sheet1,key_col1,val_col1):
  wb_obj1=get_workbook_obj(path1)
  sheet_obj1=wb_obj1[sheet1]
  sheet_key_val_list1=get_sheet_list(sheet_obj1,key_col1,val_col1)
  return sheet_key_val_list1

if __name__=="__main__":
  print("Hello")
