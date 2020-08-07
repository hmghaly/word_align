import re

class soup: #generates a soup object containing tne main elements within the nested xml/html, which can be filtered by the tag type to provide a list of target tags
	def __init__(self,xml_content,main_tag_name_criteria=None): #and also a dictionary showing the children of each tag, and another dictionary to show attributes, and a dictionary to show plain text of the contents of each tag without the nesting
		self.main_keys=[]
		tags=list(re.finditer('<([^<>]*?)>', xml_content))
		open_tags=[]
		tag_dict={}
		self.tag_txt_dict={}
		tag_counter_dict={}
		self.children_dict={}
		self.attrs_dict={}
		self.full_span_dict={}
		#sent_tokens=[]
		for t in tags:

			tag_str,tag_start,tag_end=t.group(0), t.start(), t.end()
			tag_name=re.findall(r'</?(.+?)[\s>]',tag_str)[0].lower()
			tag_count=tag_counter_dict.get(tag_name,0)
			tag_id="%s_%s"%(tag_name,tag_count)
			tag_dict[tag_id]=tag_start,tag_end
			
			
			last_tag=""
			if open_tags: last_tag=open_tags[-1]
			if tag_str.startswith('</'):
				tag_type="c"
				
				cur_span=xml_content[tag_dict[last_tag][1]:tag_start]
				cur_span_clean=re.sub('<([^<>]*?)>',"", cur_span)
				self.tag_txt_dict[last_tag]=cur_span_clean
				self.full_span_dict[last_tag]=cur_span

				open_tags=open_tags[:-1]
			elif tag_str.endswith('/>') or tag_str.startswith('<meta') or tag_str.startswith('<img'):
				tag_type='s'
				self.children_dict[last_tag]=self.children_dict.get(last_tag,[])+[tag_id]
				tag_counter_dict[tag_name]=tag_count+1
				self.attrs_dict[tag_id]=dict(iter(re.findall('(\w+?)="(.+?)"',tag_str)))
				
			else:
				tag_type='o'
				if tag_name==main_tag_name_criteria: self.main_keys.append(tag_id)
				open_tags.append(tag_id)
				self.children_dict[last_tag]=self.children_dict.get(last_tag,[])+[tag_id]
				tag_counter_dict[tag_name]=tag_count+1
				self.attrs_dict[tag_id]=dict(iter(re.findall('(\w+?)="(.+?)"',tag_str)))            


if __name__=="__main__":
	fpath="/Users/hmghaly/Documents/switchboard/breaks/sw2018.A.breaks.xml"
	#fpath="/Users/hmghaly/Documents/switchboard/terminals/sw2015.B.terminals.xml"
	fopen=open(fpath)
	content=fopen.read()
	fopen.close()
	#soup_obj=soup(content,"word")
	soup_obj=soup(content,"break")
	for k in soup_obj.main_keys:
		#continue
		print(k)
		print(soup_obj.attrs_dict.get(k))
		children=soup_obj.children_dict.get(k,[])
		for ch in children:
			print(soup_obj.attrs_dict.get(ch))
		
		print('-----')



