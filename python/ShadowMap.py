import numpy
import hardSettings
from Canvas import *
from OpenGL.GL import *
from OpenGL.GLU import *
import glew_wrap as glew
from CgUtil import CgUtil
from trackball import glTrackball

def validView(p):
    if not (hardSettings.doubleSM): return True
    if (p[0]>0): return True
    elif (p[0]<0): return False
    if (p[1]>0): return True
    elif (p[1]<0): return False
    if (p[2]<0): return True
    return False


def cross(x, y):
    return numpy.array([x[1]*y[2]-x[2]*y[1], x[2]*y[0]-x[0]*y[2], x[0]*y[1]-x[1]*y[0]])

#private to module
def setMatrices(L, screensize, screensizeHard, sx, shadowmap):
    # orthonormal basis

    az = L*1
    ax = cross(az, numpy.array([1,0,0], numpy.float32))
    if numpy.dot(ax,ax) < 0.1: ax = cross(az, numpy.array([0,1,0], numpy.float32))
    ax /= numpy.linalg.norm(ax)
    ay = cross(az, ax)
    ay /= numpy.linalg.norm(ay)

    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()

    nearPlane = 1.0
    farPlane = 201
    glOrtho(-1,+1,-1,+1, nearPlane, farPlane)

    glMatrixMode(GL_MODELVIEW)

    # PREPARE MATRIX for shadow test...

    glPushMatrix()
    glLoadIdentity()
    glOrtho(-1,+1,-1,+1, nearPlane, farPlane)

    gluLookAt(0,0,-4,   0,0,0,   0,1,0)
    gluLookAt( az[0],az[1],az[2],  0,0,0, ay[0], ay[1], ay[2] )
  
    r=shadowmap.mol.r
    px=shadowmap.mol.pos[0]
    py=shadowmap.mol.pos[1]
    pz=shadowmap.mol.pos[2]
    orien = shadowmap.mol.orien
    glScalef(1/r,1/r,1/r)
    glMultMatrixd((glTrackball.quat * orien).asRotation())
    glTranslatef(-px,-py,-pz)
    global matSM
    matSM = glGetFloatv(GL_MODELVIEW_MATRIX)

    # ...done!

    glLoadIdentity()
    gluLookAt(0,0,-4,   0,0,0,   0,1,0)
    gluLookAt( az[0],az[1],az[2],  0,0,0, ay[0], ay[1], ay[2] )

    global lastviewport
    lastviewport[:] = glGetIntegerv(GL_VIEWPORT)

    if (sx):
        glViewport(0,0,screensize,screensize)
        glEnable(GL_SCISSOR_TEST)
        glScissor(0,0,screensize,screensize)
    else:
        glViewport(screensize,0,screensize,screensize)
        glEnable(GL_SCISSOR_TEST)
        glScissor(screensize,0,screensize,screensize)

def restoreMatrices():
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)
    glPopMatrix()
    glViewport(lastviewport[0],lastviewport[1],lastviewport[2],lastviewport[3])

lastviewport = numpy.zeros(4, numpy.int) 
matSM = numpy.zeros((4,4), numpy.float32) # matrix used during shadowmmap drawing
matFinal = numpy.zeros((4,4), numpy.float32) # matrix for FP computation  = matSM x (MV)^(-1)

use_accurate_halo = True
lastL = numpy.zeros(3)

