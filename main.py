import math
import os
import pathlib
import sys
import tkinter as tk
from tkinter import ttk

import sqlite3
from tkinter import messagebox
from typing import List

if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
    executable_folder = pathlib.Path(sys.executable).parent
    DIR = executable_folder
else:
    DIR = pathlib.Path(__file__).parent

class DB():
    def __init__(self):

        db_dir = os.path.join(DIR, "herbalist.db3")
        self.conn = sqlite3.connect(db_dir)
        self.curs = self.conn.cursor()
        self.curs.execute("PRAGMA foreign_keys = ON;")

    def select_by_groups_intersect(self, groups: str):
        groups = groups.strip()
        groups_list = groups.split(";")
        groups_list = [grp.strip() for grp in groups_list if len(grp) != 0]
        # groups_list [grp for grp in groups_list if len(grp) != 0]
        # groups_str = ",".join(groups_list)
        one_select = 'SELECT herb FROM herb_subgroup WHERE subgroup = (?)'
        one_select_list = [one_select for _ in range(len(groups_list))]
        for i, select in enumerate(one_select_list):
            one_select_list[i] = select.replace('?', '\'' + groups_list[i] + '\'')

        all_selects = " INTERSECT ".join(one_select_list)

        self.curs.execute(
            all_selects
        )
        rows = self.curs.fetchall()
        return [row[0] for row in rows]

    def select_by_groups_union(self, groups: str):
        # groups = 'аллергия; порошок; '
        groups = groups.strip()
        groups_list = groups.split(";")
        groups_list = [ '\'' + grp.strip() + '\'' for grp in groups_list if len(grp) != 0]
        
        statement = 'SELECT herb, GROUP_CONCAT(subgroup) AS ch FROM herb_subgroup where subgroup IN (%s) GROUP BY herb ORDER by COUNT(subgroup) DESC, herb;' \
        % ', '.join(group for group in groups_list)
        self.curs.execute(
            statement
        )
        rows = self.curs.fetchall()
        return rows

    
    def add_combination(self, herb: str, group: str):
        first_letter = herb[0]
        herb = herb.lower()
        group = group.lower()
        try:
            self.curs.execute(
                """
                INSERT INTO herb_subgroup(letter, herb, subgroup)
                VALUES (?, ?, ?);
                """, (first_letter, herb, group)
            )
        except sqlite3.IntegrityError:
            messagebox.showerror("Error", "Препарат или группа отсутствуют в таблице")
            return
        self.conn.commit()

    def get_all_groups(self):
            self.curs.execute(
                """
                SELECT subgroup FROM subgroups ORDER BY subgroup
                """
            )
            items = self.curs.fetchall()
            items_right_view = [item[0] for item in items]
            return items_right_view
    
    def get_all_herbs(self):
            self.curs.execute(
                """
                SELECT herb FROM herbs ORDER BY herb
                """
            )
            items = self.curs.fetchall()
            items_right_view = [item[0] for item in items]
            return items_right_view



class Main(tk.Frame):
    def __init__(self, root_obj: tk.Tk, db_obj: DB):
        super().__init__(master=root_obj)
        self.root= root_obj
        self.db = db_obj
        self.init_main()
        self.show_all_combinations()

    def init_main(self):
        toolbar = tk.Frame(bg='#d7d8e0', bd=2)
        toolbar.pack(side=tk.TOP, fill=tk.X)
        btn_select = tk.Button(toolbar, text='Поиск', command=self.open_filter_dialog, bg='#d7d8e0', bd=0,
                                    compound=tk.TOP)
        btn_select.pack(side=tk.LEFT)

        btn_add_combination = tk.Button(toolbar, text='Добавить/удалить комбинацию', command=self.open_add_combination_dialog, bg='#d7d8e0', bd=0,
                                    compound=tk.TOP)
        btn_add_combination.pack(side=tk.LEFT)

        btn_add_herb = tk.Button(toolbar, text='Добавить/удалить препарат', command=self.open_add_herb_dialog, bg='#d7d8e0', bd=0,
                                    compound=tk.TOP)
        btn_add_herb.pack(side=tk.LEFT)

        btn_add_group = tk.Button(toolbar, text='Добавить/удалить группу', command=self.open_add_group_dialog, bg='#d7d8e0', bd=0,
                                    compound=tk.TOP)
        btn_add_group.pack(side=tk.LEFT)

        # treeframe = tk.Frame(self)
        
        self.tree = ttk.Treeview(self.root, columns=('', 'Лекарство', 'Группа'), show='headings')
        w = self.root.winfo_screenwidth()
        self.tree.column(column='', width=math.ceil(0.1*w), anchor=tk.CENTER)
        self.tree.column(column='Лекарство', width=math.ceil(0.5*w), anchor=tk.CENTER)
        self.tree.column(column='Группа', width=math.ceil(0.4*w), anchor=tk.CENTER)

        self.tree.heading(column='', text='')
        self.tree.heading(column='Лекарство', text='Лекарство')
        self.tree.heading(column='Группа', text='Группа')

        # treeframe.pack(padx=19, fill='both', expand="yes")
        self.tree.pack(fill=tk.BOTH, expand=1)

        self.btn_reset = tk.Button(master=self.root, text='Сброс', command=self.show_all_combinations, state=tk.DISABLED)
        self.btn_reset.pack(side=tk.BOTTOM, pady=50)

    def show_all_combinations(self):
        self.db.curs.execute('SELECT letter, herb, subgroup FROM herb_subgroup ORDER BY herb')
        [self.tree.delete(i) for i in self.tree.get_children()]
        [self.tree.insert('', 'end', values=row) for row in self.db.curs.fetchall()]
        self.btn_reset['state'] = tk.DISABLED

    def open_filter_dialog(self):
        SelectDialog(self.root, self)

    def show_herbs_by_groups(self):
        pass

    def open_add_combination_dialog(self):
        AddCombinationDialog(self.root, self)

    def open_add_herb_dialog(self):
        AddDeleteHerbDialog(self.root, self)

    def open_add_group_dialog(self):
        AddGroupDialog(self.root, self)

    def visualize_selected_herbs_intersect(self, groups: str):
        selected = self.db.select_by_groups_intersect(groups=groups)
        [self.tree.delete(i) for i in self.tree.get_children()]
        selected_rows_for_treeview = [['', row, ''] for row in selected]
        [self.tree.insert('', 'end', values=row) for row in selected_rows_for_treeview]
    
    def visualize_selected_herbs_union(self, groups: str):
        selected = self.db.select_by_groups_union(groups=groups)
        [self.tree.delete(i) for i in self.tree.get_children()]
        selected_rows_for_treeview = [['', row[0], row[1]] for row in selected]
        [self.tree.insert('', 'end', values=row) for row in selected_rows_for_treeview]

