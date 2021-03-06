
import sys
import time

import numpy as np
import numpy.linalg as la
import transformations as tr

from OpenGL.GL import *
from OpenGL.GLU import *

import math as m

if sys.platform.startswith('win'):
    timer = time.clock
else:
    timer = time.time

from camera import Camera
from robot import Robot
from plane import Plane

class Scene :
	def __init__( self , fovy , ratio , near , far , robot_files ) :
		self.fovy = fovy
		self.near = near 
		self.far = far
		self.ratio = ratio

		self.camera = None
		self.plane  = Plane( (2,2) )

		self.wall = Plane( (20,10) )
		self.mw = tr.rotation_matrix( -m.pi / 2.0 , (1,0,0) )
		self.mw = np.dot( self.mw , tr.translation_matrix( (0,3,0) ) )

		self.robot = Robot( robot_files )

		self.x = 0.0

		self.last_time = timer()

		self.plane_alpha = 65.0 / 180.0 * m.pi

		self.lpos = [ 1 ,-1 , 0 ]

		self._make_plane_matrix()

		self.draw_robot = True
		self.draw_sparks = True 
		self.draw_front = False
		self.draw_back = False

	def _make_plane_matrix( self ) :
		r = tr.rotation_matrix( self.plane_alpha , (0,0,1) )
		s = tr.scale_matrix( 1 )
		t = tr.translation_matrix( (-1.25,.7,.05) )

		self.m = np.dot( np.dot( t , s ) , r )
		self.im = la.inv( self.m )
		self.im[3] = [ 0 , 0 , 0 , 1 ]

	def gfx_init( self ) :
		self.camera = Camera( ( 2 , 1 ,  5 ) , ( 0 , 0 , 0 ) , ( 0 , 1 , 0 ) )

		self._update_proj()

		glEnable( GL_DEPTH_TEST )
		glEnable( GL_NORMALIZE )
		glEnable( GL_CULL_FACE )
		glEnable( GL_COLOR_MATERIAL )
		glColorMaterial( GL_FRONT , GL_AMBIENT_AND_DIFFUSE )

		self.robot.gfx_init()
		self.robot.create_volumes( self.lpos )

	def draw( self ) :
		self.time = timer()

		dt = self.time - self.last_time

		glMatrixMode(GL_MODELVIEW)
		glLoadIdentity()

		self.camera.look()

		self.lpos = [ m.sin(1/10.0)*.5 , m.cos(1/10.0)*.5 , 2 ]

#        self._set_lights()
		self.robot.create_volumes( self.lpos )

		self._draw_scene()

		self.robot.update( dt )

#        print dt

		self.x+=dt*.3

		self.last_time = self.time

	def _draw_scene( self ) :
		pos = np.dot( self.m , np.array( [ m.sin(self.x*7)*m.cos(self.x/3.0) , 0 , m.cos(self.x*5) , 1 ] ) )
		nrm = np.dot( self.m , np.array( [      0        ,-1 ,      0        , 0 ] ) )

		self.robot.resolve( pos , nrm )

		glClearStencil(0);
		glClear(GL_DEPTH_BUFFER_BIT|GL_STENCIL_BUFFER_BIT);

		glDisable(GL_DEPTH_TEST)
		glEnable(GL_STENCIL_TEST)
		glStencilFunc(GL_ALWAYS, 1, 1)
		glStencilOp(GL_KEEP, GL_KEEP, GL_REPLACE)

		glEnable(GL_CULL_FACE)
		glColorMask(0,0,0,0);
		glFrontFace(GL_CCW);
		self.plane.draw( self.m )

		glEnable(GL_DEPTH_TEST)

		glColorMask(1,1,1,1);
		glStencilFunc(GL_EQUAL, 1, 1);
		glStencilOp(GL_KEEP, GL_KEEP, GL_KEEP);

		glPushMatrix()
		glMultTransposeMatrixf( self.m )
		glScalef(1,-1,1)
		glMultTransposeMatrixf( self.im )

		glFrontFace(GL_CW);
		if self.draw_robot : self.robot.draw( self.draw_sparks )

		glPopMatrix();
		glFrontFace(GL_CCW);

		glDisable(GL_STENCIL_TEST)

		glEnable( GL_BLEND )
		glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

		glColor4f(.7,.7,.7,.85)

		glDisable( GL_CULL_FACE )
		self.plane.draw( self.m )

		glDisable( GL_BLEND )

		# ambinet pass
#        glColorMask(0,0,0,0)
		self._set_ambient()
		if self.draw_robot : self.robot.draw( self.draw_sparks )
		glColor4f(.1,.1,.1,1)
		self.wall.draw( self.mw )
		glColorMask(1,1,1,1)

		# lighting pass
		glPushAttrib(GL_ALL_ATTRIB_BITS)

		glClear(GL_STENCIL_BUFFER_BIT)
		glDepthMask(0);
		glColorMask(0,0,0,0);
		glEnable(GL_CULL_FACE);
		glEnable(GL_STENCIL_TEST);

		glEnable(GL_LIGHTING)
		glStencilMask(~0);
		glStencilFunc(GL_ALWAYS, 0, ~0);

		# Increment for front faces
		glCullFace(GL_BACK)
		glStencilOp(GL_KEEP,   # stencil test fail
                    GL_KEEP,   # depth test fail
                    GL_INCR);  # depth test pass

		self.robot.draw_volumes( cull = GL_BACK )

		# Decrement for back faces
		glCullFace(GL_FRONT);
		glStencilOp(GL_KEEP,   # stencil test fail
					GL_KEEP,   # depth test fail
					GL_DECR);  # depth test pass

		self.robot.draw_volumes( cull = GL_FRONT )

