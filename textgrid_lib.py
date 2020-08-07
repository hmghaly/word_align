import os, re, json
from itertools import groupby
from sys import argv

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
	#json_content=json_content.replace("{","\n{") #later we can include multiline features for ease of visual inspection
	#json_content=json_content.replace(",",",\n")
	#json_content=json_content.replace("\n \n","\n")
	#json_content=json_content.replace("\n\n","\n")
	#json_content=json_content.strip()
	fopen=open(out_fpath,"w")
	fopen.write(json_content)
	fopen.close()

tab="    "

def write_text_grid(tiers_list,out_fpath):
	"""
	a tier list is a list of tiers, where each tier item has the tier name, tier info (list of intervals or points and their times), and wgether it is an interval tier or not
	"""
	file_max_t=0 #the maximum time for the file
	tier_content_items=[]
	for tier_i,tier_item in enumerate(tiers_list):
		tier_name,tier_info_list,is_interval_tier=tier_item 
		output=tab+'item [%s]:\n'%(tier_i+1) #item number
		new_list=[]
		end_times=[]
		for a in tier_info_list:
			try:  #this is to include intervals and points which have only float times, not "NA" for example
				if is_interval_tier: 
					if float(a[1])<0 or float(a[2])<0: continue
					new_list.append((a[0],float(a[1]),float(a[2])))
					end_times.append(float(a[2]))
				else: 
					if float(a[1])<0: continue
					new_list.append((a[0],float(a[1])))
					end_times.append(float(a[1]))
			except: pass
		if not end_times: return output
		max_t1=max(end_times)
		if max_t1>file_max_t: file_max_t=max_t1
		if is_interval_tier: #if it is an interval tier
			output+=tab*2+'class = "IntervalTier"\n'
			output+=tab*2+'name = "%s"\n'%tier_name
			output+=tab*2+'xmin = 0\n'
			output+=tab*2+'xmax = %s\n'%max_t1
			output+=tab*2+'intervals: size = %s\n'%len(new_list)
			for item_i,item in enumerate(new_list):
				cur_i=item_i+1
				cur_text,cur_t0,cur_t1=item
				output+=tab*2+'intervals [%s]:\n'%cur_i
				output+=tab*3+'xmin = %s\n'%cur_t0
				output+=tab*3+'xmax = %s\n'%cur_t1
				output+=tab*3+'text = "%s"\n'%cur_text
		else: #if it is a point tier
			output+=tab*2+'class = "TextTier"\n'
			output+=tab*2+'name = "%s"\n'%tier_name
			output+=tab*2+'xmin = 0\n'
			output+=tab*2+'xmax = %s\n'%max_t1
			output+=tab*2+'points: size = %s\n'%len(new_list)
			for item_i,item in enumerate(new_list):
				cur_i=item_i+1
				cur_text,cur_t=item
				output+=tab*2+'points [%s]:\n'%cur_i
				output+=tab*3+'number = %s\n'%cur_t
				output+=tab*3+'mark = "%s"\n'%cur_text


		tier_content_items.append(output) 
	file_content='File type = "ooTextFile"\nObject class = "TextGrid"\n\n' #now start to create the content of the file
	file_content+='xmin = 0\n'
	file_content+='xmax = %s\n'%file_max_t
	file_content+='tiers? <exists> \n'
	file_content+='size = %s \n'%len(tiers_list)
	file_content+='item []:\n'
	for ci in tier_content_items:
		file_content+=ci

	fopen=open(out_fpath,"w")
	fopen.write(file_content)
	fopen.close()




def create_interval_tier(tier_name,list_intervals_times): #[(word1,w1_t0,w1_t1),(word2,w2_t0,w2_t1)...]

	output=""
	new_list=[]
	for a in list_intervals_times:
		try: new_list.append((a[0],float(a[1]),float(a[2])))
		except: pass
	list_t1=[v[2] for v in new_list] #we should check if it is actually float
	if not list_t1: return output
	max_t1=max(list_t1)
	output+=tab*2+'class = "IntervalTier"\n'
	output+=tab*2+'name = "%s"\n'%tier_name
	output+=tab*2+'xmin = 0\n'
	output+=tab*2+'xmax = %s\n'%max_t1
	output+=tab*2+'intervals: size = %s\n'%len(new_list)
	for item_i,item in enumerate(new_list):
		cur_i=item_i+1
		cur_text,cur_t0,cur_t1=item
		output+=tab*2+'intervals [%s]:\n'%cur_i
		output+=tab*3+'xmin = %s\n'%cur_t0
		output+=tab*3+'xmax = %s\n'%cur_t1
		output+=tab*3+'text = "%s"\n'%cur_text
	print output


if __name__=="__main__":
	print argv
	word_list=[("and",0,1),("here",1,2),("we",2,3),("some","3.5","NA"),("go",3,4)]
	#cur_tier_list=[("words",word_list,True)]
	point_list=[("H+",2),("H-",2.5),("L+",3.5)]
	point_list2=[("Z+",1),("Z-",1.5),("Z+",5.5)]
	cur_tier_list=[("words",word_list,True),("tones",point_list,False),("tonesZ",point_list2,False)]
	#create_interval_tier("words",word_list)
	root_dir="/Users/hmghaly/Documents/switchboard"
	new_fpath=os.path.join(root_dir,"test_out1.TextGrid")
	write_text_grid(cur_tier_list,new_fpath)

	order_elements=False
	if len(argv)<3:
		print "Usage: textgrid_lib.py /input/directory/path/file.textgrid /output/directory/file.json -order"
		print "hint: -order is optional, the default is that elements (points/intervals) are in unordered dictionary, so if you specify -order they are in an ordered list"
	else:
		src_fpath=argv[1]
		trg_fpath=argv[2]
		if "-order" in argv: order_elements=True
		textgrid_2_json(src_fpath,trg_fpath,order_elements)
		print "converted %s to %s successfully!"%(src_fpath,trg_fpath)

	#praat_dir="autobi_out"
	#fname="sw2010.B.autobi.TextGrid"
	#fpath=os.path.join(praat_dir,fname)
	#fpath="test.textgrid"
	#out_fpath=fpath+".json"
	#our_final_dict=textgrid_2_dict(fpath,elements_as_dict=False)
	#textgrid_2_json(fpath,out_fpath,elements_as_dict=False)


#for f in our_final_dict:
#	if f=="items": continue
#	print ">>>", f, our_final_dict[f]

#for f in our_final_dict["items"]:
#	cur_elements=our_final_dict["items"][f].get("points",[])+our_final_dict["items"][f].get("intervals",[])
#	print ">>>", f, len(cur_elements)
#	for a in cur_elements:
#		print a
	
	#print '-----'