class ShadowMap:
    def __init__(self, mol):
        self.mol = mol
        self.shadowSettings = CgUtil()
        self.shadowSettingsAcc = CgUtil()

    def computeAsTexture(self, L, makeboth, canvas):
        global lastL
        #if not numpy.all(lastL == L): # XXX this changes because the light no longer moves with the trackball
        if True:
            canvas.SetAsOutput()
            setMatrices(L, canvas.GetSoftRes(), canvas.GetHardRes(), True, self)
            glClearDepth(1)
            glClear(GL_DEPTH_BUFFER_BIT)
            glDisable(GL_SCISSOR_TEST)
            glDepthFunc(GL_LESS)
            self.mol.DrawShadowmap(False, self.shadowSettings)
            restoreMatrices()

            if (hardSettings.doubleSM and makeboth):
                setMatrices(L, canvas.GetSoftRes(), canvas.GetHardRes(), False, self)
                glClearDepth(-10000)
                glClear(GL_DEPTH_BUFFER_BIT)
                glDepthFunc(GL_GREATER)
                glDisable(GL_SCISSOR_TEST)
                self.mol.DrawShadowmap(False, self.shadowSettings)
                restoreMatrices()
            
            glClearDepth(1)
            glDepthFunc(GL_LESS)
            mainCanvas.SetAsOutput()
            lastL = L

        glew.glActiveTextureARB(glew.GL_TEXTURE1_ARB)
        canvas.SetAsTexture()

    def init(self, winx):
        self.shadowSettings.SetForShadowMap(False)
        self.shadowSettingsAcc.SetForShadowMap(True)
        mainCanvas.RedirectToVideo()
        mainCanvas.SetVideoSize(winx)
        # test shadow and shadowAO canvases
        shadowmapCanvas.SetRes(hardSettings.SHADOWMAP_SIZE)
        shadowmapCanvas.ratio2x1 = (hardSettings.doubleSM==1)
        if not shadowmapCanvas.Test(): return False
        shadowAOCanvas.SetRes(hardSettings.AOSM_SIZE)
        shadowAOCanvas.ratio2x1=(hardSettings.doubleSM==1)
        if not shadowAOCanvas.Test(): return False
        mainCanvas.SetAsOutput()
        return True

    def initHalo(self):
        # test halo canvases
        haloCanvas.SetSameRes(mainCanvas)
        if not haloCanvas.Test(): return False
        mainCanvas.SetAsOutput()
        return True

    def prepareDepthTextureForCurrentViewpoint(self):
        haloCanvas.SetSameRes(mainCanvas)
        haloCanvas.SetAsOutput()
        if (use_accurate_halo): self.shadowSettingsAcc.BindShaders()
        else: self.shadowSettings.BindShaders()

        glClear(GL_DEPTH_BUFFER_BIT)
        self.mol.Draw()
        mainCanvas.SetAsOutput()
        glew.glActiveTextureARB(glew.GL_TEXTURE1_ARB)
        haloCanvas.SetAsTexture()
        glEnable(GL_TEXTURE_2D)

def Update():
    global lastL
    lastL *= 0

# static functions
def validView(p):
    if not hardSettings.doubleSM: return True
    if (p[0]>0): return True
    if (p[0]<0): return False
    if (p[1]<0): return True
    if (p[1]>0): return False
    if (p[2]<0): return True
    return False
    

def GetCurrentPVMatrix():
    matP = glGetFloatv(GL_PROJECTION_MATRIX)
    matMV = glGetFloatv(GL_MODELVIEW_MATRIX)

    A= matSM.T
    B = matMV.T
    C = matP.T
    
    P = numpy.dot(C, B)
    P = numpy.linalg.inv(P)
    res = numpy.dot(A, P)

    vp = glGetIntegerv(GL_VIEWPORT)
    mul = numpy.identity(4) * numpy.array([2.0/vp[2], 2.0/vp[3], 2, 1])
    add = numpy.identity(4)
    add[:,-1] += numpy.array([-1,-1,-1,0])

    matFinal[:] = numpy.dot(res,numpy.dot(add,mul)).T

def FeedParameters():
    for i in range(3):
        glew.glProgramEnvParameter4fARB(glew.GL_FRAGMENT_PROGRAM_ARB, i+3, 
                matFinal[0][i],matFinal[1][i],matFinal[2][i],matFinal[3][i])

