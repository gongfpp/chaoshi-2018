# 由 tools/gen_game.py 自动生成，请勿手改。

define narrator = Character(None, what_color="#E8E4DC")
define xz = Character("杨保祥", who_color="#D9C8A6")
define ll = Character("刘蕾", who_color="#C98A62")
define xf = Character("罗小福", who_color="#D6A0AB")
define lt = Character("刘广田", who_color="#A89684")
define lm = Character("马长顺", who_color="#9AA79B")
define cy = Character("曹明远", who_color="#9FB0C4")
define gj = Character("高秀兰", who_color="#BFA98F")
define sg = Character("孙德胜", who_color="#A88F6E")
define wz = Character("王建平", who_color="#B0A693")
define cl = Character("陈立", who_color="#92A8B8")
define rq = Character("罗二强", who_color="#A57F6E")
define bj = Character("杨保芝", who_color="#C0A58F")
define wd = Character("王大勇", who_color="#A99C86")
define qun = Character("骑手", who_color="#A9A69C")
define police = Character("警察", who_color="#9FA5AC")
define nurse = Character("护士", who_color="#A8B4B8")
define doc = Character("医生", who_color="#A8B4B8")
define op = Character("120 接线员", who_color="#9FA5AC")
define staff = Character("工作人员", who_color="#9FA5AC")
define old = Character("老人", who_color="#B3AC9E")
define son = Character("家属", who_color="#B3AC9E")
define car = Character("车主", who_color="#B08C7A")
define qin = Character("亲戚", who_color="#AFA393")
define vol = Character("志愿者", who_color="#A3ADA6")
define guard = Character("保安", who_color="#A3ADA6")
define cust = Character("顾客", who_color="#B0A79A")
define land = Character("房东", who_color="#B0A79A")
define boss = Character("老板", who_color="#AFA08C")
define young = Character("年轻骑手", who_color="#A8B0A0")
define li = Character("小李", who_color="#A8B4A0")
define zhao = Character("老赵", who_color="#A8B4A0")
define new = Character("新司机", who_color="#A8B4A0")
define boy = Character("顾客", who_color="#A8B0A0")
define woman = Character("邻居", who_color="#B3A9A0")
define man = Character("邻居", who_color="#A9A296")
define nn = Character("杨念", who_color="#D8B9B0")
define father = Character("父亲", who_color="#B8AE9C")
define neighbor = Character("邻居", who_color="#A8A79C")
define consult = Character("顾问", who_color="#B9AFA4")
define lawyer = Character("对方律师", who_color="#A2A6AC")
define arb = Character("仲裁员", who_color="#A2A6AC")
define girl = Character("女孩", who_color="#B8AFA4")
define mom = Character("赵桂枝", who_color="#C0A99B")
define wu = Character("老吴", who_color="#A9AFA4")

default qian = 3000
default debt = 0
default shen = 10
default xin = 5
default orders = 0
default c_call = False
default c_haodan = False
default c_siyu = False
default c_gongzi = False
default c_zaodao = False
default xf_saved = False
default sold_chen = False
default xf_saved = False
default sold_chen = True

label start:
    $ quick_menu = True
    jump ch01
