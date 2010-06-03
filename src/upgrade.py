# -*- coding: utf-8 -*-
import pickle
import gzip
import os, sys
import util
from database import Dados
from Crypto.Cipher import Blowfish
from Crypto.Hash import MD5
from PyQt4.QtGui import *
from PyQt4.QtCore import *

class Upgrade:

  def __init__(self, parent, oldVersion, newVersion):
    self.__parent = parent
    self.__oldVersion = oldVersion
    self.__newVersion = newVersion


  def check(self):
    ret = True
    if self.__oldVersion == "0" and os.path.exists(os.path.join(os.path.expanduser('~'), "MyDocs", "pysafe.db")):
      ret = ToSqlite(self.__parent).run()
    else:
      ret = NewSqlite(self.__parent).run()

    return ret


class ToSqlite(QWizard):

  DATABASE_OK = 0
  ARQUIVO_NAO_LOCALIZADO = 1
  SENHA_INVALIDA = 2
  DADOS_CORROMPIDOS = 3

  def __init__(self, parent):
    QWizard.__init__(self, parent)

    self.database_data = {}

    self.currentIdChanged.connect(self.pageChanged)
    self.setWindowTitle(_("Upgrade Wizard"))

    self.addPage(self.createWelcome())
    self.addPage(self.createPassword())
    self.addPage(self.createFilename())


  def initializePage(self, id):
    QWizard.initializePage(self, id)

    if id == 2:
      fn = str(self.field("filename").toString())
      if fn is None or len(fn) == 0:
        if os.path.exists(os.path.join(os.path.expanduser('~'), "MyDocs")):
          # estamos no N900, teoricamente!
          self.setField("filename", os.path.join(os.path.expanduser('~'), "MyDocs", "pysafe.sqlite"))
        else:
          self.setField("filename", os.path.join(os.path.expanduser('~'), "pysafe.sqlite"))


  def run(self):
    if self.exec_() == 1:
      fn = str(self.field("filename").toString())
      pwd = str(self.field("password").toString())

      if os.path.exists(fn):
        if QMessageBox.question(None, " ", _("The file \"%s\" already exists. Overwrite?") % fn, QMessageBox.Yes | QMessageBox.No) != QMessageBox.Yes:
          return None
        # remove o arquivo
        os.remove(fn)

      db = Dados(fn)
      db.createDB(pwd)

      ret = db.open(pwd)
      if ret != db.DATABASE_OK:
        texto = _("An undefined error has ocurred!")
        if ret == db.ARQUIVO_NAO_LOCALIZADO:
          texto = _("Database file not found. There was an error creating the database.")
        elif ret == db.SENHA_INVALIDA:
          texto = _("Invalid password!")
        elif ret == db.DADOS_CORROMPIDOS:
          texto = _("Database corrupted or invalid password!")
        QMessageBox.warning(None, " ", texto)
        return

      progress = QProgressDialog(_("Importing..."), _("Cancel"), 0, self.__count(self.database_data), self)
      progress.show()
      self.__convertToDB(db, self.database_data, progress)
      progress.hide()
      db.close()

      ret = progress.wasCanceled()
      progress.reset()
      progress.hide()
      progress.close()

      if ret:
        return None

      return (fn, pwd)
    else:
      return None


  def __count(self, obj, contador = 0):
    if type(obj) is dict:
      keys = obj.keys()
      contador += len(keys)
      for i in keys:
        contador = self.__count(obj[i], contador)
    return contador


  def pageChanged(self, id):
    if id == 2:
      # carrega o banco atual
      ret = self.__loadOld()
      if ret != self.DATABASE_OK:
        texto = _("An undefined error has ocurred!")
        if ret == self.ARQUIVO_NAO_LOCALIZADO:
          texto = _("Database file not found")
        elif ret == self.SENHA_INVALIDA:
          texto = _("Invalid password!")
        elif ret == self.DADOS_CORROMPIDOS:
          texto = _("Database corrupted or invalid password!")
        QMessageBox.warning(None, " ", texto)
        self.back()
    elif id == 3:
      # TODO garantir que pode criar o arquivo!
      fn = str(self.field("filename").toString())
      # verifica se é possível criar o arquivo novo


  def createWelcome(self):
    page = QWizardPage(self)

    label = QLabel(_("This wizard will guide you through the upgrading process.\n\nThe database will be converted to the new format."))
    label.setWordWrap(True)

    layout = QVBoxLayout()
    layout.addWidget(label)
    page.setLayout(layout)

    return page


  def createPassword(self):
    page = QWizardPage(self)

    label = QLabel(_("Type your current password"), page)
    label.setWordWrap(True)

    password = QLineEdit(page)
    password.setEchoMode(QLineEdit.Password)
    page.registerField("password*", password)

    layout = QVBoxLayout()
    layout.addWidget(label)
    layout.addWidget(password)

    page.setLayout(layout)

    return page


  def createFilename(self):
    page = QWizardPage(self)

    label = QLabel(_("Enter the database name and location"), page)
    label.setWordWrap(True)

    button = QPushButton("")
    button.setIcon(util.getIcon("file-open.png"))
    button.clicked.connect(self.file_button_clicked)

    filename = QLineEdit()
    page.registerField("filename*", filename)

    layout = QVBoxLayout()
    layout.addWidget(label)
    layout2 = QHBoxLayout()
    layout2.addWidget(filename)
    layout2.addWidget(button)
    layout.addLayout(layout2)

    page.setLayout(layout)

    return page


  def file_button_clicked(self):
    dialog = QFileDialog(self)
    (directory, filename) = os.path.split(str(self.field("filename").toString()))
    dialog.setDirectory(directory)
    dialog.selectFile(filename)
    if dialog.exec_():
      ls = dialog.selectedFiles()
      self.setField("filename", ls[0])


  def __loadOld(self):
    pwd = str(self.field("password").toString())
    crypt = Blowfish.new(pwd)
    md5 = MD5.new()

    # le o arquivo compactado
    try:
      arch = gzip.GzipFile(os.path.join(os.path.expanduser('~'), "MyDocs", "pysafe.db"), 'rb')
    except IOError:
      return self.ARQUIVO_NAO_LOCALIZADO
    buffer = ""
    while True:
      data = arch.read()
      if data == "":
        break
      buffer += data
    arch.close()

    # teoricamente, descriptografa ele
    dados_tmp = crypt.decrypt(buffer)
    # valida a senha...segurança para saber se a senha é realmente válida
    # e as informações podem ser descriptografadas corretamente
    pos = dados_tmp.find("\n")
    if pos == -1:
      return self.SENHA_INVALIDA
    senha = dados_tmp[:pos]
    if senha != pwd:
      return self.SENHA_INVALIDA

    # chegou aqui, a senha confere...pode apagar!
    dados_tmp = dados_tmp[pos + 1:]

    version = 0
    if dados_tmp[:1] == "V":
      # temos a versão no arquivo!
      pos = dados_tmp.find("\n")
      if pos == -1:
        return self.DADOS_CORROMPIDOS
      version = int(dados_tmp[1:pos])
      dados_tmp = dados_tmp[pos + 1:]

    # pega o MD5...
    pos = dados_tmp.find("\n")
    if pos == -1:
      return self.DADOS_CORROMPIDOS
    checksum = dados_tmp[:pos]

    # remove o checksum para criar efetivamente os dados
    dados_tmp = dados_tmp[pos + 1:].strip()
    md5.update(dados_tmp)

    if checksum != md5.hexdigest():
      return self.DADOS_CORROMPIDOS

    if version == 1:
      # é da versão anterior...converte para a versão nova!
      temp = pickle.loads(dados_tmp)
      for i in temp.keys():
        self.database_data["g%s" % i] = {}
        for j in temp[i]:
          self.database_data["g%s" % i]["i%s" % j] = {}
          for k in temp[i][j]:
            self.database_data["g%s" % i]["i%s" % j]["d0%s" % k] = temp[i][j][k]
    elif version == 2:
      self.database_data = pickle.loads(dados_tmp)

    return self.DATABASE_OK


  def __convertToDB(self, db, sublist, progress, parent = 0):
    for i in sublist:
      if i[:1] == "g":
        progress.setValue(progress.value() + 1)
        QApplication.processEvents()
        if progress.wasCanceled():
          return
        id = db.add_group(parent, i[1:])
        self.__convertToDB(db, sublist[i], progress, id)
      else:
        id = db.add_item(parent, i[1:])
        keys = sublist[i].keys()
        keys.sort(key=str.lower)
        for j in keys:
          progress.setValue(progress.value() + 1)
          QApplication.processEvents()
          if progress.wasCanceled():
            return
          id1 = db.add_detail(id, j[2:])
          db.set_detail(id1, sublist[i][j])


