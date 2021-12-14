import ctypes
import os
import json
import sys
import pyperclip
from urllib import request
from pynput import keyboard

# PyQt5 stuff
from PyQt5 import QtWidgets
from PyQt5.QtCore import Qt
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

#Groups Styles
group_scrollArea_styleSheet = '''
QScrollBar:horizontal {{
    height: 13px;
    background-color: #{group_color}
}}
'''


PK_ENDPOINT = "https://api.pluralkit.me/v2/"
DEFAULT_JSON_DATA = {
    "system_id": "",
    "styles": {
        "general_groupLables_style": "",
    },
    "specified_group_ids": {
        "group_id": {
            "style_qss": ""
        },
    }
}


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


        self.resize(620, 635)
        self.setMinimumSize(460, 635)

        self.centralwidget = QtWidgets.QWidget(self)
        self.setCentralWidget(self.centralwidget)
        self.main_layout = QtWidgets.QVBoxLayout(self.centralwidget)

        self.system_data, self.config_data = getGroupsAndMembersData(validateJSON())
        self.setWindowTitle(self.system_data["name"])

        scrollArea_MAIN_WidgetContents = QtWidgets.QWidget()
        scrollArea_MAIN_groupbox = QtWidgets.QScrollArea(self.centralwidget)
        scrollArea_MAIN_groupbox.setWidget(scrollArea_MAIN_WidgetContents)
        scrollArea_MAIN_groupbox.setWidgetResizable(True)
        scrollArea_MAIN_groupbox.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        scrollArea_MAIN_groupbox.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scrollArea_MAIN_groupbox_layout = QtWidgets.QVBoxLayout(scrollArea_MAIN_WidgetContents)
        scrollArea_MAIN_groupbox_layout.setAlignment(Qt.AlignTop)
        self.main_layout.addWidget(scrollArea_MAIN_groupbox)

        colors_set = [None, None, None]
        _group_list = list(self.system_data["groups"].items())[::-1]
        _group_list_len = len(_group_list)
        for i, _group in enumerate(_group_list):
            group = _group[1]

            scrollArea_style = group["style_qss"]
            self.scrollArea_WidgetContents = QtWidgets.QWidget()

            scrollArea_groupbox = QtWidgets.QScrollArea(scrollArea_MAIN_groupbox)
            scrollArea_groupbox.setWidget(self.scrollArea_WidgetContents)
            scrollArea_groupbox.setSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Fixed)
            scrollArea_groupbox.setFixedHeight(160)
            scrollArea_groupbox.setWidgetResizable(True)
            scrollArea_groupbox.setLineWidth(3)
            scrollArea_groupbox.setFrameShape(QtWidgets.QFrame.Panel)
            scrollArea_groupbox.setFrameShadow(QtWidgets.QFrame.Sunken)
            scrollArea_groupbox.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
            scrollArea_groupbox.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOn)

            colors_set[0] = _group_list[(i - 1) % _group_list_len][1]["color"]
            colors_set[1] = _group_list[i][1]["color"]
            colors_set[2] = _group_list[(i + 1) % _group_list_len][1]["color"]

            # TODO: Add more params in JSON for blendWithWhite or something
            group_scrollArea_color_prev = blendWithWhite(color=colors_set[0], amt=1) if colors_set[0] else "F0F0F0"
            group_scrollArea_color      = blendWithWhite(color=colors_set[1], amt=1) if colors_set[1] else "F0F0F0"
            group_scrollArea_color_next = blendWithWhite(color=colors_set[2], amt=1) if colors_set[2] else "F0F0F0"

            group_scrollBar_color_prev  = blendWithWhite(color=colors_set[0], amt=0.7) if colors_set[0] else "F0F0F0"
            group_scrollBar_color       = blendWithWhite(color=colors_set[1], amt=0.7) if colors_set[1] else "F0F0F0"
            group_scrollBar_color_next  = blendWithWhite(color=colors_set[2], amt=0.7) if colors_set[2] else "F0F0F0"

            group_label_color_prev  = blendWithWhite(color=colors_set[0], amt=0.4) if colors_set[0] else "transparent"
            group_label_color       = blendWithWhite(color=colors_set[1], amt=0.4) if colors_set[1] else "transparent"
            group_label_color_next  = blendWithWhite(color=colors_set[2], amt=0.4) if colors_set[2] else "transparent"

            scrollArea_groupbox.setStyleSheet(
                scrollArea_style.format(
                    prev_group_color    = group_scrollArea_color_prev,
                    group_color         = group_scrollArea_color,
                    next_group_color    = group_scrollArea_color_next
                )
                +
                group_scrollArea_styleSheet.format(
                    prev_group_color    = group_scrollBar_color_prev,
                    group_color         = group_scrollBar_color,
                    next_group_color    = group_scrollBar_color_next
                )
            )

            scrollArea_groupbox_layout  = QtWidgets.QHBoxLayout(self.scrollArea_WidgetContents)
            scrollArea_groupbox_layout.setAlignment(Qt.AlignLeft)

            group_label_name = QtWidgets.QLabel(scrollArea_MAIN_groupbox)
            group_label_name.setText(group["display_name"] if group["display_name"] else group["name"])

            group_label_name.setStyleSheet(self.config_data["styles"]["general_groupLables_style"].format(
                prev_group_color    = group_label_color_prev,
                group_color         = group_label_color,
                next_group_color    = group_label_color_next
            ))

            scrollArea_MAIN_groupbox_layout.addWidget(group_label_name)
            for _, member in group["members"].items():
                print(member)

                try:
                    os.mkdir("avatars")
                except FileExistsError:
                    pass

                member_avy_url  = member["avatar_url"]
                member_avy_path = ""
                if member_avy_url:
                    member_avy_ext  = member_avy_url.split(".")[-1]
                    member_avy_path = f"avatars/{member['name']}.{member_avy_ext}"
                    member_avy_req  = request.Request(member_avy_url, headers={"User-Agent": "Python3.10"})
                    member_avy_img  = request.urlopen(member_avy_req)
                    with open(member_avy_path, "wb") as memberavyfile:
                        memberavyfile.write(member_avy_img.read())

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
                        "prefix": member["proxy_tags"][0]["prefix"] if member["proxy_tags"] else None,
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
                    if member_avy_url:
                        memberimage.setPixmap(QPixmap(member_avy_path))
                    else:
                        memberimage.setText("NO IMAGE")
                        memberimage.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)

                    memberimage.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
                    memberimage.setFixedSize(80, 80)

                frame_memberbox_layout.addWidget(memberimage)
                frame_memberbox_layout.addWidget(memberbutton)

                scrollArea_groupbox_layout.addWidget(frame_memberbox)

            scrollArea_MAIN_groupbox_layout.addWidget(scrollArea_groupbox)

        button_none = QtWidgets.QPushButton(self.centralwidget)
        button_none.setText("None")
        button_none.setFixedSize(100, 23)

        def none_button():
            self.active_member["button"].setChecked(False)
            self.active_member = None

        button_none.clicked.connect(lambda *args: none_button())

        self.main_layout.addWidget(button_none)


