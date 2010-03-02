# -*- coding: utf-8 -*-
#import gettext, sys, pickle
import os
import xml_util
import tempfile
from database import Dados


def convert_to_str(value):
  if type(value) is unicode:
    return value.encode("utf-8")
  return value


class import_from_file:

  (HANDY_SAFE_PRO_TEXT, HANDY_SAFE_PRO_XML, PALM_KEYRING_XML, KEEPASSX_XML) = range(4)

  """
    database - database instance
    file_name - file name
    file_format - file format
  """
  def __init__(self, database, file_name, file_format):
    if not os.path.isfile(file_name):
      raise IOError, _("File %s does not exist or it was not possible open it.") % file_name

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
    path = []
    item = None
    state = 0
    note = ""
    while len(block) > 0:
      pos = block.find("\n")
      l = block[:pos + 1]
      block = block[pos + 1:]

      if l[:10] == "[Category:":
        l = l.rstrip("\n").strip()
        g = database.add_group(path, l[11:len(l) - 1], ignore_existent = True)
        path.append(g)
      elif l[:12] == "[Card, Icon:":
        state = 1
      elif state == 1:
        pos = l.find(":")
        i = database.add_item(path, l[pos + 1:].strip(), ignore_existent = True)
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
            detail_name = database.add_detail(path, detail_name, ignore_existent = True)
            database.set_detail(path, detail_name, detail_value)

      if state == 3:
        if len(l) > 0:
          note = "%s%s" % (note, l)

    note = note.rstrip("\n").strip()
    if len(note) > 0:
      detail = database.add_detail(path, _("Note"), ignore_existent = True)
      database.set_detail(path, detail, note)


"""
Classe responsável por ler os dados de um arquivo XML, no formato do Handy Safe Pro.
"""
class handy_safe_pro_xml:

  def __init__(self, database, file_name):
    data = xml_util.ConvertXmlToDict(file_name)
    self.read(database, data["HandySafe"])


  def read(self, database, data, path = []):
    for i in data:
      print "%s.%s (%i) = %s" % (path, i, len(data[i]), type(data[i]))

      if type(data[i]) is list:
        for j in data[i]:
          if i == "Folder":
            group = database.add_group(path, convert_to_str(j["name"]), ignore_existent = True)
            path.append(group)
            self.read(database, j, path)
            path.pop()
          elif i == "Card":
            item = database.add_item(path, convert_to_str(j["name"]), ignore_existent = True)
            path.append(item)
            self.read_card(database, path, j)
            path.pop()
      elif type(data[i]) is dict:
        if i == "Card":
          item = database.add_item(path, convert_to_str(data[i]["name"]), ignore_existent = True)
          path.append(item)
          self.read_card(database, path, data[i])
          path.pop()
        elif i == "Folder":
          group = database.add_group(path, convert_to_str(data[i]["name"]), ignore_existent = True)
          path.append(group)
          self.read(database, data[i], path)
          path.pop()


  def read_card(self, database, path, data):
    name = data["name"]
    field = data["Field"]

    #item = database.add_item(path, data["name"], ignore_existent = True)
    #path.append(item)

    print "---------- %s.%s" % (path, name)
    for i in field:
      if "_text" in i:
        detail = database.add_detail(path, convert_to_str(i["name"]), ignore_existent = True)
        print "%s = \"%s\"" % (detail, i["_text"])
        database.set_detail(path, detail, convert_to_str(i["_text"]))
    if "Note" in data:
      detail = database.add_detail(path, _("Note"), multiline = True, ignore_existent = True)
      print "%s = \"%s\"" % (detail, data["Note"])
      database.set_detail(path, detail, convert_to_str(data["Note"]))
    print ""


"""
Classe responsável por ler os dados de um arquivo XML, no formato do Keyring para PalmOS.
"""
class palm_keyring_xml:

  def __init__(self, database, file_name):
    data = xml_util.ConvertXmlToDict(file_name)
    self.read(database, data["pwlist"])


  def read(self, database, data, path = []):
    for i in data:
      print "%s.%s (%i) = %s" % (path, i, len(data[i]), type(data[i]))

      if type(data[i]) is list:
        for j in data[i]:
          group = database.add_group(path, convert_to_str(j["category"]), ignore_existent = True)
          path.append(group)
          self.read_item(database, path, j)
          path.pop()


  def read_item(self, database, path, data):
    item = database.add_item(path, convert_to_str(data["title"]), ignore_existent = True)
    path.append(item)

    print "---------- %s" % (path)
    for i in data:
      if i == "title" or i == "category":
        continue
      elif i == "notes":
        ml = (data[i].find("\n") > 0)
        detail = database.add_detail(path, _("Note"), multiline = ml, ignore_existent = True)
        print "%s = \"%s\"" % (detail, data[i])
        database.set_detail(path, detail, convert_to_str(data[i]))
      else:
        detail = database.add_detail(path, convert_to_str(i), ignore_existent = True)
        print "%s = \"%s\"" % (detail, data[i])
        database.set_detail(path, detail, convert_to_str(data[i]))
    print ""

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


  def read(self, database, data, path = []):
    for i in data:
      print "%s.%s (%i) = %s" % (path, i, len(data[i]), type(data[i]))

      if type(data[i]) is list:
        for j in data[i]:
          if i == "group":
            group = database.add_group(path, convert_to_str(j["title"]), ignore_existent = True)
            path.append(group)
            self.read(database, j, path)
            path.pop()
          elif i == "entry":
            item = database.add_item(path, convert_to_str(j["title"]), ignore_existent = True)
            path.append(item)
            self.read_card(database, path, j)
            path.pop()
      elif type(data[i]) is dict:
        if i == "group":
          group = database.add_group(path, convert_to_str(data[i]["title"]), ignore_existent = True)
          path.append(group)
          self.read(database, data[i], path)
          path.pop()
        elif i == "entry":
          item = database.add_item(path, convert_to_str(data[i]["title"]), ignore_existent = True)
          path.append(item)
          self.read_card(database, path, data[i])
          path.pop()


  def read_card(self, database, path, data):
    print "---------- %s" % (path)
    for i in data:
      if i != "creation" and i != "expire" and i != "lastmod" and i != "lastaccess" and i != "icon":
        tmp = convert_to_str(data[i])
        if len(tmp.strip()) > 0:
          ml = (tmp.find("\n") > 0)
          detail = database.add_detail(path, convert_to_str(i), multiline = ml, ignore_existent = True)
          print "%s = \"%s\"" % (detail, data[i])
          database.set_detail(path, detail, tmp)
    print ""

# apenas para testes
#gettext.install('pysafe', sys.path[0])
#database = Dados("q")
#import_from_file(database, "/home/aguilar/pySafe/keepassx.xml", import_from_file.KEEPASSX_XML)
#database.save(True)
