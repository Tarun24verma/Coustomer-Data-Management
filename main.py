import flet as ft
import database_manager as dbm
import os
import threading
import time

def main(page: ft.Page):
    page.title = "Customer Data Manager"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.bgcolor = "#F0F2F5"
    page.window_width = 1100
    page.window_height = 850

    notification_text = ft.Text("", color="white", weight="bold")
    notification_container = ft.Container(
        content=notification_text,
        bgcolor="blue",
        padding=10,
        border_radius=8,
        visible=False,  # Hidden by default
    )

    # Use a Row to center the notification at the top of the overlay
    page.overlay.append(
        ft.Row(
            controls=[notification_container],
            alignment="center", # Using string instead of ft.MainAxisAlignment.CENTER
        )
    )

    def notify(message, color="blue"):
        print(f">>> NOTIFICATION: {message}")
        
        notification_text.value = message
        notification_container.bgcolor = color
        notification_container.visible = True
        page.update()
        
        # Hide after 2 seconds
        def hide_later():
            time.sleep(2)
            notification_container.visible = False
            page.update()
        
        threading.Thread(target=hide_later, daemon=True).start()

    # --- NAVIGATION ---
    def navigate_to_create(e):
        page.clean()
        show_create_view()
        page.update()

    def navigate_to_welcome(e=None):
        page.clean()
        show_welcome_view()
        page.update()

    def open_database(db_name):
        page.clean()
        show_dashboard_view(db_name)
        page.update()

    # --- VIEW: WELCOME SCREEN ---
    def show_welcome_view():
        current_path = dbm.get_base_path()
        
        # 1. Path Input Logic
        path_input = ft.TextField(
            value=current_path,
            label="Database Storage Folder Path",
            hint_text="Paste your folder path here (e.g., D:\MyData)",
            expand=True,
            text_size=12
        )

        def change_path_manually(e):
            new_path = path_input.value.strip()
            if os.path.exists(new_path):
                dbm.save_config(new_path)
                notify("Storage path updated!", "green")
                navigate_to_welcome()
            else:
                notify("Invalid path! Folder does not exist.", "red")

        # 2. Database List
        databases = dbm.list_databases()
        db_list = ft.Column(spacing=10)
        for name in databases:
            db_list.controls.append(
                ft.Container(
                    content=ft.Row([
                        ft.Text(name, size=18, weight="bold", expand=True),
                        ft.FilledButton("Open", on_click=lambda _, n=name: open_database(n))
                    ]),
                    padding=15, bgcolor="white", border_radius=10,
                )
            )

        # 3. UI LAYOUT
        page.add(
            ft.Container(
                padding=40,
                content=ft.Column([
                    ft.Text("My Databases", size=32, weight="bold"),
                    
                    # Storage Settings Section
                    ft.Container(
                        content=ft.Column([
                            ft.Text("Storage Settings", size=16, weight="bold"),
                            ft.Row([
                                path_input,
                                ft.ElevatedButton("Update Path", on_click=change_path_manually)
                            ]),
                            ft.Text("Paste a folder path above and click Update to change where databases are stored.", size=11, italic=True)
                        ]),
                        padding=20,
                        bgcolor="#E5E7EB",
                        border_radius=10
                    ),
                    
                    ft.Divider(height=40),
                    
                    # List Header
                    ft.Row([
                        ft.Text("Existing Databases", size=20, weight="bold"),
                        ft.FilledButton("Create New Database", on_click=navigate_to_create)
                    ], alignment="spaceBetween"),
                    
                    db_list if databases else ft.Text("No databases found in the folder above.")
                ], scroll="auto")
            )
        )
        page.update()

    # --- VIEW: CREATE ---
    def show_create_view():
        fields_container = ft.Column()
        def add_field_row(e=None):
            row = ft.Row([
                ft.TextField(hint_text="Field Name", expand=2),
                ft.Dropdown(value="Text", expand=1, options=[ft.dropdown.Option("Text"), ft.dropdown.Option("Number")]),
                ft.TextButton("Remove", on_click=lambda _: fields_container.controls.remove(row) or page.update())
            ])
            fields_container.controls.append(row)
            page.update()
        
        def save_db(e):
            if name_input.value:
                f_list = [{"label": r.controls[0].value, "type": r.controls[1].value} for r in fields_container.controls if r.controls[0].value]
                dbm.create_new_database(name_input.value, f_list)
                notify(f"Database '{name_input.value}' created!", "green")
                navigate_to_welcome()

        name_input = ft.TextField(label="Database Name")
        page.add(ft.Container(padding=40, content=ft.Column([
            ft.TextButton("<- Back", on_click=navigate_to_welcome),
            ft.Text("New Database", size=28),
            name_input,
            ft.Row([ft.Text("Fields"), ft.FilledButton("Add", on_click=add_field_row)]),
            fields_container,
            ft.FilledButton("Create", width=400, on_click=save_db)
        ], scroll="auto")))
        add_field_row()

    # --- VIEW: DASHBOARD ---
    def show_dashboard_view(db_name):
        fields = dbm.get_db_fields(db_name)
        
        # 1. Variables and UI controls
        input_controls = {}
        dlg_content = ft.Column(spacing=10, tight=True)
        for f in fields:
            tf = ft.TextField(label=f['label'], width=400)
            input_controls[f['id']] = tf
            dlg_content.controls.append(tf)

        table = ft.DataTable(
            columns=[ft.DataColumn(ft.Text("ID"))] + 
                    [ft.DataColumn(ft.Text(f['label'])) for f in fields] + 
                    [ft.DataColumn(ft.Text("Actions"))],
            rows=[]
        )

        # 2. Logic Functions
        def refresh_table(e=None):
            query = search_field.value if search_field.value else ""
            customers = dbm.get_customers(db_name, search_query=query)
            table.rows.clear()
            for c in customers:
                def make_del_handler(cid):
                    return lambda _: dbm.delete_customer(db_name, cid) and notify(f"Deleted {cid}", "blue") or refresh_table()

                table.rows.append(ft.DataRow(cells=[
                    ft.DataCell(ft.Text(str(c['id'])))] + 
                    [ft.DataCell(ft.Text(c.get(f['id'], ""))) for f in fields] + 
                    [ft.DataCell(ft.Row([
                        ft.TextButton("Files", on_click=lambda _, cid=c['id']: os.startfile(dbm.get_customer_path(db_name, cid))),
                        ft.TextButton("Del", on_click=make_del_handler(c['id']))
                    ]))]
                ))
            page.update()

        def save_customer(e):
            data = {f_id: ctrl.value for f_id, ctrl in input_controls.items()}
            if dbm.add_customer(db_name, data):
                add_dlg.open = False
                page.update() # Close dialog first
                notify("Customer Added Successfully", "green") # Then notify
                for ctrl in input_controls.values(): ctrl.value = ""
                refresh_table()

        # 3. Dialog
        add_dlg = ft.AlertDialog(
            title=ft.Text("Add Record"),
            content=dlg_content,
            actions=[
                ft.TextButton("Cancel", on_click=lambda _: setattr(add_dlg, "open", False) or page.update()),
                ft.FilledButton("Save", on_click=save_customer),
            ],
        )

        def open_add_dlg(e):
            page.overlay.append(add_dlg)
            add_dlg.open = True
            page.update()

        # 4. Final Layout
        search_field = ft.TextField(hint_text="Search...", expand=True, on_change=refresh_table)
        page.add(ft.Container(padding=20, content=ft.Column([
            ft.Row([
                ft.TextButton("<- Back", on_click=navigate_to_welcome),
                ft.Text(f"DB: {db_name}", size=24, weight="bold", expand=True),
                ft.FilledButton("Add Customer", on_click=open_add_dlg)
            ]),
            ft.Divider(),
            ft.Row([search_field, ft.ElevatedButton("Clear", on_click=lambda _: setattr(search_field, "value", "") or refresh_table())]),
            ft.Container(content=ft.Column([table], scroll="auto"), bgcolor="white", border_radius=10, padding=10, expand=True)
        ], expand=True)))
        refresh_table()

    # Initial App Entry
    show_welcome_view()
    page.update()

if __name__ == "__main__":
    ft.app(target=main)