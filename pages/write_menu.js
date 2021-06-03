
function makeWritingMenu(stage) {
    
    var stageW = stage.width;
    var stageH = stage.height;
    var page = new Page(stageW, stageH, red,yellow);
    page.i=0;
    STYLE = {font:"reuben", size:50};

//    menu_label=new Label({color:yellow, text:"Menu", size:25, align:CENTER})
//    page.go2menu = new Button({width:150,height:60,backgroundColor:purple,rollBackgroundColor:orange,label:menu_label,corner:20})
//    .pos(20,20,LEFT,TOP,page) 
    //menu_label=new Label({color:yellow, text:"5Write", size:60, align:CENTER})
    title=new Label({color:purple, text:"Write5", size:60,variant:true}).pos(0,50,CENTER,TOP,page);

    writing_letters_label=new Label({color:yellow, text:"Letters", size:60, align:CENTER})
    page.write_letters = new Button({width:350,height:100,backgroundColor:purple,rollBackgroundColor:orange,label:writing_letters_label,corner:20})
    .pos(0,-200,CENTER,CENTER,page)

    writing_letter_shapes_label=new Label({color:yellow, text:"Letter Shapes", size:60, align:CENTER})
    page.write_letter_shapes  = new Button({width:350,height:100,backgroundColor:purple,rollBackgroundColor:orange,label:writing_letter_shapes_label,corner:20})
    .center(page)
    
    
    writing_words_label=new Label({color:yellow, text:"Words", size:60, align:CENTER})
    page.write_words = new Button({width:350,height:100,backgroundColor:purple,rollBackgroundColor:orange,label:writing_words_label,corner:20})
    .pos(0,200,CENTER,CENTER,page)
    
    
    //write_letter_shapes, write_letters, write_words,  page.prepare
//    .tap(function(evt){
////        trg=evt.currentTarget
////        remove_el(trg)
//        page.prepare("words")
//        //page.deploy()
//    })
    
    page.prepare=function(wlist_type="letters"){
        quiz.writing_list=[]
        if (wlist_type=="letters"){
            for (const let_id of game_data.all_ids){
                cur_name=game_data.name_dict[let_id]
                if (cur_name==null || cur_name=="") continue
                letter_ar_script=game_data.letter_dict[let_id].arabic_script
                quiz.writing_list.push({id:let_id,shape:letter_ar_script,name:cur_name})
            }            
        }
        if (wlist_type=="shapes"){
            for (const let_id of game_data.all_ids){
                cur_name=game_data.name_dict[let_id]
                if (cur_name==null || cur_name=="") continue
                cur_let_shapes=game_data.shape_dict[let_id].slice(0,4)
                for (const shape0 of cur_let_shapes){
                    quiz.writing_list.push({id:let_id,shape:shape0,name:cur_name})
                }
            }            
        }
        if (wlist_type=="words"){
            //console.log(game_data.animals_ids)
            for (const word_id of game_data.animals_ids){
                cur_name=game_data.word_dict[word_id].english
                cur_word=game_data.word_dict[word_id].plain
                quiz.writing_list.push({id:word_id,shape:cur_word,name:cur_name})
            }            
        }        
//        for (const let_id of game_data.all_ids){
//            cur_name=game_data.name_dict[let_id]
//            if (cur_name==null || cur_name=="") continue
//            letter_ar_script=game_data.letter_dict[let_id].arabic_script
////            cur_let_shapes=game_data.shape_dict[let_id].slice(0,4)
////            cur_let_shapes.reverse()
////            cur_shape=cur_let_shapes.join(" ") //we should expand to all the shapes
//            
//            quiz.writing_list.push({id:let_id,shape:letter_ar_script,name:cur_name})
//        }
        zog(quiz.writing_list)
    }
    
    
    return page
}