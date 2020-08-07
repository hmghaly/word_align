import os, re
import shutil
import zipfile

w_p_exp=r"<w:p\b.*?>.*?</w:p>"
w_t_exp=r"<w:t\b.*?>.*?</w:t>"
w_r_exp=r"<w:r\b.*?>.*?</w:r>"
w_t_inside_exp=r"<w:t\b.*?>(.*?)</w:t>"
w_t_inside_outside_exp=r"(<w:t\b.*?>)(.*?)(</w:t>)"


def safe_xml(txt):
    txt=txt.replace("&","&amp;")
    txt=txt.replace("<","&lt;")
    txt=txt.replace(">","&gt;")
    return txt



def find_iter_split(expression,text): #generic function to split a text (haystack) around a certain regex
    split_text=[]
    exp_applies={} #whether the current expression applies to the current segment of the split segments
    found_objs=re.finditer(expression,text)
    indexes=[0]
    for fo in found_objs:
        start,end=fo.start(), fo.end()
        indexes.append(start)
        indexes.append(end)
        exp_applies[start]=True #in the split chunks, the regex criteria applies to some of them, and some are not, so we keep track of this
    indexes.append(len(text))
    if len(indexes)==2: return []
    counter=0
    for i0,i1 in zip(indexes,indexes[1:]):
        applies=exp_applies.get(i0,False)
        chunk=text[i0:i1] 
        split_text.append((counter,applies,chunk))
        counter+=1
    return split_text

def get_wr_text(wr_chunk):
     all_text=""
     wt_chunks=find_iter_split(w_t_exp,wr_chunk)
     for wt in wt_chunks:
        wt_counter,wt_applies,wt_chunk=wt
        wt_content=[""]
        if wt_applies: wt_content=re.findall(w_t_inside_exp,wt_chunk)
        elif "<w:br/>" in wt_chunk: wt_content=["\n"]
        elif "<w:tab/>" in wt_chunk: wt_content=["\t"]
        all_text+=wt_content[0]
     return all_text

def update_wr_text(wr_xml,new_text):
     wt_chunks=find_iter_split(w_t_exp,wr_xml)
     new_text=safe_xml(new_text)
     new_wr_content=""
     replaced=False
     for wt in wt_chunks:
        wt_counter,wt_applies,wt_chunk=wt
        if wt_applies:
                first_tag=wt_chunk[:wt_chunk.find(">")+1]
                last_tag=wt_chunk[wt_chunk.rfind("<"):]
                if replaced==False: #we replace only the first wt 
                    wt_content=first_tag+new_text+last_tag
                    replaced=True
                else: wt_content=first_tag+last_tag
                new_wr_content+=wt_content
        else: new_wr_content+=wt_chunk#.decode("utf-8")
     return new_wr_content

def get_xml_wrs(xml_content):
    cur_chunks=find_iter_split(w_p_exp,xml_content)
    return cur_chunks

def get_xml_paras_OLD(xml_content):
    new_xml_content=""
    para_chunks=find_iter_split(w_p_exp,xml_content)
    for pc in para_chunks:
        wr_counter,wr_applies,wr_chunk=pc
        if not wr_applies:
                new_xml_content+=wr_chunk#.decode("utf-8")
                continue
        wr_chunk_text=get_wr_text(wr_chunk)
        if wr_chunk_text=="":
                new_xml_content+=wr_chunk#.decode("utf-8")
                continue
        our_new_text=wr_chunk_text.replace(" ","-")#+alef_lam
        new_wr_chunk=update_wr_text(wr_chunk,our_new_text)
        new_xml_content+=new_wr_chunk

    return new_xml_content

