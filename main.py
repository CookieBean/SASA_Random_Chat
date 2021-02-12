# -*- coding: utf-8 -*-

import firebase_admin
from firebase_admin import credentials
from firebase_admin import auth
import tkinter.font as tkFont
from tkinter import messagebox
import pyrebase
import tkinter as tk
import datetime
import json
import unicodedata
import requests
import apikey_sasa as API
import hashlib

encoder = hashlib.md5()

cred = credentials.Certificate("random-chat-sasa-firebase-adminsdk-vnq8o-123e95c3a8.json")

# firebase_admin init (데이터베이스 초기 연결)
firebase_admin.initialize_app(cred, {
    'databaseURL': API.databaseURL
})

# pyrebase init (데이터베이스 초기 연결)
config = API.config

firebase = pyrebase.initialize_app(config)
db = firebase.database()


class person:

    def __init__(self, name, passwd, email):  # person 객체 생성자 (이름, 아이디, 비밀번호)
        self.__name = name
        self.__passwd = passwd
        self.__user = None
        self.__email = email

    def set_user(self, user):  # user setter (유효성 검사)
        if user != None:
            self.__user = user

    def get_user(self):  # user getter
        return self.__user

    def set_passwd(self, passwd):  # pw setter (유효성 검사 필수!)
        print("pass : ", passwd)
        print(len(passwd))
        if len(passwd) >= 8:
            self.__passwd = passwd
            return True
        else:
            return False

    def set_name(self, name):  # name setter
        self.__name = name

    def get_passwd(self):  # pw getter
        return self.__passwd

    def get_name(self):  # name getter
        return self.__name

    def set_email(self, email):
        self.__email = email

    def get_email(self):
        return self.__email

    def send_email_verification_link(self):
        payload = json.dumps({
            "email": self.get_user().email,
            "password": self.get_passwd(),
            "returnSecureToken": True
        })

        r = requests.post(API.signin_url,
                          params={"key": config["apiKey"]},
                          data=payload)
        print(r.json())
        idToken = r.json()["idToken"]

        payload = json.dumps({
            "requestType": "VERIFY_EMAIL",
            "idToken": idToken
        })

        r = requests.post(API.verify_url,
                          params={"key": config["apiKey"]},
                          data=payload)

        return r.json()

    def sign_up(self):  # person의 기초적 signup 메서드 (유저 생성 및 데이터베이스 저장)
        try:
            if self.__email[-10:] != "sasa.hs.kr":
                messagebox.showerror("Error", "This Email is not SASA email. Please enter another email.")
                return False
            user = auth.create_user(
                email=self.__email,
                email_verified=False,
                password=self.__passwd,
                display_name=self.__name,
                disabled=False)
            self.__user = user
            DB = firebase.database()
            DB.child("user").child(user.uid).set({"uid": self.get_user().uid,
                                                  "pw": self.get_passwd(),
                                                  "email_verified": False,
                                                  "name": self.get_name(),
                                                  "email": self.get_email()})
            print(self.send_email_verification_link())
            print('Sucessfully created new user: {0}'.format(user.uid))
            return True
        except Exception as e:  # 예외처리
            print(e)
            print("This ID was Already used. Try Again with another ID")
            return False

    def sign_in(self):  # person의 기초적 signin 메서드 (유저 가져오기 및 데이터베이스 내 데이터 가져오기)
        a = firebase.auth()
        try:
            print(self.__email, self.__passwd)
            a.sign_in_with_email_and_password(self.__email, self.__passwd)
            print(a)
            self.__user = auth.get_user_by_email(self.__email)
            if not self.__user.email_verified:
                messagebox.showerror("Error", "Email was not verified! Please verify your Email first!")
                return False
            self.update_value()
            return True
        except Exception as e:  # 예외처리 (ID or Password 유효하지 않을때)
            print(e)
            print("ID or Password Invalid!")
            return False

    def update_value(self):  # 유저 데이터 변경시 업데이트하는 메서드 (Auth 변경 및 데이터베이스 내 데이터 수정)
        self.set_user(auth.update_user(
            self.get_user().uid,
            email=self.__email,
            email_verified=self.get_user().email_verified,
            password=self.__passwd,
            display_name=self.get_user().display_name,
            disabled=self.get_user().disabled))
        DB = firebase.database()
        DB.child("user").child(self.get_user().uid).update({"uid": self.get_user().uid,
                                                            "pw": self.get_passwd(),
                                                            "email_verified": self.get_user().email_verified,
                                                            "name": self.get_name(),
                                                            "email": self.get_email()})
        print('Sucessfully updated user: {0}'.format(self.get_user().uid))


