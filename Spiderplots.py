import tkinter as tk
from tkinter import filedialog, messagebox, colorchooser
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt


class SpiderPlotGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Mixed-Scale Spider Plot from Excel")
        self.root.geometry("950x850")

        self.sheets_data = {}
        self.param_names = []
        self.param_ranges = []

        self.group_vars = {}
        self.group_colors = {}
        self.group_color_buttons = {}

        self.create_widgets()

    # GUI
    def create_widgets(self):

        control = tk.Frame(self.root)
        control.pack(fill=tk.X, padx=10, pady=10)

        tk.Button(control, text="Load Excel", command=self.load_excel,
                  height=2, width=18).pack(side=tk.LEFT)

        self.file_label = tk.Label(control, text="No file loaded")
        self.file_label.pack(side=tk.LEFT, padx=10)

        # VISUAL OPTIONS
        vis = tk.LabelFrame(self.root, text="Visual Options")
        vis.pack(fill=tk.X, padx=10)

        self.font_entry = self._entry(vis, "Font size", "11")
        self.line_entry = self._entry(vis, "Line width", "2.5")
        self.marker_entry = self._entry(vis, "Marker size", "6")
        self.fill_entry = self._entry(vis, "Fill alpha", "0.15")

        # RANGES
        self.range_frame = tk.LabelFrame(self.root, text="Ranges")
        self.range_frame.pack(fill=tk.X, padx=10, pady=5)

        # GROUPS
        self.group_frame = tk.LabelFrame(self.root, text="Groups")
        self.group_frame.pack(fill=tk.X, padx=10, pady=5)

        tk.Button(self.root, text="Generate Plot",
                  command=self.generate_plot,
                  bg="green", fg="white",
                  font=("Arial", 12, "bold")).pack(pady=10)

    def _entry(self, parent, label, default):
        f = tk.Frame(parent)
        f.pack(anchor="w")
        tk.Label(f, text=label, width=12).pack(side=tk.LEFT)
        e = tk.Entry(f, width=8)
        e.insert(0, default)
        e.pack(side=tk.LEFT)
        return e

    # LOAD EXCEL
    def load_excel(self):

        path = filedialog.askopenfilename(filetypes=[("Excel", "*.xlsx *.xls")])
        if not path:
            return

        xls = pd.ExcelFile(path)

        self.sheets_data = {}
        first = None

        for sheet in xls.sheet_names:
            df = pd.read_excel(xls, sheet_name=sheet, header=None)
            self.sheets_data[sheet] = df
            if first is None:
                first = df

        self.file_label.config(text=path.split("/")[-1])

        # PARAM NAMES FROM FIRST ROW
        self.param_names = [
            str(first.iloc[0, i])
            for i in range(first.shape[1])
        ]

        # RANGES
        mins = [np.inf] * len(self.param_names)
        maxs = [-np.inf] * len(self.param_names)

        for df in self.sheets_data.values():
            for i in range(len(self.param_names)):

                vals = pd.to_numeric(df.iloc[1:, i],
                                     errors="coerce").dropna()

                if len(vals):
                    mins[i] = min(mins[i], vals.min())
                    maxs[i] = max(maxs[i], vals.max())

        for i in range(len(mins)):
            if np.isinf(mins[i]): mins[i] = 0
            if np.isinf(maxs[i]): maxs[i] = 1

        self.build_ranges(mins, maxs)
        self.build_groups()

    # RANGES
    def build_ranges(self, mins, maxs):

        for w in self.range_frame.winfo_children():
            w.destroy()

        self.min_entries = []
        self.max_entries = []

        for i, name in enumerate(self.param_names):

            tk.Label(self.range_frame, text=name).grid(row=i, column=0)

            mn = tk.Entry(self.range_frame, width=10)
            mn.insert(0, mins[i])
            mn.grid(row=i, column=1)

            mx = tk.Entry(self.range_frame, width=10)
            mx.insert(0, maxs[i])
            mx.grid(row=i, column=2)

            self.min_entries.append(mn)
            self.max_entries.append(mx)

    # GROUPS (COLOUR PICKER)
    def build_groups(self):

        for w in self.group_frame.winfo_children():
            w.destroy()

        self.group_vars = {}
        self.group_colors = {}
        self.group_buttons = {}

        defaults = ["blue", "red", "green", "purple", "orange"]

        for i, name in enumerate(self.sheets_data.keys()):

            var = tk.BooleanVar(value=True)
            self.group_vars[name] = var

            tk.Checkbutton(self.group_frame, text=name,
                           variable=var).grid(row=i, column=0, sticky="w")

            color = defaults[i % len(defaults)]
            self.group_colors[name] = color

            def make_cb(n=name):
                return lambda: self.pick_color(n)

            btn = tk.Button(
                self.group_frame,
                text="Colour",
                bg=color,
                command=make_cb()
            )

            btn.grid(row=i, column=1, padx=5)
            self.group_buttons[name] = btn

    def pick_color(self, name):
        c = colorchooser.askcolor()[1]
        if c:
            self.group_colors[name] = c
            self.group_buttons[name].config(bg=c)

    # PLOT
    def generate_plot(self):

        try:
            self.param_ranges = []

            for i in range(len(self.param_names)):
                self.param_ranges.append((
                    float(self.min_entries[i].get()),
                    float(self.max_entries[i].get())
                ))

            font = float(self.font_entry.get())
            lw = float(self.line_entry.get())
            ms = float(self.marker_entry.get())
            fa = float(self.fill_entry.get())

        except:
            messagebox.showerror("Error", "Bad settings")
            return

        groups = []

        for name, df in self.sheets_data.items():

            if not self.group_vars[name].get():
                continue

            vals = []

            for i in range(len(self.param_names)):

                v = pd.to_numeric(df.iloc[1:, i],
                                  errors="coerce").dropna().values

                vals.append(v)

            groups.append({
                "name": name,
                "values": vals,
                "color": self.group_colors[name]
            })

        self.plot(groups, font, lw, ms, fa)

    # SPIDER PLOT
    def plot(self, groups, font, lw, ms, fa):

        n = len(self.param_names)

        angles = np.linspace(0, 2*np.pi, n, endpoint=False).tolist()
        angles += angles[:1]

        fig, ax = plt.subplots(figsize=(9, 9),
                               subplot_kw=dict(polar=True))

        ax.set_theta_offset(np.pi/2)
        ax.set_theta_direction(-1)

        ax.set_xticks(angles[:-1])
        ax.set_xticklabels(self.param_names, fontsize=font)

        ax.set_rlim(0, 1)

        ax.set_yticks([])

        ax.grid(True, alpha=0.4)

        for g in groups:

            vals = []

            for v, (mn, mx) in zip(g["values"], self.param_ranges):

                m = np.mean(v)
                nrm = (m - mn) / (mx - mn)
                nrm = max(0, min(1, nrm))
                vals.append(nrm)

            vals += vals[:1]

            ax.plot(
                angles,
                vals,
                color=g["color"],
                linewidth=lw,
                marker="o",
                markersize=ms,
                label=g["name"]
            )

            ax.fill(
                angles,
                vals,
                color=g["color"],
                alpha=fa
            )

        ax.legend(loc="upper right", bbox_to_anchor=(1.25, 1.1))
        plt.tight_layout()
        plt.show()


if __name__ == "__main__":
    root = tk.Tk()
    app = SpiderPlotGUI(root)
    root.mainloop()