class docx:
    def __init__(self,docx_fpath): #openning the docx file, by unzipping it


        self.TEMP_DOCX = docx_fpath
        self.closed=False
        self.COPY_DOCX = docx_fpath+"2"
        shutil.copy(self.TEMP_DOCX, self.COPY_DOCX) #keep a temp copy of out file, just in case
        self.TEMP_ZIP = docx_fpath.replace(".docx",".zip")
        self.TEMP_FOLDER = docx_fpath.replace(".docx","")
        if os.path.exists(self.TEMP_ZIP):
            os.remove(self.TEMP_ZIP)
        if os.path.exists(self.TEMP_FOLDER):
            shutil.rmtree(self.TEMP_FOLDER)
        os.rename(self.TEMP_DOCX, self.TEMP_ZIP) #rename the original docx to zip extension
        # unzip file zip to specific folder
        z_open=zipfile.ZipFile(self.TEMP_ZIP, 'r')
        z_open.extractall(self.TEMP_FOLDER)
        z_open.close()
        os.rename(self.COPY_DOCX, self.TEMP_DOCX) #keep the original file
    def save_as(self,out_fpath):
        if os.path.exists(out_fpath): #remove any of these if already exists
            os.remove(out_fpath)
        #self.OUT_ZIP = out_fpath.replace(".docx",".zip")
        #shutil.make_archive(self.OUT_ZIP, 'zip', self.TEMP_FOLDER)
        shutil.make_archive(self.TEMP_ZIP.replace(".zip", ""), 'zip', self.TEMP_FOLDER)
        os.rename(self.TEMP_ZIP, out_fpath)
    def extract_paras(self): 
        self.paras=[]
        extracted_dir=os.path.join(self.TEMP_FOLDER, "word")
        for xml_fname in os.listdir(extracted_dir):
            #print xml_fname
            if not xml_fname=="document.xml" and not xml_fname.startswith("header") and not xml_fname.startswith("footer"): continue
            cur_xml_path=os.path.join(extracted_dir,xml_fname)
            with open(cur_xml_path) as fopen:
                xml_content=fopen.read()
            cur_chunks=get_xml_wrs(xml_content)
            for cc in cur_chunks:
                cc_i,cc_true,cc_xml=cc

                cc_text=get_wr_text(cc_xml)
                if not cc_true or not cc_text: continue
                #print xml_fname, cc_i, cc_text
                self.paras.append((xml_fname, cc_i, cc_xml, cc_text))
        return self.paras

    def update_para(self,fname,para_i,new_para_text):
        extracted_dir=os.path.join(self.TEMP_FOLDER, "word")
        cur_xml_path=os.path.join(extracted_dir,fname)
        fopen_read=open(cur_xml_path)
        xml_content=fopen_read.read()
        fopen_read.close()
        #with open(cur_xml_path) as fopen:
        #   xml_content=fopen.read()
        cur_chunks=get_xml_wrs(xml_content)
        xml_content=""
        for cc in cur_chunks:
            cc_i,cc_true,cc_xml=cc
            if cc_i!=para_i: xml_content+=cc_xml
            else:
                new_wr=update_wr_text(cc_xml,new_para_text)
                xml_content+=new_wr
        
        fopen_write=open(cur_xml_path, "wb")
        fopen_write.write(xml_content)
        fopen_write.close()

    def update_para_by_dict(self,repl_dict):
        extracted_dir=os.path.join(self.TEMP_FOLDER, "word")
        for xml_fname in os.listdir(extracted_dir):
            #print xml_fname
            if not xml_fname=="document.xml" and not xml_fname.startswith("header") and not xml_fname.startswith("footer"): continue
            cur_xml_path=os.path.join(extracted_dir,xml_fname)
            fopen_read=open(cur_xml_path)
            xml_content=fopen_read.read()
            fopen_read.close()
            #with open(cur_xml_path) as fopen:
            #   xml_content=fopen.read()
            cur_chunks=get_xml_wrs(xml_content)
            xml_content=""
            for cc in cur_chunks:
                cc_i,cc_true,cc_xml=cc
                cur_key=(xml_fname,cc_i)
                new_text=repl_dict.get(cur_key)
                if new_text==None: xml_content+=cc_xml
                else:
                    new_wr=update_wr_text(cc_xml,new_text)
                    xml_content+=new_wr
            
            fopen_write=open(cur_xml_path, "wb")
            fopen_write.write(xml_content)
            fopen_write.close()


    def update_tbl_rtl(self):
        extracted_dir=os.path.join(self.TEMP_FOLDER, "word")
        cur_xml_path=os.path.join(extracted_dir,"document.xml")
        fopen_read=open(cur_xml_path)
        xml_content=fopen_read.read()
        fopen_read.close()
        xml_content=xml_content.replace("<w:tblPr>","<w:tblPr><w:bidiVisual/>")
        xml_content=xml_content.replace("<w:lang ","<w:rtl/><w:lang ")

        
        fopen_write=open(cur_xml_path, "wb")
        fopen_write.write(xml_content)
        fopen_write.close()


    def close(self):
        self.closed=True
        os.remove(self.TEMP_ZIP)
        shutil.make_archive(self.TEMP_ZIP.replace(".zip", ""), 'zip', self.TEMP_FOLDER)
        os.rename(self.TEMP_ZIP, self.TEMP_DOCX)
        shutil.rmtree(self.TEMP_FOLDER)

