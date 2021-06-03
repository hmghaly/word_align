function draw_text(text_str,x,y){
  //var newText = document.createElementNS(svgNS,"text");
  //svgNS=document.getElementById("tree_svg")
  var newText = document.createElementNS('http://www.w3.org/2000/svg',"text");    
  newText.setAttributeNS(null,"x",x);      
  newText.setAttributeNS(null,"y",y);  
  newText.setAttributeNS(null,"dominant-baseline","middle");  
  newText.setAttributeNS(null,"text-anchor","middle");      
  //text_str=text_str.split("-")[0]
//  var textNode = document.createElement("div") 
//  textNode.innerHTML=text_str
  var textNode = document.createTextNode(text_str);
  newText.appendChild(textNode)    
  return newText
}

function draw_foreign(text_str,x,y,w,h){
  var foreign_obj = document.createElementNS('http://www.w3.org/2000/svg',"foreignObject");    
  foreign_obj.setAttributeNS(null,"x",x);      
  foreign_obj.setAttributeNS(null,"y",y); 
    foreign_obj.setAttributeNS(null,"width",w); 
    foreign_obj.setAttributeNS(null,"height",h); 
    var text_div = document.createElement("div") 
    text_div.xmlns="http://www.w3.org/1999/xhtml"
    text_div.innerHTML=text_str
    text_div.style.textAlign="center"
//    text_div.style.backgroundColor="green"
    //text_div.innerHTML="Something<br><b>else</b> and more <i>hhii</i>"
//  foreign_obj.setAttributeNS(null,"dominant-baseline","middle");  
//  foreign_obj.setAttributeNS(null,"text-anchor","middle");      
    

  foreign_obj.appendChild(text_div)    
  return foreign_obj
    
}

function draw_line(x1,y1,x2,y2){
        //<text x="20%" y="80%"  fill="red" dominant-baseline="middle" text-anchor="middle">20x-80y</text>
//    text_el=document.createElement("text")
//    tree_svg=document.getElementById("tree_svg")
    //<line id="connector1" x1="0" y1="0" x2="200" y2="200" style="stroke:rgb(255,0,0);stroke-width:2;position:absolute;" />
    var line = document.createElementNS('http://www.w3.org/2000/svg', 'line');
    line.setAttribute('x1',x1);
    line.setAttribute('y1',y1);
    line.setAttribute('x2',x2);
    line.setAttribute('y2',y2);
    line.setAttribute('style',"stroke:rgb(255,0,0);stroke-width:2;position:absolute;");
    return line
//    line.setAttribute('fill',"red");
//
//    rect.setAttribute('fill','#fff');
//    rect.setAttribute('stroke','#000');
//    rect.setAttribute('stroke-width','2');
//    rect.setAttribute('rx','7');    
}

function draw_circle(cx,cy,r){
    var circle = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
    circle.setAttribute('cx',cx);
    circle.setAttribute('cy',cy);
    circle.setAttribute('r',r);
    circle.setAttribute('stroke',"black");
    circle.setAttribute('stroke-width',"3");
    circle.setAttribute('fill',"red");
    return circle
}

function draw_circle_text(txt0,x0,y0,r){
    grp0=document.createElementNS('http://www.w3.org/2000/svg', 'g');
    circle_el=draw_circle(x0,y0,r)
    txt_el=draw_text(txt0,x0,y0)
    txt_el.textLength=2*r
    grp0.appendChild(circle_el)
    grp0.appendChild(txt_el)
    return grp0
    
}

function draw_circle_text2(txt0,x0,y0,r){
    grp0=document.createElementNS('http://www.w3.org/2000/svg', 'g');
    circle_el=draw_circle(x0,y0,r)
    foreign_el_w=30
    foreign_el_h=30
    foreign_el_x=parseInt(x0)
    foreign_el_y=parseInt(y0)
    foreign_el_x=parseInt(x0)-0.5*foreign_el_w
    foreign_el_y=parseInt(y0)-0.05*foreign_el_h
//    console.log(x0,y0, foreign_el_x, foreign_el_y)
    
    foreign_el=draw_foreign(txt0,percent(foreign_el_x),percent(foreign_el_y),percent(foreign_el_w),percent(foreign_el_h))
//    txt_el=draw_text(txt0,x0,y0)
    grp0.appendChild(circle_el)
    grp0.appendChild(foreign_el)
//    console.log(foreign_el)
//    console.log(foreign_el.getBoundingClientRect())
//    console.log(foreign_el.getCTM())
//    console.log(foreign_el.getBBox())
    
    return grp0
    
}

//<circle cx="50" cy="50" r="40" stroke="black" stroke-width="3" fill="red" />

phrases=[
    ["PRO1",0,0,"NP1",1],
    ["NP1",0,0,"S1",2],
    ["V1",1,1,"VP1",1],
    ["VP1",1,4,"S1",4],
    ["PP1",2,4,"VP1",3],
    ["IN1",2,2,"PP1",1],
    ["NP2",3,4,"PP1",2],
    ["DET1",3,3,"NP2",1],
    ["NN1",4,4,"NP2",1],
    ["S1",0,4,"",5]
]



function gen_tree(list_phrases){
    tree_svg=document.getElementById("tree_svg")
    start_y=80
    end_y=0
    margin_y=3
    n_levels=7
    n_words=12
//    n_words=Math.max.apply(Math, arr.map(function (i) {
//        return i[2];
//    }))
    //console.log();
    
    step_y=(end_y-start_y)/n_levels // we can later adjust by number of levels
    step_x=100/(1+n_words)
    console.log("step_x",step_x)
    child_parent_dict={}
    el_loc_dict={}
    for (ph in list_phrases){
        cur_phrase=list_phrases[ph]
        var [ph_label,i0,i1,ph_parent,ph_level] = cur_phrase
        
        avg_i=(i0+i1)/2
        cur_x=step_x*(avg_i+1)
        cur_y=start_y+step_y*ph_level
        el_loc_dict[ph_label]=[cur_x,cur_y]
        if (ph_parent!="") child_parent_dict[ph_label]=ph_parent
        cur_x=""+cur_x+"%"
        cur_y=""+cur_y+"%"
        console.log(ph_label,cur_x,cur_y,avg_i)
        text_node=draw_text(ph_label,cur_x,cur_y)
        tree_svg.appendChild(text_node)        
        
    }
    for (child0 in child_parent_dict){
        parent0=child_parent_dict[child0]
        //if (parent0=="") return
        var [child_x,child_y]=el_loc_dict[child0]
        var [parent_x,parent_y]=el_loc_dict[parent0]
        child_y=child_y-margin_y
        parent_y=parent_y+margin_y
        cur_line=draw_line(percent(child_x) ,percent(child_y),percent(parent_x),percent(parent_y))
        tree_svg.appendChild(cur_line)        
        
    }
}