# 由 tools/gen_game.py 自动生成，请勿手改。

label ch14:
    call screen chapter_card("第十四章", "小福")
    $ qian -= 1300
    $ debt -= 15000
    scene bg_alley
    with fade
    play music "audio/bgm/alley_dusk.ogg" fadein 1.5
    "五月十六号，小福发来一条微信。"
    "{b}「祥子哥，你有空吗？」{/b}"
    "他当时在送单，没回。晚上回过去，没人接。"
    "第二天，他去了四季青。"
    "丽人足道在服装市场后面的巷子里，门口挂着一串红灯笼，玻璃门上贴着“足浴 按摩 修脚”。他推门进去，一个穿黑制服的女人迎上来。"
    boss "「先生几位？」"
    show xz tired at sprite_left
    with dissolve
    xz "「我找罗小福。」"
    boss "「小福？她走了。」"
    xz "「走哪儿去了？」"
    boss "「不知道。她爸来接的，说家里有事。」"
    "祥子站在门口。屋里有一股艾草的味道，沙发上坐着一个正在修脚的男人，电视里在放一部老电视剧。"
    xz "「她干了多久？」"
    boss "「两年多。这姑娘手脚勤快，客人喜欢。」"
    xz "「她……欠你们钱吗？」"
    boss "「不欠。工资都结了。」"
    "祥子走出来。太阳很大，巷子里的衣服在风里晃。"
    "他掏出手机，又打了一次。关机。"
    scene bg_ktv
    with fade
    play music "audio/bgm/ktv_night.ogg" fadein 1.5
    "找到小福，是三天以后。"
    "一个老乡告诉他，罗二强把女儿送进了金座 KTV，在秋涛北路，做“前台”。"
    "祥子晚上十点过去的。"
    "KTV 门口停着一排车，霓虹灯把地面照成紫红色。他站在马路对面，等了半个小时。"
    "十点四十，一群女孩从侧门出来，穿着一样的黑色短裙，站在门口抽烟。"
    "小福在最后面。"
    "她瘦了。脸上化了妆，嘴唇很红，头发烫了，搭在肩上。她穿着一双很高的高跟鞋，站得不太稳。"
    show xz tired at sprite_left
    with dissolve
    xz "「小福。」"
    "她转过头，看见他，愣住了。"
    "然后她笑了，笑得很快，像要遮掩什么。"
    show xf normal at sprite_right
    with dissolve
    xf "「祥子哥。你怎么来了？」"
    xz "「你在这儿干什么？」"
    xf "「上班啊。」"
    xz "「上什么班？」"
    xf "「前台。就……倒倒酒，陪客人说说话。」"
    "祥子看着她。她的裙子很短，领口很低。"
    xz "「谁让你来的？」"
    xf "「我爸。」"
    xz "「他收了多少？」"
    xf "「……两万。」"
    xz "「两万块，把你卖了？」"
    xf "「不是卖。是介绍费。他说这行挣钱，一个月能挣一万。」"
    xz "「挣一万，你挣了多少？」"
    xf "「……」"
    "她不说话。手里的烟快烧到手指了，她也没扔。"
    xf "「祥子哥，你别管我。」"
    xz "「我不管你谁管你？」"
    xf "「你管不了。」"
    "她把烟扔在地上，用高跟鞋碾了一下。"
    xf "「你老婆刚走，你欠着八万块，你女儿在老家。你管我？」"
    xz "「……」"
    xf "「我不是怪你。」她的声音软下来，「我是说，你顾好你自己。」"
    scene bg_alley
    with fade
    play music "audio/bgm/alley_dusk.ogg" fadein 1.5
    "那天晚上，他想起小福刚来杭州的时候。"
    "二〇一八年六月，她提着一个编织袋，站在五堡巷口，问他哪里有卖馒头的。"
    "他带她去巷子口的小卖部，买了两个馒头，一包榨菜。"
    "她蹲在台阶上吃，吃得很快，噎着了，用手捶胸口。"
    show xf normal at sprite_left
    with dissolve
    xf "「哥，杭州真大。」"
    show xz tired at sprite_right
    with dissolve
    xz "「大。」"
    xf "「我坐地铁，坐反了两次。」"
    xf "「我不敢问人。我怕人家嫌我土。」"
    "后来她在足浴店上班，一个月三千二，包住。她每个月寄两千回家，自己留一千二。"
    "她跟他说过她妈。"
    xf "「我妈的手，关节都变形了，筷子都拿不住。」"
    xf "「医生说换个关节要三万。我说我攒，我妈说不治了。」"
    xf "「我弟学习好，老师说能考上县一中。一中一年要八千。」"
    "她说这些的时候在笑，好像在说别人的事。"
    xf "「哥，你说我是不是很没用？」"
    xz "「不是。」"
    xf "「那我为什么挣不到钱？」"
    xz "「因为钱不好挣。」"
    xf "「那你怎么挣？」"
    xz "「我跑。」"
    "她低下头，看着自己的手。"
    xf "「我也想跑。」"
    xf "「可是我不会骑车。」"
    scene bg_alley
    with fade
    play music "audio/bgm/tense.ogg" fadein 1.5
    "祥子去找罗二强，是第二天。"
    "罗二强住在五堡后面的一片民房里，一间十平米的屋子，地上全是酒瓶。"
    "他正在喝酒，看见祥子，笑了一下。"
    rq "「哟，女婿来了。」"
    show xz tired at sprite_left
    with dissolve
    xz "「你把小福弄到 KTV 去了？」"
    rq "「她自己愿意去的。那地方挣钱。」"
    xz "「她十九岁。」"
    rq "「十九岁怎么了？她妈十九岁就生她了。」"
    xz "「你还是人吗？」"
    rq "「你他妈说谁？」"
    "祥子一拳打过去。"
    "他没有打过人。拳头打在罗二强的脸上，他的手也疼，指关节像裂开一样。"
    "罗二强倒在地上，摸了一下嘴，看见血，扑上来。"
    "两个人在十平米的屋子里打。酒瓶倒了，碎了。邻居在门外喊。"
    "最后是派出所的人来的。"
    scene bg_office
    with fade
    play music "audio/bgm/office_hum.ogg" fadein 1.5
    "调解室里，警察坐在中间。"
    police "「谁先动的手？」"
    rq "「他！」"
    show xz tired at sprite_left
    with dissolve
    xz "「我。」"
    police "「为什么打人？」"
    xz "「他把他女儿卖到 KTV。」"
    rq "「你放屁！那是介绍工作！」"
    police "「行了。」警察敲了敲桌子，「打人不对，知道吗？」"
    xz "「知道。」"
    police "「医药费，赔五百。写个保证书，以后不再动手。」"
    "祥子掏了五百。罗二强拿着钱，数了数，塞进兜里。"
    rq "「小子，你等着。」"
    "警察瞪了他一眼。他走了。"
    police "「小伙子。」警察收拾桌上的材料，头也不抬，「你要是真为她好，就去把她接出来。打她爸有什么用？」"
    xz "「她不出来。」"
    police "「那就是她自己的选择。」"
    scene bg_cao
    with fade
    play music "audio/bgm/room_warm.ogg" fadein 1.5
    "六月，他去找曹先生。"
    "不是送单，是有事。他站在求智巷的楼下，等了两个小时。"
    "曹先生下班回来，看见他，愣了一下。"
    show cy normal at sprite_left
    with dissolve
    cy "「祥子？你怎么在这儿站着？」"
    show xz tired at sprite_right
    with dissolve
    xz "「曹先生，我想请教您一件事。」"
    "他把事情说了。刘蕾的死，医院的账，老刘的钱，KTV 里的小福。"
    "曹先生听完，很久没说话。楼道里的声控灯灭了，他跺了一下脚，灯又亮了。"
    cy "「上楼说吧。」"
    scene bg_cao
    with fade
    play music "audio/bgm/room_warm.ogg" fadein 1.5
    "曹家的客厅很小，一面墙是书，一张旧藤椅，一张饭桌。周红给他倒了一杯茶。"
    show cy normal at sprite_left
    with dissolve
    cy "「第一件事，你太太的医疗费，你有没有想过，为什么会这么高？」"
    show xz tired at sprite_right
    with dissolve
    xz "「没有医保。」"
    cy "「为什么没有医保？」"
    xz "「公司没给我们交。」"
    cy "「公司不交，是违法的。」曹先生拿出一张纸，「你跟她签的协议，我看看。」"
    "祥子从包里掏出那张折了很多次的《劳务协议》。曹先生看了十分钟。"
    cy "「这个是承揽协议，不是劳动合同。他们把你当成个体户。」"
    xz "「什么意思？」"
    cy "「意思是，你不是他们的员工。你受伤，他们不赔；你生病，他们不管；你老婆生孩子，跟他们没关系。」"
    xz "「那我怎么办？」"
    cy "「可以申请劳动仲裁，确认劳动关系。有聊天记录吗？排班表？罚款单？工服照片？」"
    xz "「有。我都有。」"
    cy "「那就写。」"
    scene bg_cao
    with fade
    play music "audio/bgm/room_warm.ogg" fadein 1.5
    "曹先生帮他写了三页纸。"
    "仲裁申请书，请求确认劳动关系，补缴社保，支付未签合同的双倍工资差额。"
    "写完，他签了名，按了手印。"
    show cy normal at sprite_left
    with dissolve
    cy "「祥子，我跟你说实话。这个仲裁，赢的概率不大。」"
    show xz tired at sprite_right
    with dissolve
    xz "「为什么？」"
    cy "「因为你们签的是承揽协议，公司会说你是合作方。法院有时候认，有时候不认。」"
    xz "「那我还写？」"
    cy "「写。就算输，也让他们知道，有人会问。」"
    "祥子把纸折好，放进内兜。"
    xz "「曹先生，还有一件事。」"
    cy "「你说。」"
    xz "「我欠您一万块……」"
    cy "「那个不急。」"
    xz "「我可能……还要很久。」"
    cy "「祥子。」曹先生看着他，「我借你钱，不是投资。你不用还利息，也不用急着还本金。你什么时候有，什么时候还。」"
    xz "「为什么？」"
    cy "「因为你是个好人。」"
    xz "「好人有什么用？」"
    cy "「没用。」曹先生笑了一下，「但是好人晚上睡得着。」"
    scene bg_cao
    with fade
    play music "audio/bgm/room_sad.ogg" fadein 1.5
    "那是他最后一次见曹先生。"
    "七月底，他听说曹先生被学校约谈了，因为一篇访谈，里面说了些不该说的话。他的课停了，和朋友的书店也关了。"
    "八月三号，曹家搬家。"
    "祥子去送。一辆小货车，几个纸箱，一摞书。"
    show cy normal at sprite_left
    with dissolve
    cy "「去南京。我老婆在那边找了个医院。」"
    show xz tired at sprite_right
    with dissolve
    xz "「还回来吗？」"
    cy "「不知道。」"
    cy "「祥子，地图册还在吗？」"
    xz "「在。」"
    cy "「留着。别丢了。」"
    "车开了。曹先生坐在副驾驶，从窗户里伸出手，摆了摆。"
    "祥子站在巷口，看着车拐弯，消失。"
    scene bg_alley
    with fade
    play music "audio/bgm/alley_dusk.ogg" fadein 1.5
    "七月二十八号，五堡贴了拆迁通知。"
    "红纸黑字，盖着三个章。限八月底搬离。"
    "高姐坐在门口，剥着毛豆，剥着剥着就哭了。"
    show gj normal at sprite_left
    with dissolve
    gj "「我在这儿住了十六年。」"
    show xz tired at sprite_right
    with dissolve
    xz "「赔多少？」"
    gj "「按面积。我这楼，赔三套。」"
    gj "「三套有什么用？我这些人，都走了。」"
    "祥子站在巷子里，看着那些晾衣绳。绳子上的衣服一件一件，被风吹起来。"
    "他在这里住了三年零五个月。"
    scene bg_night_street
    with fade
    play music "audio/bgm/city_night.ogg" fadein 1.5
    "八月十五号，他搬到乔司。"
    "一间十平米的房子，月租一千三，比五堡贵三百。到新塘站十一公里，骑车四十分钟。"
    "搬家那天，他只用了两个编织袋。"
    "一个装被子衣服，一个装锅碗。记账本、地图册、那对印着“百年”的杯子，放在最上面。"
    scene bg_ktv
    with fade
    play music "audio/bgm/ktv_night.ogg" fadein 1.5
    "搬完家，他去看小福。"
    "KTV 门口，她穿着那件黑裙子，站在台阶上。"
    show xf normal at sprite_left
    with dissolve
    xf "「你搬家了？」"
    show xz tired at sprite_right
    with dissolve
    xz "「嗯。乔司。」"
    xf "「远吗？」"
    xz "「骑车四十分钟。」"
    xf "「……」"
    "她低下头，抠着手指甲。"
    xf "「祥子哥，我不想干了。」"
    xz "「那就不干。」"
    xf "「我爸会打死我。」"
    xz "「他敢。」"
    xf "「他敢。他打过我妈。」"
    menu:
        "当晚带她走":
            $ xf_saved = True
            jump ending_raolu
        "下个月再来接她":
            $ xf_saved = False
    "祥子看着她。"
    "霓虹灯把她的脸照成两种颜色，一半红，一半黑。"
    "他想起三年前，她在巷口递给他那对杯子，说“祥子哥，你以后还会来吗”。"
    "他想起自己说“会”。"
    xz "「小福，你跟我走。」"
    xf "「去哪儿？」"
    xz "「我那儿。乔司。我先给你找个活儿。」"
    xf "「你那儿就一间房。」"
    xz "「我睡地上。」"
    "她笑了一下，眼泪掉下来。"
    xf "「祥子哥，你连自己都顾不住。」"
    xz "「我顾得住。」"
    xf "「你顾不住。你欠八万五，你女儿在老家，你一个月挣七千。你带我走，我们俩一起饿死？」"
    "祥子说不出话。"
    xf "「等你还完债。」她说，「等你還完债，你来接我。」"
    xz "「多久？」"
    xf "「不知道。一年？两年？」"
    xz "「……」"
    xf "「我等你。」"
    "她说完，转身进了门。"
    "门里的光很亮，音乐很响。她走进去，就被那片光吞了。"
    "祥子站在门外，站了很久。"
    xz "「下个月。」"
    xz "「下个月我来接你。」"
    "门里没有人听见。"
    scene bg_room
    with fade
    play music "audio/bgm/room_night.ogg" fadein 1.5
    "那天夜里，他在乔司的房间里写："
    "{b}8 月 15 日。搬乔司。房租 1300。{/b}"
    "写完，他在下面写："
    "{b}欠小福：一次。{/b}"
    "他不知道这一次要还多久。"
    scene bg_office
    with fade
    play music "audio/bgm/office_hum.ogg" fadein 1.5
    "仲裁开庭是九月。"
    "地点在区劳动人事争议仲裁委员会，一间小屋子，一张长桌，三个仲裁员。"
    "公司来了两个人，一个是人事，一个是律师。"
    "律师穿西装，说话很慢。"
    lawyer "「申请人与我司签订的是《承揽协议》，双方系平等的民事合作关系，不存在人身依附性。」"
    lawyer "「申请人可自主决定接单时间，可拒绝派单，可使用自有车辆。这些均不符合劳动关系的从属性特征。」"
    "祥子坐在对面，手里捏着一叠打印纸。"
    "仲裁员问他："
    arb "「申请人，你有什么要说的？」"
    show xz tired at sprite_left
    with dissolve
    xz "「我……我每天早上六点半到站点，晚上十一点下班。」"
    xz "「迟到扣钱，不来算旷工，不穿工服扣五十。」"
    xz "「我不能拒绝派单。拒三次，账号就降级。」"
    xz "「这些……算不算管理？」"
    "律师翻了一页纸。"
    lawyer "「这些是平台的服务质量标准，不是劳动管理。」"
    lawyer "「申请人可以随时停止使用平台服务。」"
    "祥子看着他。"
    xz "「我停了，我吃什么？」"
    "屋里安静了几秒。"
    "仲裁员敲了敲桌子。"
    arb "「双方还有补充吗？」"
    scene bg_office
    with fade
    play music "audio/bgm/office_hum.ogg" fadein 1.5
    "裁决书是两个月后下来的。"
    "薄薄三页纸，最后一行写着：{b}驳回申请人的仲裁请求。{/b}"
    "理由是：双方签订承揽协议，申请人工作时间相对自主，报酬按单结算，不符合劳动关系认定标准。"
    "祥子把裁决书看了三遍。"
    "他不认识“承揽”这两个字，但他看懂了“驳回”。"
    "他给曹先生打电话。"
    show cy normal at sprite_left
    with dissolve
    cy "「输了？」"
    show xz tired at sprite_right
    with dissolve
    xz "「输了。」"
    cy "「……」"
    xz "「曹先生，您说得对。赢不了。」"
    cy "「祥子，你听我说。」"
    cy "「这个裁决，不是终点。今年七月，八部门发了文件，要求平台保障新就业形态劳动者权益。以后会有变化。」"
    xz "「以后是什么时候？」"
    cy "「……我不知道。」"
    xz "「我等不了以后。」"
    cy "「我知道。」"
    "电话两头都沉默了很久。"
    cy "「祥子，你别把这件事当成你的失败。」"
    xz "「那当成什么？」"
    cy "「当成一次记录。」"
    cy "「有人记录，才会有人改。」"
    "祥子把裁决书折好，放进箱子最底下，压在记账本下面。"
    "他没有再提这件事。"

    jump ch15
    return