class Dialog(tk.Toplevel):
    def __init__(self, root_obj: tk.Tk, view: Main):
        super().__init__(root_obj)
        self.view = view
        self.geometry("400x220+400+300")
        self.resizable(width=False, height=False)
        self.grab_set()
        self.focus_set()


class AddDeleteHerbDialog(Dialog):
    def __init__(self, root_obj: tk.Tk, view: Main):
        super().__init__(root_obj=root_obj, view=view)
        self.title("Добавить препарат")
        label_herb = tk.Label(self, text='Название препарата')
        label_herb.place(x=50, y=50)

        self.entry_herb_name = ttk.Entry(master=self)
        self.entry_herb_name.place(x=200, y=50)

        def add_herb(herb):
            self.view.db.curs.execute(
                """
                SELECT COUNT(herb) FROM herbs
                WHERE herb = ?
                """,(herb,)
            )
            N = self.view.db.curs.fetchall()[0][0]
            if N != 0:
                messagebox.showerror("Error", "Такой препарат уже есть в таблице")
                return
            self.view.db.curs.execute(
                """
                INSERT INTO herbs(herb) VALUES(?)
                """, (herb,)
            )
            self.view.db.conn.commit()
            self.destroy()

        def delete_herb(herb):
            self.view.db.curs.execute(
                """
                SELECT COUNT(herb) FROM herbs
                WHERE herb = ?
                """,(herb,)
            )
            N = self.view.db.curs.fetchall()[0][0]
            if N == 0:
                messagebox.showerror("Error", "Такой препарата нет в таблице")
                return
            self.view.db.curs.execute(
                """
                DELETE FROM herbs WHERE herb = ?
                """, (herb,)
            )
            self.view.db.conn.commit()
            self.destroy()

        btn_add = ttk.Button(self, text="Добавить",
                                command=lambda: add_herb(self.entry_herb_name.get().lower()))
        btn_add.place(x=100, y=150)

        btn_remove = ttk.Button(self, text="Удалить",
                                command=lambda: delete_herb(self.entry_herb_name.get().lower()))
        btn_remove.place(x=200, y=150)


class AddGroupDialog(Dialog):
    def __init__(self, root_obj: tk.Tk, view: Main):
        super().__init__(root_obj=root_obj, view=view)
        self.title("Добавить группу")
        label_herb = tk.Label(self, text='Название группы')
        label_herb.place(x=50, y=50)

        self.entry_herb_name = ttk.Entry(master=self)
        self.entry_herb_name.place(x=200, y=50)

        def add_item(item):
            self.view.db.curs.execute(
                """
                SELECT COUNT(subgroup) FROM subgroups
                WHERE subgroup = ?
                """,(item,)
            )
            N = self.view.db.curs.fetchall()[0][0]
            if N != 0:
                messagebox.showerror("Error", "Такой препарат уже есть в таблице")
                return
            self.view.db.curs.execute(
                """
                INSERT INTO subgroups(subgroup) VALUES(?)
                """, (item,)
            )
            self.view.db.conn.commit()
            # self.view.show_all_combinations()
            self.destroy()

        def delete_item(item):
            self.view.db.curs.execute(
                """
                SELECT COUNT(subgroup) FROM subgroups
                WHERE subgroup = ?
                """,(item,)
            )
            N = self.view.db.curs.fetchall()[0][0]
            if N == 0:
                messagebox.showerror("Error", "Такой группы нет в таблице")
                return
            self.view.db.curs.execute(
                """
                DELETE FROM subgroups WHERE subgroup = ?
                """, (item,)
            )
            self.view.db.conn.commit()
            self.destroy()
        
        

        btn_apply = ttk.Button(self, text="Добавить",
                                command=lambda: add_item(self.entry_herb_name.get().lower()))
        btn_apply.place(x=100, y=150)

        btn_remove = ttk.Button(self, text="Удалить",
                                command=lambda: delete_item(self.entry_herb_name.get().lower()))
        btn_remove.place(x=200, y=150)