class student(person):  # person을 상속한 student객체

    def __init__(self, name="", grade="", passwd="", email="",
                 banned=False):  # student객체 생성자 (이름, 학년, 아이디, 비밀번호, 차단여부) + Overriding
        super().__init__(name, passwd, email)
        self.__grade = grade
        self.__baned = banned

    def sign_up(self):  # person에서 정의된 signup 메서드를 재정의 (Overriding)
        flag = super().sign_up()
        if flag:
            db.child("user").child(self.get_user().uid).update({"banned": self.__baned,
                                                                "grade": self.__grade})
        return flag

    def sign_in(self):  # person에서 정의된 signin 메서드를 재정의 (Overriding)
        flag = super().sign_in()
        if flag:
            print(self.get_user().uid)
            data = db.child("user").child(self.get_user().uid).get().val()
            self.set_name(data['name'])
            self.__grade = data['grade']
            return not data['banned']
        else:
            return False

    def get_grade(self):  # grade getter
        return self.__grade

    def get_banned(self):  # banned getter
        return self.__baned

    def set_banned(self, x):  # banned setter (유효성 검사)
        if type(x) is bool:
            self.__baned = x

    def update_value(self):  # person에서 정의된 update 메서드를 재정의 (Overriding)
        super().update_value()
        DB = firebase.database()
        DB.child("user").child(self.get_user().uid).update({"banned": self.get_banned(),
                                                            "grade": self.get_grade()})


class teacher(person):  # person을 상속한 teacher객체

    def __init__(self, name="", id="", passwd="", email=""):  # teacher객체 생성자 (이름, 아이디, 비밀번호) + Overriding
        super().__init__(name, passwd, email)
        self.__ban_cnt = 0

    def sign_in(self):  # person에서 정의된 signin 메서드를 재정의 (Overriding)
        flag = super().sign_in()
        if flag:
            data = db.child("user").child(self.get_user().uid).get().val()
            self.set_name(data['name'])
        return flag

    def ban(self, ban_user_uid):  # 특정 사용자 차단 메서드
        try:
            DB = firebase.database()
            DB.child("user").child(ban_user_uid).update({"banned": True})
            self.__ban_cnt += 1
            self.update_value()
            return True
        except Exception as e:  # 예외처리
            print(e)
            return False

    def get_ban_cnt(self):  # ban_cnt getter
        return self.__ban_cnt

    def update_value(self):  # person에서 정의된 update 메서드를 재정의 (Overriding)
        super().update_value()
        DB = firebase.database()
        DB.child("user").child(self.get_user().uid).update({"ban_cnt": self.__ban_cnt})


