# -*- coding: utf-8 -*-
import gtk
import gobject
import locale
import gettext
import os
import sys
import ConfigParser
from database import Dados


"""
Classe responsável pela exibição da tela principal do aplicativo
"""
class MainWindow():

  def __init__(self, cfg):
    self.ignore_list_clicked = False
    self.atual_group = None
    self.database = None
    self.config = cfg

    self.window = gtk.Window()
    self.window.set_title("pySafe")
    size = self.config.get(self.config.WINDOW_SIZE)
    self.window.resize(size[0], size[1])
    pos = self.config.get(self.config.WINDOW_POSITION)
    self.window.move(pos[0], pos[1])

    # adiciona o menu
    self.add_group_button = gtk.MenuItem(_("Add group"))
    self.add_group_button.connect("activate", self.add_group_clicked)

    self.del_group_button = gtk.MenuItem(_("Remove group"))
    self.del_group_button.connect("activate", self.del_group_clicked)

    self.add_item_button = gtk.MenuItem(_("Add item"))
    self.add_item_button.connect("activate", self.add_item_clicked)

    self.del_item_button = gtk.MenuItem(_("Remove item"))
    self.del_item_button.connect("activate", self.del_item_clicked)

    self.change_pass_button = gtk.MenuItem(_("Change password"))
    self.change_pass_button.connect("activate", self.change_password_clicked)

    self.about_button = gtk.MenuItem(_("About"))
    self.about_button.connect("activate", self.about_clicked)

    self.add_detail_button = gtk.MenuItem(_("Add detail"))
    self.add_detail_button.connect("activate", self.add_detail_clicked)

    self.del_detail_button = gtk.MenuItem(_("Remove detail"))
    self.del_detail_button.connect("activate", self.del_detail_clicked)

    file_exit = gtk.MenuItem(_("Quit"))
    file_exit.connect("activate", self.quit, None)

    self.del_group_button.set_sensitive(False)
    self.add_item_button.set_sensitive(False)
    self.del_item_button.set_sensitive(False)
    self.add_detail_button.set_sensitive(False)
    self.del_detail_button.set_sensitive(False)

    menu_file = gtk.MenuItem(_("File"))
    menu_file.set_submenu(gtk.Menu())
    menu_file.get_submenu().append(file_exit)

    menu_edit = gtk.MenuItem(_("Edit"))
    menu_edit.set_submenu(gtk.Menu())
    menu_edit.get_submenu().append(self.add_group_button)
    menu_edit.get_submenu().append(self.del_group_button)
    menu_edit.get_submenu().append(self.add_item_button)
    menu_edit.get_submenu().append(self.del_item_button)
    menu_edit.get_submenu().append(self.change_pass_button)

    menu_help = gtk.MenuItem(_("Help"))
    menu_help.set_submenu(gtk.Menu())
    menu_help.get_submenu().append(self.about_button)

    menubar = gtk.MenuBar()
    menubar.append(menu_file)
    menubar.append(menu_edit)
    menubar.append(menu_help)
    menubar.show_all()

    vbox = gtk.VBox(False, 2)
    vbox.pack_start(menubar, False, False, 0)

    self.window.connect("destroy", self.quit, None)

    self.panel_landscape = gtk.HPaned()
    self.panel_landscape.set_position(self.config.get(self.config.LANDSCAPE_SLIDER_SIZE))

    vbox.pack_end(self.panel_landscape, True, True, 0)
    self.window.add(vbox)

    #list_store = gtk.ListStore(gtk.gdk.Pixbuf, gobject.TYPE_STRING)

    self.groupList = gtk.TreeView(gtk.ListStore(gobject.TYPE_STRING))
    #self.groupList.connect("changed", self.list_clicked)
    #self.groupList.append_column(list_store, gtk.CellRenderer())
    self.panel_landscape.add1(self.groupList)

    self.panel_detail = gtk.VBox()
    self.panel_landscape.add2(self.panel_detail)

    #self.item_detail = hildon.PannableArea()
    self.item_detail_area = gtk.VBox()
    #self.item_detail.add_with_viewport(self.item_detail_area)
    #self.panel_detail.pack_start(self.item_detail, True, True, 0)

    box = gtk.HBox()
    box.add(self.add_detail_button)
    box.add(self.del_detail_button)
    self.panel_detail.pack_end(box, False, False, 0)

    #self.window.add(vbox)

    # This call show the window and also add the window to the stack
    self.window.show_all()


  def set_database(self, d):
    self.database = d


  def quit(self, v1, v2):
    self.config.set(self.config.LANDSCAPE_SLIDER_SIZE, self.panel_landscape.get_position())
    #self.config.set(self.config.WINDOW_SIZE, self.window.get_size())
    #self.config.set(self.config.WINDOW_POSITION, self.window.get_position())

    if self.database.save() != True:
      gtk.Dialog.run(hildon.Note("information", self.window, _("The database could not be updated. Check file permissions or disk space.")))

    gtk.main_quit()


  def show(self):
    # mostra os grupos
    self.showGroups()


  def add_group_clicked(self, src):
    entry = gtk.Entry()
    label = gtk.Label(_("Name"))
    label.set_mnemonic_widget(entry)
    dialog = gtk.Dialog(title=_("New Group"), parent=self.window, buttons=(_("Ok"), gtk.RESPONSE_OK, _("Cancel"), gtk.RESPONSE_CANCEL))
    dialog.vbox.add(label)
    dialog.vbox.add(entry)
    dialog.show_all()
    response = dialog.run()
    dialog.destroy()
    if response == gtk.RESPONSE_OK:
      if self.database.addGroup(entry.get_text()):
        self.showGroups()
        # força a janela a se atualizar...se não fizer isso, o scroll abaixo pode não funcionar
        self.groupList.get_parent_window().process_updates(True)
        # seta o elemento atual
        treemodel = self.groupList.get_model(0)
        it = treemodel.get_iter_first()
        while (it != None):
          if treemodel.get_value(it, 0) == entry.get_text():
            self.groupList.select_iter(0, it, True)
            break
          it = treemodel.iter_next(it)
      else:
        MessageDialog(self.window, gtk.MESSAGE_INFORMATION, gtk.BUTTONS_OK, _("The group \"%s\" already exists!") % (entry.get_text())).show()


  def del_group_clicked(self, src):
    note = hildon.Note("confirmation", self.window, _("Are you sure you want to remove the group \"%s\" and all their itens?") % (self.atual_group))
    retcode = gtk.Dialog.run(note)
    if retcode == gtk.RESPONSE_OK:
      self.database.delGroup(self.atual_group)
      self.showGroups()
    gtk.Dialog.destroy(note)


  def add_item_clicked(self, src):
    entry = hildon.Entry(0)
    dialog = gtk.Dialog(title=_("New Item for Group \"%s\"") % (self.atual_group), parent=self.window, buttons=("Done", gtk.RESPONSE_OK))
    dialog.vbox.add(hildon.Caption(None, _("Name"), entry, None, True))
    dialog.show_all()
    response = dialog.run()
    dialog.destroy()
    if response == gtk.RESPONSE_OK:
      if self.database.addItem(self.atual_group, entry.get_text()):
        self.showItens()
        # força a janela a se atualizar...se não fizer isso, o scroll abaixo pode não funcionar
        self.groupList.get_parent_window().process_updates(True)
        # seta o elemento atual
        treemodel = self.groupList.get_model(0)
        it = treemodel.get_iter_first()
        while (it != None):
          if treemodel.get_value(it, 0) == entry.get_text():
            self.groupList.select_iter(0, it, True)
            break
          it = treemodel.iter_next(it)
      else:
        gtk.Dialog.run(hildon.Note("information", self.window, _("The item \"%s\" for the group \"%s\" already exists!") % (entry.get_text(), self.atual_group)))


  def del_item_clicked(self, src):
    group = self.atual_group
    item = self.groupList.get_current_text()
    note = hildon.Note("confirmation", self.window, _("Are you sure you want to remove the item \"%s\" from the group \"%s\"?") % (item, group))
    retcode = gtk.Dialog.run(note)
    if retcode == gtk.RESPONSE_OK:
      self.database.delItem(group, item)
      self.showItens()
      self.remove_itens_from_list()
    gtk.Dialog.destroy(note)


  def add_detail_clicked(self, src):
    entry = hildon.Entry(0)
    dialog = gtk.Dialog(title=_("New Detail for Item \"%s\" in Group \"%s\"") % (self.groupList.get_current_text(), self.atual_group), parent=self.window, buttons=(_("Done"), gtk.RESPONSE_OK))
    dialog.vbox.add(hildon.Caption(None, _("Name"), entry, None, True))
    dialog.show_all()
    response = dialog.run()
    dialog.destroy()
    if response == gtk.RESPONSE_OK:
      if self.database.addDetail(self.atual_group, self.groupList.get_current_text(), entry.get_text()):
        self.show_details_for_item()
      else:
        gtk.Dialog.run(hildon.Note("information", self.window, _("The detail \"%s\" for item \"%s\" in group \"%s\" already exists!") % (entry.get_text(), self.groupList.get_current_text(), self.atual_group)))


  def del_detail_clicked(self, src):
    RemoveDetailsWindow(self.database, self.atual_group, self.groupList.get_current_text(), self)


  def about_clicked(self, src):
    dialog = gtk.AboutDialog()
    dialog.set_name("pySafe")
    dialog.set_version("0.3.2")
    dialog.set_authors(["Jorge Aguilar"])
    dialog.set_translator_credits(_("translator-credits"))
    #dialog.set_logo(gtk.gdk.pixbuf_new_from_file_at_size("pysafe_128x128.png", 64, 64))
    dialog.run()


  def list_clicked(self, widget, column, user_data = None):
    if self.ignore_list_clicked:
      return

    print "list_clicked"

    self.ignore_list_clicked = True

    # estes botões só devem ser ativados caso seja exibido um item
    self.del_item_button.set_sensitive(False)
    self.add_detail_button.set_sensitive(False)
    self.del_detail_button.set_sensitive(False)

    self.remove_itens_from_list()

    if self.atual_group == None:
      self.atual_group = self.groupList.get_current_text()
      self.ignore_list_clicked = False
      self.showItens()
    elif self.groupList.get_current_text() == _("<< back to groups"):
      self.ignore_list_clicked = False
      self.showGroups()
    else:
      self.show_details_for_item()

      # habilita os botões
      self.del_item_button.set_sensitive(True)
      self.add_detail_button.set_sensitive(True)

    # habilita/desabilita botões dependendo do contexto
    self.del_group_button.set_sensitive(self.atual_group != None)
    self.add_item_button.set_sensitive(self.atual_group != None)

    self.ignore_list_clicked = False


  def remove_itens_from_list(self):
    # remove os itens atuais
    # o "get_children" devolve um array...por isso o índice 0
    # dentro do item_detail tem um viewport, que tem dentro um vbox, que tem dentro os elementos
    for i in self.item_detail.get_children()[0].get_children()[0].get_children():
      self.item_detail_area.remove(i)

    self.item_detail.jump_to(0, 0)


  def check_editable_details(self, editable):
    for i in self.item_detail.get_children()[0].get_children()[0].get_children():
      if type(i).__name__ == "Entry":
        i.set_editable(editable)


  def show_details_for_item(self):
    # pega os itens que deve inserir
    itens = self.database.getItem(self.atual_group, self.groupList.get_current_text())

    self.remove_itens_from_list()

    # insere os itens na tela
    keys = itens.keys()
    keys.sort(key=str.lower)
    for i in keys:
      view = hildon.Entry(0)
      view.set_text(itens[i])
      view.connect("changed", self.textview_changed, i)
      label = gtk.Label(i)
      label.set_alignment(0,0)
      self.item_detail_area.pack_start(label, False, True, 0)
      self.item_detail_area.pack_start(view, False, True, 0)

    # exibe os itens
    self.item_detail_area.show_all()

    self.del_detail_button.set_sensitive(len(keys) != 0)


  def showGroups(self):
    if self.ignore_list_clicked:
      return
  
    self.ignore_list_clicked = True

    self.atual_group = None

    # pega os valores e ordena
    keys = self.database.getGroups()
    #keys.sort(key=str.lower, reverse=True)
    keys.sort(key=str.lower)

    treemodel = self.groupList.get_model()
    treemodel.clear()
    for i in keys:
      self.groupList.append_text(i)

    self.ignore_list_clicked = False


  def showItens(self):
    if self.ignore_list_clicked:
      return
  
    self.ignore_list_clicked = True

    treemodel = self.groupList.get_model(0)
    treemodel.clear()

    """
    button = hildon.Button(gtk.HILDON_SIZE_AUTO_WIDTH | gtk.HILDON_SIZE_FINGER_HEIGHT,
                           hildon.BUTTON_ARRANGEMENT_VERTICAL)
    button.set_text("Some title", "some value")
    image = gtk.image_new_from_stock(gtk.STOCK_INFO, gtk.ICON_SIZE_BUTTON)
    button.set_image(image)
    button.set_image_position(gtk.POS_RIGHT)
    #a = gtk.icon_factory_lookup_default(gtk.STOCK_ADD)
    #self.groupList.add(a.render_icon(gtk.Style(), gtk.TEXT_DIR_LTR, gtk.STATE_NORMAL, gtk.ICON_SIZE_BUTTON, None, None))
    self.groupList.add(button)
    """

    self.groupList.append_text(_("<< back to groups"))
    keys = self.database.getItens(self.atual_group).keys()
    keys.sort(key=str.lower)
    for i in keys:
      self.groupList.append_text(i)

    self.ignore_list_clicked = False


  def textview_changed(self, src, detail):
    self.database.setDetail(self.atual_group, self.groupList.get_current_text(), detail, src.get_text())


  def change_password_clicked(self, src):
    while True:
      # cria a janela para pedir a senha
      passwordDialog = hildon.GetPasswordDialog(self.window, True)
      passwordDialog.set_title("")
      passwordDialog.set_caption(_("Type your new password"))
      passwordDialog.set_property("password", "")
      response = passwordDialog.run()
      pass1 = passwordDialog.get_password()
      passwordDialog.destroy() 
      if response != gtk.RESPONSE_OK:
        return

      if len(pass1) == 0:
        note = hildon.Note("information", self.window, _("The password can not be empty!"))
        gtk.Dialog.run(note)
        note.destroy()
        continue

      # solicita para redigitar
      passwordDialog = hildon.GetPasswordDialog(self.window, True)
      passwordDialog.set_title("")
      passwordDialog.set_caption(_("Re-type your new password"))
      passwordDialog.set_property("password", "")
      response = passwordDialog.run()
      passwordDialog.hide() 
      if response != gtk.RESPONSE_OK:
        return

      if passwordDialog.get_password() != pass1:
        note = hildon.Note("information", self.window, _("The passwords are not equals!"))
        gtk.Dialog.run(note)
        note.destroy()
      else:
        self.database.save(force = True, new_pass = pass1)
        note = hildon.Note("information", self.window, _("Password changed!"))
        gtk.Dialog.run(note)
        note.destroy()
        break


