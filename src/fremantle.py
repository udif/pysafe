# -*- coding: utf-8 -*-
import gtk
import hildon
import gettext
import os
import sys
import ConfigParser
from import_data import import_from_file
from rotation import FremantleRotation
from database import Dados

"""
Classe responsável pela exibição da tela principal do aplicativo
"""
class MainWindow():

  FOLDER_OPENED_ICON = gtk.gdk.pixbuf_new_from_file('%s/icons/folder-opened.png' % (sys.path[0]))
  FOLDER_CLOSED_ICON = gtk.gdk.pixbuf_new_from_file('%s/icons/folder-closed.png' % (sys.path[0]))

  (LIST_COLUMN_ICON, LIST_COLUMN_TEXT, LIST_COLUMN_ID) = range(3)

  def __init__(self, cfg):
    self.ignore_list_clicked = False
    self.atual_group = []
    self.database = None
    self.config = cfg

    self.window = hildon.StackableWindow()
    self.window.set_title("pySafe")

    # adiciona o menu
    self.menu = hildon.AppMenu()
    self.add_group_button = hildon.Button(gtk.HILDON_SIZE_AUTO_WIDTH | gtk.HILDON_SIZE_FINGER_HEIGHT,
                          hildon.BUTTON_ARRANGEMENT_VERTICAL)
    self.add_group_button.set_text(_("Add group"), "")
    self.add_group_button.connect("clicked", self.add_group_clicked)

    self.del_group_button = hildon.Button(gtk.HILDON_SIZE_AUTO_WIDTH | gtk.HILDON_SIZE_FINGER_HEIGHT,
                          hildon.BUTTON_ARRANGEMENT_VERTICAL)
    self.del_group_button.set_text(_("Remove group"), "")
    self.del_group_button.connect("clicked", self.del_group_clicked)

    self.add_item_button = hildon.Button(gtk.HILDON_SIZE_AUTO_WIDTH | gtk.HILDON_SIZE_FINGER_HEIGHT,
                          hildon.BUTTON_ARRANGEMENT_VERTICAL)
    self.add_item_button.set_text(_("Add item"), "")
    self.add_item_button.connect("clicked", self.add_item_clicked)

    self.del_item_button = hildon.Button(gtk.HILDON_SIZE_AUTO_WIDTH | gtk.HILDON_SIZE_FINGER_HEIGHT,
                          hildon.BUTTON_ARRANGEMENT_VERTICAL)
    self.del_item_button.set_text(_("Remove item"), "")
    self.del_item_button.connect("clicked", self.del_item_clicked)

    self.change_pass_button = hildon.Button(gtk.HILDON_SIZE_AUTO_WIDTH | gtk.HILDON_SIZE_FINGER_HEIGHT,
                          hildon.BUTTON_ARRANGEMENT_VERTICAL)
    self.change_pass_button.set_text(_("Change password"), "")
    self.change_pass_button.connect("clicked", self.change_password_clicked)

    self.about_button = hildon.Button(gtk.HILDON_SIZE_AUTO_WIDTH | gtk.HILDON_SIZE_FINGER_HEIGHT,
                          hildon.BUTTON_ARRANGEMENT_VERTICAL)
    self.about_button.set_text(_("About"), "")
    self.about_button.connect("clicked", self.about_clicked)

    self.add_detail_button = hildon.Button(gtk.HILDON_SIZE_AUTO_WIDTH | gtk.HILDON_SIZE_FINGER_HEIGHT,
                          hildon.BUTTON_ARRANGEMENT_VERTICAL)
    self.add_detail_button.set_text(_("Add detail"), "")
    self.add_detail_button.connect("clicked", self.add_detail_clicked)

    self.del_detail_button = hildon.Button(gtk.HILDON_SIZE_AUTO_WIDTH | gtk.HILDON_SIZE_FINGER_HEIGHT,
                          hildon.BUTTON_ARRANGEMENT_VERTICAL)
    self.del_detail_button.set_text(_("Remove detail"), "")
    self.del_detail_button.connect("clicked", self.del_detail_clicked)

    self.import_button = hildon.Button(gtk.HILDON_SIZE_AUTO_WIDTH | gtk.HILDON_SIZE_FINGER_HEIGHT,
                                      hildon.BUTTON_ARRANGEMENT_VERTICAL)
    self.import_button.set_text(_("Import"), "")
    self.import_button.connect("clicked", self.import_from_file_clicked)

    self.menu.append(self.add_group_button)
    self.menu.append(self.del_group_button)
    self.menu.append(self.add_item_button)
    self.menu.append(self.del_item_button)
    self.menu.append(self.import_button)
    self.menu.append(self.change_pass_button)
    self.menu.append(self.about_button)

    self.menu.show_all()
    self.window.set_app_menu(self.menu)

    self.context_menu = gtk.Menu()
    m = gtk.MenuItem("Rename")
    m.connect("activate", self.context_menu_clicked, "ren")
    self.context_menu.append(m)
    m = gtk.MenuItem("Move")
    m.connect("activate", self.context_menu_clicked, "mov")
    self.context_menu.append(m)
    m = gtk.MenuItem("Delete")
    m.connect("activate", self.context_menu_clicked, "del")
    self.context_menu.append(m)
    self.context_menu.show_all()

    self.window.connect("destroy", self.quit, None)

    self.panel_landscape = gtk.HPaned()
    self.panel_landscape.set_position(self.config.get(self.config.LANDSCAPE_SLIDER_SIZE))
    self.panel_portrait = gtk.VPaned()
    self.panel_portrait.set_position(self.config.get(self.config.PORTRAIT_SLIDER_SIZE))

    self.window.add(self.panel_portrait)

    # cria a lista com grupos e itens
    self.groupList = hildon.TouchSelector()
    # cria o modelo
    model = gtk.ListStore(gtk.gdk.Pixbuf, str, str)
    self.groupList.append_column(model, gtk.CellRendererPixbuf())

    # cria as colunas 
    column = self.groupList.get_column(0)
    column.clear()
    renderer = gtk.CellRendererPixbuf()
    column.pack_start(renderer, expand=False)
    column.add_attribute(renderer, 'pixbuf', self.LIST_COLUMN_ICON)

    renderer = gtk.CellRendererText()
    column.pack_start(renderer, expand=True)
    column.add_attribute(renderer, 'text', self.LIST_COLUMN_TEXT)

    renderer = gtk.CellRendererText()
    renderer.set_property("visible", False)
    column.pack_end(renderer)
    column.add_attribute(renderer, 'text', self.LIST_COLUMN_ID)


    self.panel_landscape.add1(self.groupList)
    self.groupList.connect("changed", self.list_clicked)
    #self.groupList.tap_and_hold_setup(menu = self.context_menu)

    self.panel_detail = gtk.VBox()
    self.panel_landscape.add2(self.panel_detail)

    self.item_detail = hildon.PannableArea()
    self.item_detail_area = gtk.VBox()
    self.item_detail.add_with_viewport(self.item_detail_area)
    self.panel_detail.pack_start(self.item_detail, True, True, 0)

    box = gtk.HBox()
    box.add(self.add_detail_button)
    box.add(self.del_detail_button)
    self.panel_detail.pack_end(box, False, False, 0)

    # cria o objeto responsável pela rotação da tela
    self.rotation_object = FremantleRotation("pySafe", self.window, cb=self.screen_rotation)
    # o deixa desativado por enquanto! Só ativa quando exibir a janela em si
    self.rotation_object.set_mode(FremantleRotation.NEVER)

    # This call show the window and also add the window to the stack
    self.window.show_all()


  def set_database(self, d):
    self.database = d


  def quit(self, v1, v2):
    self.config.set(self.config.LANDSCAPE_SLIDER_SIZE, self.panel_landscape.get_position())
    self.config.set(self.config.PORTRAIT_SLIDER_SIZE, self.panel_portrait.get_position())
    
    if self.database.save() != True:
      self.show_note("information", _("The database could not be updated. Check file permissions or disk space."))

    gtk.main_quit()


  def context_menu_clicked(self, src, data):
    #print self.groupList.get_active(0)
    print src


  def screen_rotation(self, mode):
    if mode == "landscape":
      if self.panel_portrait.get_child1() != None:
        self.panel_portrait.remove(self.groupList)
      self.panel_landscape.add1(self.groupList)
      if self.panel_portrait.get_child2() != None:
        self.panel_portrait.remove(self.panel_detail)
      self.panel_landscape.add2(self.panel_detail)
      self.window.remove(self.panel_portrait)
      self.window.add(self.panel_landscape)
      self.menu.show_all()
    elif mode == "portrait":
      if self.panel_landscape.get_child1() != None:
        self.panel_landscape.remove(self.groupList)
      self.panel_portrait.add1(self.groupList)
      if self.panel_landscape.get_child2() != None:
        self.panel_landscape.remove(self.panel_detail)
      self.panel_portrait.add2(self.panel_detail)
      self.window.remove(self.panel_landscape)
      self.window.add(self.panel_portrait)
      self.menu.hide_all()

    self.check_editable_details(mode == "landscape")

    self.window.show_all()

    if mode == "portrait":
      self.add_detail_button.get_parent().hide_all()


  def show(self):
    # habilita a rotação
    self.rotation_object.set_mode(FremantleRotation.AUTOMATIC)
    # mostra os grupos
    self.show_itens()


  def import_from_file_clicked(self, src):
    ImportWizard(self, self.database)
    self.show_itens()


  def __get_group_path_string(self):
    ret = ""
    if len(self.atual_group) != 0 and self.atual_group[0][:1] == "g":
      for i in self.atual_group:
        if i[:1] == "g":
          if len(ret) == 0:
            ret = i[1:]
          else:
            ret = "%s -> %s" % (ret, i[1:])
    return ret


  def add_group_clicked(self, src):
    entry = hildon.Entry(0)
    dialog = gtk.Dialog(parent=self.window, buttons=(_("Done"), gtk.RESPONSE_OK))
    grupos = self.__get_group_path_string()
    if len(grupos) == 0:
      dialog.set_title(_("New Group"))
    else:
      dialog.set_title(_("New Group in \"%s\"") % grupos)
    dialog.vbox.add(hildon.Caption(None, _("Name"), entry, None, True))
    dialog.show_all()
    response = dialog.run()
    dialog.destroy()
    if response == gtk.RESPONSE_OK:
      g = self.database.add_group(self.atual_group, entry.get_text())
      if g != None:
        while len(self.atual_group) > 0 and self.atual_group[-1][:1] != "g":
          self.atual_group.pop()
        self.atual_group.append(g)
        self.show_itens()
        # força a janela a se atualizar...se não fizer isso, o scroll abaixo pode não funcionar
        self.groupList.get_parent_window().process_updates(True)
      else:
        self.show_note("information", _("The group \"%s\" already exists!") % (entry.get_text()))


  def del_group_clicked(self, src):
    retcode = self.show_note("confirmation", _("Are you sure you want to remove the group \"%s\" and all its items?") % (self.__get_group_path_string()))
    if retcode == gtk.RESPONSE_OK:
      self.database.del_group(self.atual_group)
      self.atual_group.pop()
      self.show_itens()


  def add_item_clicked(self, src):
    entry = hildon.Entry(0)
    dialog = gtk.Dialog(parent=self.window, buttons=("Done", gtk.RESPONSE_OK))
    grupos = self.__get_group_path_string()
    if len(grupos) == 0:
      dialog.set_title(_("New Item"))
    else:
      dialog.set_title(_("New Item for Group \"%s\"") % grupos)
    dialog.vbox.add(hildon.Caption(None, _("Name"), entry, None, True))
    dialog.show_all()
    response = dialog.run()
    dialog.destroy()
    if response == gtk.RESPONSE_OK:
      i = self.database.add_item(self.atual_group, entry.get_text())
      if i != None:
        while len(self.atual_group) > 0 and self.atual_group[-1][:1] != "g":
          self.atual_group.pop()
        self.atual_group.append(i)
        self.show_itens()
        # força a janela a se atualizar...se não fizer isso, o scroll abaixo pode não funcionar
        self.groupList.get_parent_window().process_updates(True)
        # seta o elemento atual
        treemodel = self.groupList.get_model(0)
        it = treemodel.get_iter_first()
        while (it != None):
          if treemodel.get_value(it, self.LIST_COLUMN_ID) == i:
            self.groupList.select_iter(0, it, True)
            break
          it = treemodel.iter_next(it)
      else:
        self.show_note("information", _("The item \"%s\" already exists!") % entry.get_text())


  def del_item_clicked(self, src):
    group = self.__get_group_path_string()
    if len(group) > 0:
      msg = _("Are you sure you want to remove the item \"%s\" from the group \"%s\"?") % (self.atual_group[-1][1:], group)
    else:
      msg = _("Are you sure you want to remove the item \"%s\"?") % (self.atual_group[-1][1:])
    retcode = self.show_note("confirmation", msg)
    if retcode == gtk.RESPONSE_OK:
      self.database.del_item(self.atual_group)
      self.atual_group.pop()
      self.show_itens()


  def add_detail_clicked(self, src):
    entry = hildon.Entry(0)
    dialog = gtk.Dialog(parent=self.window, buttons=(_("Done"), gtk.RESPONSE_OK))
    grupos = self.__get_group_path_string()
    if len(grupos) == 0:
      dialog.set_title(_("New Detail for Item \"%s\"") % self.atual_group[-1][1:])
    else:
      dialog.set_title(_("New Detail for Item \"%s\" in Group \"%s\"") % (self.atual_group[-1][1:], grupos))
    dialog.vbox.add(hildon.Caption(None, _("Name"), entry, None, True))
    dialog.show_all()
    response = dialog.run()
    dialog.destroy()
    if response == gtk.RESPONSE_OK:
      if self.database.add_detail(self.atual_group, entry.get_text()) != None:
        self.show_details_for_item()
      else:
        self.show_note("information", _("The detail \"%s\" already exists!") % entry.get_text())


  def del_detail_clicked(self, src):
    RemoveDetailsWindow(self.database, self.atual_group, self)


  def about_clicked(self, src):
    dialog = gtk.AboutDialog()
    dialog.set_name("pySafe")
    dialog.set_version("0.7.2")
    dialog.set_authors(["Jorge Aguilar"])
    dialog.set_translator_credits(_("translator-credits"))
    dialog.set_logo(gtk.gdk.pixbuf_new_from_file_at_size('%s/icons/pysafe_48x48.png' % (sys.path[0]), 48, 48))
    dialog.run()
    dialog.destroy()


  def list_clicked(self, widget, column, user_data = None):
    if self.ignore_list_clicked:
      return

    self.remove_itens_from_list()

    c = self.groupList.get_active(0)
    treemodel = self.groupList.get_model(0)
    it = treemodel.get_iter_first()
    while c > 0:
      it = treemodel.iter_next(it)
      c = c - 1
    item_clicked = treemodel.get_value(it, self.LIST_COLUMN_ID)

    pos = item_clicked.find(":")
    if pos > 0 and item_clicked[:pos].isdigit() == True:
      i = int(item_clicked[:pos])
      while len(self.atual_group) > i:
        self.atual_group.remove(self.atual_group[len(self.atual_group) - 1])
      self.show_itens()
    elif item_clicked[:1] == "g":
      if len(self.atual_group) > 0 and self.atual_group[-1][:1] == "i":
        self.atual_group.pop()
      self.atual_group.append(item_clicked)
      self.show_itens()
    elif item_clicked[:1] == "i":
      if len(self.atual_group) > 0:
        if self.atual_group[-1][:1] == "i":
          self.atual_group[-1] = item_clicked
        else:
          self.atual_group.append(item_clicked)
      else:
        self.atual_group.append(item_clicked)

      self.show_details_for_item()


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
    itens = self.database.get(self.atual_group)

    self.remove_itens_from_list()

    # insere os itens na tela
    keys = itens.keys()
    keys.sort(key=str.lower)
    for i in keys:
      if i[1:2] == "0":
        view = hildon.Entry(0)
        view.set_text(itens[i])
        view.connect("changed", self.textview_changed, i)
      elif i[1:2] == "1":
        view = hildon.TextView()
        buf = gtk.TextBuffer()
        buf.set_text(itens[i])
        view.set_buffer(buf)
        buf.connect("changed", self.textview_changed, i)
      input_mode = view.get_property("hildon-input-mode")
      input_mode &= ~gtk.HILDON_GTK_INPUT_MODE_DICTIONARY
      view.set_property("hildon-input-mode", input_mode)
      label = gtk.Label(i[2:])
      label.set_alignment(0,0)
      self.item_detail_area.pack_start(label, False, True, 0)
      self.item_detail_area.pack_start(view, False, True, 0)

    self.check_editable_details(self.rotation_object.get_orientation() != "portrait")

    # exibe os itens
    self.item_detail_area.show_all()

    self.__menu_buttons_check()


  def show_itens(self):
    if self.ignore_list_clicked:
      return
  
    self.ignore_list_clicked = True

    self.remove_itens_from_list()

    el = []
    i = 0
    while i < len(self.atual_group):
      if self.atual_group[i][:1] == "g":
        el.append(self.atual_group[i])
      else:
        break
      i = i + 1

    # pega os valores e ordena
    keys = self.database.get(el)
    #keys.sort(key=str.lower, reverse=True)
    print keys
    keys.sort(key=str.lower)

    # apaga a lista exibida atualmente
    treemodel = self.groupList.get_model(0)
    treemodel.clear()

    # primeiro adiciona os grupos já abertos...
    counter = 0
    it = None
    if self.atual_group != None:
      for i in self.atual_group:
        if i[0] == "g":
          treemodel.append([self.FOLDER_OPENED_ICON, i[1:], "%i:%s" % (counter, i)])
          counter = counter + 1

    # adiciona os grupos fechados
    for i in keys:
      if i[0] == "g":
        treemodel.append([self.FOLDER_CLOSED_ICON, i[1:], i])

    # adiciona os possíveis itens
    for i in keys:
      if i[0] == "i":
        treemodel.append([None, i[1:], i])

    self.__menu_buttons_check()

    self.ignore_list_clicked = False


  def textview_changed(self, src, detail):
    if type(src) is hildon.Entry:
      self.database.set_detail(self.atual_group, detail, src.get_text())
    elif type(src) is gtk.TextBuffer:
      self.database.set_detail(self.atual_group, detail, src.get_text(src.get_start_iter(), src.get_end_iter()))


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
        self.show_note("information", _("The password can not be empty!"))
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
        self.show_note("information", _("The passwords are not equals!"))
      else:
        self.database.save(force = True, new_pass = pass1)
        self.show_note("information", _("Password changed!"))
        break


  def show_note(self, tipo, msg):
    note = hildon.Note(tipo, self.window, msg)
    response = gtk.Dialog.run(note)
    note.destroy()
    return response


  def __menu_buttons_check(self):
    self.add_group_button.set_sensitive(True)
    self.del_group_button.set_sensitive(len(self.atual_group) > 0 and self.atual_group[0][:1] == "g")

    self.add_item_button.set_sensitive(True)
    self.del_item_button.set_sensitive(len(self.atual_group) > 0 and self.atual_group[-1][:1] == "i")

    self.add_detail_button.set_sensitive(len(self.atual_group) > 0 and self.atual_group[-1][:1] == "i")
    self.del_detail_button.set_sensitive(self.add_detail_button.get_property("sensitive") and len(self.database.get(self.atual_group)) > 0)

    self.import_button.set_sensitive(True)
    self.change_pass_button.set_sensitive(True)
    self.about_button.set_sensitive(True)


