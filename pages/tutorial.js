tutorial_items=[
`Arabic has 28 letters. Let’s learn their sounds, names and shapes.

Press "Next" to continue the tutorial, otherwise press "Skip to Menu"
`,    
`Some Arabic sounds have no equivalent English letters, so we use numbers that look like the letter with this sound, as you can see below.
2 ء 
3 ع
7 ح
`,
`Other Arabic sounds have no one letter equivalent in English, so we use letter combinations:
kh خ
gh غ
dh ذ
th ث
sh ش
`,
`Some letters have a “stronger” sound. We use capital letters to show the sound difference of these letters.
s س	S ص
t ت T ط
d د D ض
dh ذ DH ظ
`,
`The character hamzah is a glottal stop, like the sound in the middle of “uh-oh”. It is not always considered an alphabet letter, but  it can be combined with other letters
hamzah = ء
hamzah 3ala nabrah = ئ
hamzah 3ala waaw = ؤ

Water- maa2- ماء 
 Question - su2aal - سؤال
Liquid - saa2il - سائل
`,
`The letter taa2 marbootah is a version of the letter taa2. It comes at the end of the word. It can be pronounced as either “h” or “t” depending on the context. 
ة ـة
 Fish - samakah - سمكة 
`,
`The letter alif can be combined with hamzah and maddah to change its sound
alif = ا
alif + hamzah = أ
alif + hamzah maksoorah (has an “i” sound) = إ
alif with maddah (long aa sound) = آ
 People - naas - ناس
 Mouse - fa2r - فأر
 Production - intaaj - إنتاج
 Machine -aalah - آلة
`,
`When the letter laam comes before alif, it forms a new character combination, called laam alif. This character combination can include the different forms of alif.
ل + ا = لا
لا
لأ
لآ
لإ
`,
`When the letter alif comes at the end of the word, sometimes it is written as “alif layyenah”, a character that looks like yaa2 but without dots
ى
Examples:
Hospital - mostashfaa - مستشفى
`,
`Letters take different shapes depending on their position within words. These shapes can be when the letter is separate, in the beginning, in the middle or at the end of a word.
The letter kaaf
ك كـ ـكـ ـك
Examples
Dog - kalb - كلب
Fish - samakah - سمكة
King - malik - ملك
Thorns - shawk - شوك
`     
]

tutorial_titles=[
    "Overview",
    "Sounds - why numbers?",
    "Sounds - letter combinations",
    "Sounds - capital letters",
    "Extended Letters - hamzah: ء",
    "Extended Letters - taa2 marbootah: ة",
    "Extended Letters - alif forms: ا",
    "Extended Letters - laam alif: لا",
    "Extended Letters - alif layyenah: ى",
    "Letter Shapes"            
]
var totorial_label;
var rect0;

