import sys

import numpy as np

from OpenGL.GL import *
from OpenGL.GLU import *

from drawable import Drawable

from copy import copy

class Mesh( Drawable ) :
	def __init__( self , f = None ) :
		Drawable.__init__( self )

		self.verts , self.v , self.n , self.t , self.ev , self.et , self.tn = [[]] * 7

		self.volume_size = 0
		self.volume = np.zeros( 0 , np.float32 )
		self.normal = np.zeros( 0 , np.float32 )

		if file : self.fromFile( f )

	def draw( self ) :
#        glDisable( GL_CULL_FACE )

		glEnableClientState(GL_VERTEX_ARRAY)
		glEnableClientState(GL_NORMAL_ARRAY)

		glVertexPointer( 3 , GL_FLOAT , 0 , self.v )
		glNormalPointer(     GL_FLOAT , 0 , self.n )

		glDrawElements( GL_TRIANGLES , len(self.t) , GL_UNSIGNED_INT , self.t )

		glDisableClientState(GL_VERTEX_ARRAY)
		glDisableClientState(GL_NORMAL_ARRAY)

#        glEnable( GL_CULL_FACE )

	def create_volume( self , p ) :

		j = 0

		for i in range(0,len(self.et),2) :
			vid1 = self.ev[i  ]*3
			vid2 = self.ev[i+1]*3

			v1 = np.array( self.verts[vid1:vid1+3] , np.float32 )
			v2 = np.array( self.verts[vid2:vid2+3] , np.float32 )

			dp = p - (v1+v2)/2.0

			tid1 = self.et[i  ]
			tid2 = self.et[i+1]

			d1 = np.dot( self.tn[tid1] , dp )
			d2 = np.dot( self.tn[tid2] , dp )

			if d1 * d2 < 0 : 
				w1 = v1 + (v1-p)*2
				w2 = v2 + (v2-p)*2

				if d1 < 0 : 
					self.volume[j   :j+ 3] = v1
					self.volume[j+ 3:j+ 6] = v2
					self.volume[j+ 6:j+ 9] = w2

					self.volume[j+ 9:j+12] = w2
					self.volume[j+12:j+15] = w1
					self.volume[j+15:j+18] = v1
				else :
					self.volume[j   :j+ 3] = w2
					self.volume[j+ 3:j+ 6] = v2
					self.volume[j+ 6:j+ 9] = v1

					self.volume[j+ 9:j+12] = v1
					self.volume[j+12:j+15] = w1
					self.volume[j+15:j+18] = w2

#        for i in range(0,t,3) :
#            self.

#                if d1 > 0 :
#                    normal = self.tn[tid1]
#                else :
#                    normal = self.tn[tid2]

#                self.normal[j   :j+ 3] = normal
#                self.normal[j+ 3:j+ 6] = normal
#                self.normal[j+ 6:j+ 9] = normal
#                self.volume[j+ 9:j+12] = normal
#                self.volume[j+12:j+15] = normal
#                self.volume[j+15:j+18] = normal

				j += 18 

		self.volume_size = j
#        

	def draw_volume( self , visible = False ) :
		if len(self.volume) == 0 : return

		if visible :
#            glDisable( GL_CULL_FACE )

			glEnable( GL_BLEND )
			glBlendFunc( GL_ONE_MINUS_SRC_ALPHA , GL_ONE )


		glEnableClientState(GL_VERTEX_ARRAY)
#        glEnableClientState(GL_NORMAL_ARRAY)

		glVertexPointer( 3 , GL_FLOAT , 0 , self.volume )
#        glNormalPointer(     GL_FLOAT , 0 , self.normal )


		glDrawArrays( GL_TRIANGLES , 0 , self.volume_size/3 )

		glDisableClientState(GL_VERTEX_ARRAY)
#        glDisableClientState(GL_NORMAL_ARRAY)

		if visible :
			glDisable( GL_BLEND )

#            glEnable( GL_CULL_FACE )

	def fromFile( self , path ) :
		f = open(path,'r')

		try :
			self.verts      = self._readVertices ( f )
			self.v , self.n = self._readPoints   ( f , self.verts )
			self.t          = self._readTriangels( f )
			self.ev,self.et = self._readEdges    ( f )
		except IOError as (errno, strerror):
			print path , " I/O error({0}): {1}".format(errno, strerror)
		except ValueError as e :
			print "Could not convert data: " , e

		self.verts = np.array( self.verts , np.float32 )
		self.v     = np.array( self.v     , np.float32 )
		self.n     = np.array( self.n     , np.float32 )
		self.t     = np.array( self.t     , np.uint32  )
		self.ev    = np.array( self.ev    , np.uint32  )
		self.et    = np.array( self.et    , np.uint32  )
		self.tn    = self.calculate_triangles_normals( self.n , self.t )
		self.an    = self.normals_to_arrays( self.n )

		self.volume.resize( len(self.t)*3*2 )
		self.normal.resize( len(self.t)*3*2 )

	def calculate_triangles_normals( self , ns , ts ) :
		tn = []

		for i in range(0,len(ts),3) :
			n = np.array((0,0,0),np.float32)
			for k in ts[i:i+3] :
				n += np.array( ns[k*3:k*3+3] , np.float32 )
			tn.append( n/3.0 )

		return tn

	def normals_to_arrays( self , n ) :
		an = []
		for i in range(0,len(n),3) :
			an.append( np.array( n[i:i+3] , np.float32 ) )
		return an

	def _readVertices( self , f ) :
		v = []
		for i in xrange(int(f.readline())) :
			v += map( float , f.readline().split(' ') )
		return v

	def _readPoints( self , f , verts ) :
		v , n = [] , []
		for i in xrange(int(f.readline())) :
			l = f.readline().split(' ')
			ind = int(l[0])*3
			v += verts[ind:ind+3]
			n += l[1:]
		return v , n

	def _readTriangels( self , f ) :
		t = []
		for i in xrange(int(f.readline())) :
			t += map( int , f.readline().split(' ') )
		return t

	def _readEdges( self , f ) :
		ev , et = [] , []
		for i in xrange(int(f.readline())) :
			l = map( int , f.readline().split(' ') )
			ev += l[:2]
			et += l[2:]
		return ev , et

