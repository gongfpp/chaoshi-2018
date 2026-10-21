# 由 tools/gen_game.py 自动生成，请勿手改。

define CHAPTERS = [
    ("ch01", "第一章", "三月雨", "2018.03"),
    ("ch02", "第二章", "单王", "2018.04"),
    ("ch03", "第三章", "调度室", "2018.07"),
    ("ch04", "第四章", "自己的车", "2018.08"),
    ("ch05", "第五章", "四十五天", "2018.10"),
    ("ch06", "第六章", "老马的车", "2018.12"),
    ("ch07", "第七章", "新国标", "2019.05"),
    ("ch08", "第八章", "彩礼", "2019.06"),
    ("ch09", "第九章", "喜酒", "2019.10"),
    ("ch10", "第十章", "封城", "2020.02"),
    ("ch11", "第十一章", "建档", "2020.08"),
    ("ch12", "第十二章", "一月十八", "2021.01"),
    ("ch13", "第十三章", "卖车", "2021.03"),
    ("ch14", "第十四章", "小福", "2021.06"),
    ("ch15", "第十五章", "服务分", "2021.09"),
    ("ch16", "第十六章", "三月十二", "2021.12"),
    ("ch17", "第十七章", "念念", "2022.06"),
    ("ch18", "第十八章", "群", "2022.11"),
    ("ch19", "第十九章", "交易", "2023.03"),
    ("ch20", "第二十章", "守夜", "2023.12"),
]

label ch01_entry:
    $ qian = 0
    $ debt = 0
    $ c_call = False
    $ c_haodan = False
    $ c_siyu = True
    $ c_gongzi = False
    $ c_zaodao = False
    $ xf_saved = False
    $ sold_chen = False
    $ visited = False
    $ track("chapter_jump", chapter="ch01")
    jump ch01

label ch02_entry:
    $ qian = 0
    $ debt = 2000
    $ c_call = False
    $ c_haodan = False
    $ c_siyu = True
    $ c_gongzi = False
    $ c_zaodao = False
    $ xf_saved = False
    $ sold_chen = False
    $ visited = False
    $ track("chapter_jump", chapter="ch02")
    jump ch02

label ch03_entry:
    $ qian = 14052
    $ debt = 0
    $ c_call = False
    $ c_haodan = False
    $ c_siyu = True
    $ c_gongzi = False
    $ c_zaodao = False
    $ xf_saved = False
    $ sold_chen = False
    $ visited = False
    $ track("chapter_jump", chapter="ch03")
    jump ch03

label ch04_entry:
    $ qian = 14052
    $ debt = 0
    $ c_call = False
    $ c_haodan = False
    $ c_siyu = True
    $ c_gongzi = False
    $ c_zaodao = False
    $ xf_saved = False
    $ sold_chen = False
    $ visited = False
    $ track("chapter_jump", chapter="ch04")
    jump ch04

label ch05_entry:
    $ qian = 3436
    $ debt = 0
    $ c_call = False
    $ c_haodan = False
    $ c_siyu = True
    $ c_gongzi = False
    $ c_zaodao = False
    $ xf_saved = False
    $ sold_chen = False
    $ visited = False
    $ track("chapter_jump", chapter="ch05")
    jump ch05

label ch06_entry:
    $ qian = 9372
    $ debt = 0
    $ c_call = False
    $ c_haodan = False
    $ c_siyu = True
    $ c_gongzi = False
    $ c_zaodao = False
    $ xf_saved = False
    $ sold_chen = False
    $ visited = False
    $ track("chapter_jump", chapter="ch06")
    jump ch06

label ch07_entry:
    $ qian = 19836
    $ debt = 0
    $ c_call = False
    $ c_haodan = False
    $ c_siyu = True
    $ c_gongzi = False
    $ c_zaodao = False
    $ xf_saved = False
    $ sold_chen = False
    $ visited = False
    $ track("chapter_jump", chapter="ch07")
    jump ch07

label ch08_entry:
    $ qian = 10421
    $ debt = 8000
    $ c_call = False
    $ c_haodan = False
    $ c_siyu = True
    $ c_gongzi = False
    $ c_zaodao = False
    $ xf_saved = False
    $ sold_chen = False
    $ visited = False
    $ track("chapter_jump", chapter="ch08")
    jump ch08

