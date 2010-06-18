# -*- coding: utf-8 -*-
import ConfigParser
import os

from PyQt4.QtGui import *
from PyQt4.QtCore import *


class Configuration:

  VERSION = 0
  PORTRAIT_SLIDER_SIZE = 1
  LANDSCAPE_SLIDER_SIZE = 2
  AUTO_ROTATION = 3
  DATABASE_FILE = 4
  AUTO_LOCK_TIME = 5


  def __init__(self):
    self.__config = ConfigParser.RawConfigParser()
    self.__load()
    self.__check_sanity()

  def __load(self):
    self.__config.read('%s/.pysafe.conf' % (os.path.expanduser('~')))

  def __save(self):
    configfile = open('%s/.pysafe.conf' % (os.path.expanduser('~')), 'wb')
    self.__config.write(configfile)
    configfile.close()

  def __check_sanity(self):
    if not self.__config.has_section('Window'):
      self.__config.add_section('Window')

    # verifica o tamanho do slider em modo retrato
    tmp = 300
    if self.__config.has_option('Window', 'portrait_slider'):
      tmp = self.__config.get('Window', 'portrait_slider')
      if not tmp.isdigit():
        tmp = 300
    # salva o tamanho na configuração para garantir que não há erros
    self.__config.set('Window', 'portrait_slider', tmp)

    # verifica o tamanho do slider em modo paisagem
    tmp = 300
    if self.__config.has_option('Window', 'landscape_slider'):
      tmp = self.__config.get('Window', 'landscape_slider')
      if not tmp.isdigit():
        tmp = 300
    self.__config.set('Window', 'landscape_slider', tmp)

    if not self.__config.has_section('General'):
      self.__config.add_section('General')
    if not self.__config.has_option('General', 'dbfile'):
      self.__config.set('General', 'dbfile', '')

    # valida a rotação
    tmp = 1
    if self.__config.has_option('General', 'auto_rotate'):
      tmp = self.__config.get('General', 'auto_rotate')
      if not tmp.isdigit():
        tmp = 1
    self.__config.set('General', 'auto_rotate', tmp)

    # valida o bloqueio automático
    tmp = 0
    if self.__config.has_option('General', 'lock_time'):
      tmp = self.__config.get('General', 'lock_time')
      if not tmp.isdigit():
        tmp = 0
    self.__config.set('General', 'lock_time', tmp)

    # verifica a versão
    if not self.__config.has_option('General', 'version'):
      self.__config.set('General', 'version', '0')


  def get(self, item):
    if item == self.PORTRAIT_SLIDER_SIZE:
      return self.__config.getint('Window', 'portrait_slider')
    elif item == self.LANDSCAPE_SLIDER_SIZE:
      return self.__config.getint('Window', 'landscape_slider')
    elif item == self.AUTO_ROTATION:
      return self.__config.getint('General', 'auto_rotate')
    elif item == self.AUTO_LOCK_TIME:
      return self.__config.getint('General', 'lock_time')
    elif item == self.DATABASE_FILE:
      return self.__config.get('General', 'dbfile')
    elif item == self.VERSION:
      return self.__config.get('General', 'version')

    return None

  def set(self, item, value):
    # se o valor é igual, não precisa alterar!
    if self.get(item) == value:
      return

    if item == self.PORTRAIT_SLIDER_SIZE:
      self.__config.set('Window', 'portrait_slider', value)
    elif item == self.LANDSCAPE_SLIDER_SIZE:
      self.__config.set('Window', 'landscape_slider', value)
    elif item == self.AUTO_ROTATION:
      self.__config.set('General', 'auto_rotate', value)
    elif item == self.AUTO_LOCK_TIME:
      self.__config.set('General', 'lock_time', value)
    elif item == self.DATABASE_FILE:
      self.__config.set('General', 'dbfile', value)
    elif item == self.VERSION:
      self.__config.set('General', 'version', value)

    self.__save()

  def showDialog(self, parent):
    window = QDialog(parent)
    window.setWindowTitle(" ")
    window.setModal(True)

    rotate = QCheckBox(_("auto-rotate (if available)"), window)
    if self.get(self.AUTO_ROTATION) == 0:
      rotate.setCheckState(Qt.Unchecked)
    else:
      rotate.setCheckState(Qt.Checked)

    lock_label = QLabel(_("seconds to auto-lock (0 disables)"))
    lock = QLineEdit(window)
    lock.setInputMask("0000")
    lock.setText(str(self.get(self.AUTO_LOCK_TIME)))

    button = QDialogButtonBox(QDialogButtonBox.Save, Qt.Horizontal, window)
    window.connect(button, SIGNAL('accepted()'), window, SLOT('accept()'))

    layout = QVBoxLayout(window)
    layout.addWidget(rotate)
    layout.addStretch(1)
    layout1 = QHBoxLayout()
    layout1.addWidget(lock)
    layout1.addWidget(lock_label)
    layout1.addStretch(1)
    layout.addLayout(layout1)
    layout.addWidget(button)

    if window.exec_() == QDialog.Accepted:
      if rotate.checkState() == Qt.Checked:
        self.set(self.AUTO_ROTATION, 1)
      else:
        self.set(self.AUTO_ROTATION, 0)

      tmp = str(lock.text().toUtf8())
      if tmp.isdigit():
        self.set(self.AUTO_LOCK_TIME, tmp)

    window.close()
