import c4d
from c4d.modules import mograph as mo
from c4d.utils import GeRayCollider
import c4d.utils as UT
import time

#array of points from plane to array of points

def main():
    #GET DOC DATA =================================================================================
    doc = c4d.documents.GetActiveDocument ()
    ctime = doc.GetTime() # Save current time

    # Get FPS and minimum + maximum frames
    fps = doc.GetFps()
    start = doc.GetMinTime().GetFrame(fps)
    end  = doc.GetMaxTime().GetFrame(fps)

    collisionMesh =  doc.SearchObject('bell')
    cameraStartRay  = doc.SearchObject('Camera')
    endrays = doc.SearchObject('CorrectionEndPlane')

    endRaysmeshPolys= endrays.GetAllPolygons()

    #MESH DATA==================================================================================
    meshPolysIndex = collisionMesh.GetAllPolygons()
    meshTag = collisionMesh.GetTag(c4d.Tpolygonselection)
    tag_baseSelect = meshTag.GetBaseSelect() #update the tag
    tag_baseSelect.DeselectAll()

    #RAY DATA =========================================================================
    frame = 0

    for f in range(start,end):
        doc.SetTime(c4d.BaseTime(f, doc.GetFps()))

        # evaluate the scene
        doc.ExecutePasses(None, True, True, True, c4d.BUILDFLAGS_NONE)

        c4d.GeSyncMessage(c4d.EVMSG_TIMECHANGED)# make the timeline, timeslider etc. do an instant redraw.)
        c4d.EventAdd(c4d.EVENT_ANIMATE)

        cameraStartRayPos = cameraStartRay.GetMg().off

        #get centre for each polygone  for the end ray plane
        def poly_center(op, polygon):
            # Determine whether you passed an index or a Polygon object
            if not isinstance(polygon, c4d.CPolygon):
                polygon = op.GetPolygon(polygon)
            indices = [polygon.a, polygon.b, polygon.c]
            # Determine whether the polygon is a triangle or a quadrangle
            if polygon.c != polygon.d:
                indices.append(polygon.d)
            # Gather a list of the points' Vectors
            vectors = list(map(lambda i: op.GetPoint(i), indices))
            # Compute the average of the Vectors
            return sum(vectors) / len(vectors)

        endRayCentrePositions = []
        for poly in endRaysmeshPolys:
            positions = poly_center(endrays,poly)
            endRayCentrePositions.append(positions)

            #======test ray lines are correct by drawing splines in the viewport ===========
            #points = [cameraStartRayPos,positions]
            #newCurve = UT.FitCurve(points,0.0,None)
            #doc.InsertObject(newCurve,checknames=True)

        #RAY STUFF================================================================================
        ray = GeRayCollider() #create a raycollider
        if not ray.Init(collisionMesh):
            raise RuntimeError('GeRayCollider could not be initialized.')

        hitFaceID = []
        endraysMg = endrays.GetMg()
        collisionMg = collisionMesh.GetMg()
        for endPos in endRayCentrePositions:
            p1 = cameraStartRayPos * ~collisionMg #start position = camera position x collision mesh global pos
            endPos = endPos  * endraysMg * ~collisionMg #endpos = endpositions x global position of end rays x global position of collision mesh
            #print(endPos)
            direction = (endPos - p1).GetNormalized()
            length = (endPos - p1).GetLength()

            ray.Intersect(p1,direction,length) #START,END, DISTANCE
            posIntersect = ray.GetNearestIntersection()
            if(posIntersect is not None): #get nearest ray hit from cameras point
                pos = posIntersect #store the ray hit
                hit = pos["face_id"] #store the polygon face it hits
                hitFaceID.append(hit) #store it in a list

        deleteDupFaceIDs = list(dict.fromkeys(hitFaceID)) #delete all duplications of the same face
        #print(deleteDupFaceIDs)
        selected  = collisionMesh.GetPolygonS() # returns what is currently selected of a particular mesh

        #select the hit polys=====================================================
        for poly in deleteDupFaceIDs:
            tag_baseSelect.Select(poly) # reflect that in the selection tag.

        c4d.DrawViews()
        c4d.EventAdd(c4d.EVENT_ANIMATE)
        frame += 1

    #only add a tag for the selection at the last frame

if __name__=='__main__':
    main()
    print("Exit")