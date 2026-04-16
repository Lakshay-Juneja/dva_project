import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import pandas as pd
import numpy as np
import os

# --- Data Import (DO NOT CHANGE LOGIC) ---
try:
    from ipl import (
        df_raw,
        overview_matches, overview_runs, overview_boundaries, overview_teams,
        runs_trend, era_avg_score, era_avg_wickets, era_runrate, era_six_counts, era_wicket_counts,
        team_season_summary, total_wickets_global, global_avg_rr, get_best_worst_seasons,
        top_10_batters, top_10_bowlers, top_venues, top_wicket_venues, season_summary, get_player_stats
    )
except Exception as e:
    import sys
    print(f"Data loading error: {e}")
    sys.exit(1)

# --- Configuration ---
WINDOW_SIZE = "1600x950"
COLOR_SIDEBAR = "#12355b"
COLOR_MAIN_BG = "#f4f7fb"
COLOR_PRIMARY = "#2563eb"
COLOR_ACCENT = "#ef4444"
COLOR_SUCCESS = "#10b981"
COLOR_CARD_BG = "#ffffff"
COLOR_TEXT_PRIMARY = "#0f172a"
COLOR_TEXT_SECONDARY = "#64748b"

FONT_TITLE = ("Segoe UI", 22, "bold")
FONT_SECTION = ("Segoe UI", 14, "bold")
FONT_KPI_VAL = ("Segoe UI", 20, "bold")
FONT_LABEL = ("Segoe UI", 11)

