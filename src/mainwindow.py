# -*- coding: utf-8 -*-
import gettext
import os
import sys
import util
import tempfile
from rotation import FremantleRotation
from database import Dados
from config import Configuration

from PyQt4.QtGui import *
from PyQt4.QtCore import *

VERSION = "PYSAFE_VERSION"


"""
Classe responsável pela exibição da tela principal do aplicativo
"""
class MainWindow(QMainWindow):

  DETAIL_ALL_VIEW = 1
  DETAIL_EDIT_VIEW = 2
  DETAIL_ONE_VIEW = 3

  def __init__(self, cfg, parent = None):
    QMainWindow.__init__(self, parent)

    self.selectedItem = None
    self.database = None
    self.config = cfg
    self.lastWidgetWithFocus = None
    self.detailView = self.DETAIL_ALL_VIEW

    # define propriedades da janela
    self.setWindowTitle("pySafe")
    self.setWindowIcon(util.getIcon("pysafe_48x48.png"))

    # adiciona o menu
    self.__create_menu()

    # cria o widget central
    centralwidget = QWidget()
    self.setCentralWidget(centralwidget)


    # cria o treeview e o modelo
    listwidget = QWidget()
    self.groupList = TreeView(listwidget, self.setLastWidgetWithFocus, self.rename)
    self.groupList.setModel(StandardItemModel())
    self.groupList.setHeaderHidden(True)
    self.groupList.clicked.connect(self.groupListClicked)

    # cria o painel para os detalhes
    detailwidget = QWidget()
    self.item_detail = QScrollArea(detailwidget)
    self.item_detail.setWidgetResizable(True)

    # cria a lista para a remocao de detalhes
    self.deleteDetailList = ListView(self.rename)
    self.deleteDetailList.clicked.connect(self.__menuButtonsCheck)
    self.deleteDetailList.setSelectionMode(QAbstractItemView.MultiSelection)
    self.deleteDetailList.setModel(StandardItemModel())

    # cria os botões da lista de grupos e itens
    self.add_group_button = QPushButton(util.getIcon("add-group.png"), "", listwidget)
    self.add_group_button.setMaximumSize(70, 70)
    self.add_group_button.clicked.connect(self.add_group_clicked)
    self.add_item_button = QPushButton(util.getIcon("add-item.png"), "", listwidget)
    self.add_item_button.setMaximumSize(70, 70)
    self.add_item_button.clicked.connect(self.add_item_clicked)
    self.del_item_group_button = QPushButton(util.getIcon("delete.png"), "", listwidget)
    self.del_item_group_button.setMaximumSize(70, 70)
    self.del_item_group_button.clicked.connect(self.del_group_item_clicked)

    # cria os botões para os detalhes
    self.find_button = Find(detailwidget, self.groupList, self.groupListClicked)
    self.find_button.setMaximumSize(70, 70)
    self.up_detail_button = QPushButton(util.getIcon("go-up.png"), "", detailwidget)
    self.up_detail_button.setMaximumSize(70, 70)
    self.up_detail_button.clicked.connect(self.up_detail_clicked)
    self.down_detail_button = QPushButton(util.getIcon("go-down.png"), "", detailwidget)
    self.down_detail_button.setMaximumSize(70, 70)
    self.down_detail_button.clicked.connect(self.down_detail_clicked)
    self.add_detail_button = QPushButton(util.getIcon("add-detail.png"), "", detailwidget)
    self.add_detail_button.setMaximumSize(70, 70)
    self.add_detail_button.clicked.connect(self.add_detail_clicked)
    self.del_detail_button = QPushButton(util.getIcon("edit.png"), "", detailwidget)
    self.del_detail_button.setMaximumSize(70, 70)
    self.del_detail_button.clicked.connect(self.del_detail_clicked)
    self.delete_detail_button = QPushButton(util.getIcon("delete.png"), "", detailwidget)
    self.delete_detail_button.setMaximumSize(70, 70)
    self.delete_detail_button.clicked.connect(self.delete_detail_clicked)
    self.cancel_del_detail_button = QPushButton(util.getIcon("back.png"), "", detailwidget)
    self.cancel_del_detail_button.setMaximumSize(70, 70)
    self.cancel_del_detail_button.clicked.connect(self.cancel_delete_detail_clicked)

    # cria o layout
    self.mainlayout = QHBoxLayout(centralwidget) # layout principal
    listlayout = QVBoxLayout(listwidget) # layout do painel da esquerda
    buttonlistlayout = QHBoxLayout() # layout do rodapé do painel da esquerda
    detaillayout = QVBoxLayout(detailwidget) # layout do painel da direita
    buttondetaillayout = QHBoxLayout() # layout do rodapé do painel da direita

    self.mainlayout.setContentsMargins(3, 3, 3, 3)
    listlayout.setContentsMargins(0, 0, 0, 0)
    buttonlistlayout.setContentsMargins(0, 0, 0, 0)
    detaillayout.setContentsMargins(0, 0, 0, 0)
    buttondetaillayout.setContentsMargins(0, 0, 0, 0)

    buttonlistlayout.addWidget(self.add_group_button)
    buttonlistlayout.addWidget(self.add_item_button)
    buttonlistlayout.addWidget(self.del_item_group_button)
    buttonlistlayout.addStretch(1)
    listlayout.addWidget(self.groupList)
    listlayout.addLayout(buttonlistlayout)

    buttondetaillayout.addWidget(self.find_button)
    buttondetaillayout.addStretch(1)
    buttondetaillayout.addWidget(self.up_detail_button)
    buttondetaillayout.addWidget(self.down_detail_button)
    buttondetaillayout.addWidget(self.add_detail_button)
    buttondetaillayout.addWidget(self.del_detail_button)
    buttondetaillayout.addWidget(self.delete_detail_button)
    buttondetaillayout.addWidget(self.cancel_del_detail_button)
    detaillayout.addWidget(self.item_detail)
    detaillayout.addLayout(buttondetaillayout)

    # cria o separador
    self.splitterHorizontal = QSplitter(Qt.Horizontal, centralwidget)
    self.splitterHorizontal.splitterMoved.connect(self.splitterMoved)
    self.splitterVertical = QSplitter(Qt.Vertical, centralwidget)
    self.splitterVertical.splitterMoved.connect(self.splitterMoved)
    self.splitterHorizontal.addWidget(listwidget)
    self.splitterHorizontal.addWidget(detailwidget)

    self.lockTimer = QTimer(self)
    self.lockTimer.timeout.connect(self.lockWindow)

    # verifica se estamos no Maemo (e portanto temos rotação)
    self.MAEMO5 =  hasattr(Qt, "WA_Maemo5PortraitOrientation")

    self.orientation = "none"
    if self.MAEMO5:
      # cria o objeto responsável pela rotação da tela
      self.rotation_object = FremantleRotation("pySafe", cb=self.screen_rotation)
      # o deixa desativado por enquanto! Só ativa quando exibir a janela em si
      self.rotation_object.set_mode(FremantleRotation.NEVER)


  """
  Cria o menu, assim como as ações para cada item
  """
  def __create_menu(self):
    self.change_pass_action = QAction(_("Change password"), self)
    self.change_pass_action.triggered.connect(self.change_password_clicked)

    self.about_action = QAction(_("About"), self)
    self.about_action.triggered.connect(self.about_clicked)

    self.import_action = QAction(_("Import"), self)
    self.import_action.triggered.connect(self.import_from_file_clicked)

    self.settings_action = QAction(_("Settings"), self)
    self.settings_action.triggered.connect(self.settings_clicked)

    self.menubar = self.menuBar()
    self.menubar.clear()
    self.menubar.addAction(self.import_action)
    self.menubar.addAction(self.change_pass_action)
    self.menubar.addAction(self.settings_action)
    self.menubar.addAction(self.about_action)


  def event(self, event):
    # bloco dentro de um try/catch porque alguns eventos ocorrem antes
    # que o próprio lockTimer já tenha sido criado...então evitamos
    # erros desnecessários
    try:
      if self.centralWidget().isVisible():
        # reinicia o timer
        self.__configLockTimer()
    except AttributeError:
      pass

    return QMainWindow.event(self, event)


  def __configLockTimer(self):
    if self.config.get(Configuration.AUTO_LOCK_TIME) == 0:
      self.lockTimer.stop()
    else:
      self.lockTimer.start(self.config.get(Configuration.AUTO_LOCK_TIME) * 1000)


  def lockWindow(self):
    self.lockTimer.stop()
    self.centralWidget().hide()

    while True:
      # cria a janela para pedir a senha
      (pass1, result) = QInputDialog.getText(self, " ", _("Type your password"), QLineEdit.Password)
      if result == False:
        self.close()
        return

      if len(pass1) == 0:
        QMessageBox.warning(self, " ", _("The password can not be empty!"))
        continue

      dbtmp = Dados(self.config.get(Configuration.DATABASE_FILE))
      ret = dbtmp.open(pass1.toUtf8())
      dbtmp.close()
      if ret == Dados.SENHA_INVALIDA:
        QMessageBox.warning(self, " ", _("Invalid password!"))
      else:
        break

    self.centralWidget().show()
    self.__configLockTimer()


  def setLastWidgetWithFocus(self, widget):
    self.lastWidgetWithFocus = widget
    self.__menuButtonsCheck()


  def groupListClicked(self, index, focus = None):
    model = self.groupList.model()
    item = model.itemFromIndex(index)
    if item.hasId():
      self.selectedItem = item
    else:
      self.selectedItem = None

    if self.detailView == self.DETAIL_ONE_VIEW:
      self.detailView = self.DETAIL_ALL_VIEW

    self.showDetailsForItem(focus)


  def set_database(self, d):
    self.database = d
    self.find_button.setDatabase(self.database)


  def rename(self, id, newName):
    if type(newName) is QString:
      newName = str(newName.toUtf8())
    elif type(newName) is not str:
      newName = str(newName)
    self.database.rename(id, newName)


  def splitterMoved(self, pos, index):
    if self.orientation == "portrait":
      self.config.set(Configuration.PORTRAIT_SLIDER_SIZE, pos)
    else:
      self.config.set(Configuration.LANDSCAPE_SLIDER_SIZE, pos)


  def screen_rotation(self, mode):
    self.orientation = mode
    if self.config.get(Configuration.AUTO_ROTATION) != 1 or mode != "portrait":
      w1 = self.splitterVertical.widget(0)
      w2 = self.splitterVertical.widget(1)

      if w1 is not None:
        w1.setParent(None)
        self.splitterHorizontal.addWidget(w1)
      if w2 is not None:
        w2.setParent(None)
        self.splitterHorizontal.addWidget(w2)

      self.mainlayout.removeWidget(self.splitterVertical)
      self.splitterVertical.setParent(None)
      self.mainlayout.addWidget(self.splitterHorizontal)
      self.splitterHorizontal.setSizes([self.config.get(Configuration.LANDSCAPE_SLIDER_SIZE), self.width() - self.config.get(Configuration.LANDSCAPE_SLIDER_SIZE)])
      if self.MAEMO5:
        self.setAttribute(Qt.WA_Maemo5LandscapeOrientation, True)
    else:
      w1 = self.splitterHorizontal.widget(0)
      w2 = self.splitterHorizontal.widget(1)

      if w1 is not None:
        w1.setParent(None)
        self.splitterVertical.addWidget(w1)
      if w2 is not None:
        w2.setParent(None)
        self.splitterVertical.addWidget(w2)

      self.mainlayout.removeWidget(self.splitterHorizontal)
      self.splitterHorizontal.setParent(None)
      self.mainlayout.addWidget(self.splitterVertical)
      self.splitterVertical.setSizes([self.config.get(Configuration.PORTRAIT_SLIDER_SIZE), self.height() - self.config.get(Configuration.PORTRAIT_SLIDER_SIZE)])
      if self.MAEMO5:
        self.setAttribute(Qt.WA_Maemo5PortraitOrientation, True)

    self.showDetailsForItem()


  def show(self):
    # habilita a rotação
    if self.MAEMO5:
      if self.config.get(Configuration.AUTO_ROTATION) != 1:
        self.orientation = "none"
        self.rotation_object.set_mode(FremantleRotation.NEVER)
      else:
        self.rotation_object.set_mode(FremantleRotation.AUTOMATIC)
    else:
      self.screen_rotation(self.orientation)
    # mostra os grupos
    self.showItens()
    self.__menuButtonsCheck()
    self.__configLockTimer()
    QMainWindow.show(self)


  def import_from_file_clicked(self):
    from import_data import ImportWizard
    progress = ProgressBarDialog(self, _("Importing..."))
    ImportWizard(self, self.database, progress)
    progress.reset()
    progress.hide()
    progress.close()
    self.showItens()


  def __get_group_path_string(self, ret = ""):
    id = 0
    if self.selectedItem is not None:
      id = self.selectedItem.getId()
      if id is None:
        self.selectedItem = None
        id = 0
    while id > 0:
      tmp = self.database.getCurrent(id)
      if tmp is not None:
        (id1, tipo, pos, label, value, id) = tmp
        if tipo == "g":
          if len(ret) == 0:
            ret = QString.fromUtf8(label)
          else:
            ret = "%s -> %s" % (QString.fromUtf8(label), ret)
    return ret


  def add_group_clicked(self):
    grupos = self.__get_group_path_string()
    title = _("New group")
    if len(grupos) > 0:
      title = _("New group in \"%s\"") % grupos
    (text, response) = QInputDialog.getText(self, " ", title)

    if response == True:
      id = 0
      if self.selectedItem is not None:
        id = self.selectedItem.getId()
      id = self.database.add_group(id, str(text.toUtf8()))
      self.addItem(str(text.toUtf8()), id, "g", self.selectedItem)


  def add_item_clicked(self):
    grupos = self.__get_group_path_string()
    title = _("New item")
    if len(grupos) > 0:
      title = (_("New item in group \"%s\"") % grupos)
    (text, response) = QInputDialog.getText(self, " ", title)
    if response == True:
      id = 0
      if self.selectedItem is not None:
        id = self.selectedItem.getId()
      id = self.database.add_item(id, str(text.toUtf8()))
      self.addItem(str(text.toUtf8()), id, "i", self.selectedItem)


  def del_group_item_clicked(self):
    isGroup = self.selectedItem.getType() == "g"
    group = self.__get_group_path_string()
    msg = ""
    if isGroup:
      msg = _("Are you sure you want to remove the group \"%s\" and all its items?") % (group)
    else:
      if len(group) > 0:
        msg = _("Are you sure you want to remove the item \"%s\" from the group \"%s\"?") % (self.selectedItem.text(), group)
      else:
        msg = _("Are you sure you want to remove the item \"%s\"?") % (self.selectedItem.text())

    response = QMessageBox.question(None, " ", msg, QMessageBox.Yes | QMessageBox.No)
    if response == QMessageBox.Yes:
      self.database.delItem(self.selectedItem.getId())

      # remove o item do treeview
      self.selectedItem.parent().removeRow(self.selectedItem.row())

      self.groupList.selectionModel().clear()
      self.__menuButtonsCheck()
      if not isGroup:
        self.showDetailsForItem()


  def up_detail_clicked(self):
    self.moveDetail(-1)

  def down_detail_clicked(self):
    self.moveDetail(1)

  def moveDetail(self, dir):
    if self.detailView == self.DETAIL_EDIT_VIEW:
      temp = {}
      model = self.deleteDetailList.model()
      # primeira pega os itens em si e coloca num dicionário tendo como chave a linha dele
      for i in self.deleteDetailList.selectedIndexes():
        temp[i.row()] = model.itemFromIndex(i).getId()
      # agora ordena dependendo da direção do movimento. Isso é necessário para evitar problemas
      # durante a movimentação, já que pode acontecer de um item selecionado ocupar o lugar
      # de outro item selecionado, e este segundo portanto deixa de existir e não será movido.
      # Fazendo a ordenação garantimos que um item não ocupará o lugar de outro selecionado...
      keys = temp.keys()
      keys.sort()
      # se a direção for para baixo (descer os elementos, inverte)
      if (dir > 0):
        keys.reverse()

      # guarda os id's novos para que o método que exibe a lista saiba quem deve selecionar
      temp1 = []
      for i in keys:
        self.database.moveDetail(temp[i], dir)
        temp1.append(temp[i])
      self.showDetailsForItem(temp1)
    elif self.detailView == self.DETAIL_ALL_VIEW and type(self.lastWidgetWithFocus) is MyLineEdit:
      id = self.lastWidgetWithFocus.getId()
      if self.database.moveDetail(id, dir) is not None:
        self.showDetailsForItem(id)


  def add_detail_clicked(self):
    grupos = self.__get_group_path_string()
    if len(grupos) == 0:
      title = (_("New detail for item \"%s\"") % self.selectedItem.text())
    else:
      title = (_("New detail for item \"%s\" in group \"%s\"") % (self.selectedItem.text(), grupos))
    (text, response) = QInputDialog.getText(None, " ", title)

    if response == True:
      id = self.database.add_detail(self.selectedItem.getId(), str(text.toUtf8()))
      if id != None:
        self.showDetailsForItem(id)


  def del_detail_clicked(self):
    self.detailView = self.DETAIL_EDIT_VIEW
    self.showDetailsForItem()


  def delete_detail_clicked(self):
    model = self.deleteDetailList.model()
    for i in self.deleteDetailList.selectedIndexes():
      self.database.del_detail(model.itemFromIndex(i).getId())
    self.cancel_delete_detail_clicked()


  def cancel_delete_detail_clicked(self):
    id = None
    if self.detailView == self.DETAIL_ONE_VIEW:
      id = self.lastWidgetWithFocus.getId()
    self.detailView = self.DETAIL_ALL_VIEW
    self.showDetailsForItem(id)


  def about_clicked(self):
    text = "(2010) Jorge Aguilar (pysafe@aguilarj.com)"
    if _("translator-credits") != "translator-credits":
      text = "%s\n\n%s" % (text, _("translator-credits"))
    QMessageBox.about(self, "pySafe %s" % (VERSION), text)


  def settings_clicked(self):
    self.config.showDialog(self)
    if self.MAEMO5:
      if self.config.get(Configuration.AUTO_ROTATION) != 1:
        self.orientation = "none"
        self.rotation_object.set_mode(FremantleRotation.NEVER)
      else:
        self.rotation_object.set_mode(FremantleRotation.AUTOMATIC)

    self.screen_rotation(self.orientation)
    self.__configLockTimer()


  def showDetailsForItem(self, focus = None):
    # não quero que o objeto seja apagado, mas apenas escondido
    self.deleteDetailList.setParent(None)

    widget = QWidget()
    teste = QVBoxLayout(widget)
    
    widgetVisible = None

    selectionModel = QItemSelection()

    if self.selectedItem is not None and self.selectedItem.getType() == "i":
      # pega os itens que deve inserir
      items = self.database.get(self.selectedItem.getId())

      if self.detailView == self.DETAIL_EDIT_VIEW:
        self.deleteDetailList.setParent(widget)
        self.deleteDetailList.model().clear()
        teste.addWidget(self.deleteDetailList)

      for i in items:
        (id, tipo, pos, labelText, text) = i
        if self.detailView == self.DETAIL_EDIT_VIEW:
          it = GroupListItem(QString.fromUtf8(labelText), id, tipo, not self.database.isReadOnly())
          self.deleteDetailList.model().appendRow(it)

          if focus is not None and id in focus:
            index = self.deleteDetailList.model().indexFromItem(it)
            selectionModel.merge(QItemSelection(index, index), QItemSelectionModel.Select)

        elif self.detailView == self.DETAIL_ALL_VIEW:
          label = QLabel(QString.fromUtf8(labelText), widget)
          teste.addWidget(label)
          
          view = MyLineEdit(QString.fromUtf8(text), widget, id, self.textview_changed, self.setLastWidgetWithFocus, pos, self.showDetailsEdit)
          view.setCursorPosition(0)
          view.setReadOnly(self.database.isReadOnly() or self.orientation == "portrait")
          view.setLast(pos == len(items) - 1)
          if focus == id:
            widgetVisible = view

          teste.addWidget(view)

        elif self.detailView == self.DETAIL_ONE_VIEW:
          if id == focus:
            label = QLabel(QString.fromUtf8(labelText), widget)
            teste.addWidget(label)

            # FIXME não aparece o scrollbar
            view = PlainTextEdit(QString(text), widget, id, self.textview_changed, self.setLastWidgetWithFocus)
            view.setReadOnly(self.database.isReadOnly() or self.orientation == "portrait")
            teste.addWidget(view)

    self.deleteDetailList.selectionModel().select(selectionModel, QItemSelectionModel.Select)

    # somente deve adicionar o "stretch" se estiver mostrando os detalhes dos itens
    if self.detailView == self.DETAIL_ALL_VIEW:
      teste.addStretch(1)

    self.item_detail.setWidget(widget)
    if widgetVisible is not None:
      widgetVisible.setFocus()
      self.item_detail.ensureWidgetVisible(widgetVisible)

    self.__menuButtonsCheck()


  def showDetailsEdit(self, detailId):
    self.detailView = self.DETAIL_ONE_VIEW
    self.showDetailsForItem(detailId)


  def showItens(self, path = 0, parent = None):
    if parent is None:
      model = self.groupList.model()
      model.clear()
      parent = GroupListItem(" ", path, None, editable = False)
      model.invisibleRootItem().appendRow(parent)
      self.groupList.setExpanded(model.indexFromItem(parent), True)

    el = self.database.get(path)
    for i in el:
      (id, tipo, pos, label, text) = i
      item = GroupListItem(QString.fromUtf8(label), id, tipo, not self.database.isReadOnly())
      parent.appendRow(item)
      if tipo == "g":
        self.showItens(id, item)

    # vamos ordenar a lista, mas somente se estivermos na raiz
    if path == 0:
      model.sort(0)


  def addItem(self, text, id, tipo, element):
    model = self.groupList.model()

    # se há um elemento deve procurar pelo primeiro pai que seja um grupo (ou a raiz)
    if element is not None:
      while element.getId() > 0 and element.getType() != "g":
        element = element.parent()

    # se não há elemento pai, deve colocar o novo item na raiz
    if element is None or element.getId() == 0:
      element = model.invisibleRootItem().child(0)

    # adiciona o item
    i = GroupListItem(QString.fromUtf8(text), id, tipo, not self.database.isReadOnly())
    element.appendRow(i)

    model.sort(0)


  def textview_changed(self, src, detail, id):
    self.database.set_detail(id, str(detail.toUtf8()))


  def change_password_clicked(self):
    while True:
      # cria a janela para pedir a senha
      (pass1, result) = QInputDialog.getText(self, " ", _("Type your new password"), QLineEdit.Password)
      if result == False:
        return

      if len(pass1) == 0:
        QMessageBox.warning(self, " ", _("The password can not be empty!"))
        continue

      # solicita para redigitar
      (pass2, result) = QInputDialog.getText(self, " ", _("Retype your new password"), QLineEdit.Password)
      if result == False:
        return

      if pass2 != pass1:
        QMessageBox.warning(self, " ", _("The passwords are not equals!"))
      else:
        progress = ProgressBarDialog(self, _("Changing password..."))
        progress.show()
        ret = self.database.changePassword(str(pass1), progress)
        if ret:
          QMessageBox.information(self, " ", _("Password changed!"))
        else:
          if progress.wasCanceled():
            QMessageBox.warning(self, " ", _("The password was not changed!"))
          else:
            QMessageBox.warning(self, " ", _("There was an error and the password was not changed!"))
        progress.reset()
        progress.hide()
        progress.close()
        break


  def __menuButtonsCheck(self):
    if self.orientation == "portrait":
      self.change_pass_action.setVisible(False)
      self.import_action.setVisible(False)
      self.settings_action.setVisible(False)

      self.add_group_button.setVisible(False)
      self.add_item_button.setVisible(False)
      self.del_item_group_button.setVisible(False)
      self.find_button.setVisible(False)
      self.add_detail_button.setVisible(False)
      self.del_detail_button.setVisible(False)
      self.up_detail_button.setVisible(False)
      self.down_detail_button.setVisible(False)
      self.delete_detail_button.setVisible(False)
      self.cancel_del_detail_button.setVisible(False)
    else:
      self.change_pass_action.setVisible(True)
      self.import_action.setVisible(True)
      self.settings_action.setVisible(True)

      self.import_action.setEnabled(True)
      self.change_pass_action.setEnabled(True)
      self.about_action.setEnabled(True)

      self.add_group_button.setVisible(True)
      self.add_item_button.setVisible(True)
      self.del_item_group_button.setVisible(True)

      self.find_button.setVisible(True)

      self.del_item_group_button.setEnabled(self.selectedItem is not None and self.selectedItem.getId() > 0)

      self.add_detail_button.setVisible(self.detailView == self.DETAIL_ALL_VIEW)
      self.del_detail_button.setVisible(self.detailView == self.DETAIL_ALL_VIEW)
      self.up_detail_button.setVisible(self.detailView != self.DETAIL_ONE_VIEW)
      self.down_detail_button.setVisible(self.detailView != self.DETAIL_ONE_VIEW)
      self.delete_detail_button.setVisible(self.detailView == self.DETAIL_EDIT_VIEW)
      self.cancel_del_detail_button.setVisible(self.detailView != self.DETAIL_ALL_VIEW)

      if self.database is not None and self.database.isReadOnly():
        self.import_action.setEnabled(False)
        self.change_pass_action.setEnabled(False)
        self.add_group_button.setEnabled(False)
        self.add_item_button.setEnabled(False)
        self.del_item_group_button.setEnabled(False)
        self.add_detail_button.setEnabled(False)
        self.del_detail_button.setEnabled(False)
        self.up_detail_button.setEnabled(False)
        self.down_detail_button.setEnabled(False)
        self.delete_detail_button.setEnabled(False)
      else:
        if self.add_detail_button.isVisible():
          self.add_detail_button.setEnabled(self.selectedItem is not None and self.selectedItem.getType() == "i")
        if self.del_detail_button.isVisible():
          self.del_detail_button.setEnabled(self.add_detail_button.isEnabled() and len(self.database.get(self.selectedItem.getId())) > 0)
        if self.delete_detail_button.isVisible():
          self.delete_detail_button.setEnabled(len(self.deleteDetailList.selectedIndexes()) > 0)

        if self.up_detail_button.isVisible():
          enableUp = self.lastWidgetWithFocus is not None or self.deleteDetailList.isVisible()
          if self.database:
            enableUp = enableUp and len(self.database.get(self.selectedItem.getId())) > 1
          enableDown = enableUp
          if enableUp:
            if self.detailView == self.DETAIL_EDIT_VIEW:
              enableUp = len(self.deleteDetailList.selectedIndexes()) > 0
              # se um dos itens selecionados for o primeiro, tem que desabilitar o botão
              for i in self.deleteDetailList.selectedIndexes():
                enableUp = enableUp and i.row() > 0
            elif self.detailView == self.DETAIL_ALL_VIEW and type(self.lastWidgetWithFocus) is MyLineEdit:
              enableUp = self.lastWidgetWithFocus.getPosition() > 0
          if enableDown:
            if self.detailView == self.DETAIL_EDIT_VIEW:
              enableDown = len(self.deleteDetailList.selectedIndexes()) > 0
              # se um dos itens selecionados for o último, tem que desabilitar o botão
              for i in self.deleteDetailList.selectedIndexes():
                enableDown = enableDown and i.row() < (self.deleteDetailList.model().rowCount() - 1)
            elif self.detailView == self.DETAIL_ALL_VIEW and type(self.lastWidgetWithFocus) is MyLineEdit:
              enableDown = not self.lastWidgetWithFocus.isLast()
          self.up_detail_button.setEnabled(enableUp)
          self.down_detail_button.setEnabled(enableDown)


