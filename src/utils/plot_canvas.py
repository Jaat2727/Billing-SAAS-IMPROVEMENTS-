# src/utils/plot_canvas.py
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.pyplot as plt

class PlotCanvas(FigureCanvas):
    def __init__(self, parent=None, width=5, height=4, dpi=100):
        fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = fig.add_subplot(111)
        super().__init__(fig)
        self.setParent(parent)

    def plot_bar(self, x, y, title, xlabel, ylabel):
        from src.utils.theme import DARK_THEME
        self.axes.cla()
        fig = self.figure
        fig.patch.set_facecolor(DARK_THEME['bg_surface'])
        self.axes.set_facecolor(DARK_THEME['bg_surface'])
        bars = self.axes.bar(x, y, color=DARK_THEME['accent_primary'])
        self.axes.set_title(title, color=DARK_THEME['text_primary'])
        self.axes.set_xlabel(xlabel, color=DARK_THEME['text_secondary'])
        self.axes.set_ylabel(ylabel, color=DARK_THEME['text_secondary'])
        self.axes.tick_params(axis='x', colors=DARK_THEME['text_secondary'])
        self.axes.tick_params(axis='y', colors=DARK_THEME['text_secondary'])
        for spine in self.axes.spines.values():
            spine.set_color(DARK_THEME['border_main'])
        self.draw()

    def plot_pie(self, sizes, labels, title):
        from src.utils.theme import DARK_THEME
        self.axes.cla()
        fig = self.figure
        fig.patch.set_facecolor(DARK_THEME['bg_surface'])
        self.axes.set_facecolor(DARK_THEME['bg_surface'])
        colors = [DARK_THEME['accent_primary'], DARK_THEME['accent_danger']]
        wedges, texts, autotexts = self.axes.pie(
            sizes, labels=labels, autopct='%1.1f%%', startangle=90, colors=colors,
            textprops={'color': DARK_THEME['text_primary'], 'fontsize': 12}
        )
        self.axes.axis('equal')
        self.axes.set_title(title, color=DARK_THEME['text_primary'])
        for text in texts:
            text.set_color(DARK_THEME['text_secondary'])
        for spine in self.axes.spines.values():
            spine.set_color(DARK_THEME['border_main'])
        self.draw()
