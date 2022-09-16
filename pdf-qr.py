import time
from reportlab.lib.enums import TA_JUSTIFY
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
import qrcode

#a library to generate PDFs and QR codes - install the following
# !pip install pillow
# !pip install qrcode
# !pip install reportlab

def make_qr(url0,img_path0):
  qr = qrcode.QRCode(
          version=1,
          box_size=10,
          border=5)
  qr.add_data(url0)
  qr.make(fit=True)
  img = qr.make_image(fill='black', back_color='white')
  img.save(img_path0)

def gen_pdf(pdf_fpath0,pdf_content0): #content is a list of items per page
  styles=getSampleStyleSheet()
  styles.add(ParagraphStyle(name='Justify', alignment=TA_JUSTIFY))
  doc = SimpleDocTemplate(pdf_fpath0,pagesize=letter,
                          rightMargin=72,leftMargin=72,
                          topMargin=72,bottomMargin=18)
  Story=[]  
  for cur_items in pdf_content0:
    for item0 in cur_items:
      print(item0)
      if item0.get("type")=="image":
        im = Image(item0["src"], item0.get("width",2)*inch, item0.get("height",2)*inch)
        Story.append(im)
      if item0.get("type")=="text":
        cur_text_content=item0["text"]
        for line0 in cur_text_content.split("\n"):
          Story.append(Paragraph(line0, styles["Normal"]))
          Story.append(Spacer(1, 12)) 
    Story.append(PageBreak())
  doc.build(Story)         
      

# cur_pdf_content=[]
# cur_pdf_content.append([{"type":"image","src":"qrcode001.png","width":2,"height":2},
#                         {"type":"text","text":"hello \n what else \n more lines"},
#                         {"type":"image","src":"qrcode001.png","width":2,"height":2}
#                         ])
# cur_pdf_content.append([{"type":"image","src":"qrcode001.png","width":2,"height":2},
#                         {"type":"text","text":"second page \n yes it is"}
#                         ])

# gen_pdf("test4.pdf",cur_pdf_content)