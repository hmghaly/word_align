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


# docx_fpath=""
# docx_copy_fpath=""
# zip_fpath=docx_copy_fpath.replace(".docx",".zip")
# tmp_extracted_folder_path=docx_copy_fpath.replace(".docx","")
# shutil.copy(docx_fpath, docx_copy_fpath)


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

