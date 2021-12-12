import json
import sys
import pyperclip
from urllib import request
from pynput import keyboard
from os import mkdir

# PyQt5 stuff
from PyQt5 import QtWidgets
from PyQt5.QtCore import Qt, QPropertyAnimation, QRect, QSize
from PyQt5.QtGui import QPixmap

#Members Styling
member_StyleSheet = '''
QFrame {{
    border: 2px solid gray;
    border-bottom-right-radius: 15px;
    border-top-left-radius: 15px;
    background: #{color};
}}
'''
memberavy_StyleSheet = '''
QLabel {
    border-bottom-right-radius: 15px;
    border-top-left-radius: 15px;
}
'''

QLabel_StyleSheet = '''
QRadioButton {
    background-color: transparent;
}
'''


#Group Styling
#AED0DD
ScrollArea_StyleSheet_Heaven = '''
QScrollArea QWidget{   
    /*background-color: #AED0DD;*/
    background-color: qlineargradient( x1:0.5 y1:0, x2:0.5 y2:1, stop:0.9 #AED0DD, stop:1 #591B79);
}
QWidget#scrollAreaWidgetContents {
    background-color: #AED0DD;
} 
QAbstractScrollArea {
    background-color: #AED0DD;
}
'''

#591B79
ScrollArea_StyleSheet_Core = '''
QScrollArea QWidget{   
    background-color: #591B79;
}

QAbstractScrollArea {
    background-color: #591B79;
}
'''

#0F1854
ScrollArea_StyleSheet_Depths = '''
QScrollArea QWidget{   
    /*background-color: #0F1854;*/
    background-color: qlineargradient( x1:0.5 y1:0, x2:0.5 y2:1, stop:0 #591B79, stop:0.1 #0F1854);
}
QWidget#scrollAreaWidgetContents {
    background-color: #0F1854;
} 
QAbstractScrollArea {
    background-color: #0F1854;
}
'''

PK_ENDPOINT = "https://api.pluralkit.me/v2/"
GROUP_ID = [
    ("civgw", ScrollArea_StyleSheet_Heaven),
    ("iswtg", ScrollArea_StyleSheet_Core),
    ("smcnu", ScrollArea_StyleSheet_Depths)
]

