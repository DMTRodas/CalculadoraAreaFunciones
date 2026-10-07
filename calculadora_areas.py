import tkinter as tk
from tkinter import messagebox
import math
from bisect import bisect_left

#  Lógica del sistema

SAFE_MATH_CONTEXT = {k: getattr(math, k) for k in dir(math) if not k.startswith("_")}
SAFE_MATH_CONTEXT.update({"abs": abs, "min": min, "max": max})


def traducir_sintaxis(expresion):
    """
    Convierte la sintaxis ingresada por el usuario a sintaxis válida de Python para que eval() funcione.
    """
    exp = expresion.strip()

    # Funciones y sus reemplazos
    exp = exp.replace("sen(", "sin(")
    exp = exp.replace("tg(", "tan(")
    exp = exp.replace("ln(", "log(")

    # Potencias
    exp = exp.replace("^", "**")

    # e^ y 10^
    exp = exp.replace("e**", "exp(")
    exp = exp.replace("10**", "10**(")

    # paréntesis
    abiertos = exp.count("(")
    cerrados = exp.count(")")
    faltantes = abiertos - cerrados

    if faltantes > 0:
        exp += ")" * faltantes

    return exp


def evaluar_funcion(expresion, x_val):
    try:
        expresion_traducida = traducir_sintaxis(expresion)
        contexto = SAFE_MATH_CONTEXT.copy()
        contexto["x"] = x_val
        return float(eval(expresion_traducida, {"__builtins__": None}, contexto))
    except Exception as e:
        raise ValueError(f"Error de sintaxis en '{expresion}': {e}")


def evaluar_limite(expresion):
    try:
        return evaluar_funcion(expresion, 0)
    except Exception as e:
        raise ValueError(f"Error en el límite '{expresion}': {e}")


def calcular_area_riemann(f_str, g_str, a, b, n):
    dx = (b - a) / n
    area_total = 0.0
    puntos_f = []
    puntos_g = []

    for i in range(n):
        x_medio = a + (i + 0.5) * dx
        try:
            y1 = evaluar_funcion(f_str, x_medio)
            y2 = evaluar_funcion(g_str, x_medio)
        except ValueError as e:
            raise ValueError(f"Error en el paso {i}: {e}")

        altura = abs(y1 - y2)
        area_total += dx * altura

        if i == 0:
            puntos_f.append((a, evaluar_funcion(f_str, a)))
            puntos_g.append((a, evaluar_funcion(g_str, a)))
        puntos_f.append((x_medio + dx / 2, evaluar_funcion(f_str, x_medio + dx / 2)))
        puntos_g.append((x_medio + dx / 2, evaluar_funcion(g_str, x_medio + dx / 2)))

    return area_total, puntos_f, puntos_g


# ═════════════════════════════════════════════════════════════
#  PALETA  ·  "Aurora nocturna"
# ═════════════════════════════════════════════════════════════

BG = "#0a0e1a"          # fondo general
PANEL = "#0f1424"       # panel lateral
CARD = "#171e35"        # tarjetas / teclas
CARD_HI = "#222b4b"     # hover de teclas
BORDER = "#283257"
TEXT = "#e9edfb"
MUTED = "#7b87b0"

F_COL = "#22d3ee"      # f(x)  · cian eléctrico
F_GLOW1 = "#0d3441"
F_GLOW2 = "#12596b"
G_COL = "#ff5c93"      # g(x)  · rosa coral
G_GLOW1 = "#40142a"
G_GLOW2 = "#7a2149"
AREA = "#8b6cff"       # área  · violeta
GOLD = "#fbbf24"       # resultado
OK = "#34d399"
ERR = "#fb7185"
PLOT_BG = "#0c1122"
GRID = "#1a2240"
GRID_STRONG = "#2c376a"

FONT_UI = "Segoe UI"
FONT_MONO = "Consolas"


#  INTERFAZ

class CalculadoraAreaApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Área entre Funciones · Integración Numérica")
        self.root.geometry("1360x820")
        self.root.minsize(1100, 700)
        self.root.configure(bg=BG)

        self.campo_activo = None
        self.datos = None       # (puntos_f, puntos_g, a, b, f_str, g_str, area)
        self.xs = []
        self.geom = None

        self.crear_widgets()
        self.campo_activo = self.entry_f
        self.root.bind("<Return>", lambda e: self.ejecutar_calculo())
        self.root.after(250, self.ejecutar_calculo)

    # ───────────────────────── helpers de widgets ─────────────────────────
    def _hover(self, widget, normal, hover):
        widget.bind("<Enter>", lambda e: widget.config(bg=hover))
        widget.bind("<Leave>", lambda e: widget.config(bg=normal))

    def _tecla(self, parent, texto, comando, tipo="num", visual=None):
        estilos = {
            "num":  (CARD, CARD_HI, TEXT, (FONT_UI, 12, "bold")),
            "op":   ("#1d2547", "#2b3664", "#b9a8ff", (FONT_UI, 12, "bold")),
            "fn":   ("#13263a", "#1c3a56", F_COL, (FONT_UI, 11, "bold")),
            "var":  ("#2a1a3d", "#3d2658", "#d9b8ff", (FONT_UI, 12, "bold", "italic")),
            "del":  ("#3a1626", "#5a2038", "#ff8fb1", (FONT_UI, 11, "bold")),
        }
        bg, hv, fg, fuente = estilos[tipo]
        b = tk.Button(parent, text=visual or texto, command=comando, bg=bg, fg=fg,
                      activebackground=hv, activeforeground=fg, relief=tk.FLAT, bd=0,
                      font=fuente, cursor="hand2", takefocus=0, highlightthickness=0)
        self._hover(b, bg, hv)
        return b

    def _campo(self, parent, etiqueta, valor, fila, ancho=None, color=None, mono=True):
        tk.Label(parent, text=etiqueta, bg=PANEL, fg=color or MUTED,
                 font=(FONT_UI, 10, "bold")).grid(row=fila, column=0, sticky="w", pady=5, padx=(0, 10))
        marco = tk.Frame(parent, bg=BORDER, padx=1, pady=1)
        marco.grid(row=fila, column=1, sticky="ew", pady=5)
        e = tk.Entry(marco, bg=CARD, fg=TEXT, insertbackground=color or AREA, relief=tk.FLAT,
                     font=(FONT_MONO, 12), bd=0, highlightthickness=0, width=ancho or 24)
        e.pack(fill=tk.X, ipady=6, padx=1, pady=1)
        e.insert(0, valor)

        def on_in(_):
            marco.config(bg=color or AREA)
            self.campo_activo = e

        e.bind("<FocusIn>", on_in)
        e.bind("<FocusOut>", lambda _: marco.config(bg=BORDER))
        return e

    # ───────────────────────── construcción ─────────────────────────
    def crear_widgets(self):
        # ── Panel izquierdo ─────────────────────────────────
        panel = tk.Frame(self.root, bg=PANEL, width=410)
        panel.pack(side=tk.LEFT, fill=tk.Y)
        panel.pack_propagate(False)
        tk.Frame(self.root, bg=BORDER, width=1).pack(side=tk.LEFT, fill=tk.Y)

        inner = tk.Frame(panel, bg=PANEL, padx=22, pady=20)
        inner.pack(fill=tk.BOTH, expand=True)

        # Encabezado
        cab = tk.Frame(inner, bg=PANEL)
        cab.pack(fill=tk.X)
        logo = tk.Canvas(cab, width=42, height=42, bg=PANEL, highlightthickness=0)
        logo.pack(side=tk.LEFT)
        logo.create_oval(2, 2, 40, 40, fill="#1b2147", outline=AREA, width=2)
        logo.create_text(21, 21, text="∫", fill=F_COL, font=(FONT_UI, 20, "bold"))
        tit = tk.Frame(cab, bg=PANEL)
        tit.pack(side=tk.LEFT, padx=12)
        tk.Label(tit, text="Grupo 2 - Área entre funciones", bg=PANEL, fg=TEXT,
                 font=(FONT_UI, 16, "bold")).pack(anchor="w")
        tk.Label(tit, text="Calculo de Área entre dos funciones", bg=PANEL, fg=MUTED,
                 font=(FONT_UI, 9)).pack(anchor="w")

        # Entradas
        tk.Label(inner, text="FUNCIONES", bg=PANEL, fg=MUTED,
                 font=(FONT_UI, 8, "bold")).pack(anchor="w", pady=(22, 0))
        fr = tk.Frame(inner, bg=PANEL)
        fr.pack(fill=tk.X)
        fr.columnconfigure(1, weight=1)
        self.entry_f = self._campo(fr, "f(x)", "x^2", 0, color=F_COL)
        self.entry_g = self._campo(fr, "g(x)", "x", 1, color=G_COL)

        tk.Label(inner, text="INTERVALO Y PRECISIÓN", bg=PANEL, fg=MUTED,
                 font=(FONT_UI, 8, "bold")).pack(anchor="w", pady=(10, 0))
        fr2 = tk.Frame(inner, bg=PANEL)
        fr2.pack(fill=tk.X)
        for c in range(6):
            fr2.columnconfigure(c, weight=1 if c % 2 else 0)
        # a, b, n en una sola fila compacta
        self.entry_a = self._mini(fr2, "a", "0", 0)
        self.entry_b = self._mini(fr2, "b", "1", 2)
        self.entry_n = self._mini(fr2, "n", "10000", 4)

        # Botón calcular
        self.btn_calc = tk.Button(inner, text="CALCULAR ÁREA   →", command=self.ejecutar_calculo,
                                  bg=AREA, fg="white", activebackground="#a58cff",
                                  activeforeground="white", relief=tk.FLAT, bd=0,
                                  font=(FONT_UI, 12, "bold"), cursor="hand2", takefocus=0)
        self.btn_calc.pack(fill=tk.X, ipady=10, pady=(16, 12))
        self._hover(self.btn_calc, AREA, "#a58cff")

        # Resultado
        res_borde = tk.Frame(inner, bg=BORDER, padx=1, pady=1)
        res_borde.pack(fill=tk.X)
        res = tk.Frame(res_borde, bg=CARD, padx=16, pady=10)
        res.pack(fill=tk.X)
        tk.Label(res, text="ÁREA TOTAL", bg=CARD, fg=MUTED, font=(FONT_UI, 8, "bold")).pack(anchor="w")
        self.lbl_resultado = tk.Label(res, text="—", bg=CARD, fg=GOLD, font=(FONT_MONO, 24, "bold"))
        self.lbl_resultado.pack(anchor="w")
        self.lbl_info = tk.Label(res, text="Esperando cálculo…", bg=CARD, fg=MUTED, font=(FONT_UI, 9))
        self.lbl_info.pack(anchor="w")

        # Teclado
        tk.Label(inner, text="TECLADO", bg=PANEL, fg=MUTED,
                 font=(FONT_UI, 8, "bold")).pack(anchor="w", pady=(16, 6))

        barra = tk.Frame(inner, bg=CARD)
        barra.pack(fill=tk.X)
        self.tab_btns = {}
        for nombre, txt in (("num", "  123  "), ("fn", "  f(x)  ")):
            b = tk.Button(barra, text=txt, relief=tk.FLAT, bd=0, font=(FONT_UI, 10, "bold"),
                          cursor="hand2", takefocus=0, command=lambda n=nombre: self.cambiar_tab(n))
            b.pack(side=tk.LEFT, expand=True, fill=tk.X, ipady=5)
            self.tab_btns[nombre] = b

        self.zona_teclado = tk.Frame(inner, bg=PANEL)
        self.zona_teclado.pack(fill=tk.BOTH, expand=True, pady=(8, 0))
        self.tab_numeros = tk.Frame(self.zona_teclado, bg=PANEL)
        self.tab_funciones = tk.Frame(self.zona_teclado, bg=PANEL)
        self.crear_teclado_numeros(self.tab_numeros)
        self.crear_teclado_funciones(self.tab_funciones)
        self.cambiar_tab("num")

        # ── Panel derecho: gráfica ──────────────────────────
        der = tk.Frame(self.root, bg=BG, padx=16, pady=16)
        der.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        self.canvas = tk.Canvas(der, bg=PLOT_BG, highlightthickness=1, highlightbackground=BORDER)
        self.canvas.pack(fill=tk.BOTH, expand=True)
        self.canvas.bind("<Configure>", lambda e: self.dibujar_grafica())
        self.canvas.bind("<Motion>", self.on_motion)
        self.canvas.bind("<Leave>", lambda e: self.canvas.delete("hover"))

    def _mini(self, parent, etiqueta, valor, col):
        tk.Label(parent, text=etiqueta, bg=PANEL, fg=MUTED,
                 font=(FONT_UI, 10, "bold")).grid(row=0, column=col, sticky="w", pady=5, padx=(0, 6))
        marco = tk.Frame(parent, bg=BORDER, padx=1, pady=1)
        marco.grid(row=0, column=col + 1, sticky="ew", pady=5, padx=(0, 10))
        e = tk.Entry(marco, bg=CARD, fg=TEXT, insertbackground=AREA, relief=tk.FLAT,
                     font=(FONT_MONO, 12), bd=0, highlightthickness=0, width=6)
        e.pack(fill=tk.X, ipady=6, padx=1, pady=1)
        e.insert(0, valor)

        def on_in(_):
            marco.config(bg=AREA)
            self.campo_activo = e

        e.bind("<FocusIn>", on_in)
        e.bind("<FocusOut>", lambda _: marco.config(bg=BORDER))
        return e

    def cambiar_tab(self, nombre):
        self.tab_numeros.pack_forget()
        self.tab_funciones.pack_forget()
        (self.tab_numeros if nombre == "num" else self.tab_funciones).pack(fill=tk.BOTH, expand=True)
        for n, b in self.tab_btns.items():
            if n == nombre:
                b.config(bg=AREA, fg="white", activebackground=AREA, activeforeground="white")
            else:
                b.config(bg=CARD, fg=MUTED, activebackground=CARD_HI, activeforeground=TEXT)

    # ───────────────────────── teclados ─────────────────────────
    def crear_teclado_numeros(self, parent):
        # (texto insertado, tipo, texto visual)
        filas = [
            [("x", "var", None), ("y", "var", None), ("pi", "fn", "π"), ("e", "fn", None), ("DEL", "del", None)],
            [("7", "num", None), ("8", "num", None), ("9", "num", None), ("/", "op", "÷"), ("AC", "del", None)],
            [("4", "num", None), ("5", "num", None), ("6", "num", None), ("*", "op", "×"), ("(", "op", None)],
            [("1", "num", None), ("2", "num", None), ("3", "num", None), ("-", "op", "−"), (")", "op", None)],
            [("0", "num", None), (".", "num", None), (",", "num", None), ("+", "op", None), ("^", "op", None)],
            [("^2", "fn", "x²"), ("^3", "fn", "x³"), ("sqrt(", "fn", "√"), ("abs(", "fn", "|x|"), ("10^", "fn", "10ˣ")],
        ]
        self._montar(parent, filas, 5)

    def crear_teclado_funciones(self, parent):
        filas = [
            [("sen(", "fn", "sen"), ("cos(", "fn", "cos"), ("tg(", "fn", "tg"), ("DEL", "del", None)],
            [("sen^-1(", "fn", "sen⁻¹"), ("cos^-1(", "fn", "cos⁻¹"), ("tg^-1(", "fn", "tg⁻¹"), ("AC", "del", None)],
            [("ln(", "fn", "ln"), ("log10(", "fn", "log₁₀"), ("log2(", "fn", "log₂"), ("%", "op", None)],
            [("e^(", "fn", "eˣ"), ("10^(", "fn", "10ˣ"), ("sqrt(", "fn", "√"), ("abs(", "fn", "|x|")],
            [("(", "op", None), (")", "op", None), ("x", "var", None), ("pi", "fn", "π")],
            [("<=", "op", "≤"), (">=", "op", "≥"), ("!", "op", None), ("°", "op", None)],
        ]
        self._montar(parent, filas, 4)

    def _montar(self, parent, filas, cols):
        for i, fila in enumerate(filas):
            for j, (texto, tipo, visual) in enumerate(fila):
                if texto == "DEL":
                    cmd = self.borrar_ultimo
                elif texto == "AC":
                    cmd = self.limpiar_campo
                else:
                    cmd = lambda t=texto: self.insertar_texto(t)
                self._tecla(parent, texto, cmd, tipo, visual).grid(
                    row=i, column=j, padx=3, pady=3, sticky="nsew")
        for j in range(cols):
            parent.columnconfigure(j, weight=1, uniform="k")
        for i in range(len(filas)):
            parent.rowconfigure(i, weight=1, uniform="r")

    # ───────────────────────── edición ─────────────────────────
    def insertar_texto(self, texto):
        if self.campo_activo is None:
            self.campo_activo = self.entry_f
        pos = self.campo_activo.index(tk.INSERT)
        self.campo_activo.insert(pos, texto)
        self.campo_activo.icursor(pos + len(texto))
        self.campo_activo.focus_set()

    def borrar_ultimo(self):
        if self.campo_activo:
            pos = self.campo_activo.index(tk.INSERT)
            if pos > 0:
                self.campo_activo.delete(pos - 1, pos)
                self.campo_activo.icursor(pos - 1)
            self.campo_activo.focus_set()

    def limpiar_campo(self):
        if self.campo_activo:
            self.campo_activo.delete(0, tk.END)
            self.campo_activo.focus_set()

    # ───────────────────────── cálculo ─────────────────────────
    def ejecutar_calculo(self):
        try:
            f_str = self.entry_f.get()
            g_str = self.entry_g.get()
            a = evaluar_limite(self.entry_a.get())
            b = evaluar_limite(self.entry_b.get())
            n = int(self.entry_n.get())

            if a >= b:
                raise ValueError("El límite inferior (a) debe ser menor que el superior (b).")
            if n <= 0:
                raise ValueError("El número de subdivisiones debe ser mayor a 0.")

            area, puntos_f, puntos_g = calcular_area_riemann(f_str, g_str, a, b, n)

            self.lbl_resultado.config(text=f"{area:.6f}", fg=GOLD)
            self.lbl_info.config(text=f"[{a:g}, {b:g}]  ·  n = {n:,}  ·  Δx = {(b - a) / n:.2e}", fg=MUTED)
            self.datos = (puntos_f, puntos_g, a, b, f_str, g_str, area)
            self.xs = [p[0] for p in puntos_f]
            self.dibujar_grafica()

        except ValueError as e:
            messagebox.showerror("Error de Entrada", str(e))
            self.lbl_resultado.config(text="Error", fg=ERR)
        except Exception as e:
            messagebox.showerror("Error Inesperado", f"Ocurrió un error: {e}")
            self.lbl_resultado.config(text="Error", fg=ERR)

    # ───────────────────────── gráfica ─────────────────────────
    def obtener_paso_eje(self, rango):
        if rango == 0:
            return 1
        exponente = math.floor(math.log10(rango))
        fraccion = rango / (10 ** exponente)
        if fraccion < 1.5:
            paso = 1
        elif fraccion < 3:
            paso = 2
        elif fraccion < 7:
            paso = 5
        else:
            paso = 10
        return paso * (10 ** exponente)

    @staticmethod
    def _fmt(v):
        if abs(v) < 1e-10:
            return "0"
        return f"{v:.4g}"

    def _ticks(self, lo, hi):
        paso = self.obtener_paso_eje((hi - lo) / 5)
        v = math.ceil(lo / paso - 1e-9) * paso
        out = []
        while v <= hi + paso * 1e-6:
            out.append(v)
            v += paso
        return out

    def dibujar_grafica(self):
        c = self.canvas
        c.delete("all")
        w, h = c.winfo_width(), c.winfo_height()
        if w < 200 or h < 200:
            return

        if not self.datos:
            c.create_text(w / 2, h / 2, text="Ingresa f(x), g(x) y pulsa  CALCULAR ÁREA",
                          fill=MUTED, font=(FONT_UI, 14))
            return

        puntos_f, puntos_g, a, b, f_str, g_str, area = self.datos

        L, R, T, B = 64, 36, 64, 52
        pw, ph = w - L - R, h - T - B

        todos_y = [p[1] for p in puntos_f] + [p[1] for p in puntos_g]
        min_y, max_y = min(todos_y), max(todos_y)
        margen = (max_y - min_y) * 0.12 if max_y != min_y else 1
        min_y -= margen
        max_y += margen

        def mx(x):
            return L + (x - a) / (b - a) * pw

        def my(y):
            return T + ph - (y - min_y) / (max_y - min_y) * ph

        self.geom = (L, T, pw, ph, min_y, max_y)

        # Fondo del área de trazado
        c.create_rectangle(L, T, L + pw, T + ph, fill=PLOT_BG, outline=BORDER)

        # Cuadrícula + etiquetas
        for v in self._ticks(a, b):
            px = mx(v)
            c.create_line(px, T, px, T + ph, fill=GRID)
            c.create_text(px, T + ph + 16, text=self._fmt(v), fill=MUTED, font=(FONT_MONO, 9))
        for v in self._ticks(min_y, max_y):
            py = my(v)
            c.create_line(L, py, L + pw, py, fill=GRID)
            c.create_text(L - 10, py, text=self._fmt(v), fill=MUTED, font=(FONT_MONO, 9), anchor="e")

        # Ejes que pasan por el origen
        if min_y <= 0 <= max_y:
            c.create_line(L, my(0), L + pw, my(0), fill=GRID_STRONG, width=2)
        if a <= 0 <= b:
            c.create_line(mx(0), T, mx(0), T + ph, fill=GRID_STRONG, width=2)

        # Reducir puntos para dibujar con fluidez
        paso = max(1, len(puntos_f) // 500)
        idx = list(range(0, len(puntos_f), paso))
        if idx[-1] != len(puntos_f) - 1:
            idx.append(len(puntos_f) - 1)
        df = [puntos_f[i] for i in idx]
        dg = [puntos_g[i] for i in idx]

        # Área entre curvas (cuadriláteros por tramo)
        for i in range(len(df) - 1):
            c.create_polygon(
                mx(df[i][0]), my(df[i][1]), mx(df[i + 1][0]), my(df[i + 1][1]),
                mx(dg[i + 1][0]), my(dg[i + 1][1]), mx(dg[i][0]), my(dg[i][1]),
                fill=AREA, outline="", stipple="gray50")

        # Límites a y b
        for xv, nom in ((a, "a"), (b, "b")):
            c.create_line(mx(xv), T, mx(xv), T + ph, fill=AREA, dash=(5, 4), width=1)
            c.create_text(mx(xv), T - 10, text=f"{nom} = {self._fmt(xv)}", fill=AREA,
                          font=(FONT_UI, 9, "bold"))

        # Curvas con brillo
        def curva(pts, g1, g2, col):
            flat = []
            for p in pts:
                flat += [mx(p[0]), my(p[1])]
            if len(flat) >= 4:
                c.create_line(*flat, fill=g1, width=9, capstyle=tk.ROUND, joinstyle=tk.ROUND)
                c.create_line(*flat, fill=g2, width=5, capstyle=tk.ROUND, joinstyle=tk.ROUND)
                c.create_line(*flat, fill=col, width=2, capstyle=tk.ROUND, joinstyle=tk.ROUND)

        curva(dg, G_GLOW1, G_GLOW2, G_COL)
        curva(df, F_GLOW1, F_GLOW2, F_COL)

        # Encabezado: leyenda y área
        x0 = L
        for col, txt in ((F_COL, f"f(x) = {f_str}"), (G_COL, f"g(x) = {g_str}")):
            c.create_line(x0, 26, x0 + 24, 26, fill=col, width=3, capstyle=tk.ROUND)
            t = c.create_text(x0 + 32, 26, text=txt, fill=TEXT, font=(FONT_MONO, 11, "bold"), anchor="w")
            x0 = c.bbox(t)[2] + 28

        badge = c.create_text(w - R - 14, 26, text=f"A = {area:.6f}", fill=GOLD,
                              font=(FONT_MONO, 12, "bold"), anchor="e")
        bx = c.bbox(badge)
        r = c.create_rectangle(bx[0] - 12, bx[1] - 6, bx[2] + 12, bx[3] + 6,
                               fill="#1b1a2e", outline=GOLD)
        c.tag_lower(r, badge)

        c.create_text(L + pw / 2, h - 12, text="x", fill=MUTED, font=(FONT_UI, 10, "italic"))

    # ───────────────────────── hover interactivo ─────────────────────────
    def on_motion(self, e):
        c = self.canvas
        c.delete("hover")
        if not self.datos or not self.geom:
            return
        L, T, pw, ph, min_y, max_y = self.geom
        if not (L <= e.x <= L + pw and T <= e.y <= T + ph):
            return

        puntos_f, puntos_g, a, b, *_ = self.datos
        x = a + (e.x - L) / pw * (b - a)
        i = bisect_left(self.xs, x)
        if i >= len(self.xs):
            i = len(self.xs) - 1
        elif i > 0 and abs(self.xs[i - 1] - x) < abs(self.xs[i] - x):
            i -= 1
        xv, fy = puntos_f[i]
        gy = puntos_g[i][1]

        def my(y):
            return T + ph - (y - min_y) / (max_y - min_y) * ph

        px = L + (xv - a) / (b - a) * pw
        c.create_line(px, T, px, T + ph, fill=TEXT, dash=(2, 4), tags="hover")
        for yv, col in ((fy, F_COL), (gy, G_COL)):
            py = my(yv)
            c.create_oval(px - 6, py - 6, px + 6, py + 6, fill="", outline=col, width=1, tags="hover")
            c.create_oval(px - 3, py - 3, px + 3, py + 3, fill=col, outline="", tags="hover")

        lineas = [f"x = {xv:.4f}", f"f = {fy:.4f}", f"g = {gy:.4f}", f"|f−g| = {abs(fy - gy):.4f}"]
        cols = [TEXT, F_COL, G_COL, GOLD]
        bw, bh = 150, 84
        tx = px + 14 if px + 14 + bw < L + pw else px - 14 - bw
        ty = max(T + 6, min(e.y - bh / 2, T + ph - bh - 6))
        c.create_rectangle(tx, ty, tx + bw, ty + bh, fill="#141a30", outline=BORDER, tags="hover")
        for k, (ln, col) in enumerate(zip(lineas, cols)):
            c.create_text(tx + 12, ty + 14 + k * 19, text=ln, fill=col,
                          font=(FONT_MONO, 10, "bold"), anchor="w", tags="hover")


# Entrada
if __name__ == "__main__":
    root = tk.Tk()
    app = CalculadoraAreaApp(root)
    root.mainloop()