class AOgpu2:
    aogpu_settings = CgUtil()
    #aogpustick_settings = CgUtil()
    def __init__(self, dir, mol, ndir, shadowmap):

        shadowmap.computeAsTexture(dir, True, shadowAOCanvas)
        glFinish()
        moltextureCanvas.SetAsOutput()
        glDisable(glew.GL_VERTEX_PROGRAM_ARB)
        glEnable(glew.GL_FRAGMENT_PROGRAM_ARB)
        AOgpu2.aogpu_settings.BindDrawAOShader()
        for i in range(3):
            glew.glProgramEnvParameter4fARB(glew.GL_FRAGMENT_PROGRAM_ARB, i,
                    matSM[0][i],matSM[1][i],matSM[2][i],matSM[3][i])
        
        glew.glProgramEnvParameter4fARB(glew.GL_FRAGMENT_PROGRAM_ARB, 3, dir[0],dir[1],dir[2], 4.0/ndir )
        #glew.glProgramEnvParameter4fARB(glew.GL_FRAGMENT_PROGRAM_ARB, 4, 0,stick_radius,0,0)
        global lastviewport
        lastviewport[:] = mol.DrawOnTexture()
        glDisable(GL_BLEND)
        glEnable(glew.GL_VERTEX_PROGRAM_ARB)

    #static functions
    @staticmethod
    def init():
        if not moltextureCanvas.Test(): return False
        mainCanvas.SetAsOutput()
        return True
    @staticmethod
    def Reset(m):
        moltextureCanvas.SetAsOutput()
        glClearColor(0,0,0,1)
        glClear(GL_COLOR_BUFFER_BIT)
    @staticmethod
    def Bind():
        if not moltextureCanvas.SetAsOutput(): raise Exception("CAnt bind moltexture canvas")
    @staticmethod
    def UnBind():
        mainCanvas.SetAsOutput()

k = 0
def myrand():
    global k
    k += 1231543214
    return ((k%12421)/12421.0)

def GenUniform(vn):
    pp = OctaLevel()
    ll = 10
    while (numpy.power(4.0,ll)+2>vn): ll-=1

    pp.Init(ll)
    pp.v.shape = (pp.sz**2, 3)

    # XXX I don't know if the next bit is correct
    # Basically need to remove all non-unique 3D vectors
    # see http://www.devx.com/tips/Tip/13990
    dd = set([tuple(c) for c in pp.v])
    pp.v = numpy.array(list(dd))
    #pp.v = numpy.sort(numpy.array(list(dd)), axis=1) #sort(pp.v.begin(), pp.v.end())
    #newsize = unique(pp.v.begin(),pp.v.end())-pp.v.begin()
    #pp.v.resize((newsize, 3))
    Perturb(pp.v)
    return pp.v

def Perturb(NN):
    width = 0.25/numpy.sqrt(len(NN))
    vert = numpy.array([1,1,1])
    for vi in NN:
        pp = numpy.random.rand(3)
        pp = pp*2.0 - vert
        pp *= width
        vi += pp
        vi /= numpy.linalg.norm(vi)

class OctaLevel:
    def __init__(self):
        self.v = numpy.zeros((1,3))
        self.sz = 0

    def Init(self, lev):
        self.sz = int(numpy.power(2.0, lev+1)+1)
        self.v.resize((self.sz, self.sz, 3))
        if (lev==0):
            self.v[0,0]=numpy.array([ 0, 0,-1]); self.v[0,1]=numpy.array([ 0, 1, 0]);  self.v[0,2]=numpy.array([ 0, 0,-1]);
            self.v[1,0]=numpy.array([-1, 0, 0]); self.v[1,1]=numpy.array([ 0, 0, 1]);   self.v[1,2]=numpy.array([ 1, 0, 0]);
            self.v[2,0]=numpy.array([ 0, 0,-1]); self.v[2,1]=numpy.array([ 0,-1, 0]);   self.v[2,2]=numpy.array([ 0, 0,-1]);
        else:
            tmp = OctaLevel()
            tmp.Init(lev-1)

            for i in range(self.sz):
                for j in range(self.sz):
                    if ((i%2) == 0 and (j%2) == 0):
                        self.v[i,j] = tmp.v[i/2,j/2]
                    if ((i%2) != 0 and (j%2) == 0):
                        self.v[i,j] = (tmp.v[i/2+0,j/2]+tmp.v[i/2+1,j/2])/2.0
                    if ((i%2) == 0 and (j%2) != 0):
                        self.v[i,j] = (tmp.v[i/2,j/2+0]+tmp.v[i/2,j/2+1])/2.0
                    if ((i%2) != 0 and (j%2) != 0):
                        self.v[i,j]=(tmp.v[i/2+0,j/2+0]+tmp.v[i/2+0,j/2+1]+tmp.v[i/2+1,j/2+0]+tmp.v[i/2+1,j/2+1])/4.0
            tmp.v.shape = (tmp.sz**2, 3)
            #self.v.shape = (self.sz**2, 3)
            for r in self.v:
                for vi in r: vi /= numpy.linalg.norm(vi)