def lerp(a, b, x): return int(a*x+b*(1-x))
def blendWithWhite(color, amt = 0.5):
    icol = int(color, 16)
    red = (icol & 0xFF0000) >> 16
    grn = (icol & 0x00FF00) >> 8
    blu = (icol & 0x0000FF)
    return '{0:06x}'.format(lerp(red, 0xff, amt) << 16 | lerp(grn, 0xff, amt) << 8 | lerp(blu, 0xff, amt))


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        self.active_member = None
        self.members = {}

        super(MainWindow, self).__init__()

        self.setWindowTitle("Test")
        self.resize(620, 487)
        self.setMinimumSize(460, 487)

        self.centralwidget = QtWidgets.QWidget(self)
        self.setCentralWidget(self.centralwidget)

        self.main_layout = QtWidgets.QVBoxLayout(self.centralwidget)

        for groupid, scrollArea_style in GROUP_ID:
            self.scrollArea_WidgetContents = QtWidgets.QWidget()
            self.scrollArea_WidgetContents.setStyleSheet(scrollArea_style)

            scrollArea_groupbox = QtWidgets.QScrollArea(self.centralwidget)
            scrollArea_groupbox.setStyleSheet(scrollArea_style)
            scrollArea_groupbox.setWidget(self.scrollArea_WidgetContents)
            scrollArea_groupbox.setWidgetResizable(True)
            scrollArea_groupbox.setLineWidth(3)
            scrollArea_groupbox.setFrameShape(QtWidgets.QFrame.Panel)
            scrollArea_groupbox.setFrameShadow(QtWidgets.QFrame.Sunken)
            scrollArea_groupbox.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

            scrollArea_groupbox_layout  = QtWidgets.QHBoxLayout(self.scrollArea_WidgetContents)
            scrollArea_groupbox_layout.setAlignment(Qt.AlignLeft)

            members = json.load(request.urlopen(f"{PK_ENDPOINT}groups/{groupid}/members"))
            for member in members:
                print(member)
                try:
                    mkdir("avatars")
                except FileExistsError:
                    pass
                member_avy_ext = member["avatar_url"].split(".")[-1]
                member_avy_path = f"avatars/{member['name']}.{member_avy_ext}"
                member_avy_req = request.Request(member["avatar_url"], headers={"User-Agent": "Python3.10"})
                member_avy = request.urlopen(member_avy_req)
                with open(member_avy_path, "wb") as memberavyfile:
                    memberavyfile.write(member_avy.read())

                frame_memberbox = QtWidgets.QFrame(self.scrollArea_WidgetContents)
                frame_memberbox.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
                frame_memberbox.setFixedSize(102, 120)
                frame_memberbox.setLineWidth(2)
                frame_memberbox.setFrameShape(QtWidgets.QFrame.Panel)
                frame_memberbox.setFrameShadow(QtWidgets.QFrame.Sunken)
                frame_memberbox.setStyleSheet(member_StyleSheet.format(color=blendWithWhite(color=member["color"], amt=0.4)))

                frame_memberbox_layout = QtWidgets.QVBoxLayout(frame_memberbox)

                if "In memberbox":
                    memberbutton = QtWidgets.QRadioButton(frame_memberbox)
                    memberdict = {
                        "frame":  frame_memberbox,
                        "button": memberbutton,
                        "prefix": member["proxy_tags"][0]["prefix"],
                        "name": member["name"]
                    }
                    self.members[member["name"]] = memberdict
                    memberbutton.setText(member["name"])
                    memberbutton.setStyleSheet(QLabel_StyleSheet)

                    def disableButtons(*_, foo = member["name"]):
                        meme = self.members[foo]
                        if self.active_member:
                            self.active_member["button"].setChecked(False)
                        self.active_member = meme
                        self.active_member["button"].setChecked(True)
                    memberbutton.clicked.connect(disableButtons)

                    memberimage = QtWidgets.QLabel(frame_memberbox)
                    memberimage.setScaledContents(True)
                    memberimage.setPixmap(QPixmap(member_avy_path))
                    memberimage.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
                    memberimage.setFixedSize(80, 80)

                frame_memberbox_layout.addWidget(memberimage)
                frame_memberbox_layout.addWidget(memberbutton)

                scrollArea_groupbox_layout.addWidget(frame_memberbox)

            self.main_layout.addWidget(scrollArea_groupbox)

        button_none = QtWidgets.QPushButton(self.centralwidget)
        button_none.setText("None")
        button_none.setFixedSize(100, 23)

        def none_button():
            self.active_member["button"].setChecked(False)
            self.active_member = None

        button_none.clicked.connect(lambda *args: none_button())

        self.main_layout.addWidget(button_none)



if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = MainWindow()
    window.show()

    kb_controller = keyboard.Controller()
    sending = False
    def sendWithPrefix():
        with kb_controller.pressed(keyboard.Key.ctrl):
            kb_controller.tap(keyboard.Key.home)

        prefix = " "+window.active_member["prefix"]
        pyperclip.copy(prefix)
        with kb_controller.pressed(keyboard.Key.ctrl):
            kb_controller.tap('v')





        kb_controller.tap(keyboard.Key.enter)

    def inputfilter(message, data):
        global sending
        print(message, data.vkCode, sending)
        if not sending and data.vkCode == 0x0d and message == 0x100 and window.active_member is not None:
            sending = True
            sendWithPrefix()
            sending = False
            listener.suppress_event()
        return False

    listener = keyboard.Listener(win32_event_filter = inputfilter)
    listener.start()
    status = app.exec_()
    listener.stop()
    sys.exit(status)
