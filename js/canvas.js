function get_dist(pt1, pt2) { //get the Euclidean distance between two points
    var [x1,y1]=pt1
    var [x2,y2]=pt2
    delta_x=x2-x1
    delta_y=y2-y1
    return Math.sqrt(Math.pow(delta_x,2)+Math.pow(delta_y,2)) 
}

function bring2front(cur_obj){
    par=cur_obj.parent
    cur_obj.new_index=par.numChildren+1
    cur_obj.original_index=par.getChildIndex(cur_obj)
    par.setChildIndex(cur_obj,cur_obj.new_index)
}
function send2back(cur_obj){
    par=cur_obj.parent
    par.setChildIndex(cur_obj,cur_obj.original_index)
}


function draw_bubble_img(x,y,img_obj,color="red",txt="",txt_style="bold 12px Arial",txt_color="#FFF",radius=50,max_height=100,max_width=100,secondary_obj=null,secondary_above=false){
    var bubble = new createjs.Container();
    var circle = new createjs.Shape();
    circle.graphics.beginFill(color).drawCircle(x, y, radius); //we will need to make the color adaptive 
    cur_bmp=draw_bitmap(x,y,img_obj,max_height,max_height)

    var label = new createjs.Text(txt, txt_style, txt_color);
//    label.name = "label";
    label.textAlign = "center";
    label.textBaseline = "top";
    label.x=x;
    label.y=y+radius+2;
    bubble.addChild(circle,cur_bmp,label)
    
    if (secondary_obj!=null){
        secondary_obj.x=x+radius/2;
        if (secondary_above) secondary_obj.y=y-radius/2;
        else secondary_obj.y=y+radius/2;
        bubble.addChild(secondary_obj)
    }
    return bubble
}

//text -img_obj, radius, color
function draw_bubble(x,y,text="",color="red",radius=50,txt_style="bold 36px Arial",txt_color="#FFF"){
    var bubble = new createjs.Container();
    var circle = new createjs.Shape();
    circle.graphics.beginFill(color).drawCircle(0, 0, radius); //we will need to make the color adaptive
    circle.name="circle"
    bubble.addChild(circle);
    var label = new createjs.Text(text, txt_style, txt_color);
    label.textAlign = "center";
    label.textBaseline="middle"
    bubble.addChild(circle,label); 
    bubble.x=x;
    bubble.y=y;
    return bubble
}

function draw_bubble_old(x,y,text="",img_obj=null,color="red",radius=50,style="bold 36px Arial",img_scale=0.75){ //a circle with text
    var bubble = new createjs.Container();
    var circle = new createjs.Shape();
//    radius=50 //we will need to make it adpative
    circle.graphics.beginFill(color).drawCircle(0, 0, radius); //we will need to make the color adaptive
    circle.name="circle"
    bubble.addChild(circle);
    
    if (text!=""){
        var label = new createjs.Text(text, style, "#FFFFFF");
        label.textAlign = "center";
        label.textBaseline="middle"
        bubble.addChild(label); 
    }
    if (img_obj!=null){
        bmp=bitmap(img_obj)
        bubble.addChild(bmp); 
        if (bmp.width>2*radius || bmp.height>2*radius){
            cur_scale=2*radius/(Math.min(bmp.width,bmp.height))
            bmp.scaleX=bmp.scaleY=cur_scale*img_scale;            
        }
    }
    bubble.x=x;
    bubble.y=y;
    bubble.radius=radius;
    return bubble
}


function draw_circle(x,y,radius,color){
    var circle = new createjs.Shape();
//    radius=50 //we will need to make it adpative
    circle.graphics.beginFill(color).drawCircle(x, y, radius); //we will need to make the color adaptive
    return circle
}

function draw_bitmap(x,y,img_obj,max_height=100,max_width=100){
    var bitmap = new createjs.Bitmap(img_obj);
    bitmap.regX=img_obj.width*0.5
    bitmap.regY=img_obj.height*0.5
    bitmap.width=img_obj.width
    bitmap.height=img_obj.height
    min_scale=Math.max(max_width/bitmap.width,max_height/bitmap.height)
    bitmap.scaleX=min_scale
    bitmap.scaleY=min_scale
    bitmap.x=x;
    bitmap.y=y;
    return bitmap  
}