"""
Esta classe exibe a janela de exclusão de detalhes do item
"""
class RemoveDetailsWindow:

  """
    Parâmetros:
    d - banco de dados
    g - grupo selecionado
    i - item selecionado
    c - instância da janela principal
  """
  def __init__(self, d, g, i, c):
    self.database = d
    self.grupo = g
    self.item = i
    self.callback_function_on_close = c

    window = hildon.StackableWindow()
    window.set_border_width(6)

    # Create a new edit toolbar
    toolbar = hildon.EditToolbar(_("Choose details to delete"), _("Delete"))

    area = hildon.PannableArea()
    tree_view = self.create_treeview(gtk.HILDON_UI_MODE_EDIT)

    # Add toolbar to the window
    window.set_edit_toolbar(toolbar)

    area.add(tree_view)
    window.add(area)

    toolbar.connect("button-clicked", self.delete_button_clicked, tree_view)
    toolbar.connect_object("arrow-clicked", self.close_window, window)

    window.show_all()
    # Set window to fullscreen
    window.fullscreen()


  def close_window(self, window):
    MainWindow.show_details_for_item(self.callback_function_on_close)
    window.destroy()


  def delete_button_clicked(self, button, treeview):
      selection = treeview.get_selection()

      (model, selected_rows) = selection.get_selected_rows()

      row_references = []
      for path in selected_rows:
          ref = gtk.TreeRowReference(model, path)
          row_references.append(ref)

      for ref in row_references:
          path = ref.get_path()
          iter = model.get_iter(path)
          self.database.delDetail(self.grupo, self.item, model.get_value(iter, 0))
          model.remove(iter)


  def create_treeview(self, tvmode):
      tv = hildon.GtkTreeView(tvmode)
      renderer = gtk.CellRendererText()
      col = gtk.TreeViewColumn("Title", renderer, text=0)

      tv.append_column(col)

      # Set multiple selection mode
      selection = tv.get_selection()
      selection.set_mode(gtk.SELECTION_MULTIPLE)

      store = gtk.ListStore(gobject.TYPE_STRING)
      itens = self.database.getItem(self.grupo, self.item)
      keys = itens.keys()
      keys.sort(key=str.lower, reverse=True)
      # insere os itens na tela
      for i in keys:
        store.insert(0, [i])

      tv.set_model(store)

      return tv