class BaseFrame(tk.Tk):  # tk.TK를 상속받은 BaseFrame객체

    def __init__(self, *args, **kwargs):
        global Font
        tk.Tk.__init__(self, *args, **kwargs)  # tk init
        self.container = tk.Frame(self)
        Font = tkFont.Font(family="AppleGothic")  # Font 설정
        self.container.pack(side="top", fill="both", expand=True)

        self.container.grid_rowconfigure(0, weight=1)
        self.container.grid_columnconfigure(0, weight=1)

        self.frames = {}  # 프레임 초기화

        # 각 페이지 초기화
        self.ListPage_frame_init(student())
        self.LoginPage_frame_init(student())
        self.WaitPage_frame_init(student())
        self.ChatPage_frame_init(student(), "")
        self.ManagePage_frame_init(student())
        self.ProfilePage_frame_init(student())

        # 초기 페이지 LoginPage 보이기
        self.show_frame(LoginPage)

    def ListPage_frame_init(self, account):  # ListPage 초기화
        frame = ListPage(self.container, self, account)

        self.frames[ListPage] = frame

        frame.grid(row=0, column=0, sticky="nsew")

    def LoginPage_frame_init(self, account):  # LoginPage 초기화
        frame = LoginPage(self.container, self, account)

        self.frames[LoginPage] = frame

        frame.grid(row=0, column=0, sticky="nsew")

    def WaitPage_frame_init(self, account):  # WaitPage 초기화
        frame = WaitPage(self.container, self, account)

        self.frames[WaitPage] = frame

        frame.grid(row=0, column=0, sticky="nsew")

    def ChatPage_frame_init(self, account, roomname):  # ChatPage 초기화
        frame = ChatPage(self.container, self, account, roomname)

        self.frames[ChatPage] = frame

        frame.grid(row=0, column=0, sticky="nsew")

    def ManagePage_frame_init(self, account):  # ManagePage 초기화
        frame = ManagePage(self.container, self, account)

        self.frames[ManagePage] = frame

        frame.grid(row=0, column=0, sticky="nsew")

    def ProfilePage_frame_init(self, account):  # ProfilePage 초기화
        frame = ProfilePage(self.container, self, account)

        self.frames[ProfilePage] = frame

        frame.grid(row=0, column=0, sticky="nsew")

    def show_frame(self, cont):  # Frame 보여주기 (페이지 전환)
        frame = self.frames[cont]
        frame.tkraise()


class LoginPage(tk.Frame):  # tk.Frame객체를 상속받은 LoginPage객체

    def __init__(self, parent, controller, account):  # LoginPage객체 생성자
        tk.Frame.__init__(self, parent)

        label = tk.Label(self, text="Login Page", bg='#3E4149', fg="#FFFFFF")
        label.pack(pady=10, padx=10)
        self.configure(bg="#3E4149")

        label1 = tk.Label(self, text="Name(Sign up)", bg='#3E4149', fg="#FFFFFF")
        label1.pack(pady=20, padx=20)

        self.name = tk.Entry(self, width=20)  # 이름 입력
        self.name.pack()

        label2 = tk.Label(self, text="Grade(Sign up)", bg='#3E4149', fg="#FFFFFF")
        label2.pack(pady=20, padx=20)

        self.grade = tk.Entry(self, width=20)  # 학년 입력
        self.grade.pack()

        label5 = tk.Label(self, text="SASA Email", bg='#3E4149', fg="#FFFFFF")
        label5.pack(pady=20, padx=20)

        self.email = tk.Entry(self, width=20)  # 이메일 입력
        self.email.pack()

        label4 = tk.Label(self, text="Password", bg='#3E4149', fg="#FFFFFF")
        label4.pack(pady=20, padx=20)

        self.pw = tk.Entry(self, width=20, show='*')  # 비밀번호 입력
        self.pw.pack()

        label6 = tk.Label(self, text="Teacher Password(Optional)", bg='#3E4149', fg="#FFFFFF")
        label6.pack(pady=20, padx=20)

        self.tpw = tk.Entry(self, width=20)  # 관리자 비밀번호 입력
        self.tpw.pack()

        button = tk.Button(self, text="Sign up",
                           command=lambda: self.signup_action(controller), highlightbackground='#3E4149')  # Sign up 버튼
        button.pack(pady=10)

        button2 = tk.Button(self, text="Sign in",
                            command=lambda: self.signin_action(controller), highlightbackground='#3E4149')  # Sign in 버튼
        button2.pack()

    def signup_action(self, controller):  # 가입 Method
        tpw = self.tpw.get()
        if tpw == "SASA_":  # 관리자 유효 검사
            account = teacher(self.name.get())
        else:
            account = student(self.name.get(), self.grade.get())
        account.set_email(self.email.get())
        password = hashlib.md5(self.pw.get().encode('utf-8')).hexdigest()
        if not account.set_passwd(password):  # 비밀번호 유효성 검사
            messagebox.showerror("Error", "PassWord must be longer than 8")
        else:
            flag = account.sign_up()
            if flag:  # 가입 성공 여부
                print("Successfully Registered!")
                messagebox.showinfo("Info", "Successfully Registered!\nNow verify your email and  Login Please")
            else:  # 예외처리
                messagebox.showerror("Error", "Cannot Signup! Report this issue to Developer to fix it.")

    def signin_action(self, controller):  # 로그인 Method
        tpw = self.tpw.get()
        if tpw == "SASA_":  # 관리자 유효 검사
            account = teacher(self.name.get())
        else:
            account = student(self.name.get(), self.grade.get())
        account.set_email(self.email.get())
        password = hashlib.md5(self.pw.get().encode('utf-8')).hexdigest()
        if not account.set_passwd(password):  # 비밀번호 유효성 검사
            messagebox.showerror("Error", "PassWord must be longer than 8")
        else:
            flag = account.sign_in()
            if flag:  # 로그인 성공 여부
                print("going to listpage")
                controller.ListPage_frame_init(account)
                controller.show_frame(ListPage)
            else:  # 예외처리
                messagebox.showerror("Error", "Cannot Signin! Check your id or password again!")


