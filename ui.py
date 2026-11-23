from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from tkinter import filedialog, messagebox

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

import calculations
import plotting
from design_files import BeamFileError, load_beam, save_beam
from member_data import designations, get_member
from models import (
    BeamModel,
    LoadDirection,
    MemberType,
    PointLoad,
    SupportType,
    UniformLoad,
)
from validation import validate_cut, validate_model


PINK = "#fbeaf2"
PANEL = "#fffafd"
PURPLE = "#7654a7"
PURPLE_PALE = "#e7dafa"
INK = "#17151a"
MUTED = "#68616d"
GREEN = "#cfe9d7"
GREEN_TEXT = "#2f6842"
RED = "#f3d2d2"
RED_TEXT = "#8a3838"


class AppView:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("Beam Designer")
        self.root.geometry("1280x900")
        self.root.minsize(860, 620)
        self.root.configure(bg=PINK)
        self.point_rows: list[dict[str, object]] = []
        self.uniform_rows: list[dict[str, object]] = []
        self._building_member = False
        self._build_styles()
        self._build_menu()
        self._build_layout()
        self._load_example()
        self.recalculate()

    def _build_styles(self) -> None:
        style = ttk.Style(self.root)
        style.theme_use("clam")
        style.configure("TFrame", background=PINK)
        style.configure("Panel.TFrame", background=PANEL)
        style.configure("TLabel", background=PANEL, foreground=INK)
        style.configure("Muted.TLabel", background=PANEL, foreground=MUTED, font=("Segoe UI", 9))
        style.configure("Heading.TLabel", background=PANEL, foreground=INK, font=("Segoe UI", 11, "bold"))
        style.configure("Title.TLabel", background=PINK, foreground=INK, font=("Segoe UI", 16, "bold"))
        style.configure("TButton", padding=(8, 5))
        style.configure("Accent.TButton", background=PURPLE_PALE, foreground=PURPLE, padding=(8, 5))
        style.configure("TEntry", padding=5)
        style.configure("TCombobox", padding=4)
        style.configure("TLabelframe", background=PANEL, bordercolor="#dccfe1")
        style.configure("TLabelframe.Label", background=PANEL, foreground=INK, font=("Segoe UI", 10, "bold"))
        style.configure("Pass.TLabel", background=GREEN, foreground=GREEN_TEXT, padding=8)
        style.configure("Fail.TLabel", background=RED, foreground=RED_TEXT, padding=8)
        style.configure("MetricLavender.TLabel", background="#f2ecfb", foreground=INK, padding=8)
        style.configure("MetricBlue.TLabel", background="#dceaf6", foreground=INK, padding=8)
        style.configure("MetricGreen.TLabel", background=GREEN, foreground=INK, padding=8)
        style.configure("MetricPink.TLabel", background="#f4cfe1", foreground=INK, padding=8)

    def _build_menu(self) -> None:
        menu = tk.Menu(self.root)
        file_menu = tk.Menu(menu, tearoff=False)
        file_menu.add_command(label="Open", accelerator="Ctrl+O", command=self.open_beam)
        file_menu.add_command(label="Save", accelerator="Ctrl+S", command=self.save_beam)
        menu.add_cascade(label="File", menu=file_menu)
        self.root.configure(menu=menu)
        self.root.bind("<Control-o>", lambda _event: self.open_beam())
        self.root.bind("<Control-s>", lambda _event: self.save_beam())

    def _panel(self, parent: tk.Widget, title: str) -> ttk.LabelFrame:
        frame = ttk.LabelFrame(parent, text=title, style="TLabelframe", padding=10)
        frame.columnconfigure(0, weight=1)
        return frame

    def _build_layout(self) -> None:
        header = ttk.Frame(self.root)
        header.pack(fill="x", padx=18, pady=(12, 4))
        ttk.Label(header, text="🐼  Beam Designer", style="Title.TLabel").pack(side="left")
        self.header_status = ttk.Label(header, text="●  Example beam loaded", foreground=GREEN_TEXT, background=PINK)
        self.header_status.pack(side="right")

        split = ttk.PanedWindow(self.root, orient="horizontal")
        split.pack(fill="both", expand=True, padx=14, pady=10)
        left = ttk.Frame(split)
        right_container = ttk.Frame(split)
        split.add(left, weight=4)
        split.add(right_container, weight=1)
        left.columnconfigure(0, weight=1)
        left.rowconfigure(0, weight=1)
        right_container.columnconfigure(0, weight=1)
        right_container.rowconfigure(0, weight=1)

        left_canvas = tk.Canvas(left, bg=PINK, highlightthickness=0)
        left_scroll = ttk.Scrollbar(left, orient="vertical", command=left_canvas.yview)
        left_content = ttk.Frame(left_canvas)
        left_content.columnconfigure(0, weight=1)
        left_content.bind("<Configure>", lambda _: left_canvas.configure(scrollregion=left_canvas.bbox("all")))
        left_canvas.create_window((0, 0), window=left_content, anchor="nw", tags="content")
        left_canvas.configure(yscrollcommand=left_scroll.set)
        left_canvas.pack(side="left", fill="both", expand=True)
        left_scroll.pack(side="right", fill="y")
        left_canvas.bind("<Configure>", lambda event: left_canvas.itemconfigure("content", width=event.width))

        self._build_results(left_content)

        control_canvas = tk.Canvas(right_container, bg=PINK, highlightthickness=0)
        control_scroll = ttk.Scrollbar(right_container, orient="vertical", command=control_canvas.yview)
        control_content = ttk.Frame(control_canvas)
        control_content.columnconfigure(0, weight=1)
        control_content.bind("<Configure>", lambda _: control_canvas.configure(scrollregion=control_canvas.bbox("all")))
        control_canvas.create_window((0, 0), window=control_content, anchor="nw", tags="content")
        control_canvas.configure(yscrollcommand=control_scroll.set)
        control_canvas.pack(side="left", fill="both", expand=True)
        control_scroll.pack(side="right", fill="y")
        control_canvas.bind("<Configure>", lambda event: control_canvas.itemconfigure("content", width=event.width))
        self._build_controls(control_content)

    def _build_results(self, parent: ttk.Frame) -> None:
        beam_panel = self._panel(parent, "Beam and loading")
        beam_panel.pack(fill="x", pady=(0, 10))
        self.figure = plotting.create_figure()
        self.figure_canvas = FigureCanvasTkAgg(self.figure, master=beam_panel)
        self.figure_canvas.get_tk_widget().pack(fill="both", expand=True, padx=4, pady=4)

        self.results_container = ttk.Frame(parent)
        self.results_container.pack(fill="x")
        self.results_container.columnconfigure(0, weight=1)
        self.metrics = ttk.Frame(self.results_container)
        self.metrics.pack(fill="x", pady=(0, 8))
        for column in range(4):
            self.metrics.columnconfigure(column, weight=1)
        self.metric_labels: dict[str, ttk.Label] = {}
        for column, (key, title, style) in enumerate((
            ("left", "Left reaction", "MetricLavender.TLabel"),
            ("right", "Right reaction", "MetricBlue.TLabel"),
            ("moment", "Maximum moment", "MetricGreen.TLabel"),
            ("deflection", "Maximum deflection", "MetricPink.TLabel"),
        )):
            card = ttk.Frame(self.metrics, style="Panel.TFrame", padding=3)
            card.grid(row=0, column=column, sticky="nsew", padx=3)
            ttk.Label(card, text=title, style="Muted.TLabel").pack(anchor="w")
            value = ttk.Label(card, text="--", style=style, font=("Segoe UI", 12, "bold"))
            value.pack(fill="x")
            self.metric_labels[key] = value

        self.checks = ttk.Frame(self.results_container)
        self.checks.pack(fill="x", pady=(0, 8))
        self.checks.columnconfigure(0, weight=1)
        self.checks.columnconfigure(1, weight=1)
        self.bending_label = ttk.Label(self.checks, text="Bending stress\n--", style="Pass.TLabel")
        self.bending_label.grid(row=0, column=0, sticky="ew", padx=3)
        self.deflection_label = ttk.Label(self.checks, text="Deflection\n--", style="Fail.TLabel")
        self.deflection_label.grid(row=0, column=1, sticky="ew", padx=3)

        comparison = self._panel(self.results_container, "Section comparison")
        comparison.pack(fill="x", pady=(0, 10))
        cut_controls = ttk.Frame(comparison, style="Panel.TFrame")
        cut_controls.pack(fill="x")
        self.cut1_var = tk.StringVar(value="5")
        self.cut2_var = tk.StringVar(value="15")
        ttk.Label(cut_controls, text="Cut 1 location (ft)").grid(row=0, column=0, sticky="w")
        ttk.Entry(cut_controls, textvariable=self.cut1_var, width=12).grid(row=1, column=0, sticky="ew", padx=(0, 8))
        ttk.Label(cut_controls, text="Cut 2 location (ft)").grid(row=0, column=1, sticky="w")
        ttk.Entry(cut_controls, textvariable=self.cut2_var, width=12).grid(row=1, column=1, sticky="ew")
        cut_controls.columnconfigure(0, weight=1)
        cut_controls.columnconfigure(1, weight=1)
        self.cut_labels = []
        cut_cards = ttk.Frame(comparison, style="Panel.TFrame")
        cut_cards.pack(fill="x", pady=(10, 0))
        cut_cards.columnconfigure(0, weight=1)
        cut_cards.columnconfigure(1, weight=1)
        for column, name in enumerate(("Cut 1", "Cut 2")):
            card = ttk.Frame(cut_cards, style="Panel.TFrame", padding=8)
            card.grid(row=0, column=column, sticky="nsew", padx=3)
            ttk.Label(card, text=f"{name}  |  I-section sketch", style="Heading.TLabel").pack(anchor="w")
            values = ttk.Label(card, text="--", justify="left", style="Muted.TLabel")
            values.pack(anchor="w", pady=(6, 0))
            self.cut_labels.append(values)
        self.comparison_frame = comparison

        for variable in (self.cut1_var, self.cut2_var):
            variable.trace_add("write", lambda *_: self.recalculate())

    def _build_controls(self, parent: ttk.Frame) -> None:
        beam = self._panel(parent, "Beam inputs")
        beam.pack(fill="x", pady=(0, 8))
        self.support_var = tk.StringVar(value=SupportType.SIMPLY_SUPPORTED.value)
        self.span_var = tk.StringVar(value="20")
        self.deflection_limit_var = tk.StringVar(value="")
        ttk.Label(beam, text="Support type").grid(row=0, column=0, sticky="w")
        support = ttk.Combobox(beam, textvariable=self.support_var, values=[item.value for item in SupportType], state="readonly")
        support.grid(row=1, column=0, sticky="ew", pady=(2, 8))
        support.bind("<<ComboboxSelected>>", lambda _: self.recalculate())
        ttk.Label(beam, text="Span (ft)").grid(row=2, column=0, sticky="w")
        ttk.Entry(beam, textvariable=self.span_var).grid(row=3, column=0, sticky="ew")
        ttk.Label(beam, text="Deflection limit (in), blank for L/360").grid(row=4, column=0, sticky="w")
        ttk.Entry(beam, textvariable=self.deflection_limit_var).grid(row=5, column=0, sticky="ew")
        for variable in (self.span_var, self.deflection_limit_var):
            variable.trace_add("write", lambda *_: self.recalculate())

        self.loads_frame = self._panel(parent, "Load inputs")
        self.loads_frame.pack(fill="x", pady=(0, 8))
        self.load_rows_frame = ttk.Frame(self.loads_frame, style="Panel.TFrame")
        self.load_rows_frame.pack(fill="x")
        self.load_count_label = ttk.Label(self.loads_frame, text="", style="Muted.TLabel")
        self.load_count_label.pack(anchor="e")
        ttk.Button(self.loads_frame, text="+ Add point load", style="Accent.TButton", command=lambda: self._add_load("point")).pack(fill="x", pady=(6, 2))
        ttk.Button(self.loads_frame, text="+ Add uniform load", style="Accent.TButton", command=lambda: self._add_load("uniform")).pack(fill="x")
        self.self_weight_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            self.loads_frame,
            text="Include assumed self-weight",
            variable=self.self_weight_var,
            command=self.recalculate,
        ).pack(anchor="w", pady=(8, 0))

        member = self._panel(parent, "Member inputs")
        member.pack(fill="x", pady=(0, 8))
        self.member_type_var = tk.StringVar(value=MemberType.STEEL.value)
        self.designation_var = tk.StringVar()
        self.member_type_combo = ttk.Combobox(member, textvariable=self.member_type_var, values=[item.value for item in MemberType], state="readonly")
        self.member_type_combo.grid(row=0, column=0, sticky="ew")
        self.member_type_combo.bind("<<ComboboxSelected>>", self._member_type_changed)
        self.designation_combo = ttk.Combobox(member, textvariable=self.designation_var, state="readonly")
        self.designation_combo.grid(row=1, column=0, sticky="ew", pady=(6, 8))
        self.designation_combo.bind("<<ComboboxSelected>>", lambda _: self.recalculate())
        self.member_properties = ttk.Label(member, text="", justify="left", style="Muted.TLabel")
        self.member_properties.grid(row=2, column=0, sticky="w")
        self.validation_label = ttk.Label(member, text="", wraplength=280, justify="left")
        self.validation_label.grid(row=3, column=0, sticky="ew", pady=(10, 0))
        member.columnconfigure(0, weight=1)
        self._member_type_changed()

    def _load_example(self) -> None:
        self._add_load("point", 5.0, 5.0, LoadDirection.DOWN)
        self._add_load("point", 3.0, 17.0, LoadDirection.DOWN)
        self._add_load("uniform", 1.0, 0.0, LoadDirection.DOWN, end=20.0)

    def _add_load(self, kind: str, magnitude: float = 2.0, position: float = 10.0, direction: LoadDirection = LoadDirection.DOWN, end: float = 20.0) -> None:
        row = ttk.Frame(self.load_rows_frame, style="Panel.TFrame", padding=5)
        row.pack(fill="x", pady=3)
        variables: dict[str, object] = {
            "kind": kind,
            "magnitude": tk.StringVar(value=str(magnitude)),
            "direction": tk.StringVar(value=direction.value),
            "_row": row,
        }
        if kind == "point":
            variables["position"] = tk.StringVar(value=str(position))
            ttk.Label(row, text="Point load").grid(row=0, column=0, columnspan=2, sticky="w")
            self._field(row, "Magnitude (kip)", variables["magnitude"], 1, 0)
            self._field(row, "Position (ft)", variables["position"], 1, 1)
        else:
            variables["start"] = tk.StringVar(value=str(position))
            variables["end"] = tk.StringVar(value=str(end))
            ttk.Label(row, text="Uniform load").grid(row=0, column=0, columnspan=2, sticky="w")
            self._field(row, "Magnitude (kip/ft)", variables["magnitude"], 1, 0)
            self._field(row, "From (ft)", variables["start"], 1, 1)
            self._field(row, "To (ft)", variables["end"], 2, 0)
        direction_combo = ttk.Combobox(row, textvariable=variables["direction"], values=["down", "up"], state="readonly", width=10)
        direction_combo.grid(row=2 if kind == "point" else 3, column=1, sticky="ew", padx=3, pady=2)
        ttk.Label(row, text="Direction").grid(row=2 if kind == "point" else 3, column=0, sticky="w")
        ttk.Button(row, text="Remove", command=lambda: self._remove_load(row, variables)).grid(row=2 if kind == "point" else 4, column=0, columnspan=2, sticky="ew", pady=(3, 0))
        row.columnconfigure(0, weight=1)
        row.columnconfigure(1, weight=1)
        for variable in variables.values():
            if isinstance(variable, tk.Variable):
                variable.trace_add("write", lambda *_: self.recalculate())
        (self.point_rows if kind == "point" else self.uniform_rows).append(variables)
        self._update_load_count()

    def _field(self, parent: ttk.Frame, label: str, variable: tk.Variable, row: int, column: int) -> None:
        cell = ttk.Frame(parent, style="Panel.TFrame")
        cell.grid(row=row, column=column, sticky="ew", padx=3)
        ttk.Label(cell, text=label, style="Muted.TLabel").pack(anchor="w")
        ttk.Entry(cell, textvariable=variable).pack(fill="x")

    def _remove_load(self, row: ttk.Frame, variables: dict[str, object]) -> None:
        row.destroy()
        rows = self.point_rows if variables["kind"] == "point" else self.uniform_rows
        rows.remove(variables)
        self._update_load_count()
        self.recalculate()

    def _update_load_count(self) -> None:
        self.load_count_label.configure(text=f"{len(self.point_rows) + len(self.uniform_rows)} total")

    def _member_type_changed(self, _event=None) -> None:
        if self._building_member:
            return
        self._building_member = True
        member_type = MemberType(self.member_type_var.get())
        values = designations(member_type)
        self.designation_combo.configure(values=values)
        self.designation_var.set(values[0])
        self._building_member = False
        self.recalculate()

    def _read_float(self, variable: tk.Variable) -> float | None:
        try:
            text = str(variable.get()).strip()
            return float(text) if text else None
        except (TypeError, ValueError):
            return None

    def save_beam(self) -> None:
        model = self._model()
        errors = validate_model(model)
        if errors:
            messagebox.showerror("Cannot save beam", errors[0].message, parent=self.root)
            return
        path = filedialog.asksaveasfilename(
            parent=self.root,
            title="Save beam design",
            defaultextension=".beam.json",
            filetypes=[("Beam design", "*.beam.json"), ("JSON", "*.json"), ("All files", "*.*")],
        )
        if not path:
            return
        try:
            save_beam(path, model)
        except BeamFileError as exc:
            messagebox.showerror("Save failed", str(exc), parent=self.root)
            return
        messagebox.showinfo("Beam saved", "Beam design saved successfully.", parent=self.root)

    def open_beam(self) -> None:
        path = filedialog.askopenfilename(
            parent=self.root,
            title="Open beam design",
            filetypes=[("Beam design", "*.beam.json"), ("JSON", "*.json"), ("All files", "*.*")],
        )
        if not path:
            return
        try:
            model = load_beam(path)
            errors = validate_model(model)
            if errors:
                raise BeamFileError(errors[0].message)
        except BeamFileError as exc:
            messagebox.showerror("Open failed", str(exc), parent=self.root)
            return
        self._apply_model(model)
        self.recalculate()
        messagebox.showinfo("Beam opened", "Beam design opened successfully.", parent=self.root)

    def _clear_loads(self) -> None:
        for row in self.point_rows:
            row["_row"].destroy()
        for row in self.uniform_rows:
            row["_row"].destroy()
        self.point_rows.clear()
        self.uniform_rows.clear()

    def _apply_model(self, model: BeamModel) -> None:
        self._clear_loads()
        self.support_var.set(model.support_type.value)
        self.span_var.set(str(model.span))
        self.deflection_limit_var.set("" if model.deflection_limit is None else str(model.deflection_limit))
        self.self_weight_var.set(model.include_self_weight)
        self.member_type_var.set(model.member.member_type.value)
        self._member_type_changed()
        self.designation_var.set(model.member.designation)
        for load in model.point_loads:
            self._add_load("point", load.magnitude, load.position, load.direction)
        for load in model.uniform_loads:
            self._add_load("uniform", load.magnitude, load.start, load.direction, end=load.end)
        if not model.point_loads and not model.uniform_loads:
            self._update_load_count()

    def _model(self) -> BeamModel:
        span = self._read_float(self.span_var) or 0.0
        deflection_text = str(self.deflection_limit_var.get()).strip()
        deflection_limit = self._read_float(self.deflection_limit_var)
        if deflection_text and deflection_limit is None:
            deflection_limit = -1.0
        member_type = MemberType(self.member_type_var.get())
        member = get_member(member_type, self.designation_var.get())
        point_loads = []
        for row in self.point_rows:
            magnitude = self._read_float(row["magnitude"])
            position = self._read_float(row["position"])
            point_loads.append(PointLoad(
                magnitude if magnitude is not None else 0.0,
                position if position is not None else -1.0,
                LoadDirection(row["direction"].get()),
            ))
        uniform_loads = []
        for row in self.uniform_rows:
            magnitude = self._read_float(row["magnitude"])
            start = self._read_float(row["start"])
            end = self._read_float(row["end"])
            uniform_loads.append(UniformLoad(
                magnitude if magnitude is not None else 0.0,
                start if start is not None else -1.0,
                end if end is not None else -1.0,
                LoadDirection(row["direction"].get()),
            ))
        return BeamModel(
            span,
            SupportType(self.support_var.get()),
            point_loads,
            uniform_loads,
            member,
            self.self_weight_var.get(),
            deflection_limit,
        )

    def _set_status(self, message: str, valid: bool) -> None:
        self.validation_label.configure(text=("✓ " if valid else "! ") + message, style="Pass.TLabel" if valid else "Fail.TLabel")
        self.header_status.configure(text="●  Valid results" if valid else "●  Invalid inputs", foreground=GREEN_TEXT if valid else RED_TEXT)

    def _hide_results(self) -> None:
        for axis in self.figure.axes:
            axis.clear()
        self.figure_canvas.draw_idle()
        for label in self.metric_labels.values():
            label.configure(text="--")
        self.bending_label.configure(text="Bending stress\n--", style="Fail.TLabel")
        self.deflection_label.configure(text="Deflection\n--", style="Fail.TLabel")
        for label in self.cut_labels:
            label.configure(text="Comparison unavailable")

    def recalculate(self) -> None:
        if not hasattr(self, "validation_label"):
            return
        model = self._model()
        errors = validate_model(model)
        cut1 = self._read_float(self.cut1_var) or -1.0
        cut2 = self._read_float(self.cut2_var) or -1.0
        errors.extend(error for error in (validate_cut(cut1, model.span, 1), validate_cut(cut2, model.span, 2)) if error)
        if errors:
            self._set_status(errors[0].message, False)
            self._hide_results()
            return

        results = calculations.calculate(model, (cut1, cut2))
        self._set_status(f"{len(model.point_loads) + len(model.uniform_loads)} loads entered. Assumed self-weight: {'included' if model.include_self_weight else 'excluded'}.", True)
        self.metric_labels["left"].configure(text=f"{results.reactions.left:.2f} kip")
        self.metric_labels["right"].configure(text=f"{results.reactions.right:.2f} kip")
        self.metric_labels["moment"].configure(text=f"{abs(results.max_absolute_moment):.2f} kip-ft")
        self.metric_labels["deflection"].configure(text=f"{results.deflection_check.actual:.3f} in")
        self.bending_label.configure(
            text=f"{'✓' if results.bending_check.passes else '✕'} Bending stress\n{results.bending_check.actual:.2f} ksi of {results.bending_check.allowable:.2f} ksi at {results.bending_check.location:.1f} ft",
            style="Pass.TLabel" if results.bending_check.passes else "Fail.TLabel",
        )
        self.deflection_label.configure(
            text=f"{'✓' if results.deflection_check.passes else '✕'} Deflection\n{results.deflection_check.actual:.3f} in of {results.deflection_check.allowable:.3f} in at {results.deflection_check.location:.1f} ft",
            style="Pass.TLabel" if results.deflection_check.passes else "Fail.TLabel",
        )
        for label, cut in zip(self.cut_labels, results.cuts):
            label.configure(
                text=f"Location: {cut.location:.1f} ft\n"
                f"Shear: {cut.shear:+.2f} kip\n"
                f"Moment: {cut.moment:+.2f} kip-ft\n"
                f"Bending stress: {cut.stress:.2f} ksi\n"
                f"Deflection slope: {cut.slope:+.6f} rad"
            )
        plotting.render(self.figure, model, results)
        self.figure_canvas.draw_idle()