class AddCombinationDialog(Dialog):
    def __init__(self, root_obj: tk.Tk, view: Main):
        super().__init__(root_obj=root_obj, view=view)
        self.title("Добавление пары препарат-группа")
        self.geometry("400x220+400+300")
        self.resizable(width=False, height=False)

        self.entry_herb_name = ttk.Entry(master=self)
        self.entry_herb_name.place(x=200, y=50)

        self.entry_group_name = ttk.Entry(master=self)
        self.entry_group_name.place(x=200, y=100)

        all_herbs = self.view.db.get_all_herbs()
        all_groups = self.view.db.get_all_groups()

        self.cpb_herbs = ttk.Combobox(self, values=all_herbs)
        self.cpb_herbs.place(x=50, y=50)

        self.cpb_herbs.bind('<<ComboboxSelected>>',
                              func=lambda func: self.entry_herb_name.insert('end', self.cpb_herbs.get()))
        
        self.cpb_groups = ttk.Combobox(self, values=all_groups)
        self.cpb_groups.place(x=50, y=100)

        self.cpb_groups.bind('<<ComboboxSelected>>',
                              func=lambda func: self.entry_group_name.insert('end', self.cpb_groups.get()))

        label_herb = tk.Label(self, text='Название препарата')
        label_herb.place(x=50, y=20)


        label_group = tk.Label(self, text='Название группы')
        label_group.place(x=50, y=75)

        btn_add = ttk.Button(self, text="Добавить", command=self.add_and_close)
        btn_add.place(x=50, y=150)

        btn_remove = ttk.Button(self, text="Удалить", command=self.delete_and_close)
        btn_remove.place(x=150, y=150)

    def add_and_close(self):
        self.view.db.add_combination(herb=self.entry_herb_name.get(), group=self.entry_group_name.get())
        self.view.show_all_combinations()
        self.destroy()

    def delete_and_close(self):
        self.view.db.curs.execute(
                """
                DELETE FROM herb_subgroup WHERE herb = ? AND subgroup = ?
                """, (self.entry_herb_name.get(), self.entry_group_name.get())
            )
        self.view.db.conn.commit()
        self.view.show_all_combinations()
        self.destroy()


class SelectDialog(Dialog):
    def __init__(self, root_obj: tk.Tk, view: Main):
        super().__init__(root_obj=root_obj, view=view)
        self.title("Поиск препаратов по группе")
        self.geometry("400x220+400+300")
        self.resizable(width=False, height=False)
        
        label_group = tk.Label(self, text='Выбранные')
        label_group.place(x=50, y=50)

        self.entry_group_name = ttk.Entry(master=self)
        self.entry_group_name.place(x=200, y=50)

        label_all_groups = tk.Label(self, text='Группы')
        label_all_groups.place(x=50, y=80)

        left_values_from_db = self.view.db.get_all_groups()
        # last_selected = ''
        # def update_cpb_values():
        #     self.cpb_groups["values"].remove(last_selected)
            
        self.cpb_groups = ttk.Combobox(self, values=left_values_from_db)
        self.cpb_groups.place(x=200, y=80)
        def insert_to_entry(item):
            last_selected = item
            self.entry_group_name.insert('end', last_selected + '; ')

        self.cpb_groups.bind('<<ComboboxSelected>>',
                              func=lambda func: insert_to_entry(self.cpb_groups.get()))


        btn_apply_intersect = ttk.Button(self, text="Пересечение", command=self.apply_intersect_and_close)
        btn_apply_intersect.place(x=50, y=110)

        btn_apply_union = ttk.Button(self, text="Объединение", command=self.apply_union_and_close)
        btn_apply_union.place(x=150, y=110)
        # self.apply_and_close()

    def apply_intersect_and_close(self):
        self.view.visualize_selected_herbs_intersect(self.entry_group_name.get())
        self.view.btn_reset['state'] = tk.ACTIVE
        self.destroy()
    
    def apply_union_and_close(self):
        self.view.visualize_selected_herbs_union(self.entry_group_name.get())
        self.view.btn_reset['state'] = tk.ACTIVE
        self.destroy()



if __name__ == "__main__":
    root = tk.Tk()
    db = DB()
    app = Main(root, db)
    app.pack()

    root.title("Herbalist")
    root.geometry("1800x900+150+100")
    # root.geometry("{0}x{1}+0+0".format(root.winfo_screenwidth(), root.winfo_screenheight()))    
    # root.resizable(False, False)
    root.mainloop()