class ListPage(tk.Frame):  # tk.Frame객체를 상속한 ListPage객체

    def __init__(self, parent, controller, account):  # ListPage객체 생성자
        tk.Frame.__init__(self, parent)
        label = tk.Label(self, text="Room List", bg='#3E4149', fg="#FFFFFF")
        label.pack(pady=10, padx=10)
        self.configure(bg="#3E4149")

        profile = tk.Button(self, text="Go to the Profile",
                            command=lambda: self.go_profile_action(controller, account),
                            highlightbackground='#3E4149')  # ProfilePage 이동 버튼
        profile.pack()

        refresh = tk.Button(self, text="Refresh",
                            command=self.refresh_list, highlightbackground='#3E4149')  # 리스트 새로고침 버튼
        refresh.pack()

        scrollbar = tk.Scrollbar(self, orient="vertical")
        self.listNodes = tk.Listbox(self, width=50, height=25, yscrollcommand=scrollbar.set)  # 방 목록 리스트
        self.listNodes.pack(padx=10, pady=10)
        self.refresh_list()
        print("printing user uid")

        button1 = tk.Button(self, text="Logout",
                            command=lambda: self.logout_action(controller), highlightbackground='#3E4149')  # 로그아웃 버튼
        button1.pack()

        button3 = tk.Button(self, text="Make A Room",
                            command=lambda: self.wait_action(controller, account),
                            highlightbackground='#3E4149')  # 방 생성 버튼
        button3.pack()

        button2 = tk.Button(self, text="Go!",
                            command=lambda: self.go_action(controller, account),
                            highlightbackground='#3E4149')  # 방 참가 버튼
        button2.pack()

        try:
            account.get_ban_cnt()
            button4 = tk.Button(self, text="Manage Requests",
                                command=lambda: self.request_action(controller, account),
                                highlightbackground='#3E4149')  # 관리자 전용 관리 버튼
            button4.pack()
        except:  # 예외처리 (관리자 아님)
            pass

    def go_profile_action(self, controller, account):  # ProfilePage 이동 메서드
        controller.ProfilePage_frame_init(account)
        controller.show_frame(ProfilePage)

    def request_action(self, controller, account):  # ManagePage 이동 메서드 (관리자 전용)
        controller.ManagePage_frame_init(account)
        controller.show_frame(ManagePage)

    def logout_action(self, controller):  # 로그아웃 메서드
        n_acc = student()
        controller.LoginPage_frame_init(n_acc)
        controller.show_frame(LoginPage)

    def wait_action(self, controller, account):  # 대기 페이지 이동 메서드
        print("waiting")
        print(account.get_user().uid)
        try:
            DB = firebase.database()
            DB.child("room").child(account.get_user().uid).set({"host": account.get_user().uid})  # 데이터베이스에 방 생성
            controller.WaitPage_frame_init(account)
            controller.show_frame(WaitPage)
        except:  # 예외 처리
            print("Set Failed")

    def refresh_list(self):  # 리스트 새로고침 메서드
        room_list = db.child("room").get()
        self.listNodes.delete(0, tk.END)
        cnt = 0
        try:
            for i in room_list.each():
                print(i.val())
                if "client" not in i.val().keys():
                    self.listNodes.insert(cnt, i.val()['host'])
                    cnt += 1
        except:
            print("Not Yet")

    def go_action(self, controller, account):  # 방 참가 + 창 이동 메서드
        host = self.listNodes.get(self.listNodes.curselection()[0])
        pre_hostname = db.child("room").child(host).get().val()['host']
        if pre_hostname != host:
            messagebox.showinfo("Error", "It's not available room!\nPlease refresh the room list!")
            return
        db.child("room").child(host).update({"host": account.get_user().uid})
        db.child("chat").child(host + "+" + account.get_user().uid).set(
            {"chat_count": 1, "exist_": 2})  # 채팅 기본값 데이터베이스에 저장
        db.child("chat").child(host + "+" + account.get_user().uid).child("messages").child(0).set({"number": 0,
                                                                                                    "data": {
                                                                                                        "date": datetime.datetime.now().strftime(
                                                                                                            '%Y-%m-%d %H:%M:%S'),
                                                                                                        "from": "public",
                                                                                                        "message": "----- The Chat Starts -----"}})  # 첫 공식 채팅 데이터베이스에 저장
        controller.ChatPage_frame_init(account, host + "+" + account.get_user().uid)
        controller.show_frame(ChatPage)