function draw_line(x0,y0,x1,y1){
    var shape = new createjs.Shape();
    //shape.graphics = new createjs.Graphics().beginLinearGradientStroke(["red", "blue"], [0, 1], 5, 0, 110, 0).moveTo(x0, y0).lineTo(x1, y1);
    shape.graphics = new createjs.Graphics().beginStroke("red").moveTo(x0, y0).lineTo(x1, y1);
    return shape
}

function draw_poly(){
    var container1=new createjs.Container();
    y_offset=50
    y0=0.1*h
    
    line1=draw_line(0.1*w,y0,0.9*w,y0)
    y1=y0+y_offset
    line2=draw_line(0.1*w+y_offset*.5,y1,0.9*w-y_offset,y1)
    y2=y1+y_offset
    y3=y2+y_offset
    line3=draw_line(0.1*w+y_offset*0.5,y2,0.9*w-y_offset,y2)
    y4=y3+y_offset
    y5=y4+y_offset
    
    
    
    arc1=draw_arc(0.9*w-y_offset,y0,0,90,y_offset,"blue")
    //line1=draw_line(w/10,h/10,9*w/10,h/10)
    arc2=draw_arc(0.1*w+y_offset*.5,y1+y_offset*0.5,90,270,y_offset*0.5,"red")
    //line2=draw_line(8*w/10,h/5,2*w/10,h/5)
    arc3=draw_arc(0.9*w-y_offset,y4,270,90,y_offset,"red")
    container1.addChild(line1,line2,line3,arc1,arc2,arc3)

    
    //shape.graphics = new createjs.Graphics().beginStroke("red").moveTo(50, 50).arcTo(400, 50, 400, 600, 50);
    return container1

}

function draw_arc(x0,y0,angle1,angle2,radius,color="red"){
    var shape=new createjs.Shape().set({x:x0, y:y0});
    //shape.graphics.s("#f00").ss(1);
    shape.graphics.s(color).ss(1);
    var startAngle = angle1 * Math.PI/180;
    var endAngle = angle2 * Math.PI/180;
    //shape.graphics.moveTo(0,0)
    shape.graphics.arc(0,0,radius,startAngle,endAngle);
    return shape
}

function change_bubble_color(bubble_obj,new_color){
    bubble_obj.children[0].graphics._fill.style=new_color
}    


function change_color(element,new_color){
    element.graphics._fill.style=new_color
}

function animated_msg(msg_txt_str,x,y,callback_fn,txt_style="bold 24px Comic",txt_color="#000",delay=1000){
    msg_text=draw_text(x,y,msg_txt_str,txt_style,txt_color)
    stage.addChild(msg_text)        
    createjs.Tween.get(msg_text, {loop: 0})
    .to({scaleX: 2, scaleY: 2}, delay, createjs.Ease.bounceOut)  
    .call(function(){
       this.parent.removeChild(this) 
        callback_fn()
        //gen_lesson_quiz()
    })   
    
}


function shake_horizontal(cur_obj,delay=100){      
    cur_x=cur_obj.x
    createjs.Tween.get(cur_obj, {loop: 0})
    .to({x: cur_x+10}, delay)      
    .to({x: cur_x-10}, delay*2)      
    .to({x: cur_x}, delay)      
}

//recursively look for an element on the stage with a certain name -it will retrieve only one item
function get_child(parent1,name){
    //console.log(parent1.name)
    children=parent1.children
    if (parent1.children!=undefined && parent1.children!=null){
        //console.log(">>>>", parent1.children)
        check=parent1.getChildByName(name)
        if (check!=null) return check
        for (ch in parent1.children){
            //console.log("children", parent1.children)
            child0=parent1.children[ch]
            check2=get_child(child0,name)
            if (check2) return check2
        } 
    }
}

//recursively look for an element on the stage with a certain ID
//function get_children_by_id(parent,id0){
////    check=parent.getChildByName(name)
////    if (check!=null) return check
//    cur_children=parent.children
//    if (cur_children==null || cur_children==undefined) return
//    //console.log(parent,cur_children)
//    for (cc in cur_children){
//        //console.log(">>>", cur_children)
//        if (cur_children==undefined) continue
//        child0=cur_children[cc]
//        if (child0==null|| child0==undefined|| child0.id==undefined) continue
//        if (child0.id==id0) return child0
//        recursive_check=get_children_by_id(child0,id0)
//        if (recursive_check!=null){
//            return recursive_check
//        }
//    }  
//}

