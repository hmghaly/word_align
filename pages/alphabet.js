function makeAlphabet(stage) {
    var stageW = stage.width;
    var stageH = stage.height;
    var page = new Page(stageW, stageH, green,yellow);
    STYLE = {font:"reuben", size:50};
    
    new Label({color:purple, text:"Alphabet\nList", size:50,variant:true, align:CENTER}).pos(0,30,CENTER,TOP,page);
    menu_label=new Label({color:yellow, text:"Menu", size:25, align:CENTER})
    page.go2menu = new Button({width:140,height:60,backgroundColor:purple,rollBackgroundColor:orange,label:menu_label,corner:20})
    .pos(30,30,RIGHT,TOP,page)   
    tutorial_label=new Label({color:yellow, text:"Tutorial", size:25, align:CENTER})
    page.go2tutorial = new Button({width:140,height:60,backgroundColor:purple,rollBackgroundColor:orange,label:tutorial_label,corner:20})
    .pos(30,30,LEFT,TOP,page)   

    // MIDDLE REGION
	// WINDOW, WRAPPER

	var win = new Window({
        width:stageW*0.8,
        height:600,
        interactive:false,
        padding:10,
		corner:10,
		scrollBarDrag:true,
        backgroundColor:purple.darken(.5),
        borderColor:purple
    }).pos(0,50,CENTER,CENTER,page);
    
    //page.win=win

	const wrapper = new Wrapper({
		spacingH:20,
		spacingV:20
	});
    
    page.deploy_list=function(){
        const objects = []; //[new Circle(20, red), new Rectangle(30,30,red).rot(20).sca(2).reg(30,150), new Rectangle(30,30,orange), new Rectangle(30,30,blue), new Rectangle(30,30,green), new Rectangle(30,30,purple)];
//        for (const let0 of game_data.letter_ids){
//            console.log(let0)
//        }
        const colors = series(green,blue,pink,yellow,orange)
        y0=0
        y_offset=30
        zim.loop(game_data.letter_ids,function(item,i){
            //console.log(item,i)
            shapes=game_data.shape_dict[item]
            shapes.reverse();
            name=game_data.name_dict[item]
            //console.log(name,shapes)
            let rect0 = new Rectangle(stageW*0.8,100,colors)
            rect0.id=item
            name_ml=multiline(name,5)
            //new Label({text:name_ml, color:black,  size:30}).center(rect0)
            new Label({text:name_ml, color:black,  size:30}).pos(30,0, LEFT,CENTER,rect0)
            
            //circle.pos(30,y0,page.win)
            x0=stageW*0.3
            objects.push(rect0);
            for (const sh of shapes){
                let circle = new Circle(30, purple);
                new Label({text:sh, color:color, align:CENTER, size:circle.radius}).centerReg(circle);
                circle.pos(x0,0,LEFT,CENTER,rect0)
                x0+=70
                //objects.push(circle);
            }
            rect0.tap(function(evt){
                trg=evt.currentTarget
                console.log(trg)
                frame.asset(trg.id).play()
            })
            
            //y0+=y_offset
        })
        //new Label({text:"", color:color, align:CENTER, size:circle.radius}).rot(rand(-10,10)).centerReg(circle);
        let rect0 = new Rectangle(stageW*0.8,50,white).alp(0)
        objects.push(rect0);
        
        //const letters = series("WRAPPER".split(""));
        //const letters = game_data.letter_ids.map(x => game_data.shape_dict[x][0])
//        zim.loop(letters.array.length*7, function (item, i) {
//            console.log(item,i)
//            let circle = new Circle({min:20, max:40}, colors);
//            new Label({text:letters(), color:color, align:CENTER, size:circle.radius}).rot(rand(-10,10)).centerReg(circle);
//            objects.push(circle);
//        });
        wrapper.add(objects)
        win.add(wrapper).addTo(page);        
    }
    //page.deploy_list()


    
    return page;
    
}