class WaitPage(tk.Frame):  # tk.Frame객체를 상속한 WaitPage객체

    def __init__(self, parent, controller, account):  # WaitPage객체 생성자
        tk.Frame.__init__(self, parent)
        label = tk.Label(self, text="You are now waiting for a opponent... It will take a while", bg='#3E4149',
                         fg="#FFFFFF")
        label.pack(pady=10, padx=10)
        self.configure(bg="#3E4149")

        button2 = tk.Button(self, text="Delete Room and Go Back",
                            command=lambda: self.delete_action(controller, account),
                            highlightbackground='#3E4149')  # 방 삭제 및 뒤로가기 버튼
        button2.pack()

        my_stream = db.child('room').stream(
            lambda x: self.stream_handler(x, account, controller))  # 스트림 핸들러 (데이터베이스에서 바뀐 값을 실시간으로 감지)

    def delete_action(self, controller, account):  # 방 삭제 및 뒤로가기 메서드
        db.child('room').child(account.get_user().uid).remove()
        controller.ListPage_frame_init(account)
        controller.show_frame(ListPage)

    def stream_handler(self, message, account, controller):  # 스트림 핸들러 - 이벤트 발생시 호출
        try:
            message = str(message['data']).replace("'", '"')
            message = json.loads(message)
            if message['host'] != account.get_user().uid:  # 호스트 바뀜 == 다른사람이 방에 입장함
                client = db.child('room').child(account.get_user().uid).get()
                client = client.val()['host']
                db.child('room').child(account.get_user().uid).remove()  # 대기목록에서 방 삭제
                messagebox.showinfo("Info", "Opponent Matched Successfully!")
                controller.ChatPage_frame_init(account, account.get_user().uid + "+" + client)
                controller.show_frame(ChatPage)
        except:  # 예외처리
            print("Cannot Remove")


