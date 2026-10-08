import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
import pacientes
import medicos
import citas

# ============================================================
# CONTROL DE CITAS MÉDICAS
# Interfaz de escritorio 100% Python con Tkinter/ttk.
# Basada visualmente en la maqueta entregada.
# ============================================================

BG = "#F5F7FA"
WHITE = "#FFFFFF"
BLUE = "#1769E0"
BLUE_LIGHT = "#EAF2FF"
TEXT = "#1D2938"
MUTED = "#8993A2"
BORDER = "#E5EAF0"
GREEN = "#168252"
GREEN_BG = "#E8F8F0"
YELLOW = "#956B08"
YELLOW_BG = "#FFF4D8"
RED = "#B33D48"
RED_BG = "#FDEBED"

FONT = "Segoe UI"

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("MedCheck — Control de Citas Médicas")
        self.geometry("1240x760")
        self.minsize(980, 650)
        self.configure(bg=BG)

        self.style = ttk.Style(self)
        self.style.theme_use("clam")
        self.style.configure("Treeview", background=WHITE, fieldbackground=WHITE,
                             foreground=TEXT, rowheight=34, font=(FONT, 9),
                             borderwidth=0)
        self.style.configure("Treeview.Heading", background="#FBFCFD",
                             foreground=MUTED, font=(FONT, 8, "bold"),
                             relief="flat")
        self.style.map("Treeview", background=[("selected", BLUE_LIGHT)],
                       foreground=[("selected", TEXT)])

        self.sidebar = tk.Frame(self, bg=WHITE, width=220)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        self.body = tk.Frame(self, bg=BG)
        self.body.pack(side="left", fill="both", expand=True)

        self.build_sidebar()
        self.build_topbar()
        self.content = tk.Frame(self.body, bg=BG)
        self.content.pack(fill="both", expand=True, padx=34, pady=28)

        self.show_dashboard()

    def build_sidebar(self):
        brand = tk.Frame(self.sidebar, bg=WHITE)
        brand.pack(fill="x", padx=14, pady=(18, 28))
        icon = tk.Label(brand, text="✚", bg=BLUE, fg="white",
                        font=(FONT, 13, "bold"), width=3, height=1)
        icon.pack(side="left")
        b = tk.Frame(brand, bg=WHITE)
        b.pack(side="left", padx=8)
        tk.Label(b, text="MedCheck", bg=WHITE, fg=TEXT,
                 font=(FONT, 12, "bold")).pack(anchor="w")
        tk.Label(b, text="Control médico", bg=WHITE, fg=MUTED,
                 font=(FONT, 8)).pack(anchor="w")

        self.nav_buttons = {}
        for key, label, symbol, command in [
            ("dashboard", "Dashboard", "▦", self.show_dashboard),
            ("pacientes", "Pacientes", "♙", self.show_pacientes),
            ("medicos", "Médicos", "♙", self.show_medicos),
            ("citas", "Citas", "▣", self.show_citas),
        ]:
            btn = tk.Button(self.sidebar, text=f"  {symbol}   {label}",
                            command=command, anchor="w", relief="flat",
                            bd=0, cursor="hand2", padx=14, pady=9,
                            bg=WHITE, fg="#687486", activebackground=BLUE_LIGHT,
                            activeforeground=BLUE, font=(FONT, 9))
            btn.pack(fill="x", padx=10, pady=1)
            self.nav_buttons[key] = btn

        bottom = tk.Frame(self.sidebar, bg=WHITE)
        bottom.pack(side="bottom", fill="x", padx=15, pady=16)
        tk.Frame(bottom, bg=BORDER, height=1).pack(fill="x", pady=(0, 12))
        tk.Label(bottom, text="EF", bg=BLUE_LIGHT, fg=BLUE,
                 font=(FONT, 8, "bold"), width=4, height=2).pack(side="left")
        user = tk.Frame(bottom, bg=WHITE)
        user.pack(side="left", padx=8)
        tk.Label(user, text="Edgard Francisco", bg=WHITE, fg=TEXT,
                 font=(FONT, 8, "bold")).pack(anchor="w")
        tk.Label(user, text="Administrador", bg=WHITE, fg=MUTED,
                 font=(FONT, 7)).pack(anchor="w")

    def build_topbar(self):
        bar = tk.Frame(self.body, bg=WHITE, height=54,
                       highlightbackground=BORDER, highlightthickness=1)
        bar.pack(fill="x")
        bar.pack_propagate(False)
        self.breadcrumb = tk.Label(bar, text="MedCheck  ›  Panel de Control",
                                   bg=WHITE, fg=MUTED, font=(FONT, 8))
        self.breadcrumb.pack(side="left", padx=30)
        tk.Label(bar, text="♧", bg=WHITE, fg="#687486",
                 font=(FONT, 13)).pack(side="right", padx=28)

    def set_active(self, key, title):
        for name, btn in self.nav_buttons.items():
            if name == key:
                btn.configure(bg=BLUE_LIGHT, fg=BLUE)
            else:
                btn.configure(bg=WHITE, fg="#687486")
        self.breadcrumb.configure(text=f"MedCheck  ›  {title}")

    def clear(self):
        for child in self.content.winfo_children():
            child.destroy()

    def title_row(self, title, subtitle, button_text=None, command=None):
        row = tk.Frame(self.content, bg=BG)
        row.pack(fill="x", pady=(0, 20))
        left = tk.Frame(row, bg=BG)
        left.pack(side="left")
        tk.Label(left, text=title, bg=BG, fg=TEXT,
                 font=(FONT, 19, "bold")).pack(anchor="w")
        tk.Label(left, text=subtitle, bg=BG, fg=MUTED,
                 font=(FONT, 9)).pack(anchor="w", pady=(3,0))
        if button_text:
            tk.Button(row, text=button_text, command=command, bg=BLUE,
                      fg="white", relief="flat", bd=0, padx=13, pady=8,
                      cursor="hand2", font=(FONT, 8, "bold")).pack(side="right")

    def card(self, parent, width=None):
        frame = tk.Frame(parent, bg=WHITE, highlightbackground=BORDER,
                         highlightthickness=1)
        if width:
            frame.configure(width=width)
            frame.pack_propagate(False)
        return frame

    def confirmar_eliminacion(self, titulo, mensaje):
        win = tk.Toplevel(self)
        win.title(titulo)
        win.geometry("430x210")
        win.resizable(False, False)
        win.configure(bg=BG)
        win.transient(self)
        win.grab_set()

        tk.Label(win, text=titulo, bg=BG, fg=TEXT,
                 font=(FONT, 13, "bold")).pack(anchor="w", padx=22, pady=(18, 8))
        tk.Label(win, text=mensaje, bg=BG, fg="#586575",
                 font=(FONT, 9), justify="left", wraplength=385).pack(
                     anchor="w", padx=22, fill="x")
        tk.Label(win, text="Esta acción no se puede deshacer.",
                 bg=BG, fg=MUTED, font=(FONT, 8)).pack(
                     anchor="w", padx=22, pady=(8, 0))

        respuesta = {"confirmada": False}

        def confirmar():
            respuesta["confirmada"] = True
            win.destroy()

        acciones = tk.Frame(win, bg=BG)
        acciones.pack(side="bottom", fill="x", padx=16, pady=14)
        tk.Button(acciones, text="Eliminar", command=confirmar,
                  bg=RED, fg="white", activebackground=RED_BG,
                  relief="flat", bd=0, padx=13, pady=6,
                  font=(FONT, 8, "bold")).pack(side="right", padx=(6, 0))
        tk.Button(acciones, text="Cancelar", command=win.destroy,
                  bg=WHITE, fg="#657183", relief="solid", bd=1,
                  padx=12, pady=5, font=(FONT, 8)).pack(side="right")
        win.protocol("WM_DELETE_WINDOW", win.destroy)
        win.wait_window()
        return respuesta["confirmada"]

    def stat_card(self, parent, title, value, note):
        f = self.card(parent)
        f.pack(side="left", fill="both", expand=True, padx=5)
        tk.Label(f, text=title, bg=WHITE, fg=MUTED,
                 font=(FONT, 8)).pack(anchor="w", padx=14, pady=(13,0))
        tk.Label(f, text=str(value), bg=WHITE, fg=TEXT,
                 font=(FONT, 21, "bold")).pack(anchor="w", padx=14, pady=(5,0))
        tk.Label(f, text=note, bg=WHITE, fg="#9AA3AE",
                 font=(FONT, 7)).pack(anchor="w", padx=14, pady=(0,13))
        return f

    def panel_header(self, parent, title, subtitle="", button=None, command=None):
        h = tk.Frame(parent, bg=WHITE)
        h.pack(fill="x", padx=15, pady=13)
        l = tk.Frame(h, bg=WHITE)
        l.pack(side="left")
        tk.Label(l, text=title, bg=WHITE, fg=TEXT,
                 font=(FONT, 11, "bold")).pack(anchor="w")
        if subtitle:
            tk.Label(l, text=subtitle, bg=WHITE, fg=MUTED,
                     font=(FONT, 7)).pack(anchor="w", pady=(2,0))
        if button:
            tk.Button(h, text=button, command=command, bg=WHITE,
                      fg="#657183", relief="solid", bd=1,
                      highlightthickness=0, padx=10, pady=5,
                      font=(FONT, 7)).pack(side="right")

    def show_dashboard(self):
        self.clear(); self.set_active("dashboard", "Panel de Control")
        ps, ms, cs = pacientes.cargar_pacientes(), medicos.cargar_medicos(), citas.cargar_citas()
        pending = sum(c.get("estado") == "Pendiente" for c in cs)
        self.title_row("Panel de Control", "Resumen general del sistema de citas médicas",
                       "＋ Nueva cita", self.show_nueva_cita)

        stats = tk.Frame(self.content, bg=BG)
        stats.pack(fill="x", pady=(0,18))
        self.stat_card(stats, "Pacientes registrados", len(ps), "Registros actuales")
        self.stat_card(stats, "Médicos", len(ms), "Activos en el sistema")
        self.stat_card(stats, "Citas totales", len(cs), "Historial registrado")
        self.stat_card(stats, "Citas pendientes", pending, "Requieren atención")

        panel = self.card(self.content)
        panel.pack(fill="both", expand=True)
        self.panel_header(panel, "Próximas citas",
                          "Seguimiento de las citas registradas",
                          "Ver todas", self.show_citas)
        self.citas_tree(panel, cs[-5:] if cs else [])

    def citas_tree(self, parent, datos, allow_double=True, allow_delete=False):
        cols = ("Paciente", "Médico", "Fecha", "Hora", "Estado")
        if allow_delete:
            cols += ("Acción",)
        tree = ttk.Treeview(parent, columns=cols, show="headings", selectmode="browse")
        widths = {
            "Paciente": 230, "Médico": 190, "Fecha": 100, "Hora": 80,
            "Estado": 100, "Acción": 54,
        }
        for c in cols:
            tree.heading(c, text="×" if c == "Acción" else c.upper())
            tree.column(c, width=widths[c],
                        anchor="center" if c == "Acción" else "w",
                        stretch=c != "Acción")
        for i, c in enumerate(datos):
            valores = (
                c["paciente"], c["medico"], c["fecha"], c["hora"],
                c.get("estado", "Pendiente"),
            )
            if allow_delete:
                valores += ("×",)
            tree.insert("", "end", iid=str(i), values=valores)
        tree.pack(fill="both", expand=True, padx=10, pady=(0,10))
        if allow_double:
            tree.bind("<Double-1>", lambda e: self.open_cita_from_tree(tree, datos, e))
        if allow_delete:
            tree.bind(
                "<Button-1>",
                lambda event: self.eliminar_cita_desde_fila(tree, datos, event),
            )
        return tree

    def eliminar_cita_desde_fila(self, tree, datos, event):
        if tree.identify_column(event.x) != "#6":
            return
        item = tree.identify_row(event.y)
        if item and item.isdigit() and int(item) < len(datos):
            self.eliminar_cita(datos[int(item)])
        return "break"

    def open_cita_from_tree(self, tree, datos, event=None):
        if event and tree.identify_column(event.x) == "#6":
            return
        sel = tree.selection()
        if not sel: return
        local = int(sel[0])
        if local < len(datos):
            cita_obj = datos[local]
            # Buscar por objeto dentro del archivo para conservar el índice real.
            todos = citas.cargar_citas()
            for idx, c in enumerate(todos):
                if c == cita_obj:
                    self.show_detalle_cita(idx)
                    return

    def show_pacientes(self):
        self.clear(); self.set_active("pacientes", "Pacientes")
        ps = pacientes.cargar_pacientes()
        self.title_row("Pacientes", "Registro y gestión de pacientes",
                       "＋ Registrar paciente", self.show_nuevo_paciente)
        panel = self.card(self.content); panel.pack(fill="both", expand=True)
        self.panel_header(panel, "Pacientes registrados", f"{len(ps)} registros")
        cols=("Paciente","Documento","Edad","Sexo","Teléfono","Sangre","Acción")
        tree=ttk.Treeview(panel,columns=cols,show="headings")
        for c,w in zip(cols,(250,190,70,90,120,100,54)):
            tree.heading(c,text="×" if c=="Acción" else c.upper())
            tree.column(c,width=w,anchor="center" if c=="Acción" else "w",
                        stretch=c!="Acción")
        for i,p in enumerate(ps):
            tree.insert("", "end", values=(
                f'{p["nombre"]} {p["apellido"]}',p["documento"],p["edad"],
                p["sexo"],p["telefono"],p["tipo_sangre"],"×"), iid=str(i))
        tree.pack(fill="both",expand=True,padx=10,pady=(0,10))
        tree.bind(
            "<Button-1>",
            lambda event: self.eliminar_paciente_desde_fila(tree, ps, event),
        )

    def eliminar_paciente_desde_fila(self, tree, pacientes_lista, event):
        if tree.identify_column(event.x) != "#7":
            return
        item = tree.identify_row(event.y)
        if item and item.isdigit() and int(item) < len(pacientes_lista):
            self.eliminar_paciente(pacientes_lista[int(item)])
        return "break"

    def eliminar_paciente(self, paciente):
        nombre = f'{paciente["nombre"]} {paciente["apellido"]}'
        try:
            asociadas = citas.contar_citas_paciente(
                paciente["documento"], nombre
            )
            if asociadas:
                messagebox.showwarning(
                    "No se puede eliminar",
                    f"El paciente {nombre} tiene {asociadas} cita(s) "
                    "registrada(s). Elimine primero las citas.",
                    parent=self,
                )
                return
            if not self.confirmar_eliminacion(
                "Eliminar paciente",
                f"¿Está seguro de que desea eliminar a:\n{nombre}?",
            ):
                return
            if not pacientes.eliminar_paciente(paciente["documento"]):
                messagebox.showwarning(
                    "Paciente no encontrado",
                    "El paciente ya no existe en el archivo.",
                    parent=self,
                )
                return
            self.show_pacientes()
        except (OSError, ValueError, TypeError, KeyError) as error:
            messagebox.showerror(
                "No se pudo eliminar el paciente", str(error), parent=self
            )

    def show_medicos(self):
        self.clear(); self.set_active("medicos", "Médicos")
        ms = medicos.cargar_medicos()
        self.title_row("Médicos", "Profesionales registrados en el sistema",
                       "＋ Registrar médico", self.show_nuevo_medico)
        container=tk.Frame(self.content,bg=BG); container.pack(fill="both",expand=True)
        for i,m in enumerate(ms):
            card=self.card(container); card.grid(row=i//2,column=i%2,sticky="nsew",padx=6,pady=6)
            container.grid_columnconfigure(i%2,weight=1)
            tk.Label(card,text="✚",bg=BLUE_LIGHT,fg=BLUE,font=(FONT,15,"bold"),
                     width=3,height=2).pack(side="left",padx=14,pady=16)
            info=tk.Frame(card,bg=WHITE); info.pack(side="left",fill="both",expand=True,pady=15)
            tk.Label(info,text=f'{m["nombre"]} {m["apellido"]}',bg=WHITE,fg=TEXT,
                     font=(FONT,11,"bold")).pack(anchor="w")
            tk.Label(info,text=m["especialidad"],bg=WHITE,fg=BLUE,
                     font=(FONT,8)).pack(anchor="w",pady=3)
            tk.Label(info,text=f'Consultorio {m["consultorio"]} · {m["horario"]}',
                     bg=WHITE,fg=MUTED,font=(FONT,8)).pack(anchor="w")
            tk.Button(
                card, text="×", command=lambda medico=m: self.eliminar_medico(medico),
                bg=WHITE, fg=RED, activebackground=RED_BG, relief="flat",
                bd=0, cursor="hand2", padx=8, pady=4, font=(FONT, 12, "bold"),
            ).pack(side="right", padx=10)

    def eliminar_medico(self, medico):
        nombre = f'{medico["nombre"]} {medico["apellido"]}'
        try:
            asociadas = citas.contar_citas_medico(nombre)
            if asociadas:
                messagebox.showwarning(
                    "No se puede eliminar",
                    f"El médico {nombre} tiene {asociadas} cita(s) "
                    "registrada(s). Elimine primero las citas.",
                    parent=self,
                )
                return
            if not self.confirmar_eliminacion(
                "Eliminar médico",
                f"¿Está seguro de que desea eliminar al médico:\n{nombre}?",
            ):
                return
            if not medicos.eliminar_medico(medico["documento"]):
                messagebox.showwarning(
                    "Médico no encontrado",
                    "El médico ya no existe en el archivo.",
                    parent=self,
                )
                return
            self.show_medicos()
        except (OSError, ValueError, TypeError, KeyError) as error:
            messagebox.showerror(
                "No se pudo eliminar el médico", str(error), parent=self
            )

    def show_citas(self):
        self.clear(); self.set_active("citas", "Todas las Citas")
        cs=citas.cargar_citas()
        self.title_row("Todas las Citas", "Consulta y seguimiento de citas médicas",
                       "＋ Agendar cita", self.show_nueva_cita)
        tabs=tk.Frame(self.content,bg=BG); tabs.pack(fill="x",pady=(0,12))
        self.current_filter=tk.StringVar(value="Todas")
        for f in ("Todas","Pendiente","Realizada","Cancelada"):
            tk.Button(tabs,text=f,command=lambda x=f:self.filter_citas(x),
                      relief="flat",bd=0,padx=12,pady=6,
                      bg=BLUE if f=="Todas" else WHITE,
                      fg="white" if f=="Todas" else "#778392",
                      font=(FONT,8)).pack(side="left",padx=(0,4))
        self.citas_panel=self.card(self.content); self.citas_panel.pack(fill="both",expand=True)
        self.filter_citas("Todas")

    def filter_citas(self, filtro):
        for child in self.citas_panel.winfo_children(): child.destroy()
        cs=citas.cargar_citas()
        if filtro!="Todas": cs=[c for c in cs if c.get("estado") == filtro]
        self.panel_header(self.citas_panel,"Citas registradas",filtro)
        self.citas_tree(self.citas_panel,cs,allow_delete=True)

    def eliminar_cita(self, cita):
        nombre = (
            f'Paciente: {cita["paciente"]}\n'
            f'Médico: {cita["medico"]}\n'
            f'Fecha y hora: {cita["fecha"]} {cita["hora"]}'
        )
        if not self.confirmar_eliminacion(
            "Eliminar cita",
            f"¿Está seguro de que desea eliminar esta cita?\n\n{nombre}",
        ):
            return
        try:
            if not citas.eliminar_cita(cita):
                messagebox.showwarning(
                    "Cita no encontrada",
                    "La cita ya no existe en el archivo.",
                    parent=self,
                )
                return
            self.filter_citas(self.current_filter.get())
        except (OSError, ValueError, TypeError, KeyError) as error:
            messagebox.showerror(
                "No se pudo eliminar la cita", str(error), parent=self
            )

    def labeled_entry(self,parent,label,row,col,values=None):
        tk.Label(parent,text=label,bg=WHITE,fg="#697586",font=(FONT,8,"bold")).grid(
            row=row,column=col,sticky="w",padx=10,pady=(9,2))
        if values:
            w=ttk.Combobox(parent,values=values,state="readonly",font=(FONT,9))
        else:
            w=tk.Entry(parent,bd=1,relief="solid",font=(FONT,9))
        w.grid(row=row+1,column=col,sticky="ew",padx=10,pady=(0,7),ipady=5)
        return w

    def form_window(self,title, fields, save_callback):
        win=tk.Toplevel(self)
        win.title(title); win.geometry("760x620"); win.configure(bg=BG)
        win.transient(self); win.grab_set()
        outer=tk.Frame(win,bg=BG); outer.pack(fill="both",expand=True,padx=28,pady=25)
        tk.Label(outer,text=title,bg=BG,fg=TEXT,font=(FONT,17,"bold")).pack(anchor="w")
        tk.Label(outer,text="Completa la información solicitada",bg=BG,fg=MUTED,
                 font=(FONT,9)).pack(anchor="w",pady=(3,15))
        panel=self.card(outer); panel.pack(fill="both",expand=True)
        form=tk.Frame(panel,bg=WHITE); form.pack(fill="both",expand=True,padx=12,pady=12)
        widgets={}
        for i,(key,label,kind,vals) in enumerate(fields):
            r=(i//2)*2; c=i%2
            form.grid_columnconfigure(c,weight=1)
            widgets[key]=self.labeled_entry(form,label,r,c,vals if kind=="combo" else None)
        actions=tk.Frame(panel,bg=WHITE); actions.pack(fill="x",padx=15,pady=15)
        tk.Button(actions,text="Cancelar",command=win.destroy,bg=WHITE,fg="#657183",
                  relief="solid",bd=1,padx=14,pady=7,font=(FONT,8)).pack(side="right",padx=5)
        tk.Button(actions,text="Guardar",command=lambda:save_callback(widgets,win),
                  bg=BLUE,fg="white",relief="flat",bd=0,padx=15,pady=8,
                  font=(FONT,8,"bold")).pack(side="right")
        return win

    def show_nuevo_paciente(self):
        fields=[
            ("documento","Documento","text",None),("nombre","Nombre","text",None),
            ("apellido","Apellido","text",None),("edad","Edad","text",None),
            ("sexo","Sexo","combo",["masculino","femenino"]),
            ("fecha_nacimiento","Fecha de nacimiento","text",None),
            ("telefono","Teléfono","text",None),("direccion","Dirección","text",None),
            ("correo","Correo electrónico","text",None),("tipo_sangre","Tipo de sangre","text",None),
            ("seguro_medico","Seguro médico","text",None)]
        self.form_window("Registrar Nuevo Paciente",fields,self.save_paciente)

    def save_paciente(self,w,win):
        try:
            data={k:v.get().strip() for k,v in w.items()}
            data["edad"]=int(data["edad"])
            if not all(str(v).strip() for v in data.values()): raise ValueError
            pacientes.registrar_paciente(data); win.destroy(); self.show_pacientes()
        except ValueError:
            messagebox.showerror("Datos inválidos","Completa todos los campos y verifica la edad.")

    def show_nuevo_medico(self):
        fields=[
            ("documento","Documento","text",None),("nombre","Nombre","text",None),
            ("apellido","Apellido","text",None),("telefono","Teléfono","text",None),
            ("correo","Correo electrónico","text",None),("modulo","Módulo","text",None),
            ("especialidad","Especialidad","text",None),("consultorio","Consultorio","text",None),
            ("horario","Horario","text",None)]
        self.form_window("Registrar Nuevo Médico",fields,self.save_medico)

    def save_medico(self,w,win):
        data={k:v.get().strip() for k,v in w.items()}
        if not all(data.values()):
            messagebox.showerror("Datos inválidos","Completa todos los campos."); return
        medicos.registrar_medico(data); win.destroy(); self.show_medicos()

    def show_nueva_cita(self):
        ps=pacientes.cargar_pacientes(); ms=medicos.cargar_medicos()
        if not ps or not ms:
            messagebox.showwarning("No disponible","Debe existir al menos un paciente y un médico."); return
        fields=[
            ("paciente","Paciente","combo",[f'{p["nombre"]} {p["apellido"]}' for p in ps]),
            ("medico","Médico","combo",[f'{m["nombre"]} {m["apellido"]}' for m in ms]),
            ("fecha","Fecha (dd/mm/aaaa)","text",None),("hora","Hora (hh:mm)","text",None),
            ("tipo","Tipo de cita","combo",["presencial","virtual"]),
            ("motivo","Motivo de consulta","text",None),
            ("observaciones","Observaciones","text",None)]
        self.form_window("Agendar Nueva Cita",fields,self.save_cita)

    def save_cita(self,w,win):
        values={k:v.get().strip() for k,v in w.items()}
        if not all(values.values()):
            messagebox.showerror("Datos inválidos","Completa todos los campos."); return
        try:
            datetime.strptime(values["fecha"],"%d/%m/%Y")
            datetime.strptime(values["hora"],"%H:%M")
        except ValueError:
            messagebox.showerror("Fecha u hora inválida","Usa dd/mm/aaaa y hh:mm."); return
        ps=pacientes.cargar_pacientes(); ms=medicos.cargar_medicos()
        p=next(p for p in ps if f'{p["nombre"]} {p["apellido"]}'==values["paciente"])
        m=next(m for m in ms if f'{m["nombre"]} {m["apellido"]}'==values["medico"])
        cita_data={
            "paciente":f'{p["nombre"]} {p["apellido"]}',
            "documento_paciente":p["documento"],
            "medico":f'{m["nombre"]} {m["apellido"]}',
            "especialidad":m["especialidad"],"modulo":m["modulo"],
            "fecha":values["fecha"],"hora":values["hora"],"tipo":values["tipo"],
            "motivo":values["motivo"],"observaciones":values["observaciones"],
            "estado":"Pendiente"}
        citas.agregar_cita(cita_data); win.destroy(); self.show_citas()

    def show_detalle_cita(self,index):
        all_citas=citas.cargar_citas()
        if index<0 or index>=len(all_citas): return
        c=all_citas[index]
        win=tk.Toplevel(self); win.title("Detalle de la Cita"); win.geometry("650x540"); win.configure(bg=BG)
        outer=tk.Frame(win,bg=BG); outer.pack(fill="both",expand=True,padx=28,pady=25)
        tk.Label(outer,text="Detalle de la Cita",bg=BG,fg=TEXT,font=(FONT,17,"bold")).pack(anchor="w")
        panel=self.card(outer); panel.pack(fill="both",expand=True,pady=(12,0))
        head=tk.Frame(panel,bg=WHITE); head.pack(fill="x",padx=18,pady=18)
        tk.Label(head,text=c["paciente"][0],bg=BLUE_LIGHT,fg=BLUE,font=(FONT,14,"bold"),
                 width=3,height=2).pack(side="left")
        info=tk.Frame(head,bg=WHITE); info.pack(side="left",padx=10)
        tk.Label(info,text=c["paciente"],bg=WHITE,fg=TEXT,font=(FONT,12,"bold")).pack(anchor="w")
        tk.Label(info,text=c["documento_paciente"],bg=WHITE,fg=MUTED,font=(FONT,8)).pack(anchor="w")
        self.badge(head,c.get("estado","Pendiente")).pack(side="right")
        grid=tk.Frame(panel,bg=WHITE); grid.pack(fill="x",padx=18)
        info_items=[("MÉDICO",c["medico"]),("ESPECIALIDAD",c["especialidad"]),
                    ("FECHA",c["fecha"]),("HORA",c["hora"]),("MÓDULO",c["modulo"]),("TIPO",c["tipo"])]
        for i,(lab,val) in enumerate(info_items):
            cell=tk.Frame(grid,bg=WHITE); cell.grid(row=i//3,column=i%3,sticky="w",padx=8,pady=10)
            tk.Label(cell,text=lab,bg=WHITE,fg="#99A2AE",font=(FONT,7,"bold")).pack(anchor="w")
            tk.Label(cell,text=val,bg=WHITE,fg=TEXT,font=(FONT,9,"bold")).pack(anchor="w",pady=(3,0))
        for lab,key in [("MOTIVO DE CONSULTA","motivo"),("OBSERVACIONES","observaciones")]:
            box=tk.Frame(panel,bg="#FAFBFD",highlightbackground=BORDER,highlightthickness=1)
            box.pack(fill="x",padx=18,pady=5)
            tk.Label(box,text=lab,bg="#FAFBFD",fg="#99A2AE",font=(FONT,7,"bold")).pack(anchor="w",padx=10,pady=(8,2))
            tk.Label(box,text=c[key],bg="#FAFBFD",fg="#586575",font=(FONT,9),
                     wraplength=540,justify="left").pack(anchor="w",padx=10,pady=(0,8))
        if c.get("estado")=="Pendiente":
            tk.Button(panel,text="✓  Marcar como realizada",
                      command=lambda:self.complete_cita(index,win),
                      bg=BLUE,fg="white",relief="flat",bd=0,padx=14,pady=8,
                      font=(FONT,8,"bold")).pack(anchor="e",padx=18,pady=15)

    def badge(self,parent,state):
        bg,fg=(GREEN_BG,GREEN) if state=="Realizada" else (YELLOW_BG,YELLOW) if state=="Pendiente" else (RED_BG,RED)
        return tk.Label(parent,text=state,bg=bg,fg=fg,font=(FONT,8,"bold"),padx=8,pady=4)

    def complete_cita(self,index,win):
        citas.marcar_como_realizada(index); win.destroy(); self.show_citas()
        messagebox.showinfo("Cita actualizada","La cita fue marcada como realizada.")

if __name__ == "__main__":
    App().mainloop()
