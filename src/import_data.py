# -*- coding: utf-8 -*-
#import gettext, sys, pickle
import os
import xml_util
import sys
import tempfile
from database import Dados

from PyQt4.QtGui import *
from PyQt4.QtCore import *


def convert_to_str(value):
  if type(value) is unicode:
    return value.encode("utf-8")
  return value


class ImportWizard(QWizard):

  def __init__(self, parent, database):
    QWizard.__init__(self, parent)

    self.import_type = QListView()
    self.filetype = None

    self.currentIdChanged.connect(self.pageChanged)
    self.setWindowTitle(_("Import Wizard"))

    self.addPage(self.createWelcome())
    self.addPage(self.createFileName())
    self.addPage(self.createFileType())

    while self.exec_():
      if self.filetype != None and type(self.filetype) is int:
        import_from_file(database, self.field("filename").toString(), self.filetype)
        break


  def pageChanged(self, id):
    if id == 2:
      f = str(self.field("filename").toString()).strip()
      if len(f) == 0:
        self.back()
      if not os.path.isfile(f):
        QMessageBox.warning(None, " ", _("File \"%s\" does not exist or it was not possible open it.") % f)
        self.back()


  def createWelcome(self):
    page = QWizardPage()

    label = QLabel(_("This wizard will guide you through the importing process."))
    label.setWordWrap(True)

    layout = QVBoxLayout()
    layout.addWidget(label)
    page.setLayout(layout)

    return page


  def createFileName(self):
    page = QWizardPage()

    button = QPushButton("")
    button.setIcon(QIcon('%s/icons/file-open.png' % (sys.path[0])))
    button.clicked.connect(self.file_button_clicked)

    filename = QLineEdit()
    page.registerField("filename*", filename)

    layout = QHBoxLayout()
    layout.addWidget(filename)
    layout.addWidget(button)

    page.setLayout(layout)

    return page


  def createFileType(self):
    page = QWizardPage()

    self.import_type.clicked.connect(self.groupListClicked)
    model = QStandardItemModel()
    self.import_type.setModel(model)
    parent = model.invisibleRootItem()

    tipos = import_from_file.get_types()
    for i in tipos:
      item = GroupListItem(tipos[i], i)
      parent.appendRow(item)

    layout = QHBoxLayout()
    layout.addWidget(self.import_type)

    page.setLayout(layout)

    return page


  def file_button_clicked(self):
    dialog = QFileDialog(self)
    dialog.setViewMode(QFileDialog.List)
    dialog.setReadOnly(True)
    dialog.setNameFilterDetailsVisible(False)
    if dialog.exec_():
      ls = dialog.selectedFiles()
      self.setField("filename", ls[0])


  def groupListClicked(self, index):
    model = self.import_type.model()
    item = model.itemFromIndex(index)
    self.filetype = item.getId()


class GroupListItem(QStandardItem):

  def __init__(self, text, id):
    QStandardItem.__init__(self, text)

    self.__text = text
    self.__id = id

  def getId(self):
    return self.__id


class import_from_file:

  (HANDY_SAFE_PRO_TEXT, HANDY_SAFE_PRO_XML, PALM_KEYRING_XML, KEEPASSX_XML) = range(4)

  """
    database - database instance
    file_name - file name
    file_format - file format
  """
  def __init__(self, database, file_name, file_format):
    if not os.path.isfile(file_name):
      raise IOError, _("File \"%s\" does not exist or it was not possible open it.") % file_name

    if type(file_name) is not str:
      file_name = str(file_name)

    if file_format == self.HANDY_SAFE_PRO_TEXT:
      handy_safe_pro_text(database, file_name)
    elif file_format == self.HANDY_SAFE_PRO_XML:
      handy_safe_pro_xml(database, file_name)
    elif file_format == self.PALM_KEYRING_XML:
      palm_keyring_xml(database, file_name)
    elif file_format == self.KEEPASSX_XML:
      keepassx_xml(database, file_name)
    else:
      raise AttributeError, _("The file format parameter was not recognized.")


  @staticmethod
  def get_types():
    ret = {import_from_file.HANDY_SAFE_PRO_TEXT: _("Handy Safe Pro (text)"),
           import_from_file.HANDY_SAFE_PRO_XML: _("Handy Safe Pro (xml)"),
           import_from_file.KEEPASSX_XML: _("KeePassX (xml)"),
           import_from_file.PALM_KEYRING_XML: _("Keyring for PalmOS (xml)")}
    return ret

