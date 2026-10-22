# 由 tools/gen_game.py 自动生成，请勿手改。

label ch16:
    call screen chapter_card("第十六章", "三月十二")
    $ track("chapter_enter", chapter="ch16")
    $ qian -= 800
    $ debt -= 10000
    scene bg_night_street
    with fade
    play music "audio/bgm/city_night.ogg" fadein 1.5
    "三月十号，祥子给小福发微信。"
    "{b}「小福，最近怎么样？」{/b}"
    "没有回。"
    "十一号，他又发了一条。"
    "{b}「你在哪儿？我去看你。」{/b}"
    "还是没有回。"
    "十二号早上，他打了一个电话。关机。"
    "他心里开始发慌。"
    scene bg_alley
    with fade
    play music "audio/bgm/alley_dusk.ogg" fadein 1.5
    "小福去年冬天从 KTV 出来了。"
    "罗二强在乔司给她租了一间房，一个月六百，让她在附近的超市上班。她给他发过一次定位，说“祥子哥，我搬这儿了，你有空来坐”。"
    "他当时在跑单，回了一句“好，改天”。"
    "改天。"
    scene bg_alley
    with fade
    play music "audio/bgm/silence_tense.ogg" fadein 1.5
    "乔司，朝阳村，十七号。"
    "房东是个五十多岁的女人，正在院子里晒被子。"
    land "「找谁？」"
    show xz tired at sprite_left
    with dissolve
    xz "「罗小福。住二楼的。」"
    land "「你是她什么人？」"
    xz "「老乡。她哥。」"
    land "「……」"
    "房东看了他一眼，把被子放下。"
    land "「她两天没出来了。」"
    xz "「什么？」"
    land "「我昨天敲门，没人应。我以为她上班去了。」"
    xz "「开门。」"
    land "「我没有钥匙，她从里面反锁了。」"
    xz "「砸开。」"
    scene bg_room
    with fade
    play music "audio/bgm/silence_tense.ogg" fadein 1.5
    "门是撞开的。"
    "屋里很暗，窗帘拉着。一股味道冲出来，甜的，呛的，像烧过的煤。"
    "小福躺在床上，盖着被子，脸朝着墙。"
    "床边有一个铁盆，里面是烧完的炭，灰白的。"
    "窗户的缝隙用胶带封着。"
    show xz tired at sprite_left
    with dissolve
    xz "「小福！」"
    "祥子扑过去，把她的肩翻过来。"
    "她的脸是青的，嘴唇是紫的，眼睛闭着。"
    "身体已经硬了。"
    scene bg_room
    with fade
    play music "audio/bgm/silence.ogg" fadein 1.5
    "警察来了，拉了警戒线。"
    "法医进去，出来，问了祥子几个问题，做了记录。"
    police "「你最后一次联系她是什么时候？」"
    show xz tired at sprite_left
    with dissolve
    xz "「去年……去年五月。」"
    police "「之后没见过？」"
    xz "「没有。」"
    police "「她家里人呢？」"
    xz "「她爸在杭州。」"
    police "「联系上了吗？」"
    xz "「……联系上了。他说他不来。」"
    "警察抬头看了他一眼，没说话。"
    scene bg_room
    with fade
    play music "audio/bgm/silence.ogg" fadein 1.5
    "桌上有一张纸。"
    "不是遗书。是一张超市的收银小票，背面用圆珠笔写着几行字："
    "{b}妈的手术费 30000{/b}"
    "{b}弟弟学费 8000{/b}"
    "{b}欠二叔 5000{/b}"
    "下面画了一道线，写着：{b}43000{/b}。"
    "再下面，是一行很小的字："
    "{b}对不起。{/b}"
    "祥子把那张纸捏在手里，捏得皱成一团。"
    scene bg_room
    with fade
    play music "audio/bgm/silence.ogg" fadein 1.5
    "她的手机在枕头旁边。"
    "警察解锁后给他看。微信里，最后一个对话是他。"
    "{b}「祥子哥，你有空吗？」{/b}——2021 年 5 月 16 日。"
    "下面是他三天后回的一句：{b}「在跑单，晚点说。」{/b}"
    "再下面，就没有了。"
    "她发过很多条，都是发给别人的。发给“妈”，发给“二叔”，发给一个叫“小雨”的同事。没有一条发给他。"
    "他翻到最后，看见她在 3 月 11 日晚上十一点，发了一条朋友圈，只有一张照片。"
    "照片是窗外的天，灰的，有一根电线。"
    "没有文字。"
    scene bg_room
    with fade
    play music "audio/bgm/silence.ogg" fadein 1.5
    "他把她的手机翻了一遍。"
    "相册里有三百多张照片。大部分是自拍，滤镜开得很重，脸白得发亮。有几张是吃的：麻辣烫、煎饼、一杯奶茶。"
    "有一张是 2021 年 5 月拍的，拍的是他的背影。"
    "那天他在 KTV 门口等她，穿着外卖服，站在马路对面。她隔着玻璃拍的，照片有点糊。"
    "还有一段视频，11 秒。是她自己在宿舍里唱歌，唱的是《后来》。"
    "她唱得不好，跑调，唱到一半自己笑了，说“算了算了”。"
    "祥子把这段视频看了七遍。"
    "第七遍的时候，他听见背景里有别人的声音，一个女的说“小福你别唱了，难听死了”。"
    "她笑着说“我就要唱”。"
    show xz tired at sprite_left
    with dissolve
    xz "「你唱吧。」"
    "他对着手机说。"
    "「你唱。」"
    "手机屏幕暗了。"
    xz "「小福。」"
    "他蹲在地上，把脸埋进膝盖。"
    "「你有空吗。」"
    "他重复了一遍。"
    "「我有空。」"
    "「我现在有空。」"
    scene bg_funeral
    with fade
    play music "audio/bgm/funeral_low.ogg" fadein 1.5
    "三月二十号，火化。"
    "殡仪馆在留下，一片山坡上，种着松树。"
    "来的人很少。祥子，罗二强，小福的两个弟弟从老家赶来，还有超市的一个同事。"
    "罗二强穿了一件不合身的黑西装，站在角落里抽烟。他的脸肿着，眼睛红着，不知道是哭的还是喝酒喝的。"
    "火化前，他走过来。"
    rq "「丧葬费，你出。」"
    show xz tired at sprite_left
    with dissolve
    xz "「多少？」"
    rq "「六千。」"
    xz "「我出三千。」"
    rq "「你他妈……」"
    xz "「我出三千。」祥子看着他，「剩下的你出。你是她爸。」"
    rq "「我没钱。」"
    xz "「你卖她的钱呢？」"
    rq "「……」"
    "罗二强没说话，转身走了。"
    "三千块，祥子出的。他当时卡里有四千二。"
    scene bg_funeral
    with fade
    play music "audio/bgm/funeral_low.ogg" fadein 1.5
    "罗二强在殡仪馆门口拦住他。"
    "他喝了酒，眼睛通红，身上一股酸味。"
    rq "「三千不够。」"
    show xz tired at sprite_left
    with dissolve
    xz "「什么不够？」"
    rq "「火化费、骨灰盒、灵堂，加起来六千。你出三千，我出三千。我哪来的三千？」"
    xz "「你卖她的两万呢？」"
    rq "「花了。」"
    xz "「花哪儿了？」"
    rq "「关你屁事。」"
    "祥子看着他。这个男人的脸肿着，嘴角有一道新的口子，不知道跟谁打的。"
    "他忽然觉得很累。"
    xz "「我再给你一千。」"
    rq "「一千不够。」"
    xz "「我就一千。」"
    rq "「你他妈……」"
    xz "「罗二强。」祥子打断他，「你女儿死了。」"
    rq "「我知道！」"
    xz "「你知道她最后一条微信发给我什么吗？」"
    rq "「……」"
    xz "「'你有空吗'。」"
    xz "「她没找你。她找我。」"
    xz "「我他妈也没回。」"
    "罗二强站在那儿，嘴唇动了动，没说话。"
    "过了一会儿，他转身走了。走了几步，蹲在路边，抱着头。"
    "祥子没有过去。"
    scene bg_room
    with fade
    play music "audio/bgm/room_empty.ogg" fadein 1.5
    "小福的遗物，房东收拾出来，装了两个纸箱。"
    "一箱是衣服。粉色的卫衣，黑色的工作服，几件打折买的T恤。都洗得很干净，叠得很整齐。"
    "一箱是杂物。一个吹风机，一盒没吃完的感冒药，一本记账本，一个铁盒子。"
    "铁盒子里有钱。"
    "一沓一沓，用皮筋捆着，最大的五十，最小的一块。数下来，四千三百。"
    "还有一张纸条：{b}妈的手术费{/b}。"
    "祥子把铁盒子盖上，抱在怀里，坐了很久。"
    "他想起她说“我攒，我妈说不治了”。"
    "她攒了四千三。三万的手术费，她攒了四千三。"
    show xz tired at sprite_left
    with dissolve
    xz "「小福。」"
    "他对着纸箱说。"
    "「你攒得真慢。」"
    scene bg_station_arrival
    with fade
    play music "audio/bgm/train.ogg" fadein 1.5
    "三月二十六号，他请了三天假，带着骨灰盒去郸城。"
    "罗二强不肯去。他说他去了没法见人。"
    "祥子没说什么。他去殡仪馆领了骨灰，装在一个红布包里，放在背包最里面，背着上了火车。"
    "十三个小时。他一路没睡。"
    "到县城是第二天早上，又坐了一个小时的中巴到罗楼。"
    "村子很小，三十几户人家。村口有一棵大槐树，树下坐着几个老人。"
    "他问罗小福家怎么走。一个老人抬头看他，看了很久。"
    old "「你是她啥人？」"
    show xz tired at sprite_left
    with dissolve
    xz "「老乡。」"
    old "「她家在最里头，红砖房，门口有一堆柴。」"
    scene bg_home
    with fade
    play music "audio/bgm/rural_winter.ogg" fadein 1.5
    "罗家的院子很小，三间砖房，一间厨房。院子里堆着玉米秸，一只鸡在啄食。"
    "她妈坐在门槛上，看见他，愣了一下。"
    "祥子把红布包拿出来，放在她手里。"
    show xz tired at sprite_left
    with dissolve
    xz "「婶，小福……走了。」"
    xz "「我把她送回来。」"
    "她妈没有哭。"
    "她抱着那个布包，坐在门槛上，一动不动。"
    "过了一会儿，她说："
    mom "「她小时候，最爱在这棵树下玩。」"
    mom "「她爸打她，她就躲到树上。」"
    mom "「我喊她下来吃饭，她不下来。」"
    mom "「她说，妈，我在上面看得很远。」"
    "祥子站在院子里，看着那棵光秃秃的树。"
    mom "「她在杭州，过得好不好？」"
    xz "「……好。」"
    mom "「她寄钱回来，说在超市上班。」"
    mom "「我知道她骗我。」"
    mom "「她一个初中毕业的丫头，在杭州能挣四千，怎么可能。」"
    mom "「我不问。我怕她说了，我受不了。」"
    "她低下头，把脸埋在红布包上。"
    "祥子蹲下来，蹲在她旁边。"
    "他不知道该说什么。"
    "他想说“对不起”，但这句话太轻了。"
    "他想说“我该早点去接她”，但这句话太重了，他说不出口。"
    "最后他说："
    xz "「婶，我给她买块碑。」"
    mom "「不用。」"
    mom "「她自己攒的钱，留着给她弟上学。」"
    mom "「她要是知道钱花在碑上，会不高兴。」"
    "祥子从包里掏出那个铁盒子，放在她手边。"
    xz "「这是她攒的。四千三。」"
    mom "「……」"
    xz "「她说给妈做手术。」"
    "她妈抱着铁盒子，终于哭了。"
    "哭声很小，像漏气。"
    scene bg_home
    with fade
    play music "audio/bgm/rural_winter.ogg" fadein 1.5
    "祥子在罗楼住了一晚。"
    "她家给他腾了一间屋，床上铺着新洗的床单，有一股太阳的味道。"
    "夜里他睡不着，起来上厕所，看见堂屋里还亮着灯。"
    "她妈坐在桌边，面前摊着一沓钱，一张一张地数。"
    "数完，用皮筋捆好，放进铁盒子，盖上盖，抱在怀里。"
    "祥子站在门口，没有进去。"
    "他退回屋里，躺下，睁着眼睛到天亮。"
    scene bg_funeral
    with fade
    play music "audio/bgm/funeral_low.ogg" fadein 1.5
    scene cg_funeral
    with fade
    "火化的时候，他站在炉子外面。"
    "这是他一年里第二次站在这里。"
    "铁门关上，火“轰”的一声。"
    "他想起小福第一次来杭州，提着一个编织袋，站在五堡巷口，问他“祥子哥，这儿有卖馒头的吗”。"
    "他想起她给他那对杯子，说“百年”。"
    "他想起她在 KTV 门口，说“我等你”。"
    "他想起自己说“下个月”。"
    show xz tired at sprite_left
    with dissolve
    xz "「对不起。」"
    "他对着铁门说。"
    scene bg_funeral
    with fade
    play music "audio/bgm/funeral_low.ogg" fadein 1.5
    "出来的时候，他看见殡仪馆门口贴着一张招工纸。"
    "{b}招临时工。守夜、抬棺、代客排队。日结，一百八。联系电话：……{/b}"
    "他站在那里，看了很久。"
    "一个穿蓝大褂的老头走过来，问他：“找活儿？”"
    show xz tired at sprite_left
    with dissolve
    xz "「……看看。」"
    old "「想干就打电话。这活儿不累，就是要熬夜，胆子要大。」"
    xz "「熬夜我行。」"
    old "「那你来。」"
    "祥子把那个电话号码存进手机。"
    "存的名字是：{b}殡仪馆{/b}。"
    scene bg_night_street
    with fade
    play music "audio/bgm/city_night.ogg" fadein 1.5
    "回乔司的路上，他接到姐姐的电话。"
    bj "「祥子，念念发烧了，三十九度。」"
    show xz tired at sprite_left
    with dissolve
    xz "「去医院了吗？」"
    bj "「去了。医生说要住院，押金两千。」"
    xz "「我转你。」"
    bj "「你还有钱吗？」"
    xz "「有。」"
    "他挂了电话，打开手机银行。余额：一千二百。"
    "他给王大勇发微信：{b}「哥，借两千，急用。」{/b}"
    "十分钟后，钱到了。"
    "他转给姐姐两千。"
    "转完，余额：负八百。"
    "他坐在路边的台阶上，点了一根烟。"
    xz "「四千三。」"
    "他对自己说。"
    "「小福欠四万三。」"
    "他抽了一口烟，看着烟雾散在黑里。"
    "「我也欠着。」"
    scene bg_room
    with fade
    play music "audio/bgm/room_night.ogg" fadein 1.5
    "那天夜里，他做了个梦。"
    "梦见小福站在五堡的巷口，穿着那件粉色的卫衣，手里拎着塑料袋。"
    show xf sad at sprite_left
    with dissolve
    xf "「祥子哥，你有空吗？」"
    show xz tired at sprite_right
    with dissolve
    xz "「有。」"
    xf "「那你来接我。」"
    xz "「好。我现在就来。」"
    "他跑过去，巷子很长，怎么跑都跑不到。"
    "她站在那儿，笑着，越退越远。"
    "祥子醒了。"
    "天还没亮。乔司的窗外有一只鸟在叫，一声一声。"
    "他躺在床上，看着天花板。"
    "天花板上有一块水渍，形状像一只趴着的狗。"

    $ track("chapter_complete", chapter="ch16")
    jump ch17
    return
