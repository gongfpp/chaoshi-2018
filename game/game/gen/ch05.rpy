# 由 tools/gen_game.py 自动生成，请勿手改。

label ch05:
    call screen chapter_card("第五章", "四十五天")
    $ track("chapter_enter", chapter="ch05")
    $ amb_layer_pause(0.0)
    $ qian = 9372
    $ debt = 0
    scene bg_alley
    with fade
    $ implicit_amb("bg_alley")
    play music "audio/bgm/alley_dusk.ogg" fadein 1.5
    "十月一号，国庆。"
    "那天单多，从早上七点开始，手机就没停过。祥子跑到下午两点，实在憋不住，回五堡上个厕所，顺便给车充电。"
    "他把车停在十二号楼下，锁了两道，一道是车锁，一道是碟刹锁。上楼，烧水，泡了碗面。"
    "二十分钟。"
    "下来的时候，车没了。"
    scene bg_alley
    with fade
    $ implicit_amb("bg_alley")
    play music "audio/bgm/silence_tense.ogg" fadein 1.5
    "巷子很静。下午两点半，太阳很好，晾衣绳上的被单在风里鼓起来。"
    "祥子站在原地，看着那块空地。地上有一道刹车印，是他的车早上进来时留下的。"
    "他往前走了几步，又走回来。他蹲下去，摸了摸地面。地面是热的。"
    show xz normal at sprite_left
    with dissolve
    xz "「车呢？」"
    "他问自己。然后他开始跑。"
    "跑到巷口，问修鞋的老头。老头说没看见。跑到隔壁的棋牌室，四个人在打牌，说没注意。跑到高姐那儿，高姐正在阳台上收衣服，听见他喊，探出头来。"
    show gj normal at sprite_right
    with dissolve
    gj "「什么车？」"
    xz "「我的车！蓝色的！」"
    gj "「……」"
    "高姐下楼，看了看那块空地，又看了看他。"
    gj "「锁了没有？」"
    xz "「锁了两道。」"
    gj "「两道也没用。上个月老周的车，锁了三道，一样没了。」"
    scene bg_office
    with fade
    $ implicit_amb("bg_office")
    play music "audio/bgm/office_hum.ogg" fadein 1.5
    "派出所离五堡三公里。祥子跑着去的，跑到的时候，衬衫全湿了。"
    "接待他的是个年轻警察，二十七八岁，正在吃盒饭。"
    show xz normal at sprite_left
    with dissolve
    xz "「我车被偷了。」"
    police "「什么时候？」"
    xz "「两点十分左右。五堡十二号楼下。蓝色的，七十二伏，新车，骑了四十五天。」"
    police "「发票呢？」"
    xz "「在车上。」"
    police "「……」"
    "警察把盒饭放下，抽了张表。"
    police "「车牌号记得吗？」"
    xz "「记得。杭……」"
    police "「写这儿。」"
    "祥子写了。写完，警察看了一眼。"
    police "「这车上了牌，有登记。我们给你录进去。有消息通知你。」"
    xz "「多久能有消息？」"
    police "「不好说。这种案子，找到了会打你电话。」"
    xz "「那要是找不到呢？」"
    police "「找不到就是找不到。」"
    "祥子站在那里。他看见警察桌上有一摞表，最上面那张写着“电动车被盗”，日期是九月二十八。<!-- s:xz -->「同志，我想问一下，监控……」"
    police "「五堡那边的监控，归街道管。你去问问。」"
    scene bg_alley
    with fade
    $ implicit_amb("bg_alley")
    play music "audio/bgm/alley_dusk.ogg" fadein 1.5
    scene bg_alley
    with fade
    $ implicit_amb("bg_alley")
    play music "audio/bgm/alley_dusk.ogg" fadein 1.5
    "街道办的人说，巷子里的监控是去年装的，坏了半年，一直没修。"
    "物业说，五堡是农民房，没有物业。"
    "房东高姐说，她只负责租房，车丢了不归她管。"
    "祥子一家一家问，问到天黑。他回到十二号楼下，坐在台阶上。"
    "那块空地还在。地上有一小片油渍，是他的车漏的。"
    "五堡丢车是常事。"
    "王大勇说，去年一年，这条巷子丢了十一辆。有人专门收这种车，推到乔司那边拆了卖零件，车架论斤，电池最值钱，一组能卖六七百。"
    wd "「你这算好的。老周那辆，锁了三道，第二天早上只剩一个轮子。」"
    show xz normal at sprite_left
    with dissolve
    xz "「报警没用？」"
    wd "「有用。警察给你登记，登记完就完了。」"
    wd "「我丢第一辆的时候，天天去派出所问。问到第三个月，那个警察看见我就躲。」"
    "高姐从楼上下来，手里端着一盆水，泼在墙根。"
    show gj normal at sprite_right
    with dissolve
    gj "「我儿子以前也跑单。」"
    xz "「他也丢过？」"
    gj "「丢过两辆。后来不跑了，去学开叉车，现在在物流园，一个月六千五，有社保。」"
    gj "「他跟我说，妈，跑单不是人干的。」"
    "祥子没说话。"
    "一个穿蓝衣服的骑手在巷口停下，脚撑着地，看了看他。"
    qun "「你车丢了？」"
    xz "「嗯。」"
    qun "「什么颜色？」"
    xz "「蓝的。七十二伏。」"
    qun "「我帮你留意。我们群里每天都有人发收车的消息。」"
    "他骑走了。祥子连他叫什么都不知道。"
    gj "「吃饭没有？」"
    "高姐端了一碗饭下来，饭上卧着一个荷包蛋。"
    xz "「吃不下。」"
    gj "「吃不下也得吃。你跟车较劲，车能回来？」"
    "祥子接过碗，扒了两口，忽然把脸埋进手里。"
    "他没有哭出声。肩膀抖了几下，就停了。"
    scene bg_market
    with fade
    $ implicit_amb("bg_market")
    play music "audio/bgm/market_noise.ogg" fadein 1.5
    "有人告诉他，九堡有个收车的地方。"
    "在一片拆了一半的厂房后面，铁皮围挡，门口停着几辆面包车。里面停着几十辆电动车，新的旧的都有，车架上用白漆写着编号。"
    "祥子走进去，一个穿背心的男人拦住他。"
    boss "「买车？」"
    show xz normal at sprite_left
    with dissolve
    xz "「找车。」"
    boss "「找什么车？」"
    xz "「蓝色的，七十二伏，车架上有道划痕，在后轮附近。」"
    "男人看了他一眼。"
    boss "「这儿没有你的车。」"
    xz "「我看一眼。」"
    boss "「说了没有。」"
    xz "「我就看一眼。」"
    "男人往前一步，挡在他面前。"
    boss "「小兄弟，我跟你讲道理。这儿的车，都有主的。你说你的车在这儿，你拿什么证明？」"
    xz "「我有发票。」"
    boss "「发票上写车架号了吗？」"
    xz "「……」"
    boss "「没写吧。」"
    boss "「没写，就证明不了。」"
    boss "「你走吧。」"
    "祥子站在那儿，没动。"
    "男人身后又出来两个人。"
    boss "「怎么？想打架？」"
    xz "「我不想打架。」"
    boss "「那就走。」"
    "祥子转身走了。"
    "走出十几米，他回头看了一眼。那几十辆车停在那儿，在太阳底下反着光。"
    "其中有一辆，可能就是他的。"
    "他没有再回头。"
    scene bg_market
    with fade
    $ implicit_amb("bg_market")
    play music "audio/bgm/market_noise.ogg" fadein 1.5
    "第二天下午，他去了彭埠的二手电动车市场。"
    "一条街，两边都是修车铺，门口摆着旧车、旧电池、旧轮胎。有人蹲在地上拆电机，有人在给车架喷漆。空气里全是橡胶和机油的味道。"
    "祥子一辆一辆看。他知道希望不大，但他还是看。"
    "看到第三家，他停住了。"
    "墙角堆着几组电池，其中一组，外壳上贴着一张小小的贴纸，是卡通猫，缺了一只耳朵。"
    "那是高姐的猫。他买车那天，高姐的孙女在楼下玩贴纸，给他贴了一张。"
    show xz normal at sprite_left
    with dissolve
    xz "「老板，这电池哪来的？」"
    boss "「收的。」"
    xz "「跟谁收的？」"
    boss "「记不清了。一天收十几组。」"
    xz "「这组我要了。」"
    boss "「八百。」"
    xz "「这电池是我的。」"
    boss "「你的？你叫它一声它答应吗？」"
    "祥子看着他。老板四十多岁，胳膊上有一道疤，手里拿着一把扳手。"
    "祥子没有再说。他掏出手机，扫了八百。"
    scene bg_alley
    with fade
    $ implicit_amb("bg_alley")
    play music "audio/bgm/alley_dusk.ogg" fadein 1.5
    "他把电池拎回五堡，放在那块空地上。"
    "同乡王大勇来看他，蹲下来看那组电池。"
    wd "「就剩这个了？」"
    show xz normal at sprite_left
    with dissolve
    xz "「嗯。」"
    wd "「六百九的车，剩八百的电池。你还赚了。」"
    xz "「……」"
    wd "「行了，别丧气。这地方一年丢几十辆。你才丢一辆。」"
    "王大勇拍拍他的肩，走了两步，又回头。"
    wd "「祥子，以后人家问你叫什么，你就说'电池'。电池祥子，好记。」"
    "祥子没笑。但那天晚上，站点群里有人发消息：{b}电池祥子，明天帮我带包烟。{/b}"
    "他看着那四个字，看了很久。然后他回了一个“好”。"
    scene bg_room
    with fade
    $ implicit_amb("bg_room")
    play music "audio/bgm/room_night.ogg" fadein 1.5
    "他在本子上写："
    "{b}10 月 1 日。车丢了。45 天。{/b}"
    "{b}10 月 3 日。电池卖 800。{/b}"
    "写完，他把笔放下，从床底下摸出一瓶白酒。是上个月老刘生日剩的，他带回来一直没喝。"
    "他拧开盖子，喝了一口。辣，从嗓子一直烧到胃。"
    "他又喝了一口。"
    show xz normal at sprite_left
    with dissolve
    xz "「四十五天。」"
    "他对着墙说。墙上的水渍还在，像一只趴着的狗。"
    "「六千九。四十五天。」"
    "他想起提车那天，老刘说“以后车坏了我修”。他想起江边的风，想起他在本子上画的那个圈，圈里写着“自己的”。"
    "他拿起笔，翻到那一页，看着那个圈。"
    "然后他把笔尖按下去，在“自己的”三个字上，画了一道横线。"
    "画完，他把本子合上，仰面躺下。"
    "天花板上的灯泡在晃。他喝多了，看什么都在晃。"
    play sound "audio/sfx/phone_notify.ogg"
    "手机响了。是刘蕾。"
    "{b}「听说你车丢了？」{/b}"
    "他盯着屏幕，没有回。"
    "过了一会儿，又来一条。"
    "{b}「明天来站点，我给你想办法。」{/b}"
    "祥子把手机扣在胸口。他想回“不用”，想了半天，回了一个“好”。"
    "窗外有人在放国庆的烟花，很远，“砰”的一声，光在窗帘上亮了一下，就没了。"

    $ track("chapter_complete", chapter="ch05")
    jump ch06
    return
