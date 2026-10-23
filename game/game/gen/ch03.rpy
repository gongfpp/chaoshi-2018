# 由 tools/gen_game.py 自动生成，请勿手改。

label ch03:
    call screen chapter_card("第三章", "调度室")
    $ track("chapter_enter", chapter="ch03")
    $ amb_layer_pause(0.0)
    $ qian = 14052
    $ debt = 0
    scene bg_station
    with fade
    $ implicit_amb("bg_station")
    play music "audio/bgm/station_room.ogg" fadein 1.5
    "调度室在站点最里面，用玻璃隔出来的一个小间，门上贴着一张 A4 纸：{b}非工作人员禁止入内{/b}。"
    "里面有两台电脑、一台打印机、一面墙的监控屏。屏幕上是新塘站的配送地图，密密麻麻的黄点在动，每个点是一个骑手。"
    "祥子第一次进去，是因为超时。"
    "那天下午一场暴雨，他在庆春广场附近堵了四十分钟。三单超时，罚六十。他站在白板前面看自己的名字，看了很久。"
    "玻璃门开了。"
    "「杨保祥？」"
    "一个女人，三十来岁，烫着小卷，穿一件黑色的站点马甲，手里端着一个印着“奖”字的搪瓷杯。她比他想象的胖，但走路很快。"
    "「进来。」"
    scene bg_office
    with fade
    $ implicit_amb("bg_office")
    play music "audio/bgm/office_hum.ogg" fadein 1.5
    "监控屏的光照在她脸上。她坐下来，鼠标点了几下。"
    show ll normal at sprite_left
    with dissolve
    ll "「这三单，都是暴雨。商家出餐时间有记录，你申诉了吗？」"
    show xz normal at sprite_right
    with dissolve
    xz "「没。」"
    ll "「为什么不申诉？」"
    xz "「不会。」"
    "她“啧”了一声，不是嫌弃，是那种“你怎么这么老实”的啧。她把三单的商家出餐时间调出来，截图，填表，点提交。"
    ll "「改好了。下次记住，超时不是你的错，你得让系统知道不是你的错。」"
    xz "「……谢谢。」"
    ll "「谢什么。我叫刘蕾，这里的调度。以后有事找我，别找站长，他只会扣钱。」"
    "她说这话的时候，王站长正好从门外走过。她也没避讳。"
    "祥子站在那里，不知道该怎么接。屋里开着空调，他一身雨水，冷得发抖。她看了他一眼。"
    ll "「你站着干嘛？坐。」"
    xz "「我身上湿。」"
    ll "「湿就湿。这屋里没地毯。」"
    "他坐下，只坐了一半。她把搪瓷杯推过来，里面是热水。"
    ll "「喝了。跑单的人，最怕的不是累，是感冒。一感冒，三天白干。」"
    "祥子捧着杯子，热气扑到脸上。他听见外面有人在喊“二十三号好了没有”，听见充电器的风扇在响，听见她在键盘上敲字。"
    "那一刻他忽然觉得很困。"
    ll "「你多大了？」"
    xz "「二十二。」"
    ll "「河南哪儿的？」"
    xz "「周口。」"
    ll "「周口出骗子。」她说完自己笑了，「开玩笑。我们这儿河南的多，信阳的、驻马店的、周口的，一半。」"
    xz "「嗯。」"
    ll "「一个月跑多少？」"
    xz "「一千一。」"
    ll "「一千一？」她抬起头，「你几月来的？」"
    xz "「三月。」"
    ll "「三月来，七月跑一千一。你知道站里跑一千一的有几个？」"
    xz "「不知道。」"
    ll "「三个。一个跑了五年，一个跑了三年，一个是你。」"
    "她把杯子拿回去，喝了一口。"
    ll "「你能跑。但你别觉得自己能跑就了不起。这行不看你能跑多久，看你能跑几年。」"
    scene bg_station
    with fade
    $ implicit_amb("bg_station")
    play music "audio/bgm/station_room.ogg" fadein 1.5
    scene bg_office
    with fade
    $ implicit_amb("bg_office")
    play music "audio/bgm/office_hum.ogg" fadein 1.5
    "抄白板的日子，他们说话不多。"
    "早上七点半，他把前一天的数抄到本子上：总单量、准时率、投诉、新增、离职。她坐在电脑前核对，一边核对一边骂人。"
    "有一天她骂完了，忽然问他："
    show ll normal at sprite_left
    with dissolve
    ll "「祥子，你结过婚没有？」"
    show xz normal at sprite_right
    with dissolve
    xz "「没有。」"
    ll "「我结过。」"
    ll "「二〇一五年离的。他做布料生意，欠了一屁股债，人跑了，债主堵到我家门口。我替他还了七万。」"
    "她说话的时候没抬头，眼睛还盯着屏幕。"
    ll "「七万，我做了三年档口才还清。那时候我每天早上四点起床，晚上十点收摊，中午吃一个包子。」"
    xz "「……他没回来？」"
    ll "「回来过一次。问我要钱。」"
    ll "「我拿扫把把他打出去了。」"
    "她笑了一下，笑得很短。"
    ll "「所以你别看我凶。我不凶，早就被人吃干净了。」"
    "祥子站在旁边，手里拿着笔。他忽然明白，她为什么总在算账，为什么把每一笔钱都记得那么清楚。"
    "一个被钱伤过的人，才会把钱看得比什么都重。"
    ll "「你呢？你攒钱干什么？」"
    xz "「买车。」"
    ll "「买了车呢？」"
    xz "「自己干。」"
    ll "「自己干？」她抬起头，「你以为有车就是自己干？你有车，单还是平台派的。你不接，照样没钱。」"
    xz "「那也比租车强。」"
    ll "「强一点。」她低下头，继续敲键盘，「强一点也是强。」"
    $ track("choice_shown", choice="ch03")
    menu:
        "接下这些“刚好”的单子":
            $ track("choice_pick", choice="ch03", option=0)
            $ c_haodan = True
            $ xin += 1
            $ qian += 300
        "把钥匙还回去":
            $ track("choice_pick", choice="ch03", option=1)
            $ c_haodan = False
            $ xin -= 1
            jump ch03_alt
    "从那天起，祥子的单子变顺了。"
    "不是明显的好单，是那种“刚好”的单：商家出餐快，小区让进，楼层不高，几单顺路。他的准时率从九十四回到九十八，罚单少了，工资多了三百。"
    "同组的人开始说话。"
    qun "「祥子，你最近挺顺啊。」"
    xz "「运气好。」"
    qun "「运气好的人，都在调度室喝水。」"
    "祥子没接话。他知道他们什么意思，他也知道自己没做什么。他只是接了那些“刚好”的单，而“刚好”是别人安排的。"
    scene bg_office
    with fade
    $ implicit_amb("bg_office")
    play music "audio/bgm/office_hum.ogg" fadein 1.5
    "抄白板抄了一个月，祥子才知道调度能做什么。"
    "她能在系统里改派单。一单从 A 骑手转到 B 骑手，只要点几下，理由填“骑手异常”。"
    "她能在后台标注“商家出餐延迟”。标了，超时就不算骑手的。"
    "她能决定谁上早班，谁上晚班。早班单少，晚班单贵。"
    "她还能决定谁去跑“远区”。远区是九堡、乔司、临平，一趟十几公里，回来空车。"
    show xz normal at sprite_left
    with dissolve
    xz "「蕾姐，系统不是自动派的吗？」"
    show ll normal at sprite_right
    with dissolve
    ll "「自动派，人工调。」"
    ll "「系统是死的，人是活的。」"
    xz "「那……谁调？」"
    ll "「我。」"
    "她说这话的时候，眼睛没离开屏幕。"
    ll "「你别觉得我坏。我要是不调，好单全被那几个老油条抢走，新人跑两天就跑了。」"
    ll "「我要让每个人都能活下去。」"
    xz "「那我呢？」"
    ll "「你？」她抬起头，笑了一下，「你能跑。你不需要我照顾。」"
    xz "「那你还给我好单？」"
    ll "「因为你值得。」"
    "祥子没接话。"
    "他站在那里，看着屏幕上那些移动的黄点。"
    "每一个点都是一个人。每一单都要有人跑。她能决定谁跑哪一单。"
    "这就是权力。"