class MyLineEdit(QLineEdit):

  def __init__(self, text = None, parent = None, id = 0, callback = None, focus = None, pos = 0, dbClick = None):
    QLineEdit.__init__(self, text, parent)
    try:
      # evitar o uso dicionário interno do aparelho (e impedir
      # que as palavras sejam inseridas nele)
      self.setInputMethodHints(Qt.ImhNoPredictiveText | Qt.ImhNoAutoUppercase)
    except:
      pass
    self.textChanged.connect(self.text_changed)
    self.__id = id
    self.callback = callback
    self.focus = focus
    self.__position = pos
    self.__last = False
    self.__dbClick = dbClick

  def getId(self):
    return self.__id

  def setLast(self, l):
    self.__last = l

  def isLast(self):
    return self.__last

  def getPosition(self):
    return int(self.__position)

  def text_changed(self, src):
    if self.callback != None:
      self.callback(self, src, self.__id)

  def focusInEvent(self, focus):
    QLineEdit.focusInEvent(self, focus)
    if self.focus is not None:
      self.focus(self)

  def mouseDoubleClickEvent(self, event):
    if self.__dbClick is not None:
      self.__dbClick(self.getId())


class PlainTextEdit(QPlainTextEdit):

  def __init__(self, text = None, parent = None, id = None, callback = None, focus = None):
    QPlainTextEdit.__init__(self, text, parent)
    try:
      self.setInputMethodHints(Qt.ImhNoPredictiveText | Qt.ImhNoAutoUppercase)
    except:
      pass
    self.textChanged.connect(self.text_changed)
    self.__id = id
    self.__callback = callback
    self.__focus = focus

  def getId(self):
    if type(self.__id) is QString:
      return str(self.__id.toUtf8())
    return self.__id

  def text_changed(self):
    if self.__callback != None:
      self.__callback(self, self.toPlainText(), self.__id)

  def focusInEvent(self, focus):
    QPlainTextEdit.focusInEvent(self, focus)
    if self.__focus is not None:
      self.__focus(self)


