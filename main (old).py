import json
import sys
from urllib import request

# PyQt5 stuff
from PyQt5 import QtWidgets
from PyQt5.QtGui import QPixmap

PK_ENDPOINT = "https://api.pluralkit.me/v2/"
GROUP_ID = ["civgw", "iswtg", "smcnu"]


class MainWindow(QtWidgets.QDialog):
    def __init__(self, parent = None):
        self.active_member = None
        self.members = []

        QtWidgets.QDialog.__init__(self, parent)

        self.setWindowTitle("Test")
        self.resize(300, 400)

        # Make a vertical layout for aligning elements in it evenly
        self.main_layout = QtWidgets.QVBoxLayout()
        self.setLayout(self.main_layout)
        for groupid in GROUP_ID:
            members = json.load(request.urlopen(f"{PK_ENDPOINT}groups/{groupid}/members"))
            groupbox = QtWidgets.QScrollArea(self)
            groupboxlayout = QtWidgets.QHBoxLayout()
            groupbox.setLayout(groupboxlayout)
            for member in members:
                print(member)
                memberavyext = member["avatar_url"].split(".")[-1]
                memberavypath = f"avatars/{member['name']}.{memberavyext}"
                memberavyreq = request.Request(member["avatar_url"], headers={"User-Agent": "Python3.10"})
                memberavy = request.urlopen(memberavyreq)
                with open(memberavypath, "wb") as memberavyfile:
                    memberavyfile.write(memberavy.read())


                memberbox = QtWidgets.QFrame(groupbox)
                memberbox.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Maximum)
                memberbox.setMinimumSize(150, 150)

                memberboxlayout = QtWidgets.QVBoxLayout(memberbox)
                memberbox.setLayout(memberboxlayout)

                memberbutton = QtWidgets.QRadioButton(memberbox)
                memberdict = {
                    "button": memberbutton,
                    "prefix": member["proxy_tags"][0]["prefix"],
                    "name": member["name"]
                }
                self.members.append(memberdict)
                memberbutton.setText(member["name"])

                # hElloO uwuwuwuwuwuuwuwuw ye
                # do u see dis? yooooo
                # brb gettin fish n chips   # Bon apetit <3
                # ye oke
                # damn async writing too
                # amazing hooly fucking draggy

                #Also uh your name is Spyro in here, I guess it inherits your PC's name or soemthing?

                def disableButtons(*_, foo = member["name"]):
                    for m in self.members:
                        button = m["button"]
                        print(foo, m["name"])
                        if foo == m["name"]:
                            button.setChecked(True)
                            self.active_member = m
                        else:
                            button.setChecked(False)
                memberbutton.clicked.connect(disableButtons)

                memberimage = QtWidgets.QLabel(memberbox)
                memberimage.setPixmap(QPixmap(memberavypath))
                memberimage.setMinimumSize(50, 50)
                memberimage.setMaximumSize(50, 50)
                memberimage.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
                memberimage.setScaledContents(True)

                memberboxlayout.addWidget(memberimage)
                memberboxlayout.addWidget(memberbutton)
                groupboxlayout.addWidget(memberbox)

            self.main_layout.addWidget(groupbox)

        print(self.members)



if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