class IPLDashboardApp:
    def __init__(self, root):
        self.root = root
        self.root.title("IPL Analytics Dashboard")
        self.root.geometry(WINDOW_SIZE)
        self.root.state('zoomed')
        self.root.configure(bg=COLOR_MAIN_BG)
        
        # Global UI Styling for Combobox Dropdowns
        self.root.option_add('*TCombobox*Listbox.font', ("Segoe UI", 12))
        self.root.option_add('*TCombobox*Listbox.selectBackground', COLOR_PRIMARY)
        self.root.option_add('*TCombobox*Listbox.selectForeground', "white")

        # Main Containers
        self.sidebar = tk.Frame(self.root, width=280, bg=COLOR_SIDEBAR)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        self.content_frame = tk.Frame(self.root, bg=COLOR_MAIN_BG)
        self.content_frame.pack(side="right", fill="both", expand=True)

        self.setup_sidebar()
        self.show_page("Overview")

    def setup_sidebar(self):
        # Logo
        try:
            logo_path = os.path.join("public", "IPL Logo.avif")
            img = Image.open(logo_path)
            img = img.resize((200, 120), Image.LANCZOS)
            self.logo_img = ImageTk.PhotoImage(img)
            logo_label = tk.Label(self.sidebar, image=self.logo_img, bg=COLOR_SIDEBAR)
            logo_label.pack(pady=(30, 5))
        except:
            tk.Label(self.sidebar, text="IPL Analytics", font=FONT_TITLE, fg="white", bg=COLOR_SIDEBAR).pack(pady=40)

        tk.Label(self.sidebar, text="Analytics Platform", font=("Segoe UI", 11, "italic"), fg="#94a3b8", bg=COLOR_SIDEBAR).pack(pady=(0, 30))

        # RadioButtons for Navigation
        self.nav_var = tk.StringVar(value="Overview")
        
        pages = [
            ("Overview", "Overview"),
            ("Era Analysis", "Era Analysis"),
            ("Team Performance", "Team Performance"),
            ("Player Analysis", "Player Analysis"),
            ("Venue Analysis", "Venue Analysis")
        ]

        for text, val in pages:
            rb = tk.Radiobutton(
                self.sidebar, text=f"  {text}", value=val, variable=self.nav_var,
                font=("Segoe UI", 12, "bold"), fg="white", bg=COLOR_SIDEBAR,
                selectcolor=COLOR_PRIMARY, activebackground=COLOR_PRIMARY,
                activeforeground="white", indicatoron=0, anchor="w",
                padx=20, pady=12, borderwidth=0,
                command=lambda v=val: self.show_page(v)
            )
            rb.pack(fill="x", padx=15, pady=2)

    def clear_content(self):
        for widget in self.content_frame.winfo_children():
            widget.destroy()

    def apply_modern_plot_style(self, ax, title="", x_label="", y_label="", is_secondary=False, color=COLOR_TEXT_SECONDARY):
        """Standardizes axis styling across all charts."""
        ax.set_title(title, fontsize=14, fontweight='bold', pad=20, color=COLOR_SIDEBAR)
        if x_label: ax.set_xlabel(x_label, fontsize=11, fontweight='bold', color=COLOR_TEXT_SECONDARY)
        if y_label: ax.set_ylabel(y_label, fontsize=11, fontweight='bold', color=color)
        
        ax.tick_params(axis='both', which='major', labelsize=10, colors=COLOR_TEXT_SECONDARY)
        if is_secondary:
            ax.tick_params(axis='y', colors=color)
            ax.spines['right'].set_color(color)
            ax.spines['right'].set_visible(True)
        else:
            ax.spines['right'].set_visible(False)
            
        ax.spines['top'].set_visible(False)
        ax.spines['left'].set_color('#e2e8f0')
        ax.spines['bottom'].set_color('#e2e8f0')
        ax.grid(True, linestyle='--', alpha=0.3, axis='y')

    def create_kpi_card(self, parent, label, value):
        card = tk.Frame(parent, bg=COLOR_CARD_BG, padx=25, pady=20, highlightthickness=1, highlightbackground="#e2e8f0")
        tk.Label(card, text=label.upper(), font=("Segoe UI", 11, "bold"), fg=COLOR_TEXT_SECONDARY, bg=COLOR_CARD_BG).pack(anchor="w")
        tk.Label(card, text=value, font=FONT_KPI_VAL, fg=COLOR_SIDEBAR, bg=COLOR_CARD_BG).pack(anchor="w", pady=(5, 0))
        return card

    def show_insights_popup(self, title, insights):
        popup = tk.Toplevel(self.root)
        popup.title(title)
        popup.geometry("700x500")
        popup.configure(bg="#f8fafc")
        popup.transient(self.root)
        popup.grab_set()

        hdr = tk.Frame(popup, bg=COLOR_PRIMARY, height=70)
        hdr.pack(fill="x")
        tk.Label(hdr, text=f"✨ {title}", font=FONT_SECTION, fg="white", bg=COLOR_PRIMARY).pack(pady=20, padx=30, side="left")
        
        main = tk.Frame(popup, bg="white", padx=40, pady=40, highlightthickness=1, highlightbackground="#e2e8f0")
        main.pack(fill="both", expand=True, padx=20, pady=20)
        
        for line in insights:
            f = tk.Frame(main, bg="white")
            f.pack(fill="x", pady=8)
            tk.Label(f, text="•", font=("Segoe UI", 12, "bold"), fg=COLOR_PRIMARY, bg="white").pack(side="left")
            tk.Label(f, text=line, font=("Segoe UI", 11), fg=COLOR_TEXT_PRIMARY, bg="white", wraplength=550, justify="left").pack(side="left", padx=10)
            
        tk.Button(popup, text="Close Insights", command=popup.destroy, font=("Segoe UI", 10, "bold"), 
                  fg="white", bg=COLOR_SIDEBAR, padx=30, pady=8).pack(pady=(0, 20))

    def show_page(self, name):
        self.clear_content()
        # Responsive header with white bar
        self.header_frame = tk.Frame(self.content_frame, bg="white", height=70)
        self.header_frame.pack(fill="x")
        self.header_frame.pack_propagate(False)
        tk.Label(self.header_frame, text=name, font=FONT_TITLE, fg=COLOR_TEXT_PRIMARY, bg="white").pack(side="left", padx=40)

        if name == "Overview": self.render_overview()
        elif name == "Era Analysis": self.render_era()
        elif name == "Team Performance": self.render_team()
        elif name == "Player Analysis": self.render_player()
        elif name == "Venue Analysis": self.render_venue()

    def render_overview(self):
        # KPI Row
        kpi_frame = tk.Frame(self.content_frame, bg=COLOR_MAIN_BG)
        kpi_frame.pack(fill="x", padx=40, pady=20)
        
        metrics = [
            ("Total Matches", f"{overview_matches['Value'].iloc[0]:,}"),
            ("Total Runs", f"{int(overview_runs['Value'].iloc[0]):,}"),
            ("Total Wickets", f"{int(total_wickets_global):,}"),
            ("Avg Run Rate", f"{global_avg_rr:.2f}")
        ]
        
        for i, (label, val) in enumerate(metrics):
            card = self.create_kpi_card(kpi_frame, label, val)
            card.grid(row=0, column=i, padx=10, sticky="nsew")
            kpi_frame.grid_columnconfigure(i, weight=1)

        # Combined Dual-Axis Chart
        chart_frame = tk.Frame(self.content_frame, bg=COLOR_CARD_BG, padx=20, pady=20)
        chart_frame.pack(fill="both", expand=True, padx=40, pady=(0, 40))
        
        fig, ax1 = plt.subplots(figsize=(15, 8), dpi=100, facecolor='white')
        ax2 = ax1.twinx()
        
        # Dual Lines
        ax1.plot(season_summary['season'], season_summary['Runs'], marker='o', color=COLOR_PRIMARY, linewidth=3, label='Runs Trend')
        ax2.plot(season_summary['season'], season_summary['Wickets'], marker='s', color=COLOR_ACCENT, linewidth=3, label='Wickets Trend')
        
        self.apply_modern_plot_style(ax1, "Runs & Wickets Trend (2008-2025)", "Season", "Runs Scored", color=COLOR_PRIMARY)
        self.apply_modern_plot_style(ax2, y_label="Wickets Taken", is_secondary=True, color=COLOR_ACCENT)
        
        # Merge legends with better styling
        lines, labels = ax1.get_legend_handles_labels()
        lines2, labels2 = ax2.get_legend_handles_labels()
        ax1.legend(lines + lines2, labels + labels2, loc='upper left', frameon=True, facecolor='white', edgecolor='#e2e8f0', fontsize=10)
        
        fig.tight_layout()
        canvas = FigureCanvasTkAgg(fig, master=chart_frame)
        canvas.draw(); canvas.get_tk_widget().pack(fill="both", expand=True)

        ins = [
            f"IPL has seen a huge {int(overview_runs['Value'].iloc[0]):,} total runs since 2008. It's growing every year.",
            f"The average run rate is {global_avg_rr:.2f}. This shows that players are hitting the ball much harder now.",
            "Both runs and wickets are increasing, meaning every match is now a high-scoring thriller."
        ]
        tk.Button(self.header_frame, text="✨ Show Insights", font=("Segoe UI", 10, "bold"), bg=COLOR_SUCCESS, fg="white", 
                  command=lambda: self.show_insights_popup("Overview Insights", ins), padx=20, pady=5).pack(side="right", padx=40)

    def render_era(self):
        # KPI Row: Summary of Wicket counts / Six counts
        kpi_frame = tk.Frame(self.content_frame, bg=COLOR_MAIN_BG)
        kpi_frame.pack(fill="x", padx=40, pady=10)
        eras = era_avg_score['era'].tolist()
        for i, era in enumerate(eras):
            runs = era_avg_score[era_avg_score['era'] == era]['avg_match_score'].iloc[0]
            card = self.create_kpi_card(kpi_frame, f"Era {era}", f"Avg {int(runs)} Runs")
            card.grid(row=0, column=i, padx=10, sticky="nsew")
            kpi_frame.grid_columnconfigure(i, weight=1)

        # Charts Row 1: Avg Runs & Avg Wickets
        row1 = tk.Frame(self.content_frame, bg=COLOR_MAIN_BG)
        row1.pack(fill="both", expand=True, padx=40, pady=10)
        row1.grid_columnconfigure(0, weight=1)
        row1.grid_columnconfigure(1, weight=1)
        
        c1 = tk.Frame(row1, bg=COLOR_CARD_BG, padx=10, pady=10)
        c1.grid(row=0, column=0, padx=(0, 10), sticky="nsew")
        fig1, ax1 = plt.subplots(figsize=(6, 4), dpi=90, facecolor='white')
        ax1.bar(era_avg_score['era'], era_avg_score['avg_match_score'], color=COLOR_PRIMARY)
        self.apply_modern_plot_style(ax1, "Avg Runs per Match (Era)")
        fig1.tight_layout()
        FigureCanvasTkAgg(fig1, c1).get_tk_widget().pack(fill="both", expand=True)

        c2 = tk.Frame(row1, bg=COLOR_CARD_BG, padx=10, pady=10)
        c2.grid(row=0, column=1, padx=(10, 0), sticky="nsew")
        fig2, ax2 = plt.subplots(figsize=(6, 4), dpi=90, facecolor='white')
        ax2.bar(era_avg_wickets['era'], era_avg_wickets['avg_match_wickets'], color=COLOR_SUCCESS)
        self.apply_modern_plot_style(ax2, "Avg Wickets per Match (Era)")
        fig2.tight_layout()
        FigureCanvasTkAgg(fig2, c2).get_tk_widget().pack(fill="both", expand=True)

        # Row 2: Run Rate Trend
        row2 = tk.Frame(self.content_frame, bg=COLOR_CARD_BG, padx=20, pady=20)
        row2.pack(fill="both", expand=True, padx=40, pady=(10, 30))
        fig3, ax3 = plt.subplots(figsize=(14, 4), dpi=90, facecolor='white')
        ax3.plot(era_runrate['era'], era_runrate['run_rate'], marker='o', color=COLOR_ACCENT, linewidth=4)
        self.apply_modern_plot_style(ax3, "Run Rate Progression across Eras")
        fig3.tight_layout()
        FigureCanvasTkAgg(fig3, row2).get_tk_widget().pack(fill="both", expand=True)

        ins = [
            "Scores in 2008 were much lower than they are now. The game has changed a lot.",
            f"The run rate has jumped from {era_runrate['run_rate'].iloc[0]:.2f} to {era_runrate['run_rate'].iloc[-1]:.2f}. Teams are hitting more big shots.",
            "Even though players score more, bowlers are still taking lots of wickets to slow them down."
        ]
        tk.Button(self.header_frame, text="✨ Show Insights", font=("Segoe UI", 10, "bold"), bg=COLOR_SUCCESS, fg="white", 
                  command=lambda: self.show_insights_popup("Era Insights", ins), padx=20, pady=5).pack(side="right", padx=40)

    def render_team(self):
        # Selector Card for Team
        selector_card = tk.Frame(self.content_frame, bg=COLOR_CARD_BG, padx=25, pady=15, highlightthickness=1, highlightbackground="#e2e8f0")
        selector_card.pack(fill="x", padx=40, pady=10)
        
        tk.Label(selector_card, text="Select Team Performance:", font=FONT_SECTION, bg=COLOR_CARD_BG, fg=COLOR_SIDEBAR).pack(side="left")
        teams = sorted(team_season_summary['Team'].unique().tolist())
        self.team_selection = tk.StringVar(value=teams[0])
        
        # Larger Combobox
        combo = ttk.Combobox(selector_card, textvariable=self.team_selection, values=teams, font=("Segoe UI", 12), state="readonly", width=35)
        combo.pack(side="left", padx=25)
        combo.bind("<<ComboboxSelected>>", lambda e: self.update_team_chart())
        
        # Chart Area
        self.team_chart_frame = tk.Frame(self.content_frame, bg=COLOR_CARD_BG, padx=20, pady=20)
        self.team_chart_frame.pack(fill="both", expand=True, padx=40, pady=(10, 40))
        self.update_team_chart()

    def update_team_chart(self):
        for w in self.team_chart_frame.winfo_children(): w.destroy()
        team = self.team_selection.get()
        data = team_season_summary[team_season_summary['Team'] == team]
        
        fig, ax1 = plt.subplots(figsize=(14, 7), dpi=100, facecolor='white')
        ax2 = ax1.twinx()
        
        ax1.plot(data['season'], data['Total Runs'], marker='o', color=COLOR_PRIMARY, linewidth=4, label='Season Runs')
        ax2.plot(data['season'], data['Wickets Taken'], marker='s', color=COLOR_ACCENT, linewidth=4, label='Season Wickets')
        
        self.apply_modern_plot_style(ax1, f"{team}: Performance (Runs + Wickets)", "Season", "Runs Scored", color=COLOR_PRIMARY)
        self.apply_modern_plot_style(ax2, y_label="Wickets Taken", is_secondary=True, color=COLOR_ACCENT)
        
        lines, labels = ax1.get_legend_handles_labels()
        lines2, labels2 = ax2.get_legend_handles_labels()
        ax1.legend(lines + lines2, labels + labels2, loc='upper left', frameon=True, facecolor='white', edgecolor='#e2e8f0')
        
        fig.tight_layout()
        canvas = FigureCanvasTkAgg(fig, master=self.team_chart_frame)
        canvas.draw(); canvas.get_tk_widget().pack(fill="both", expand=True)

    def render_player(self):
        # Selector Card for Player
        selector_card = tk.Frame(self.content_frame, bg=COLOR_CARD_BG, padx=25, pady=20, highlightthickness=1, highlightbackground="#e2e8f0")
        selector_card.pack(fill="x", padx=40, pady=10)
        
        all_players = sorted(list(set(top_10_batters['batter'].tolist() + top_10_bowlers['bowler'].tolist())))
        self.player_selection = tk.StringVar(value=all_players[0])
        
        left_grp = tk.Frame(selector_card, bg=COLOR_CARD_BG)
        left_grp.pack(side="left")
        
        tk.Label(left_grp, text="Expert Player Explorer:", font=FONT_SECTION, bg=COLOR_CARD_BG, fg=COLOR_SIDEBAR).pack(side="left")
        
        # Larger Combobox
        combo = ttk.Combobox(left_grp, textvariable=self.player_selection, values=all_players, font=("Segoe UI", 12), width=35, state="readonly")
        combo.pack(side="left", padx=25)
        
        # Career Stats Display
        self.player_info_label = tk.Label(selector_card, text="", font=("Segoe UI", 12, "bold"), fg=COLOR_PRIMARY, bg=COLOR_CARD_BG)
        self.player_info_label.pack(side="right", padx=10)
        
        def update_player_info(event=None):
            p = self.player_selection.get()
            s = get_player_stats(p)
            txt = f"{p} Career >> "
            if 'runs' in s: txt += f"Runs: {s['runs']:,} [SR: {s['sr']:.2f}] | "
            if 'wickets' in s: txt += f"Wickets: {s['wickets']} [Econ: {s['econ']:.2f}]"
            self.player_info_label.configure(text=txt)
            
        combo.bind("<<ComboboxSelected>>", update_player_info)
        update_player_info() # Initial load
        
        # Charts Row
        chart_row = tk.Frame(self.content_frame, bg=COLOR_MAIN_BG)
        chart_row.pack(fill="both", expand=True, padx=40, pady=10)
        chart_row.grid_columnconfigure(0, weight=1)
        chart_row.grid_columnconfigure(1, weight=1)

        c1 = tk.Frame(chart_row, bg=COLOR_CARD_BG, padx=15, pady=15)
        c1.grid(row=0, column=0, padx=(0, 10), sticky="nsew")
        fig1, ax1 = plt.subplots(figsize=(6, 8), dpi=90, facecolor='white')
        ax1.barh(top_10_batters['batter'], top_10_batters['Runs'], color='#1e40af')
        ax1.invert_yaxis()
        self.apply_modern_plot_style(ax1, "Top 10 Batsmen", x_label="Runs Scored")
        fig1.tight_layout()
        FigureCanvasTkAgg(fig1, c1).get_tk_widget().pack(fill="both", expand=True)

        c2 = tk.Frame(chart_row, bg=COLOR_CARD_BG, padx=15, pady=15)
        c2.grid(row=0, column=1, padx=(10, 0), sticky="nsew")
        fig2, ax2 = plt.subplots(figsize=(6, 8), dpi=90, facecolor='white')
        ax2.barh(top_10_bowlers['bowler'], top_10_bowlers['Wickets'], color='#dc2626')
        ax2.invert_yaxis()
        self.apply_modern_plot_style(ax2, "Top 10 Bowlers", x_label="Wickets Taken")
        fig2.tight_layout()
        FigureCanvasTkAgg(fig2, c2).get_tk_widget().pack(fill="both", expand=True)

    def render_venue(self):
        # Two Charts: Avg Runs & Avg Wickets per Venue
        row1 = tk.Frame(self.content_frame, bg=COLOR_MAIN_BG)
        row1.pack(fill="both", expand=True, padx=40, pady=20)
        row1.grid_columnconfigure(0, weight=1)
        row1.grid_columnconfigure(1, weight=1)
        
        c1 = tk.Frame(row1, bg=COLOR_CARD_BG, padx=15, pady=15)
        c1.grid(row=0, column=0, padx=(0, 10), sticky="nsew")
        fig1, ax1 = plt.subplots(figsize=(8, 7), dpi=105, facecolor='white')
        ax1.bar(top_venues['venue'], top_venues['Avg Score'], color='#1e293b')
        self.apply_modern_plot_style(ax1, "High-Scoring Grounds (Avg Runs/Match)")
        plt.setp(ax1.get_xticklabels(), rotation=35, horizontalalignment='right', fontsize=9)
        fig1.subplots_adjust(bottom=0.30) # Critical for rotated labels
        FigureCanvasTkAgg(fig1, c1).get_tk_widget().pack(fill="both", expand=True)

        c2 = tk.Frame(row1, bg=COLOR_CARD_BG, padx=15, pady=15)
        c2.grid(row=0, column=1, padx=(10, 0), sticky="nsew")
        fig2, ax2 = plt.subplots(figsize=(8, 7), dpi=105, facecolor='white')
        ax2.bar(top_wicket_venues['venue'], top_wicket_venues['Avg Wickets'], color='#4338ca')
        self.apply_modern_plot_style(ax2, "Wicket-Friendly Grounds (Avg Wickets/Match)")
        plt.setp(ax2.get_xticklabels(), rotation=35, horizontalalignment='right', fontsize=9)
        fig2.subplots_adjust(bottom=0.30) # Critical for rotated labels
        FigureCanvasTkAgg(fig2, c2).get_tk_widget().pack(fill="both", expand=True)

        ins = [
            f"Stadiums like {top_venues['venue'].iloc[0]} are very easy for batsmen to score a lot of runs.",
            f"Other grounds like {top_wicket_venues['venue'].iloc[0]} are better for bowlers because more wickets fall there.",
            "Ground size and the pitch make a big difference in how many runs are scored in a match."
        ]
        tk.Button(self.header_frame, text="✨ Show Insights", font=("Segoe UI", 10, "bold"), bg=COLOR_SUCCESS, fg="white", 
                  command=lambda: self.show_insights_popup("Venue Insights", ins), padx=20, pady=5).pack(side="right", padx=40)


if __name__ == "__main__":
    root = tk.Tk()
    app = IPLDashboardApp(root)
    root.mainloop()