class Configuration:

  LANDSCAPE_SLIDER_SIZE = 2
  DATABASE_FILE = 3
  WINDOW_POSITION = 4
  WINDOW_SIZE = 5

  def __init__(self):
    self.config = ConfigParser.RawConfigParser()
    self.changed = False
    self.load()
    self.check_sanity()

  def load(self):
    self.config.read('%s/.pysafe.conf' % (os.path.expanduser('~')))

  def save(self):
    if self.changed:
      configfile = open('%s/.pysafe.conf' % (os.path.expanduser('~')), 'wb')
      self.config.write(configfile)
      configfile.close()
      self.changed = False

  def check_sanity(self):
    if not self.config.has_section('Window'):
      self.config.add_section('Window')

    # verifica o tamanho do slider em modo paisagem
    tmp = 300
    if self.config.has_option('Window', 'landscape_slider'):
      tmp = self.config.get('Window', 'landscape_slider')
      if not tmp.isdigit():
        tmp = 300
    self.config.set('Window', 'landscape_slider', tmp)

    # verifica a posição X da janela
    tmp = 0
    if self.config.has_option('Window', 'x'):
      tmp = self.config.get('Window', 'x')
      if not tmp.isdigit():
        tmp = 0
    self.config.set('Window', 'x', tmp)

    # verifica a posição Y da janela
    tmp = 0
    if self.config.has_option('Window', 'y'):
      tmp = self.config.get('Window', 'y')
      if not tmp.isdigit():
        tmp = 0
    self.config.set('Window', 'y', tmp)

    # verifica o comprimento da janela
    tmp = 600
    if self.config.has_option('Window', 'width'):
      tmp = self.config.get('Window', 'width')
      if not tmp.isdigit():
        tmp = 600
    self.config.set('Window', 'width', tmp)

    # verifica a altura da janela
    tmp = 300
    if self.config.has_option('Window', 'height'):
      tmp = self.config.get('Window', 'height')
      if not tmp.isdigit():
        tmp = 300
    self.config.set('Window', 'height', tmp)


  def get(self, item):
    if item == self.LANDSCAPE_SLIDER_SIZE:
      return self.config.getint('Window', 'landscape_slider')
    elif item == self.WINDOW_POSITION:
      return (self.config.getint('Window', 'x'), self.config.getint('Window', 'y'))
    elif item == self.WINDOW_SIZE:
      return (self.config.getint('Window', 'width'), self.config.getint('Window', 'height'))

    return None

  def set(self, item, value):
    # se o valor é igual, não tem por alterar!
    if self.get(item) == value:
      return

    if item == self.LANDSCAPE_SLIDER_SIZE:
      self.config.set('Window', 'landscape_slider', value)
    elif item == self.WINDOW_POSITION:
      self.config.set('Window', 'x', value[0])
      self.config.set('Window', 'y', value[1])
    elif item == self.WINDOW_SIZE:
      self.config.set('Window', 'width', value[0])
      self.config.set('Window', 'height', value[1])

    self.changed = True


