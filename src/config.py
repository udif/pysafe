# -*- coding: utf-8 -*-
import ConfigParser
import os


class Configuration:

  VERSION = 0
  PORTRAIT_SLIDER_SIZE = 1
  LANDSCAPE_SLIDER_SIZE = 2
  DATABASE_FILE = 3

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

    # verifica a versão
    if not self.__config.has_option('General', 'version'):
      self.__config.set('General', 'version', '0')


  def get(self, item):
    if item == self.PORTRAIT_SLIDER_SIZE:
      return self.__config.getint('Window', 'portrait_slider')
    elif item == self.LANDSCAPE_SLIDER_SIZE:
      return self.__config.getint('Window', 'landscape_slider')
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
    elif item == self.DATABASE_FILE:
      self.__config.set('General', 'dbfile', value)
    elif item == self.VERSION:
      self.__config.set('General', 'version', value)

    self.__save()
