# -*- coding: utf-8 -*-
import gobject
import pickle
import gzip
import os
from Crypto.Cipher import Blowfish
from Crypto.Hash import MD5

"""
Esta classe mantém as informações sobre os itens (grupos e seus itens internos)
Também salva e carrega do arquivo
"""
class Dados:

  VERSION = 2

  DATABASE_OK = 0
  ARQUIVO_NAO_LOCALIZADO = 1
  SENHA_INVALIDA = 2
  DADOS_CORROMPIDOS = 3

  def __init__(self, p, db = "%s/MyDocs/pysafe.db" % (os.path.expanduser('~'))):
    self.password = p
    self.database_file = db
    self.changed = False
    self.dados = {}
    self.version = 1
    #print "Database location: %s" % (db)


  def load(self):
    crypt = Blowfish.new(self.password)
    md5 = MD5.new()

    # le o arquivo compactado
    try:
      arch = gzip.GzipFile(self.database_file, 'rb')
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
    if senha != self.password:
      return self.SENHA_INVALIDA

    # chegou aqui, a senha confere...pode apagar!
    dados_tmp = dados_tmp[pos + 1:]

    if dados_tmp[:1] == "V":
      # temos a versão no arquivo!
      pos = dados_tmp.find("\n")
      if pos == -1:
        return self.DADOS_CORROMPIDOS
      self.version = int(dados_tmp[1:pos])
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

    self.load_data(dados_tmp)

    return self.DATABASE_OK


  def save(self, force = False, new_pass = None):
    if force == False and self.changed == False:
      return True

    if new_pass != None:
      self.password = new_pass

    crypt = Blowfish.new(self.password)
    md5 = MD5.new()

    # serializa os dados
    dados_tmp = pickle.dumps(self.dados, 1)
    # cria o MD5 deles
    md5.update(dados_tmp)
    # acrescenta a senha e o checksum
    dados_tmp = "%s\nV%i\n%s\n%s" % (self.password, self.VERSION, md5.hexdigest(), dados_tmp)
    # criptografa!
    dados_tmp = crypt.encrypt(self.__fillWithSpace(dados_tmp))

    # salva o arquivo compactado
    try:
      arch = gzip.GzipFile(self.database_file, "wb")
    except IOError:
      return False
    arch.write(dados_tmp)
    arch.close()
    return True


  def __fillWithSpace(self, s):
    while len(s) % 8 != 0:
      s = "%s " % (s)
    return s


  def load_data(self, t):
    if self.version == 1:
      # é da versão anterior...converte para a versão nova!
      temp = pickle.loads(t)
      for i in temp.keys():
        self.dados["g%s" % i] = {}
        for j in temp[i]:
          self.dados["g%s" % i]["i%s" % j] = {}
          for k in temp[i][j]:
            self.dados["g%s" % i]["i%s" % j]["d0%s" % k] = temp[i][j][k]
      # informa que alterou para que seja salvo ao sair!
      self.changed = True
    elif self.version == 2:
      self.dados = pickle.loads(t)


  def get(self, path = [], sublist = None):
    if sublist == None:
      sublist = self.dados
    if path == None or len(path) == 0:
      ret = []
      for i in sublist:
        ret.append(i)
      return ret
    else:
      if path[0][:1] == "i":
        return self.get_details(sublist[path[0]])
      else:
        return self.get(path[1:], sublist[path[0]])


  def get_details(self, sublist = None):
    ret = {}
    for i in sublist:
      ret[i] = sublist[i]
    return ret


  def __add_element(self, path, name):
    temp = self.dados
    i = 0
    while i < len(path) and path[i][:1] == "g":
      temp = temp[path[i]]
      i = i + 1
    #print "__add_element: %s" % name
    temp[name] = {}


  def add_group(self, path, name, ignore_existent = False):
    name = "g%s" % name

    # grupos só podem ser adicionados a grupos....portanto
    # remove do path tudo que não seja um grupo!
    temp = []
    for i in path:
      if i[:1] == "g":
        temp.append(i)

    if name in self.get(temp):
      if ignore_existent:
        return name
      return None

    self.__add_element(temp, name)
    self.changed = True
    return name


  def del_group(self, path):
    temp = self.dados
    i = 0
    while i < len(path) - 1 and path[i][:1] == "g":
      temp = temp[path[i]]
      i = i + 1
    del temp[path[i]]
    self.changed = True


  def add_item(self, path, name, ignore_existent = False):
    name = "i%s" % name

    # itens só podem ser adicionados a grupos....portanto
    # remove do path tudo que não seja um grupo!
    temp = []
    for i in path:
      if i[:1] == "g":
        temp.append(i)

    if name in self.get(temp):
      if ignore_existent:
        return name
      return None

    self.__add_element(temp, name)
    self.changed = True
    return name


  def del_item(self, path):
    temp = self.dados
    i = 0
    while i < len(path) and path[i][:1] != "i":
      temp = temp[path[i]]
      i = i + 1
    if path[-1] in temp:
      del temp[path[-1]]
      self.changed = True


  def add_detail(self, path, name, multiline = False, ignore_existent = False):
    if multiline:
      name = "d1%s" % name
    else:
      name = "d0%s" % name

    if name in self.get(path):
      if ignore_existent:
        return name
      return None

    self.set_detail(path, name)
    return name


  def del_detail(self, path, name):
    self.changed = True

    temp = self.dados
    i = 0
    while i < len(path):
      temp = temp[path[i]]
      i = i + 1
    del temp[name]


  def set_detail(self, path, name, value = ""):
    self.changed = True

    temp = self.dados
    i = 0
    while i < len(path):
      temp = temp[path[i]]
      i = i + 1
    temp[name] = value
