#read text files for anotating audio files
import json, re
from itertools import groupby


def read_json(json_path0):
  fopen0=open(json_path0)
  cur_obj=json.load(fopen0)
  fopen0.close()
  return cur_obj

def read_tsv(tsv_fpath0):
  tsv_fopen=open(tsv_fpath0)
  tsv_list0=[]
  for tsv0 in tsv_fopen: 
    line_split=tsv0.strip().split("\t")
    if len(line_split)!=2: continue
    a,b=line_split
    tsv_list0.append([float(a),b])
  tsv_fopen.close()
  return tsv_list0



def read_phn(phn_fpath0,sample_rate=16000): #also works for wrd files
  phn_list=[]
  fopen=open(phn_fpath0)
  for line0 in fopen:
    line_split=line0.strip().split(" ")
    #print(line_split)
    if len(line_split)!=3: continue
    sample_i0_str,sample_i1_str,phone0=line_split
    sample_i0,sample_i1=int(sample_i0_str),int(sample_i1_str)
    phone_t0,phone_t1=sample_i0/sample_rate,sample_i1/sample_rate
    phn_list.append((phone_t0,phone_t1,phone0))
  return phn_list

def read_gentle(gentle_out_fpath):
  final_list=[]
  fopen=open(gentle_out_fpath)
  json_obj=json.load(fopen)
  fopen.close()
  for w0 in json_obj.get("words",[]):
    #start_t0=w0["start"]
    start_t0=w0.get("start")
    if start_t0==None: continue
    phones0=w0["phones"]
    #print("start_t0",start_t0)
    cur_start_time=start_t0
    for ph0 in phones0:
      #print(ph0)
      ph_dur=ph0["duration"]
      ph_str=ph0["phone"].split("_")[0]
      cur_end_time=cur_start_time+ph_dur
      #print(ph_str,round(cur_start_time,2),round(cur_end_time,2))
      final_list.append((cur_start_time,cur_end_time,ph_str))
      cur_start_time=cur_end_time
    #print("-------")
  return final_list


def read_gentle_new(gentle_out_fpath):
  final_list=[]
  fopen=open(gentle_out_fpath)
  json_obj=json.load(fopen)
  fopen.close()
  word_time_phn_list=[]
  full_phn_list=[]
  for w0 in json_obj["words"]:
    word_str=w0["word"]
    start_t0=w0["start"]
    end_t0=w0["end"]
    phones0=w0["phones"]
    cur_word_obj={}
    cur_word_obj["word"]=word_str
    cur_word_obj["start"]=start_t0
    cur_word_obj["end"]=end_t0

    tmp_rel_phn_list=[]
    rel_time=0
    for ph0 in phones0:
      ph_dur=ph0["duration"]
      ph_str=ph0["phone"].split("_")[0]
      cur_start_time=start_t0+rel_time
      rel_start_time,rel_end_time=rel_time,rel_time+ph_dur
      tmp_rel_phn_list.append((rel_start_time,rel_end_time,ph_str))
      rel_time+=ph_dur
      cur_end_time=start_t0+rel_time
      full_phn_list.append((cur_start_time,cur_end_time,ph_str))
      cur_start_time=cur_end_time

    cur_word_obj["phones"]=tmp_rel_phn_list
    word_time_phn_list.append(cur_word_obj)
  return word_time_phn_list,full_phn_list

