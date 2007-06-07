from ctypes import *
from ctypes.util import find_library

from glew import *

# XXX Don't know if this will work on windows or linux
path = find_library('GLEW')
gl = cdll.LoadLibrary(path)

glewInit = gl.glewInit
_glGenProgramsARB = gl.glGenProgramsARB
_glGenProgramsARB.argtypes = [c_int, POINTER(c_ulong)]
glBindProgramARB = gl.glBindProgramARB
glBindProgramARB.argtypes = [c_int, c_ulong]
_glProgramStringARB = gl.glProgramStringARB
_glProgramStringARB.argtypes = [c_int, c_int, c_int, c_char_p]
_glCheckFramebufferStatusEXT = gl.glCheckFramebufferStatusEXT
_glCheckFramebufferStatusEXT.argtypes = [c_int]

glProgramEnvParameter4fARB = gl.glProgramEnvParameter4fARB
glProgramEnvParameter4fARB.argtypes = [c_int,c_int,c_float,c_float,c_float,c_float]

glCheckFramebufferStatusEXT = gl.glCheckFramebufferStatusEXT
glCheckFramebufferStatusEXT.argtypes = [c_int]

_glGenFramebuffersEXT = gl.glGenFramebuffersEXT
_glGenFramebuffersEXT.argtypes = [c_int, POINTER(c_ulong)]

_glGenRenderbuffersEXT = gl.glGenRenderbuffersEXT
_glGenRenderbuffersEXT.argtypes= [c_int, POINTER(c_ulong)]

_glGenTextures = gl.glGenTextures
_glGenTextures.argtypes = [c_int, POINTER(c_ulong)]

glBindFramebufferEXT = gl.glBindFramebufferEXT
glBindFramebufferEXT.argtypes = [c_int, c_ulong]

glBindRenderbufferEXT = gl.glBindRenderbufferEXT
glBindRenderbufferEXT.argtypes = [c_int, c_ulong]

glActiveTextureARB = gl.glActiveTextureARB
glActiveTextureARB.argtypes = [c_int]

glMultiTexCoord2fARB = gl.glMultiTexCoord2fARB
glMultiTexCoord2fARB.argtypes = [c_int, c_float, c_float]

glMultiTexCoord4fARB = gl.glMultiTexCoord4fARB
glMultiTexCoord4fARB.argtypes = [c_int, c_float, c_float, c_float, c_float]

glTexParameteri = gl.glTexParameteri
glTexParameteri.argtypes = [c_int, c_int, c_int]

glTexImage2D = gl.glTexImage2D
glTexImage2D.argtypes = [c_int]*9

glFramebufferTexture2DEXT = gl.glFramebufferTexture2DEXT
glFramebufferTexture2DEXT.argtypes = [c_int, c_int, c_int, c_ulong, c_int]

glRenderbufferStorageEXT = gl.glRenderbufferStorageEXT
glRenderbufferStorageEXT.argtypes = [c_int, c_int, c_int, c_int]

glFramebufferRenderbufferEXT = gl.glFramebufferRenderbufferEXT
glFramebufferRenderbufferEXT.argtypes = [c_int, c_int, c_int, c_ulong]

def glGenProgramsARB(i):
    id = c_ulong()
    _glGenProgramsARB(i, byref(id))
    return id.value

def glProgramStringARB(i1, i2, prog):
    _glProgramStringARB(i1,i2,len(prog),c_char_p(prog))

def glGenFramebuffersEXT(i):
    id = c_ulong()
    _glGenFramebuffersEXT(i, byref(id))
    return id.value

def glGenRenderbuffersEXT(i):
    id = c_ulong()
    _glGenRenderbuffersEXT(i, byref(id))
    return id.value

def glGenTextures(i):
    id = c_ulong()
    _glGenTextures(i, byref(id))
    return id.value

