
import numpy
import random
from OpenGL.GL import *
import glew_wrap as glew
from Canvas import moltextureCanvas, haloCanvas
from OctaMap import octamap
from trackball import glTrackball
from quaternion import quaternion
from CgUtil import cgSettings
import hardSettings
import ShadowMap
from ShadowMap import AOgpu2
import struct
from MDAnalysis import *
import molGL

TOO_BIG = 0
TOO_SMALL = 1
SIZE_OK = 2

def getAtomRadius(atom, coarse_grain = False):
    E2R = {"F": 1.47, "CL": 1.89, "H": 1.10, "C":1.548, "N": 1.4, "O":1.348, "P":1.88, "S":1.808, "CA":1.948, "FE":1.948, "ZN": 1.148, "I": 1.748}
    rad = E2R.get(atom[:1], 0)
    if rad == 0: rad = E2R.get(atom[:2], 0)
    if rad == 0: 1.5
    if coarse_grain: rad = 2.35
    return rad

def getAtomColor(atom):
    E2C = {"H": 0xFFFFFF,
"HE": 0xFFC0CB,
"LI": 0xB22222,
"BE": 0xFF1493,
"B": 0x00FF00,
"C": 0x808080,
"N": 0x8F8FFF,
"O": 0xF00000,
"F": 0xDAA520,
"NE": 0xFF1493,
"NA": 0x0000FF,
"MG": 0x228B22,
"AL": 0x808090,
"SI": 0xDAA520,
"P": 0xFFA500,
"S": 0xFFC832,
"CL": 0x00FF00,
"AR": 0xFF1493,
"K": 0xFF1493,
"CA": 0x808090,
"SC": 0xFF1493,
"TI": 0x808090,
"V": 0xFF1493,
"CR": 0x808090,
"MN": 0x808090,
"FE": 0xFFA500,
"CO": 0xFF1493,
"NI": 0xA52A2A,
"CU": 0xA52A2A,
"ZN": 0xA52A2A}

    E2C_coarse = {"NC3": 0x00CC00 ,"PO4": 0x6600CC, "GL": 0xFFFF33, "W": 0x0000CC}
    E2C.update(E2C_coarse)
    color = E2C.get(atom, 0)
    if color == 0: color = E2C.get(atom[:2], 0)
    if color == 0: color = E2C.get(atom[:1], 0)
    color_int = [ord(val) for val in struct.unpack("cccc", struct.pack("i", color))]
    return numpy.array(color_int[1:])/255.

def convert_color(color):
    color_int = [ord(val) for val in struct.unpack("cccc", struct.pack("i", color))]
    return numpy.array(color_int[1:])/255.

