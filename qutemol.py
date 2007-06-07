import os, sys
import numpy
import Image

from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import *
import Qutemol.glew_wrap as glew

from Qutemol.Molecule import Molecule, convert_color
from Qutemol.Canvas import *
from Qutemol.CgUtil import cgSettings
from Qutemol.ShadowMap import ShadowMap, AOgpu2
from Qutemol.trackball import glTrackball
from Qutemol.quaternion import quaternion

from Qutemol.presets import real, real2, direct, illustr, illustr2, illustr_motm, qutemol1, qutemol2, qutemol3, coolb, coold, borders_cool, sem, sem2, shape, illustr_new, illustrm

#from IPython.Shell import IPShellEmbed
#ipshell = IPShellEmbed()

ERRGL_OK = 0
ERRGL_NO_FS = 1
ERRGL_NO_VS = 2
ERRGL_NO_FBO_SHADOWMAP = 4
ERRGL_NO_FBO_HALO = 8
ERRGL_NO_FBO_AO = 16
ERRGL_NO_GLEW = 32

width = 512
height = 512
oldX, oldY = 0, 0
mustDoHQ = True

def saveSnapshot(res, mol, filename = "snapshot", hires = True):
    global draw_axes
    save_draw_axes = draw_axes
    draw_axes = False
    mainCanvas.RedirectToMemory()
    if hires: res *= 2
    mainCanvas.SetRes(res)
    if not mainCanvas.SetAsOutput(): raise Exception()
    
    drawFrame(mol)

    res = mainCanvas.GetHardRes()
    data = glReadPixels(0,0,res,res,GL_RGB,GL_UNSIGNED_BYTE)
    image = Image.fromstring("RGB", (data.shape[1], data.shape[0]), data[::-1].tostring())
    if hires: image = image.resize((res/2, res/2), Image.ANTIALIAS)
    image.save(filename+".png")
    mainCanvas.RedirectToVideo()
    mainCanvas.SetAsOutput()
    draw_axes = save_draw_axes

def initGL(shadowmap, cgSettings, winx):
    res = 0
    glClearDepth(1.0)
    glDepthFunc(GL_LESS)
    glEnable(GL_DEPTH_TEST)
    glEnable(GL_LIGHTING)
    glShadeModel(GL_SMOOTH)

    glEnable(GL_CLIP_PLANE0)

    glEnable(glew.GL_VERTEX_PROGRAM_ARB)
    glEnable(glew.GL_FRAGMENT_PROGRAM_ARB)

    err = glew.glewInit()
    if (err != glew.GLEW_OK):
        lasterr = glew.glewGetErrorString(err)
        res |= ERRGL_NO_GLEW

    # XXX override in glew_wrap.py
    #if not glew.GLEW_ARB_vertex_program: res |= ERRGL_NO_VS
    #if not glew.GLEW_ARB_fragment_program: res |= ERRGL_NO_FS

    if not shadowmap.init(winx): res |= ERRGL_NO_FBO_SHADOWMAP
    if not shadowmap.initHalo(): res |= ERRGL_NO_FBO_HALO
    if not AOgpu2.init(): res |= ERRGL_NO_FBO_AO
    cgSettings.UpdateShaders()

    if not res == ERRGL_OK:
        # Print error message
        errmsg = "Unrecoverable error: Problems initializing graphics\n"
        if (res & ERRGL_NO_GLEW): errmsg += " - cannot initialize GLEW\n"+lasterr+"\n"
        if (res & ERRGL_NO_FS): errmsg += " - no Programmable Fragment Shader found\n"
        if (res & ERRGL_NO_VS): errmsg += " - no Programmable Vertex Shader found\n"
        if (res & ERRGL_NO_FBO_SHADOWMAP): errmsg += " - cannot initialize FrameBufferObject for shadowmaps\n"
        if (res & ERRGL_NO_FBO_HALO): errmsg += " - cannot initialize FrameBufferObject for halos\n"
        if (res & ERRGL_NO_FBO_AO): errmsg += " - cannot initialize FrameBufferObject for A.O. computation\n"
        raise Exception(errmsg)

def setLightDir(d):
    f = (d[0], d[1], d[2], 0)
    glLightfv(GL_LIGHT0, GL_POSITION, f)

