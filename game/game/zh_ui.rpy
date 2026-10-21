# 中文界面与主菜单

## 内置界面文案汉化
translate None strings:
    old "Start"
    new "开始"
    old "Load"
    new "读取"
    old "Save"
    new "保存"
    old "Preferences"
    new "设置"
    old "About"
    new "关于"
    old "Help"
    new "帮助"
    old "Quit"
    new "退出"
    old "History"
    new "历史"

    old "Chapters"
    new "章节目录"
    old "Skip"
    new "快进"
    old "Auto"
    new "自动"
    old "Q.Save"
    new "快存"
    old "Q.Load"
    new "快读"
    old "Back"
    new "回退"
    old "Main Menu"
    new "返回标题"
    old "Return"
    new "继续"
    old "Yes"
    new "是"
    old "No"
    new "否"
    old "Are you sure?"
    new "确定吗？"
    old "Are you sure you want to delete this save?"
    new "确定删除这个存档？"
    old "Are you sure you want to overwrite your save?"
    new "确定覆盖这个存档？"
    old "Loading will lose unsaved progress.\nAre you sure you want to do this?"
    new "读取存档会丢失当前未保存的进度。\n确定继续？"
    old "Are you sure you want to quit?"
    new "确定退出游戏？"
    old "Are you sure you want to return to the main menu?\nThis will lose unsaved progress."
    new "确定返回标题画面？\n未保存的进度会丢失。"
    old "Page {}"
    new "第 {} 页"
    old "Automatic saves"
    new "自动存档"
    old "Quick saves"
    new "快速存档"
    old "Display"
    new "显示"
    old "Window"
    new "窗口"
    old "Fullscreen"
    new "全屏"
    old "Rollback Side"
    new "回退侧"
    old "Disable"
    new "关闭"
    old "Left"
    new "左"
    old "Right"
    new "右"
    old "Unseen Text"
    new "未读文本"
    old "After Choices"
    new "选项之后"
    old "Transitions"
    new "转场"
    old "Text Speed"
    new "文字速度"
    old "Auto-Forward Time"
    new "自动前进间隔"
    old "Music Volume"
    new "音乐音量"
    old "Sound Volume"
    new "音效音量"
    old "Voice Volume"
    new "语音音量"
    old "Mute All"
    new "全部静音"
    old "Test"
    new "试听"
    old "Language"
    new "语言"
    old "The dialogue history is empty."
    new "还没有对白记录。"
    old "Entering the main menu."
    new "已返回标题。"
    old "Skip Mode"
    new "快进中"
    old "This save was created with a different version of the game."
    new "这个存档来自另一个版本的游戏。"
    old "empty slot"
    new "空存档"
    old "Upload Sync"
    new "上传同步"
    old "Download Sync"
    new "下载同步"
    old "Prefs"
    new "设置"
    old "Sync"
    new "同步"
    old "Version [config.version!t]\n"
    new "版本 [config.version!t]\n"
    old "Made with {a=https://www.renpy.org/}Ren'Py{/a} [renpy.version_only].\n\n[renpy.license!t]"
    new "使用 {a=https://www.renpy.org/}Ren'Py{/a} [renpy.version_only] 制作。\n\n[renpy.license!t]"

## 主菜单：左侧竖排，标题压在暗部
screen main_menu():
    tag menu

    add "images/cg/title.jpg"

    # 左侧渐隐压暗，保证文字可读
    add "gui/menu_fade.png"

    vbox:
        xpos 96
        ypos 118
        spacing 6
        text "超时":
            font "NotoSerifSC-Regular.otf"
            size 92
            color "#E8E4DC"
        text "一个骑手的五年　2018—2023":
            font "NotoSansSC-Regular.otf"
            size 20
            color "#C79A4B"
        null height 46
        textbutton "开始" action Start() style "main_menu_textbutton"
        textbutton "章节目录" action ShowMenu("chapter_list") style "main_menu_textbutton"
        textbutton "读取" action ShowMenu("load") style "main_menu_textbutton"
        textbutton "设置" action ShowMenu("preferences") style "main_menu_textbutton"
        textbutton "关于" action ShowMenu("about") style "main_menu_textbutton"
        textbutton "退出" action Quit(confirm=False) style "main_menu_textbutton"

    text "杭州 · 2018—2023":
        xalign 0.98
        yalign 0.965
        font "NotoSansSC-Regular.otf"
        size 15
        color "#8A8F96"

style main_menu_textbutton:
    font "NotoSerifSC-Regular.otf"
    size 30
    color "#B9B4AA"
    hover_color "#F2EDE4"
    selected_color "#C79A4B"
    insensitive_color "#5A5C60"

style main_menu_textbutton_text is main_menu_textbutton
