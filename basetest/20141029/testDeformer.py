##############################################################################
'''
testDeformer.py

NOTE: There is a significant speed hit when using a python plugin versus a compiled C plugin.  The benefit is that this python plugin should work on any OS (Win/ Mac/ Linux) and Maya version (8.5+).

NOTE: Tested on Win (32/ 64) and Linux for Maya 8.5, 2008, +
'''
##############################################################################

import math, sys

import maya.cmds
import maya.OpenMaya as OpenMaya
import maya.OpenMayaMPx as OpenMayaMPx


kPluginNodeTypeName = "testDeformer"


testDeformerID = OpenMaya.MTypeId( 0x7269b )


#==================================================

class testDeformer( OpenMayaMPx.MPxDeformerNode ):
	#----------------------------------------

	driver_mesh = OpenMaya.MObject()
	initialized_data = OpenMaya.MObject()
	vert_map = OpenMaya.MObject()	
	
	
	#==================================================
	# constructor
	def __init__(self):
		OpenMayaMPx.MPxDeformerNode.__init__(self)
	

	
	#==================================================
	# deform
	def deform( self, data, iter, localToWorldMatrix, mIndex ):

		initialized_mapping = data.inputValue( self.initialized_data ).asShort();
		
		if( initialized_mapping == 1 ):
			self.initVertMapping(data, iter, localToWorldMatrix, mIndex)
			initialized_mapping = data.inputValue( self.initialized_data ).asShort()
	
		if( initialized_mapping == 2 ): 
	
			envelope = OpenMayaMPx.cvar.MPxDeformerNode_envelope
			envelopeHandle = data.inputValue( envelope )
			env = envelopeHandle.asFloat()
			
			vertMapArrayData  = data.inputArrayValue( self.vert_map )
			
			meshAttrHandle = data.inputValue( self.driver_mesh )
			meshMobj = OpenMaya.MObject()
			
			meshMobj = meshAttrHandle.asMesh()
			vertIter = OpenMaya.MItMeshVertex( meshMobj )
			
			while( iter.isDone() == False ):
				weight = self.weightValue( data, mIndex, iter.index() ) #//painted weight
				ww = weight * env;
					
				if ( ww != 0 ): 
					vertMapArrayData.jumpToElement( iter.index() )
					index_mapped = vertMapArrayData.inputValue().asInt() 
					if( index_mapped >= 0 ): 
						util = OpenMaya.MScriptUtil()   
						prevInt = util.asIntPtr()   
					
						vertIter.setIndex( index_mapped, prevInt )
						
						mappedPt = OpenMaya.MPoint()
						mappedPt = vertIter.position( OpenMaya.MSpace.kWorld )
					
						iterPt = OpenMaya.MPoint()
						iterPt = iter.position() * localToWorldMatrix
						
						pt = OpenMaya.MPoint()
						pt = iterPt + ((mappedPt - iterPt) * ww )
						pt = pt * localToWorldMatrix.inverse() 
						iter.setPosition( pt )	
				
				iter.next()


	def initVertMapping( self, data, iter, localToWorldMatrix, mIndex):
		meshAttrHandle = data.inputValue( self.driver_mesh  )
		meshMobj = meshAttrHandle.asMesh()
		vertIter = OpenMaya.MItMeshVertex( meshMobj )
		vertIter.reset()
		count = iter.count()
		
		vertMapOutArrayData = data.outputArrayValue( self.vert_map )
		
		vertMapOutArrayBuilder = OpenMaya.MArrayDataBuilder( self.vert_map, count )
		allPts = OpenMaya.MPointArray()
		allPts.clear()
		
		i = 0
		while( iter.isDone() == False ):
			initIndexDataHnd = vertMapOutArrayBuilder.addElement( i )
			negIndex = -1
			
			initIndexDataHnd.setInt( negIndex )
			initIndexDataHnd.setClean()
			
			
			allPts.append( iter.position() * localToWorldMatrix )
			i = i+1
			iter.next()
			
		vertMapOutArrayData.set( vertMapOutArrayBuilder )
		
		while( vertIter.isDone() == False ):
			driver_pt = OpenMaya.MPoint()
			driver_pt = vertIter.position( OpenMaya.MSpace.kWorld )
			closest_pt_index = self.getClosestPt( driver_pt, allPts )
			
			snapDataHnd = vertMapOutArrayBuilder.addElement( closest_pt_index )
			snapDataHnd.setInt( vertIter.index() )
			
			snapDataHnd.setClean()
			vertIter.next()
		
		vertMapOutArrayData.set( vertMapOutArrayBuilder )
	
		tObj  =  self.thisMObject()
		
		setInitMode = OpenMaya.MPlug( tObj, self.initialized_data  )
		setInitMode.setShort( 2 ) 
	
		iter.reset()

	def getClosestPt( self, pt, points ):
		ptIndex=0
		currentDistance = 9e99
		furthestDistanceSoFar = 9e99
		for i in range( 0, points.length() ):
			currentDistance = pt.distanceTo( points[i] )
			if(currentDistance < furthestDistanceSoFar ):
				ptIndex = i 
				furthestDistanceSoFar = currentDistance
			
		return ( ptIndex )
	
	