class NewSqlite(QWizard):

  def __init__(self, parent):
    QWizard.__init__(self, parent)

    self.database_data = {}

    self.currentIdChanged.connect(self.pageChanged)
    self.setWindowTitle(_("Setup Wizard"))

    self.addPage(self.createWelcome())
    self.addPage(self.createFilename())
    self.addPage(self.createNewPassword())
    self.addPage(self.createPassword())


  def initializePage(self, id):
    QWizard.initializePage(self, id)

    if id == 1:
      fn = str(self.field("filename").toString())
      if fn is None or len(fn) == 0:
        if os.path.exists(os.path.join(os.path.expanduser('~'), "MyDocs")):
          # estamos no N900, teoricamente!
          self.setField("filename", os.path.join(os.path.expanduser('~'), "MyDocs", "pysafe.sqlite"))
        else:
          self.setField("filename", os.path.join(os.path.expanduser('~'), "pysafe.sqlite"))


  def nextId(self):
    id = QWizard.nextId(self)
    if id == 2:
      fn = str(self.field("filename").toString())
      if os.path.exists(fn) and not self.field("overwrite").toBool():
        id = 3
    elif id == 3:
      id = -1
    return id


  def run(self):
    while True:
      if self.exec_() == 1:
        fn = str(self.field("filename").toString())
        ovw = self.field("overwrite").toBool()

        if os.path.exists(fn) and not ovw:
          pwd = str(self.field("password").toString())
          db = Dados(fn)
          ret = db.open(pwd)
          if ret != db.DATABASE_OK:
            texto = _("An undefined error has ocurred!")
            if ret == db.ARQUIVO_NAO_LOCALIZADO:
              texto = _("Database file not found. There was an error creating the database.")
            elif ret == db.SENHA_INVALIDA:
              texto = _("Invalid password!")
            elif ret == db.DADOS_CORROMPIDOS:
              texto = _("Database corrupted or invalid password!")
            QMessageBox.warning(None, " ", texto)
            continue

          return (fn, pwd)

        else:
          if self.field("password1") != self.field("password2"):
            QMessageBox.warning(None, " ", _("The passwords are not equals!"))
            continue

          pwd = str(self.field("password1").toString())

          if os.path.exists(fn):
            # remove o arquivo
            os.remove(fn)

          db = Dados(fn)
          db.createDB(pwd)

          return (fn, pwd)
      else:
        return None


  def pageChanged(self, id):
    # TODO garantir que pode criar o arquivo!
    if id == 3:
      if self.field("password1") != self.field("password2"):
        QMessageBox.warning(None, " ", _("The passwords are not equals!"))
        self.back()


  def createWelcome(self):
    page = QWizardPage()

    label = QLabel(_("This wizard will guide you through the setup process."))
    label.setWordWrap(True)

    layout = QVBoxLayout()
    layout.addWidget(label)
    page.setLayout(layout)

    return page


  def createNewPassword(self):
    page = QWizardPage()

    label1 = QLabel(_("Type your password"), page)
    label1.setWordWrap(True)

    label2 = QLabel(_("Retype your password"), page)
    label2.setWordWrap(True)

    password1 = QLineEdit(page)
    password1.setEchoMode(QLineEdit.Password)
    page.registerField("password1*", password1)

    password2 = QLineEdit(page)
    password2.setEchoMode(QLineEdit.Password)
    page.registerField("password2*", password2)

    layout = QVBoxLayout()
    layout.addWidget(label1)
    layout.addWidget(password1)
    layout.addSpacing(10)
    layout.addWidget(label2)
    layout.addWidget(password2)

    page.setLayout(layout)

    return page


  def createPassword(self):
    page = QWizardPage(self)

    label = QLabel(_("Type your current password"), page)
    label.setWordWrap(True)

    password = QLineEdit(page)
    password.setEchoMode(QLineEdit.Password)
    page.registerField("password*", password)

    layout = QVBoxLayout()
    layout.addWidget(label)
    layout.addWidget(password)

    page.setLayout(layout)

    return page


  def createFilename(self):
    page = QWizardPage()

    label = QLabel(_("Enter the database name and location"), page)
    label.setWordWrap(True)

    button = QPushButton("", page)
    button.setIcon(util.getIcon("file-open.png"))
    button.clicked.connect(self.file_button_clicked)

    filename = QLineEdit(page)
    page.registerField("filename*", filename)

    overwrite = QCheckBox(_("Overwrite"), page)
    page.registerField("overwrite", overwrite)

    label1 = QLabel(_("(if unchecked and the file exists will try to use it)"), page)
    label1.setWordWrap(True)

    layout = QVBoxLayout()
    layout.addWidget(label)
    layout2 = QHBoxLayout()
    layout2.addWidget(filename)
    layout2.addWidget(button)
    layout.addLayout(layout2)
    layout.addWidget(overwrite)
    layout.addWidget(label1)

    page.setLayout(layout)

    return page


  def file_button_clicked(self):
    dialog = QFileDialog(self)
    (directory, filename) = os.path.split(str(self.field("filename").toString()))
    dialog.setDirectory(directory)
    dialog.selectFile(filename)
    if dialog.exec_():
      ls = dialog.selectedFiles()
      self.setField("filename", ls[0])
