import numpy

from OpenGL.GL import *
from OpenGL import GLU
import glew_wrap as glew
from Canvas import moltextureCanvas
import hardSettings

class CgUtil:
    MAXPOW = 15
    ORTHO = 1
    PERSPECTIVE = 2
    shaderHasChanged = False
    def __init__(self):
        self.P_light_base = 0. # from 0 (dark) to 1 (bright)
        self.P_lighting = 0.   # from 0 (no lighting) to 1 (full lighting)
        self.P_phong = 0.      # from 0 (no phong lighting) to 1 (full lighting)
        self.P_phong_size = 0. # from 0 (POW=100) to 1 (POW=1)

        self.P_col_atoms_sat = 0.  # base color: saturation
        self.P_col_atoms_bri = 0.  # base color: brightness

        self.P_texture = 0.    # FOR AO! from 0 (no AO) to 1 full AO
        self.P_border_inside = 0. # size of antialiased borders inside, in % of atom
        self.P_border_outside = 0. # borders outside (pure black), full size
        self.P_depth_full = 0. #size of depth step for a full border

        self.P_sem_effect = False

        self.P_halo_size = 0.
        self.P_halo_col = 0.
        self.P_halo_str = 0.
        self.P_halo_aware = 0.

        self.P_fog = 0.
        self.P_capping = False # capping
        self.P_shadowstrenght = 0. # how much light 

        self.P_bg_color_R = 0.
        self.P_bg_color_G = 0.
        self.P_bg_color_B = 0.

        self.P_double_shadows = False
        self.P_border_fixed = False
      
        # questi sono settati automaticamente
        self.gap = 0. # gap, % of border texels to be skipped
        self.writeAlpha = False # True during probe rendering only
        self.writeCol = False #write a color at all?
        self.cyl_radius = 0.

        self.doingAlphaSnapshot = False # lots of things change when doing an alpha snapshot

        # from CgUtil::CgUtil() private variables
        self.loaded = False
        self.idf = self.idv = 666
        self.auto_normalize = False
        self.norm = 1
        self.loadedVertexHalo = False
        self.ResetHalo()
        self.proj_figa = False
        self.idfStick = self.idvStick = 666
        self.loadedStick = False
        self.idvHalo = 666
        self.cyl_radius = 0.2
        self.shadowmapBuilding = False
        self.accurateShadowmapBuilding = False
        self.doingAlphaSnapshot = False
        self.shadersMade = False
        self.loadedHalo = numpy.zeros(CgUtil.MAXPOW, numpy.bool)
        self.idfHalo = numpy.zeros(CgUtil.MAXPOW, numpy.int)

    def do_use_doubleshadow(self):
        return (self.P_double_shadows and self.can_use_doubleshadow())
    def can_use_doubleshadow(self):
        return ((self.P_light_base==0.0) and hardSettings.doubleSM)
    def P_use_shadowmap(self):
        return self.P_shadowstrenght>0
    def _border_outside(self): return self.P_border_outside*0.075
    def _border_inside(self): return self.P_border_inside*0.5
    def UseHalo(self): return (self.P_halo_size**2 > 0.)

    def SetDefaults(self):    # set default params 
        self.P_light_base=0.0
        self.P_lighting=0.9
        self.P_phong=0.0
        self.P_phong_size=0.75

        self.P_col_atoms_sat=0.5
        self.P_col_atoms_bri=1.0

        self.P_texture=0.0
        self.P_border_inside=0.0

        self.P_border_outside=0.0
        self.P_depth_full=0.5

        self.P_sem_effect=False
        self.P_shadowstrenght=0.0
        self.P_double_shadows=True
        self.P_fog=0

        self.P_bg_color_R=self.P_bg_color_G=self.P_bg_color_B=0.5
        self.projmode=self.ORTHO

        self.writeAlpha=False
        self.writeCol=True
        self.gap =0.5

        self.P_capping=False

        self.P_halo_size=0.0
        self.P_halo_col =0.0
        self.P_halo_str =1.0
        self.P_halo_aware=0.5

    def SetForOffLine(self):  # set default params for an offscreen rendering
        self.P_light_base=0.0
        self.P_lighting=0.0
        self.P_phong=0.0

        self.P_col_atoms_sat=0.0
        self.P_col_atoms_bri=0.0
        self.P_lighting=0.0
        self.P_texture=1.0
        self.P_border_inside=0.0
        self.P_border_outside=0.0
        self.P_sem_effect=False
        self.P_shadowstrenght=0.0
        self.P_fog=0
        self.projmode=self.ORTHO

        self.writeAlpha=True
        self.writeCol=True

        self.P_capping=False

        self.gap =0.2

        self.P_halo_size=0.0

    def SetForShadowMap(self, accurate): # set default params for an offscreen rendering
        self.P_light_base=0.0
        self.P_lighting=0.0
        self.P_phong=0.0

        self.P_col_atoms_sat=0.0
        self.P_col_atoms_bri=0.0
        self.P_texture=0.0
        self.P_border_inside=0.0
        self.P_border_outside=0.0
        self.P_sem_effect=False
        self.P_shadowstrenght=0.0
        self.P_fog=0

        self.projmode=self.ORTHO

        self.writeAlpha=False
        self.writeCol=False
        self.P_capping=False

        self.P_halo_size=0.0

        self.shadowmapBuilding=True
        self.accurateShadowmapBuilding=accurate

    def MakeShaders(self):    # activates parameters
        if (self.shadersMade): return
        self.shadersMade = True
        if (self.idf == 666): self.idf = glew.glGenProgramsARB(1)
        glew.glBindProgramARB(glew.GL_FRAGMENT_PROGRAM_ARB, self.idf)
        self.setBallFragmentProgram()
        if (self.idv == 666): self.idv = glew.glGenProgramsARB(1)
        glew.glBindProgramARB(glew.GL_VERTEX_PROGRAM_ARB, self.idv)
        self.setBallVertexProgram()
        self.loaded = True
        #self.MakeStickShaders()  # XXX Stick shaders not fully ported

    def UpdateShaders(self):
        self.shadersMade=False    # activates params 

    def BindShaders(self):    # binds, loads if necessary
        if not self.loaded: self.MakeShaders()
        glew.glBindProgramARB(glew.GL_FRAGMENT_PROGRAM_ARB, self.idf)
        glew.glBindProgramARB(glew.GL_VERTEX_PROGRAM_ARB, self.idv)

    def MakeStickShaders(self):
        if (self.idfStick == 666): self.idfStick = glew.glGenProgramsARB(1)
        glew.glBindProgramARB(glew.GL_FRAGMENT_PROGRAM_ARB, self.idfStick)
        self.setStickFragmentProgram()

        if (self.idvStick==666): self.idvStick = glew.glGenProgramsARB(1)
        glew.glBindProgramARB(glew.GL_VERTEX_PROGRAM_ARB, self.idvStick)
        self.setStickVertexProgram()

        self.loadedStick=True
        
    def BindStickShaders(self):
        if not self.loadedStick:  self.MakeStickShaders()
        glew.glBindProgramARB(glew.GL_FRAGMENT_PROGRAM_ARB, self.idfStick)
        glew.glBindProgramARB(glew.GL_VERTEX_PROGRAM_ARB, self.idvStick)

    def BindDrawAOShader(self):
        if (self.idf==666): self.idf = glew.glGenProgramsARB(1)
        glew.glBindProgramARB(glew.GL_FRAGMENT_PROGRAM_ARB, self.idf)
        if not self.loaded: self.MakeDrawAOShader()
        self.loaded = True
        return True

    def MakeDrawAOShader(self):
        fp  = '''\
!!ARBfp1.0  \n\
PARAM  Smat0 = program.env[0];\n\
PARAM  Smat1 = program.env[1];\n\
PARAM  Smat2 = program.env[2];\n\
PARAM  param = program.env[3];\n\
ATTRIB tc   = fragment.texcoord;  \n\
ATTRIB data   = fragment.texcoord[1];  \n\
TEMP tmp,nor, pos,origpos, abs,l;\n\
\n\
# Find shpere normal... \n\
CMP abs, tc, -tc, tc;\n\
MAD nor, -abs, {1,1,0,0}, +1;\n\
CMP tmp.x, tc.x, -nor.y, nor.y;    # tmp_i = sign_i*( 1-abs_i) \n\
CMP tmp.y, tc.y, -nor.x, nor.x;    # tmp_i = sign_i*( 1-abs_i) \n\
ADD nor.z, abs.x, abs.y; \n\
ADD nor.z, nor.z, -1; \n\
CMP nor.x, -nor.z, tmp.x, tc.x;\n\
CMP nor.y, -nor.z, tmp.y, tc.y;\n\
# Normalize \n\
DP3 tmp.x, nor, nor; \n\
RSQ tmp.x, tmp.x; \n\
MUL nor, nor, tmp.x; \n\
\n\
# Find pos \n\
MAD origpos, data.w, nor, data;\n\
MOV origpos.w, 1;\n'''
        fp += self.addDrawAOShaderSnippet()

        glew.glProgramStringARB(glew.GL_FRAGMENT_PROGRAM_ARB, glew.GL_PROGRAM_FORMAT_ASCII_ARB, fp)
        if not _checkProgramError(fp): return False
        else: return True

    def BindDrawAOShaderSticks(self):
        if (self.idf==666): self.idf = glew.glGenProgramsARB(1)
        glew.glBindProgramARB(glew.GL_FRAGMENT_PROGRAM_ARB, self.idf)
        if not self.loaded: self.MakeDrawAOShaderSticks()
        self.loaded = True
        return True

    def MakeDrawAOShaderSticks(self):
        fp = '''\
!!ARBfp1.0  \n\
PARAM  Smat0 = program.env[0];\n\
PARAM  Smat1 = program.env[1];\n\
PARAM  Smat2 = program.env[2];\n\
PARAM  param = program.env[3];\n\
PARAM  radius = program.env[4];\n\
ATTRIB axispos= fragment.texcoord[1];  \n\
ATTRIB data   = fragment.texcoord;  \n\
TEMP tmp,n,nor, pos,origpos, abs,l;\n\
\n\n\
# find norm in cyl space \n\
MAD n.y, data.y, -2, 0; \n\
CMP n.y, n.y, -n.y, n.y; \n\
ADD n.x, 2, -n.y; \n\
MIN n.x, n.x, n.y; \n\
CMP n.x, data.y, n.x, -n.x; \n\
MAD n, n, {1,1,0,0}, {0,-1,0,0};\n\
\n\
# normalize \n\
DP3 tmp.x, n, n;\n\
RSQ tmp.x, tmp.x;\n\
MUL n, tmp.x, n;\n\
\n\
# rotate \n\
MUL nor, -n.x, fragment.texcoord[2];\n\
MAD nor,  n.y, fragment.texcoord[3], nor;\n\
\n\
# find position \n\
MAD origpos, nor, radius.y, axispos; \n\
MOV origpos.w, 1;\n'''
        fp += self.addDrawAOShaderSnippet()
        glew.glProgramStringARB(glew.GL_FRAGMENT_PROGRAM_ARB, glew.GL_PROGRAM_FORMAT_ASCII_ARB, fp)
        if not _checkProgramError(fp): return False
        else: return True

    def BindHaloShader(self, powres): # 1^powres = size of halo texture
        if (self.idfHalo[powres]==666):
            self.idfHalo[powres] = glew.glGenProgramsARB(1)
        glew.glBindProgramARB(glew.GL_FRAGMENT_PROGRAM_ARB, self.idfHalo[powres])

        if not self.loadedHalo[powres]: self.MakeHaloShader(powres)

        if (self.idvHalo==666): self.idvHalo = glew.glGenProgramsARB(1)
        glew.glBindProgramARB(glew.GL_VERTEX_PROGRAM_ARB, self.idvHalo)
        if not self.loadedVertexHalo: self.LoadVertexHaloShader()

        self.loadedHalo[powres] = True
        self.loadedVertexHalo = True
        return True

    def MakeHaloShader(self, powres):
        fp = '''\
!!ARBfp1.0\n\
\n\
ATTRIB data   = fragment.texcoord;  \n\
\n\
TEMP tmp,tmp2,tmp3, t,t0,t1,t2,nor,n,nabs,nsign,disp,res,depth,pos,\n\
     lighting;  \n\
\n\
MOV nor, data;  \n\
MUL tmp, data, data;  \n\
ADD tmp2.x, tmp.x, tmp.y;\n\
ADD tmp2.z, -tmp2.x, 1;\n\
KIL tmp2.z;\n\
\n\
MAD tmp2.x, -data.z, tmp2.x, data.z;\n\
\n\
#TEST!\n\
#ADD tmp2.x, tmp2.x, %10.8f;\n\
#CMP result.color, tmp2.x, {1,0,0,1}, {0,0,1,1};\n\
\n\
MUL tmp, fragment.position, {%14.12f, %14.12f, 0, 0};\n\
#MAD tmp, fragment.position, {0.5, 0.5, 0, 0}, {0.5, 0.5, 0, 0};\n\
TEX tmp.z, tmp, texture[1], 2D; # tmp.z = old depth \n\
ADD tmp.z, tmp.z, -fragment.position.z; \n\
MUL_SAT tmp.z, tmp.z, program.env[0].x; \n\
MUL tmp.z, tmp.z, tmp2.x; \n\
MUL tmp.z, tmp.z, tmp2.x;  # again for smoother edges\n'''%(self.P_halo_str-1, 1.0/(1<<powres), 1.0/(1<<powres))
        if (self.P_halo_str<1.0): fp += "MUL tmp.z , tmp.z, %10.8f;\n"%(self.P_halo_str)
        if not self.doingAlphaSnapshot:
            fp += "MAD result.color, {0,0,0,1}, tmp.z, {%5.4f,%5.4f,%5.4f,0.0} ;\n"%(self.P_halo_col,self.P_halo_col,self.P_halo_col)
        else:
            if (self.P_halo_col==1.0): fp += "MOV result.color, tmp.z;\n"
            else: fp += "MUL result.color, {0,0,0,1}, tmp.z;\n"
        fp += "END\n"

        glew.glProgramStringARB(glew.GL_FRAGMENT_PROGRAM_ARB, glew.GL_PROGRAM_FORMAT_ASCII_ARB, fp)
        if not _checkProgramError(fp): return False
        else: return True

    def ResetHalo(self):
        self.loadedHalo = numpy.zeros(CgUtil.MAXPOW, numpy.bool)
        self.idfHalo = numpy.zeros(CgUtil.MAXPOW, numpy.int)+666

    def setBallVertexProgram(self):
        vertex_prog = '''\
!!ARBvp1.0\n\
\n\
ATTRIB pos = vertex.position;\n\
ATTRIB data = vertex.normal;\n\
\n'''

        if (self.P_texture>0): vertex_prog += 'ATTRIB offset = vertex.texcoord;\n'

        vertex_prog += '''\
\n\
PARAM  mat[4] = { state.matrix.mvp };\n\
PARAM  matP[4] = { state.matrix.projection };\n\
\n\
TEMP p,po, disp, dataout, tmp;\n\
\n\
# Transform by concatenation of the\n\
# MODELVIEW and PROJECTION matrices.\n\
DP4 p.x, mat[0], pos;\n\
DP4 p.y, mat[1], pos;\n\
DP4 p.z, mat[2], pos;\n\
DP4 p.w, mat[3], pos;\n\
#MOV p.w, 1; \n\
\n\
MOV dataout, data;\n\
MUL dataout.z, dataout.z, program.env[0].x;\n'''
        # Enlarge impostors to include borders
        if (self._border_outside() != 0): vertex_prog += '''\
RSQ tmp.y,  dataout.z ;\n\
#MUL tmp.y,  tmp.y , tmp.y; # Comment to 'almost'\n\
MUL tmp.x,  %7.5f , tmp.y;\n\
ADD dataout.w,  tmp.x , 1;\n\
MUL dataout.xy, dataout, dataout.w ;\n\
MAD dataout.w,  dataout.w, dataout.w, -1;\n'''%(self._border_outside())

        vertex_prog += '''\n\
MUL disp, dataout, dataout.z; \n\
#MUL disp.x, disp.x, matP[0].x;\n\
#MUL disp.y, disp.y, matP[1].y;\n\
MAD p, {1,1,0,0},  disp, p;\n\
\n\
MOV result.position, p;\n\
\n\
#MOV dataout.w, p.w;\n\
MOV result.texcoord, dataout;\n\
'''

        if ((self.P_col_atoms_sat>0) and (self.P_col_atoms_bri>0)): vertex_prog += "MOV result.color, vertex.color;\n"
        if (self.P_texture>0): vertex_prog += "MOV result.texcoord[2], offset;\n"
        if (self.P_use_shadowmap() ): vertex_prog +=" MOV result.texcoord[3], vertex.position;\n"
        vertex_prog += "\nEND\n"

        glew.glProgramStringARB(glew.GL_VERTEX_PROGRAM_ARB, glew.GL_PROGRAM_FORMAT_ASCII_ARB, vertex_prog)
        if not _checkProgramError(vertex_prog): return False
        else: return True

    def setBallFragmentProgram(self):
        CgUtil.shaderHasChanged = True
        frag_prog = ''
        if (self.shadowmapBuilding):
            frag_prog += '''\
!!ARBfp1.0  \n\
\n\
ATTRIB data = fragment.texcoord;  \n\
TEMP tmp; \n\
\n\
MAD tmp.x, data.x, data.x, -1;  \n\
MAD tmp.x, data.y, data.y, tmp.x;  \n\
KIL -tmp.x;\n'''
            if (self.accurateShadowmapBuilding):
                frag_prog += '''\
RSQ tmp.x, tmp.x;  \n\
RCP tmp.x, tmp.x;  \n\
MUL tmp.x, tmp.x, data.z; \n\
MAD result.depth, -tmp.x, 0.005, fragment.position.z;\n'''

            frag_prog += '''\
MOV result.color, 1;\n\
END\n'''

            glew.glProgramStringARB(glew.GL_FRAGMENT_PROGRAM_ARB, glew.GL_PROGRAM_FORMAT_ASCII_ARB, frag_prog)
            if not _checkProgramError(frag_prog): return False
            else: return True

        #####
        ## Fragment program ball
        ####
        frag_prog += '''\
!!ARBfp1.0  \n\
\n\
ATTRIB data = fragment.texcoord;  \n\
ATTRIB offset = fragment.texcoord[2];\n\
ATTRIB basecol = fragment.color;  \n\
'''
        if self.P_use_shadowmap():
            frag_prog += '''\
PARAM  Smat0  = program.env[3];   \n\
PARAM  Smat1  = program.env[4];   \n\
PARAM  Smat2  = program.env[5];   \n\
#PARAM  ratio  = program.env[6];   \n\
ATTRIB origpos = fragment.texcoord[3];  \n'''

        if (moltextureCanvas.GetHardRes()==0): TNORM=0
        else: TNORM = 1.0/moltextureCanvas.GetHardRes()
        frag_prog += '''\n\
TEMP tmp,tmp2,tmp3, t,t0,t1,t2,nor,n,nabs,nsign,disp,res,depth,\n\
     lighting, border, posScreen;  \n\
PARAM TNORM={%10.9f,%10.9f,0,0};  \n\
\n\
PARAM LIGHT= state.light[0].position ;  \n\
PARAM hwv  = state.light[0].half;\n\
\n\
PARAM  mat[4] = { state.matrix.projection };  \n\
PARAM  mat0 = program.env[0];\n\
PARAM  mat1 = program.env[1];\n\
PARAM  mat2 = program.env[2];\n\
\n'''%(TNORM,TNORM)

        frag_prog += '''MOV nor, data;  \n'''

        frag_prog += '''\
MUL tmp, data, data;  \n\
MOV tmp.z, 1;          \n\
DP3 border.x, tmp, {1,1,-1,0};  \n'''

        if (self._border_outside() > 0):
            frag_prog += '''\
ADD tmp2.y, -border.x, data.w;  # allow for border (part ii)  \n\
#MAD tmp2.y, data.z, -border.x, %7.5f;\n\
#MAD tmp2.y, data.z, tmp2.y, %7.5f;\n\
KIL tmp2.y;  \n'''%(-2*self._border_outside(), self._border_outside()*self._border_outside())
        else: frag_prog += '''\n\nKIL -border.x;  \n'''

        frag_prog += '''\
RSQ tmp2.y, border.x;  \n\
RCP tmp2.x, tmp2.y;  \n\
MOV nor.z, tmp2.x;  \n\
\n\
MAD tmp2.y, tmp2.x, data.z, 0;  # note: add an extra range of 0 \n\n
MAD depth.x, -tmp2.y, 0.005, fragment.position.z; # ortho \n'''

        frag_prog += self.addDepthAdjustSnippet()

        if ((self.P_texture>0) or (self.P_use_shadowmap())):
            frag_prog += '''\n\n\
# rotate normal           \n\
DP3 n.x, mat0, nor;        \n\
DP3 n.y, mat1, nor;         \n\
DP3 n.z, mat2, nor;          \n\
MOV n.w, 0;                   \n\n'''

        frag_prog += self.addDirectLightingSnippet()
        if (self.P_use_shadowmap()): frag_prog += self.addShadowMapComputation()

        if (self.P_texture>0):
            CSIZE = hardSettings.CSIZE
            frag_prog += '''\n\n\
## TEXTURING OCTAMAP STYLE    \n\
#                              \n\
CMP nabs, n, -n, n;             \n\
DP3 tmp.y, {1,1,1,0}, nabs;      \n\
RCP tmp.z, tmp.y;                 \n\
MUL t0, n, tmp.z;                  \n\
MAD t1, nabs, tmp.z, -1;            \n\
#   t1= -(1-abs(t))                  \n\
CMP t2.x, n.x, t1.y, -t1.y;           \n\
CMP t2.y, n.y, t1.x, -t1.x;            \n\
CMP t0, n.z, t0, t2;                    \n\
MAD t, t0, {%5.2f, %5.2f, 0,0},          \n\
           {%5.2f, %5.2f, 0,0};           \n\n'''%(CSIZE/2.0 - self.gap, CSIZE/2.0 - self.gap, CSIZE/2.0, CSIZE/2.0)

        frag_prog += self.addTexturingSnippet()
        frag_prog += '''\
ADD result.color, res, {0,0,0,1};\n\n\
END\n'''
        glew.glProgramStringARB(glew.GL_FRAGMENT_PROGRAM_ARB, glew.GL_PROGRAM_FORMAT_ASCII_ARB, frag_prog)
        if not _checkProgramError(frag_prog): return False
        else: return True

    #def setStickVertexProgram(self): pass
    #def setStickFragmentProgram(self): pass

    def LoadVertexHaloShader(self):
        vp = '''\
!!ARBvp1.0\n\
\n\
ATTRIB pos = vertex.position;\n\
ATTRIB dataA = vertex.texcoord[0];\n\
ATTRIB dataB = vertex.texcoord[1];\n\
\n\n\
PARAM  mat[4] = { state.matrix.mvp };\n\
PARAM  matP[4] = { state.matrix.projection };\n\
\n\
TEMP p,po, disp, dataout, tmp;\n\
\n\
# Transform by concatenation of the\n\
# MODELVIEW and PROJECTION matrices.\n\
DP4 p.x, mat[0], pos;\n\
DP4 p.y, mat[1], pos;\n\
DP4 p.z, mat[2], pos;\n\
DP4 p.w, mat[3], pos;\n\
#MOV p.w, 1; \n\
\n\
MOV dataout, dataA;\n\
MOV dataout.z, dataB.y;\n\n\
MUL disp, dataA, dataB.x; \n\
MUL disp, disp, program.env[0].x; \n\
#MUL disp.x, disp.x, matP[0].x;\n\
#MUL disp.y, disp.y, matP[1].y;\n\
MAD p, {1,1,0,0},  disp, p;\n\
MOV result.position, p;\n\
MOV result.texcoord, dataout;\n\
\nEND\n'''

        glew.glProgramStringARB(glew.GL_VERTEX_PROGRAM_ARB, glew.GL_PROGRAM_FORMAT_ASCII_ARB, vp);
        if not _checkProgramError(vp): return False
        else: return True

    def addDirectLightingSnippet(self):
        prog = ''
        #NOTE:
        #lighting.x = lambert direct (halved if opposite side)
        #lighting.y = phong  direct (zeroed if opposite side)
        #lighting.z = lamber original (negative if opposite side)
        if not (self.P_sem_effect): lighting = self.P_lighting
        else: lighting = 1 - self.P_lighting

        if (lighting>0): prog += '''\n\n\
## LIGHTING of Normal        \n\
DP3 lighting.z, nor, LIGHT;        \n\
MUL tmp.y, -lighting.z, 0.35;        \n\
CMP lighting.x, lighting.z, tmp.y, lighting.z; \n\n'''

        if (self.P_phong>0.0):
            # phong
            prog += '''\
## PHONG \n\
#ADD hwv, {0,0,+1,0}, LIGHT;\n\
#DP3 lighting.y, hwv, hwv;\n\
#RSQ lighting.y, lighting.y;\n\
#MUL hwv, hwv, lighting.y;\n\
DP3 lighting.y, nor, hwv;\n'''

            # compute exponent (TODO: use some sort of EXP funtion)
            for i in range(int(numpy.ceil((1.0-self.P_phong_size)*6.0+3))):
                prog += "MUL lighting.y, lighting.y, lighting.y;\n"

            if (self.P_phong<1.0):
                prog += "\nMUL lighting.y,%5.4f,lighting.y;\n"%(self.P_phong)
        if(self.P_light_base>0): prog += "\nLRP lighting.x,%5.4f, 1, lighting.x; # flatten light \n"%(self.P_light_base)
        prog += "\nMOV res, %5.4f;\n"%(0.0)
        return prog

    def addShadowMapComputation(self):
        prog = '''\n\
#SHADOWMAP\n\
\n\
#compute orig pos from attributes... MODE 1\n\
#MUL t0.x, data.z, ratio.x;\n\
#MAD pos, n, t0.x, origpos;\n\
#\n\
# ...or MODE 2!!! \n\
MAD posScreen, fragment.position, {1,1,0,0}, {0,0,0,1} ;\n\
MOV posScreen.z, depth.x;\n\
\n\
DP4 t0.x, Smat0, posScreen;        \n\
DP4 t0.y, Smat1, posScreen;         \n\
DP4 t0.z, Smat2, posScreen;          \n'''

        if (self.do_use_doubleshadow()): prog += '''\n\
CMP t1, lighting.z, {0.75,0.5,0.5,1}, {0.25,0.5,0.5,1};\n\
MAD t0, t0, {0.25,0.5,0.5,0}, t1; \n\
\n'''
        else:
            if hardSettings.doubleSM: tmp=0.25
            else: tmp = 0.5
            prog += "\nMAD t0, t0, {%4.2f,0.5,0.5,0}, {%4.2f,0.5,0.5,1}; \n"%(tmp,tmp)
        prog += '''\n\
# Access shadow map! \n\
TEX t1, t0, texture[1], 2D;\n\
ADD t.z, -t1.z, t0.z; \n'''
        if (self.do_use_doubleshadow()): prog += "\nCMP t.z, lighting.z, -t.z, t.z; \n\n"

        if (not self.do_use_doubleshadow() and self.P_light_base>0): prog += "\nCMP t.z, lighting.z, 1, t.z;    # if light<0,  then in shadow \n"

        if (self.P_shadowstrenght<1):
            prog += '''\n\
MUL tmp, lighting, %5.4f; # compute attenuated light \n\
CMP lighting, t.z, lighting, tmp; # if in shadow, then use attenuated light \n'''%(1.0-self.P_shadowstrenght)
        else: prog += '''\n\
CMP lighting, t.z, lighting, 0; # if in shadow, then no light \n\
#CMP result.color, t.z, {0,1,0,0}, {1,0,0,0}; \n\
#\n\
#MAD t0, t0, {0.5,0.5, 200.0,0}, {0.5,0.5,196.5,0}; \n\
#TEX t1, t0, texture[1], 2D;\n\
#MAD t1, t1, 400, -3.5;\n\
#MUL t1, t1.z, {1,0,1,0};\n\
##ADD t.z, -t1.z, t0.z; \n\
#MAD t0, t0.z, {0,1,0,0}, {0,0,0,0};\n\
#CMP result.color, mat0.x, t1, t0; \n\
#MUL result.color, {0.002,0.002,0,0}, posScreen; \n'''
        return prog

    def addTexturingSnippet(self):
        prog = ''
        if (self.P_texture>0):
            prog += '''\n\n\
# texture access           \n\
MAD t, t, TNORM, offset;    \n\
TEX t, t, texture[0], 2D;    \n\n'''

            if (self.P_capping):
                #overwrite ambient occlusion for close fragments
                prog += '''\n\n\
# lighten OC for close frags           \n\
MAD tmp.x, depth.x, -250, 0.50;   \n\
CMP tmp.x, tmp.x, 0, tmp.x;    \n\
# overwrite OC for cut   \n\
CMP tmp.x, depth.x, 0.70, tmp.x;    \n\
LRP t, tmp.x, 1, t;    \n'''

            # Add "future" AO prediction (AO not computed yet)

            # multiplicative prediction:
            prog += "MUL t, t, program.env[6].x;\n"
            prog += "MAD res, %5.2f, t, res;\n"%(self.P_texture)
            if (self.P_phong>0.0):
                #weigth phong with AO light
                prog += "\nMUL lighting.y,lighting.y, t;\n"

        if not (self.P_sem_effect): lighting = self.P_lighting
        else: lighting = 1 - self.P_lighting
        # apply lighting
        if ( lighting>0 ):
            if (self.P_sem_effect): prog += '''\
MAD lighting.x, lighting.x, -1, 1 ;\n\
MAD lighting.x, %10.8f, lighting.x, %10.8f;\n\
MUL res, lighting.x, res;\n'''%(lighting, 1-lighting)
            else: prog += "\nMAD res, lighting.x, %f, res;\n"%(lighting)

        if (self.P_col_atoms_sat>0):
            if ((self.P_col_atoms_sat<1) or (self.P_col_atoms_bri<1)):
                prog += "MAD tmp, %5.3f, basecol,%5.3f;\n"%(self.P_col_atoms_sat*self.P_col_atoms_bri, (1.0-self.P_col_atoms_sat)*self.P_col_atoms_bri )
                prog += "MUL res, res, tmp;\n"
            else: prog += "MUL res, res, basecol;\n"
        else:
            if (self.P_col_atoms_bri<1.0): prog += "MUL res, res, %5.3f;\n"%(self.P_col_atoms_bri)

        if (self.writeCol):
            if (self.P_phong>0): prog += "LRP res, lighting.y, 1, res;\n"

        if (self.writeAlpha): prog += "MOV res.w, nor.z;\n"
        # UNUSED:
        if ( self._border_inside()>0 ): prog += '''\n\
MAD tmp2.z, border.x, %f, 1;     \n\
LRP tmp3, tmp2.z, 0, res;\n\
CMP res, -tmp2.z,  tmp3, res;\n\n'''%(1.0/self._border_inside())
        if ( self._border_outside()>0 ):
            #Blackens borders:
            prog += "CMP res, -border.x,  {0,0,0,0}, res;\n"

        if ( self.P_fog>0 ):
            prog += "MAD_SAT tmp.x, depth.x,  50, 0;\n"
            prog += "MUL tmp.x, tmp.x, %5.4f;\n"%(self.P_fog)
            prog += "LRP res, tmp.x, {%10.9f,%10.9f,%10.9f,1}, res;\n"%(self.P_bg_color_R,self.P_bg_color_G,self.P_bg_color_B)

        return prog

    def addDepthAdjustSnippet(self):
        prog = ''
        depth_full=self.P_depth_full*120.0

        # DEPTH AWARE
        if ( self._border_outside()>0 ): prog += '''\
MUL tmp3.z,  -border.x,  data.z;\n\
MAD tmp3.z,  %8.7f , tmp3.z , fragment.position.z;\n\
CMP depth.x, -border.x, tmp3.z, depth.x;\n\
\n'''%(-depth_full/self._border_outside() / 20000.0) #-0.001)

        if (self.P_capping): prog += "ADD result.depth, depth.x, 0.001;\n"
        else: prog += "MOV result.depth, depth.x;\n"

        prog += "MUL res, res, t;\n"
        if not (self.P_sem_effect): lighting = self.P_lighting
        else: lighting = 1 - self.P_lighting

        if ((self.P_capping) and ( (lighting>0) or (self.P_phong>0) ) ): prog += '''\n\
# Overwrite capped normal    \n\
CMP nor, depth.x, {0,0,1,0}, nor;\n'''
        return prog

    def addDrawAOShaderSnippet(self):
        prog = '''\n\
# Find shading value \n\
DP3 l.x, nor, -param; \n\
#MUL_SAT l.x, l.x, param.w; \n\
MUL l.x, l.x, param.w; \n\
#KIL l.x; \n'''
        if ( not hardSettings.doubleSM) and ( not hardSettings.NVIDIA_PATCH):
            prog += "\nKIL l.x; # early KILL of fragments on the dark side...\n"

        prog += '''\n\
# Project! \n\
DP4 pos.x, Smat0, origpos;   \n\
DP4 pos.y, Smat1, origpos;    \n\
DP4 pos.z, Smat2, origpos;     \n'''
        if (hardSettings.doubleSM): prog += '''\n\
CMP tmp, l.x, {0.75,0.5,0.5,1}, {0.25,0.5,0.5,1};\n\
MAD pos, pos, {0.25,0.5,0.5,0}, tmp; \n\
\n'''
        else: prog += '''\n\
MAD pos, pos, {0.5,0.5,0.5,0}, {0.5,0.5,0.5,1}; \n'''

        prog += '''\n\
# Access shadow map! \n\
TEX tmp.x, pos, texture[1], 2D;\n\
SUB l.z, tmp.x, pos.z; \n'''

        if (hardSettings.doubleSM): prog += '''\n\
CMP l.z, l.x, -l.z, l.z; \n\
CMP l.x, l.x, -l.x, l.x; # DOUBLE SIDE\n\n'''

        if hardSettings.NVIDIA_PATCH: nvidia_patch = "MUL l.x, 0.5, param.w;          # <-- patch! REMOVE ME when N-VIDIA wakes up \n"
        else: nvidia_patch = ""

        prog += '''\n\
# NVIDIA BUUUUGUUGUGUGUGUGUUGUUGGUGUUGUG GUUGUGUG GGFUCKFUCKFUCKFUCKFUCKFUCKFUCK!!! \n\
%s\
CMP result.color, l.z, 0, l.x;  # <-- (shadow & shading) \n\
#CMP result.color, l.z, 0, 1;   # <-- (TEST: only shadow - works) \n\
#CMP result.color, 1, 0, l.x;   # <-- (TEST: only shading - works) \n\
# NVIDIA BUUUUGUUGUGUGUGUGUUGUUGGUGUUGUG GUUGUGUG GGFUCKFUCKFUCKFUCKFUCKFUCKFUCK!!! \n\
\n\
# TEST1: MAD result.color, {0.5,0.5,0.5,0},nor, {0.5,0.5,0.5,1};\n\
# TEST2: MAD result.color, {0.5,0.5,0.5,0},origpos, {0.5,0.5,0.5,1};\n\
# TEST3: CMP result.color, l.z, {1,0,0,1}, {0,0,0.5,1};\n\
# TEST4: MOV result.color, tmp.x;\n\
\n\
\n\
END\n'''%(nvidia_patch)
        return prog

    def Save(self, filename):
        FORMAT="void CgUtil::Set(int K){\nif (K==0){\n P_light_base = %f ;\n P_lighting = %f ;\n P_phong = %f ;\n P_phong_size = %f ;\n P_col_atoms_sat = %f ;\n P_col_atoms_bri = %f ;\n P_texture = %f ;\n P_border_inside = %f ;\n P_border_outside = %f ;\n P_depth_full = %f ;\n P_sem_effect = %d ;\n P_halo_size = %f ;\n P_halo_col = %f ;\n P_halo_str = %f ;\n P_halo_aware = %f ;\n P_fog = %f ;\n P_capping = %d ;\n P_shadowstrenght = %f ;\n P_bg_color_R = %f ;\n P_bg_color_G = %f ;\n P_bg_color_B = %f ;\n auto_normalize = %d ;\n P_double_shadows = %d ;\n P_border_fixed = %d ;\n}\n}"
        print FORMAT%(self.P_light_base,self.P_lighting,self.P_phong,self.P_phong_size,self.P_col_atoms_sat,self.P_col_atoms_bri,self.P_texture,self.P_border_inside,self.P_border_outside,self.P_depth_full,self.P_sem_effect,self.P_halo_size,self.P_halo_col,self.P_halo_str,self.P_halo_aware,self.P_fog,self.P_capping,self.P_shadowstrenght,self.P_bg_color_R,self.P_bg_color_G,self.P_bg_color_B,self.auto_normalize,self.P_double_shadows,self.P_border_fixed)

