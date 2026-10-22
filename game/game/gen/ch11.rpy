# 由 tools/gen_game.py 自动生成，请勿手改。

label ch11:
    call screen chapter_card("第十一章", "建档")
    $ track("chapter_enter", chapter="ch11")
    $ qian -= 1000
    scene bg_room
    with fade
    play music "audio/bgm/room_dawn.ogg" fadein 1.5
    "五月二十六号，早上。"
    "刘蕾从卫生间出来，手里捏着一根验孕棒，手在抖。"
    show ll sick at sprite_left
    with dissolve
    ll "「祥子。」"
    show xz normal at sprite_right
    with dissolve
    xz "「嗯？」"
    ll "「两条。」"
    "祥子坐起来。他看见那根塑料棒上，两道红杠，很浅，但确实是两道。"
    xz "「……有了？」"
    ll "「有了。」"
    "她笑了，笑着笑着，眼泪下来了。"
    ll "「我三十五了。我以为我生不出来了。」"
    "祥子把她抱住。她的身体很软，很热，肩膀在抖。"
    "那一刻他是高兴的。他真的高兴。"
    scene bg_hospital
    with fade
    play music "audio/bgm/hospital_day.ogg" fadein 1.5
    "高兴只持续了三天。"
    "建档。刘蕾是杭州本地户口，户口在彭埠，挂在老刘的房下。她可以去彭埠社区卫生服务中心建档。"
    "去了。医生问了一堆问题，量了血压。"
    "{b}158/98。{/b}"
    "医生皱了皱眉。"
    doc "「你血压高。以前高不高？」"
    show ll sick at sprite_left
    with dissolve
    ll "「有时候高。」"
    doc "「吃药没有？」"
    ll "「没吃。」"
    doc "「空腹血糖查过没有？」"
    ll "「没有。」"
    "医生开了一堆单子：血常规、尿常规、肝肾功能、糖耐量、甲状腺、心电图、B 超。"
    doc "「你是高龄产妇，血压又高，属于高危。我给你转到市一医院，你去那边建档，做系统产检。」"
    ll "「市一？那边人多，排队要一天。」"
    doc "「人多也得去。你这个情况，社区不敢收。」"
    "刘蕾拿着转诊单，站在医院门口。"
    ll "「去市一，一次要请一天假。我现在走不开。」"
    show xz normal at sprite_right
    with dissolve
    xz "「我陪你去。」"
    ll "「你陪我去，你一天少挣三百。」"
    "她把转诊单折起来，塞进包里。"
    "那张纸后来一直没拿出来。"
    scene bg_office
    with fade
    play music "audio/bgm/office_hum.ogg" fadein 1.5
    "六月，王站长还在安徽老家，回不来。站点的事全压在刘蕾身上。"
    "她要排班、要盯准时率、要应付公司的检查、要安抚闹情绪的骑手。她每天早上七点到站点，晚上九点回家，中间只在椅子上眯一会儿。"
    "祥子劝她请假。"
    show ll sick at sprite_left
    with dissolve
    ll "「请什么假？我一走，这个站就乱了。」"
    show xz normal at sprite_right
    with dissolve
    xz "「站乱了可以再整，孩子……」"
    ll "「孩子在我肚子里，跑不了。」"
    "她说完，自己笑了一下。"
    ll "「你放心，我心里有数。」"
    scene bg_office
    with fade
    play music "audio/bgm/office_hum.ogg" fadein 1.5
    "她心里有没有数，祥子不知道。他只知道，那段时间她每天回家越来越晚。"
    "七月的站点出了两件事。"
    "一件是有个骑手在秋涛北路闯红灯，被一辆网约车撞了，腿断了。骑手是众包，站点不认工伤，只给了一千块“慰问金”。他老婆抱着孩子来站点闹，坐在门口哭了一下午。"
    "另一件是有个顾客投诉餐里有头发，要求十倍赔偿。那单是刘蕾派的，她被公司扣了五百。"
    show ll sick at sprite_left
    with dissolve
    ll "「一单四块八，我扣五百。」"
    show xz normal at sprite_right
    with dissolve
    xz "「凭什么扣你？」"
    ll "「因为我是调度。」"
    xz "「又不是你做的餐。」"
    ll "「公司不管谁做的。公司只管谁负责。」"
    "她把包扔在桌上，坐下来，手撑着腰。"
    ll "「祥子，我想把这个站接下来。」"
    xz "「多少钱？」"
    ll "「三十万。」"
    xz "「我们没有三十万。」"
    ll "「我知道。」她闭上眼睛，「我就是想想。」"
    "祥子站在门口，看着她。"
    "她的脸在灯下有点浮肿，眼下是青的。她今天没化妆，眉毛显得更青了。"
    "他想说“你别干了”，但他知道说了没用。他也想说“我养你”，但他知道他说不起。"
    "他最后说："
    xz "「你躺一会儿。我去做饭。」"
    scene bg_hospital
    with fade
    play music "audio/bgm/hospital_day.ogg" fadein 1.5
    "八月，她终于去了一次医院。"
    "不是市一，是彭埠路口那家私立妇产医院，叫“玛莉亚”，门口立着罗马柱，大厅里放着钢琴曲。"
    "一次产检六百。不用排队，护士全程陪着，医生说话很温柔。"
    scene bg_hospital
    with fade
    play music "audio/bgm/hospital_day.ogg" fadein 1.5
    "第一次去，接待他们的是一个穿套装的顾问。"
    "顾问姓陈，说话很甜，一口一个“姐姐”。"
    consult "「姐姐，你这个是高危妊娠，我们这儿有专门的专家团队，一对一服务。」"
    consult "「普通产检六百，专家号八百。做一个套餐更划算，一万二，包到生。」"
    consult "「我们还有月子中心，两万八一个月，二十四小时护理。」"
    "刘蕾听得眼睛发亮。"
    "祥子坐在旁边，一句话没说。"
    "他算了一笔账：套餐一万二，月子中心两万八，加起来四万。他们一共六万。"
    show ll sick at sprite_left
    with dissolve
    ll "「祥子，你看呢？」"
    show xz normal at sprite_right
    with dissolve
    xz "「太贵了。」"
    ll "「不贵。市一排队排一天，我请一天假损失三百。」"
    ll "「而且这儿服务好，医生有耐心。」"
    xz "「医生有耐心，是因为你花了钱。」"
    ll "「花钱买服务，有什么不对？」"
    "他答不上来。"
    "他说不出“这个钱应该花在别处”，因为他不知道别处在哪儿。"
    scene bg_hospital
    with fade
    play music "audio/bgm/hospital_day.ogg" fadein 1.5
    "那天做完检查，医生把他们叫到办公室。"
    "医生姓吴，四十多岁，说话很稳。"
    doc "「你们这个情况，我建议去综合医院。」"
    doc "「我们这儿是专科，真出了并发症，抢救条件不够。」"
    show xz normal at sprite_left
    with dissolve
    xz "「什么并发症？」"
    doc "「子痫、胎盘早剥、产后出血。你太太血压高，体重也偏高，属于高危。」"
    doc "「我不是吓你们。我是告诉你们，万一有事，我们这儿处理不了。」"
    "刘蕾笑了一下。"
    show ll sick at sprite_right
    with dissolve
    ll "「医生，你们这儿不是天天接生吗？」"
    doc "「接生是接生。抢救是抢救。」"
    "回去的路上，刘蕾没说话。"
    "走到小区门口，她忽然说："
    ll "「他说得对。」"
    xz "「那我们去市一。」"
    ll "「市一排队。」"
    xz "「排队就排队。」"
    ll "「排队要请一天假，一天三百。」"
    xz "「三百就三百。」"
    ll "「你一个月挣七千。」"
    xz "「七千也够。」"
    "她看着他，看了很久。"
    ll "「祥子，你不懂。」"
    xz "「我不懂什么？」"
    ll "「我不是舍不得三百。」"
    ll "「我是舍不得那个'排队'。」"
    ll "「排队一天，我一个人坐在走廊里，看着别人的老公陪着老婆。」"
    ll "「我不想一个人。」"
    "祥子站在那儿，说不出话。"
    "那天晚上，他答应她，下次一定陪她去市一。"
    "下次是十二月二十号。"
    "十二月二十号，她的血压是一百六十八，一百一十。"
    "她没有去市一。"
    "他坐在走廊的沙发上，看着墙上的宣传画。画上是一个笑着的孕妇，旁边写着“尊享孕育，幸福一生”。"
    "沙发很软。他坐了一会儿，睡着了。"
    scene bg_station
    with fade
    play music "audio/bgm/station_room.ogg" fadein 1.5
    "九月八号，那篇写骑手的文章出来了。"
    "祥子是在群里看到的，标题很长：《外卖骑手，困在系统里》。"
    "他没看完。里面写的东西，他大部分都知道：超时、罚款、逆行、电梯、算法。他奇怪的是，这些事怎么忽然有人写了，还有那么多人转发。"
    "第二天，平台宣布：给骑手留出八分钟弹性时间。"
    "站点开会。王站长回来了，瘦了一圈，站在白板前。"
    wz "「从今天起，超时不罚款了。」"
    "屋里一片欢呼。"
    wz "「改成扣服务分。一分等于十块钱，扣满二十分，停单一天。」"
    qun "「那不还是一样？」"
    wz "「不一样。以前是罚钱，现在是扣分。罚钱你还有钱，扣分你连单都没有。」"
    "祥子举手。"
    show xz normal at sprite_left
    with dissolve
    xz "「站长，那八分钟，是给我们的？」"
    wz "「是给顾客的。」"
    xz "「什么意思？」"
    wz "「意思是，系统会把时间放宽八分钟，但是顾客看到的时间不变。你迟到八分钟，顾客还是觉得你迟到。」"
    xz "「那这八分钟……」"
    wz "「这八分钟是给你喘气的，不是给你迟到的。」"
    scene bg_road
    with fade
    play music "audio/bgm/city_day.ogg" fadein 1.5
    "单量在涨，骑手也在涨。"
    "站点从四十多人涨到七十多人。新来的大多是厂里出来的，有的连电动车都不会骑，第一天就摔。"
    "单价从四块八降到四块五。王站长说，这是“公司统一调整”。"
    "祥子算了一下。他跑一千单，少三百。"
    "刘蕾的肚子越来越大。她还在上班，走路的时候一手扶着腰，一手扶着桌子。"
    "有一天晚上，她坐在床边脱袜子，脱了半天脱不下来。"
    show ll sick at sprite_left
    with dissolve
    ll "「祥子，帮我一下。」"
    "他蹲下去，把袜子从她脚上褪下来。她的脚肿了，脚踝粗得像馒头，按下去一个坑，半天不起来。"
    show xz normal at sprite_right
    with dissolve
    xz "「去医院看看吧。」"
    ll "「产检刚去过。医生说正常，孕晚期都肿。」"
    show xz tired
    with dissolve
    xz "「你血压多少？」"
    ll "「一百四。」"
    xz "「一百四还不高？」"
    ll "「怀孕都高。」"
    scene bg_hospital
    with fade
    play music "audio/bgm/hospital_night.ogg" fadein 1.5
    "十二月二十号，产检。"
    "私立医院的医生量了三次血压，脸色变了。"
    doc "「一百六十八，一百一十。你这个不行，得住院。」"
    show ll sick at sprite_left
    with dissolve
    ll "「住多久？」"
    doc "「住到生。」"
    ll "「那要住一个月？多少钱？」"
    doc "「押金一万。」"
    ll "「……」"
    doc "「你这个是重度子痫前期，不能拖。拖下去会抽，会脑出血，孩子也保不住。」"
    ll "「我回去商量一下。」"
    "医生看着她，叹了口气。"
    doc "「刘女士，我不是吓你。你今天不住，明天可能就来不了了。」"
    scene bg_room
    with fade
    play music "audio/bgm/room_night.ogg" fadein 1.5
    "回家的路上，刘蕾一句话没说。"
    "到了家，她坐在床上，把包里的检查单一张一张摊开。"
    show ll sick at sprite_left
    with dissolve
    ll "「住院押金一万，生的时候还要一万，孩子早产还要钱。」"
    show xz normal at sprite_right
    with dissolve
    xz "「钱我来想。」"
    ll "「你怎么想？你一个月七千，房贷没有，房租一千，我们欠着四万。」"
    xz "「我去借。」"
    ll "「跟谁借？我爸？他有三万八的彩礼压着，你去要，他能给你？」"
    xz "「……」"
    ll "「祥子，我不是不想住。我是想省下这一万，留给孩子。」"
    "她把手放在肚子上。肚子很大，皮肤绷得发亮，上面有一条一条的紫纹。"
    ll "「我这辈子，什么都没攒下。就攒了这六万。我想给孩子留点。」"
    "祥子蹲在她面前，握住她的手。"
    xz "「明天我们去市一。住院。」"
    ll "「明天站里开会。」"
    xz "「会不开了。」"
    ll "「祥子，你不懂。这个站，下个月就要定承包权。我要是不在，我爸一个人争不过王建平。」"
    xz "「一个站，比你的命重要？」"
    ll "「比我的命重要。」她看着他，「也比你的命重要。你懂不懂？」"
    "他不懂。他当时真的不懂。"
    scene bg_room
    with fade
    play music "audio/bgm/room_night.ogg" fadein 1.5
    "夜里两点，她醒了。"
    "她推了推他。"
    show ll sick at sprite_left
    with dissolve
    ll "「祥子。」"
    show xz normal at sprite_right
    with dissolve
    xz "「嗯？」"
    ll "「我头疼。」"
    xz "「厉害吗？」"
    ll "「有点。眼睛也花，看东西有黑点。」"
    "祥子坐起来，摸她的额头。不烫。"
    xz "「去医院。」"
    ll "「现在？大半夜的。」"
    xz "「去医院。」"
    ll "「我躺一会儿就好。明天早上，你送我去。」"
    scene bg_room
    with fade
    play music "audio/bgm/room_night.ogg" fadein 1.5
    "她没有马上睡。"
    "她侧躺着，看着窗帘。"
    show ll sick at sprite_left
    with dissolve
    ll "「祥子。」"
    show xz normal at sprite_right
    with dissolve
    xz "「嗯。」"
    ll "「你说，孩子生下来，像谁好？」"
    xz "「像你。」"
    ll "「像我不好。我丑。」"
    xz "「不丑。」"
    ll "「你嘴上说。你心里嫌我胖。」"
    "祥子没笑。她也没笑。"
    "过了一会儿，她说："
    ll "「像你吧。」"
    ll "「像你，能吃苦。」"
    ll "「不过这世道，能吃苦不是好事。」"
    "她把手放在肚子上。"
    ll "「我这辈子，没做过什么坏事。」"
    ll "「就是脾气不好，爱骂人。」"
    ll "「你说，我这样的人，能不能上天堂？」"
    "祥子不知道该怎么答。"
    xz "「能。」"
    ll "「你骗我。」"
    xz "「我不骗你。」"
    ll "「那你发誓。」"
    xz "「我发誓。」"
    "她笑了一下。"
    ll "「行了，睡觉。」"
    ll "「明天还要上班。」"
    "她翻了个身，背对着他。"
    "祥子坐在黑暗里，听着她的呼吸。呼吸很重，一下一下，像拉风箱。"
    "他想起医生说的“会抽，会脑出血”。"
    "他伸手去拿手机，想打 120。"
    "手机屏幕亮了，上面弹出一条消息：{b}您有一笔新订单，请在 32 分钟内送达。{/b}"
    "他看着那行字，手指停在半空。"

    $ track("chapter_complete", chapter="ch11")
    jump ch12
    return
