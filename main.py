import ctypes, os, sys
import json, pyperclip
from urllib import request
import ssl

from pynput import keyboard

# PyQt5 stuff
from PyQt5 import QtWidgets
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap, QIcon

PK_ENDPOINT = "https://api.pluralkit.me/v2/"

DEFAULT_JSON_DATA = {
    "system_id": "",
    "styles": {
        "general_groupLables_style": {
            "style_css": ""
        },
        "general_members_style": {
            "style_css": ""
        }
    },
    "specified_group_ids": {
        "group_id": {
            "blend_groupLabel_to_white":    0,
            "blend_group_to_white":         0,
            "blend_scrollBar_to_white":     0,
            "blend_members_to_white":       0,

            "styles_qss": {
                "group":                "",
                "member_frame":         "",
                "member_imageLabel":    "",
                "member_radioButton":   ""
            }
        },
        "no_group": {
            "name": "non grouped",

            "blend_groupLabel_to_white":    0,
            "blend_group_to_white":         0,
            "blend_scrollBar_to_white":     0,
            "blend_members_to_white":       0,

            "styles_qss": {
                "group":                "",
                "member_frame":         "",
                "member_imageLabel":    "",
                "member_radioButton":   ""
            }
        },
    }
}

DEFAULT_GROUP_DATA = {
    "id":           "",
    "uuid":         "",
    "name":         "",
    "display_name": "",
    "description":  "",
    "icon":         None,
    "banner":       None,
    "color":        "",
    "created":      "",
    "privacy":      None,
    # "members": {},
}

DEFAULT_CTX = ssl.create_default_context()
DEFAULT_CTX.check_hostname = False
DEFAULT_CTX.verify_mode = ssl.CERT_NONE

#Main TODOs or something:
#TODO: General styles should go somewhere else but in `config.json`

#TODO: Refactor the code so it's more manageable and easy to read.

#TODO: Make a Custom dialog for adding custom members/groups

#TODO: Make a Custom dialog for managing config aka: settings.

#TODO: Make an ability to refresh the groups

#TODO: Make documentation for styles
#TODO: Make documentation for config

def lerp(a, b, x) -> int: return int(b*x+a*(1-x))
def blendWithWhite(color, amt = 0.5) -> str:
    icol = int(color, 16)
    red = (icol & 0xFF0000) >> 16
    grn = (icol & 0x00FF00) >> 8
    blu = (icol & 0x0000FF)
    return '{0:06x}'.format(lerp(red, 0xff, amt) << 16 | lerp(grn, 0xff, amt) << 8 | lerp(blu, 0xff, amt))


