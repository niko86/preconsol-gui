from itertools import combinations

import matplotlib as mpl
import numpy as np
from kneed import KneeLocator
from matplotlib.backend_bases import MouseButton, FigureCanvasBase
from matplotlib.figure import Figure
from matplotlib.ticker import ScalarFormatter
from scipy.interpolate import UnivariateSpline


class Casagrande_PreConsolidation:

    LINSPACE_RANGE = 10_000
    PLOT_Y_PADDING = 0.2

    def __init__(self, figsize: tuple = (12, 8)) -> None:
        self._figure = Figure(figsize=figsize)
        self._ax = self._figure.subplots(1, 1)
        if mpl.rcParams['backend'] == 'QtAgg':
            from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
            self._canvas = FigureCanvas(self._figure)
    

    def _ascending_values(self, array:np.ndarray, return_index:bool = False) -> tuple:
        values = list()
        indices = list()
        for i, value in enumerate(array):
            if i == 0 or value > values[-1]:
                values.append(value)
                indices.append(True)
                continue
            indices.append(False)
        return np.array(values), np.array(indices) if return_index else np.array(values)



    def _bisector_function(self, xs) -> np.ndarray:
        return np.array((np.log10(xs) - self._knee_log10_x) * np.divide(self._spline_deriv(self._knee_log10_x), 2) + self._spline(self._knee_log10_x))


    def _calculate_preconsolidation(self, smoothing_degree: int = 2, smoothing_factor: float | None = 0) -> None:
        self._set_spline(smoothing_degree=smoothing_degree, smoothing_factor=smoothing_factor)
        a = self._bisector_function(self._after_knee_linspace) 
        b = self._straight_line_function(self._after_knee_linspace)
        for exponent in range(-8, 3): 
            solution = np.isclose(a, b, rtol=1*10**exponent) # Allows for ensuring a solution if found rather than using for example a fixed RTOL of 0.0001
            if len(self._after_knee_linspace[solution]) > 0:
                self._p = self._after_knee_linspace[solution][0]
                self._e = a[solution][0]
                break
        return


    def _click_handle(self, event) -> None:
        if event.artist is self._peak_curvature_handle:
            self._draggable_upper_limit = np.min(self._straightest_line_handles.get_offsets().T[0])
            self._draggable_lower_limit = self._asc_axial_loads[0]
            self._limit_span = self._ax.axvspan(self._draggable_upper_limit, np.max(self._ax.get_xlim()), color='red', alpha=0.5, lw=0, label='span')
        elif event.artist is self._straightest_line_handles:
            self._draggable_upper_limit = self._asc_axial_loads[-1]
            self._draggable_lower_limit = self._peak_curvature_handle.get_offsets()[0, 0]
            self._limit_span = self._ax.axvspan(np.min(self._ax.get_xlim()), self._draggable_lower_limit, color='red', alpha=0.5, lw=0, label='span')
        self._current_artist = event.artist
        self._current_index = event.ind[0]  # event index to help identify the collection?
        self._current_offsets = self._current_artist.get_offsets()
        self._follower = self._canvas.mpl_connect("motion_notify_event", self._follow_mouse)
        self._releaser = self._canvas.mpl_connect("button_release_event", self._release_onclick)
        return


    def _determine_peak_slope(self) -> None:
        self._straight_line_xs = None
        self._straight_line_ys = None
        self._straight_line_slope = None
        self._straight_line_intercept = None
        mask: np.ndarray = self._asc_axial_loads > self._knee_x 
        d = dict(zip(self._asc_axial_loads[mask], self._asc_void_ratios[mask]))
        for i in range(2, len(self._asc_axial_loads[mask])+1):
            for combin in combinations(self._asc_axial_loads[mask], i):
                temp_xs = np.fromiter(combin, dtype=float)
                temp_ys = np.fromiter((d[x] for x in temp_xs), dtype=float)
                m, c = self._determine_slope(temp_xs, temp_ys)
                if (self._straight_line_slope == None) or (np.abs(m) > np.abs(self._straight_line_slope)):
                    self._straight_line_xs = temp_xs
                    self._straight_line_ys = temp_ys
                    self._straight_line_slope = m
                    self._straight_line_intercept = c
        return


    def _determine_slope(self, xs: np.ndarray, ys: np.ndarray) -> np.ndarray:
        A = np.vstack([np.log10(xs), np.ones(len(xs))]).T
        return np.linalg.lstsq(A, ys, rcond=None)[0]


    def _find_nearest(self, array, value) -> np.ndarray:
        array = np.asarray(array)
        idx = (np.abs(array - value)).argmin()
        return array[idx]


    def _follow_mouse(self, event) -> None:
        if event.xdata is not None and (event.xdata > self._draggable_lower_limit and event.xdata < self._draggable_upper_limit):
            self._update_offset(event)
        return


    def _initial_draw_plot(self) -> None:
        self._ax.cla()
        self._x_limits = self._set_x_limits()
        self._ax.set_ylim(np.min(self._asc_void_ratios)*(1 - self.PLOT_Y_PADDING), np.max(self._asc_void_ratios)*(1 + self.PLOT_Y_PADDING))
        self._ax.set_ylabel('Voids Ratio')
        self._ax.set_xlim(self._x_limits)
        self._ax.set_xlabel('Axial Load  [kPa]')
        self._ax.set_xscale('log')
        self._ax.xaxis.set_major_formatter(ScalarFormatter())
        self._ax.xaxis.grid(visible=True, which='major', color='black', linestyle='-')
        self._ax.xaxis.grid(visible=True, which='minor', color='grey', linestyle='--')

        self._determine_peak_slope()
        self._calculate_preconsolidation()

        self._spline_curve, = self._ax.plot(self._full_range_linspace, self._spline(np.log10(self._full_range_linspace)), color='blue', label='spline_curve',)
        self._straightest_line, = self._ax.plot(
            [self._asc_axial_loads[0], self._asc_axial_loads[-1]], 
            [self._straight_line_function(self._asc_axial_loads[0]), self._straight_line_function(self._asc_axial_loads[-1])], 
            color='red', linestyle='--', label='straightest_line',
        )
        self._horizontal_line, = self._ax.plot(
            [self._knee_x, np.max(self._asc_axial_loads[-1])], 
            [self._knee_y,] * 2, 
            color="red", label='horizontal_line',
        ) 
        self._peak_curvature_line, = self._ax.plot(
            [self._asc_axial_loads[0], self._asc_axial_loads[-1]], 
            [self._peak_curve_function(self._asc_axial_loads[0]), self._peak_curve_function(self._asc_axial_loads[-1])], 
            color='red', label='peak_curvature_line',
        )
        self._bisector_line, = self._ax.plot(
            [self._knee_x, self._asc_axial_loads[-1]], 
            [self._bisector_function(self._knee_x), self._bisector_function(self._asc_axial_loads[-1])], 
            color='red', linestyle='--', label='bisector_line',
        )
        self._p_e_scatter = self._ax.scatter(
            self._asc_axial_loads, 
            self._asc_void_ratios, 
            color='blue',
        )
        self._straightest_line_handles = self._ax.scatter(
            self._straight_line_xs, 
            self._straight_line_ys, 
            color='red', zorder=2.5, picker=True,
        )
        self._peak_curvature_handle = self._ax.scatter(
            self._knee_x, 
            self._knee_y, 
            color='red', zorder=2.5, picker=True,
        )
        self._preconsolidation_point = self._ax.scatter(
            self._p, 
            self._e, 
            color='black', zorder=2.5,
        )
        self._preconsolidation_annotation = self._ax.annotate(
            f"Preconsolidation Pressure: {self._p:.0f}kPa", xy=(0.97, 0.95), xycoords="axes fraction", 
            va="center", ha="right", zorder=5,bbox=dict(boxstyle="square", fc="w", pad=0.6),
        )
        self._canvas.draw_idle()
        return


    def _peak_curve_function(self, xs) -> float:
        return (np.log10(xs) - self._knee_log10_x) * self._spline_deriv(self._knee_log10_x) + self._spline(self._knee_log10_x)


    def _recalculate_parameters(self, event) -> None:
        if self._current_artist is self._peak_curvature_handle:
            self._knee_x, self._knee_y = (event.xdata, self._spline(np.log10(event.xdata)))
            self._knee_log10_x = np.log10(self._knee_x)
        elif self._current_artist is self._straightest_line_handles:
            temp_xs, temp_ys = self._current_offsets.T
            self._straight_line_slope, self._straight_line_intercept = self._determine_slope(temp_xs, temp_ys)
            #self._peak_gradient = self._determine_peak_slope()
        self._update_preconsolidation_point()
        return

    
    def _release_onclick(self, event) -> None:
        if event.button == MouseButton.LEFT:
            self._canvas.mpl_disconnect(self._releaser)
            self._canvas.mpl_disconnect(self._follower)
            self._limit_span.remove()
            self._recalculate_parameters(event)
            self._update_offset(event)
            self._update_lines()
        return


    def _set_knee_point(self) -> None:
        kneed = KneeLocator(self._asc_axial_loads, self._asc_void_ratios, S=1.0, curve="concave", direction="decreasing")
        self._knee_x = kneed.knee
        self._knee_y = kneed.knee_y
        self._knee_log10_x = np.log10(self._knee_x)
        self._after_knee_linspace = np.linspace(self._knee_x, self._asc_axial_loads[-1], self.LINSPACE_RANGE)
        return


    def _set_spline(self, smoothing_degree: int, smoothing_factor: float | None) -> None: 
        self._spline = UnivariateSpline(np.log10(self._asc_axial_loads), self._asc_void_ratios, s=smoothing_factor, k=smoothing_degree)
        self._spline_deriv = self._spline.derivative()
        return


    def _set_x_limits(self) -> tuple[float, float]:
        return (10 ** np.floor(np.log10(self._asc_axial_loads[0])), 10 ** np.ceil(np.log10(self._asc_axial_loads[-1])))


    def _straight_line_function(self, xs) -> np.ndarray:
        return np.array(np.log10(xs) * self._straight_line_slope + self._straight_line_intercept)


    def _update_lines(self) -> None:
        self._spline_curve.set_data(
            self._full_range_linspace, 
            self._spline(np.log10(self._full_range_linspace)), 
        )
        self._straightest_line.set_data(
            [self._asc_axial_loads[0], self._asc_axial_loads[-1]], 
            [self._straight_line_function(self._asc_axial_loads[0]), self._straight_line_function(self._asc_axial_loads[-1])], 
        )
        self._horizontal_line.set_data(
            [self._knee_x, np.max(self._asc_axial_loads[-1])], 
            [self._knee_y,] * 2, 
        ) 
        self._peak_curvature_line.set_data(
            [self._asc_axial_loads[0], self._asc_axial_loads[-1]], 
            [self._peak_curve_function(self._asc_axial_loads[0]), self._peak_curve_function(self._asc_axial_loads[-1])],
        )
        self._bisector_line.set_data(
            [self._knee_x, self._asc_axial_loads[-1]], 
            [self._bisector_function(self._knee_x), self._bisector_function(self._asc_axial_loads[-1])], 
        )
        self._figure.canvas.draw_idle()
        return


    def _update_offset(self, event) -> None:
        self._current_offsets[self._current_index] = (event.xdata, self._spline(np.log10(event.xdata)))
        self._current_artist.set_offsets(self._current_offsets)
        self._ax.draw_artist(self._current_artist)
        self._canvas.blit(self._ax.bbox)
        self._canvas.draw_idle()
        return


    def _update_preconsolidation_point(self) -> None:
        self._calculate_preconsolidation()
        self._preconsolidation_annotation.set_text(f"Preconsolidation Pressure: {self._p:.0f}kPa")
        self._preconsolidation_point.set_offsets([self._p, self._e])
        self._ax.draw_artist(self._preconsolidation_point)
        self._canvas.blit(self._ax.bbox)
        self._canvas.draw_idle()
        return


    def get_canvas(self) -> FigureCanvasBase:
        return self._canvas


    def get_e(self) -> float:
        return self._e


    def get_p(self) -> float:
        return self._p


    def set_data(self, axial_loads_kpa: np.ndarray, void_ratios: np.ndarray) -> None:
        self._axial_loads_kpa = axial_loads_kpa
        self._void_ratios = void_ratios
        self._asc_axial_loads, mask = self._ascending_values(self._axial_loads_kpa, return_index=True)
        self._asc_void_ratios = self._void_ratios[mask]
        self._full_range_linspace = np.linspace(self._asc_axial_loads[0], self._asc_axial_loads[-1], self.LINSPACE_RANGE)
        self._set_knee_point()
        self._initial_draw_plot()


    def set_interactive(self) -> None:
        # TODO Need show to load up tk backend as built in to show? Also need to generate fig using pyplot if run as a script??
        self._canvas.mpl_connect("pick_event", self._click_handle)
        self._ax.fmt_xdata = lambda x: f"{x:.3f}"
        self._ax.fmt_ydata = lambda y: f"{y:.3f}"
        self._canvas.draw_idle()
        return
    

    def save_plot(self, filename:str) -> None:
        self._figure.savefig(f"{filename}.png", dpi='figure', format='png')
        return


if __name__ == '__main__':
    pass