#        glClear(GL_STENCIL_BUFFER_BIT)
#        glColorMask(0, 0, 0, 0);
#        glDisable(GL_LIGHTING)
#        glStencilFunc(GL_ALWAYS, 0, ~0);
#        glStencilMask(~0);

#        glActiveStencilFaceEXT(GL_FRONT)
#        glStencilOp(GL_KEEP, GL_DECR_WRAP_EXT, GL_KEEP)
#        glActiveStencilFaceEXT(GL_BACK)
#        glStencilOp(GL_KEEP, GL_INCR_WRAP_EXT, GL_KEEP)
#        glCullFace(GL_NONE)

#        glEnable(GL_LIGHTING)
		glStencilFunc(GL_EQUAL, 0, ~0)
#        glActiveStencilFaceEXT(GL_FRONT)
#        glStencilOp(GL_KEEP, GL_KEEP, GL_KEEP)
#        glActiveStencilFaceEXT(GL_BACK)

		glStencilOp(GL_KEEP, GL_KEEP, GL_KEEP)
		glDepthFunc(GL_LEQUAL)
		glColorMask(1, 1, 1, 1)
		glDepthMask(1)

		glEnable(GL_CULL_FACE)
		glCullFace(GL_BACK)

		glEnable(GL_BLEND)
		glBlendFunc(GL_ONE,GL_ONE)

		self._set_diffuse()

		if self.draw_robot : self.robot.draw( self.draw_sparks )

		glColor4f(1,1,1,1)
		self.wall.draw( self.mw )

		glDisable(GL_BLEND)

		glPopAttrib()

		if self.draw_back  : self.robot.draw_volumes( cull = GL_FRONT )
		if self.draw_front : self.robot.draw_volumes( cull = GL_BACK  )

	def _update_proj( self ) :
		glMatrixMode(GL_PROJECTION)
		glLoadIdentity()
		gluPerspective( self.fovy , self.ratio , self.near , self.far )
		glMatrixMode(GL_MODELVIEW)

	def _set_lights( self ) :
		glEnable(GL_LIGHTING);
		glLightfv(GL_LIGHT0, GL_AMBIENT, [ 0.2 , 0.2 , 0.2 ] );
		glLightfv(GL_LIGHT0, GL_DIFFUSE, [ 0.9 , 0.9 , 0.9 ] );
		glLightfv(GL_LIGHT0, GL_SPECULAR,[ 0.3 , 0.3 , 0.3 ] );
		glLightfv(GL_LIGHT0, GL_POSITION, self.lpos );
		glEnable(GL_LIGHT0); 

	def _set_ambient( self ) :
		glEnable(GL_LIGHTING);
		glLightfv(GL_LIGHT0, GL_AMBIENT, [ 0.1 , 0.1 , 0.1 ] );
		glLightfv(GL_LIGHT0, GL_DIFFUSE, [ 0.0 , 0.0 , 0.0 ] );
		glLightfv(GL_LIGHT0, GL_SPECULAR,[ 0.0 , 0.0 , 0.0 ] );
		glLightfv(GL_LIGHT0, GL_POSITION, self.lpos );
		glEnable(GL_LIGHT0); 

	def _set_diffuse( self ) :
		glEnable(GL_LIGHTING);
		glLightfv(GL_LIGHT0, GL_AMBIENT , [ 0.0 , 0.0 , 0.0 ] );
		glLightfv(GL_LIGHT0, GL_DIFFUSE , [ 0.9 , 0.9 , 0.9 ] );
		glLightfv(GL_LIGHT0, GL_SPECULAR, [ 0.3 , 0.3 , 0.3 ] );
#        glLightf(GL_LIGHT0, GL_CONSTANT_ATTENUATION, 1.0)
#        glLightf(GL_LIGHT0, GL_LINEAR_ATTENUATION, 0.2)
#        glLightf(GL_LIGHT0, GL_QUADRATIC_ATTENUATION, 0.08)
		glLightfv(GL_LIGHT0, GL_POSITION, self.lpos );
		glEnable(GL_LIGHT0); 
						 
	def set_fov( self , fov ) :
		self.fov = fov
		self._update_proj()

	def set_near( self , near ) :
		self.near = near
		self._update_proj()

	def set_ratio( self , ratio ) :
		self.ratio = ratio
		self._update_proj()

	def set_screen_size( self , w , h ) :
		self.width  = w 
		self.height = h
		self.set_ratio( float(w)/float(h) )

	def mouse_move( self , df ) :
		self.camera.rot( *map( lambda x : -x*.2 , df ) )

	def key_pressed( self , mv ) :
		self.camera.move( *map( lambda x : x*.25 , mv ) )

