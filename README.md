[![Black](https://github.com/niko86/preconsol-gui/actions/workflows/black.yml/badge.svg)](https://github.com/niko86/preconsol-gui/actions/workflows/black.yml)

## About

A simple GUI application to estimate preconsolidation pressure using the casagrande method from AGS4 data format files.

![Screenshot of app](/assets/media/screen_capture.png?raw=true "Screenshot of app")

The red scatter points represent draggable handles which allow interactive adjustment of the maximum curviture and straightest line points.

## Installation

Required libraries can be installed from the `requirements.txt` or `poetry.lock` files in this repo. The required python version for these files is `3.11`, this is the version I have installed and confirmed to work.

```python
pip install -r "requirements.txt"
```

If you use a different version of python installation of the libraries credited below individually should work, however, incompatible versions may be determined by `pip`. 

## Credits

* [NumPy](https://numpy.org) NumPy is the fundamental package for scientific computing in Python.
* [pandas](https://pandas.pydata.org) Pandas is a fast, powerful, flexible and easy to use open source data analysis and manipulation tool.
* [Matplotlib](https://matplotlib.org) Matplotlib is a comprehensive library for creating static, animated, and interactive visualizations in Python.
* [SciPy](https://scipy.org) Fundamental algorithms for scientific computing in Python.
* [kneed](https://github.com/arvkevi/kneed/) This repository is an attempt to implement the kneedle algorithm.
* [PySide6](https://wiki.qt.io/Qt_for_Python) The Qt for Python project aims to provide a complete port of the PySide module to Qt.
* [AGS Python Library](https://gitlab.com/ags-data-format-wg/ags-python-library) A library to read and write AGS files using Pandas DataFrames.