"""
Classe responsável por ler os dados de um arquivo texto.
"""
class handy_safe_pro_text:

  def __init__(self, database, file_name):
    file = open(file_name, "r")
    state = 0
    block = ""
    while True:
      line = convert_to_str(file.readline())
      if len(line) == 0:
        break

      # remove o fim de linha
      #line = line.rstrip("\n")

      # é vazio?
      if state != 2 and len(line.rstrip("\n")) == 0:
        continue

      # é uma categoria?
      if line[:10] == "[Category:":
        if state == 2:
          self.read_handy_safe_pro_text_block(database, block)
          block = ""

        state = 1
      elif line[:12] == "[Card, Icon:":
        if state == 2:
          self.read_handy_safe_pro_text_block(database, block)
          block = ""

        state = 1
      else:
        state = 2

      block = "%s%s" % (block, line)

    file.close()

    self.read_handy_safe_pro_text_block(database, block)


  def read_handy_safe_pro_text_block(self, database, block):
    # remove todos os linefeed do final, mas coloca um!
    block = "%s\n" % block.rstrip("\n")
    path = [0]
    item = None
    state = 0
    note = ""
    while len(block) > 0:
      pos = block.find("\n")
      l = block[:pos + 1]
      block = block[pos + 1:]

      if l[:10] == "[Category:":
        l = l.rstrip("\n").strip()
        g = database.add_group(path[-1], l[11:len(l) - 1])
        path.append(g)
      elif l[:12] == "[Card, Icon:":
        state = 1
      elif state == 1:
        pos = l.find(":")
        i = database.add_item(path[-1], l[pos + 1:].strip())
        path.append(i)
        state = 2
      elif state == 2:
        pos = l.find(":")
        detail_name = l[:pos]
        detail_value = l[pos + 1:]
        if detail_name == "Note":
          l = detail_value
          state = 3
        else:
          detail_value = detail_value.rstrip("\n").strip()
          if len(detail_value) > 0:
            id = database.add_detail(path[-1], detail_name)
            database.set_detail(id, detail_value)

      if state == 3:
        if len(l) > 0:
          note = "%s%s" % (note, l)

    note = note.rstrip("\n").strip()
    if len(note) > 0:
      id = database.add_detail(path[-1], _("Note"))
      database.set_detail(id, note)


"""
Classe responsável por ler os dados de um arquivo XML, no formato do Handy Safe Pro.
"""
class handy_safe_pro_xml:

  def __init__(self, database, file_name):
    data = xml_util.ConvertXmlToDict(file_name)
    self.read(database, data["HandySafe"])


  def read(self, database, data, path = [0]):
    for i in data:
      if type(data[i]) is list:
        for j in data[i]:
          if i == "Folder":
            id = database.add_group(path[-1], convert_to_str(j["name"]))
            path.append(id)
            self.read(database, j, path)
            path.pop()
          elif i == "Card":
            id = database.add_item(path[-1], convert_to_str(j["name"]))
            path.append(id)
            self.read_card(database, path, j)
            path.pop()
      elif type(data[i]) is dict:
        if i == "Card":
          id = database.add_item(path[-1], convert_to_str(data[i]["name"]))
          path.append(id)
          self.read_card(database, path, data[i])
          path.pop()
        elif i == "Folder":
          id = database.add_group(path[-1], convert_to_str(data[i]["name"]))
          path.append(id)
          self.read(database, data[i], path)
          path.pop()


  def read_card(self, database, path, data):
    name = data["name"]
    field = data["Field"]

    #item = database.add_item(path, data["name"], ignore_existent = True)
    #path.append(item)

    if type(field) is list:
      for i in field:
        if "_text" in i:
          id = database.add_detail(path[-1], convert_to_str(i["name"]))
          database.set_detail(id, convert_to_str(i["_text"]))
    elif type(field) is dict:
      if "_text" in field:
        id = database.add_detail(path[-1], convert_to_str(field["name"]))
        database.set_detail(id, convert_to_str(field["_text"]))
    if "Note" in data:
      id = database.add_detail(path[-1], _("Note"))
      database.set_detail(id, convert_to_str(data["Note"]))