"""
Esta classe exibe a janela de exclusão de detalhes do item
"""
class RemoveDetailsWindow:

  """
    Parâmetros:
    d - banco de dados
    p - caminho do item selecionado
    c - instância da janela principal
  """
  def __init__(self, d, p, c):
    self.database = d
    self.path = p
    self.instance = c

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
    MainWindow.show_details_for_item(self.instance)
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
      self.database.del_detail(self.path, model.get_value(iter, 1))
      model.remove(iter)


  def create_treeview(self, tvmode):
    tv = hildon.GtkTreeView(tvmode)

    renderer = gtk.CellRendererText()
    col = gtk.TreeViewColumn("Title", renderer, text=0)

    col.clear()
    renderer = gtk.CellRendererText()
    col.pack_start(renderer, expand=True)
    col.add_attribute(renderer, 'text', 0)

    renderer = gtk.CellRendererText()
    renderer.set_property("visible", False)
    col.pack_end(renderer)
    col.add_attribute(renderer, 'text', 1)

    tv.append_column(col)

    # Set multiple selection mode
    selection = tv.get_selection()
    selection.set_mode(gtk.SELECTION_MULTIPLE)

    store = gtk.ListStore(str, str)
    itens = self.database.get(self.path)
    keys = itens.keys()
    keys.sort(key=str.lower, reverse=True)
    # insere os itens na tela
    for i in keys:
      store.insert(0, [i[2:], i])

    tv.set_model(store)

    return tv


