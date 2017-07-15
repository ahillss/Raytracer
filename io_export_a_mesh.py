"""
overall data layout:
nodes|primitives|triangles|vertices|materials|textures

individual data layout:
node(type/right/primtiveIndex/triangle,split/primitiveNum)
primitive(triangleIndices[primitiveNum])
triangle(vertexIndices[3],material)
vertex(px,py,pz,normal,texcoords[uvLayers],tangents[uvLayers],colors[colLayers])
material(color,(textureIndex,uvIndex)[])
texture(width/height,data[])
"""

bl_info = {
    "name": "A Mesh Exporter V2",
    "author": "me",
    "version": (1,0,0),
    "blender": (2,7,8),
    "location": "File > Export",
    "description": "Export a mesh",
    "warning": "",
    "wiki_url": "",
    "tracker_url": "",
    "category" : "Import-Export"}

import bpy,bmesh,bpy_extras,struct,os,mathutils,functools,base64,math,re,lzma,binascii,time

def runExporter(theWriter,filepath,useNormals,useTexcoords,useTangents,useColors,useMaterials,useTextures,useTransform,useSelected):
    startTime=time.time()
    
    #
    print("generating vertices...")

    #
    mes=do_meshes(useSelected,useNormals,useTexcoords,useTangents,useColors,useTransform,useMaterials,useTextures)

    #    
    mtrl_inds=dict([(n,i) for i,n in enumerate(mes["material_names"])])
    uv_inds=dict([(n,i) for i,n in enumerate(mes["uv_names"])])
    col_inds=dict([(n,i) for i,n in enumerate(mes["color_names"])])
    texMaxSlotNum=max([0]+[tex["slot"]+1 for ma in mes["materials"].values() for tex in ma["textures"]])
    imgsByName=dict([(re.sub("^//","",img.filepath),img) for img in bpy.data.images])
    imgs=list(set([imgsByName[tex["image"]] for ma in mes["materials"].values() for tex in ma["textures"]]))
    img_inds=dict([(re.sub("^//","",img.filepath),i) for i,img in enumerate(imgs)])
    
    #
    print("building kd-tree...")

    #
    kdtree=buildKdTree(mes["positions"],mes["indices"])

    #
    print("organising data...")

    #
    outNodeList=[]

    #generate outNodeList
    traverseStk=[kdtree["root"]]

    while len(traverseStk)>0:
        n=traverseStk.pop()
        n["index"]=len(outNodeList)
        outNodeList.append(n)

        if n["type"]!=3:
            traverseStk.append(n["right"])
            traverseStk.append(n["left"])

    #prims
    outPrimIndsTotalNum=0

    for n in outNodeList:
        if n["type"]==3:
            primInds=n["primInds"]
            primIndsNum=len(primInds)

            if primIndsNum==1:
                n["primIndsStart"]=primInds[0]
            elif primIndsNum>1:
                n["primIndsStart"]=outPrimIndsTotalNum
                outPrimIndsTotalNum+=primIndsNum
            else:
                n["primIndsStart"]=0

    #outTris
    outTris=[]

    for n in mes["material_names"]:
        ma=mes["materials"][n]
        inds=mes["indices"][ma["start"]:ma["end"]]

        for i in range(0,len(inds)//3):
            tri=[inds[i*3+j] for j in range(0,3)]+[mtrl_inds[n]]
            outTris.append(tri)
            

    #materials and textures
    outMtrls=[]
    
    for maName in mes["material_names"]:
        ma=mes["materials"][maName]
        outMtrlTexs=[None for i in range(0,texMaxSlotNum)]

        for tex in ma["textures"]:
            img_ind=img_inds[tex["image"]]
            uv_ind=uv_inds[tex["uv"]]
            outMtrlTexs[tex["slot"]]=[img_ind,uv_ind]
        
        outMtrl={"col":ma["color"],"texs":outMtrlTexs}
        outMtrls.append(outMtrl)
                
    #offsets
    outNodesOffset=6
    outNodeSizeOffset=2;
    outPrimsOffset=outNodesOffset+len(outNodeList)*outNodeSizeOffset
    outTrisOffset=outPrimsOffset+outPrimIndsTotalNum
    outTriSizeOffset=3

    if useMaterials:
        outTriSizeOffset+=1

    outVertsOffset=outTrisOffset+(mes["indices_num"]//3)*outTriSizeOffset
    outVertSizeOffset=3

    if useNormals:
        outVertSizeOffset+=1

    if useTexcoords:
        outVertSizeOffset+=len(mes["texcoords"])

    if useTangents:
        outVertSizeOffset+=len(mes["tangents"]) #*5

    if useColors:
        outVertSizeOffset+=len(mes["colors"])

    outMtrlOffset=outVertsOffset+mes["vertices_num"]*outVertSizeOffset
    outMtrlSizeOffset=0
    
    if useMaterials:
        outMtrlSizeOffset+=1

    if useTextures:
        outMtrlSizeOffset+=texMaxSlotNum*2
                    
    if useMaterials:
        for tri in outTris:
            tri[3]*=outMtrlSizeOffset
            tri[3]+=outMtrlOffset

    outImgOffset=outMtrlOffset+(len(mes["materials"])*outMtrlSizeOffset if useMaterials else 0)

    endOffset=outImgOffset
    
    imageOffsets=[]
    
    if useTextures:
        for img in imgs:
            imageOffsets.append(endOffset)
            endOffset+=1+len(img.pixels)//4

        for outMtrl in outMtrls:
            for tex in outMtrl["texs"]:
                if tex!=None:
                    tex[0]=imageOffsets[tex[0]]
   
    for n in outNodeList:
        n["index"]*=outNodeSizeOffset
        n["index"]+=outNodesOffset

        if n["type"]==3:
            primInds=n["primInds"]
            primIndsNum=len(primInds)

            if primIndsNum>1:
                n["primIndsStart"]+=outPrimsOffset

                for p in range(0,primIndsNum):
                    primInds[p]*=outTriSizeOffset
                    primInds[p]+=outTrisOffset

            elif primIndsNum==1:
                n["primIndsStart"]*=outTriSizeOffset
                n["primIndsStart"]+=outTrisOffset

    for i in range(0,len(outTris)):
        for j in range(0,3):
            outTris[i][j]*=outVertSizeOffset
            outTris[i][j]+=outVertsOffset

    #
    print("offsets {} {} {} {} {} {} {}".format(outNodesOffset,outPrimsOffset,outTrisOffset,outVertsOffset,outMtrlOffset,outImgOffset,endOffset))

    #
    print("nodes = {}".format(len(outNodeList)))
    print("triangles = {}".format(mes["indices_num"]//3))
    print("depth = {}".format(kdtree["depth"]))
    
    #
    print("writing file...")

    #
    #with lzma.open(filepath,"wb",format=lzma.FORMAT_ALONE) as fh:
    #with lzma_open_for_write(filepath) as fh:
    with theWriter(filepath) as fh:
    
        #write min bound
        fh.write(struct.pack('3f',*kdtree["min"]))

        #write max bound
        fh.write(struct.pack('3f',*kdtree["max"]))

        #
        print("file node offset = {}".format(fh.tell()/4))

        #write nodes
        for n in outNodeList:
            type=n["type"]

            if type==3: #on leaf
                primIndsNum=len(n["primInds"])
                fh.write(struct.pack('2I',(primIndsNum<<2)|type,n["primIndsStart"]))
            else: #on branch
                fh.write(struct.pack('If',(n["right"]["index"]<<2)|type,n["split"]))

        #
        print("file prims offset = {}".format(fh.tell()/4))

        #write prims
        for n in outNodeList:
            if n["type"]==3:
                primInds=n["primInds"]
                primIndsNum=len(primInds)

                if primIndsNum>1:
                    fh.write(struct.pack('{}I'.format(primIndsNum),*primInds))


        #
        print("file outTris offset = {}".format(fh.tell()/4))

        #write outTris
        for tri in outTris:
            fh.write(struct.pack('3I',*(tri[0:3])))

            if useMaterials or useTextures:
                fh.write(struct.pack('I',tri[3]))

        #
        print("file verts offset = {}".format(fh.tell()/4))

        #write vertices
        for i in range(0,mes["vertices_num"]):
            fh.write(struct.pack('3f',*mes["positions"][i*3:i*3+3]))

            if useNormals:
                fh.write(struct.pack('3Bx',*[int((x*0.5+0.5)*255.0) for x in mes["normals"][i*3:i*3+3]]))

            if useTexcoords:
                for k in mes["uv_names"]:
                    fh.write(struct.pack('2H',*[half_float_compress(x) for x in mes["texcoords"][k][i*2:i*2+2]]))

            if useTangents:
                for k in mes["uv_names"]:
                    fh.write(struct.pack('4B',*[int((x*0.5+0.5)*255.0) for x in mes["tangents"][k][i*4:i*4+4]]))
                    #fh.write(struct.pack('4f',*mes["tangents"][k][i*4:i*4+4]))

            if useColors:
                for k in mes["color_names"]:
                    fh.write(struct.pack('3Bx',*[int(x*255.0) for x in mes["colors"][k][i*3:i*3+3]]))


        #
        print("file mtrl offset = {}".format(fh.tell()/4))
        
        #write materials
        for outMtrl in outMtrls:
            if useMaterials:
                fh.write(struct.pack('4B',*[int(x*255.0) for x in outMtrl["col"]]))
            
            if useTextures:
                for tex in outMtrl["texs"]:
                    if tex==None:
                        fh.write(struct.pack('2I',0,0))
                    else:
                        fh.write(struct.pack('2I',tex[0],tex[1]))


        #
        print("file image offset = {}".format(fh.tell()/4))
        
        #
        if useTextures:
            for img in imgs:
                fh.write(struct.pack('2H',img.size[0],img.size[1]))
                fh.write(bytes([int(p*255) for p in img.pixels]))
                
        
        #
        print("file end offset = {}".format(fh.tell()/4))

    print('Exported to "%s", taking %.3f seconds.'%(filepath,time.time()-startTime))
    
############################################

class MyExportAMeshDat(bpy.types.Operator, bpy_extras.io_utils.ExportHelper):
    bl_idname = "my_export_mesh.dat";
    bl_label = "Export";
    bl_options = {'PRESET'};
    filename_ext = ".dat";

    useNormals=bpy.props.BoolProperty(name="normals",default=True)
    useTexcoords=bpy.props.BoolProperty(name="texcoords",default=False)
    useTangents=bpy.props.BoolProperty(name="tangents",default=False)
    useColors=bpy.props.BoolProperty(name="colors",default=False)
    useMaterials=bpy.props.BoolProperty(name="materials",default=False)
    useTextures=bpy.props.BoolProperty(name="textures",default=False)
    useTransform=bpy.props.BoolProperty(name="transform",default=True)
    useSelected=bpy.props.BoolProperty(name="selected",default=False)

    def execute(self, context):
        runExporter(lzma_open_for_write,self.filepath,self.useNormals,self.useTexcoords,self.useTangents,self.useColors,self.useMaterials,self.useTextures,self.useTransform,self.useSelected)
        return {'FINISHED'};

class MyExportAMeshPNG(bpy.types.Operator, bpy_extras.io_utils.ExportHelper):
    bl_idname = "my_export_mesh.png";
    bl_label = "Export";
    bl_options = {'PRESET'};
    filename_ext = ".png";

    useNormals=bpy.props.BoolProperty(name="normals",default=True)
    useTexcoords=bpy.props.BoolProperty(name="texcoords",default=False)
    useTangents=bpy.props.BoolProperty(name="tangents",default=False)
    useColors=bpy.props.BoolProperty(name="colors",default=False)
    useMaterials=bpy.props.BoolProperty(name="materials",default=False)
    useTextures=bpy.props.BoolProperty(name="textures",default=False)
    useTransform=bpy.props.BoolProperty(name="transform",default=True)
    useSelected=bpy.props.BoolProperty(name="selected",default=False)

    def execute(self, context):
        runExporter(png_open_for_write,self.filepath,self.useNormals,self.useTexcoords,self.useTangents,self.useColors,self.useMaterials,self.useTextures,self.useTransform,self.useSelected)
        return {'FINISHED'};

def menu_func(self, context):
    self.layout.operator(MyExportAMeshDat.bl_idname, text="Export A Mesh .dat");
    self.layout.operator(MyExportAMeshPNG.bl_idname, text="Export A Mesh .png");

def register():
    bpy.utils.register_module(__name__);
    bpy.types.INFO_MT_file_export.append(menu_func);

def unregister():
    bpy.utils.unregister_module(__name__);
    bpy.types.INFO_MT_file_export.remove(menu_func);

if __name__ == "__main__":
    register()

###########################################

def buildKdTree(verts,inds):
    bounds=getBounds(verts,inds)
    worldBound=getWorldBound(bounds)

    isectCost=80.0
    traversalCost=1.0
    emptyBonus=0.5

    maxPrims=1
    badRefines=0

    maxDepth=math.floor(0.5+ (8.0+1.3*math.floor(math.log2(len(bounds)))))

    rootNode={}

    buildStk=[{
        "node":rootNode,
        "primInds":[i for i in range(0,len(bounds))],
        "bmin":worldBound["min"].copy(),
        "bmax":worldBound["max"].copy(),
        "depth":maxDepth}]

    while len(buildStk)>0:
        cur=buildStk.pop()

        if len(cur["primInds"]) <=maxPrims or cur["depth"]==0:
            cur["node"]["type"]=3
            cur["node"]["primInds"]=cur["primInds"]
        else:
            primInds=cur["primInds"]
            bmin=cur["bmin"]
            bmax=cur["bmax"]
            edges=[None,None,None]
            diag=bmax-bmin
            bestAxis=-1
            bestOffset=-1
            bestCost=math.inf
            oldCost=isectCost*len(primInds)
            totalSa=2.0*(diag.x*diag.y+diag.x*diag.z+diag.y*diag.z)
            invTotalSa=1.0/totalSa
            retries=0
            axis=0 if diag.x>diag.y and diag.x>diag.z else (1 if diag.y>diag.z else 2)

            while True:
                #
                edges[axis]=[None for x in range(0,len(primInds)*2)]

                for i in range(0,len(primInds)):
                    v=primInds[i]
                    edges[axis][2*i]=  {"type":0,"val":bounds[v]["min"][axis],"primInd":v};
                    edges[axis][2*i+1]={"type":1,"val":bounds[v]["max"][axis],"primInd":v};

                edges[axis].sort(key=functools.cmp_to_key(edgeCompare))

                #
                nBelow=0
                nAbove=len(primInds)

                for i in range(0,2*len(primInds)):
                    if edges[axis][i]["type"]==1:
                        nAbove-=1

                    edget=edges[axis][i]["val"]

                    #
                    if edget>bmin[axis] and edget<bmax[axis]:
                        otherAxis0=(axis+1)%3
                        otherAxis1=(axis+2)%3
                        belowSa=2.0*(diag[otherAxis0]*diag[otherAxis1]+(edget-bmin[axis])*(diag[otherAxis0]+diag[otherAxis1]))
                        aboveSa=2.0*(diag[otherAxis0]*diag[otherAxis1]+(bmax[axis]-edget)*(diag[otherAxis0]+diag[otherAxis1]))
                        pBelow=belowSa*invTotalSa
                        pAbove=aboveSa*invTotalSa
                        eb=emptyBonus if (nAbove==0 or nBelow==0) else 0.0
                        cost=traversalCost+isectCost*(1.0-eb)*(pBelow*nBelow+pAbove*nAbove)

                        if cost < bestCost:
                            bestCost=cost
                            bestAxis=axis
                            bestOffset=i

                    #
                    if edges[axis][i]["type"]==0:
                        nBelow+=1

                #
                axis = (axis+1) % 3

                #
                if bestAxis != -1 or retries == 2:
                    break

                retries+=1

            #
            if bestCost > oldCost:
                badRefines+=1

            #
            if (bestCost>(4.0*oldCost) and len(primInds)<16) or bestAxis==-1 or badRefines==3:
                cur["node"]["type"]=3
                cur["node"]["primInds"]=cur["primInds"]
            else:
                split=edges[bestAxis][bestOffset]["val"]
                leftInds= [edges[bestAxis][i]["primInd"] for i in range(0, bestOffset) if edges[bestAxis][i]["type"]==0]
                rightInds=[edges[bestAxis][i]["primInd"] for i in range(bestOffset+1,2*len(primInds)) if edges[bestAxis][i]["type"]==1]

                #
                cur["node"]["right"]={}
                cur["node"]["left"]={}

                rightBuild={
                    "node":cur["node"]["right"],
                    "primInds":rightInds,
                    "bmin":cur["bmin"].copy(),
                    "bmax":cur["bmax"].copy(),
                    "depth":cur["depth"]-1}

                leftBuild={
                    "node":cur["node"]["left"],
                    "primInds":leftInds,
                    "bmin":cur["bmin"].copy(),
                    "bmax":cur["bmax"].copy(),
                    "depth":cur["depth"]-1}

                rightBuild["bmin"][bestAxis]=split
                leftBuild["bmax"][bestAxis]=split

                buildStk.append(rightBuild)
                buildStk.append(leftBuild)

                cur["node"]["type"]=bestAxis;
                cur["node"]["split"]=split;

    #
    return {"min":worldBound["min"],"max":worldBound["max"],"root":rootNode,"depth":maxDepth}

def getBounds(verts,inds):
    bounds=[]

    for tri in range(0,len(inds)//3):
        triInds=inds[tri*3:tri*3+3]
        triVerts=[verts[ind*3:ind*3+3] for ind in triInds]
        bmin=mathutils.Vector([min([vert[x] for vert in triVerts]) for x in range(0,3)])
        bmax=mathutils.Vector([max([vert[x] for vert in triVerts]) for x in range(0,3)])
        bounds.append({"min":bmin,"max":bmax})

    return bounds

def getWorldBound(bounds):
    bmin=mathutils.Vector([min([bound["min"][x] for bound in bounds]) for x in range(0,3)])
    bmax=mathutils.Vector([max([bound["max"][x] for bound in bounds]) for x in range(0,3)])
    return {"min":bmin,"max":bmax}

def edgeCompare(a,b):
    if a["val"]==b["val"]:
        return -1 if a["type"] < b["type"] else 1

    return -1 if a["val"]<b["val"] else 1

###########################################

def do_meshes(useSelected,useNormals, useTexcoords,useTangents, useColors, useTransform, useMaterials,useTextures):
    all=not (useSelected and bpy.context.selected_objects)
    objects=bpy.data.objects if all else bpy.context.selected_objects
    objects2=[ob for ob in objects if ob.type == "MESH"]

    #rotY(-pi/2)*rotX(-pi/2)=[0,0,-1, 0,1,0, 1,0,0]*[1,0,0, 0,0,1, 0,-1,0]=[0,1,0, 0,0,1, 1,0,0]

    fixModelMat=mathutils.Matrix([[0,1,0,0],[0,0,1,0],[1,0,0,0],[0,0,0,1]])
    fixNormalMat=mathutils.Matrix([[0,1,0],[0,0,1],[1,0,0]])

    vertsCount=0
    indsCount=0

    uvLayers=sorted(list(set([x.name for ob in objects2 for x in ob.data.uv_textures])))
    colLayers=sorted(list(set([x.name for ob in objects2 for x in ob.data.vertex_colors])))
    
    indsByMat={}

    out={"positions" : [],
         "normals" : [],
         "texcoords" : dict([(x.name,[]) for ob in objects2 for x in ob.data.uv_textures]) if useTexcoords and len(uvLayers)>0 else {},
         "tangents" : dict([(x.name,[]) for ob in objects2 for x in ob.data.uv_textures]) if useTangents and len(uvLayers)>0 else {},
         "colors" : dict([(x.name,[]) for ob in objects2 for x in ob.data.vertex_colors]) if useColors and len(colLayers)>0 else {},
         "indices" : [],
         "materials" : {}
        }

    #get object meshes
    for ob in objects2:
        worldMat=fixModelMat*ob.matrix_world if useTransform else fixModelMat
        normalMat=fixNormalMat*ob.matrix_world.to_quaternion().to_matrix() if useTransform else fixNormalMat

        myme=do_mesh(ob.data,worldMat,normalMat,useNormals,useTexcoords,useTangents,useColors)

        #combine vertices/indices and fill in missing vertices

        #positions
        for pos in myme["positions"]:
            out["positions"].extend(pos)

        #normals
        if useNormals:
            for nor in myme["normals"]:
                out["normals"].extend(nor)

        #texcoords
        if useTexcoords:
            #missing
            for uv in uvLayers:
                if uv not in myme["texcoords"].keys():
                    out["texcoords"][uv]=[0.0 for i in range(0,myme["vertices_num"]*2)]

            #has
            for uv,texs in myme["texcoords"].items():
                for tex in texs:
                    out["texcoords"][uv].extend(tex)

        #tangents
        if useTangents:
            #missing
            for uv in uvLayers:
                if uv not in myme["tangents"].keys():
                    out["tangents"][uv]=[0.0 for i in range(0,myme["vertices_num"]*4)]

            #has
            for uv,tgs in myme["tangents"].items():
                for tg in tgs:
                    out["tangents"][uv].extend(tg)

        #colors
        if useColors:
            #missing
            for c in colLayers:
                if c not in myme["colors"].keys():
                    out["colors"][c]=[1.0 for i in range(0,myme["vertices_num"]*3)]

            #has
            for c,cols in myme["colors"].items():
                for col in cols:
                    out["colors"][c].extend(col)

        #indices by material
        for ma,inds in myme["indices"].items():
            if ma not in indsByMat.keys():
                indsByMat[ma]=[]

            indsByMat[ma].extend([x+vertsCount for x in inds])
            indsCount+=len(inds)

        #
        vertsCount+=myme["vertices_num"]

    #
    mtrlNames=sorted([k for k in indsByMat.keys()])
    
    #
    out["material_names"]=mtrlNames
    out["uv_names"]=uvLayers
    out["color_names"]=colLayers
    out["indices_num"]=indsCount
    out["vertices_num"]=vertsCount
    
    #
    mtrlsByName=dict([(ma.name,ma) for ma in bpy.data.materials])
  
    for mtrlName in mtrlNames:
        ma_inds=indsByMat[mtrlName]
        
        indsStart=len(out["indices"])
        out["indices"].extend(ma_inds)
        indsEnd=len(out["indices"])
        
        col=[0.8,0.8,0.8,1.0]
        fresnel=0.1
        fresnel_factor=0.5
        emit=0.0
        roughness=0.5
        hardness=50.0
        intensity=0.5
        texs=[]

        if mtrlName!="":
            ma=mtrlsByName[mtrlName]
            col=[ma.diffuse_color[0],ma.diffuse_color[1],ma.diffuse_color[2],ma.alpha]
            fresnel=ma.diffuse_fresnel
            fresnel_factor=ma.diffuse_fresnel_factor
            emit=ma.emit
            roughness=ma.roughness
            hardness=ma.specular_hardness
            intensity=ma.specular_intensity
            
            for texSlotInd,texSlot in enumerate(ma.texture_slots):
                if (texSlot != None and texSlot.use and
                    texSlot.texture.type=='IMAGE' and
                    texSlot.texture_coords=='UV' and
                    texSlot.uv_layer != ''):
                
                    fn=re.sub("^//","",texSlot.texture.image.filepath)
                    uvName=texSlot.uv_layer
                    
                    texs.append({"slot":texSlotInd,"uv":uvName,"image":fn})
            
        out["materials"][mtrlName]={
            "start":indsStart,"end":indsEnd,
            "color":col,
            "fresnel":fresnel,
            "fresnel_factor":fresnel_factor,
            "emit":emit,
            "roughness":roughness,
            "hardness":hardness,
            "intensity":intensity,
            "textures":texs}
    

    #

    return out

def do_mesh(me,modelMat,normalMat,useNormals,useTexcoords, useTangents,useColors):

    me.update(calc_tessface=True)

    my_verts_num=0
    my_inds_num=0

    my_positions=[]
    my_normals=[]
    my_colors=dict([(x.name,[]) for x in me.vertex_colors])
    my_texcoords=dict([(x.name,[]) for x in me.uv_textures])
    my_tangents=dict([(x.name,[]) for x in me.uv_textures])
    my_matCols=[]

    my_vert_inds=dict()
    my_indices=dict([(ma.name if ma != None else "",[]) for ma in me.materials] if me.materials else [("",[])])
    orig_vert_inds=[]

    #
    faceTriVertInds=[] #[faceInd][triInd]=[0,1,2]/[0,2,3]
    faceTriNors=[] #[faceInd][triInd]=nor
    uvFaceTriTangs=[] #[uvInd][faceInd]=[tri0Tang,tri1Tang]
    vertFaceTris=[[] for x in me.vertices] #[vertInd]=[[faceInd,triInd,triVertInd],...]

    #face triangulation inds
    for faceInd, face in enumerate(me.tessfaces):
        if len(face.vertices)==4:
            #todo: find best split
            faceTriVertInds.append([[0,1,2],[0,2,3]])
        else:
            faceTriVertInds.append([[0,1,2]])

    #
    for faceInd, face in enumerate(me.tessfaces):
        for triInd,triVertInds in enumerate(faceTriVertInds[faceInd]):
            for i,triVertInd in enumerate(triVertInds):
                vertInd=face.vertices[triVertInd]
                vertFaceTris[vertInd].append([faceInd,triInd,i])

    #face triangulated nors
    for faceInd, face in enumerate(me.tessfaces):
        nors=[]

        for triVertInds in faceTriVertInds[faceInd]:
            pt1=me.vertices[face.vertices[triVertInds[0]]].co
            pt2=me.vertices[face.vertices[triVertInds[1]]].co
            pt3=me.vertices[face.vertices[triVertInds[2]]].co

            e1=pt2-pt1
            e2=pt3-pt1

            nor=e1.cross(e2)
            nor.normalize()
            nors.append(nor)

        faceTriNors.append(nors)

    #
    if useTangents:
        for uvInd,uvtex in enumerate(me.uv_textures):
            uvFaceTriTangs.append([])

            for faceInd, face in enumerate(me.tessfaces):
                tcs=[]
                pts=[]

                #
                uvFaceTriTangs[uvInd].append([])

                #face texcoords
                tcs.append(me.tessface_uv_textures[uvInd].data[faceInd].uv1)
                tcs.append(me.tessface_uv_textures[uvInd].data[faceInd].uv2)
                tcs.append(me.tessface_uv_textures[uvInd].data[faceInd].uv3)

                if len(face.vertices)==4:
                    tcs.append(me.tessface_uv_textures[uvInd].data[faceInd].uv4)

                #face verts
                for vertInd in face.vertices:
                    pts.append(me.vertices[vertInd].co)

                for triInd,triVertInds in enumerate(faceTriVertInds[faceInd]):
                    nor=faceTriNors[faceInd][triInd]
                    tang=calc_tangent_space(pts[triVertInds[0]],pts[triVertInds[1]],pts[triVertInds[2]], tcs[triVertInds[0]],tcs[triVertInds[1]],tcs[triVertInds[2]], nor)
                    uvFaceTriTangs[uvInd][faceInd].append(tang)


    #gen vert+index for each poly
    for faceInd, face in enumerate(me.tessfaces):
        # if useSelectedFaces and not face.select:
        #     continue

        #
        ma=me.materials[face.material_index] if me.materials else None
        maName=(ma.name if ma != None else "") if me.materials else ""
        face_cols = [[] for x in me.vertex_colors]

        #
        if useColors:
            for i,x in enumerate(me.vertex_colors):
                face_cols[i].append(me.tessface_vertex_colors[i].data[faceInd].color1)
                face_cols[i].append(me.tessface_vertex_colors[i].data[faceInd].color2)
                face_cols[i].append(me.tessface_vertex_colors[i].data[faceInd].color3)

                if len(face.vertices)==4:
                    face_cols[i].append(me.tessface_vertex_colors[i].data[faceInd].color4)

        if useTexcoords or useTangents:
            face_uvs = [[] for x in me.uv_textures]

            for i,x in enumerate(me.uv_textures):
                face_uvs[i].append(me.tessface_uv_textures[i].data[faceInd].uv1)
                face_uvs[i].append(me.tessface_uv_textures[i].data[faceInd].uv2)
                face_uvs[i].append(me.tessface_uv_textures[i].data[faceInd].uv3)

                if len(face.vertices)==4:
                    face_uvs[i].append(me.tessface_uv_textures[i].data[faceInd].uv4)

        #
        for triInd,triVertInds in enumerate(faceTriVertInds[faceInd]):
            for triVertInd in triVertInds:
                key=''
                cols=[]
                uvs=[]
                tangs=[]
                vertInd=face.vertices[triVertInd]

                pos=me.vertices[vertInd].co
                nor=None

                if useNormals or useTangents:
                    if face.use_smooth:
                        nor=mathutils.Vector((0,0,0))

                        for x in vertFaceTris[vertInd]:
                            faceInd2=x[0]
                            triInd2=x[1]
                            face2=me.tessfaces[faceInd2]
                            triVertInds2=faceTriVertInds[faceInd2][triInd2]

                            p0=me.vertices[face2.vertices[triVertInds2[x[2]%3]]].co
                            p1=me.vertices[face2.vertices[triVertInds2[(x[2]+1)%3]]].co
                            p2=me.vertices[face2.vertices[triVertInds2[(x[2]+2)%3]]].co

                            if face2.use_smooth:
                                nor2=faceTriNors[faceInd2][triInd2]
                                area=calc_triangle_area(p0,p1,p2)
                                angle=calc_vec_angle(p2-p0,p1-p0)
                                #nor=nor+nor2.xyz*angle*area
                                nor=nor+nor2.xyz*(angle+area)
                                #nor=nor+nor2.xyz*area
                                #nor=nor+nor2.xyz*angle

                        nor.normalize()

                    else:
                        nor=faceTriNors[faceInd][triInd]

                #
                key+=' %g %g %g'%(pos[0],pos[1],pos[2])

                if useNormals:
                    key+=' %g %g %g'%(nor[0],nor[1],nor[2])

                #
                if useColors:
                    for face_col in face_cols:
                        col=face_col[triVertInd]
                        cols.append(col)
                        key+=' %g %g %g'%(col[0],col[1],col[2])

                if useTexcoords:
                    for face_uv in face_uvs:
                        uv=face_uv[triVertInd]
                        uvs.append(uv)
                        key+=' %g %g'%(uv[0],uv[1])

                #
                if useTangents:
                    for uvInd,uvtex in enumerate(me.uv_textures):
                        #todo: check mirroring via dot( cross( T, B ), N ) ?
                        tang=None
                        triTang=uvFaceTriTangs[uvInd][faceInd][triInd]

                        if triTang.w==0:
                            tang=triTang
                        elif face.use_smooth:
                            avgTang=mathutils.Vector((0,0,0))

                            for x in vertFaceTris[vertInd]:
                                faceInd2=x[0]
                                triInd2=x[1]
                                face2=me.tessfaces[faceInd2]
                                tang2=uvFaceTriTangs[uvInd][faceInd2][triInd2]
                                triVertInds2=faceTriVertInds[faceInd2][triInd2]

                                p0=me.vertices[face2.vertices[triVertInds2[x[2]%3]]].co
                                p1=me.vertices[face2.vertices[triVertInds2[(x[2]+1)%3]]].co
                                p2=me.vertices[face2.vertices[triVertInds2[(x[2]+2)%3]]].co

                                if face2.use_smooth:
                                    if tang2.w==triTang.w and tang2.xyz.dot(triTang.xyz)>0:
                                        area=calc_triangle_area(p0,p1,p2)
                                        angle=calc_vec_angle(p2-p0,p1-p0)
                                        #avgTang=avgTang+tang2.xyz*angle*area
                                        avgTang=avgTang+tang2.xyz*(angle+area)

                            avgTang.normalize()
                            avgTang=orthog_vec(nor,avgTang)
                            tang=mathutils.Vector((avgTang.x,avgTang.y,avgTang.z,triTang.w))

                        else:
                            if False:
                                #no smoothing
                                tang=triTang
                            else:
                                avgTang=mathutils.Vector((0,0,0))

                                for x in vertFaceTris[vertInd]:
                                    faceInd2=x[0]
                                    triInd2=x[1]
                                    face2=me.tessfaces[faceInd2]
                                    nor2=faceTriNors[faceInd2][triInd2]
                                    tang2=uvFaceTriTangs[uvInd][faceInd2][triInd2]
                                    triVertInds2=faceTriVertInds[faceInd2][triInd2]

                                    p0=me.vertices[face2.vertices[triVertInds2[x[2]%3]]].co
                                    p1=me.vertices[face2.vertices[triVertInds2[(x[2]+1)%3]]].co
                                    p2=me.vertices[face2.vertices[triVertInds2[(x[2]+2)%3]]].co

                                    if not face2.use_smooth:
                                        if nor.x==nor2.x and nor.y==nor2.y and nor.z==nor2.z:
                                            if tang2.w==triTang.w and tang2.xyz.dot(triTang.xyz)>0:
                                                area=calc_triangle_area(p0,p1,p2)
                                                angle=calc_vec_angle(p2-p0,p1-p0)
                                                #avgTang=avgTang+tang2.xyz*angle*area
                                                avgTang=avgTang+tang2.xyz*(angle+area)

                                avgTang.normalize()
                                avgTang=orthog_vec(nor,avgTang)
                                tang=mathutils.Vector((avgTang.x,avgTang.y,avgTang.z,triTang.w))

                        tangs.append(tang)
                        key+=' %g %g %g %g'%(tang[0],tang[1],tang[2],tang[3])

                #
                if key not in my_vert_inds.keys():
                    orig_vert_inds.append(vertInd)

                    my_vert_inds[key]=my_verts_num
                    my_positions.append(pos)

                    if useNormals:
                        my_normals.append(nor)

                    if useColors:
                        for i,vertcol in enumerate(me.vertex_colors):
                            my_colors[vertcol.name].append(cols[i])

                    if useTexcoords:
                        for i,uvtex in enumerate(me.uv_textures):
                            my_texcoords[uvtex.name].append(uvs[i])

                    if useTangents:
                        for i,uvtex in enumerate(me.uv_textures):
                            my_tangents[uvtex.name].append(tangs[i])

                    #if useMaterialColors:
                    #    my_matCols.append(matCol)

                    my_verts_num+=1

                my_vert_indice=my_vert_inds[key]
                my_indices[maName].append(my_vert_indice)
                my_inds_num+=1

    #apply transforms
    for i,x in enumerate(my_positions):
        my_positions[i]=modelMat*x;
        
    #print(normalMat)
    for i,x in enumerate(my_normals):
        my_normals[i]=normalMat*x;


    for k,v in my_tangents.items():
        for i,tg in enumerate(v):
            w=tg.w
            tg2=normalMat*tg.xyz
            my_tangents[k][i]=mathutils.Vector((tg2[0],tg2[1],tg2[2],w));

    #
    return {
        "positions" : my_positions,
        "normals" : my_normals,
        "texcoords" : my_texcoords,
        "tangents" : my_tangents,
        "colors" :  my_colors,
        "indices" : my_indices,
        "vertices_num" : my_verts_num,
        "indices_num" : my_inds_num
    }

###########################################

def orthog_vec(nor,vec):
    r=(vec - nor * nor.dot(vec))
    r.normalize()
    return r

def calc_tangent_space(pt1,pt2,pt3,uv1,uv2,uv3,nor):
    e1=pt2-pt1
    e2=pt3-pt1
    e1uv=uv2-uv1
    e2uv=uv3-uv1

    cp=e1uv.x*e2uv.y - e1uv.y*e2uv.x

    if cp == 0.0:
        return mathutils.Vector((0,0,0,0))

    r = 1.0 / cp
    sdir=(e2uv.y*e1 - e1uv.y*e2)*r
    tdir=(e1uv.x*e2 - e2uv.x*e1)*r
    tg=orthog_vec(nor,sdir)
    w=-1.0 if nor.cross(sdir).dot(tdir) < 0.0 else 1.0

    return mathutils.Vector((tg.x,tg.y,tg.z,w))

def calc_vec_angle(v0,v1):
    try:
        l=v0.length*v1.length
        d=v0.dot(v1)
        a=math.acos(d/l)
        return a
    except ValueError as e:
        return 0

def calc_triangle_area(p0,p1,p2):
    try:
        e0=p1-p0
        e1=p2-p0
        c=e0.cross(e1)
        # l=math.sqrt(c.dot(c))
        a=c.length/2.0
        return a
    except ValueError as e:
        return 0

###########################################

#from https://gamedev.stackexchange.com/a/28756

def half_float_compress(float32):
    F16_EXPONENT_BITS = 0x1F
    F16_EXPONENT_SHIFT = 10
    F16_EXPONENT_BIAS = 15
    F16_MANTISSA_BITS = 0x3ff
    F16_MANTISSA_SHIFT =  (23 - F16_EXPONENT_SHIFT)
    F16_MAX_EXPONENT =  (F16_EXPONENT_BITS << F16_EXPONENT_SHIFT)

    a = struct.pack('>f',float32)
    b = binascii.hexlify(a)

    f32 = int(b,16)
    f16 = 0
    sign = (f32 >> 16) & 0x8000
    exponent = ((f32 >> 23) & 0xff) - 127
    mantissa = f32 & 0x007fffff

    if exponent == 128:
        f16 = sign | F16_MAX_EXPONENT

        if mantissa:
            f16 |= (mantissa & F16_MANTISSA_BITS)

    elif exponent > 15:
        f16 = sign | F16_MAX_EXPONENT

    elif exponent > -15:
        exponent += F16_EXPONENT_BIAS
        mantissa >>= F16_MANTISSA_SHIFT
        f16 = sign | exponent << F16_EXPONENT_SHIFT | mantissa

    else:
        f16 = sign

    return f16

##########################################

def lzma_open_for_write(fn):
    return lzma.open(fn,"wb",format=lzma.FORMAT_ALONE)

def next_greater_power_of_2(x):
    return 2**(x-1).bit_length()

class png_open_for_write():
    def __init__(self, fn):
        self.fn = fn
        self.pixels=[]

    def __enter__(self):
        return self
        
    def __exit__(self, type, value, traceback):
        paddedPixelsNum=next_greater_power_of_2(len(self.pixels)//4)
        self.pixels.extend([0,0,0,255]*paddedPixelsNum)
        
        pixelsWidth=1
        pixelsHeight=1
        
        while paddedPixelsNum!=pixelsWidth*pixelsHeight:
            if pixelsWidth<=pixelsHeight:
                pixelsWidth*=2
            else:
                pixelsHeight*=2

        image = bpy.data.images.new("untitled",width=pixelsWidth,height=pixelsHeight,alpha=True)
        image.pixels = self.pixels
        image.filepath_raw = self.fn
        image.file_format = 'PNG'

        try:
            image.save()
        except Exception as error:
            raise error
        finally:
            bpy.data.images.remove(image)
            
    def write(self,data):
        self.pixels.extend([x/255.0 for x in bytearray(data)])
        
    def tell(self):
        return len(self.pixels)