//function set_stage_OLD(canvas_id,max_canvas_width=500,max_canvas_height=400){
//        var win = window,
//        doc = document,
//        e = doc.documentElement,
//        g = doc.getElementsByTagName('body')[0],
//        xS = win.innerWidth || e.clientWidth || g.clientWidth,
//        yS = win.innerHeight|| e.clientHeight|| g.clientHeight;
//    //if (max_canvas_width !== undefined) max_canvas_width=500;
//    
//    if (xS<max_canvas_width) $$(canvas_id).width=xS //for small devices fill the screen, but use max width large devices
//    else $$(canvas_id).width=max_canvas_width
//    $$(canvas_id).height=Math.min(yS,max_canvas_height)
//    
//    //console.log($$(canvas_id))
//    var cur_stage = new createjs.Stage(canvas_id);
//    cur_stage.removeAllChildren()
//    createjs.Touch.enable(cur_stage);
//    cur_stage.mouseMoveOutside = true; 
//    cur_stage.width=$$(canvas_id).width
//    cur_stage.height=$$(canvas_id).height
//    w=$$(canvas_id).width //gloabal w and h
//    h=$$(canvas_id).height
//    
//    return cur_stage
//}   

function set_stage(canvas_id){
    var cur_stage = new createjs.Stage(canvas_id);
    cur_stage.removeAllChildren()
    createjs.Touch.enable(cur_stage);
    cur_stage.mouseMoveOutside = true; 
    //console.log(cur_stage)
    return cur_stage
}

function draw_text(x,y,txt_str,txt_style="bold 24px Arial",txt_color="#FFFFFF"){
//    var label = new createjs.Text(txt, "bold 24px Arial", "#FFFFFF");
    var label = new createjs.Text(txt_str, txt_style, txt_color);
//    label.name = "label";
    label.textAlign = "center";
    label.textBaseline = "middle";
    label.x=x;
    label.y=y;
    return label
}   

//simple background rectangle
function draw_rect(rect_x,rect_y,rect_w,rect_h,rect_color,rect_r=0){
    var cur_rect = new createjs.Shape();
    cur_rect.graphics.beginFill(rect_color).drawRoundRect(0, 0, rect_w, rect_h, rect_r);
    cur_rect.regX=rect_w*0.5
    cur_rect.regY=rect_h*0.5
    cur_rect.x=rect_x
    cur_rect.y=rect_y
    return cur_rect
}

//function draw_button_OLD(x,y,text="",img_obj,color="red",btn_w=150,btn_h=60,border_r=10,txt_style="bold 24px Arial",txt_color="#FFFFFF"){
//    var button = new createjs.Container();
//    var btn_background = new createjs.Shape();
//    btn_background.name = "background";
//    btn_background.graphics.beginFill(color).drawRoundRect(0, 0, btn_w, btn_h, border_r);
//    btn_background.regX=btn_w*0.5
//    btn_background.regY=btn_h*0.5
//    button.addChild(btn_background); 
//    if (text!=""){
//        var label = new createjs.Text(text, txt_style, txt_color);
//        label.name = "label";
//        label.textAlign = "center";
//        label.textBaseline = "middle";    
//        button.addChild(label); 
//    }
//    button.x=x
//    button.y=y
//    //button.name = "button";
//    //button.addChild(btn_background, label); 
//    //console.log(label)
//    return button
//}    

function draw_text_test(x,y,text="",txt_style="bold 24px Arial",txt_color="#FFFFFF"){
    var label = new createjs.Text(text, txt_style, txt_color);
    label.textAlign = "center";
    label.textBaseline = "top";    
    label.x=x
    label.y=y
    lbh=label._getBounds().height //to account for multiline texts
    //lbw=label._getBounds().width 
//    min_scale=1
//    if (lbw>btn_w) min_scale=0.95*Math.min(min_scale,btn_w/lbw)
//    if (lbh>btn_h) min_scale=0.95*Math.min(min_scale,btn_h/lbh)
//    label.scaleX=min_scale
//    label.scaleY=min_scale
    label.y-=lbh/2 //we shift the y of the button text to half its width
    //label.y-=min_scale*lbh/2 //we shift the y of the button text to half its width
    return label
}