class TreeView(QTreeView):

  def __init__(self, parent, focus = None, renamecb = None):
    QTreeView.__init__(self, parent)
    self.collapsed.connect(self.collapse)
    self.expanded.connect(self.expand)
    self.focus = focus
    self.__renamecb = renamecb

  def focusInEvent(self, focus):
    QTreeView.focusInEvent(self, focus)
    if self.focus is not None:
      self.focus(None)

  def dataChanged(self, topLeft, bottomRight):
    QTreeView.dataChanged(self, topLeft, bottomRight)
    item = self.model().itemFromIndex(topLeft)
    if self.__renamecb is not None:
      self.__renamecb(item.getId(), item.text())
      item.textChanged(True)


  def collapse(self, index):
    model = index.model()
    item = model.itemFromIndex(index)
    if item.getId() == 0:
      item.setIcon(util.getIcon("folder-closed.png"))

  def expand(self, index):
    model = index.model()
    item = model.itemFromIndex(index)
    if item.getId() == 0:
      item.setIcon(util.getIcon("folder-opened.png"))


class ListView(QListView):

  def __init__(self, renamecb = None):
    QListView.__init__(self)
    self.__renamecb = renamecb

  def dataChanged(self, topLeft, bottomRight):
    QListView.dataChanged(self, topLeft, bottomRight)
    item = self.model().itemFromIndex(topLeft)
    if self.__renamecb is not None:
      self.__renamecb(item.getId(), item.text())


