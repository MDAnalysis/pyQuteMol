
cdef extern from "Python.h":
        ctypedef int Py_intptr_t

cdef extern from "numpy/arrayobject.h":
    ctypedef class numpy.ndarray [object PyArrayObject]:
        cdef char *data
        cdef int nd
        cdef Py_intptr_t *dimensions
        cdef Py_intptr_t *strides
        cdef object base
        cdef int flags
        cdef object weakreflist
        # descr not implemented yet here...

ctypedef unsigned int GLenum
ctypedef float GLfloat

cdef extern from "myrand.h":
    float myrand()

cdef extern from "OpenGL/gl.h":
    void glVertex2f(GLfloat x, GLfloat y)
    void glVertex3f(GLfloat x, GLfloat y, GLfloat z)
    void glNormal3f(GLfloat nx, GLfloat ny, GLfloat nz)
    void glTexCoord2f(GLfloat s, GLfloat t)
    void glColor3f(GLfloat r, GLfloat g, GLfloat b)

cdef extern from "OpenGL/glext.h":
    void glMultiTexCoord2fARB(GLenum target, GLfloat s, GLfloat t)
    void glMultiTexCoord4fARB(GLenum target, GLfloat s, GLfloat t, GLfloat u, GLfloat v)

GL_TEXTURE0_ARB = 0x84C0
GL_TEXTURE1_ARB = 0x84C1

import numpy

def MolDraw(ndarray coords, ndarray radii, ndarray textures, ndarray colors, ndarray clipplane, ndarray exclude, ndarray indices = None):
    cdef int i, index, numindices, numexclude
    cdef int stride1, stride2
    cdef int *idx, *excl
    
    cdef int clipping
    cdef float *vert, *rad, *col, *tex, *clip
    cdef float x, y, z, r
    cdef int noindices
    vert = <float*>(coords.data)
    col = <float*>(colors.data)
    rad = <float*>(radii.data)
    tex = <float*>(textures.data)

    if coords.nd != 2:
        raise Exception("conf must be a sequence of 3 dimensional coordinates")
    if coords.dimensions[1] == 3:
        stride1 = coords.strides[0]/sizeof(float)
        stride2 = coords.strides[1]/sizeof(float)
    else:
        stride1 = coords.strides[1]/sizeof(float)
        stride2 = coords.strides[0]/sizeof(float)

    if indices is None:
        if coords.dimensions[1] == 3: numindices = coords.dimensions[0]
        else: numindices = coords.dimensions[1]
        noindices = 0
    else:
        numindices = len(indices)
        idx = <int*>(indices.data)
        noindices = 1

    if not numpy.allclose(clipplane,0):
        clipping = 1
        clip = <float*>(clipplane.data)
        excl = <int*>(exclude.data)
        numexclude = len(exclude)
    else: clipping = 0

    for i from 0<=i<numindices:
        if noindices == 0: index = i
        else: index = idx[i]

        x = vert[index*stride1+stride2*0]
        y = vert[index*stride1+stride2*1]
        z = vert[index*stride1+stride2*2]
        r = rad[index]
        if clipping == 1 and (x*clip[0]+y*clip[1]+z*clip[2]+clip[3]) < 0: continue
        glColor3f(col[index*3+0],col[index*3+1],col[index*3+2])
        glTexCoord2f(tex[index*2+0], tex[index*2+1])
        glNormal3f(+1,+1, r)
        glVertex3f(x, y, z)
        glNormal3f(-1,+1, r)
        glVertex3f(x, y, z)
        glNormal3f(-1,-1, r)
        glVertex3f(x, y, z)
        glNormal3f(+1,-1, r)
        glVertex3f(x, y, z)
    # Draw those excluded from clipping
    if clipping == 1:
        for i from 0<=i<numexclude:
            index = excl[i]
            x = vert[index*stride1+stride2*0]
            y = vert[index*stride1+stride2*1]
            z = vert[index*stride1+stride2*2]
            r = rad[index]
            glColor3f(col[index*3+0],col[index*3+1],col[index*3+2])
            glTexCoord2f(tex[index*2+0], tex[index*2+1])
            glNormal3f(+1,+1, r)
            glVertex3f(x, y, z)
            glNormal3f(-1,+1, r)
            glVertex3f(x, y, z)
            glNormal3f(-1,-1, r)
            glVertex3f(x, y, z)
            glNormal3f(+1,-1, r)
            glVertex3f(x, y, z)

