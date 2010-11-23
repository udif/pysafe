# -*- coding: utf-8 -*-
import sys
import os
from PyQt4.QtGui import *
from PyQt4.QtCore import *


def getIcon(icon):
  return QIcon(os.path.join(sys.path[0], "icons", icon))


def getButtonBoxText(t):
  dialog = QDialogButtonBox()
  button = dialog.addButton(t)
  return button.text()


def getText(parent, title = QString(' '), label = None, mode = QLineEdit.Normal, text = QString(), flag = Qt.Dialog):
  dialog = QDialog(parent, flag)
  dialog.setWindowTitle(title)

  layout = QVBoxLayout(dialog)

  if label is not None:
    f = QLabel(label, dialog)
    f.setWordWrap(True)
    layout.addWidget(f)

  lineedit = QLineEdit(text, dialog)
  lineedit.setEchoMode(mode)
  layout1 = QHBoxLayout()
  layout1.addWidget(lineedit, 1)

  button = QDialogButtonBox(dialog)
  button.addButton(QDialogButtonBox.Ok)
  layout1.addWidget(button)

  layout.addLayout(layout1)

  dialog.connect(button, SIGNAL('accepted()'), dialog, SLOT('accept()'))

  r = dialog.exec_()

  return (lineedit.text(), r)