class StandardItemModel(QStandardItemModel):

  def __init__(self):
    QStandardItemModel.__init__(self)

  def flags(self, index):
    f = QStandardItemModel.flags(self, index)
    if self.itemFromIndex(index).isEditable():
      f |= Qt.ItemIsEditable
    else:
      f &= ~Qt.ItemIsEditable
    return f


class GroupListItem(QStandardItem):

  def __init__(self, text, id, tipo, editable = True):
    QStandardItem.__init__(self, text)

    self.__text = text
    self.__id = id
    self.__type = tipo
    self.__editable = editable

    if self.__id > 0:
      if self.__type == "i":
        self.setIcon(util.getIcon("item.png"))
      self.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled | Qt.ItemIsTristate | Qt.ItemIsUserCheckable)

  def textChanged(self, confirm):
    if confirm:
      self.__text = self.text()
    else:
      self.setText(self.__text)
    
  def hasId(self):
    return self.__id > 0;

  def getId(self):
    return self.__id

  def setId(self, id):
    self.__id = id

  def isEditable(self):
    return self.__editable

  def getType(self):
    return self.__type


class ProgressBarDialog(QProgressDialog):

  def __init__(self, parent, label):
    QProgressDialog.__init__(self, label, _("Cancel"), 0, 0, parent)
    self.setWindowTitle(" ")

  def updateProgressBar(self, total):
    if self.maximum() != total:
      self.setMaximum(total)
    self.setValue(self.value() + 1)
    QApplication.processEvents()
    return self.wasCanceled()