class ImportWizard:

  def __init__(self, mw, database):
    self.main_window = mw

    self.filename = hildon.Entry(0)
    self.import_type = hildon.TouchSelector()

    notebook = self.create_notebook()
    self.dialog = hildon.WizardDialog(self.main_window.window, _("Import Wizard"), notebook)
    self.dialog.set_forward_page_func(self.page_func)
    response = self.dialog.run()
    self.dialog.destroy()
    if response == hildon.WIZARD_DIALOG_FINISH:
      c = self.import_type.get_active(0)
      treemodel = self.import_type.get_model(0)
      it = treemodel.get_iter_first()
      while c > 0:
        it = treemodel.iter_next(it)
        c = c - 1
      item_clicked = treemodel.get_value(it, 1)
      import_from_file(database, self.filename.get_text(), int(item_clicked))


  def page_func(self, notebook, current_page_number, user_data):
    if current_page_number == 1:
      f = self.filename.get_text().strip()
      if len(f) == 0:
        return False
      if not os.path.isfile(f):
        self.main_window.show_note("information", _("File \"%s\" does not exist or it was not possible open it.") % f)
        return False

    return True


  def create_notebook(self):
    notebook = gtk.Notebook()

    label_welcome = gtk.Label(_("This wizard will guide you through the importing data process."))
    label_welcome.set_line_wrap(True)

    button = hildon.Button(gtk.HILDON_SIZE_AUTO_WIDTH | gtk.HILDON_SIZE_FINGER_HEIGHT,
                           hildon.BUTTON_ARRANGEMENT_VERTICAL)
    button.set_image(gtk.image_new_from_stock(gtk.STOCK_FILE, gtk.ICON_SIZE_BUTTON))
    button.connect("clicked", self.file_button_clicked)

    tab1 = gtk.Table(3, 2)
    tab1.attach(gtk.Label(""), 0, 2, 0, 1)
    tab1.attach(self.filename, 0, 1, 1, 2)
    tab1.attach(button, 1, 2, 1, 2, xoptions = gtk.SHRINK, yoptions = gtk.SHRINK)
    tab1.attach(gtk.Label(""), 0, 2, 2, 3)

    model = gtk.ListStore(str, str)
    self.import_type.append_column(model, gtk.CellRendererText())
    column = self.import_type.get_column(0)
    column.clear()
    renderer = gtk.CellRendererText()
    column.pack_start(renderer, expand=True)
    column.add_attribute(renderer, 'text', 0)
    renderer = gtk.CellRendererText()
    renderer.set_property("visible", False)
    column.pack_end(renderer)
    column.add_attribute(renderer, 'text', 1)

    tipos = import_from_file.get_types()
    for i in tipos:
      model.append([tipos[i], i])

    notebook.append_page(label_welcome)
    notebook.append_page(tab1, gtk.Label(_("File location")))
    notebook.append_page(self.import_type, gtk.Label(_("File type")))

    notebook.show_all()

    return notebook


  def file_button_clicked(self, src):
    chooser = hildon.FileChooserDialog(self.main_window.window, gtk.FILE_CHOOSER_ACTION_OPEN, hildon.FileSystemModel())
    chooser.set_default_response(gtk.RESPONSE_OK)
    chooser.set_current_folder(os.path.expanduser('~'))
    if chooser.run() == gtk.RESPONSE_OK:
      self.filename.set_text(chooser.get_filename())
    chooser.destroy()