class PasswordDialog:

  def __init__(self, main, text):
    self.dialog = gtk.Dialog(parent = main, 
                             flags = gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT, 
                             buttons = (gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL,
                                        gtk.STOCK_OK, gtk.RESPONSE_OK))

    vbox = self.dialog.get_content_area()
    vbox.pack_start(gtk.Label(text), False, False, 0)

    self.pass_entry = gtk.Entry()
    self.pass_entry.set_visibility(False)
    vbox.pack_end(self.pass_entry, False, False, 0)

  def show(self):
    self.dialog.show_all()
    return self.dialog.run()

  def destroy(self):
    self.dialog.destroy()

  def get_password(self):
    return self.pass_entry.get_text()


class MessageDialog:

  def __init__(self, main, t, b, text):
    self.dialog = gtk.MessageDialog(parent = main,
                                    flags = gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
                                    type = t,
                                    buttons = b,
                                    message_format = text)

  def show(self):
    response = self.dialog.run()
    self.dialog.destroy()
    return response


class pysafe:
  def __init__(self):

    gettext.install('pysafe', sys.path[0])

    config = Configuration()

    # cria a janela principal
    win = MainWindow(config)

    while True:
      # cria a janela para pedir a senha
      passwordDialog = PasswordDialog(win.window, _("Type your password"))
      response = passwordDialog.show()
      pass1 = passwordDialog.get_password()
      passwordDialog.destroy() 
      if response != gtk.RESPONSE_OK:
        return

      if len(pass1) == 0:
        continue

      database = Dados(pass1)
      ret = database.load()
      if ret == database.DATABASE_OK:
        # tenta salvar o banco (para garantir que será atualizavel)
        if database.save(force = True) == False:
          MessageDialog(win.window, gtk.MESSAGE_WARNING, gtk.BUTTONS_OK, _("The database are not updataple. Check file permissions or disk space.")).show()
        break
      elif ret == database.ARQUIVO_NAO_LOCALIZADO:
        note = MessageDialog(win.window, gtk.MESSAGE_QUESTION, gtk.BUTTONS_YES_NO, _("Database file not found. Confirm the creation of a new one?")).show()
        if note != gtk.RESPONSE_YES:
          return

        # solicita para redigitar
        passwordDialog = PasswordDialog(win.window, _("Re-type your password"))
        response = passwordDialog.show()
        pass2 = passwordDialog.get_password()
        passwordDialog.destroy()
        if response != gtk.RESPONSE_OK:
          return

        if pass2 != pass1:
          MessageDialog(win.window, gtk.MESSAGE_ERROR, gtk.BUTTONS_OK, _("The passwords are not equals!")).show()
        else:
          if database.save(force = True) == False:
            MessageDialog(win.window, gtk.MESSAGE_WARNING, gtk.BUTTONS_OK, _("The database are not updataple. Check file permissions or disk space.")).show()
          break
      else:
        texto = _("An undefined error has ocurred!")
        if ret == database.SENHA_INVALIDA:
          texto = _("Invalid password!")
        elif ret == database.DADOS_CORROMPIDOS:
          texto = _("Database corrupted or invalid password!")
        MessageDialog(win.window, gtk.MESSAGE_ERROR, gtk.BUTTONS_OK, texto).show()

    passwordDialog.destroy() 

    win.set_database(database)
    win.show()
    gtk.main()

    config.save()

