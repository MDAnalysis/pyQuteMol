
import numpy

def Area(a, b, c):
    v = numpy.cross(b-a,c-a)
    return numpy.sqrt(numpy.dot(v,v))*0.5

class OctaMapSamp:
    def __init__(self):
        self.size = 0
        self.dir = None
        self.dirrot = None

        self.weight = None

    def nsamp(self):
        return len(self.dir)

    def DuplicateTexels(self, t, s, tx, ty):
        e=self.size - 1
        # four corners
        k0=(tx+  (ty  )*s)*3
        k1=(tx+e+(ty  )*s)*3
        k2=(tx+e+(ty+e)*s)*3
        k3=(tx+  (ty+e)*s)*3
        t[k0  ]=t[k1  ]=t[k2  ]=t[k3  ]
        t[k0+1]=t[k1+1]=t[k2+1]=t[k3+1]
        t[k0+2]=t[k1+2]=t[k2+2]=t[k3+2]

        # sides
        for i in range(1,size/2):
            k0a=(tx    + (ty +i  )*s)*3
            k0b=(tx    + (ty +e-i)*s)*3
            k1a=(tx+e  + (ty +i  )*s)*3
            k1b=(tx+e  + (ty +e-i)*s)*3
            k2a=(tx+i  + (ty     )*s)*3
            k2b=(tx+e-i+ (ty     )*s)*3
            k3a=(tx+i  + (ty +e  )*s)*3
            k3b=(tx+e-i+ (ty +e  )*s)*3

            t[k0a+0]=t[k0b+0]; t[k1a+0]=t[k1b+0]; t[k2a+0]=t[k2b+0]; t[k3a+0]=t[k3b+0];
            t[k0a+1]=t[k0b+1]; t[k1a+1]=t[k1b+1]; t[k2a+1]=t[k2b+1]; t[k3a+1]=t[k3b+1];
            t[k0a+2]=t[k0b+2]; t[k1a+2]=t[k1b+2]; t[k2a+2]=t[k2b+2]; t[k3a+2]=t[k3b+2];

    def FillTexture(self, t, s, tx, ty, cr, cg, cb):
        for y in range(self.size):
            for x in range(self.size):
                k=(x+tx+(y+ty)*s)*3
                p=dir[ Index( x , y ) ]

                q=(p+numpy.array(1,1,1))/2.0*255.0
                t[k]= q[0]
                t[k+1]= q[1]
                t[k+2]= q[2]

    def Index(self,x, y):
        return x+y*self.size

    def Smooth(self,t, s, tx, ty):
        size = self.size
        oldvalue = numpy.zeros(size*size*6)
        # copy old values
        for y in range(0,size*2):
            for x in range(0,size*3):
                k=(x+tx+(y+ty)*s)*3
                i= Index( x , y )
                oldvalue[i]=t[k]

        dy=size, dx=1;
        e=size-1;
        # smooth old values
        for y in range(size):
            for x in range(size):
                i= Index( x , y )
                TH=2
                sum=oldvalue[i]
                ddiv=1
                w=0

                if (y!=0):  w=oldvalue[i-dy]
                else:       w=oldvalue[ Index( e-x , 1 ) ]
                if(w>TH):
                    sum+=w
                    ddiv+=1

                if (x!=0):  w=oldvalue[i-dx]
                else:       w=oldvalue[ Index( 1 , e-y ) ]
                if(w>TH):
                    sum+=w
                    ddiv+=1

                if (y!=e):  w=oldvalue[i+dy]
                else:       w=oldvalue[ Index( e-x ,e-1 ) ]
                if(w>TH):
                    sum+=w
                    ddiv+=1

                if (x!=e):  w=oldvalue[i+dx]
                else:       w=oldvalue[ Index( e-1 , e-y ) ]
                if(w>TH):
                    sum+=w
                    ddiv+=1

                sum=(sum+ddiv/2)/ddiv
                k=(x+tx+(y+ty)*s)*3
                t[k]=t[k+1]=t[k+2]=sum

    def SetSize(self,_size):
        self.size=_size
        self.initMap()
        self.ComputeWeight()

    def getDir(self, x, y):
        fs=float(self.size)-1
        #create point -
        p = numpy.array((x*2./fs-1.,y*2./fs-1,0))
        ax=numpy.abs(p[0]); ay=numpy.abs(p[1]); az=1
        if (ax+ay>1.0):
            p = numpy.array((numpy.sign(p[0])*(1-ay),numpy.sign(p[1])*(1-ax), 0))
            az=-1
        p[2]=(1-ax-ay)*az
        # Normalize
        p /= numpy.linalg.norm(p)
        return p

    def initMap(self):
        size = self.size
        dir = self.dir = numpy.zeros((size*size, 3))

        for y in range(size):
            for x in range(size):
                dir[self.Index(x,y)]=self.getDir(x,y)

    def ComputeWeight(self):
        size = self.size
        getDir = self.getDir
        weight = self.weight = numpy.zeros((size*size))
        k = 0
        for y in range(size):
            for x in range(size):
                h=0.5
                p00=getDir(x-h,y-h)
                p01=getDir(x-h,y+0)
                p02=getDir(x-h,y+h)
                p10=getDir(x+0,y-h)
                p11=getDir(x+0,y+0)
                p12=getDir(x+0,y+h)
                p20=getDir(x+h,y-h)
                p21=getDir(x+h,y+0)
                p22=getDir(x+h,y+h)

                tota=0; c=0; e=size-1

                if ( (x!=0) and (y!=0) ):
                    tota+=Area( p00, p10, p01 )
                    tota+=Area( p10, p11, p01 )
                    c+=1
                if ( (x!=0) and (y!=e) ):
                    tota+=Area( p01, p11, p12 )
                    tota+=Area( p01, p12, p02 )
                    c+=1
                if ( (x!=e) and (y!=0) ):
                    tota+=Area( p10, p20, p21 )
                    tota+=Area( p21, p11, p10 )
                    c+=1
                if ( (x!=e) and (y!=e) ):
                    tota+=Area( p11, p21, p12 )
                    tota+=Area( p21, p22, p12 )
                    c+=1
                weight[k]=1.0/(tota*4/c)
                k+=1

    def TotTexSizeX(self): return self.size
    def TotTexSizeY(self): return self.size

octamap = OctaMapSamp()
