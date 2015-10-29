===========
 pyQuteMol
===========

A Python port of C++ QuteMol_

:Author: Naveen Michaud-Agrawal
:Year:   2007
:License: GPL v2

------------------------------------------------------------

.. Warning:: Code is broken but might be useful as a starting point
             for new projects. Use the `Issue Tracker`_ to start a 
             discussion or fork and send pull requests or make it 
             your own!

------------------------------------------------------------


Naveen wrote the code some time in 2007 and it is made public with his
permission. He says:

  pyQuteMol was a direct port of the C++ Qutemol
  (http://qutemol.sourceforge.net/), so I guess it falls under the
  same license (GPL)? Most of the interesting work is done in the
  shader code which was copied verbatim from Qutemol (my only
  improvement was using numpy arrays to populate the opengl buffers so
  I could hook it into MDAnalysis_ to animate trajectories). The code
  should be workable if somebody is familiar with OpenGL (particularly
  the new programmable pipeline) and how to set it up in python (I
  think I had a port to pyglet at one point since that supported
  vertex and fragment shaders). Feel free to use/abuse as you see fit
  (I guess within the constraints of the GPL :)


Installing
==========

.. Note:: Installation is broken. The description here outlines how
          it *should* have worked.

Try ::

  python setup.py build

Compiling on Mac OS X 10.6.5 with MacPorts failed because ``glewpy``
appears to be broken and ``glewpy`` is not maintained anymore
(`Macports Ticket 18066`_). Perhaps it needs to be rewritten with
PyOpenGL?

 
.. _QuteMol:  http://qutemol.sourceforge.net/
.. _Issue Tracker: https://github.com/MDAnalysis/pyQuteMol/issues
.. _MDAnalysis: http://www.mdanalysis.org
.. _Macports Ticket 18066:
   https://trac.macports.org/ticket/18066

Usage
=====

Usage::

  qutemol.py PREFIX IS_TRJ IS_COARSEGRAIN

* *PREFIX*: Looks for ``PREFIX.pdb`` or ``PREFIX.psf PREFIX.dcd``.
* *IS_TRJ*: 0: look for pdb; 1: look for psf/dcd combo
* *IS_COARSEGRAIN*: 0: atomistic; 1: hacks for coarse grained structures