# This is not necessary any more - but I really have to figure out what I'm
# doing with the model-view matrices
#def getDirFromTrackball(mol):
#    # XXX this is complete wrong, but it shows that shadowing works
#    glPushMatrix()
#    gluLookAt(1,-3,-5,   0,0,0,   0,1,0)

#    #glMultMatrixd((-1*glTrackball.quat * mol.orien).asRotation())
#    d = glGetFloatv(GL_MODELVIEW_MATRIX)
#    glPopMatrix()
#    res = numpy.array([-d[2,0], -d[2,1], -d[2,2]])
#    res /= numpy.linalg.norm(res)
#    return res

def getGlLightPos():
    pos = glGetLightfv(GL_LIGHT0,GL_POSITION)
    x = glGetFloatv(GL_MODELVIEW_MATRIX)
    res = numpy.inner(x,pos.T)
    res /= numpy.linalg.norm(res)
    return -res[:3]


def setProjection(res):
    winx = winy = res
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    nearPlane = 0.01
    farPlane = 10000
    size = 1.2
    ratio = size*winx/winy
    if cgSettings.projmode == cgSettings.PERSPECTIVE:
        gluPerspective(60.0, ratio, nearPlane, farPlane)
    else:
        glOrtho(-winx/winy, winx/winy,-1,1,40-2,40+200)
    glViewport(0,0,winx,winy)
    glMatrixMode(GL_MODELVIEW)

def makeHiQualityScreen(quality, mol):
    # XXX This function does not currently work
    # For some reason when using mainCanvas as a texture everything is really dark
    # although if you look closely enough you can see the antialiased version
    curres = mainCanvas.GetSoftRes()
    mainCanvas.RedirectToMemory()
    # Render into a higher quality buffer,
    # resample into smaller main window
    mainCanvas.SetRes(curres*quality / 100)
    if not mainCanvas.SetAsOutput():
        # something's wrong - do a normal screen
        mainCanvas.RedirectToVideo()
        mainCanvas.SetAsOutput()
        drawFrame(mol)
        return

    HSratio = float(mainCanvas.GetSoftRes()) / mainCanvas.GetHardRes()
    drawFrame(mol)

    mainCanvas.RedirectToVideo()
    mainCanvas.SetAsOutput()
    glew.glActiveTextureARB(glew.GL_TEXTURE1_ARB)
    glDisable(GL_TEXTURE_2D)
    glew.glActiveTextureARB(glew.GL_TEXTURE0_ARB)
    mainCanvas.SetAsTexture()

    glDisable(glew.GL_FRAGMENT_PROGRAM_ARB)
    glDisable(glew.GL_VERTEX_PROGRAM_ARB)

    setProjection(mainCanvas.GetSoftRes())

    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()

    glEnable(GL_TEXTURE_2D)
    glDisable(GL_DEPTH_TEST)

    glColor3f(1.,1.,1.)

    z=-45.

    glBegin(GL_QUADS)
    glTexCoord2f(0,0); glVertex3f(-1,-1, z)
    glTexCoord2f(HSratio,0); glVertex3f(+1,-1, z)
    glTexCoord2f(HSratio,HSratio); glVertex3f(+1,+1, z)
    glTexCoord2f(0,HSratio); glVertex3f(-1,+1, z)
    glEnd()

    glEnable(glew.GL_FRAGMENT_PROGRAM_ARB)
    glEnable(glew.GL_VERTEX_PROGRAM_ARB)
    glEnable(GL_DEPTH_TEST)

def drawScene(mol):
    # XXX High quality screen version not working yet
    #if (mustDoHQ): makeHiQualityScreen(hardSettings.STILL_QUALITY, mol)
    #else: drawFrame(mol)
    drawFrame(mol)
    glutSwapBuffers()

