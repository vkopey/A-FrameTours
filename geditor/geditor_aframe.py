import tkinter as tk
from tkinter import filedialog, ttk, messagebox
import json
import server, math
server.launch_server()

def auto_name(first_letter, names):
    "Автоматично нумерує вузли і ребра"
    if not names: return f"{first_letter}1"
    names0=[int(n[1:]) for n in names]
    mn,mx=min(names0), max(names0)
    all_names=set(range(mn,mx))
    free_names=set(all_names)-set(names0)
    if free_names:
        name=sorted(free_names)[0]
    else:
        name=mx+1
    return f"{first_letter}{name}"

class GraphEditor(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Graph editor")
        self.state("zoomed") # розгортає вікно на весь екран
        #self.attributes("-fullscreen", True) # повноекранний режим
        #self.geometry(f"{self.winfo_screenwidth()-10}x{self.winfo_screenheight()-60}+0+0")

        frame = tk.Frame(self)
        frame.pack(fill=tk.BOTH, expand=True)

        vbar=tk.Scrollbar(frame, orient=tk.VERTICAL)
        vbar.pack(side=tk.RIGHT, fill=tk.Y)
        hbar=tk.Scrollbar(self, orient=tk.HORIZONTAL)
        hbar.pack(side=tk.BOTTOM, fill=tk.X)

        self.canvas = tk.Canvas(frame, bg="white", yscrollcommand=vbar.set, xscrollcommand=hbar.set)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        canvas_width, canvas_height=2000, 2000
        self.canvas.config(scrollregion=(0, 0, canvas_width, canvas_height))

        vbar.config(command=self.canvas.yview)
        hbar.config(command=self.canvas.xview)

        self.create_grid(canvas_width, canvas_height)

        # ================= Data =================
        self.nodes = {}   # nid: {node data}
        self.edges = {}   # eid: {edge data}
        self.node_colors={"":"yellow", "sky":"yellow", "image":"lightblue", "sound":"lightgreen", "object":"gray"}

        self.drag = {"item": None, "x": 0, "y": 0}
        self.edge_start = None

        # ================= Context menu =================
        self.menu = tk.Menu(self, tearoff=0)
        self.menu.add_command(label="Create node", command=self.create_node_at_click)
        self.menu.add_separator()
        self.menu.add_command(label="Export JSON", command=self.export_json)
        self.menu.add_command(label="Help", command=self.help_window)

        self.menu_node = None
        self.menu_edge = None
        self.menu_x = self.menu_y = 0

        # ================= Bindings =================
        self.canvas.bind("<Button-1>", self.on_left_press)
        self.canvas.bind("<B1-Motion>", self.on_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_left_release)
        self.canvas.bind("<Shift-Button-1>", self.start_edge)
        self.canvas.bind("<Shift-ButtonRelease-1>", self.finish_edge)
        self.canvas.bind("<Double-Button-1>", self.open_editor)
        self.canvas.bind("<Button-3>", self.show_menu)
        self.canvas.bind("<Motion>", self.auto_scroll)

        self.import_json() # відкрити файл

        self.canvas.xview_moveto(0.25)
        self.canvas.yview_moveto(0.5)

    # ==================================================
    # Nodes
    def create_node(self, x, y, node_id=None, data=None):
        r = 25
        if node_id is None:
            node_id=auto_name('N', self.nodes.keys())

        self.canvas.create_oval(x-r, y-r, x+r, y+r, fill="yellow", outline="black", width=2, tags=(node_id, node_id+"_oval")) # один тег спільний, один унікальний
        self.canvas.create_text(x,y,text=node_id,fill="brown",anchor="s",tags=(node_id, node_id+"_label"))

        self.nodes[node_id] = data or {
            "x": x,
            "y": y,
            "label": node_id,
            "type": "",
            "description": ""
        }
        self.update_nodes(node_id)

    def delete_node(self):
        if not self.menu_node: return
        nid = self.menu_node

        for e in self.edges.copy(): # спочатку ребра вузла
            if nid in self.edges[e]["nodes"]:
                self.canvas.delete(e)
                del self.edges[e]

        self.canvas.delete(nid) # потім вузол
        del self.nodes[nid]
        self.menu_node=None

    def delete_edge(self):
        if not self.menu_edge: return

        for e in self.edges.copy():
            if e == self.menu_edge:
                self.canvas.delete(e)
                del self.edges[e]
                self.menu_edge=None
                break

    # ==================================================
    # Dragging

    def on_left_press(self, event):
        nid = self.get_node_at(event)
        if nid:
            self.drag["item"] = nid
            self.drag["x"] = self.canvas.canvasx(event.x)
            self.drag["y"] = self.canvas.canvasy(event.y)

    def on_drag(self, event):
        nid = self.drag["item"]
        if not nid: return

        x = self.canvas.canvasx(event.x)
        y = self.canvas.canvasy(event.y)
        dx, dy = x - self.drag["x"], y - self.drag["y"]

        self.canvas.move(nid, dx, dy)

        self.drag["x"], self.drag["y"] = x, y

        self.nodes[nid]["x"] += dx
        self.nodes[nid]["y"] += dy

        self.update_edges()

    def on_left_release(self, event):
        self.drag["item"] = None

    # ==================================================
    # Edges

    def start_edge(self, event):
        self.edge_start = self.get_node_at(event)

    def finish_edge(self, event):
        if self.edge_start:
            end = self.get_node_at(event)
            if end and end != self.edge_start:
                self.create_edge(self.edge_start, end)
        self.edge_start = None

    def create_edge(self, f, t, eid=None, data=None):
        if eid is None:
            eid=auto_name('E', self.edges.keys())

        self.canvas.create_line(*self.node_center(f), *self.node_center(t), arrow=tk.LAST, width=2, fill="red", tags=eid)

        self.edges[eid]=data or {
            "nodes":(f, t),
            "label": eid,
            "type": "",
            "description": ""
            }

    def update_nodes(self, nid):
        data = self.nodes[nid]
        k=data["type"]
        color=self.node_colors.get(k, "yellow")
        self.canvas.itemconfig(nid+"_oval", fill=color)
        self.canvas.itemconfig(nid+"_label", text=data["label"]) # показувати label


    def update_edges(self):
        for e in self.edges:
            f,t=self.edges[e]["nodes"]
            self.canvas.coords(e, *self.node_center(f), *self.node_center(t))

    # ==================================================
    # Редактор вузлів/ребер
    def open_editor(self, event):
        nid = self.get_node_at(event)
        if nid:
            self.open_node_editor(nid)
            return
        eid = self.get_edge_at(event)
        if eid:
            self.open_edge_editor(eid)

    def open_node_editor(self, nid):
        #print(self.nodes)

        data = self.nodes[nid]
        win = tk.Toplevel(self)
        win.title(f"Node {nid}")
        win.geometry("350x400")
        win.grab_set() # робить вікно модальним
        win.focus_set() # передає фокус
        fields = {}

        for i, key in enumerate(["label", "type", "description"]):
            tk.Label(win, text=key).grid(row=i, column=0, sticky="w", padx=5, pady=5)
            if key in ["type"]:
                el=ttk.Combobox(win, values=list(self.node_colors.keys()))
                el.insert(0, data[key])
            elif key in ["description"]:
                el = tk.Text(win, height=6, width=30)
                el.insert("1.0", data["description"])
            else:
                el = tk.Entry(win)
                el.insert(0, data[key])
            el.grid(row=i, column=1, sticky="ew", padx=5)
            fields[key] = el

        def save():
            data["label"] = fields["label"].get()
            data["type"] = fields["type"].get()
            data["description"] = fields["description"].get("1.0", "end").strip()
            self.update_nodes(nid)
            win.destroy()

        def check_messages():
            if server.message[0]:
                fields["description"].delete("1.0", "end")
                fields["description"].insert("1.0", server.message[0])
                server.message[0]=""
            win.after(500, check_messages)
        check_messages() # очікування повідомлень від сервера

        tk.Button(win, text="Save", command=save).grid(row=i+1, column=1, columnspan=2, pady=10)

        self.menu_node=nid
        tk.Button(win, text="Delete", command=lambda:(self.delete_node(), win.destroy())).grid(row=i+1, column=0, columnspan=1, padx=10)
        tk.Button(win, text="OpenHTML", command=self.openHTML).grid(row=i+2, column=1, columnspan=1, padx=10)
        def fromGraph():
            #print(self.edges)
            i=0
            d={}
            for k,v in self.edges.items():
                node1_id=None
                node2_id=None
                if v['nodes'][0]==nid:
                    node1_id=nid
                    node2_id=v['nodes'][1]
                if v['nodes'][1]==nid:
                    node1_id=nid
                    node2_id=v['nodes'][0]
                if node1_id:
                    node1=self.nodes[node1_id]
                    xc=node1['x']
                    yc=node1['y']
                    node2=self.nodes[node2_id]
                    x=node2['x']-xc
                    y=node2['y']-yc
                    label=node2['label']
                    t=node2['type'] or "sky"
                    a=math.atan2(y,x)
                    #r=math.hypot(x,y)
                    r=4.5
                    x=round(r*math.cos(a), 1)
                    y=round(r*math.sin(a), 1)
                    i+=1
                    if t=='image':
                        ar=-round(math.degrees(a)%360)+360-90
                        d[i]={"src":label, "type":t, "pos":f"{x} -2.0 {y}", "rot":f"0 {ar} 0"}
                    else:
                        d[i]={"src":label, "type":t, "pos":f"{x} -2.0 {y}", "rot":"-90 0 0"}
            if i:
                s=json.dumps(d, indent=2)
                fields["description"].delete("1.0", "end")
                fields["description"].insert("1.0", s)

        tk.Button(win, text="FromGraph", command=fromGraph).grid(row=i+3, column=0, columnspan=1, padx=10)
        win.wait_window() # чекає, поки вікно закриється


    def open_edge_editor(self, eid):
        print(self.edges)
        data = self.edges[eid]
        win = tk.Toplevel(self)
        win.title(f"Edge {eid}")
        win.geometry("350x300")
        fields = {}

        for i, key in enumerate(["label", "type", "description"]):
            tk.Label(win, text=key).grid(row=i, column=0, sticky="w", padx=5, pady=5)
            if key in ["type"]:
                el=ttk.Combobox(win, values=["a","b","c"])
                el.insert(0, data[key])
            elif key in ["description"]:
                el = tk.Text(win, height=6, width=30)
                el.insert("1.0", data["description"])
            else:
                el = tk.Entry(win)
                el.insert(0, data[key])
            el.grid(row=i, column=1, sticky="ew", padx=5)
            fields[key] = el

        def save():
            data["label"] = fields["label"].get()
            data["type"] = fields["type"].get()
            data["description"] = fields["description"].get("1.0", "end").strip()
            win.destroy()

        tk.Button(win, text="Save", command=save).grid(row=i+1, column=1, columnspan=2, pady=10)

        self.menu_edge=eid
        tk.Button(win, text="Delete", command=self.delete_edge).grid(row=i+1, column=0, columnspan=1, padx=10)


    # ==================================================
    # Utils

    def node_center(self, nid):
        x1, y1, x2, y2 = self.canvas.coords(nid) # знайти коодинати за тегом
        return (x1+x2)/2, (y1+y2)/2

    def get_node_at(self, event):
        x, y = self.canvas.canvasx(event.x), self.canvas.canvasy(event.y)
        for i in self.canvas.find_overlapping(x-1, y-1, x+1, y+1):
            for t in self.canvas.gettags(i):
                if t.startswith("N"):
                    return t
        return None

    def get_edge_at(self, event):
        x, y = self.canvas.canvasx(event.x), self.canvas.canvasy(event.y)
        for i in self.canvas.find_overlapping(x-3, y-3, x+3, y+3):
            for t in self.canvas.gettags(i):
                if t.startswith("E"):
                    return t
        return None

    # ==================================================
    # Menu & JSON

    def show_menu(self, event):
        self.menu_x = self.canvas.canvasx(event.x)
        self.menu_y = self.canvas.canvasy(event.y)
        self.menu_node = self.get_node_at(event)
        self.menu_edge = self.get_edge_at(event)
        self.menu.tk_popup(event.x_root, event.y_root)

    def create_node_at_click(self):
        self.create_node(self.menu_x, self.menu_y)

    def export_json(self):
        data = {"nodes": self.nodes, "edges": self.edges}
        #print(data)
        f=filedialog.asksaveasfilename(defaultextension=".json")
        import convert
        if f:
            with open(f, "w", encoding="utf-8") as file:
                json.dump(data, file, indent=2)
            convert.graph2aframe(f, "data.json")

    def import_json(self):
        f = filedialog.askopenfilename(filetypes=[("JSON", "*.json")])
        if not f: return

        with open(f, "r", encoding="utf-8") as file:
            data = json.load(file)

        for nid, nd in data["nodes"].items():
            self.create_node(nd["x"], nd["y"], nid, nd)

        for eid, ed in data["edges"].items():
            self.create_edge(ed["nodes"][0], ed["nodes"][1], eid, ed)

    def create_grid(self, width, height):
        grid_size = 100
        for x in range(0, width, grid_size):
            if x==grid_size*10: fill="green"
            else: fill="lightgray"
            self.canvas.create_line(x, 0, x, height, fill=fill)
        for y in range(0, height, grid_size):
            if y==grid_size*10: fill="green"
            else: fill="lightgray"
            self.canvas.create_line(0, y, width, y, fill=fill)

    # Функція автопрокрутки
    def auto_scroll(self, event):
        x, y = event.x, event.y
        w = self.canvas.winfo_width()
        h = self.canvas.winfo_height()

        margin = 20  # зона біля краю

        # Горизонталь
        if x < margin:
            self.canvas.xview_scroll(-1, "units")
        elif x > w - margin:
            self.canvas.xview_scroll(1, "units")

        # Вертикаль
        if y < margin:
            self.canvas.yview_scroll(-1, "units")
        elif y > h - margin:
            self.canvas.yview_scroll(1, "units")

    def help_window(self):
        messagebox.showinfo("Help", """Права кнопка миші - створити вузол.
Ліва кнопка миші - перетягнути вузол.
Shift + перетягування миші між двома вузлами - створити ребро.
Подвійний натиск лівою - редагувати вузол або ребро з можливістю видалення.""")

    def openHTML(self):
        data = self.nodes[self.menu_node]
        with open("examples/museum/edit.html", 'r', encoding='utf-8') as f:
            t=f.read()
        with open("examples/museum/edit_tmp.html", 'w', encoding='utf-8') as f:
            t=t.replace("museum147.jpg", data['label'])
            if data['description'].strip(): t=t.replace("const data={};", "const data="+data['description']+";")
            f.write(t)
        server.webbrowser.open("http://localhost:8000/examples/museum/edit_tmp.html")

if __name__ == "__main__":
    GraphEditor().mainloop()