class ChatPage(tk.Frame):  # tk.Frame객체를 상속한 ChatPage

    def __init__(self, parent, controller, account, roomname):  # ChatPage 생성자
        tk.Frame.__init__(self, parent)
        self.configure(bg="#3E4149")

        button2 = tk.Button(self, text="Go Back",
                            command=lambda: self.go_back_action(controller, account, roomname),
                            highlightbackground='#3E4149')  # 뒤로가기 버튼
        button2.pack()

        button3 = tk.Button(self, text="Report Opponent",
                            command=lambda: self.report_action(account, roomname),
                            highlightbackground='#3E4149')  # 상대 신고버튼
        button3.pack()

        my_stream = db.child('chat').child(roomname).child("messages").stream(
            lambda x: self.stream_handler(x, account=account))  # 스트림 핸들러 (데이터베이스에서 바뀐 값을 실시간으로 감지)

        scrollbar = tk.Scrollbar(self, orient="vertical")
        scrollbar.pack(side="left", fill=tk.Y)
        self.listNodes = tk.Listbox(self, width=100, height=20, yscrollcommand=scrollbar.set, font=Font)  # 채팅 리스트
        self.listNodes.configure(exportselection=False, yscrollcommand=scrollbar.set)
        self.listNodes.pack(padx=10, pady=10)
        scrollbar.configure(command=self.listNodes.yview)
        chat_list = db.child("chat").child(roomname).child("messages").get()  # 초기 채팅 데이터 가져오기
        try:
            for i in chat_list.each():
                print("i val")
                print(i.val()['data'])
                if i.val()['data']['from'] == account.get_user().uid:  # 내가 보낸 채팅
                    self.listNodes.insert(self.listNodes.size(),
                                          "Me" + " / " + i.val()['data']['date'] + "<<-- " + i.val()['data']['message'])
                elif i.val()['data']['from'] == "public":  # 공식 채팅
                    self.listNodes.insert(self.listNodes.size(), i.val()['data']['message'])
                else:  # 상대가 보낸 채팅
                    self.listNodes.insert(self.listNodes.size(),
                                          "Anonymous" + " / " + i.val()['data']['date'] + "-->> " + i.val()['data'][
                                              'message'])
        except:  # 예외처리
            print("Not Yet")

        self.chat = tk.Entry(self, width=100, font=Font)  # 대화 입력기
        self.chat.pack()
        self.chat.bind("<Return>", lambda x: self.send_chat(account, roomname))

        button1 = tk.Button(self, text="Send",
                            command=lambda: self.send_chat(account, roomname), highlightbackground='#3E4149')  # 전송버튼
        button1.pack()

    def report_action(self, account, roomname):  # 신고 메서드
        DB = firebase.database()
        l = roomname.split("+")
        target = ""
        for i in l:
            if i != account.get_user().uid:
                target = i
        DB.child("request").child(roomname).set({"victim": account.get_user().uid,
                                                 "target": target})  # request에는 신고 대상자와 신고자 uid 목록이 저장됨
        context = DB.child("chat").child(roomname).child("messages").get()  # 채팅 데이터 가져오기
        DB.child("ban_req").child(roomname).set(context.val())  # 신고목록에 채팅데이터 저장

    def stream_handler(self, message, account):  # 스트림 핸들러 - 이벤트 발생시 호출
        print("handled")
        print(message)
        try:
            print(message['data'])
            message = message['data']
            print(message['data'])
            message = message['data']
            print(message)
            if message['from'] == account.get_user().uid:  # 내가 보낸 채팅
                self.listNodes.insert(self.listNodes.size(),
                                      "Me" + " / " + message['date'] + "<<-- " + message['message'])
                print(message['from'] + " / " + message['date'] + "<<-- " + message['message'])
            elif message['from'] == "public":  # 공식 채팅
                self.listNodes.insert(self.listNodes.size(), message['message'])
                print(message['message'])
            else:  # 상대가 보낸 채팅
                self.listNodes.insert(self.listNodes.size(),
                                      "Anonymous" + " / " + message['date'] + "-->> " + message['message'])
                print(message['from'] + " / " + message['date'] + "-->> " + message['message'])
            self.listNodes.selection_clear(0, tk.END)
            self.listNodes.select_set(tk.END)
            self.listNodes.yview(tk.END)
        except Exception as e:  # 예외처리
            print("Not Yet")
            print(e)

    def send_chat(self, account, roomname):  # 채팅 전송 메서드
        if self.chat.get() != "":
            cnt = db.child("chat").child(roomname).get().val()['chat_count']
            m = unicodedata.normalize('NFC', self.chat.get())
            db.child("chat").child(roomname).child("messages").child(cnt).set({"number": cnt,
                                                                               "data": {
                                                                                   "date": datetime.datetime.now().strftime(
                                                                                       '%Y-%m-%d %H:%M:%S'),
                                                                                   "from": account.get_user().uid,
                                                                                   "message": m}})  # 대화 객체 (Dictionary Type) 데이터베이스에 저장
            cnt += 1
            db.child("chat").child(roomname).update({"chat_count": cnt})  # 대화 카운트 증가
            self.chat.delete(0, "end")  # 입력칸 비우기

    def go_back_action(self, controller, account, roomname):  # 뒤로가기 메서드
        exist_ = db.child("chat").child(roomname).get().val()['exist_']
        if exist_ == 2:  # 내가 상대보다 먼저 나가면
            exist_ -= 1
            db.child("chat").child(roomname).update({"exist_": exist_})  # 남은 사람 수 1 감소
        else:  # 내가 마지막으로 나가는 거라면
            db.child("chat").child(roomname).remove()  # 방 삭제
        controller.ListPage_frame_init(account)
        controller.show_frame(ListPage)