def drawFrame(mol):
    cgSettings.MakeShaders()
    if (mol.DoingAO()):
        mol.PrepareAOstep(1, shadowmap)
        while not mol.DecentAO(): mol.PrepareAOstep(1, shadowmap)

    mainCanvas.SetAsOutput()
    if cgSettings.doingAlphaSnapshot:
        glClearColor( cgSettings.P_halo_col, cgSettings.P_halo_col, cgSettings.P_halo_col, 0.0)
    else:
        glClearColor( cgSettings.P_bg_color_R, cgSettings.P_bg_color_G, cgSettings.P_bg_color_B, 0.0)

    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()

    if cgSettings.P_sem_effect: lightDir = (0,0,1)
    #else: lightDir= getDirFromTrackball(mol) #(0,0.8,0.6)
    else: lightDir= (0.,0.8,0.6)
    #else: lightDir= (1,1,1)

    setLightDir(lightDir)

    gluLookAt(0,0,-40,   0,0,0,   0,1,0)
    #if (MovingLightMode): drawLightDir()
    glColor3f(1,1,1)
    setProjection(mainCanvas.GetSoftRes())

    if cgSettings.P_use_shadowmap():
        shadowmap.computeAsTexture(getGlLightPos() , cgSettings.do_use_doubleshadow(), shadowmapCanvas)
    cgSettings.BindShaders()
    glEnable(GL_TEXTURE_2D)
    glew.glActiveTextureARB(glew.GL_TEXTURE1_ARB)
    shadowmapCanvas.SetAsTexture()
    mol.Draw()

    glDisable(glew.GL_VERTEX_PROGRAM_ARB)
    glDisable(glew.GL_FRAGMENT_PROGRAM_ARB)
    glDisable(GL_BLEND)

    if (cgSettings.UseHalo() > 0):
        shadowmap.prepareDepthTextureForCurrentViewpoint()
        mol.DrawHalos()
    
    # Draw axes
    if draw_axes:
        px, py, pz = mol.pos
        r = mol.r
        orien = mol.orien
        glPushMatrix()
        glScalef(1./r,1./r,1./r)
        glMultMatrixd((glTrackball.quat * orien).asRotation())
        glTranslatef(-px, -py, -pz)
        glDisable(GL_LIGHTING)
        glBegin(GL_LINES)
        glColor3f(0.,0.,0.)
        glVertex3f(px, py, pz)
        glColor3f(0.,1.,0.)
        glVertex3f(px+r, py, pz)
        glColor3f(0.,0.,0.)
        glVertex3f(px, py, pz)
        glColor3f(1.,0.,0.)
        glVertex3f(px, py+r, pz)
        glColor3f(0.,0.,0.)
        glVertex3f(px, py, pz)
        glColor3f(0.,0.,1.)
        glVertex3f(px, py, pz+r)
        glEnd()
        glPopMatrix()

def onMouseButton(button, state, x, y):
    global oldX, oldY
    global isRotating, isZooming, isClipping
    global mustDoHQ
    oldX, oldY = x, y
    if (button == GLUT_LEFT_BUTTON):
        if (state == GLUT_DOWN):
            mustDoHQ = False
            isRotating = True
        elif (state == GLUT_UP):
            mol.orien = glTrackball.quat * mol.orien
            glTrackball.reset()
            mustDoHQ = True
            isRotating = not isRotating
            glutPostRedisplay()
    elif (button == GLUT_RIGHT_BUTTON):
        keys = glutGetModifiers()
        if (keys & GLUT_ACTIVE_SHIFT):
            if (state == GLUT_DOWN):
                isClipping = True
            elif (state == GLUT_UP):
                isClipping = not isClipping
        else:
            if (state == GLUT_DOWN):
                isZooming = True
            elif (state == GLUT_UP):
                isZooming = not isZooming

isRotating = False
isZooming = False
isClipping = False
def onMouseDrag(x, y):
    global clipplane, oldY, oldX
    if isRotating:
        glTrackball.update(oldX, oldY, x, y, width, height)
    elif isZooming:
        ydiff = y - oldY
        oldX, oldY = x, y
        mol.scaleFactor += -0.1*ydiff*mol.scaleFactor
        if mol.scaleFactor < 0.1: mol.scaleFactor = 0.1
    elif isClipping:
        ydiff = oldY - y
        oldX, oldY = x, y
        clipplane[1] = -1
        #clipplane[0] = -1
        clipplane += [0, 0, 0, 0.1*ydiff]
    glutPostRedisplay()

shaders = [direct, illustr_motm, real, real2, illustr, illustr_new, qutemol1, qutemol2, qutemol3, coolb, coold, borders_cool, sem, sem2, shape, illustrm]