function rectangle_item(cur_item){
    cur_h=cur_item._getBounds().height //to account for multiline texts  
    cur_w=cur_item._getBounds().width     
    cur_x=cur_item._getBounds().x+cur_w*0.5 //to account for multiline texts  
    cur_y=cur_item._getBounds().y+cur_h*0.5
//    cur_x=cur_left+0.5*cur_w
//    cur_y=cur_top+0.5*cur_h
    cur_rect=draw_rect(cur_x,cur_y,cur_w,cur_h,"blue",0)
    return cur_rect
}

function draw_button(x,y,text="",img_obj=null,color="red",btn_w=150,btn_h=60,border_r=10,txt_style="bold 24px Arial",txt_color="#FFFFFF"){
    var button = new createjs.Container();
    var btn_background = new createjs.Shape();
    btn_background.name = "background";
    btn_background.graphics.beginFill(color).drawRoundRect(0, 0, btn_w, btn_h, border_r);
    btn_background.regX=btn_w*0.5
    btn_background.regY=btn_h*0.5
    button.addChild(btn_background); 
    if (text!=""){
        //var label = draw_text(0,0,text,txt_style,txt_color)
        //lb= draw_text(w/2,h/2,"text1 and\nother text\nwe need to do","bold 24px Arial","#FFFFFF")
        
        var label = new createjs.Text(text, txt_style, txt_color);
        //label.name = "label";
        label.textAlign = "center";
        label.textBaseline = "top";    
        button.addChild(label); 
        lbh=label._getBounds().height //to account for multiline texts
        
        
        lbw=label._getBounds().width 
        min_scale=1
        if (lbw>btn_w) min_scale=0.95*Math.min(min_scale,btn_w/lbw)
        if (lbh>btn_h) min_scale=0.95*Math.min(min_scale,btn_h/lbh)
        label.scaleX=min_scale
        label.scaleY=min_scale
        
        label.y-=min_scale*lbh/2 //we shift the y of the button text to half its width
        
    }
    button.x=x
    button.y=y
    //button.name = "button";
    //button.addChild(btn_background, label); 
    //console.log(label)
    return button
}    

function multicolor_txt(x,y,list_str_color=[],ltr=true,txt_style="bold 24px Arial"){
    txt_container=new createjs.Container()
    //list_str_color=[["A","red"],["L","green"],["I","blue"],["F","Magenta"]]
    x0=0;
    for (it in list_str_color){
        var [cur_obj,txt_color]=list_str_color[it]
        //console.log(cur_obj,txt_color)
        if (typeof cur_obj === 'string' || cur_obj instanceof String) var label = new createjs.Text(cur_obj, txt_style, txt_color);
        else {
            var label = cur_obj;
            label.regX=0;
        } 
        lbw=label._getBounds().width
        //alert(lbw)
        //label.name = "label";

 
        label.x=x0;
        label.textBaseline = "middle";
        txt_container.addChild(label)
        if (ltr){
            label.textAlign = "left";        
            x0+=lbw            
        }
        else {
            label.textAlign = "right";        
            x0-=lbw             
        }

    }
    txt_container_w=txt_container._getBounds().width
    txt_container_h=txt_container._getBounds().height
    
    txt_container.regX=txt_container_w*0.5
    txt_container.regY=txt_container_h*0.5    
    //alert(txt_container_w)
    txt_container.x=x//+txt_container_w*0.5;
    txt_container.y=y;
    txt_container.w=txt_container_w
    txt_container.f=txt_container_h
    txt_container.top=y+0.5*txt_container_h
    txt_container.bottom=y+0.5*txt_container_h
    
    return txt_container
}