class Find(QPushButton):

  __ENTER_FIND = 0
  __FINDING = 1

  __FIND_TEXT = 1
  __FIND_GROUP = 2
  __FIND_ITEM = 3
  __FIND_DETAIL_LABEL = 4
  __FIND_DETAIL_TEXT = 5
  __FIND_ATUAL = 6

  def __init__(self, parent, treeview, treeviewclicked):
    QPushButton.__init__(self, util.getIcon("find.png"), "", parent)
    self.clicked.connect(self.__button_clicked)
    self.__treeview = treeview
    self.__treeviewClicked = treeviewclicked
    self.__database = None
    self.__state = self.__ENTER_FIND
    self.__findInfo = {self.__FIND_ATUAL: None,
                       self.__FIND_TEXT: "", 
                       self.__FIND_GROUP: Qt.Checked, 
                       self.__FIND_ITEM: Qt.Checked, 
                       self.__FIND_DETAIL_LABEL: Qt.Unchecked,
                       self.__FIND_DETAIL_TEXT: Qt.Checked}

  def setDatabase(self, db):
    self.__database = db

  def __button_clicked(self):
    if self.__state == self.__ENTER_FIND:
      if self.__showDialog() == QDialog.Accepted:
        self.setIcon(util.getIcon("find-next.png"))
        self.__state = self.__FINDING

    if self.__state == self.__FINDING:
      self.__doSearch()

  def contextMenuEvent(self, event):
    if self.__state == self.__FINDING:
      self.setIcon(util.getIcon("find.png"))
      self.__state = self.__ENTER_FIND

  def __doSearch(self):
    self.setCursor(Qt.WaitCursor)
    model = self.__treeview.model()
    index = None
    detail = None
    if self.__findInfo[self.__FIND_DETAIL_LABEL] != Qt.Checked and self.__findInfo[self.__FIND_DETAIL_TEXT] != Qt.Checked:
      # não deve procurar nos detalhes...ótimo! Mais fácil!
      # basta procurar no modelo do próprio treeview
      found = model.findItems(self.__findInfo[self.__FIND_TEXT], Qt.MatchContains | Qt.MatchRecursive)
      if len(found) > 0:
        if self.__FIND_ATUAL not in self.__findInfo:
          index = found[0]
        else:
          i = 0
          for j in range(len(found)):
            item = found[j]
            if item.getId() == self.__findInfo[self.__FIND_ATUAL]:
              i = j + 1
              break
          if i >= len(found):
            i = 0
          index = found[i]

        self.__findInfo[self.__FIND_ATUAL] = index.getId()

    else:
      # deve procurar em tudo...cria um novo modelo só para a busca, onde
      # colocamos os grupos, itens e os detalhes
      modelTemp = StandardItemModel()
      self.__createModel(modelTemp)
      found = modelTemp.findItems(self.__findInfo[self.__FIND_TEXT], Qt.MatchContains | Qt.MatchRecursive)
      if len(found) > 0:
        if self.__FIND_ATUAL not in self.__findInfo:
          index = found[0]
        else:
          i = 0
          for j in range(len(found)):
            item = found[j]
            if item.getId() == self.__findInfo[self.__FIND_ATUAL]:
              i = j + 1
              break
          if i >= len(found):
            i = 0
          index = found[i]

        self.__findInfo[self.__FIND_ATUAL] = index.getId()

        # agora busca no modelo original pelo índice correto
        idOk = None
        if index.getType() == "d":
          idOk = index.parent().getId()
          detail = index.getId()
          found = model.findItems(index.parent().text() , Qt.MatchExactly | Qt.MatchRecursive)
        else:
          idOk = index.getId()
          found = model.findItems(index.text() , Qt.MatchExactly | Qt.MatchRecursive)
        index = None
        for i in found:
          if i.getId() == idOk:
            index = i
            break

    if index is not None:
      self.__treeview.setCurrentIndex(model.indexFromItem(index))
      self.__treeviewClicked(model.indexFromItem(index), detail)

    self.setCursor(Qt.ArrowCursor)

  def __createModel(self, model, path = 0, parent = None):
    if parent is None:
      model.clear()
      parent = GroupListItem(" ", path, "g", editable = False)
      model.invisibleRootItem().appendRow(parent)

    el = self.__database.get(path)
    for i in el:
      (id, tipo, pos, label, text) = i
      item = GroupListItem(QString(label), id, tipo, not self.__database.isReadOnly())
      parent.appendRow(item)
      if tipo == "g":
        self.__createModel(model, id, item)
      elif tipo == "i":
        details = self.__database.get(id)
        for i in details:
          (id, tipo, pos, labelText, text) = i
          if self.__findInfo[self.__FIND_DETAIL_LABEL] == Qt.Checked:
            detail = GroupListItem(QString(labelText), id, tipo, not self.__database.isReadOnly())
            item.appendRow(detail)
          if self.__findInfo[self.__FIND_DETAIL_TEXT] == Qt.Checked:
            detail = GroupListItem(QString(text), id, tipo, not self.__database.isReadOnly())
            item.appendRow(detail)

    # vamos ordenar a lista, mas somente se estivermos na raiz
    if path == 0:
      model.sort(0)

  def __showDialog(self):
    self.setCursor(Qt.WaitCursor)
    dialog = QDialog()
    dialog.setModal(True)
    dialog.setWindowTitle(" ")

    self.text = QLineEdit(self.__findInfo[self.__FIND_TEXT], dialog)
    self.text.textChanged.connect(self.checkFindButton)
    try:
      # evitar o uso dicionário interno do aparelho (e impedir
      # que as palavras sejam inseridas nele)
      self.text.setInputMethodHints(Qt.ImhNoPredictiveText)
    except:
      pass
    self.group = QCheckBox(_("Group"), dialog)
    self.group.stateChanged.connect(self.checkFindButton)
    self.item = QCheckBox(_("Item"), dialog)
    self.item.stateChanged.connect(self.checkFindButton)
    self.detailName = QCheckBox(_("Detail name"), dialog)
    self.detailName.stateChanged.connect(self.checkFindButton)
    self.detailText = QCheckBox(_("Detail text"), dialog)
    self.detailText.stateChanged.connect(self.checkFindButton)
    self.button = QPushButton(_("Find"), dialog)

    self.group.setCheckState(self.__findInfo[self.__FIND_GROUP])
    self.item.setCheckState(self.__findInfo[self.__FIND_ITEM])
    self.detailName.setCheckState(self.__findInfo[self.__FIND_DETAIL_LABEL])
    self.detailText.setCheckState(self.__findInfo[self.__FIND_DETAIL_TEXT])

    self.button.setDefault(True)
    self.button.setAutoDefault(True)
    self.connect(self.button, SIGNAL('clicked()'), dialog, SLOT('accept()'))

    layout1 = QVBoxLayout(dialog)
    layout2 = QHBoxLayout()
    layout3 = QHBoxLayout()
    layout4 = QHBoxLayout()

    layout1.addWidget(self.text)
    layout2.addWidget(self.group)
    layout2.addWidget(self.item)
    layout3.addWidget(self.detailName)
    layout3.addWidget(self.detailText)
    layout1.addLayout(layout2)
    layout1.addLayout(layout3)
    layout4.addStretch(1)
    layout4.addWidget(self.button)
    layout1.addLayout(layout4)

    self.checkFindButton()

    self.setCursor(Qt.ArrowCursor)

    response = dialog.exec_()

    if response == QDialog.Accepted:
      self.__findInfo = {self.__FIND_TEXT: self.text.text(), 
                         self.__FIND_GROUP: self.group.checkState(), 
                         self.__FIND_ITEM: self.item.checkState(), 
                         self.__FIND_DETAIL_LABEL: self.detailName.checkState(),
                         self.__FIND_DETAIL_TEXT: self.detailText.checkState()}

    return response

  def checkFindButton(self, info = None):
    self.button.setEnabled((self.group.checkState() == Qt.Checked or self.item.checkState() == Qt.Checked or self.detailName.checkState() == Qt.Checked or self.detailText.checkState() == Qt.Checked) and
                           len(self.text.text()) > 0)