def printHelp():
    print '''\
Welcomd to pyQutemol

Left mouse button to rotate the system
Right mousebutton to scale the system
Right mouse button + Shift key to move the clipping plane along y axis

Keyboard options:

q or Esc      - quit pyQutemol
h             - help
r             - run through trajectory
j             - jump to a certain step
n             - next step in trajectory (includes averaging)
p             - previous step in trajectory
+             - increase the number of frames averaged together (doesn't account for periodicity)
-             - decrease the number of frames averaged together (minimum of 1)
g             - next visualization
G             - previous visualization
k             - change color for selection (must be in hex format)
o             - redo ambient occlusion shading
a             - toggle axes
x, y, or z    - align viewpoint along respective axes
s             - save snapshot to shapshot.png in local directory
m             - make movie (requires ffmpeg) - edit makeMovie() to script the movie
c             - change primary selection
e             - change excluded selection (shown even with the clipping plane)

The selections only work if you have loaded a psf/dcd combination
'''

run_trj = False
draw_axes = True
def keyfunc_mol(mol, shadowmap):
    shader_i = [0]
    def keyfunc(k, x, y):
        global run_trj, draw_axes
        if k == "q" or ord(k) == 27: # Escape
            sys.exit(0)
        elif k == "h":
            printHelp()
        elif k == "i":
            ipshell()
        elif k == "n":
            mol.read_next_frame()
            glutPostRedisplay()
        elif k == "p":
            mol.read_previous_frame()
            glutPostRedisplay()
        elif k == "j":
            print "Current frame %d, Total frames %d, select frame:"%(mol.universe.dcd.ts.frame, mol.universe.dcd.numframes)
            selection = raw_input("> ")
            try:
                frameno = int(selection)
                mol.universe.dcd[frameno]
                glutPostRedisplay()
            except:
                print "Invalid frame"
        elif k == "+":
            mol.averaging += 1
        elif k == "-":
            mol.averaging -= 1
            if mol.averaging < 1: mol.averaging = 1
        elif k == "r":
            run_trj = not run_trj
        elif k == "v":
            mol.PrepareAOSingleView(shadowmap)
            glutPostRedisplay()
        elif k == "a":
            draw_axes = not draw_axes
            glutPostRedisplay()
        elif k == "s":
            saveSnapshot(mainCanvas.GetHardRes()*2, mol)
        elif k == "g":
            shader_i[0] += 1
            if shader_i[0] == len(shaders): shader_i[0] = 0
            shaders[shader_i[0]].set(cgSettings)
            cgSettings.UpdateShaders()
            glutPostRedisplay()
        elif k == "G":
            shader_i[0] -= 1
            if shader_i[0] == -1: shader_i[0] = len(shaders)-1
            shaders[shader_i[0]].set(cgSettings)
            cgSettings.UpdateShaders()
            glutPostRedisplay()
        elif k == "o":
            mol.ResetAO()
            glutPostRedisplay()
        elif k == "m":
            makeMovie(mol)
        elif k == "k":
            print "Make selection for color change:"
            selection = raw_input("> ")
            try:
                sel = mol.universe.selectAtoms(selection)
                idx = sel.indices()
                print "input color:"
                color = raw_input("> ")
                mol.colors[idx] = convert_color(int(color,0))
                glutPostRedisplay()
            except:
                print "Invalid selection"
        elif k == "e":
            print "Make selection for exclusion:"
            selection = raw_input("> ")
            try:
                sel = mol.universe.selectAtoms(selection)
                mol.excl = sel.indices()
                mol.ResetAO()
                glutPostRedisplay()
            except:
                print "Invalid selection"
        elif k == "c":
            print "Make new selection:"
            selection = raw_input("> ")
            try:
                mol.sel = mol.universe.selectAtoms(selection)
                mol.pos = mol.sel.centerOfGeometry()
                coor = mol.sel.coordinates()
                min, max = numpy.minimum.reduce(coor), numpy.maximum.reduce(coor)
                mol.r = 0.5*numpy.sqrt(numpy.sum(numpy.power(max-min-4,2)))
                mol.min, mol.max = min, max
                mol.idx = mol.sel.indices()
                mol.ResetAO()
                glutPostRedisplay()
            except:
                print "Invalid selection"
        elif k == "x":
            mol.orien *= 0
            v = numpy.sin(numpy.pi/4.)
            mol.orien = quaternion([-.5,-.5,0.5,0.5])
            glTrackball.reset()
            glutPostRedisplay()
        elif k == "y":
            mol.orien *= 0
            v = numpy.sin(numpy.pi/4.)
            mol.orien.array += [-v,-v,0,0]
            glTrackball.reset()
            glutPostRedisplay()
        elif k == "z":
            mol.orien *= 0
            mol.orien.array[2] = -1
            glTrackball.reset()
            glutPostRedisplay()
    return keyfunc

