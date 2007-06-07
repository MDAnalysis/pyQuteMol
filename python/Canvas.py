
import numpy
import glew_wrap as glew
from OpenGL import GL
import hardSettings

class Canvas:
    INVALID_ID = 666
    MAX_RES = 15
    DEPTH = 0
    COLOR = 1
    COLOR_AND_DEPTH=2
    def __init__(self, kind, name="",size=0):
        self.name = name
        self.currentRes = 0
        self.onVideo = False
        self.kind = kind
        self.frameID = numpy.zeros(Canvas.MAX_RES, numpy.int)+Canvas.INVALID_ID
        self.textureID = numpy.zeros(Canvas.MAX_RES, numpy.int)+Canvas.INVALID_ID
        self.softRes = 0
        self.ratio2x1 = False
        if size != 0: self.SetRes(size)
    def SetRes(self, res):
        i = 0
        self.softRes = res
        while ((1<<i) < res): i+= 1
        if (i>=Canvas.MAX_RES):
            i = Canvas.MAX_RES-1
            self.softRes=1<<i
        self.currentRes = i
    def setResPow2(self, pow):
        self.currentRes=pow
        self.softRes=1<<self.currentRes
    def getResPow2(self):
        return self.currentRes
    def RedirectToVideo(self):
        self.onVideo = True
    def RedirectToMemory(self):
        self.onVideo=False
    def SetVideoSize(self, v):
        self.videoSize=v
    def GetVideoSize(self):
        return self.videoSize
    def GetHardRes(self):
        if (self.onVideo): return self.videoSize
        else: return 1<<self.currentRes
    def GetSoftRes(self):
        if (self.onVideo): return self.videoSize
        else: return self.softRes
    def SetSameRes(self,c):
        if (c.onVideo): self.SetRes(c.videoSize)
        else:
            currentRes = c.currentRes
            softRes = c.softRes
    def CheckFrameBuffer():
        res = glew.glCheckFramebufferStatusEXT(glew.GL_FRAMEBUFFER_EXT)
        if res == glew.GL_FRAMEBUFFER_COMPLETE_EXT: return True
        else: return False

    dummydepth=666
    def InitRes(self):
        depth = self.kind==Canvas.DEPTH
        hide = self.kind==Canvas.DEPTH
        use_depth = self.kind==Canvas.COLOR_AND_DEPTH
        screensizex = self.GetHardRes()
        screensizey = self.GetHardRes()
        if (self.ratio2x1): screensizex*=2
        status=12345
        status = glew.glCheckFramebufferStatusEXT(glew.GL_FRAMEBUFFER_EXT)
        if status == 12345: return False
        self.frameID[self.currentRes] = glew.glGenFramebuffersEXT(1)
        self.textureID[self.currentRes] = GL.glGenTextures(1)
        glew.glBindFramebufferEXT(glew.GL_FRAMEBUFFER_EXT, self.frameID[self.currentRes])
        tryme = [glew.GL_DEPTH_COMPONENT24, glew.GL_DEPTH_COMPONENT16]
        if (depth or use_depth): NTRIES=2
        else: NTRIES = 1

        for i in range(NTRIES):
            #initialize texture
            #glew.glActiveTextureARB(glew.GL_TEXTURE1_ARB)
            GL.glBindTexture(GL.GL_TEXTURE_2D, self.textureID[self.currentRes] )
            if depth: code1=tryme[i]; code2=GL.GL_DEPTH_COMPONENT; code3=GL.GL_UNSIGNED_INT
            else: code1 = GL.GL_RGBA8; code2=GL.GL_RGBA; code3=GL.GL_UNSIGNED_BYTE
            glew.glTexImage2D(GL.GL_TEXTURE_2D, 0, code1,
                screensizex, screensizey, 0, code2, code3, 0)
            GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MIN_FILTER, GL.GL_LINEAR)
            GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MAG_FILTER, GL.GL_LINEAR)
            GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_WRAP_S, GL.GL_CLAMP_TO_EDGE)
            GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_WRAP_T, GL.GL_CLAMP_TO_EDGE)

            #attach texture to framebuffer depth or color buffer
            if (depth): code1 = glew.GL_DEPTH_ATTACHMENT_EXT
            else: code1 = glew.GL_COLOR_ATTACHMENT0_EXT
            glew.glFramebufferTexture2DEXT(glew.GL_FRAMEBUFFER_EXT, code1, GL.GL_TEXTURE_2D, self.textureID[self.currentRes], 0)
            if (depth):
                GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MIN_FILTER, GL.GL_NEAREST)
                GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MAG_FILTER, GL.GL_NEAREST)
                GL.glTexParameteri(GL.GL_TEXTURE_2D, glew.GL_DEPTH_TEXTURE_MODE, GL.GL_LUMINANCE)
                if (hide):
                    # TODO: render to buffer NONE
                    renderID = glew.glGenRenderbuffersEXT(1)
                    glew.glBindRenderbufferEXT(glew.GL_RENDERBUFFER_EXT, renderID )
                    glew.glRenderbufferStorageEXT(glew.GL_RENDERBUFFER_EXT, GL.GL_RGBA, screensizex, screensizey)
                    glew.glFramebufferRenderbufferEXT(glew.GL_FRAMEBUFFER_EXT, glew.GL_COLOR_ATTACHMENT0_EXT,
                            glew.GL_RENDERBUFFER_EXT, renderID )
            if (use_depth):
                if Canvas.dummydepth == 666: Canvas.dummydepth = glew.glGenRenderbuffersEXT(1)
                glew.glBindRenderbufferEXT(glew.GL_RENDERBUFFER_EXT, Canvas.dummydepth )
                glew.glRenderbufferStorageEXT(glew.GL_RENDERBUFFER_EXT, tryme[i], screensizex, screensizey )
                # attach it to framebuffer
                glew.glFramebufferRenderbufferEXT(glew.GL_FRAMEBUFFER_EXT, glew.GL_DEPTH_ATTACHMENT_EXT, glew.GL_RENDERBUFFER_EXT, Canvas.dummydepth)
            Canvas.dummydepth=666
            if (self.CheckFrameBuffer()):
                glew.glBindFramebufferEXT(glew.GL_FRAMEBUFFER_EXT, 0 )
                return True
        glew.glBindFramebufferEXT(glew.GL_FRAMEBUFFER_EXT, 0 )
        return False

    def SetAsOutput(self):
        if (self.onVideo): glew.glBindFramebufferEXT(glew.GL_FRAMEBUFFER_EXT,0)
        else:
            if (self.frameID[self.currentRes] == Canvas.INVALID_ID):
                if not self.InitRes(): return False
            glew.glBindFramebufferEXT(glew.GL_FRAMEBUFFER_EXT,self.frameID[self.currentRes])
            if not self.CheckFrameBuffer(): return False
        return True

    def SetAsTexture(self):
        GL.glBindTexture(GL.GL_TEXTURE_2D, self.textureID[self.currentRes])
        if not self.CheckFrameBuffer(): return False

    def Test(self):
        return self.SetAsOutput()

    def CheckFrameBuffer(self):
        res = glew.glCheckFramebufferStatusEXT(glew.GL_FRAMEBUFFER_EXT)
        if (res == glew.GL_FRAMEBUFFER_COMPLETE_EXT): return True
        elif (res == glew.GL_FRAMEBUFFER_UNSUPPORTED_EXT):
            print "Unsupported FB!\n"
            return False
        elif (res == glew.GL_FRAMEBUFFER_INCOMPLETE_ATTACHMENT_EXT):
            print "Incomplete: attachment !\n"
            return False
        elif (res == glew.GL_FRAMEBUFFER_INCOMPLETE_MISSING_ATTACHMENT_EXT):
            print "Incomplete: missing attach  FB!\n"
            return False
        elif (res == glew.GL_FRAMEBUFFER_INCOMPLETE_DUPLICATE_ATTACHMENT_EXT):
            print "Incomplete: duplicate attach  FB!\n"
            return False
        elif (res == glew.GL_FRAMEBUFFER_INCOMPLETE_DIMENSIONS_EXT):
            print "Incomplete: dimensions!\n"
            return False
        elif (res == glew.GL_FRAMEBUFFER_INCOMPLETE_FORMATS_EXT):
            print "Incomplete: formats!\n"
            return False
        elif (res == glew.GL_FRAMEBUFFER_INCOMPLETE_DRAW_BUFFER_EXT):
            print "Incomplete: draw buffer!\n"
            return False
        elif (res == glew.GL_FRAMEBUFFER_INCOMPLETE_READ_BUFFER_EXT):
            print "Incomplete: read buffer!\n"
            return False
        else:
            print "Unknown FB error!\n"
            return False

mainCanvas = Canvas(Canvas.COLOR_AND_DEPTH, "mainCanvas")
moltextureCanvas = Canvas(Canvas.COLOR,"moltextureCanvas", size=hardSettings.TSIZE)
shadowmapCanvas = Canvas(Canvas.DEPTH,"shadowmapCanvas")
shadowAOCanvas = Canvas(Canvas.DEPTH,"shadowAOCanvas")
haloCanvas = Canvas(Canvas.DEPTH,"haloCanvas")

canvases = [mainCanvas, moltextureCanvas, shadowmapCanvas, shadowAOCanvas, haloCanvas]