def MolDrawShadow(ndarray coords, ndarray radii, ndarray clipplane, ndarray exclude, ndarray indices = None):
    cdef int i, index, numindices, numexclude, stride1, stride2
    cdef int *idx, *excl
    cdef float *vert, *rad, *clip
    cdef float x, y, z, r
    cdef int noindices, clipping
    vert = <float*>(coords.data)
    rad = <float*>(radii.data)

    if coords.nd != 2:
        raise Exception("conf must be a sequence of 3 dimensional coordinates")
    if coords.dimensions[1] == 3:
        stride1 = coords.strides[0]/sizeof(float)
        stride2 = coords.strides[1]/sizeof(float)
    else:
        stride1 = coords.strides[1]/sizeof(float)
        stride2 = coords.strides[0]/sizeof(float)

    if indices is None:
        numindices = len(coords)
        noindices = 0
    else:
        numindices = len(indices)
        idx = <int*>(indices.data)
        noindices = 1
    
    if not numpy.allclose(clipplane,0):
        clipping = 1
        clip = <float*>(clipplane.data)
        excl = <int*>(exclude.data)
        numexclude = len(exclude)
    else: clipping = 0

    for i from 0<=i<numindices:
        if noindices == 0: index = i
        else: index = idx[i]
        x = vert[index*stride1+stride2*0]
        y = vert[index*stride1+stride2*1]
        z = vert[index*stride1+stride2*2]
        r = rad[index]
        if (clipping == 1) and (x*clip[0]+y*clip[1]+z*clip[2]+clip[3]) < 0: continue
        glNormal3f(1,1,r)
        glVertex3f(x, y, z)
        glNormal3f(-1,+1, r)
        glVertex3f(x, y, z)
        glNormal3f(-1,-1, r)
        glVertex3f(x, y, z)
        glNormal3f(+1,-1, r)
        glVertex3f(x, y, z)
    # Draw those excluded from clipping
    if clipping == 1:
        for i from 0<=i<numexclude:
            index = excl[i]
            x = vert[index*stride1+stride2*0]
            y = vert[index*stride1+stride2*1]
            z = vert[index*stride1+stride2*2]
            r = rad[index]
            glNormal3f(+1,+1, r)
            glVertex3f(x, y, z)
            glNormal3f(-1,+1, r)
            glVertex3f(x, y, z)
            glNormal3f(-1,-1, r)
            glVertex3f(x, y, z)
            glNormal3f(+1,-1, r)
            glVertex3f(x, y, z)

def MolDrawHalo(ndarray coords, ndarray radii, float halo_size, ndarray clipplane, ndarray exclude, ndarray indices = None):
    cdef int i, index, numindices, numexclude
    cdef int stride1, stride2
    cdef int *idx, *excl
    cdef float *vert, *rad, *clip
    cdef int noindices, clipping
    cdef float r, s
    
    vert = <float*>(coords.data)
    rad = <float*>(radii.data)
    s = halo_size * 2.5
    
    if coords.nd != 2:
        raise Exception("conf must be a sequence of 3 dimensional coordinates")
    if coords.dimensions[1] == 3:
        stride1 = coords.strides[0]/sizeof(float)
        stride2 = coords.strides[1]/sizeof(float)
    else:
        stride1 = coords.strides[1]/sizeof(float)
        stride2 = coords.strides[0]/sizeof(float)

    if indices is None:
        if coords.dimensions[1] == 3: numindices = coords.dimensions[0]
        else: numindices = coords.dimensions[1]
        noindices = 0
    else:
        numindices = len(indices)
        idx = <int*>(indices.data)
        noindices = 1
    
    if not numpy.allclose(clipplane,0):
        clipping = 1
        clip = <float*>(clipplane.data)
        excl = <int*>(exclude.data)
        numexclude = len(exclude)
    else: clipping = 0

    for i from 0<=i<numindices:
        if noindices == 0: index = i
        else: index = idx[i]

        x = vert[index*stride1+stride2*0]
        y = vert[index*stride1+stride2*1]
        z = vert[index*stride1+stride2*2]
        r = rad[index]
        if clipping == 1 and (x*clip[0]+y*clip[1]+z*clip[2]+clip[3]) < 0: continue

        glMultiTexCoord2fARB(GL_TEXTURE1_ARB, r+s, (r+s)*(r+s) / (s*s+2*r*s))

        glTexCoord2f(+1,+1)
        glVertex3f(x, y, z)
        glTexCoord2f(-1,+1)
        glVertex3f(x, y, z)
        glTexCoord2f(-1,-1)
        glVertex3f(x, y, z)
        glTexCoord2f(+1,-1)
        glVertex3f(x, y, z)
    # Draw those excluded from clipping
    if clipping == 1:
        for i from 0<=i<numexclude:
            index = excl[i]
            x = vert[index*stride1+stride2*0]
            y = vert[index*stride1+stride2*1]
            z = vert[index*stride1+stride2*2]
            r = rad[index]
            glMultiTexCoord2fARB(GL_TEXTURE1_ARB, r+s, (r+s)*(r+s) / (s*s+2*r*s))

            glTexCoord2f(+1,+1)
            glVertex3f(x, y, z)
            glTexCoord2f(-1,+1)
            glVertex3f(x, y, z)
            glTexCoord2f(-1,-1)
            glVertex3f(x, y, z)
            glTexCoord2f(+1,-1)
            glVertex3f(x, y, z)