def makeMovie(mol):
    import tempfile
    import shutil
    path = tempfile.mkdtemp()
    path = "./movie"
    print "Making movie"
    try:
        # Start trajectory
        res = mainCanvas.GetHardRes()*2
        mol.universe.dcd.skip=200
        mol.universe.dcd._reset_dcd_read()
        numframes = len(mol.universe.dcd)
        i = 0

        # First do a cool trick with the clipping plane
        #mol.clipplane *= 0
        #mol.clipplane[1] = -1
        #bbox = mol.max-mol.min
        #clippositions = numpy.arange(1.1*mol.max[1], 1.1*mol.min[1], -0.5)
        #clippositions = numpy.concatenate((clippositions, clippositions[::-1]))
        #for clippos in clippositions:
        #    print "Saving frame %d of %d"%(i, len(clippositions))
        #    mol.clipplane[-1] = clippos
        #    mol.ResetAO()
        #    ts = mol.universe.dcd.read_next_timestep()
        #    saveSnapshot(res,mol,path+"/img%06d"%i, True)
        #    i += 1

        #md_range = range(0,200,10)
        #k = 0
        #for l, time in enumerate(md_range):
        #    ts = mol.universe.dcd[time]
        #    print "Saving frame %d of %d"%(ts.frame, numframes)
            #if l > (len(md_range) - len(clippositions)):
            #    # start moving clipplane back
            #    mol.clipplane[-1] = clippositions[::-1][k]
            #    k += 1
        #    saveSnapshot(res, mol, path+"/img%06d"%(ts.frame), True)
        #    i+=1

        j = 0
        for i in range(0,numframes, mol.universe.dcd.skip):
            mol.universe.dcd[i]
            print "Saving snapshot %d of %d (frame %d)"%(i+1, numframes, mol.universe.dcd.ts.frame)
            saveSnapshot(res, mol, path+"/img%06d"%(j))
            j += 1

        # Now generate movie
        #output = "test.mp4"
        #movie_cmd = "ffmpeg2 -r 10 -b 1800 -y -i %s/img%%06d.png %s"%(path,output)
        #os.system(movie_cmd)
        #shutil.rmtree(path)
    except:
        shutil.rmtree(path)
        raise

def idlefunc_mol(mol):
    def idlefunc():
        global run_trj
        if run_trj:
            mol.read_next_frame()
            glutPostRedisplay()
    return idlefunc

if __name__=="__main__":
    
    # Get around a bug in GLUT on OS X
    cwd = os.getcwd()
    glutInit(sys.argv)
    os.chdir(cwd)
    
    if len(sys.argv) != 4:
        print "Usage: %s [prefix] [is_trj] [is_coarsegrain]"%sys.argv[0]
        print "If viewing a trajectory, prefix should be the name of the psf/dcd combo without the extension"
        print "otherwise the name of the pdb file"
        sys.exit(0)

    prefix = sys.argv[1]
    istrj = sys.argv[2]
    iscoarse = sys.argv[3]

    istrj = (int(istrj) == 1)
    iscoarse = (int(iscoarse) == 1)

    glutInitDisplayMode(GLUT_DOUBLE |  GLUT_RGB | GLUT_DEPTH )
    glutInitWindowSize( width, height)
    glutCreateWindow( sys.argv[0])

    mol = Molecule(prefix, istrj, iscoarse)

    # Set the clipping plane
    global clipplane
    clipplane = mol.clipplane

    shadowmap = ShadowMap(mol)
    cgSettings.SetDefaults()
    direct.set(cgSettings)

    initGL(shadowmap, cgSettings, width)

    dispfunc = lambda: drawScene(mol)
    glutKeyboardFunc(keyfunc_mol(mol, shadowmap))
    glutDisplayFunc(dispfunc)
    glutMouseFunc(onMouseButton)
    glutMotionFunc(onMouseDrag)
    glutIdleFunc(idlefunc_mol(mol))
    glutMainLoop()