label ch03_join:
    scene bg_alley
    with fade
    $ implicit_amb("bg_alley")
    play music "audio/bgm/wedding_soft.ogg" fadein 1.5
    "七月十六，老刘生日。"
    "阿二饭店在彭埠老街，门口挂着红灯笼，包厢里两桌。老刘坐主位，刘蕾坐他旁边，王站长坐对面，还有几个车行的伙计、站点的老骑手。"
    "祥子是被刘蕾叫来的。"
    show ll normal at sprite_left
    with dissolve
    ll "「我爸生日，你来。别空手，买条烟。」"
    "他买了一条利群，二百六。进门的时候，老刘看见烟，笑得很响。"
    show lt normal at sprite_right
    with dissolve
    lt "「小杨来了！坐坐坐，坐蕾蕾旁边。」"
    "刘蕾给他挪了个位置。桌上已经摆了八个冷菜，啤酒开了四瓶。"
    "老刘酒量好，一轮一轮地敬。敬到祥子，他把杯子压得很低。"
    lt "「小杨，我听蕾蕾说，你能跑。一个月一千一？」"
    hide ll
    with dissolve
    show xz normal at sprite_right
    with dissolve
    xz "「运气好。」"
    lt "「不是运气。是你不偷懒。」老刘喝了一口，「我跟你讲，我这车行开了十二年，见过的人多了。能跑的人不少，能一直跑的少。你知道为什么？」"
    xz "「不知道。」"
    lt "「因为大部分人，跑着跑着就想'我为什么跑'。你不想，你就能跑。」"
    "桌上的人都笑。祥子也笑，笑得有点僵。"
    "刘蕾给他夹了一块红烧肉。"
    hide lt
    with dissolve
    show ll normal at sprite_right
    with dissolve
    ll "「吃。你太瘦了。」"
    qun "「蕾姐偏心啊，我们怎么没有？」"
    ll "「你有手。」"
    "又是一桌笑。祥子低头吃肉，肉很烂，甜的。他很久没吃过这样的肉。"
    "酒到后半场，老刘开始说站点的事。说加盟商又要换人，说押金压了三十万，说“这行不好做了”。"
    hide xz
    with dissolve
    show lt normal at sprite_right
    with dissolve
    lt "「蕾蕾，你那个站，明年能不能接下来？」"
    ll "「接下来要三十万，你有？」"
    lt "「我没有，你有啊。」"
    ll "「我的钱是我的钱。」"
    "老刘哈哈笑，转头对王站长说：“你看我这个女儿，比我会算。”"
    "王站长赔着笑，眼睛却看了祥子一眼。那一眼很短，祥子记住了。"
    scene bg_office
    with fade
    $ implicit_amb("bg_office")
    "散场的时候，刘蕾送他到门口。夜里有风，她的头发被吹起来，露出一截白白的脖子。"
    show ll normal at sprite_left
    with dissolve
    ll "「祥子。」"
    show xz normal at sprite_right
    with dissolve
    xz "「嗯。」"
    ll "「你觉得我爸怎么样？」"
    xz "「刘老板……挺豪爽。」"
    ll "「他豪爽个屁。」她笑了一下，「他这个人，一分钱能攥出水来。今天这顿饭，他能念叨半年。」"
    "祥子不知道说什么。她看着他，忽然问："
    ll "「你想不想多挣点？」"
    xz "「想。」"
    ll "「那你听我的。下个月开始，你跑晚班。晚班单少，但单价高，罚得也松。你白天睡，晚上跑，一个月能多一千五。」"
    xz "「白天睡不安稳。」"
    ll "「那就看你多想挣钱了。」"
    "她从包里拿出一串钥匙，取下其中一把，递给他。"
    ll "「调度室的。以后你早上来，帮我把白板上的数抄一遍。一个月给你三百。」"
    "祥子看着那把钥匙。铜的，磨得发亮。"
    xz "「这……合适吗？」"
    ll "「有什么不合适。我让你干活，给你钱。」"
    "他把钥匙接过来，攥在手心。钥匙是热的，她的体温。"
    "走回五堡的路上，他把钥匙举到路灯下看。他知道这把钥匙不只是开一扇门。他也知道，自己已经收下了。"
    scene bg_room
    with fade
    $ implicit_amb("bg_room")
    play music "audio/bgm/room_night.ogg" fadein 1.5
    "那天夜里，他在记账本上写："
    "{b}7 月 16 日。刘老板生日。烟 260。{/b}"
    "写完，他停了一下，在下面又写："
    "{b}欠刘蕾：一次超时，一个人情。{/b}"
    "他不知道这个人情值多少钱。他后来知道了。"

    $ track("chapter_complete", chapter="ch03")
    jump ch04
    return
