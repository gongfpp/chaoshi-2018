# 由 tools/gen_game.py 自动生成，请勿手改。

label ch10:
    call screen chapter_card("第十章", "封城")
    $ track("chapter_enter", chapter="ch10")
    $ amb_layer_pause(0.0)
    $ qian -= 2649
    scene bg_station
    with fade
    $ implicit_amb("bg_station")
    play music "audio/bgm/station_room.ogg" fadein 1.5
    "腊月二十九，站点开会。"
    "王站长站在白板前，戴着一个蓝色的医用口罩，说话的声音闷闷的。"
    wz "「武汉封了。浙江今天启动一级响应。从明天起，所有人必须戴口罩，一天两个，站点发。箱子一天消毒两次。」"
    qun "「站长，口罩不够怎么办？」"
    wz "「不够就自己想办法。网上买，药店买，别来问我。」"
    qun "「网上都卖光了。」"
    wz "「那你就别出门。」"
    "大家笑了一下，笑得不太自然。"
    "祥子领了十个口罩，两瓶消毒水。他把口罩塞进保温箱的夹层，把消毒水放在车筐里。"
    scene bg_alley
    with fade
    $ implicit_amb("bg_alley")
    play music "audio/bgm/alley_dusk.ogg" fadein 1.5
    "正月初二，五堡封了。"
    "巷口拉了一道铁马，两个穿红马甲的人守着，桌上放着一个测温枪、一本登记簿。"
    vol "「出入证有没有？」"
    show xz normal at sprite_left
    with dissolve
    xz "「什么出入证？」"
    vol "「社区发的。一户一张，两天出去一次，一次两小时。」"
    xz "「我是送外卖的。」"
    vol "「送外卖的也要证。」"
    xz "「我一天要跑十几个小时，两天出去一次，我怎么跑？」"
    vol "「那我不管。你去社区办。」"
    "祥子去了社区。社区在一条巷子的尽头，门口排了三十多个人，都戴着口罩，隔着一米站着。"
    "排了两个小时，轮到他。"
    staff "「身份证。租房合同。单位证明。」"
    xz "「单位证明是什么？」"
    staff "「公司盖章，证明你必须在岗。」"
    xz "「我们公司……在萧山。」"
    "工作人员抬起头，看了他一眼。"
    staff "「那你让你们站长开个证明，拍照发过来，打印出来，盖章。」"
    xz "「盖章要回萧山？」"
    staff "「对。」"
    "祥子站在社区门口，风很大。他把口罩往上拉了拉，呼出的气在眼镜上结了一层雾——他没有眼镜，是睫毛上结了水汽。"
    scene bg_station
    with fade
    $ implicit_amb("bg_station")
    play music "audio/bgm/station_room.ogg" fadein 1.5
    "证明是刘蕾想办法弄的。"
    "她找了个做广告的朋友，刻了一个“杭州速达配送服务有限公司”的章，在打印纸上盖了一下。"
    show ll normal at sprite_left
    with dissolve
    ll "「别说出去。」"
    show xz normal at sprite_right
    with dissolve
    xz "「这……能行吗？」"
    ll "「不行也得行。你不跑，我们吃什么？」"
    "祥子拿着那张纸，看着上面的红章。章盖得有点歪，“速达”两个字压在一起。"
    "他把纸折好，放进内兜。"
    scene bg_road
    with fade
    $ implicit_amb("bg_road")
    play music "audio/bgm/city_empty.ogg" fadein 1.5
    play sound "audio/sfx/scooter.ogg"
    "二月的杭州是空的。"
    "马路上一辆车都没有，红绿灯还在闪，闪着给空气看。商场关门，写字楼关门，只有药店、超市、菜场开着，门口排着队，人和人之间隔着一米。"
    "订单变了。"
    "以前是奶茶、炸鸡、麻辣烫，现在是药、菜、米、油、纸尿裤。一单二十斤，从超市扛到六楼。"
    qun "「今天八单，九十六块。口罩用了三个。」"
    qun "「我十二单，一百四。电梯不敢坐，爬了八趟楼。」"
    qun "「你们还有单。我这儿一下午就两单，都是口罩。」"
    qun "「口罩怎么送？」"
    qun "「挂门把手上，敲门，跑。」"
    "祥子那天送了一单药。"
    "地址是采荷小区，六楼。备注写着：{b}独居老人，不会用手机，请敲门，谢谢。{/b}"
    play sound "audio/sfx/door_knock.ogg"
    "他爬上去，敲门。门开了一条缝，一个老太太露出半张脸，戴着棉布口罩。"
    old "「谁？」"
    show xz normal at sprite_left
    with dissolve
    xz "「送药的。您儿子买的。」"
    old "「哦……哦。」"
    "她接过袋子，看了半天。"
    old "「小伙子，你等一等。」"
    "她转身进屋，出来的时候，手里拿着一个白色的口罩，N95，包装上印着“3M”。"
    old "「给你。我儿子寄的，我戴不惯。」"
    xz "「奶奶，这个您留着，现在买不到。」"
    old "「我一个老太婆，不出门。你天天在外面跑。」"
    xz "「不行，我不能要。」"
    old "「拿着。」"
    "她把口罩塞进他手里，关上了门。"
    "祥子站在楼道里，手里捏着那个口罩。楼道很暗，只有一扇小窗透进光。他听见门里传来电视的声音，是新闻，在说“应收尽收”。"
    "他把口罩放进内兜，贴着那张盖了歪章的证明。"
    scene bg_rain
    with fade
    $ implicit_amb("bg_rain")
    play music "audio/bgm/rain_light.ogg" fadein 1.5
    "也有难堪的时候。"
    "有一天下午下雨，他送一份菜到一个小区。小区封了，只开一个门，门口摆着两张桌子，物业在登记。"
    guard "「外卖不能进。」"
    show xz normal at sprite_left
    with dissolve
    xz "「顾客让我送进去。」"
    guard "「让他下来拿。」"
    xz "「他电话不接。」"
    "他在雨里等了四十分钟。餐在箱子里，菜是凉的，汤洒了一点。"
    "顾客终于回电话了。"
    cust "「你放门口不就行了？」"
    xz "「门口不让放。」"
    cust "「那你等着。」"
    "又等了十分钟，一个穿睡衣的男人撑着伞出来，接过袋子，看了一眼。"
    cust "「都凉了。」"
    xz "「对不起。」"
    cust "「算了。」"
    "他转身走了。祥子站在雨里，看着他的背影。"
    xz "「对不起。」"
    "他又说了一遍，对着空气。"
    scene bg_road
    with fade
    $ implicit_amb("bg_road")
    play music "audio/bgm/city_empty.ogg" fadein 1.5
    "二月中旬，他送过一单特别的。"
    "下单的是个大学生，地址在城西一个老小区，六楼。订单是火锅食材：肥牛、虾滑、宽粉、金针菇、两瓶可乐。"
    "备注写着：{b}隔离第七天，一个人，想吃点热的。放门口就行，谢谢。{/b}"
    $ pa("shop_sale")
    "祥子到超市取货，装了满满一箱。"
    "他骑到小区门口，登记，量体温，进去。小区里很静，只有几只鸟在叫。"
    "爬到六楼，他把东西放在门口，拍照，点“已送达”。"
    "转身要走的时候，门里传来声音。"
    boy "「是外卖吗？」"
    show xz normal at sprite_left
    with dissolve
    xz "「是。放门口了。」"
    boy "「谢谢。」"
    boy "「你等一下。」"
    "门开了一条缝，一只手伸出来，手里拿着一个橘子。"
    boy "「给你。」"
    xz "「不用。」"
    boy "「拿着吧。我买了十斤，一个人吃不完。」"
    xz "「……谢谢。」"
    "他接过橘子。"
    "门关上了。"
    "他站在门口，手里捏着那个橘子，站了一会儿。"
    "下楼的时候，他听见六楼传来音乐声，很小，是有人在放歌。"
    scene bg_room
    with fade
    $ implicit_amb("bg_room")
    play music "audio/bgm/room_night.ogg" fadein 1.5
    "那天晚上，他把橘子剥了，分成两半，一半给刘蕾。"
    "她正在算账，头也没抬。"
    show ll normal at sprite_left
    with dissolve
    ll "「哪来的？」"
    show xz normal at sprite_right
    with dissolve
    xz "「一个顾客给的。」"
    ll "「顾客给你橘子？」"
    xz "「嗯。」"
    ll "「为什么？」"
    xz "「不知道。」"
    "她抬起头，看了他一眼，笑了。"
    ll "「你这个人，运气好。」"
    xz "「运气好？」"
    ll "「有人给你橘子，就是运气好。」"
    "她把橘子吃了，把皮扔进垃圾桶。"
    ll "「甜。」"
    scene bg_room
    with fade
    $ implicit_amb("bg_room")
    play music "audio/bgm/room_night.ogg" fadein 1.5
    "三月十号，站点复工，单量恢复到六成。"
    "二月他跑了不到五百单，收入三千八。这是他来杭州以后最低的一个月。"
    "刘蕾把账本摊在床上，算给他看。"
    show ll normal at sprite_left
    with dissolve
    ll "「二月亏了两千六。三月能补回来。」"
    show xz normal at sprite_right
    with dissolve
    xz "「嗯。」"
    ll "「祥子。」"
    xz "「嗯？」"
    ll "「我们要个孩子吧。」"
    "祥子抬起头。她坐在床沿，穿着一件旧的棉睡衣，头发散着，脸上的肉有点松。"
    "她三十五了。再过几个月，就三十六。"
    xz "「现在？这个时候？」"
    ll "「这个时候怎么了？都在家，正好。」"
    xz "「万一……」"
    ll "「万一什么？万一染上？我们这儿一个都没有。」"
    xz "「我是说钱。」"
    ll "「钱我有。六万。」"
    xz "「那是你的钱。」"
    ll "「我跟你说了，我现在是你老婆。」"
    "她走过来，坐在他旁边，把手放在他手上。她的手很热。"
    ll "「祥子，我不怕穷。我怕的是，等到我们有钱了，我生不出来了。」"
    xz "「……」"
    ll "「你答应我。」"
    "祥子看着她。他想起婚礼那天，她站在门口迎客，笑得很大声。他想起她说“你说的话，我信”。"
    "他点了点头。"
    scene bg_alley
    with fade
    $ implicit_amb("bg_alley")
    play music "audio/bgm/alley_dusk.ogg" fadein 1.5
    "三月，五堡的房客走了一半。"
    "做装修的老陈回安徽了，走的时候把电饭锅和被子都留下，说“等疫情过了再来”。做保洁的两个大姐也走了，她们的活停了，房租交不上。"
    "高姐坐在门口，剥着毛豆，盆里的毛豆越来越少。"
    show gj normal at sprite_left
    with dissolve
    gj "「十二间房，空了五间。」"
    show xz normal at sprite_right
    with dissolve
    xz "「会回来的。」"
    gj "「回来什么。他们在老家待两个月，就不想出来了。」"
    gj "「在老家，一个月挣两千，但是不用交房租，不用看人脸色。」"
    gj "「在这儿，一个月挣七千，房租一千，吃饭一千，寄回家两千，剩三千。」"
    gj "「三千块，换一条命。你说值不值？」"
    "祥子没答。"
    "他想起自己。他一个月挣七千，房租一千，吃饭一千二，寄回家两千，还债两千。"
    "剩八百。"
    "八百块，他活了一个月。"
    gj "「祥子，你攒下钱没有？」"
    xz "「攒了点。」"
    gj "「多少？」"
    xz "「……六千。」"
    gj "「六千。」高姐重复了一遍，「你来两年了。」"
    xz "「嗯。」"
    gj "「两年，六千。」"
    "她把毛豆壳往盆里一推，站起来。"
    gj "「我跟你说，钱要分开存。一张卡还债，一张卡过日子，一张卡死活不动。」"
    xz "「为什么？」"
    gj "「因为人到了急的时候，什么都敢动。你要是只有一张卡，一次就花完了。」"
    gj "「我男人在工地上摔断过腿。那时候我要是有三张卡，也不至于去借高利贷。」"
    "祥子看着她。"
    "她的手上有一道很深的疤，从虎口一直到手腕。"
    scene bg_alley
    with fade
    $ implicit_amb("bg_alley")
    play music "audio/bgm/alley_dusk.ogg" fadein 1.5
    "那天晚上，他下楼倒垃圾，看见巷口的铁马还没撤。"
    "两个穿红马甲的人坐在棚子里，一个人打瞌睡，一个人在刷手机。"
    "祥子走过去，把手里的一包烟放在桌上。"
    vol "「干什么？」"
    show xz normal at sprite_left
    with dissolve
    xz "「给你们抽。夜里冷。」"
    "那人看了他一眼，把烟收下了。"
    vol "「谢了。你是送外卖的吧？」"
    xz "「嗯。」"
    vol "「你们辛苦。」"
    xz "「你们也辛苦。」"
    "祥子往回走。走到楼道口，他回头看了一眼。"
    "棚子里的灯很亮，照着那张登记簿。风把纸吹起来，又落下去。"
    "他忽然觉得，这个城市像一个巨大的机器，所有的齿轮都在转，只有他是被夹在中间的那粒沙子。"
    "可他还是在转。"

    $ track("chapter_complete", chapter="ch10")
    jump ch11
    return