class ManagePage(tk.Frame):  # tk.Frame을 상속한 ManagePage객체

    def __init__(self, parent, controller, account):  # ManagePage객체 생성자
        tk.Frame.__init__(self, parent)
        label = tk.Label(self, text="The Chat will be displayed at victim's perspective", bg='#3E4149',
                         fg="#FFFFFF")  # 모든 채팅 내역은 피해자(신고자)의 입장에서 보여진다
        label.pack(pady=10, padx=10)
        self.configure(bg="#3E4149")

        refresh = tk.Button(self, text="Refresh",
                            command=self.refresh_list, highlightbackground='#3E4149')  # 신고 목록 새로고침 버튼
        refresh.pack()

        show = tk.Button(self, text="Show Chat",
                         command=self.show_chat, highlightbackground='#3E4149')  # 채팅 내역 보기 버튼
        show.pack()

        frame1 = tk.Frame(self)
        frame1.configure(bg='#3E4149')
        frame1.pack(fill=tk.BOTH)

        scrollbar = tk.Scrollbar(self, orient="vertical")
        self.listNodes = tk.Listbox(frame1, width=30, height=30, yscrollcommand=scrollbar.set)  # 신고 목록 리스트 박스
        self.listNodes.pack(side=tk.LEFT, padx=10, pady=10)
        self.refresh_list()

        scrollbar2 = tk.Scrollbar(self, orient="vertical")
        self.Chat = tk.Listbox(frame1, width=100, height=30, yscrollcommand=scrollbar2.set)  # 채팅 내역 리스트 박스
        self.Chat.configure(exportselection=False)
        self.Chat.pack(fill=tk.BOTH, padx=10, pady=10)
        self.refresh_list()

        button3 = tk.Button(self, text="Ban",
                            command=lambda: self.ban_action(account), highlightbackground='#3E4149')  # 차단하기 버튼
        button3.pack()

        button1 = tk.Button(self, text="Go Back",
                            command=lambda: self.go_action(controller, account),
                            highlightbackground='#3E4149')  # 뒤로가기 버튼
        button1.pack()

    def ban_action(self, account):  # 해당 사용자 차단 메서드
        roomname = self.listNodes.get(self.listNodes.curselection()[0])  # 사건 일어난 방 번호
        target = db.child("request").child(roomname).get().val()['target']  # 피의자 UID
        print(target)
        if not account.ban(target):  # 예외처리 (차단 불가능)
            messagebox.showerror("Error", "Unexpected Error : Cannot Ban the target")
        else:
            db.child("request").child(roomname).remove()  # 신고내역 지우기
            db.child("ban_req").child(roomname).remove()
            self.refresh_list()
            self.Chat.delete(0, tk.END)
            messagebox.showinfo("Info", "Successfully Banned \n " + target)

    def refresh_list(self):  # 리스트 새로고침 메서드
        room_list = db.child("request").get()
        self.listNodes.delete(0, tk.END)
        cnt = 0
        try:
            for i in room_list.each():
                print(i.key())
                self.listNodes.insert(cnt, i.key())
                cnt += 1
        except:
            print("Not Yet")

    def show_chat(self):  # 채팅내역 보여주기 메서드
        self.Chat.delete(0, tk.END)
        roomname = self.listNodes.get(self.listNodes.curselection()[0])  # 방 번호 가져오기
        chat_list = db.child("ban_req").child(roomname).get()  # 채팅 내역 데이터베이스에서 가져오기
        victim = db.child("request").child(roomname).get().val()['victim']  # 피해자 UID
        try:
            for i in chat_list.each():
                print("i val")
                print(i.val()['data'])
                if i.val()['data']['from'] == victim:
                    self.Chat.insert(self.Chat.size(),
                                     "Me" + " / " + i.val()['data']['date'] + "<<-- " + i.val()['data'][
                                         'message'])  # 피해자가 보낸 채팅
                elif i.val()['data']['from'] == "public":  # 공식 채팅
                    self.Chat.insert(self.Chat.size(), i.val()['data']['message'])
                else:  # 피의자가 보낸 채팅
                    self.Chat.insert(self.Chat.size(),
                                     "Anonymous" + " / " + i.val()['data']['date'] + "-->> " + i.val()['data'][
                                         'message'])
        except:  # 예외처리
            print("Not Yet")

    def go_action(self, controller, account):  # 뒤로가기 메서드
        controller.ListPage_frame_init(account)
        controller.show_frame(ListPage)