def errorMsg(message, title, _exit=True):
    ctypes.windll.user32.MessageBoxW(0, message, title, 0)
    if _exit: sys.exit()


def validateJSON(config_name = "config.json"):
    # Check if config exists
    if not os.path.exists(config_name):
        f = open(config_name, 'w+')
        f.write(json.dumps(DEFAULT_JSON_DATA, indent=4))
        f.close()
        errorMsg(f"Setup the '{config_name}' first", "Welcome!")

    # Check the config itself.
    config_data_raw = open(config_name, 'r+')
    config_data = json.load(config_data_raw)
    print(config_data)

    # Check the fields in the config
    if config_data["system_id"] == "":
        errorMsg("The System ID is not specifyed", f"Error in {config_name}")

    print("Seems loik everything is fine with the config! ^w^")

    return config_data


def getGroupsAndMembersData(config_data):
    config_system_id           = config_data["system_id"]
    config_specified_groups    = config_data["specified_group_ids"]

    systems_data    = json.load(request.urlopen(f"{PK_ENDPOINT}systems/{config_system_id}"))
    systems_groups  = json.load(request.urlopen(f"{PK_ENDPOINT}systems/{config_system_id}/groups"))

    prepared_systems_data = systems_data
    prepared_systems_data["groups"] = {}
    for systems_group in systems_groups:
        group_id = systems_group["id"]
        prepared_group = systems_group

        # Preparing and appending data for conveniece idk.
        prepared_group["members"] = {}

        # If the group specified in the config - retreive the data
        prepared_group["style_qss"] = ""
        if group_id in config_specified_groups:
            prepared_group["style_qss"] = str(config_specified_groups[group_id]["style_qss"])

        # Append members into the group's data
        groups_members = json.load(request.urlopen(f"{PK_ENDPOINT}groups/{group_id}/members"))
        for member in groups_members:
            prepared_group["members"][member["id"]] = member

        # Append the prepared group in the main data
        prepared_systems_data["groups"][group_id] = prepared_group

    f = open("your_system.json", 'w+')
    f.write(json.dumps(prepared_systems_data, indent=4))
    f.close()

    return prepared_systems_data, config_data


if __name__ == "__main__":
    # WINDOW HANDLING
    app = QtWidgets.QApplication(sys.argv)
    window = MainWindow()
    window.show()

    # KEYBOARD HANDLING
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
        if not sending and data.vkCode == 0x0d and message == 0x100 and window.active_member is not None:
            sending = True
            sendWithPrefix()
            sending = False
            kb_listener.suppress_event()
        return False
    kb_listener = keyboard.Listener(win32_event_filter = inputfilter)
    kb_listener.start()

    # STATUSES HANDLING
    status = app.exec_()
    kb_listener.stop()
    sys.exit(status)








