function init_OLD(){
    create_intro()
    
    stage1=set_stage("canvas1")
    bubble1=create_txt_bubble("أ",stage1.width*0.5,stage1.height*0.5)
    stage1.addChild(bubble1)
    
    
    
    coin_bitmap=add_image("img/hud_coins.png")
    stage1.addChild(coin_bitmap)
    coin_bitmap.visible=false;

    
    btn1=add_button("",stage1.width,stage1.height*0.1)
    btn1.x=stage1.width*0.5
    btn1.y=stage1.height*0.05
    
    stage1.addChild(btn1)
    
    avatar_bubble=create_img_bubble("img/avatars/024-boy-11.png",stage1.width*0.5,stage1.height*0.05,50)
    stage1.addChild(avatar_bubble)
    
    
    
    
    //btn=add_button_image("hello",250,60,"img/hud_coins.png")
    coin_bitmap2=add_image("img/hud_coins.png")
    coin_bitmap2.x=stage1.width*0.05
    coin_bitmap2.y=stage1.height*0.05
    
    stage1.addChild(coin_bitmap)
    
    stage1.addChild(coin_bitmap2)
    
    stage1.update()
    
    //coin_bitmap.hidden=true;
    
    stage1.on("stagemousedown", function(evt) {
        console.log("the canvas was clicked at "+evt.stageX+","+evt.stageY);
//        var randomColor = Math.floor(Math.random()*16777215).toString(16);
//        console.log(randomColor)
        //var [bub_x,bub_y]=[bubble1.x,bubble1.y]
        cur_dist=get_dist([bubble1.x,bubble1.y],[evt.stageX,evt.stageY])
        animation_time=cur_dist/speed
        //change_bubble_color(bubble1,randomColor)
        
//        createjs.Tween.get(bubble1, {loop: 0})
        createjs.Tween.get(bubble1, {loop: 0})
        .to({x: evt.stageX, y: evt.stageY}, animation_time, createjs.Ease.bounceOut)
        
        stage1.update()
    })
    locs=[["alif", stage1.width*0.25,stage1.height*0.25],
          ["baa2", stage1.width*0.25,stage1.height*0.75],
          ["thaa2", stage1.width*0.75,stage1.height*0.25],
          ["jeem", stage1.width*0.75,stage1.height*0.75]
         ]
    for (l0 in locs){
        var [text0,x0,y0]=locs[l0]
        var new_bub=create_txt_bubble(text0,x0,y0)
        stage1.addChild(new_bub)
        change_bubble_color(new_bub,random_color())
        bubble_list.push(new_bub)
        
    }

    //console.log(bubble1)
    //createjs.Ticker.addEventListener("tick", stage1);
    createjs.Ticker.on("tick", tick);
    createjs.Ticker.framerate = 180;
    stage2=set_stage("canvas2")
}

    
function check_collision(){
    var [bub1_x,bub1_y,bub1_radius]=[bubble1.x,bubble1.y,bubble1.radius]
    for (b0 in bubble_list){
        bub2=bubble_list[b0]
        //var [bub2_x,bub2_y,bub2_radius]=[bub2.x,bub2.y,bub2.radius]
        cur_dist=get_dist([bub1_x,bub1_y],[bub2.x,bub2.y])
        if (cur_dist<bub1_radius+bub2.radius){
            var [dx,dy]=[bub2.x-bub1_x,bub2.y-bub1_y]
            var [final_x,final_y]=[bub1_x+1.5*dx,bub1_y+1.5*dy]
            tween=createjs.Tween.get(bub2, {loop: 0})
                .to({x: final_x, y: final_y, scaleX: 0.1, scaleY: 0.1}, 500)
                .call(function(){
                    coin_bitmap.x=this.x
                    coin_bitmap.y=this.y
                    console.log("done")
                    this.parent.removeChild(this)
                    coin_bitmap.visible=true;
                    simple_tween(coin_bitmap,{x: stage1.width*0.05, y: stage1.height*0.05},0.3,function(){this.visible=false;})
                });
            bubble_list.splice(b0, 1);
            break
        }
    }
    
}

function simple_tween(cur_obj,dest_info,cur_speed,callback){
    distance=get_dist([cur_obj.x,cur_obj.y],[dest_info.x,dest_info.y])
    console.log(distance)
    travel_time=distance/cur_speed
    tween=createjs.Tween.get(cur_obj, {loop: 0})
    .to(dest_info, travel_time)
    .call(callback)
}
    
function tick() { 
//    console.log("TICK!!!"); 
    check_collision()
    stage1.update()
}    