class testDialog(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super(testDialog, self).__init__(parent=parent)

        self.resize(280, 200)
        self.setWindowTitle("test")


WINDOW_NAME = "Plural Helper"
class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent=parent)

        # Class fields.
        self.active_member  = None
        self.members        = {}
        self.actuallyClose  = False

        # Data
        self.system_data, self.config_data = getGroupsAndMembersData(validateJSON())

        # Preparing the Tray
        self.tray = QtWidgets.QSystemTrayIcon(self)
        self.tray.setIcon(QIcon("res/plurpyicon.png"))
        self.tray.setToolTip(WINDOW_NAME)
        self.tray_menu  = QtWidgets.QMenu(self)
        tray_menu_view  = QtWidgets.QAction("Show window", self)
        tray_menu_view.triggered.connect(lambda *args: self.show())
        tray_menu_close = QtWidgets.QAction("Close", self)
        tray_menu_close.triggered.connect(lambda *args: self.closeThing())
        self.tray_menu.addAction(tray_menu_view)
        self.tray_menu.addAction(tray_menu_close)
        self.tray.setContextMenu(self.tray_menu)
        self.tray.activated.connect(self.iconActivated)
        self.tray.show()
        t_icon = QtWidgets.QSystemTrayIcon.MessageIcon(QtWidgets.QSystemTrayIcon.Information)
        self.tray.showMessage(WINDOW_NAME, "The program will run in the background if you close it!", t_icon, 5)

        # Preparing the main window
        self.resize(620, 635)
        self.setMinimumSize(460, 635)

        self.centralwidget = QtWidgets.QWidget(self)
        self.setCentralWidget(self.centralwidget)
        self.main_layout = QtWidgets.QVBoxLayout(self.centralwidget)

        self.setWindowTitle(WINDOW_NAME + ": " + self.system_data["name"])

        scrollArea_MAIN_WidgetContents = QtWidgets.QWidget()
        scrollArea_MAIN_groupbox = QtWidgets.QScrollArea(self.centralwidget)
        scrollArea_MAIN_groupbox.setWidget(scrollArea_MAIN_WidgetContents)
        scrollArea_MAIN_groupbox.setWidgetResizable(True)
        scrollArea_MAIN_groupbox.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        scrollArea_MAIN_groupbox.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scrollArea_MAIN_groupbox_layout = QtWidgets.QVBoxLayout(scrollArea_MAIN_WidgetContents)
        scrollArea_MAIN_groupbox_layout.setAlignment(Qt.AlignTop)
        self.main_layout.addWidget(scrollArea_MAIN_groupbox)

        # `colors_set` is for styling purposes, [0] - prev group cloro, [1] - current, [2] - next group color
        # So people for example could do group color transitions between each other, idk.
        # TODO: Prob need to turn it into some Datatype with a Class, just for the refactoring purposes?
        colors_set      = [None, None, None]
        _group_list     = list(self.system_data["groups"].items())
        _group_list_len = len(_group_list)
        for i, _group in enumerate(_group_list):
            group_id    = _group[0]
            group       = _group[1]

            print(group_id, group["name"])
            group_config_data  = self.config_data["specified_group_ids"].get(group_id, {})

            styles = group["styles_qss"]

            self.scrollArea_WidgetContents = QtWidgets.QWidget()

            scrollArea_groupbox = QtWidgets.QScrollArea(scrollArea_MAIN_groupbox)
            scrollArea_groupbox.setWidget(self.scrollArea_WidgetContents)
            scrollArea_groupbox.setSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Fixed)
            scrollArea_groupbox.setWidgetResizable(True)
            scrollArea_groupbox.setFixedHeight(160)
            scrollArea_groupbox.setLineWidth(3)
            scrollArea_groupbox.setFrameShape(QtWidgets.QFrame.Panel)
            scrollArea_groupbox.setFrameShadow(QtWidgets.QFrame.Sunken)
            scrollArea_groupbox.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
            scrollArea_groupbox.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOn)

            # A way to pick prev and next groups, loops around if the index goes OOB
            colors_set[0] = _group_list[(i - 1) % _group_list_len][1]["color"]
            colors_set[1] = _group_list[i][1]["color"]
            colors_set[2] = _group_list[(i + 1) % _group_list_len][1]["color"]

            # Get Style's params.
            groupLabel_blend    = group_config_data.get("blend_groupLabel_to_white",    0)
            group_blend         = group_config_data.get("blend_group_to_white",         0)
            scrollBar_blend     = group_config_data.get("blend_scrollBar_to_white",     0)
            member_blend        = group_config_data.get("blend_members_to_white",       0)

            group_scrollArea_color_prev = blendWithWhite(color=colors_set[0], amt=group_blend)      if colors_set[0] else "F0F0F0"
            group_scrollArea_color      = blendWithWhite(color=colors_set[1], amt=group_blend)      if colors_set[1] else "F0F0F0"
            group_scrollArea_color_next = blendWithWhite(color=colors_set[2], amt=group_blend)      if colors_set[2] else "F0F0F0"

            group_scrollBar_color       = blendWithWhite(color=colors_set[1], amt=scrollBar_blend)  if colors_set[1] else "F0F0F0"
            group_scrollBar_color_next  = blendWithWhite(color=colors_set[2], amt=scrollBar_blend)  if colors_set[2] else "F0F0F0"
            group_scrollBar_color_prev  = blendWithWhite(color=colors_set[0], amt=scrollBar_blend)  if colors_set[0] else "F0F0F0"

            group_label_color_prev      = blendWithWhite(color=colors_set[0], amt=groupLabel_blend) if colors_set[0] else "transparent"
            group_label_color           = blendWithWhite(color=colors_set[1], amt=groupLabel_blend) if colors_set[1] else "transparent"
            group_label_color_next      = blendWithWhite(color=colors_set[2], amt=groupLabel_blend) if colors_set[2] else "transparent"

            # Load a `group` style and apply it.
            scrollArea_style = loadStyle(styles.get("group", ""))
            scrollArea_groupbox.setStyleSheet(
                scrollArea_style.format(
                    prev_group_color            = group_scrollArea_color_prev,
                    group_color                 = group_scrollArea_color,
                    next_group_color            = group_scrollArea_color_next,
                    scrollBar_prev_group_color  = group_scrollBar_color_prev,
                    scrollBar_group_color       = group_scrollBar_color,
                    scrollBar_next_group_color  = group_scrollBar_color_next
                )
            )

            scrollArea_groupbox_layout  = QtWidgets.QHBoxLayout(self.scrollArea_WidgetContents)
            scrollArea_groupbox_layout.setAlignment(Qt.AlignLeft)

            group_label_name = QtWidgets.QLabel(scrollArea_MAIN_groupbox)
            group_label_text = group_config_data.get("name", group.get("display_name", group.get("name", "NO NAME")))
            group_label_name.setText(group_label_text)

            group_label_name.setStyleSheet(loadStyle(self.config_data["styles"]["general_groupLables_style"]["style_css"]).format(
                prev_group_color    = group_label_color_prev,
                group_color         = group_label_color,
                next_group_color    = group_label_color_next
            ))

            scrollArea_MAIN_groupbox_layout.addWidget(group_label_name)
            for _, member in group["members"].items():
                print(member)

                # Download avatars and put them into `avatars` folder.
                member_avy_url  = member["avatar_url"]
                member_avy_path = ""
                if member_avy_url:
                    member_avy_ext  = member_avy_url.split(".")[-1]
                    member_avy_path = f"avatars/{member['name']}.{member_avy_ext}"
                    member_avy_req  = request.Request(member_avy_url, headers={"User-Agent": "Python3.10"})
                    member_avy_img  = request.urlopen(member_avy_req, context=DEFAULT_CTX)
                    with open(member_avy_path, "wb") as memberavyfile:
                        memberavyfile.write(member_avy_img.read())

                frame_memberbox = QtWidgets.QFrame(self.scrollArea_WidgetContents)
                frame_memberbox.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
                frame_memberbox.setFixedSize(102, 120)
                frame_memberbox.setLineWidth(2)
                frame_memberbox.setFrameShape(QtWidgets.QFrame.Panel)
                frame_memberbox.setFrameShadow(QtWidgets.QFrame.Sunken)

                # Load a `member_frame` style and apply it.
                member_frame_style = loadStyle(styles.get("member_frame", ""))
                frame_memberbox.setStyleSheet(member_frame_style.format(color=blendWithWhite(color=member["color"] or "F0F0F0", amt=member_blend)))

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
                    memberbutton.setText(member["display_name"] or member["name"])

                    # Load a `member_radioButton` style and apply it.
                    member_radioButton_style = loadStyle(styles.get("member_radioButton", ""))
                    memberbutton.setStyleSheet(member_radioButton_style)

                    # Workaround for unchecking prev radio buttons when you click on another.
                    # Actually has to be defined in here or else it won't work, it's very stupid tbh.
                    def disableButtons(*_, foo = member["name"]):
                        meme = self.members[foo] # "Haha Amy very funni" - (c) Amy in her head.
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

                    # Load a `member_imageLabel` style and apply it.
                    member_imageLabel_style = loadStyle(styles.get("member_imageLabel", ""))
                    memberimage.setStyleSheet(member_imageLabel_style)

                frame_memberbox_layout.addWidget(memberimage)
                frame_memberbox_layout.addWidget(memberbutton)

                scrollArea_groupbox_layout.addWidget(frame_memberbox)

            scrollArea_MAIN_groupbox_layout.addWidget(scrollArea_groupbox)

        button_none = QtWidgets.QPushButton(self.centralwidget)
        button_none.setText("None")
        button_none.setFixedSize(100, 23)

        def none_button():
            if not self.active_member: return

            self.active_member["button"].setChecked(False)
            self.active_member = None

        button_none.clicked.connect(lambda *args: none_button())

        button_dialogTest = QtWidgets.QPushButton(self.centralwidget)
        button_dialogTest.setText("Dialog Test")
        button_dialogTest.setFixedSize(100, 23)

        # The TODO boy
        def test_dialog():
            dialog = testDialog(parent=self)
            dialog.show()

        button_dialogTest.clicked.connect(lambda *args: test_dialog())

        self.main_layout.addWidget(button_none)
        self.main_layout.addWidget(button_dialogTest)


    def closeThing(self):
        self.actuallyClose = True
        self.close()


    def closeEvent(self, event):
        if not self.actuallyClose: event.ignore()
        self.hide()


    def iconActivated(self, reason: QtWidgets.QSystemTrayIcon.ActivationReason):
        if reason == QtWidgets.QSystemTrayIcon.Trigger:
            self.show()