function makeTutorial(stage) {
    
    var stageW = stage.width;
    var stageH = stage.height;
    var page = new Page(stageW, stageH, green,yellow);
    page.i=0;
    STYLE = {font:"reuben", size:50};

    menu_label=new Label({color:yellow, text:"Skip to Menu", size:25, align:CENTER})
    page.go2menu = new Button({width:stageW*0.8,height:60,backgroundColor:purple,rollBackgroundColor:orange,label:menu_label,corner:20})
    .pos(0,150,CENTER,CENTER,page)   

    
    new Label({color:purple, text:"Tutorial", size:45,variant:true}).pos(0,70,CENTER,TOP,page);
    
    //new Label({color:black, text:"Click the play button below to listen to tutorial.\nClick the alphabet button for the list of all letters", size:25}).pos(0,150,CENTER,CENTER,page);
    
    page.deploy_tutorial=function(){
        tutorial_text=multiline(tutorial_items[page.i],20)
        tutorial_number=page.i+1
        tutorial_progress_str=""+tutorial_number +"/"+tutorial_titles.length
        title_str=multiline(tutorial_titles[page.i],30)
        full_title_text=tutorial_progress_str+"\n"+title_str
        page.main_cont = new Container(stageW, stageH).addTo(page);
        new Label({color:purple, text:full_title_text, size:30,variant:true, align:CENTER}).pos(0,120,CENTER,TOP,page.main_cont);

        var win = new Window({
            width:stageW*0.8,
            height:stageH*0.4,
            interactive:true,
            padding:10,
            corner:10,
            scrollBarDrag:true,
            backgroundColor:purple.darken(.5),
            borderColor:purple
        }).pos(0,-50,CENTER,CENTER,page.main_cont);

        //page.win=win

        const wrapper = new Wrapper({
            spacingH:20,
            spacingV:20
        });
        const objects = []; 
        
        //rect0 = new Rectangle(stageW*0.8,stageH,blue)
        totorial_label=new Label({color:yellow, text:tutorial_text, size:30, align:CENTER})//.pos(30,0, LEFT,CENTER,rect0)
        rect_h=totorial_label.getBounds().height+10;
        
        rect0 = new Rectangle(stageW*0.8-20,rect_h,purple.darken(.5))
        totorial_label.pos(0,10, CENTER,TOP,rect0)

        

        
        
        //totorial_label=new Label({color:yellow, text:tutorial_text, size:30, align:CENTER})//.pos(0,0,CENTER,CENTER);
            
//        name_ml=multiline(name,5)
//        new Label({text:name_ml, color:black,  size:30}).pos(30,0, LEFT,CENTER,rect0)
        
        
        objects.push(rect0);
        wrapper.add(objects)
        win.add(wrapper).addTo(page); 
        //win.add(totorial_label)
        
    }
    page.deploy_tutorial()
    
    
    //new Label({color:purple, text:"GO", size:30,variant:true})
//    font_size=35
//    test_label=new Label({color:yellow, text:"Play", size:font_size, align:CENTER})//.pos(0,-100,CENTER,CENTER,page1);
//    page.go2menu = new Button({width:140,height:140,backgroundColor:purple,rollBackgroundColor:orange,label:test_label,corner:70})
//    .pos(0,30,CENTER,BOTTOM,main_cont)    
    var play = page.play = new Button({
        backgroundColor:purple,
        rollBackgroundColor:orange,
        width:100,
        height:100,
        corner:50,
        icon:pizzazz.makeIcon("play", white, 1.5)
    })
    .pos(0,90,CENTER,BOTTOM,page) 
    

    alphabet_label=new Label({color:yellow, text:"View All Alphabet Letters", size:25, align:CENTER})
    page.go2alphabet = new Button({width:stageW*0.8,height:60,backgroundColor:blue.darken(0.5),rollBackgroundColor:orange,label:alphabet_label,corner:20})
    .pos(0,20,CENTER,BOTTOM,page)   
    
    
    
    next_label=new Label({color:yellow, text:"Next >", size:25, align:CENTER})
    page.next = new Button({width:140,height:60,backgroundColor:purple,rollBackgroundColor:orange,label:next_label,corner:20})
    .pos(60,100,RIGHT,BOTTOM,page) 
    .tap(function(){
        
        if (page.i+1<tutorial_titles.length){
            page.i+=1
            remove_el(page.main_cont)
            page.deploy_tutorial()            
        }
    })
    
    
    prev_label=new Label({color:yellow, text:"< Previous", size:25, align:CENTER})
    page.prev = new Button({width:140,height:60,backgroundColor:purple,rollBackgroundColor:orange,label:prev_label,corner:20})
    .pos(60,100,LEFT,BOTTOM,page)    
    .tap(function(){
        
        if (page.i-1>=0){
            page.i-=1
            remove_el(page.main_cont)
            page.deploy_tutorial()            
        }
    })
    
//    new Label({
//        color:purple,
//        text:"ALPHA5",
//        size:45,
//        variant:true
//    })
//        .pos(0,30,CENTER,TOP,page)
//        .alp(0)
//        .animate({
//            props:{alpha:.9},
//            wait:0.5
//        });
//
//    new Label({
//        color:purple,
//        text:"Learn Arabic Alphabet",
//        size:30,
//        variant:true
//    })
//        .pos(0,100,CENTER,TOP,page)
//        .alp(0)
//        .animate({
//            props:{alpha:.9},
//            wait:1
//        });
//
//    new Label({
//        color:purple,
//        text:"5 minutes a day!",
//        size:30,
//        variant:true
//    })
//        .pos(0,150,CENTER,TOP,page)
//        .alp(0)
//        .animate({
//            props:{alpha:.9},
//            wait:1.5
//        });
//
//var help = new Label({
//        backing:new Circle(30, green.darken(.6)),
//        align:CENTER,
//        valign:CENTER,
//        size:60,
//        color:green,
//        shiftVertical:1,
//        shiftHorizontal:1,
//        text:"?"
//    }).pos(60,100,LEFT,BOTTOM,page)
//        .expand() // make it easier to press on mobile especially for kids
//        .cur() // show a cursor if not on mobile
//        .sca(1) // start with the help not seen - we will animate it in
//        //.tap(page.readQuestion); // call
    
//        page.replay = new Button({
//        width:60,
//        height:60,
//        backgroundColor:green,
//        rollBackgroundColor:blue,
//        //icon:pizzazz.makeIcon("rotate", white, .9),
//        label:"What is it?",
//        corner:30
//    }).tap(function () {
//        // scrambler.enabled = true; // chose not to use as the page swipes
//        page.go.animate({alpha:0}, .3);
//        page.replay.animate({alpha:0}, .3);
//        //scrambler.scramble(1.5,.3, 3);
//    })
    
    
//    label2=new Label({
//        color:purple,
//        text:"What?",
//        size:45,
//        variant:true
//    })
//        .alp(.7)
//        .pos(0,100,CENTER,TOP,page);    
    // this button and the toggle need to be used by the main script
    // so store them on the intro page which is being returned to the main script
//    page.go = new Button({
//        width:140,
//        height:140,
//        backgroundColor:purple,
//        rollBackgroundColor:orange,
//        label:"GO",
//        corner:70
//    })
//        .centerReg(page)
//        .pos(50,50,RIGHT,BOTTOM)
//        .sca(0)
//        .animate({
//            wait:1.5,
//            props:{scale:1},
//            ease:"backOut",
//            time:.5
//        });
//
//    page.music = new Toggle({label:"music", color:green.darken(.5), startToggled:true})
//        .sca(.8)
//        .pos(40,40,LEFT,BOTTOM,page)
//        .alp(0)
//        .animate({
//            props:{alpha:.8},
//            wait:3
//        });

    return page;
}