class Configuration:

  PORTRAIT_SLIDER_SIZE = 1
  LANDSCAPE_SLIDER_SIZE = 2
  DATABASE_FILE = 3

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

    # verifica o tamanho do slider em modo retrato
    tmp = 300
    if self.config.has_option('Window', 'portrait_slider'):
      tmp = self.config.get('Window', 'portrait_slider')
      if not tmp.isdigit() or int(tmp) > 800:
        tmp = 300
    # salva o tamanho na configuração para garantir que não há erros
    self.config.set('Window', 'portrait_slider', tmp)

    # verifica o tamanho do slider em modo paisagem
    tmp = 300
    if self.config.has_option('Window', 'landscape_slider'):
      tmp = self.config.get('Window', 'landscape_slider')
      if not tmp.isdigit() or int(tmp) > 800:
        tmp = 300
    self.config.set('Window', 'landscape_slider', tmp)

  def get(self, item):
    if item == self.PORTRAIT_SLIDER_SIZE:
      return self.config.getint('Window', 'portrait_slider')
    elif item == self.LANDSCAPE_SLIDER_SIZE:
      return self.config.getint('Window', 'landscape_slider')

    return None

  def set(self, item, value):
    # se o valor é igual, não tem por alterar!
    if self.get(item) == value:
      return

    if item == self.PORTRAIT_SLIDER_SIZE:
      self.config.set('Window', 'portrait_slider', value)
    elif item == self.LANDSCAPE_SLIDER_SIZE:
      self.config.set('Window', 'landscape_slider', value)

    self.changed = True