# Pop Up window with message.
def errorMsg(message, title, _exit=True) -> None:
    """
    :param message: Message to display.
    :param title: Title.
    :param _exit: If the exit from the program is required on the call.
    :return: None
    """
    ctypes.windll.user32.MessageBoxW(0, message, title, 0)
    if _exit: sys.exit()


def validateJSON(config_name = r"config.json") -> dict:
    """
    :param config_name: name for the config to create/check.
    :return: config_data: dict
    """
    # Check if config exists, if not - create it with default params.
    if not os.path.exists(config_name):
        f = open(config_name, 'w+')
        f.write(json.dumps(DEFAULT_JSON_DATA, indent=4))
        f.close()
        errorMsg(f"Setup the '{config_name}' first", "Welcome!")

    # Check the config itself.
    config_data_raw = open(config_name, 'r+')
    config_data     = json.load(config_data_raw)
    config_data_raw.close()
    print(config_data)

    # Check the fields in the config
    if config_data["system_id"] == "":
        errorMsg("The System ID is not specifyed", f"Error in {config_name}")

    print("Seems loik everything is fine with the confeeg! ^w^")

    return config_data


def orderGroups(systems_data, config_data) -> None:
    """
    :param systems_data:
    :param config_data:
    :return: None

    Gets the unsorted dict of groups from the System and
    sorts it with the specified order from the `congig.json`.

    First it figures our which groups are specified and sorts them out,
    and then it puts the unsorted leftovers at the end of the list.
    """
    config_specified_groups = config_data["specified_group_ids"]
    systems_groups          = systems_data["groups"].copy()

    organised_groups = {}
    for group in config_specified_groups:
        if group in systems_groups:
            organised_groups[group] = systems_groups.pop(group)

    for key, sg in systems_groups.items():
        organised_groups[key] = sg

    systems_data["groups"] = organised_groups