def textgrid_2_dict(fpath,order_elements=False): #process the contents of textgrid file and return as a dictinoary 
	#parameters: fpath = file path, order_elements = if we want elements (points and intervals) presented as an ordered list within each tier or as an unordered dictionary
	open_item="" #identify which item/tier are we currently working with
	open_element="" #identify which element (point/interval) are we currently working with
	#order_elements=False #if we want elements (points and intervals) presented as an ordered list within each tier or as an unordered dictionary
	final_list=[]
	fopen=open(fpath)
	for fi,f in enumerate(fopen): #iterating over the entire textgrid file, line by line
		cur_line=f.strip("\t\n\r ") #strip the whitespaces and line breaks
		if not cur_line: continue #skip empty lines
		if cur_line=='item []:': continue #skip the empty item line 
		if cur_line.lower().startswith("item") and cur_line[-1]==":" : open_item,open_element=cur_line, "" #for non-empty items, indicate it as the current active item, and indicate that there is no active/open element
		elif cur_line[-1]==":" : open_element=cur_line #otherwise if the current line ends with colon, indicate that it is an active/open element
		if cur_line[-1]==":": continue #now we want to move to the contents of the elements, so we skip processing the lines that end with colon
		split=[v.strip() for v in cur_line.split("=")] #we split each item around equal sign
		if len(split)==2: #if we have 2 split strings, we process them as key and value 
			key,val = split
			#print "????", val
			if val.startswith('"'): #this is a string value
				our_val=val.strip('"')
			else: #this is a numerical value
				try: our_val=int(val.strip('"')) #check if int
				except:
					try: our_val=float(val.strip('"')) #check if float
					except: our_val=val.strip('"') #else, treat it as string
			#print key, our_val
			final_list.append((open_item, open_element,key, our_val)) #put all keys, values, together with their active items (tiers) and elements into a list


	fopen.close()
	grouped=[(key,[v[1:] for v in list(group)]) for key,group in groupby(final_list,lambda x:x[0])] #we group the list by the items
	final_dict={}
	for k, grp in grouped:
		if k=="": #for the first information lines about the file, outside the items
			for g in grp:
				final_dict[g[-2]]=g[-1] #put these keys and values directly into our output dictionary
			final_dict["items"]={} #then we start filling the items part within the output dictionary
		else:
			item_number=k.split()[1].strip("[]: ")
			tmp_dict={}
			element_dict={}
			element_list=[]
			tier_grouped=[(key,[v[1:] for v in list(group)]) for key,group in groupby(grp,lambda x:x[0])] #we group the key-value pairs for the current tier/item, by element
			tier_type=""
			for tk, tgrp in tier_grouped:
				#print tk, len(tgrp), tgrp[:10]
				if tk=="": #the outside information of the tier, without going into the elements
					for t0,t1 in tgrp:
						tmp_dict[t0]=t1
						if t0.startswith("points"): tier_type="points" #given these outside info, if one of the keys start with points, it is a points tier
						if t0.startswith("intervals"): tier_type="intervals" #otherwise, it is an interval tier
				else:
					element_number=tk.split()[1].strip("[]: ") #we get the element number
					local_dict=dict(iter(tgrp)) #and create a local dict for element data

					element_dict[element_number]=local_dict #we update the element dictionary with the local element dictionary
					local_dict["id"]=element_number #for the option that we want to keep the elements ordered, we add another key to the local dict to keep the id of the element
					element_list.append(local_dict) #and we put it in the ordered list of elements

			if not order_elements: #then we decide if we want the elements in a dicionary e.g. our_dict[iten_number][element_number]={"xmin":20,"xmax":21}
				if tier_type=="points": tmp_dict["points"]=element_dict #depending in the type of elements, we update the tmp_dict
				if tier_type=="intervals": tmp_dict["intervals"]=element_dict
			else: #or we want it an ordered list e.g. our_dict[iten_number]=[{"id":15,"xmin":20,"xmax":21},{"id":16,"xmin":21,"xmax":22}]
				if tier_type=="points": tmp_dict["points"]=element_list
				if tier_type=="intervals": tmp_dict["intervals"]=element_list

			
			final_dict["items"][item_number]=tmp_dict #and finally we update the final dict with the tmp dict
	return final_dict


def textgrid_2_json(input_fpath,out_fpath,order_elements=False): #convert the input textgrid file into json file
	cur_dict=textgrid_2_dict(input_fpath,order_elements)
	json_content=json.dumps(cur_dict)
	fopen=open(out_fpath,"w")
	fopen.write(json_content)
	fopen.close()

def phn2tsv(t_list0,phn_fpath0,cur_mapping_fn=lambda x:x):
  phn_out=read_phn(phn_fpath0)
  tsv_list=[]
  for tl0 in t_list0:
    cur_phone="sil"
    for phn_item in phn_out:
      ph_t0,ph_t1,ph0=phn_item
      if tl0>=ph_t0 and tl0<ph_t1:
        cur_phone=ph0
        break
    corr_phone=cur_mapping_fn(cur_phone) #cur_mapping_dict0.get(cur_phone,"-")
    tsv_list.append((tl0,corr_phone))
  return tsv_list

def create_tsv_files(cur_dir_path0,cur_params0,cur_mapping_fn=lambda x:x,cur_tsv_suffix0="0"):
  cur_wav_files=get_dir_files(cur_dir_path0,extension="wav")
  tsv_dir_name="tsv-"+cur_tsv_suffix0
  print("cur dir:",cur_dir_path0,"total number of files:",len(cur_wav_files))
  for wav_fpath in cur_wav_files:
    tmp_dir0,fname0=os.path.split(wav_fpath)
    cur_ann_fpath=wav_fpath.replace(".wav",".phn")
    if not os.path.exists(cur_ann_fpath): continue
    # phn_out=read_phn(cur_ann_fpath)
    # for a in phn_out:
    #   print(a, cur_mapping_fn(a[-1]))
    # print("-----")
    # continue

    t_list,ft_list=extract_audio_features(wav_fpath,cur_params0)
    cur_tsv_list=phn2tsv(t_list,cur_ann_fpath,cur_mapping_fn)      
    tsv_fname=fname0.replace(".wav",".tsv")
    tsv_subdir=os.path.join(tmp_dir0, tsv_dir_name)
    if not os.path.exists(tsv_subdir): os.mkdir(tsv_subdir)
    tsv_fpath=os.path.join(tsv_subdir,tsv_fname)
    tsv_fopen=open(tsv_fpath,"w")
    for tsv_item in cur_tsv_list:
      line="%s\t%s\n"%(tsv_item[0],tsv_item[1])
      tsv_fopen.write(line)
    tsv_fopen.close()	