# XXX This class isn't actually used, since everything is in numpy arrays and the drawing is done in C code
class Atom: 
    def __init__(self, atomid, name):
        self.id = atomid
        self.r = getAtomRadius(name)
        self.col = numpy.array(getAtomColor(name))/255.
    def Draw(self):
        r = self.r
        p = self.pos[self.id]
        col = self.col
        glColor3f(col[0],col[1],col[2])
        glTexCoord2f(self.tx/moltextureCanvas.GetHardRes(),self.ty/moltextureCanvas.GetHardRes())
        glNormal3f(1,1,r)
        glVertex3f(p[0],p[1],p[2])
        glNormal3f(-1,+1, r)
        glVertex3f(p[0],p[1],p[2])
        glNormal3f(-1,-1, r)
        glVertex3f(p[0],p[1],p[2])
        glNormal3f(+1,-1, r)
        glVertex3f(p[0],p[1],p[2])
    def FillTexture(self,texture, texsize):
        octamap.FillTexture(texture, texsize, self.tx, self.ty, self.col[0], self.col[1], self.col[2])
    def AssignNextTextPos(self, texsize):
        self.tx = lx
        self.ty = ly
        if (lx+octamap.TotTexSizeX()>texsize) or (ly+octamap.TotTexSizeY()>texsize): return False
        lx += octamap.TotTexSizeX()
        if (lx+octamap.TotTexSizeX()>texsize):
            ly+=octamap.TotTexSizeY()
            lx=0
        return True
    def DrawOnTexture(self, CSIZE, px, py, pz, r):
        glColor3f(ShadowMap.myrand(), ShadowMap.myrand(), ShadowMap.myrand())
        h = 0.0
        Xm = -1.0-1.0/CSIZE
        Xp = 1.0+1.0/CSIZE
        Ym=Xm
        Yp=Xp
        glew.glMultiTexCoord4fARB(glew.GL_TEXTURE1_ARB, px,py,pz,r)
        glTexCoord2f(Xm,Ym); glVertex2f(-h+self.tx,      -h+self.ty)
        glTexCoord2f(Xp,Ym); glVertex2f(-h+self.tx+CSIZE,-h+self.ty)
        glTexCoord2f(Xp,Yp); glVertex2f(-h+self.tx+CSIZE,-h+self.ty+CSIZE)
        glTexCoord2f(Xm,Yp); glVertex2f(-h+self.tx,      -h+self.ty+CSIZE)
    def DrawShadowmap(self):
        r = self.r
        px, py, pz = self.pos[self.id]
        #if ((!geoSettings.showHetatm)&&(hetatomFlag)): return
        glNormal3f(+1,+1, r)
        glVertex3f(px,py,pz)
        glNormal3f(-1,+1, r)
        glVertex3f(px,py,pz)
        glNormal3f(-1,-1, r)
        glVertex3f(px,py,pz)
        glNormal3f(+1,-1, r)
        glVertex3f(px,py,pz)
    def DrawHalo(self, r, px, py, pz):
        #r = self.r
        #px, py, pz = self.pos[self.id]
        #if ((!geoSettings.showHetatm)&&(hetatomFlag)) return
        s=cgSettings.P_halo_size * 2.5
        glew.glMultiTexCoord2fARB(glew.GL_TEXTURE1_ARB, r+s, (r+s)*(r+s) / (s*s+2*r*s))
        glTexCoord2f(+1,+1)
        glVertex3f(px,py,pz)
        glTexCoord2f(-1,+1)
        glVertex3f(px,py,pz)
        glTexCoord2f(-1,-1)
        glVertex3f(px,py,pz)
        glTexCoord2f(+1,-1)
        glVertex3f(px,py,pz)