def getGroupsAndMembersData(config_data: dict) -> tuple[dict, dict]:
    """
    :param config_data: dict of config_data
    :return: systems_data: dict, config_data: dict
    """
    config_system_id           = config_data["system_id"]
    config_specified_groups    = config_data["specified_group_ids"]

    # Gather system's data
    systems_data        = json.load(request.urlopen(f"{PK_ENDPOINT}systems/{config_system_id}",         context=DEFAULT_CTX))
    systems_groups      = json.load(request.urlopen(f"{PK_ENDPOINT}systems/{config_system_id}/groups",  context=DEFAULT_CTX))
    systems_all_members = json.load(request.urlopen(f"{PK_ENDPOINT}systems/{config_system_id}/members", context=DEFAULT_CTX))

    # Prepare the "no_group" group for members without a group and append it into the list of the groups
    # For easy to maintain purpose later
    prepared_no_group       = DEFAULT_GROUP_DATA
    prepared_no_group["id"] = "no_group"
    systems_groups.append(prepared_no_group)


    # prepared_systems_data = systems_data
    systems_data["groups"] = {}
    for i, systems_group in enumerate(systems_groups, 1):
        # if no leftover members are left - don't include "no_group"
        if len(systems_all_members) == 0: break

        group_id        = systems_group["id"]
        prepared_group  = systems_group

        # Preparing and appending data for conveniece idk.
        prepared_group["members"] = {}

        # If the group specified in the config - retreive the data
        prepared_group["styles_qss"] = {}
        if group_id in config_specified_groups:
            prepared_group["styles_qss"] = config_specified_groups[group_id]["styles_qss"]

        # Append members into the group's data if it's not "no_group"
        if group_id != "no_group":
            groups_members = json.load(request.urlopen(f"{PK_ENDPOINT}groups/{group_id}/members"))
            for member in groups_members:
                prepared_group["members"][member["id"]] = member

            # Take out members that already in some group
            # At the end of iterations the leftover members will be
            # appended into the "no_group" group
            for groups_member in groups_members:
                for n, member in enumerate(systems_all_members):
                    if groups_member == member:
                        systems_all_members.pop(n) #what's popin?
                        break

        # Append the prepared group in the main data
        systems_data["groups"][group_id] = prepared_group

        # Add the "no_group" members if exist (if they don't the loop interrupts anyway before this statement)
        if i == len(systems_groups):
            systems_data["groups"]["no_group"]["members"] = {member["id"]: member for member in systems_all_members}

    # Just saves System's info, debugging purpose and just for owner's curiousity idk
    with open("your_system.json", 'w+') as f:
        f.write(json.dumps(systems_data, indent=4))

    orderGroups(systems_data, config_data)

    return systems_data, config_data


def loadStyle(style_name) -> str:
    """
    :param style_name:
    :return: str: Style Code(QSS) String

    A safe way to get a style and return if none was specified.
    """
    style_code = ""
    if not style_name: return ""

    try:
        with open("styles/"+style_name, "r") as style:
            style_code = style.read()
    except FileNotFoundError:
        errorMsg("The specified style file: '"+str(style_name)+"' does not exist!", "Style Error!")

    return style_code


def makeDir(name) -> None:
    """
    :param name:
    :return: None

    A safe way to make a directory.
    """
    try:
        os.mkdir(name)
    except FileExistsError:
        pass


def prepareFolders() -> None:
    """
    :return: None
    """
    makeDir("avatars")
    makeDir("styles")


if __name__ == "__main__":
    prepareFolders()

    # WINDOW HANDLING
    app = QtWidgets.QApplication(sys.argv)
    window = MainWindow()
    window.show()

    # KEYBOARD HANDLING
    kb_controller = keyboard.Controller()
    sending = False
    def sendWithPrefix():
        # Go the the very beginning of the line
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








