# BASE
import os
import json
import ctypes
#import chardet # -> might drop later

# PARSE
import pfp
import struct
#GLTF EXPORT
import operator
from pygltflib import GLTF2 as G2, Scene as SC, Accessor as AC, Buffer as BU, BufferView as BV, BufferFormat as BF, Asset as AS, Mesh as MS, Node as NO, Primitive as PM, Attributes as ATTB
from pygltflib.validator import validate, summary

### FUNCTIONS ###
# CREDIT: llasram, jscs @ Stackoverflow
def unpack_string(data):
    size = len(data)
    fmt = '{}s'
    string = struct.unpack(fmt.format(size), data)[0].decode()
    return string

# MAKE A BYTE VERTEX ARRAY FROM A VERTEX POSITION LIST
def makeBinaryVectorArrayFromList(vertices, mode='f'):
    vertex_bytearray = bytearray()
    for vertex in vertices:
        for value in vertex:
            vertex_bytearray.extend(struct.pack(mode, value))

    bytelen = len(vertex_bytearray)
    mins = [min([operator.itemgetter(i)(vertex) for vertex in vertices]) for i in range(3)]
    maxs = [max([operator.itemgetter(i)(vertex) for vertex in vertices]) for i in range(3)]
    return vertex_bytearray, bytelen, mins, maxs, len(vertices)

# MAKE A BYTE FACE INDEX ARRAY FROM FACE INDEX LIST
def makeBinaryShortArrayFromList(faces):
    faces_bytearray = bytearray()
    for face in faces:
        faces_bytearray.extend(struct.pack('i', int(face)))

    bytelen = len(faces_bytearray)
    mins = min(faces)
    maxs = max(faces)
    return faces_bytearray, bytelen, mins, maxs, len(faces)

### DEFINE LOCATION VARS VARIABLES ###
with open("dev_env.json", 'r') as f:
    WORKING_DIR = json.load(f)["WORKING_DIR"]

print(WORKING_DIR)
path = WORKING_DIR

# FIND FILES IN FOLDER
files = []
# r=root, d=directories, f = files
for r, d, f in os.walk(path):
    for file in f:
        if '.drs' in file:
            files.append(os.path.join(r, file))

#FOR EACH FILE
for f in files:
    # DO SOME FILE PATH MAGIC - I.E: clean export and renaming
    file_name = os.path.split(f)[1]
    abs_path = os.path.abspath(f)
    abs_bt = os.path.abspath("drs.bt")

    print('------ IN ------> ', abs_path, abs_bt)
    # READ DRS FILE
    dom = pfp.parse(data_file=abs_path, template_file=abs_bt)

    for node in dom.Nodes:
        node_name = unpack_string(node.Name.Text._pfp__build())
        # IF GEO NODE
        if node_name == 'CGeoMesh':
            print('MeshNode!')
            # GET VERTICES FROM NODE
            positions = []
            for vertex in node.Mesh.Vertices:
                #LOOP OVER VERTECIES AND STORE INTO TULPE
                xyzw = struct.unpack('ffff', vertex._pfp__build())
                xyz = xyzw[0:3]
                xyz = [ctypes.c_float(float).value for float in xyz]
                xyz = tuple(map(float, xyz))
                positions.append(xyz)

            #GET PRIMITIVES FROM NODE
            faces = []
            for face in node.Mesh.Faces:
                index = struct.unpack('hhh', face._pfp__build())
                # THESE ARE LIKELY POINT NUMBERS THE TRIANGLE IS BOUND TO
                # LIST OF 3-POINT-ID-GROUPS
                faces.append(index)

            #ORDERED LIST OF POINTS FOR GLTF
            faces_o = [item for grp in faces for item in grp]

            # GET NORMALS
            # GET UVs
            # GET BONES

            ################ debug array (triangle, quad) ################
            #vertices = [(0.5, -0.5, 0.0), (-0.5, -0.5, 0.0), (-0.5, 0.5, 0.0), (0.5, 0.5, 0.0)]
            #faces = [1,0,3,1,3,2]
            #vertices = [(0.5, -0.5, 0.0), (-0.5, -0.5, 0.0), (-0.5, 0.5, 0.0)]
            #faces = [1,2,3]
            ##############################################################

            # MAKE BINARY ARRAYS:
            # POSITIONS
            position_bytearray, position_bytelen, position_mins, position_maxs, position_count = makeBinaryVectorArrayFromList(positions)
            print('--- POSITIONS ---\nByteLen: ', position_bytelen,'\n Min: ', position_mins,'\n Max: ', position_maxs,'\n Count: ', position_count)
            # FACES / POINT IDs
            faces_bytearray, faces_bytelen, faces_mins, faces_maxs, faces_count =  makeBinaryShortArrayFromList(faces_o)
            #faces_bytearray, faces_bytelen, faces_mins, faces_maxs =  makeBinaryVectorArrayFromList(faces, 'i')
            print('--- INDICES ---\nByteLen: ', faces_bytelen,'\n Min: ', faces_mins,'\n Max: ', faces_maxs,'\n Count: ', faces_count)

            #TOTAL DATA:
            data_bytearray = position_bytearray + faces_bytearray
            print('--- DATA ---\nByteLen: ', len(data_bytearray))

            data_path = abs_path.replace(".drs", "_data.bin")

            # LATER EMBED INTO GLB FILE (GLTF BINARY)
            with open(data_path, 'wb') as out_file:
                out_file.write(data_bytearray)
                out_file.close()

            ### MAKE GLTF FILE ###
            # Buffer
            buffer = BU(uri=file_name.replace(".drs", "_data.bin"), byteLength=len(data_bytearray)) # BUFFER
            # Buffer Views
            pos_bw = BV(name='pos', buffer=0, byteLength=position_bytelen)
            ind_bw = BV(name='ind', buffer=0, byteOffset=position_bytelen, byteLength=faces_bytelen)
            # Accessors
            pos_ac = AC(name="ac_pos", bufferView=0, componentType=5126, min=position_mins,max=position_maxs, count=position_count, type="VEC3")
            ind_ac = AC(name="ac_ind", bufferView=1, componentType=5125, count=faces_count, type="SCALAR")

            # PRIM -> MESH -> NODE -> SCENE
            prim = PM(attributes=ATTB(0),indices = 1) #<-- ADD NORMALS. UVS, BONES - ACs here!
            mesh = MS(primitives=[prim])
            node = NO(mesh=0)
            scene = SC(nodes=[0])

            #MAKE GLTF STRUCTURE
            gltf = G2(accessors=[pos_ac, ind_ac], bufferViews=[pos_bw, ind_bw], buffers=[buffer], meshes=[mesh], nodes=[node], scenes=[scene], scene=0)

            #OUTPUT
            out_gltf2 = abs_path.replace(".drs", ".gltf")
            gltf.save_json(out_gltf2)
            #EXPORT FILE
            print('----- OUT GLTF -----> ', out_gltf2)

    # Debug File Structure
    out_path = abs_path.replace(".drs", ".txt")
    print('----- OUT TEXT -----> ', out_path)
    with open(out_path, "w") as f:
        f.write(dom._pfp__show(include_offset=True))
        f.close()
    print('------------------------------------------------------------------')

#dom = pfp.parse(
#	data_file="~/Desktop/image.png",
#	template_file="~/Desktop/PNGTemplate.bt"
#)
