# BASE
import pprint
import os
import json
import ctypes
import re
import fnmatch
# PARSE
import pfp
import struct
#GLTF EXPORT
import base64
import operator
from pygltflib import GLTF2 as G2, Scene as SC, Accessor as AC, Buffer as BU, BufferView as BV, BufferFormat as BF, Asset as AS, Mesh as MS, Node as NO, Primitive as PM, Attributes as ATTB
from pygltflib.validator import validate, summary
# DDS TO PNG
from PIL import Image

pp = pprint.PrettyPrinter()
### FUNCTIONS ###
# CREDIT: llasram, jscs @ Stackoverflow
def unpack_string(data):
    size = len(data)
    fmt = '{}s'
    string = struct.unpack(fmt.format(size), data)[0].decode()
    return string

def dataString(list_of_lists):
    master_string = ''
    lst_len = []
    for list in list_of_lists:
        temp = ', '.join(map(str, list))
        lst_len.append(len(temp))
        master_string += ', '.join(map(str, list))

    return master_string, lst_len

def convertDDStoPNG(path):
    im = Image.open(path).save(path.replace('.dds','.png'))

# GENERAL FUNCTION TO CONVERT A LIST OF SCALAR, VECTORS, ETC TO BYTE ARRAYS!
def makeByteArrayFromList(list, mode, type):
    out_bytearray = None
    if mode == 'SCALAR':
        out_bytearray = bytearray()
        for item in list:
            out_bytearray.extend(struct.pack(type, item))

        byte_length = len(out_bytearray)
        min_val = min(list)
        max_val = max(list)
        count = len(list)

        return out_bytearray, byte_length, min_val, max_val, count
    if mode == 'VEC':
        out_bytearray = bytearray()
        for t in list:
            tulpe_len = len(t)
            for value in t:
                out_bytearray.extend(struct.pack(type, value))

        byte_length = len(out_bytearray)
        min_val = [min([operator.itemgetter(i)(item) for item in list]) for i in range(tulpe_len)]
        max_val = [max([operator.itemgetter(i)(item) for item in list]) for i in range(tulpe_len)]
        count = len(list)

        return out_bytearray, byte_length, min_val, max_val, count

# SEARCH FILE SYSTEM AND RETURN FILES
def searchFileSystem(main_path):
    main_list = []
    for r, d, f in os.walk(WORKING_DIR):
        drss = fnmatch.filter(f, '*.drs')
        imgs = fnmatch.filter(f, '*.dds')

        for file in drss:
            name = file.split('.')[0]
            file = os.path.join(r, file)
            regex = '('+name+'\_[a-z]{3}\.dds)|('+name+'\.drs)'
            rel_img = []
            for img in imgs:
                if re.match(regex, img):
                    rel_img.append(os.path.join(r ,img))

            if len(rel_img) != 0:
                data = [file, rel_img]
                main_list.append(data)

    pp.pprint(main_list)
    return main_list




def parseDRStoLists(abs_file_path, abs_bt_path):
    print('------ IN ------> ', abs_file_path)
    # READ DRS FILE
    dom = pfp.parse(data_file=abs_file_path, template_file=abs_bt_path)

    # BASE LISTS
    list_VEC3_normals = []
    list_VEC2_uvs = []
    list_VEC3_positions = []
    list_SCALAR_faceIndices = []

    #LOOP OVER NODES
    for node in dom.Nodes:
        node_name = unpack_string(node.Name.Text._pfp__build())
        print(node_name)

        # ATTRIBUTE NODE // POSITIONS - NORMALS - UVS - BBOX - MATERIALS
        if node_name == 'CDspMeshFile':
            print('CDspMeshFile!')
            #LOOP OVER SUBMESHES
            for submesh in node.MeshFile.meshes:
                # CHECK IF GOOD NODE
                try:
                    print('A good submesh!')
                    VertexCount =  struct.unpack('i', submesh.VertexCount._pfp__build())
                    FaceCount = struct.unpack('i', submesh.FaceCount._pfp__build())
                    print('---------------')
                except:
                    print('Not a good submesh!')
                    VertexCount, FaceCount = None, None

                if VertexCount != None and FaceCount != None:
                    # OFFSET FOR SUBMESHES
                    offset = len(list_VEC3_positions)
                    # LOOP OVER FACE STRUCTURE:
                    for face in submesh.Faces:
                        indices = struct.unpack('hhh', face._pfp__build())
                        for index in list(indices):
                            list_SCALAR_faceIndices.append(index + offset)
                    # LOOP OVER VERTEX STRUCTURE
                    for vertex in submesh.Meshes[0].Vertex:
                        #GET POS
                        xyz = struct.unpack('fff', vertex.vertex._pfp__build())
                        list_VEC3_positions.append(xyz)
                        # GET NORMALS
                        nxyz = struct.unpack('fff', vertex.vertexNormal._pfp__build())
                        list_VEC3_normals.append(nxyz)
                        # GET UVs
                        uxy = struct.unpack('ff', vertex.vertexTexture._pfp__build())
                        list_VEC2_uvs.append(uxy)

            # GET BONES FROM NODE
            # GET WEIGHTS FROM NODE
    ## NODES LOOP END ##########################################################

    # Debug File Structure
    out_path = abs_file_path.replace(".drs", ".txt")
    print('----- OUT TEXT -----> ', out_path)
    with open(out_path, "w") as f:
        f.write(dom._pfp__show(include_offset=True))
        f.close()

    return list_VEC3_positions, list_SCALAR_faceIndices, list_VEC3_normals, list_VEC2_uvs

