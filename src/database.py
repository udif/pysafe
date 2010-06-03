# -*- coding: utf-8 -*-
import pdb
import os
import sqlite3
import sys
from Crypto.Cipher import Blowfish

"""
Esta classe mantém as informações sobre os itens (grupos e seus itens internos)
Também salva e carrega do arquivo
"""
class Dados:

  __VERSION = 2

  __FIELD_PASSWORD = -1

  DATABASE_OK = 0
  ARQUIVO_NAO_LOCALIZADO = 1
  SENHA_INVALIDA = 2
  DADOS_CORROMPIDOS = 3
  SOMENTE_LEITURA = 4

  def __init__(self, db):
    self.__connection = None
    self.__blowfish = None
    self.__databaseFile = db
    self.__readonly = False
    self.__inTransaction = False

    print "Database location: %s" % (db)


  def open(self, pwd):
    if not os.path.exists(self.__databaseFile):
      return self.ARQUIVO_NAO_LOCALIZADO

    # é um banco sqlite?
    self.__connection = sqlite3.connect(self.__databaseFile)
    self.__connection.text_factory = str
    try:
      self.__connection.cursor().execute("PRAGMA quick_check")
    except sqlite3.DatabaseError:
      return self.DADOS_CORROMPIDOS

    # cria o objeto para criptografia
    self.__blowfish = Blowfish.new(pwd)

    # valida a senha
    c = self.__connection.cursor()
    r = c.execute("select value from info where parent = ?", (self.__FIELD_PASSWORD,)).fetchone()
    if r is None:
      return self.DADOS_CORROMPIDOS
    (p, ) = r

    if self.__decrypt(p) != pwd:
      self.__connection.close()
      return self.SENHA_INVALIDA

    # verifica se é a última versão do banco de dados
    self.__checkVersion(c)

    # verifica se pode alterar dados (banco somente leitura)
    try:
      c.execute("delete from V%i" % self.__VERSION)
    except sqlite3.OperationalError:
      self.__readonly = True

    c.close()

    if self.__readonly:
      return self.SOMENTE_LEITURA
    else:
      return self.DATABASE_OK


  def close(self):
    self.__connection.close()


  def isReadOnly(self):
    return self.__readonly


  def __encrypt(self, txt, bf):
    if bf is not None and txt is not None and len(txt) > 0:
      tmp = "%i;%s" % (len(txt), txt)
      pad_bytes = 8 - (len(tmp) % 8)
      while pad_bytes > 0:
        tmp = "%s " % tmp
        pad_bytes -= 1
      tmp = bf.encrypt(tmp)
      return tmp.encode("hex")
    else:
      return txt


  def __decrypt(self, txt):
    if self.__blowfish is not None and txt is not None and len(txt) > 0:
      tmp = self.__blowfish.decrypt(txt.decode("hex"))
      p = tmp.find(";")
      l = 0
      try:
        l = int(tmp[:p])
      except ValueError:
        return None
      tmp = tmp[p + 1:p + l + 1]
      return tmp
    else:
      return txt


  def __checkVersion(self, c):
    (row,) = c.execute("SELECT name from sqlite_master WHERE name like 'V%'").fetchone()
    if "V%i" % self.__VERSION == row:
      return

    # altera as tabelas conforme a versão atual
    if row == "V1":
      c.execute("alter table info add column timestamp integer")

    # coloca a versão correta na tabela
    c.execute("alter table %s rename to 'V%i'" % (row, self.__VERSION))


  def createDB(self, pwd):
    connection = sqlite3.connect(self.__databaseFile)
    c = connection.cursor()
    c.execute("create table V%i (nothing integer primary key)" % self.__VERSION)
    c.execute("create table info (id integer primary key, parent integer, type text, pos long, label text, value text, timestamp integer)")
    self.__blowfish = Blowfish.new(pwd)
    c.execute("insert into info (parent, value) values (?, ?)", (self.__FIELD_PASSWORD, self.__encrypt(pwd, self.__blowfish)))
    self.__blowfish = None
    connection.commit()
    c.close()
    connection.close()


  def changePassword(self, newpwd, progress = None):
    if self.__readonly:
      return False

    # cria o blowfish para a nova senha
    newbf = Blowfish.new(newpwd)

    c = self.__connection.cursor()
    ret = True
    try:
      rows = c.execute("select id, parent, label, value from info").fetchall()

      for r in rows:
        if progress is not None:
          if progress.updateProgressBar(len(rows)):
            ret = False
            break
        (id, parent, label, value) = r
        l1 = self.__decrypt(label)
        l2 = self.__encrypt(l1, newbf)
        if parent == self.__FIELD_PASSWORD:
          # o caso da senha deve ser diferente, pois não devo criptografar
          # a senha antiga, mas sim a nova!!
          v2 = self.__encrypt(newpwd, newbf)
        else:
          v1 = self.__decrypt(value)
          v2 = self.__encrypt(v1, newbf)
        c.execute("update info set label = ?, value = ? where id = ?", (l2, v2, id))

      if ret:
        self.__connection.commit()
      else:
        self.__connection.rollback()
    except:
      # se deu qualquer erro, cancela tudo!
      print "Error:", sys.exc_info()
      self.__connection.rollback()
      ret = False
    c.close()

    # se alterou com sucesso, fecha o banco e abre de novo
    if ret:
      self.close()
      self.open(newpwd)

    return ret


  def get(self, parent = 0):
    ret = []

    c = self.__connection.cursor()
    c.execute("select id, type, pos, label, value from info where parent = ? order by pos", (parent,))
    while True:
      r = c.fetchone()
      if r is None:
        break
      (d1, d2, d3, d4, d5) = r
      r = (d1, d2, d3, self.__decrypt(d4), self.__decrypt(d5))
      ret.append(r)
    c.close()
    return ret


  def getCurrent(self, id = 0):
    c = self.__connection.cursor()
    c.execute("select id, type, pos, label, value, parent from info where id = ? order by pos", (id,))
    ret = c.fetchone()
    (d1, d2, d3, d4, d5, d6) = ret
    ret = (d1, d2, d3, self.__decrypt(d4), self.__decrypt(d5), d6)
    c.close()
    return ret


  def __add_element(self, parent, tipo, name, value = "", pos = 0):
    if self.__readonly:
      return None

    c = self.__connection.cursor()
    if tipo == "d":
      # busca a maior posição...
      (pos, ) = c.execute("select max(pos) from info where parent = ?", (parent,)).fetchone()
      if pos == None:
        pos = 0
      else:
        pos += 1

    c.execute("insert into info (parent, type, pos, label, value, timestamp) values (?,?,?,?,?,strftime('%s','now'))", (parent, tipo, pos, self.__encrypt(name, self.__blowfish), self.__encrypt(value, self.__blowfish), ))
    id = c.lastrowid
    if not self.__inTransaction:
      self.__connection.commit()
    c.close()
    return id


  def __removeElement(self, id, cursor = None):
    if self.__readonly:
      return

    commit = cursor is None
    if commit:
      cursor = self.__connection.cursor()

    # pega os possíveis filhos deste registro
    rows = cursor.execute("select id from info where parent = ?", (id,)).fetchall()
    # e manda apagar também!
    for el in rows:
      (i,) = el
      self.__removeElement(i, cursor)

    # altera o posicionamento se for detalhe
    (parent, pos, tipo,) = cursor.execute("select parent, pos, type from info where id = ?", (id,)).fetchone()
    if tipo == "d":
      cursor.execute("update info set pos = pos - 1 where parent = ? and pos > ?", (parent, pos,))

    # remove o registro
    cursor.execute("delete from info where id = ?", (id,))

    # marca o "pai" como alterado
    cursor.execute("update info set timestamp = strftime('%s','now') where id = ?", (parent,))

    # deve fazer o commit e fechar o cursor?
    if commit:
      self.__connection.commit()
      cursor.close()


  def add_group(self, id, name):
    # grupos só podem ser adicionados a grupos....portanto
    # busca o primeiro ID pai que não seja um grupo
    parent = 0
    while id > 0:
      tmp = self.getCurrent(id)
      if tmp is not None:
        (id, tipo, pos, label, value, parent) = tmp
        if tipo == "g":
          parent = id
          break
        elif parent == 0:
          break

    id = self.__add_element(parent, "g", name)
    return id


  def delItem(self, id):
    self.__removeElement(id)


  def add_item(self, id, name):
    # itens só podem ser adicionados a grupos....portanto
    # busca o primeiro ID pai que não seja um item
    parent = id
    while parent > 0:
      tmp = self.getCurrent(id)
      if tmp is None:
        parent = 0
      else:
        (id1, tipo, pos, label, value, parent1) = tmp
        if tipo == "g":
          break
        else:
          parent = parent1

    id = self.__add_element(parent, "i", name)
    return id


  def add_detail(self, parent, name):
    return self.__add_element(parent, "d", name)


  def del_detail(self, id):
    self.__removeElement(id)


  def set_detail(self, id, value = ""):
    if self.__readonly:
      return

    c = self.__connection.cursor()
    c.execute("update info set value = ?, timestamp = strftime('%s','now') where id = ?", (self.__encrypt(value, self.__blowfish), id))
    if not self.__inTransaction:
      self.__connection.commit()
    c.close()


  def moveDetail(self, id, dir):
    if self.__readonly:
      return None

    c = self.__connection.cursor()

    c.execute("select pos, parent, type from info where id = ?", (id,))
    tmp = c.fetchone()
    if tmp is None:
      c.close()
      return None
    (pos, parent, tipo) = tmp

    posNew = pos + dir

    # busca pelo registro que este vai deslocar
    c.execute("select id from info where parent = ? and type = ? and pos = ?", (parent, tipo, posNew,))
    tmp = c.fetchone()
    if tmp is None:
      c.close()
      return None
    (idNew, ) = tmp

    # troca as posições
    c.execute("update info set pos = ? where id = ?", (posNew, id,))
    c.execute("update info set pos = ? where id = ?", (pos, idNew,))

    self.__connection.commit()
    c.close()

    return id


  def rename(self, id, label):
    if self.__readonly:
      return

    c = self.__connection.cursor()
    c.execute("update info set label = ?, timestamp = strftime('%s','now') where id = ?", (self.__encrypt(label, self.__blowfish), id,))
    self.__connection.commit()
    c.close()


  def beginTransaction(self):
    self.__inTransaction = True


  def commitTransaction(self):
    if self.__inTransaction:
      self.__inTransaction = False
      self.__connection.commit()


  def rollbackTransaction(self):
    if self.__inTransaction:
      self.__inTransaction = False
      self.__connection.rollback()