class Molecule:
    def __init__(self,filename,istrj = True,coarse_grain=False):
        self.r = 0 # default scaling factor for system
        self.pos = numpy.zeros(3) # center of bounding box
        self.orien = quaternion([0,0,-1,0]) # orientation in space
        self.scaleFactor = 1
        self.idx = None
        self.DirV = []
        self.istrj = istrj
        self.coarse_grain = coarse_grain
        self.clipplane = numpy.array([0.,0.,0.,0,], numpy.float32)
        self.excl = numpy.array([], numpy.int32)
        if not istrj: self.load_pdb(filename)
        else: self.load_trj(filename)
    def load_pdb(self,filename):
        infile = file(filename)
        coords = []
        radii = []
        colors = []
        radii = []
        for i,line in enumerate(infile):
            if not (line[:4] == "ATOM" or line[:6] == "HETATM"): continue
            name = line[13:16]
            x, y, z = float(line[30:38]),float(line[38:46]),float(line[46:54])
            coords.append((x,y,z))
            radii.append(getAtomRadius(name, self.coarse_grain))
            colors.append(getAtomColor(name))
        self.numatoms = len(coords)
        self.atompos = numpy.array(coords, numpy.float32)
        self.colors = numpy.array(colors, numpy.float32)
        self.radii = numpy.array(radii, numpy.float32)

        # Calculate bounding box
        min = numpy.minimum.reduce(self.atompos)
        max = numpy.maximum.reduce(self.atompos)
        pos = (min+max)/2
        self.r = 0.5*numpy.sqrt(numpy.sum(numpy.power(max-min-4,2)))
        self.pos = pos
        self.min, self.max = min-pos, max-pos

        self.textureAssigned = False
        self.textures = numpy.ones((self.numatoms, 2), numpy.float32)
        self.ReassignTextureAutosize()
        self.ResetAO()
    def load_trj(self,prefix):
        universe = AtomGroup.Universe(prefix+".psf", prefix+".dcd")
        print "Finished loading psf"
        self.universe = universe

        #self.atompos = numpy.asarray(universe.dcd.ts._pos).T
        self.atompos = universe.dcd.ts._pos

        self.sel = universe
        self.idx = self.sel.atoms.indices()

        self.numatoms = universe.atoms.numberOfAtoms()
        print "Finished selection"

        radii = [getAtomRadius(a.name, self.coarse_grain) for a in universe.atoms]
        colors = [getAtomColor(a.name) for a in universe.atoms]
        self.colors = numpy.array(colors, numpy.float32)
        self.radii = numpy.array(radii, numpy.float32)

        # This is the old way for using Vertex arrays - it might still be faster if I can use indexes arrays
        # or vertex buffer objects
        # see glDrawElements so I don't have to duplicate everything by 4
        #verts = numpy.transpose(universe.dcd.ts._pos)
        #self.atompos = numpy.repeat(verts, 4, axis=0)
        # Set up vertex arrays
        #glVertexPointer(3, GL_FLOAT, 0, self.atompos)
        #glEnableClientState(GL_VERTEX_ARRAY)
        #glNormalPointer(GL_FLOAT, 0, self.normals)
        #glEnableClientState(GL_NORMAL_ARRAY)
        #glColorPointer(3,GL_FLOAT, 0, self.colors)
        #glEnableClientState(GL_COLOR_ARRAY)

        # Calculate bounding box
        min = numpy.minimum.reduce(self.atompos)
        max = numpy.maximum.reduce(self.atompos)
        pos = (min+max)/2
        self.r = 0.5*numpy.sqrt(numpy.sum(numpy.power(max-min-4,2)))
        self.pos = pos
        self.min, self.max = min-pos, max-pos

        # for drawing lines
        if hasattr(self.universe, "_bonds"):
            self.bonds = numpy.array(self.universe._bonds)

        self.textureAssigned = False
        self.textures = numpy.ones((self.numatoms, 2), numpy.float32)
        self.ReassignTextureAutosize()
        self.ResetAO()

        # this is for trajectory averaging
        self.new_ts = self.universe.dcd.ts._pos
        self.averaging = 1

    def read_next_frame(self):
        if self.istrj:
            currframe = self.universe.dcd.ts.frame
            if currframe == len(self.universe.dcd): currframe = 0
            ts = self.universe.dcd[currframe] # this looks weird, but currframe is 1-indexed

            if self.averaging > 1 and not ts.frame > len(self.universe.dcd)-self.averaging:
                self.new_ts *= 0
                self.new_ts += self.atompos
                for ts in self.universe.dcd[currframe+1:currframe+self.averaging]:
                    self.new_ts += self.atompos
                ts.frame = currframe+1
                self.atompos[:] = self.new_ts/self.averaging

    def read_previous_frame(self):
        if self.istrj:
            currframe = self.universe.dcd.ts.frame-1
            self.universe.dcd[currframe-1]

    def ReassignTextureAutosize(self):
        if (self.textureAssigned): return

        guess = hardSettings.TSIZE
        lastThatWorked = guess
        enlarge = False; shrink = False; forced = False

        while True:
            if (enlarge and shrink): forced = True
            moltextureCanvas.SetRes(guess)
            lastThatWorked = guess
            res = SetCsize(guess, self.numatoms)
            if not forced:
                if ((res==TOO_BIG) and (guess/2 >= 16)):
                    shrink = True
                    guess /= 2
                    continue
                if ((res == TOO_SMALL) and (guess*2 <= hardSettings.MAX_TSIZE)):
                    enlarge = True
                    guess *= 2
                    continue
            octamap.SetSize(hardSettings.CSIZE)
            self.ReassignTexture(guess)
            break

        # Rebuild texture arrays
        #glTexCoordPointer(2, GL_FLOAT, 0, self.textures)
        #glEnableClientState(GL_TEXTURE_COORD_ARRAY)

    def ReassignTexture(self, texsize):
        lx = ly = 0
        # assign texture positions
        textures = []
        for i in range(self.numatoms):
            textures.append((lx, ly))
            if (lx+octamap.TotTexSizeX()>texsize) or (ly+octamap.TotTexSizeY()>texsize): raise Exception
            lx += octamap.TotTexSizeX()
            if (lx+octamap.TotTexSizeX()>texsize):
                ly+=octamap.TotTexSizeY()
                lx=0
        self.textures = numpy.array(textures, numpy.float32)

    def DrawLines(self):
        r = self.r * self.scaleFactor
        px, py, pz = self.pos
        glPushMatrix()
        glScalef(1./r,1./r,1./r)
        glMultMatrixd((glTrackball.quat * self.orien).asRotation())
        glTranslatef(-px, -py, -pz)

        glDisable(glew.GL_VERTEX_PROGRAM_ARB)
        glDisable(glew.GL_FRAGMENT_PROGRAM_ARB)
        
        glBegin(GL_LINES)
        molGL.molDrawSticks(self.atompos, self.bonds, self.colors, self.clipplane)
        glEnd()

        glPopMatrix()

    def Draw(self):
        r = self.r * self.scaleFactor
        px, py, pz = self.pos
        glPushMatrix()
        glScalef(1./r,1./r,1./r)
        glMultMatrixd((glTrackball.quat * self.orien).asRotation())
        glTranslatef(-px, -py, -pz)
        #glClipPlane(GL_CLIP_PLANE0, self.clipplane)

        x = glGetFloatv(GL_MODELVIEW_MATRIX)
        scalef = extractCurrentScaleFactor_x(x)
        glew.glProgramEnvParameter4fARB(glew.GL_VERTEX_PROGRAM_ARB,0,scalef,0,0,0)

        glEnable(glew.GL_VERTEX_PROGRAM_ARB)
        glEnable(glew.GL_TEXTURE_2D)

        glew.glActiveTextureARB(glew.GL_TEXTURE0_ARB)
        moltextureCanvas.SetAsTexture()

        if cgSettings.P_shadowstrenght>0:
            ShadowMap.GetCurrentPVMatrix()
            ShadowMap.FeedParameters()

        for i in range(3):
            glew.glProgramEnvParameter4fARB(glew.GL_FRAGMENT_PROGRAM_ARB, i, 
                    x[i][0],x[i][1],x[i][2],0)
        glew.glProgramEnvParameter4fARB(glew.GL_FRAGMENT_PROGRAM_ARB, 6,
            self.PredictAO(),0,0,0)

        glEnable(glew.GL_VERTEX_PROGRAM_ARB)
        glEnable(glew.GL_FRAGMENT_PROGRAM_ARB)

        glBegin(GL_QUADS)
        molGL.MolDraw(self.atompos, self.radii, self.textures/moltextureCanvas.GetHardRes(), self.colors, self.clipplane, self.excl, self.idx)
        glEnd()
        #glDrawArrays(GL_QUADS, 0, self.numatoms)

        glDisable(glew.GL_VERTEX_PROGRAM_ARB)
        glDisable(glew.GL_FRAGMENT_PROGRAM_ARB)

        # Draw wireframe for clipplane
        if not numpy.allclose(self.clipplane, 0):
            clipplane = self.clipplane
            glColor(0.5, 0.5, 0.5)
            glBegin(GL_LINE_STRIP)
            glVertex3f(px-r, clipplane[3], pz-r)
            glVertex3f(px-r, clipplane[3], pz+r)
            glVertex3f(px+r, clipplane[3], pz+r)
            glVertex3f(px+r, clipplane[3], pz-r)
            glVertex3f(px-r, clipplane[3], pz-r)
            glEnd()

        glPopMatrix()

    def DrawShadowmap(self,invert,shadowSettings):
        r = self.r * self.scaleFactor
        px, py, pz = self.pos
        glPushMatrix()
        glScalef(1./r,1./r, 1./r)
        glMultMatrixd((glTrackball.quat * self.orien).asRotation())
        glTranslate(-px, -py, -pz)
        #glClipPlane(GL_CLIP_PLANE0, self.clipplane)

        scalef=extractCurrentScaleFactor()
        glew.glProgramEnvParameter4fARB(glew.GL_VERTEX_PROGRAM_ARB, 0, scalef,0,0,0)

        glEnable(glew.GL_VERTEX_PROGRAM_ARB)
        glEnable(glew.GL_FRAGMENT_PROGRAM_ARB)

        glew.glActiveTextureARB(glew.GL_TEXTURE0_ARB)
        glDisable(GL_TEXTURE_2D)
        glew.glActiveTextureARB(glew.GL_TEXTURE1_ARB)
        glDisable(GL_TEXTURE_2D)

        shadowSettings.BindShaders()
        glBegin(GL_QUADS)
        molGL.MolDrawShadow(self.atompos, self.radii, self.clipplane, self.excl, self.idx)
        glEnd()

        #glDisableClientState(GL_COLOR_ARRAY)
        #glDisableClientState(GL_TEXTURE_COORD_ARRAY)
        #glDrawArrays(GL_QUADS, 0, self.numatoms)
        #glEnableClientState(GL_COLOR_ARRAY)
        #glEnableClientState(GL_TEXTURE_COORD_ARRAY)

        #if (sticks):
        #    pass

        glPopMatrix()

    def DrawHalos(self):
        # let's try to aviod THIS!
        # Moved to drawFrame()
        #shadowmap.prepareDepthTextureForCurrentViewpoint() # hum, unavoidable.

        r = self.r * self.scaleFactor
        px, py, pz = self.pos
        glPushMatrix()
        glScalef(1/r,1/r,1/r)
        glMultMatrixd((glTrackball.quat * self.orien).asRotation())
        glTranslatef(-px,-py,-pz)
        #glClipPlane(GL_CLIP_PLANE0, self.clipplane)

        x = glGetFloatv(GL_MODELVIEW_MATRIX)
        scalef = extractCurrentScaleFactor_x(x)
        glew.glProgramEnvParameter4fARB(glew.GL_VERTEX_PROGRAM_ARB, 0,scalef, 0,0,0)

        glEnable(glew.GL_VERTEX_PROGRAM_ARB)
        glEnable(glew.GL_FRAGMENT_PROGRAM_ARB)

        glDepthMask(False)
        glEnable(GL_BLEND)

        if (cgSettings.doingAlphaSnapshot): glBlendFunc(GL_ONE, GL_ONE_MINUS_SRC_ALPHA)
        else: glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

        cgSettings.BindHaloShader( haloCanvas.getResPow2() )

        glew.glProgramEnvParameter4fARB(glew.GL_FRAGMENT_PROGRAM_ARB, 0,
          (100.0+cgSettings.P_halo_aware*1300.0)/scalef/r, 0,0,0)

        glBegin(GL_QUADS)
        molGL.MolDrawHalo(self.atompos, self.radii, cgSettings.P_halo_size, self.clipplane, self.excl, self.idx)
        glEnd()

        glDisable(GL_BLEND)
        cgSettings.BindShaders()

        glDepthMask(True)

        glPopMatrix()
        glDisable(glew.GL_VERTEX_PROGRAM_ARB)
        glDisable(glew.GL_FRAGMENT_PROGRAM_ARB)

    def DrawOnTexture(self):
        glEnable(GL_BLEND)
        glBlendFunc(GL_ONE,GL_ONE)
        glMatrixMode(GL_PROJECTION)
        glPushMatrix()
        glLoadIdentity()
        glOrtho(0,moltextureCanvas.GetSoftRes(),0,moltextureCanvas.GetSoftRes(), 0,1)

        glMatrixMode(GL_MODELVIEW)
        glPushMatrix()
        glLoadIdentity()

        lastviewport = glGetIntegerv(GL_VIEWPORT)
        glViewport(0,0,moltextureCanvas.GetSoftRes(),moltextureCanvas.GetSoftRes())

        glew.glActiveTextureARB(glew.GL_TEXTURE1_ARB)
        glDisable(GL_TEXTURE_2D)
        glew.glActiveTextureARB(glew.GL_TEXTURE0_ARB)
        glDisable(GL_TEXTURE_2D)

        glBegin(GL_QUADS)
        molGL.MolDrawOnTexture(self.atompos, self.radii, self.textures, hardSettings.CSIZE, self.idx)
        glEnd()

        #if (self.sticks):
        #    pass

        glMatrixMode(GL_PROJECTION)
        glPopMatrix()
        glMatrixMode(GL_MODELVIEW)
        glPopMatrix()
        glViewport(lastviewport[0],lastviewport[1],lastviewport[2],lastviewport[3])
        return lastviewport

    def PrepareAOstep(self, nsteps, shadowmap):
        if not self.DoingAO(): return True
        if not self.AOstarted: self.PrepareAOstart()
        AOgpu2.Bind()
        if ShadowMap.validView(self.DirV[self.AOdoneLvl]): ao = AOgpu2(self.DirV[self.AOdoneLvl], self, len(self.DirV), shadowmap)
        AOgpu2.UnBind()
        self.AOdoneLvl += 1
        return (self.AOdoneLvl >= len(self.DirV))

    # for testing
    def PrepareAOSingleView(self, shadowmap, static_i=[0]):
        self.PrepareAOstart()
        AOgpu2.Bind()
        ao = AOgpu2(self.DirV[static_i[0]], self, 4, shadowmap)
        static_i[0] += 1
        if (static_i[0] > len(self.DirV)): static_i[0] = 0
        AOgpu2.UnBind()
        self.AOdoneLvl = len(self.DirV)

    def PrepareAOstart(self):
        self.AOdoneLvl = 0
        AOgpu2.Reset(self)
        self.AOstarted = True
        if (len(self.DirV) == 0):
            # generate probe views
            self.DirV = ShadowMap.GenUniform(hardSettings.N_VIEW_DIR)
            # mix them up
            numpy.random.shuffle(self.DirV)

    def ResetAO(self):
        self.AOready = False
        self.AOstarted = False
        self.AOdoneLvl = 0
        #self.DirV = []

    def DoingAO(self):
        if (cgSettings.P_texture == 0): return False
        if (len(self.DirV) == 0): return True
        return self.AOdoneLvl < len(self.DirV)

    def DecentAO(self):
        k = 1.
        if (self.AOdoneLvl>=len(self.DirV)): return True
        else: return False # XXX
        if (self.numatoms<10): return (self.AOdoneLvl>6*k)
        if (self.numatoms<100): return (self.AOdoneLvl>4*k)
        if (self.numatoms<1000): return (self.AOdoneLvl>2*k)
        if (self.numatoms<10000): return (self.AOdoneLvl>1*k)
        return True

    def PredictAO(self):
        # multiplicative prediction
        if self.AOstarted == False: return 1.0
        else:
            coeff = 0.25+(self.AOdoneLvl-1)/20.
            if (coeff > 1.0): coeff = 1.0
            return coeff*len(self.DirV)*1.0/self.AOdoneLvl

def extractCurrentScaleFactor():
    x = glGetFloatv(GL_MODELVIEW_MATRIX)
    scalef=numpy.power(numpy.abs(numpy.linalg.det(x)),1./3.)
    return scalef

def extractCurrentScaleFactor_x(x):
    return numpy.power(numpy.abs(numpy.linalg.det(x)),1./3.)

def SetCsize(textsize, natoms):
    # initial guess
    i = numpy.ceil(numpy.sqrt(natoms))
    hardSettings.CSIZE = textsize / int(i)
    if (hardSettings.CSIZE > 250):
        hardSettings.CSIZE = 250
        return TOO_BIG
    if (hardSettings.CSIZE < 6):
        hardSettings.CSIZE = 6
        return TOO_SMALL
    return SIZE_OK