### DEFINE LOCATION VARS VARIABLES ###
with open("dev_env.json", 'r') as f:
    WORKING_DIR = json.load(f)["WORKING_DIR"]

# FIND FILES IN FOLDER
master_list = searchFileSystem(WORKING_DIR)

#FOR EACH FILE
for model in master_list:
    file_name = os.path.split(model[0])[1]
    abs_path = os.path.abspath(model[0])
    abs_bt = os.path.abspath("drs.bt")
    #CONVERT IMAGES TO PNG / BASE64 STRING
    for img in model[1]:
        img_name = os.path.split(img)[1]
        img_path = os.path.abspath(img)
        convertDDStoPNG(img_path)

    print(file_name, abs_path, abs_bt)
    #PARSE FILE TO LISTS
    list_VEC3_positions, list_SCALAR_faceIndices, list_VEC3_normals, list_VEC2_uvs = parseDRStoLists(abs_path, abs_bt)

    # MAKE BINARY ARRAYS:
    # POSITIONS
    position_bytearray, position_bytelen, position_mins, position_maxs, position_count = makeByteArrayFromList(list_VEC3_positions, 'VEC', 'f')
    print('--- POSITIONS ---\nByteLen: ', position_bytelen,'\n Min: ', position_mins,'\n Max: ', position_maxs,'\n Count: ', position_count)

    # FACES / POINT IDs
    faces_bytearray, faces_bytelen, faces_mins, faces_maxs, faces_count =  makeByteArrayFromList(list_SCALAR_faceIndices, "SCALAR", "i")
    print('--- INDICES ---\nByteLen: ', faces_bytelen,'\n Min: ', faces_mins,'\n Max: ', faces_maxs,'\n Count: ', faces_count)

    # Normals
    normals_bytearray, normals_bytelen, normals_mins, normals_maxs, normals_count = makeByteArrayFromList(list_VEC3_normals, 'VEC', 'f')
    print('--- NORMALS ---\nByteLen: ', normals_bytelen,'\n Min: ', normals_mins,'\n Max: ', normals_maxs,'\n Count: ', normals_count)

    # UVs
    uvs_bytearray, uvs_bytelen, uvs_mins, uvs_maxs, uvs_count = makeByteArrayFromList(list_VEC2_uvs, 'VEC', 'f')
    print('--- UVs ---\nByteLen: ', uvs_bytelen,'\n Min: ', uvs_mins,'\n Max: ', uvs_maxs,'\n Count: ', uvs_count)

    #TOTAL DATA:
    data_bytearray = position_bytearray + faces_bytearray + normals_bytearray + uvs_bytearray
    print('--- DATA ---\nByteLen: ', len(data_bytearray))

    ### MAKE GLTF FILE ###
    # EMBEDDED IMG FILES

    #### EMBEDDED GEO FILE ####
    base_uri = 'data:application/octet-stream;base64,'
    datauri_geo = base_uri + base64.encodebytes(data_bytearray).decode()

    #BUFFERS
    buffer_geo = BU(uri=datauri_geo, byteLength=len(data_bytearray))
    #BUFFERVIEWS
    pos_bw = BV(name='pos', buffer=0, byteLength=position_bytelen)
    ind_bw = BV(name='ind', buffer=0, byteOffset=position_bytelen, byteLength=faces_bytelen)
    nor_bw = BV(name='nor', buffer=0, byteOffset=position_bytelen+faces_bytelen, byteLength=normals_bytelen)
    uvs_bw = BV(name='uvs', buffer=0, byteOffset=(position_bytelen+faces_bytelen+normals_bytelen), byteLength=uvs_bytelen)
    # Accessors
    pos_ac = AC(name="ac_pos", bufferView=0, componentType=5126, min=position_mins, max=position_maxs, count=position_count, type="VEC3")
    ind_ac = AC(name="ac_ind", bufferView=1, componentType=5125, count=faces_count, type="SCALAR")
    nor_ac = AC(name="ac_nor", bufferView=2, componentType=5126, min=normals_mins, max=normals_maxs, count=normals_count, type="VEC3", normalized=True)
    uvs_ac = AC(name="ac_uvs", bufferView=3, componentType=5126, min=uvs_mins, max=uvs_maxs, count=uvs_count, type="VEC2")
    # PRIM -> MESH -> NODE -> SCENE
    prim = PM(attributes=ATTB(0,2,TEXCOORD_0=3), indices = 1) #<-- ADD NORMALS. UVS, BONES - ACs here!
    mesh = MS(primitives=[prim])
    node = NO(mesh=0)
    scene = SC(nodes=[0])

    #MAKE GLTF STRUCTURE
    gltf_emb = G2(accessors=[pos_ac, ind_ac, nor_ac, uvs_ac], bufferViews=[pos_bw, ind_bw, nor_bw, uvs_bw], buffers=[buffer_geo], meshes=[mesh], nodes=[node], scenes=[scene], scene=0)

    #OUTPUT
    ext = "_embeded.gltf"
    out_gltf = abs_path.replace(".drs", ext)
    gltf_emb.save_json(out_gltf)
    print('----- OUT GLTF (EMBEDED) -----> ', out_gltf)

    print('------------------------------------------------------------------')
