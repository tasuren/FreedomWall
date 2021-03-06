r""" 
  ______                 _                 
 |  ____|               | |                
 | |__ _ __ ___  ___  __| | ___  _ __ ___  
 |  __| '__/ _ \/ _ \/ _` |/ _ \| '_ ` _ \ 
 | |  | | |  __/  __/ (_| | (_) | | | | | |
 |_|  |_|  \___|\___|\__,_|\___/|_| |_| |_|
 \ \        / /  | | |                     
  \ \  /\  / /_ _| | |                     
   \ \/  \/ / _` | | |      by tasuren
    \  /\  / (_| | | |                     
     \/  \/ \__,_|_|_|                     
"""


from util.win32 import GetActiveWindow,GetWindowRect,setClickthrough,GetWindow
from util.tasktray import TaskTray
from util.player import TkPlayer

from tkinter import Tk,ttk,Canvas,BOTH,NW
from threading import Thread
from json import load,dump



class Wallcord():
    def __init__(self,root):
        self.root = root

        with open("data.json","r") as f:
            self.data = load(f)

        self.targets = list(self.data["windows"].keys())

        self.window_title = "FredomWall"
        self.window_show = False
        self.version = "1.2.1"

        # 壁紙を映すためのクラスのインスタンス化。
        self.video = TkPlayer("")
        self.now_window = ""
        self.onoff = True
        # 表示中の壁紙のパス。
        self.now = {
            "path"     : "",
            "alpha"    : 0,
            "exception": []
        }
        # メインスレッドで実行したい関数をタスクトレイから入れるためのリスト。
        # ループで存在確認して実行する。
        self.q = []

        self.create_window()

        self.video_player()
        self.discord_and_open()

    # ウィンドウセッティング。
    def create_window(self):
        # ウィンドウタイトルを設定する。
        self.root.title(self.window_title)
        # ウィンドウタイトルバーを非表示にする。
        # self.debugがTrueの場合わかるように非表示にしない。
        self.root.overrideredirect(1)
        # 最小ウィンドウサイズを設定する。
        self.root.minsize(width=10,height=10)
        self.width,self.height = 10,10

        # 白色は透明化にする。
        self.root.wm_attributes("-transparentcolor","white")
        # 全体的に薄く表示する。
        self.root.attributes("-alpha",0.1)
        # 動画再生部分の表示。
        self.canvas = Canvas(self.root,width=5,height=5)
        self.canvas.pack(expand=True,fill=BOTH)

        # タイトルバー非表示にする。
        root.overrideredirect(1)

        # クリック無効にする。
        self.root.update()
        setClickthrough(int(root.frame(),16))

        # アイコンを設定する。
        self.root.iconbitmap(default="icon.ico")

        # ウィンドウを非表示状態にする。
        self.root.withdraw()
        self.root.attributes("-topmost",False)

        # 終了時は終了するか聞く。
        root.protocol("WM_DELETE_WINDOW",lambda: root.destroy() if messagebox.askokcancel("FreedomWall","壁紙の設定を終了しますか？") else print())


    # データリロード。
    def reload(self):
        with open("data.json","r") as f:
            self.data = load(f)
        self.targets = list(self.data["windows"].keys())

    # 壁紙再生と設定画面実行のループ。
    def video_player(self):

        # 設定などのタスクトレイから実行するやつをメインスレッドで実行するためのもの。
        # Tkinterのメソッドはメインスレッドからじゃないと実行できないためキューに追加してここで実行する。
        if self.q:
            for q in self.q:
                q()
                self.q.pop(0)

        # 壁紙再生。
        # 未設定じゃない時のみ実行する。
        if self.now != {"path":"","alpha":0,"exception":[]} and self.onoff:
            # 他のウィンドウになったらそのウィンドウの壁紙に変更
            if self.now["path"] != self.video.path:
                self.video = TkPlayer(self.now["path"])

            # ターゲットのウィンドウが表示されている時だけ実行する。
            if self.window_show:
                # 描画はutil/player.pyに主要コードがある。
                self.image = self.video.get_frame(self.height,self.width)
                if self.image:
                    self.canvas.create_image(0,0,image=self.image,anchor=NW)

        self.root.after(int(1/self.video.fps*100) if self.video else 10,self.video_player)

    # Discord開くときだけウィンドウを表示するためのループ。
    def discord_and_open(self):
        # ONのときだけ
        if self.onoff:

            handle,window_name = GetActiveWindow()
            if handle != 0:

                # 対象が空の場合無視する。
                if self.targets:
                    
                    for target in self.targets:
                        # パスと透明度をだす。
                        data = self.data["windows"][target]

                        # `target in window_name`は壁紙設定ウィンドウかどうか調べるもの。
                        # `any(not e in window_name for e in data["exception"])`は例外ウィンドウではないか調べる。
                        run = target in window_name and all(not e in window_name for e in data["exception"])
                        if run or self.window_title == window_name:
                            # 壁紙のパスが違うパスだったら新しいパスに更新する。
                            # それと透明度を変更しとく。
                            if self.now != data:
                                self.root.attributes("-alpha",data["alpha"])
                                self.now = data
                                self.now_window = target

                            # もし壁紙ウィンドウを非表示にしているかつ、今壁紙を表示すべきなら、壁紙ウィンドウを表示する。
                            if not self.window_show and run:
                                self.root.deiconify()
                                self.window_show = True
                                self.root.attributes("-topmost",True)

                            # もし検知したアクティブウィンドウが壁紙ウィンドウじゃないならウィンドウサイズを適切なのに変更する。
                            if self.window_title != window_name:
                                x0,y0,x1,y1 = GetWindowRect(handle)
                                sa = 0
                                self.width,self.height = x1-x0,y1-y0
                                self.root.geometry(f"{self.width}x{self.height}+{x0-sa}+{y0-sa}")

                            # 他の壁紙とかぶった際にチカチカ防止のため壁紙のセットは一回きりにする。
                            break

                        else:
                            # 違うウィンドウになったから壁紙のパスを空にする。
                            self.now = {
                                "path"     : "",
                                "alpha"    : 0,
                                "exception": []
                            }

                    # もし違うウィンドウになって壁紙のパスが空じゃないならウィンドウを非表示にする。
                    if self.window_show and self.now == {"path":"","alpha":0,"exception":[]}:
                        self.root.withdraw()
                        self.window_show = False
                        self.root.attributes("-topmost",False)

                # ターゲットがない際は実行しないようにする。
                if not self.window_show:
                    self.now = {
                        "path"     : "",
                        "alpha"    : 0,
                        "exception": []
                    }

        self.root.after(10,self.discord_and_open)



root = Tk()
wallcord = Wallcord(root)
tasktray = TaskTray(wallcord)
    

# タスクトレイは別スレッドにて実行する。
Thread(target=lambda:tasktray.run()).start()
root.mainloop()