class ProfilePage(tk.Frame):  # tk.Frame객체를 상속한 ProfilePage객체

    def __init__(self, parent, controller, account):  # ProfilePage객체 생성자
        tk.Frame.__init__(self, parent)

        label1 = tk.Label(self, text="Profile Page", bg='#3E4149', fg="#FFFFFF")
        label1.pack(pady=10, padx=10)
        self.configure(bg="#3E4149")

        label2 = tk.Label(self, text="Current Name : " + account.get_name(), bg='#3E4149', fg="#FFFFFF")
        label2.pack()
        try:  # 학년 표시 (학생 전용)
            label3 = tk.Label(self, text="Current Grade: " + account.get_grade(), bg='#3E4149', fg="#FFFFFF")
            label3.pack()
        except:  # 차단 횟수 표시 (관리자 전용)
            label3 = tk.Label(self, text="Banned Count: " + str(account.get_ban_cnt()), bg='#3E4149', fg="#FFFFFF")
            label3.pack()

        self.pw = tk.Entry(self, width=20)  # 비밀번호 입력
        self.pw.pack()

        PW = tk.Button(self, text="Change PW",
                       command=lambda: self.pw_change(account), highlightbackground='#3E4149')  # 비밀번호 바꾸기 버튼
        PW.pack()

        button = tk.Button(self, text="Go Back",
                           command=lambda: self.go_back_action(controller, account),
                           highlightbackground='#3E4149')  # 뒤로가기 버튼
        button.pack()

    def go_back_action(self, controller, account):  # 뒤로가기 메서드
        controller.ListPage_frame_init(account)
        controller.show_frame(ListPage)

    def pw_change(self, account):  # 비밀번호 바꾸기 메서드
        if account.set_passwd(self.pw.get()):
            account.update_value()
            messagebox.showinfo("Info", "Successfully Changed Passwd")
        else:  # 예외처리
            messagebox.showerror("Error", "PW must be longer than 8")


if __name__ == "__main__":
    app = BaseFrame()
    app.geometry("1000x700+400+200")  # 창 크기, 위치 조절
    app.title("SASA Random Chat")
    try:
        Font = tkFont.Font(family="AppleGothic")  # 맥용 폰트 설정
    except:  # 예외처리
        pass
    app.mainloop()  # 시작