def MolDrawOnTexture(ndarray coords, ndarray radii, ndarray textures, int CSIZE, ndarray indices = None):
    cdef int i, index, numindices
    cdef int stride1, stride2
    cdef int *idx
    cdef float *vert, *rad, *tex
    cdef int noindices
    cdef float h, Xm, Xp, Ym, Yp, tx, ty

    vert = <float*>(coords.data)
    rad = <float*>(radii.data)
    tex = <float*>(textures.data)

    if coords.nd != 2:
        raise Exception("conf must be a sequence of 3 dimensional coordinates")
    if coords.dimensions[1] == 3:
        stride1 = coords.strides[0]/sizeof(float)
        stride2 = coords.strides[1]/sizeof(float)
    else:
        stride1 = coords.strides[1]/sizeof(float)
        stride2 = coords.strides[0]/sizeof(float)

    if indices is None:
        if coords.dimensions[1] == 3: numindices = coords.dimensions[0]
        else: numindices = coords.dimensions[1]
        noindices = 0
    else:
        numindices = len(indices)
        idx = <int*>(indices.data)
        noindices = 1

    h = 0
    Xm = -1.0 - 1.0/CSIZE
    Xp = 1.0 + 1.0/CSIZE
    Ym = Xm
    Yp = Xp

    for i from 0<=i<numindices:
        if noindices == 0: index = i
        else: index = idx[i]

        tx = tex[index*2+0]
        ty = tex[index*2+1]

        glColor3f(myrand(), myrand(), myrand())

        glMultiTexCoord4fARB(GL_TEXTURE1_ARB, vert[index*stride1+stride2*0],vert[index*stride1+stride2*1],vert[index*stride1+stride2*2], rad[index])
        glTexCoord2f(Xm,Ym); glVertex2f(-h+tx,      -h+ty)
        glTexCoord2f(Xp,Ym); glVertex2f(-h+tx+CSIZE,-h+ty)
        glTexCoord2f(Xp,Yp); glVertex2f(-h+tx+CSIZE,-h+ty+CSIZE)
        glTexCoord2f(Xm,Yp); glVertex2f(-h+tx,      -h+ty+CSIZE)

def molDrawSticks(ndarray coords, ndarray bonds, ndarray colors, ndarray clipplane, ndarray indices = None):
    cdef int i, index, nbonds, numindices, numexclude
    cdef int stride1, stride2
    cdef int *idx, *excl, *bnds
    
    cdef int clipping
    cdef float *vert, *col, *clip
    cdef float x, y, z
    cdef int noindices
    vert = <float*>(coords.data)
    col = <float*>(colors.data)
    bnds = <int*>(bonds.data)

    if coords.nd != 2:
        raise Exception("conf must be a sequence of 3 dimensional coordinates")
    if coords.dimensions[1] == 3:
        stride1 = coords.strides[0]/sizeof(float)
        stride2 = coords.strides[1]/sizeof(float)
    else:
        stride1 = coords.strides[1]/sizeof(float)
        stride2 = coords.strides[0]/sizeof(float)

    nbonds = len(bonds)

    if indices is None:
        if coords.dimensions[1] == 3: numindices = coords.dimensions[0]
        else: numindices = coords.dimensions[1]
        noindices = 0
    else:
        numindices = len(indices)
        idx = <int*>(indices.data)
        noindices = 1

    #if not numpy.allclose(clipplane,0):
    #    clipping = 1
    #    clip = <float*>(clipplane.data)
    #    excl = <int*>(exclude.data)
    #    numexclude = len(exclude)
    #else: clipping = 0

    for i from 0<=i<nbonds:
        #if noindices == 0: index = i
        #else: index = idx[i]

        index = bnds[i*2+0]
        x = vert[index*stride1+stride2*0]
        y = vert[index*stride1+stride2*1]
        z = vert[index*stride1+stride2*2]
        #if clipping == 1 and (x*clip[0]+y*clip[1]+z*clip[2]+clip[3]) < 0: continue
        glColor3f(col[index*3+0],col[index*3+1],col[index*3+2])
        glVertex3f(x, y, z)
        index = bnds[i*2+1]
        x = vert[index*stride1+stride2*0]
        y = vert[index*stride1+stride2*1]
        z = vert[index*stride1+stride2*2]
        glColor3f(col[index*3+0],col[index*3+1],col[index*3+2])
        glVertex3f(x, y, z)