class errorLog:
  def __init__(self):
    self.__filename = os.path.join(tempfile.gettempdir(), "pysafe.log")
    self.__file = open(self.__filename, "w")
    self.__messageViewed = False

  def write(self, msg):
    self.__file.write(msg)
    if not self.__messageViewed:
      QMessageBox.warning(None, _("Error!"), _("An error has ocurred and a log was saved in \"%s\".\n\nSend it to the developer: pysafe@aguilarj.com.") % self.__filename)
      self.__messageViewed = True


class pysafe:
  def __init__(self):
    if not "-no-trap-error" in sys.argv:
      sys.stderr = errorLog()

    app = QApplication(sys.argv)

    gettext.install('pysafe', sys.path[0], 'utf-8')

    config = Configuration()

    # cria a janela principal
    win = MainWindow(config)

    if config.get(Configuration.VERSION) == "0":
      from upgrade import Upgrade
      u = Upgrade(win, config.get(Configuration.VERSION), VERSION)
      ret = u.check()
      if ret is None:
        return
      (fn, pwd) = ret
      config.set(Configuration.DATABASE_FILE, fn)
      config.set(Configuration.VERSION, VERSION)

      database = Dados(config.get(Configuration.DATABASE_FILE))
      database.open(pwd)
    else:
      database = Dados(config.get(Configuration.DATABASE_FILE))
      while True:
        # cria a janela para pedir a senha
        (pass1, result) = QInputDialog.getText(win, " ", _("Type your password"), QLineEdit.Password)
        if result == False:
          return

        if len(pass1) == 0:
          QMessageBox.warning(win, " ", _("The password can not be empty!"))
          continue

        ret = database.open(pass1.toUtf8())
        if ret == database.DATABASE_OK:
          break
        elif ret == database.SOMENTE_LEITURA:
          QMessageBox.warning(win, " ", _("The database are not updataple. Check file permissions or disk space."))
          break
        elif ret == database.ARQUIVO_NAO_LOCALIZADO:
          response = QMessageBox.warning(win, " ", _("Database file not found:\n\"%s\"") % config.get(Configuration.DATABASE_FILE))
          return
        else:
          texto = _("An undefined error has ocurred!")
          if ret == database.SENHA_INVALIDA:
            texto = _("Invalid password!")
          elif ret == database.DADOS_CORROMPIDOS:
            texto = _("Database corrupted or invalid password!")
          QMessageBox.warning(win, " ", texto)

    win.set_database(database)
    win.show()

    app.exec_()

    database.close()