def _checkProgramError(prog):
    res = True
    while (True):
        error = glew.glGetError()
        if (error == glew.GL_NO_ERROR): return res
        res = False
        if (error == glew.GL_INVALID_OPERATION):
            print prog
            errPos = glGetIntegerv(glew.GL_PROGRAM_ERROR_POSITION_ARB)
            errString = glGetString(glew.GL_PROGRAM_ERROR_STRING_ARB)
            print "error at position: %d\n[%s]"%(errPos,errString)
            print "\n\"..."
            for i in range(errPos-40,errPos+40):
                if (i >= 0):
                    if not prog[i]: break
                    if (i == errPos): print "(*)"
                    if (prog[i]=='\n'): print '\\'
                    else: print prog[i]
            print "...\"\n"
        else:
            errString = GLU.gluErrorString(error)
            print "error: [%s]"%errString

def __showShaderInfo(fp):
    size = 10
    i = numpy.zeros(size, numpy.int)
    j = numpy.zeros(size, numpy.int)
    k = numpy.zeros(size, numpy.int)
    h = numpy.zeros(size, numpy.int)

    glew.glGetProgramivARB(fp, GL_MAX_PROGRAM_INSTRUCTIONS_ARB,     i)
    glew.glGetProgramivARB(fp, GL_MAX_PROGRAM_ALU_INSTRUCTIONS_ARB, i+1)
    glew.glGetProgramivARB(fp, GL_MAX_PROGRAM_TEX_INSTRUCTIONS_ARB, i+2)
    glew.glGetProgramivARB(fp, GL_MAX_PROGRAM_TEX_INDIRECTIONS_ARB, i+3)
    glew.glGetProgramivARB(fp, GL_MAX_PROGRAM_TEMPORARIES_ARB,      i+4)
    glew.glGetProgramivARB(fp, GL_MAX_PROGRAM_PARAMETERS_ARB,       i+5)
    glew.glGetProgramivARB(fp, GL_MAX_PROGRAM_ATTRIBS_ARB,          i+6)
    
    glew.glGetProgramivARB(fp, GL_PROGRAM_INSTRUCTIONS_ARB,     j)
    glew.glGetProgramivARB(fp, GL_PROGRAM_ALU_INSTRUCTIONS_ARB, i+1)
    glew.glGetProgramivARB(fp, GL_PROGRAM_TEX_INSTRUCTIONS_ARB, j+2)
    glew.glGetProgramivARB(fp, GL_PROGRAM_TEX_INDIRECTIONS_ARB, j+3)
    glew.glGetProgramivARB(fp, GL_PROGRAM_TEMPORARIES_ARB,      j+4)
    glew.glGetProgramivARB(fp, GL_PROGRAM_PARAMETERS_ARB,       j+5)
    glew.glGetProgramivARB(fp, GL_PROGRAM_ATTRIBS_ARB,          j+6)
    
    glew.glGetProgramivARB(fp, GL_PROGRAM_NATIVE_INSTRUCTIONS_ARB,     k)
    glew.glGetProgramivARB(fp, GL_PROGRAM_NATIVE_ALU_INSTRUCTIONS_ARB, k+1)
    glew.glGetProgramivARB(fp, GL_PROGRAM_NATIVE_TEX_INSTRUCTIONS_ARB, k+2)
    glew.glGetProgramivARB(fp, GL_PROGRAM_NATIVE_TEX_INDIRECTIONS_ARB, k+3)
    glew.glGetProgramivARB(fp, GL_PROGRAM_NATIVE_TEMPORARIES_ARB,      k+4)
    glew.glGetProgramivARB(fp, GL_PROGRAM_NATIVE_PARAMETERS_ARB,       k+5)
    glew.glGetProgramivARB(fp, GL_PROGRAM_NATIVE_ATTRIBS_ARB,          k+6)
    
    glew.glGetProgramivARB(fp, GL_MAX_PROGRAM_NATIVE_INSTRUCTIONS_ARB,     h)
    glew.glGetProgramivARB(fp, GL_MAX_PROGRAM_NATIVE_ALU_INSTRUCTIONS_ARB, h+1)
    glew.glGetProgramivARB(fp, GL_MAX_PROGRAM_NATIVE_TEX_INSTRUCTIONS_ARB, h+2)
    glew.glGetProgramivARB(fp, GL_MAX_PROGRAM_NATIVE_TEX_INDIRECTIONS_ARB, h+3)
    glew.glGetProgramivARB(fp, GL_MAX_PROGRAM_NATIVE_TEMPORARIES_ARB,      h+4)
    glew.glGetProgramivARB(fp, GL_MAX_PROGRAM_NATIVE_PARAMETERS_ARB,       h+5)
    glew.glGetProgramivARB(fp, GL_MAX_PROGRAM_NATIVE_ATTRIBS_ARB,          h+6)

    st = ["Instr","Alu Instr","Tex Instr","Tex Indir","Temp","Param","Attr"]
    if (fp==glew.GL_FRAGMENT_PROGRAM_ARB): outst = "FRAGMENT"
    else: outst = "VERTEX"
    print "            %s PROGRAM STATS       "%outst
    print "              original    |  native         "
    print "            MAX   current |    MAX   current"
    for c in range(7):
        print "%10s   %5d %5d  |  %5d %5d"%(st[c],i[c],j[c],h[c],k[c])
    print "\n"

cgSettings = CgUtil()