class pysafe:
  def __init__(self):

    gettext.install('pysafe', sys.path[0])

    config = Configuration()

    # cria a janela principal
    win = MainWindow(config)

    while True:
      # cria a janela para pedir a senha
      passwordDialog = hildon.GetPasswordDialog(win.window, True)
      passwordDialog.set_title("")
      passwordDialog.set_caption(_("Type your password"))
      passwordDialog.set_property("password", "")
      response = passwordDialog.run()
      pass1 = passwordDialog.get_password()
      passwordDialog.destroy() 
      if response != gtk.RESPONSE_OK:
        return

      if len(pass1) == 0:
        win.show_note("information", _("The password can not be empty!"))
        continue

      database = Dados(pass1)
      ret = database.load()
      if ret == database.DATABASE_OK:
        # tenta salvar o banco (para garantir que será atualizavel)
        if database.save(force = True) == False:
          win.show_note("information", _("The database are not updataple. Check file permissions or disk space."))
        break
      elif ret == database.ARQUIVO_NAO_LOCALIZADO:
        response = win.show_note("confirmation", _("Database file not found. Confirm the creation of a new one?"))
        if response != gtk.RESPONSE_OK:
          return

        # solicita para redigitar
        passwordDialog = hildon.GetPasswordDialog(win.window, True)
        passwordDialog.set_title("")
        passwordDialog.set_caption(_("Re-type your password"))
        passwordDialog.set_property("password", "")
        response = passwordDialog.run()
        passwordDialog.hide() 
        if response != gtk.RESPONSE_OK:
          return

        if passwordDialog.get_password() != pass1:
          win.show_note("information", _("The passwords are not equals!"))
        else:
          database.save(force = True)
          break
      else:
        texto = _("An undefined error has ocurred!")
        if ret == database.SENHA_INVALIDA:
          texto = _("Invalid password!")
        elif ret == database.DADOS_CORROMPIDOS:
          texto = _("Database corrupted or invalid password!")
        win.show_note("information", texto)

    passwordDialog.destroy() 

    win.set_database(database)
    win.show()
    gtk.main()

    config.save()