function add_timer(remaining_time,x0,y0,callback_fn,cur_txt_style="bold 48px Arial",cur_txt_color="#F0A"){
    timer_text=draw_text(x0,y0,""+remaining_time,cur_txt_style,cur_txt_color)
    //stage.addChild(timer_text)
    
    tw=createjs.Tween.get(timer_text, {loop: -1})
        .wait(1000)
        .call(function(){
            cur_remaining_time=Number(this.text)
            cur_remaining_time-=1;
            this.text=""+cur_remaining_time
            if (cur_remaining_time ==0){
                this.parent.removeChild(this)
                callback_fn()
                //alert("Time is Up")
            }
            //console.log("Hello")

        })  
    return timer_text
}

function add_button_image(txt,btn_w,btn_h,img_src){
    var btn=add_button(txt,btn_w,btn_h)
    var bmp0=add_image(img_src)
    bmp0.x=btn_w*0.75
    bmp0.y=btn_h*0.5
    btn.addChild(bmp0)
    return btn
}



function add_text_OLD(txt_str,txt_style,txt_color){
//    var label = new createjs.Text(txt, "bold 24px Arial", "#FFFFFF");
    var label = new createjs.Text(txt_str, txt_style, txt_color);
//    label.name = "label";
    label.textAlign = "center";
    label.textBaseline = "middle";
    return label
}   

function add_text_xy(txt_str,txt_style,txt_color,x,y){
    var txt0=add_text(txt_str,txt_style,txt_color)
    txt0.x=x
    txt0.y=y
    return txt0
}

function add_btn_xy(txt_str,color,w0,h0,x,y){
    var btn0= add_button_full(txt_str,w0,h0,color)
//    var txt0=add_text(txt_str,txt_style,txt_color)
    btn0.x=x
    btn0.y=y
    return btn0
}
    
    
function random_color(){
    shuffle(colors)
    return colors[0]
}

function create_html_el(x,y,width,height,inner_html,canvas_id){
    var html = document.createElement('div');
//    html.id = 'ab';
    html.style.height = ''+height +'px';
    html.style.width = ''+width+ 'px';
    //html.style.backgroundColor = "Blue" //'#000000';
    html.style.position = "absolute";
    html.style.textAlign="center"
    //html.style.textAlign="left"
    html.style.verticalAlign = "middle";
    html.className="embed"
    html.innerHTML=inner_html;
    //html.hidden=true;
//    html.innerHTML='<h1 id="html_obj" dir="rtl"><span style="color:Green;">كَـ</span><span style="color:deeppink;">ـلـ</span><span style="color:blue;">ـب</span></h1>'
//    html.style.top = 0;
//    html.style.left = 0;
    var cur_canvas=$$(canvas_id)
    html.style.top = ""+ cur_canvas.getBoundingClientRect().top+"px";
    html.style.left =""+ cur_canvas.getBoundingClientRect().left+"px";

    document.body.appendChild(html);

    var gg = new createjs.DOMElement(html); //should be the same as the input width and height
    html_w=html.getBoundingClientRect().width;
    html_h=html.getBoundingClientRect().height;
    //console.log(html_w,html_h)
    gg.regX=html_w*0.5
    gg.regY=html_h*0.5    
    
    gg.x = x;
    gg.y = y;
//    gg.scaleX=2;
//    gg.scaleY=2;
    return gg
    
}


function create_html_el_OLD(){
    var html = document.createElement('div');
    html.id = 'ab';
    html.style.height = '50px';
    html.style.width = '100px';
    //html.style.backgroundColor = '#000000';
    html.style.position = "absolute";
    html.style.textAlign="center"
    html.innerHTML='<h1 id="html_obj" dir="rtl"><span style="color:Green;">كَـ</span><span style="color:deeppink;">ـلـ</span><span style="color:blue;">ـب</span></h1>'
//    html.style.top = 0;
//    html.style.left = 0;
    html.style.top = ""+ $$("canvas2").getBoundingClientRect().top+"px";
    html.style.left =""+ $$("canvas2").getBoundingClientRect().left+"px";

    document.body.appendChild(html);

    var gg = new createjs.DOMElement(html);
    html_w=html.getBoundingClientRect().width;
    html_h=html.getBoundingClientRect().height;
    console.log(html_w,html_h)
    gg.regX=html_w*0.5
    gg.regY=html_w*0.5    
    
    gg.x = stage2.width*0.5;
    gg.y = stage2.height*0.5;
    gg.scaleX=2;
    gg.scaleY=2;
    
}