"""
Classe responsável por ler os dados de um arquivo XML, no formato do Keyring para PalmOS.
"""
class palm_keyring_xml:

  def __init__(self, database, file_name):
    data = xml_util.ConvertXmlToDict(file_name)
    self.read(database, data["pwlist"])


  def read(self, database, data, path = [0]):
    for i in data:

      if type(data[i]) is list:
        for j in data[i]:
          id = database.add_group(path[-1], convert_to_str(j["category"]))
          path.append(id)
          self.read_item(database, path, j)
          path.pop()


  def read_item(self, database, path, data):
    id = database.add_item(path[-1], convert_to_str(data["title"]))
    path.append(id)

    for i in data:
      if i == "title" or i == "category":
        continue
      elif i == "notes":
        id = database.add_detail(path[-1], _("Note"))
        database.set_detail(id, convert_to_str(data[i]))
      else:
        id = database.add_detail(path[-1], convert_to_str(i))
        database.set_detail(id, convert_to_str(data[i]))

    path.pop()


"""
Classe responsável por ler os dados de um arquivo XML, no formato do Keyring para PalmOS.
"""
class keepassx_xml:

  def __init__(self, database, file_name):
    file = open(file_name, "r")
    buffer = ""
    while True:
      data = file.read()
      if data == "":
        break
      buffer += data
    file.close()

    buffer = buffer.replace("<br/>", "\n")

    tmp = tempfile.NamedTemporaryFile(mode="w+b")
    tmp.write(buffer)
    tmp.flush()
    data = xml_util.ConvertXmlToDict(tmp.name)
    tmp.close()
    self.read(database, data["database"])


  def read(self, database, data, path = [0]):
    for i in data:

      if type(data[i]) is list:
        for j in data[i]:
          if i == "group":
            id = database.add_group(path[-1], convert_to_str(j["title"]))
            path.append(id)
            self.read(database, j, path)
            path.pop()
          elif i == "entry":
            id = database.add_item(path[-1], convert_to_str(j["title"]))
            path.append(id)
            self.read_card(database, path, j)
            path.pop()
      elif type(data[i]) is dict:
        if i == "group":
          id = database.add_group(path[-1], convert_to_str(data[i]["title"]))
          path.append(id)
          self.read(database, data[i], path)
          path.pop()
        elif i == "entry":
          id = database.add_item(path[-1], convert_to_str(data[i]["title"]))
          path.append(id)
          self.read_card(database, path, data[i])
          path.pop()


  def read_card(self, database, path, data):
    for i in data:
      if i != "creation" and i != "expire" and i != "lastmod" and i != "lastaccess" and i != "icon":
        tmp = convert_to_str(data[i])
        if len(tmp.strip()) > 0:
          id = database.add_detail(path[-1], convert_to_str(i))
          database.set_detail(id, tmp)

# apenas para testes
#gettext.install('pysafe', sys.path[0])
#database = Dados("q")
#import_from_file(database, "/home/aguilar/pySafe/keepassx.xml", import_from_file.KEEPASSX_XML)
#database.save(True)