if __name__=="__main__":
    cwd=os.getcwd()
    cur_fpath=os.path.join(cwd,"test-docx-new.docx")
    #cur_fpath=os.path.join(cwd,"25-september_ar.docx")
    
    test_fpath=os.path.join(cwd,"test-docx-new-test15.docx")
    docx_obj=docx(cur_fpath)
    #paras=docx_obj.extract_paras()
    #docx_obj.update_para("header1.xml",7,"----- What else-----")
    #docx_obj.update_para("footer2.xml",1,"@@@ updated footer")
    #docx_obj.update_para("header1.xml",1,"No. 2018/118 ------ header 1")
    #docx_obj.update_para("header2.xml",1,"No. 2018/118 ------ header 2")
    #docx_obj.update_para("header3.xml",5,"No. 2018/118 ------ header 3")
    docx_obj.update_tbl_rtl()

    cur_repl_dict={}
    cur_repl_dict[("header3.xml",5)]="No. 2018/118 ------ header 3 - REPL UPDATE"
    cur_repl_dict[("document.xml",983)]="______________________!!!!!!!!!!!!!!!!!!!!!!_________________"
    docx_obj.update_para_by_dict(cur_repl_dict)

    
    
    paras=docx_obj.extract_paras()

    docx_obj.save_as(test_fpath)

    #simplified approach =================
    tmp_extracted_folder_path="test-docx-new"
    extracted_dir=os.path.join(tmp_extracted_folder_path, "word")
    for xml_fname in os.listdir(extracted_dir):
        #print xml_fname
        if not xml_fname=="document.xml" and not xml_fname.startswith("header") and not xml_fname.startswith("footer"): continue
        cur_xml_path=os.path.join(extracted_dir,xml_fname)
        print ">>>", cur_xml_path
        xml_fopen=open(cur_xml_path)
        xml_content=xml_fopen.read()
        xml_fopen.close()
        
        w_p_segs=re.findall(w_p_exp,xml_content)
        
        for w0 in w_p_segs:
            para_id=re.findall('paraId="(.+?)"',w0)
            wr_segs=re.findall(w_r_exp,w0)
            w_t_inside=re.findall(w_t_inside_exp,w0)

            print xml_fname, para_id
            for wt0 in w_t_inside:
                print wt0
            print "###"
            print w0
            print "-----"


    #docx_obj.close()
    #print docx_obj.TEMP_DOCX





# def get_paras_docx_xml(docx_fpath,out_fpath):
#     #TEMP_DOCX = docx_fpath
#     #temp_zip_fname = fname.replace(".docx",".zip")
#     #temp_folder_name = fname.replace(".docx","")


#     TEMP_DOCX = docx_fpath
#     TEMP_ZIP = docx_fpath.replace(".docx",".zip")
#     TEMP_FOLDER = docx_fpath.replace(".docx","")
#     shutil.copy(TEMP_DOCX, TEMP_DOCX+"2") #keep a temp copy of out file

#     #print "TEMP_DOCX", TEMP_DOCX
#     #print "TEMP_ZIP", TEMP_ZIP
#     #print "TEMP_FOLDER", TEMP_FOLDER
#     # remove old zip file or folder template
#     if os.path.exists(out_fpath):
#         os.remove(out_fpath)
#     if os.path.exists(TEMP_ZIP):
#         os.remove(TEMP_ZIP)
#     if os.path.exists(TEMP_FOLDER):
#         shutil.rmtree(TEMP_FOLDER)
#     # reformat template.docx's extension
    
#     os.rename(TEMP_DOCX, TEMP_ZIP)
    

#     # unzip file zip to specific folder
#     z_open=zipfile.ZipFile(TEMP_ZIP, 'r')
#     z_open.extractall(TEMP_FOLDER)
#     z_open.close()
    
#     #with zipfile.ZipFile(TEMP_ZIP, 'r') as z:
#     #    z.extractall(TEMP_FOLDER)

      
#     extracted_dir=os.path.join(TEMP_FOLDER, "word")
#     for xml_fname in os.listdir(extracted_dir):
#         print xml_fname
#         #if not xml_fname.endswith(".xml") or xml_fname=="numbering.xml" or xml_fname=="styles.xml":
#         #        continue
#         if not xml_fname=="document.xml" and not xml_fname.startswith("header") and not xml_fname.startswith("footer"): continue
#         #if xml_fname=="numbering.xml": continue
#         #if xml_fname=="styles.xml": continue
        
#         #print xml_fname
#         cur_xml_path=os.path.join(extracted_dir,xml_fname)
#         with open(cur_xml_path) as fopen:
#             xml_content=fopen.read()
#         modified_xml_content=get_xml_paras(xml_content)
#         with open(cur_xml_path, "wb") as f:
#         #    #f.write(modified_xml_content.encode("UTF-8"))
#             f.write(modified_xml_content)                
    
#     os.remove(TEMP_ZIP)
#     shutil.make_archive(TEMP_ZIP.replace(".zip", ""), 'zip', TEMP_FOLDER)

#     # rename zip file to docx
#     os.rename(TEMP_DOCX+"2", TEMP_DOCX)
#     os.rename(TEMP_ZIP, out_fpath)
#     shutil.rmtree(TEMP_FOLDER)

