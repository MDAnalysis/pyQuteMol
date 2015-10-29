"""
Script for building the example.

Usage:
    python setup.py build --build-lib=./
"""
from distutils.core import setup, Extension
#from Pyrex.Distutils import build_ext
import numpy

extensions = [
    Extension("molGL", ["src/molGL.c"], #["src/molGL.pyx"],
              libraries = [],
              include_dirs = [numpy.get_include()],
              extra_link_args=["-framework","OpenGL"])
    ]

RELEASE = "0.0.1"

setup(
    name="pyQuteMol",
    author='Naveen Michaud-Agrawal',
    license='GPL 2',
    url='https://github.com/MDAnalysis/pyQuteMol',
    packages=['Qutemol', 'Qutemol.presets'],
    package_dir= {'Qutemol': 'python'},
    ext_package='Qutemol',
    ext_modules= extensions,
    #cmdclass = {'build_ext': build_ext}
)
