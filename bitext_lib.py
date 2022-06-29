import pandas as pd
def get_bitext(xls_path0,sheet_name0="",src_col="en",trg_col="ar",filter_non_alpha=False, filter_numbers=False):
  #xls_path='https://docs.google.com/spreadsheets/d/e/2PACX-1vSVy7hY4fV0LHqTCypOjZAM9OrBevDDnpIcEKEAPKDsYRoxAz9TUBcDIgy8PvHkw5IDAZ6eRmKdZuRw/pub?output=xlsx'
  cur_xls = pd.ExcelFile(xls_path0)
  bitext_list=[]
  if sheet_name0!="": cur_sheet_list=[sheet_name0]
  else: cur_sheet_list=cur_xls.sheet_names
  for cur_sheet_name in cur_sheet_list:
    print(cur_sheet_name)
    cur_sheet_obj=pd.read_excel(cur_xls, cur_sheet_name,keep_default_na=False)
    cur_sheet_obj[src_col]=cur_sheet_obj[src_col].apply(str)
    cur_sheet_obj[trg_col]=cur_sheet_obj[trg_col].apply(str)
    for i,row in enumerate(cur_sheet_obj.iterrows()):
      row_dict=row[1].to_dict()
      en0,ar0=row_dict["en"],row_dict["ar"]
      test_alpha=re.sub("\W+","",en0)
      if filter_non_alpha and test_alpha=="": continue
      if filter_numbers and test_alpha.isdigit(): continue
      if trg_col=="ar": ar0=clean_ar(ar0)
      bitext_list.append((en0,ar0))
  return bitext_list