label ch09_entry:
    $ qian = 21205
    $ debt = 0
    $ c_call = False
    $ c_haodan = False
    $ c_siyu = True
    $ c_gongzi = False
    $ c_zaodao = False
    $ xf_saved = False
    $ sold_chen = False
    $ visited = False
    $ track("chapter_jump", chapter="ch09")
    jump ch09

label ch10_entry:
    $ qian = 8449
    $ debt = 14000
    $ c_call = False
    $ c_haodan = False
    $ c_siyu = True
    $ c_gongzi = False
    $ c_zaodao = False
    $ xf_saved = False
    $ sold_chen = False
    $ visited = False
    $ track("chapter_jump", chapter="ch10")
    jump ch10

label ch11_entry:
    $ qian = 5800
    $ debt = 14000
    $ c_call = False
    $ c_haodan = False
    $ c_siyu = True
    $ c_gongzi = False
    $ c_zaodao = False
    $ xf_saved = False
    $ sold_chen = False
    $ visited = False
    $ track("chapter_jump", chapter="ch11")
    jump ch11

label ch12_entry:
    $ qian = 4800
    $ debt = 14000
    $ c_call = False
    $ c_haodan = False
    $ c_siyu = True
    $ c_gongzi = False
    $ c_zaodao = False
    $ xf_saved = False
    $ sold_chen = False
    $ visited = False
    $ track("chapter_jump", chapter="ch12")
    jump ch12

label ch13_entry:
    $ qian = 4306
    $ debt = 85000
    $ c_call = False
    $ c_haodan = False
    $ c_siyu = True
    $ c_gongzi = False
    $ c_zaodao = False
    $ xf_saved = False
    $ sold_chen = False
    $ visited = False
    $ track("chapter_jump", chapter="ch13")
    jump ch13

label ch14_entry:
    $ qian = 4306
    $ debt = 85000
    $ c_call = False
    $ c_haodan = False
    $ c_siyu = True
    $ c_gongzi = False
    $ c_zaodao = False
    $ xf_saved = False
    $ sold_chen = False
    $ visited = False
    $ track("chapter_jump", chapter="ch14")
    jump ch14

label ch15_entry:
    $ qian = 3006
    $ debt = 70000
    $ c_call = False
    $ c_haodan = False
    $ c_siyu = True
    $ c_gongzi = False
    $ c_zaodao = False
    $ xf_saved = False
    $ sold_chen = False
    $ visited = False
    $ track("chapter_jump", chapter="ch15")
    jump ch15

label ch16_entry:
    $ qian = 2006
    $ debt = 40000
    $ c_call = False
    $ c_haodan = False
    $ c_siyu = True
    $ c_gongzi = False
    $ c_zaodao = False
    $ xf_saved = False
    $ sold_chen = False
    $ visited = False
    $ track("chapter_jump", chapter="ch16")
    jump ch16

label ch17_entry:
    $ qian = 1206
    $ debt = 30000
    $ c_call = False
    $ c_haodan = False
    $ c_siyu = True
    $ c_gongzi = False
    $ c_zaodao = False
    $ xf_saved = False
    $ sold_chen = False
    $ visited = False
    $ track("chapter_jump", chapter="ch17")
    jump ch17

label ch18_entry:
    $ qian = 806
    $ debt = 28000
    $ c_call = False
    $ c_haodan = False
    $ c_siyu = True
    $ c_gongzi = False
    $ c_zaodao = False
    $ xf_saved = False
    $ sold_chen = False
    $ visited = False
    $ track("chapter_jump", chapter="ch18")
    jump ch18

label ch19_entry:
    $ qian = 1206
    $ debt = 26000
    $ c_call = False
    $ c_haodan = False
    $ c_siyu = True
    $ c_gongzi = False
    $ c_zaodao = False
    $ xf_saved = False
    $ sold_chen = False
    $ visited = False
    $ track("chapter_jump", chapter="ch19")
    jump ch19

label ch20_entry:
    $ qian = 2866
    $ debt = 22000
    $ c_call = False
    $ c_haodan = False
    $ c_siyu = True
    $ c_gongzi = False
    $ c_zaodao = False
    $ xf_saved = False
    $ sold_chen = False
    $ visited = False
    $ track("chapter_jump", chapter="ch20")
    jump ch20

