# 由 tools/gen_game.py 自动生成，请勿手改。

label ch15:
    call screen chapter_card("第十五章", "服务分")
    $ qian -= 1000
    $ debt -= 30000
    scene bg_station
    with fade
    play music "audio/bgm/station_room.ogg" fadein 1.5
    "四月九号，杭州区划调整。"
    "江干区没了，并入上城区。祥子的居住登记在乔司，属于临平区，跟这事没关系。但他的罚单、社保、劳务协议上，写的都是“江干区新塘路”。"
    "王站长在白板上贴了一张纸：{b}地址变更通知。原江干区各站点，归属上城区。系统信息更新中，暂时不要修改个人资料。{/b}"
    "“暂时”持续了三个月。"
    "那三个月，他的罚单寄不到，他的申诉也提交不上去。系统提示“地址不匹配”。"
    wz "「先别管。等系统更新。」"
    show xz tired at sprite_left
    with dissolve
    xz "「罚单呢？」"
    wz "「罚单照扣。」"
    scene bg_station
    with fade
    play music "audio/bgm/station_room.ogg" fadein 1.5
    "七月二十六号，七部门发了文件。"
    "王站长在早会上念了几条：算法取中，放宽配送时限，不得以最严算法考核，职业伤害保障试点。"
    qun "「这是不是以后不罚了？」"
    wz "「不罚？」王站长笑了一下，「你们看后面。公司要'优化考核体系'。从下个月起，超时不扣钱，扣服务分。」"
    qun "「服务分是什么？」"
    wz "「准时率、好评率、着装、餐箱清洁、顾客评价，都算分。满分一百，低于八十五，派单降级。」"
    show xz tired at sprite_left
    with dissolve
    xz "「降级是什么意思？」"
    wz "「意思是，好单不给你，远的、偏的、没电梯的，都给你。」"
    scene bg_station
    with fade
    play music "audio/bgm/station_busy.ogg" fadein 1.5
    "八月，祥子成了“老骑手”。"
    "站点招了一批新人，最大的四十五，最小的十九。王站长让他带三个。"
    wz "「你跑得稳，你带。带好了，一个月多三百。」"
    show xz tired at sprite_left
    with dissolve
    xz "「带不好呢？」"
    wz "「带不好扣你分。」"
    "三个新人，一个叫小李，十九岁，安徽人，第一次来杭州；一个叫老赵，四十五，原来在厂里，厂子搬走了；一个叫阿强，二十三，跑过众包。"
    "第一天，祥子带他们跑新塘路。"
    li "「哥，一天能跑多少？」"
    xz "「看你会不会算。」"
    li "「怎么算？」"
    xz "「看单先看楼。几楼，有没有电梯，小区让不让进，单元门有没有密码。四个看完了，再接。」"
    li "「系统派的，能挑？」"
    xz "「不能挑，能算。算不过来，接了就得认。」"
    "小李点头，掏出手机记。"
    "祥子看着他记，忽然想起三年前的自己。那时候老马跟他说一样的话，他也记。"
    xz "「还有一条。」"
    li "「什么？」"
    xz "「别买车。」"
    li "「啊？不买车怎么跑？」"
    xz "「租。租车坏了有人修，丢了不心疼。」"
    li "「可是租车一个月四百五，一年五千四。」"
    xz "「你算得对。」祥子说，「但是你没算丢车。我丢过一辆，六千九，四十五天。」"
    li "「……」"
    xz "「你自己想。」"
    scene bg_road
    with fade
    play music "audio/bgm/city_day.ogg" fadein 1.5
    "带了一个月，三个人跑了两个。"
    "小李回安徽了，说这行太累。阿强去了饿了么，说那边单价高五毛。"
    "小李走的那天，请他吃了一顿饭。"
    "路边小炒，两个菜，一瓶啤酒。小李二十一岁，脸上还有青春痘，说话的时候不敢看他。"
    li "「哥，我不是怕累。」"
    show xz tired at sprite_left
    with dissolve
    xz "「那怕什么？」"
    li "「我怕我干三年，还是这样。」"
    li "「我表哥在厂里，干了五年，现在是线长，一个月八千，有宿舍，有社保。他说我再不去，以后就没位置了。」"
    xz "「那你去。」"
    li "「哥，你不劝我？」"
    xz "「劝什么。你算得对。」"
    "小李低下头，喝了一口啤酒。"
    li "「哥，你说这行有没有前途？」"
    xz "「没有。」"
    li "「那你为什么还干？」"
    xz "「我欠钱。」"
    li "「……」"
    xz "「你还年轻。别学我。」"
    "第二天，小李走了。他把工服洗干净，叠好，放在站点的桌子上。"
    "祥子把工服收起来，塞进柜子里。"
    scene bg_station
    with fade
    play music "audio/bgm/station_busy.ogg" fadein 1.5
    "八月，服务分正式开始扣。"
    "第一周，祥子被扣了八分。"
    "三分是因为超时，两分是因为餐箱没擦干净，三分是因为一个顾客给了四星，评语是“汤有点凉”。"
    "他去找王站长。"
    show xz tired at sprite_left
    with dissolve
    xz "「四星也扣分？」"
    wz "「四星等于不满意。」"
    xz "「四星怎么会等于不满意？」"
    wz "「系统就这么定的。」"
    xz "「那我怎么办？」"
    wz "「让顾客给五星。」"
    "祥子站在那儿，忽然笑了。"
    wz "「你笑什么？」"
    xz "「我笑我以前以为，只要跑得快就行。」"
    scene bg_road
    with fade
    play music "audio/bgm/city_day.ogg" fadein 1.5
    "只剩下老赵。老赵四十五，跑得慢，但从不超时，从不差评。他有一个儿子在读大学，一年学费两万。"
    zhao "「祥子，我这年纪，还能跑几年？」"
    show xz tired at sprite_left
    with dissolve
    xz "「跑到跑不动。」"
    zhao "「跑不动了怎么办？」"
    xz "「不知道。」"
    "老赵笑了一下，笑得有点苦。"
    zhao "「我以前在厂里，干了十八年。厂子说搬就搬，赔了三个月工资。」"
    zhao "「我以为送外卖自由。自由是自由，就是没有底。」"
    "老赵有一套自己的办法。"
    "每次送餐，他都会在门口站三秒，把餐盒摆正，把袋子口捋平，然后敲门。开门的时候，他往后退半步，笑一下。"
    zhao "「您好，您的外卖。」"
    zhao "「祝您用餐愉快。」"
    "祥子问他为什么。"
    zhao "「三秒钟，换个五星。」"
    zhao "「我以前在厂里，做质检。质检这活儿，就是让别人挑不出错。」"
    zhao "「现在我给自己做质检。」"
    "祥子学他。学了半个月，服务分从八十二回到九十一。"
    "他发现，原来“跑得快”不是最重要的。“让人挑不出错”才是。"
    "这个道理，他在厂里学不到，在马路上学会了。"
    scene bg_rain
    with fade
    play music "audio/bgm/rain_light.ogg" fadein 1.5
    "十一月二十二号，老马摔了。"
    "这次摔得重。雨天，路滑，他被一辆右转的货车带倒，锁骨骨折，肋骨裂了两根。"
    "祥子去医院看他。"
    "老马躺在病床上，半边身子不能动，脸上青一块紫一块。"
    show lm normal at sprite_left
    with dissolve
    lm "「祥子来了。」"
    show xz tired at sprite_right
    with dissolve
    xz "「马叔。」"
    lm "「没事。死不了。」"
    "他从枕头底下摸出一个信封。"
    lm "「三千。站点给的。」"
    xz "「三千？你锁骨断了。」"
    lm "「人道补助。他们说我这是众包，不算工伤。」"
    xz "「你不是在专送干过？」"
    lm "「干了两年，后来转众包了。众包自由。」"
    lm "「自由。」他重复了一遍，笑了，「自由就是摔了没人管。」"
    "祥子坐在床边，给他削苹果。刀不快，削得很厚。"
    lm "「祥子，我准备回去了。」"
    xz "「回信阳？」"
    lm "「嗯。跑不动了。」"
    xz "「小雨的手术……」"
    lm "「还差五万。」老马看着天花板，「我回去，把房子卖了。」"
    xz "「卖了住哪儿？」"
    lm "「住我儿子那儿。」"
    scene bg_hospital
    with fade
    play music "audio/bgm/hospital_low.ogg" fadein 1.5
    "临走的时候，老马叫住他。"
    show lm normal at sprite_left
    with dissolve
    lm "「祥子。」"
    show xz tired at sprite_right
    with dissolve
    xz "「嗯？」"
    lm "「你还记得我跟你说的话吗？」"
    xz "「哪句？」"
    lm "「车不是你的。」"
    xz "「记得。」"
    lm "「现在我再加一句。」"
    lm "「命也不是你的。」"
    "祥子站在门口。"
    "老马把头转过去，看着窗外。"
    lm "「命是钱的。钱是别人的。」"
    scene bg_station_arrival
    with fade
    play music "audio/bgm/train.ogg" fadein 1.5
    "老马走的那天，他去送。"
    "信阳的火车，下午三点。老马只有一个编织袋，比祥子当年来的时候还小。"
    "他的锁骨还没长好，右胳膊用一条布带吊着。走路一瘸一拐。"
    show lm normal at sprite_left
    with dissolve
    lm "「别送了。」"
    show xz tired at sprite_right
    with dissolve
    xz "「送到站台。」"
    lm "「你这人。」"
    "两个人在候车厅坐下。老马从口袋里摸出一包烟，抽了一根，点上。"
    lm "「祥子，我跑了七年，你是第二个送我的。」"
    xz "「第一个是谁？」"
    lm "「一个安徽的小伙子。跑了两年，回老家结婚了。」"
    lm "「他走的时候跟我说，马叔，我以后再也不跑单了。」"
    xz "「他做到了吗？」"
    lm "「不知道。没联系了。」"
    "广播开始检票。"
    "老马站起来，把烟头摁灭在椅子扶手上。"
    lm "「祥子。」"
    xz "「嗯。」"
    lm "「别学我。」"
    xz "「学你什么？」"
    lm "「跑一辈子。」"
    "他拎起编织袋，走进检票口。"
    "祥子站在原地看着。老马走了十几米，回头挥了挥手，那只手是好的那只。"
    "然后他就被人群吞了。"
    scene bg_night_street
    with fade
    play music "audio/bgm/city_night.ogg" fadein 1.5
    "那天晚上，祥子在便利店买了一包烟。"
    "他戒烟三年了。"
    "他坐在乔司的出租屋里，点了一根，抽了一口，呛得咳嗽。"
    "咳完，他又抽了一口。"
    "烟在黑暗里一明一暗。他看着那一点红，看了很久。"
    scene bg_room
    with fade
    play music "audio/bgm/room_night.ogg" fadein 1.5
    "他翻出记账本。"
    "2021 年的账，他只记到一月份。后面全是空白。"
    "他拿起笔，想补，写了两个字：“二月”，又停了。"
    "他把笔放下，把本子扔到床底下。"
    "从那天起，他不再记账。"

    jump ch16
    return