#==================================================	
# creator
def nodeCreator():
	return OpenMayaMPx.asMPxPtr( testDeformer() )

#==================================================
# initializer
def nodeInitializer():
	numericAttr = OpenMaya.MFnNumericAttribute()
	polyMeshAttr = OpenMaya.MFnTypedAttribute()
	enumAttr = OpenMaya.MFnEnumAttribute()
	
	
	testDeformer.driver_mesh = polyMeshAttr.create( "vertSnapInput", "vsnpin", OpenMaya.MFnData.kMesh )
	polyMeshAttr.setStorable(False)
	polyMeshAttr.setConnectable(True)
	testDeformer.addAttribute( testDeformer.driver_mesh )
	testDeformer.attributeAffects( testDeformer.driver_mesh, OpenMayaMPx.cvar.MPxDeformerNode_outputGeom )

	testDeformer.initialized_data = enumAttr.create( "initialize", "inl" )
	enumAttr.addField(	"Off", 0)
	enumAttr.addField(	"Re-Set Bind", 1)	
	enumAttr.addField(	"Bound", 2)
	enumAttr.setKeyable(True)
	enumAttr.setStorable(True)
	enumAttr.setReadable(True)
	enumAttr.setWritable(True)
	enumAttr.setDefault(0)
	testDeformer.addAttribute( testDeformer.initialized_data )
	testDeformer.attributeAffects( testDeformer.initialized_data, OpenMayaMPx.cvar.MPxDeformerNode_outputGeom )	

	testDeformer.vert_map = numericAttr.create( "vtxIndexMap", "vtximp", OpenMaya.MFnNumericData.kLong )
	numericAttr.setKeyable(False)
	numericAttr.setArray(True)
	numericAttr.setStorable(True)
	numericAttr.setReadable(True)
	numericAttr.setWritable(True)
	testDeformer.addAttribute( testDeformer.vert_map )
	testDeformer.attributeAffects( testDeformer.vert_map, OpenMayaMPx.cvar.MPxDeformerNode_outputGeom  )

	maya.cmds.makePaintable( kPluginNodeTypeName, 'weights', attrType='multiFloat' )
	
	
#==================================================
# initialize the script plug-in
def initializePlugin(mobject):
	mplugin = OpenMayaMPx.MFnPlugin(mobject, "Erick Miller - Paul Thuriot", "1.0.1") 
	try:
		mplugin.registerNode( kPluginNodeTypeName, testDeformerID, nodeCreator, nodeInitializer, OpenMayaMPx.MPxNode.kDeformerNode )
	except:
		sys.stderr.write( "Failed to register node: %s\n" % kPluginNodeTypeName )

# uninitialize the script plug-in
def uninitializePlugin(mobject):
	mplugin = OpenMayaMPx.MFnPlugin(mobject)
	try:
		mplugin.deregisterNode( testDeformerID )
	except:
		sys.stderr.write( "Failed to unregister node: %s\n" % kPluginNodeTypeName )

		