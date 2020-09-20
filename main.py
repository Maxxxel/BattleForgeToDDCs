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
import pygltflib
from pygltflib import GLTF2 as G2, Scene as SC, Accessor as AC, Buffer as BU, BufferView as BV, BufferFormat as BF, Asset as AS, Mesh as MS, Node as NO, Primitive as PM, Attributes as ATTB, Material as MAT, Image as IMG, Skin as SK

from gltflib import (GLTF, GLTFModel, Asset, Scene, Node, Mesh, Primitive, Attributes, Buffer, BufferView, Accessor, AccessorType, BufferTarget, ComponentType, GLBResource, FileResource)
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

def convertDDStoPNG(img_path):
    try:
        Image.open(img_path).save(img_path.replace('.dds','.png'))
    except:
        print('file not found. Note: Probably a texture for debris but they use the default texture set')
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
    elif mode == 'VEC':
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
    # LOOP OVER MAIN PATH
    for r, d, f in os.walk(main_path):
        # FILTER FOR FILES
        drss = fnmatch.filter(f, '*.drs')
        imgs = []

        # CLEAN DEBRIS FOLDER FROM IMG PATH
        for file in os.listdir(r.replace('\\meshes', '')):
            imgs.append(file.replace('\\meshes', ''))
        imgs = fnmatch.filter(imgs, '*.dds')

        # IF THE GUY WHO MADE THE NAMING SCHEME FOR BATTLEFORGE READS THIS:
        # -> PLEASE THINK OF A BETTER NAMING SCHEMES ... It is annoying to reverse :D
        # f.E: [AssetType]_[Fraction]_[AssetName*]_{Suffix}.{extension}
        # -> Asset Name should be {Pascal,Camel}Case and not snake_case like the other parts.

        # FOR EACH DRS FIND FILE AND TEXTURES
        for file in drss:
            model_dict = dict()
            sub_strings = file.split('.')[0].split('_')
            # FILE PATH (RELATIVE)
            model_dict['filepath'] = os.path.join(r, file)
            # CHECK IF TYPE EXISTS
            name_offset = 0
            regex_type = r'(unit)|(building)|(fortification)|(object)'
            try:
                end_type = [i for i, s_item in enumerate(sub_strings) if re.search(regex_type, s_item)][0]
                model_dict['type'] = sub_strings[end_type]
                name_offset +=1
            except:
                model_dict['type'] = ''
            # CHECK IF VARIANT EXISTS
            regex_variant = r"(lostsouls)|(twilight)|(stonekin)|(bandit)|(frost)|(nature)|(fire)|(shadow)|(quest)|(legendary)"
            try:
                end_variant = [i for i, s_item in enumerate(sub_strings) if re.search(regex_variant, s_item)][0]
                model_dict['variant'] = sub_strings[end_variant]
                name_offset +=1
            except:
                model_dict['variant'] = ''

            #FIND END OF ASSET NAME
            regex_name = r"(decal)|(module[0-9]*)" # MAYBE ADD MORE BUT NOT FOR NOW
            try:
                end_name = [i for i, s_item in enumerate(sub_strings) if re.search(regex_name, s_item)][0]
            except:
                end_name = len(sub_strings)
            model_dict['name'] = '_'.join(sub_strings[name_offset:end_name])
            model_dict['suffix'] = '_'.join(sub_strings[end_name:])

            # UNIT TEXTURES
            if model_dict['type'] == 'unit' and model_dict['suffix'] == '':
                tex_pat = r'[a-zA-Z_]{'+str(len(model_dict['type'])) + ',' + str(len(model_dict['type'])+1)+'}[a-zA-Z_]{'+str(len(model_dict['variant'])) + ',' + str(len(model_dict['variant'])+1)+'}'+model_dict["name"]+'_[a-zA-Z]*\.dds'

                tmp_list = []
                #print(tex_pat)
                for img in imgs:
                    if re.match(tex_pat, img):
                        img_sub_string = img.split('.')[0].split('_')
                        type = img_sub_string[len(img_sub_string)-1]
                        if type == 'fluid':
                            type = 'flu'
                        tmp_list.append({"type":type, "path":os.path.join(r , img)})
                model_dict['textures'] = tmp_list
            # DECALS OF BUILDINGS
            elif model_dict['type'] == 'building' and model_dict['suffix'] == 'decal':
                tex_pat = r'[a-zA-Z_]{'+str(len(model_dict['type'])) + ',' + str(len(model_dict['type'])+1)+'}[a-zA-Z_]{'+str(len(model_dict['variant'])) + ',' + str(len(model_dict['variant'])+1)+'}'+model_dict["name"] + '_' + model_dict['suffix'] +'_[a-zA-Z]*\.dds'
                tmp_list = []
                #print(tex_pat)
                for img in imgs:
                    if re.match(tex_pat, img):
                        img_sub_string = img.split('.')[0].split('_')
                        type = img_sub_string[len(img_sub_string)-1]
                        if type == 'fluid':
                            type = 'flu'
                        tmp_list.append({"type":type, "path":os.path.join(r , img)})
                model_dict['textures'] = tmp_list
            # GENERAL BUILDING MODULES
            elif model_dict['type'] == 'building' and re.match(r'module[0-9]*.*', model_dict['suffix']):
                tex_pat = r'[a-zA-Z_]{'+str(len(model_dict['type'])) + ',' + str(len(model_dict['type'])+1)+'}[a-zA-Z_]{'+str(len(model_dict['variant'])) + ',' + str(len(model_dict['variant'])+1)+'}'+model_dict["name"]+'_[a-zA-Z]*\.dds'
                #print(imgs)
                tmp_list = []
                for img in imgs:
                    if re.match(tex_pat, img):
                        img_sub_string = img.split('.')[0].split('_')
                        type = img_sub_string[len(img_sub_string)-1]
                        if type == 'fluid':
                            type = 'flu'
                        tmp_list.append({"type":type, "path":os.path.join(r , img)})
                model_dict['textures'] = tmp_list

            main_list.append(model_dict)

    #pp.pprint(main_list)
    return main_list

# PNG TO BYTE ARRAYS
def makeImgFromImgList(img_list):
    img_src_list = []
    img_smp_list = []
    img_tex_list = []

    for i in range(len(img_list)):
        img_dict = img_list[i]
    #for img_dict in img_list:
        tex_type = img_dict['type']
        b64_data = base64.b64encode(open(img_dict['path'].replace('\meshes', '').replace('.dds','.png'), 'rb').read())
        b64_data_string = b64_data.decode()
        datauri_text = 'data:image/png;base64,' + b64_data_string
        #print(datauri_text[:1000])
        img_src_list.append(IMG(uri=datauri_text, name=tex_type+'_img'))
        img_tex_list.append(pygltflib.Texture(name=tex_type+'_img', source=i, sampler=0))
    # ADD SAMPLER
    img_smp_list.append(pygltflib.Sampler())
    return img_smp_list, img_src_list, img_tex_list


# PARSE FILE
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
            print("--- CDspMeshFile ---")
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

        # GET JOINTS FROM NODE 'CSkSkeleton'
        if node_name == "CDspJointMap":
            print("--- Joint Groups ---")
            if struct.unpack('i', node.JointMap.JointGroupCount._pfp__build())[0] != 0:
                joint_groups = []
                for jointGroup in node.JointMap.JointGroups:
                    jointCount = struct.unpack("i", jointGroup.JointCount._pfp__build())[0]
                    jointIndices = struct.unpack("h"*jointCount, jointGroup.JointIndices._pfp__build())
                    jointIndices = list(jointIndices)
                    joint_groups.append(jointIndices)

                #print("JOINT GROUPS: ", joint_groups)

        # GET VERTEX WEIGHTS FROM NODE 'CSkSkinInfo'
        if node_name == "CSkSkinInfo":
            print("--- SKIN WEIGHTS ---")
            vertexSkinData = []
            # MIGHT LOOP OVER Length to assign vertex numbers but general list should be fine...
            for vertexData in node.SkinInfo.VertexWeights:
                vertexWeights = list(struct.unpack("ffff", vertexData.Weights._pfp__build()))
                vertexBoneIndicies = list(struct.unpack("iiii", vertexData.BoneIndices._pfp__build()))
                vertexSkinData.append([vertexBoneIndicies, vertexWeights])

                #print("BONE INDICES: ", vertexBoneIndicies, "\t| WEIGHTS: ", vertexWeights)

        # GET BONES FROM NODE 'CSkSkeleton'
        if node_name == "CSkSkeleton":
            print("--- SKELETON ---")
            boneMatrices = []
            boneMeta = []
            if struct.unpack('i', node.Skeleton.BoneMatrixCount._pfp__build())[0] != 0:
                print('--- Bone Matrix ---')
                for boneMatrix in node.Skeleton.BoneMatrices:
                    boneMatrixData = []
                    for boneVertices in boneMatrix.BoneVertices:
                        data_tuple = struct.unpack("fffi", boneVertices._pfp__build())
                        parent = data_tuple[3]
                        xyz = list(data_tuple[:3])
                        boneMatrixData.append([parent, xyz])

                        # PRINT
                        #print("PARENT: ", parent, "\t| POSITION: ", xyz)

                    boneMatrices.append(boneMatrixData)

            if struct.unpack('i', node.Skeleton.BoneCount._pfp__build())[0] != 0:
                print('--- Bone Meta ---')
                for bone in node.Skeleton.Bones:
                    boneName = unpack_string(bone.Name.Text._pfp__build())
                    boneId = struct.unpack("i", bone.Identifier._pfp__build())[0]
                    boneChildCount = struct.unpack("i", bone.ChildCount._pfp__build())[0]
                    if boneChildCount != 0:
                        boneChildren = struct.unpack("i"*boneChildCount, bone.Children._pfp__build())
                        boneChildren = list(boneChildren)
                    else:
                        boneChildren = None

                    #print(boneName, "\t| ID: ", boneId, "\t| CHILDREN: ", boneChildCount, "\t| LIST OF CHILDREN: ", boneChildren)
                    boneMeta.append([boneName, boneId, boneChildren])

            print('----')
            print(len(boneMatrices))
            print(len(boneMeta))


            if len(boneMatrices) > 0 and len(boneMeta) > 0 and len(boneMatrices) == len(boneMeta):
                # COMBINE LISTS
                list_DATA_bones = []
                print('--- COMBINE LISTS (TODO) ---')
                for i in range(len(boneMeta)):
                    list_DATA_bones.append({"bone_id": boneMeta[i][1], "bone_name": boneMeta[i][0], "bone_children": boneMeta[i][2]})
                list_DATA_bones = sorted(list_DATA_bones, key = lambda x: x['bone_id'])



    ## NODES LOOP END ##########################################################

    # Debug File Structure
    out_path = abs_file_path.replace(".drs", ".txt")
    print('----- OUT TEXT -----> ', out_path)
    with open(out_path, "w") as f:
        f.write(dom._pfp__show(include_offset=True))
        f.close()

    # RETURN STUFF
    try:
        return list_VEC3_positions, list_SCALAR_faceIndices, list_VEC3_normals, list_VEC2_uvs, list_DATA_bones
    except:
        return list_VEC3_positions, list_SCALAR_faceIndices, list_VEC3_normals, list_VEC2_uvs, None


def makeNodes(bone_list):
    nodes_list = []
    min_bone, max_bone = None, None
    joint_ids_list = []
    if bone_list != None:
        skl_assset = True
    else:
        skl_assset = False

    # ROOT NODE [0]
    if skl_assset:
        # INDEX 1
        geo_node = NO(mesh=0, skin=0, name="Proxy")
        nodes_list.append(geo_node)
        # INDEX 2 - IF SKELETAL MESH ROOT NODE
        rig_node = NO(name="Rig", children=[2])
        nodes_list.append(rig_node)
        min_bone = len(nodes_list)
        # DEFINE MIN BONE
        # ADD BONES
        for i in range(len(bone_list)):
            bone = bone_list[i]
            # ADD PONE OFFSET
            if bone["bone_children"] != None:
                children = [child_id + min_bone for child_id in bone["bone_children"]]
            else:
                children = None
            # APPEND NODE
            nodes_list.append(NO(name=bone["bone_name"], translation = [1.0,1.0,1.0], children=children))
            joint_ids_list.append(i + min_bone)

    else:
        # INDEX 0
        geo_node = NO(mesh=0, name="Proxy")
        nodes_list.append(geo_node)

    return nodes_list, skl_assset, joint_ids_list

### DEFINE LOCATION VARS VARIABLES ###
with open("dev_env.json", 'r') as f:
    WORKING_DIR = json.load(f)["WORKING_DIR"]

# FIND FILES IN FOLDER
master_list = searchFileSystem(WORKING_DIR)

#FOR EACH FILE
for model in master_list:
    file_name = model["name"]
    abs_path = os.path.abspath(model["filepath"])
    abs_bt = os.path.abspath("drs.bt")

    print('NAME: ', file_name, '\nUSING DRS:', abs_path, '\nUSING BT: ', abs_bt, '\nIMGs:')
    #CONVERT IMAGES TO PNG
    for img in model["textures"]:
        print(img['path'])
        convertDDStoPNG(os.path.abspath(img['path']).replace('\\meshes', ''))
        # CONVERT TO PBR


    print("--- PARSING ---")
    #PARSE FILE TO LISTS
    list_VEC3_positions, list_SCALAR_faceIndices, list_VEC3_normals, list_VEC2_uvs, list_DATA_bones = parseDRStoLists(abs_path, abs_bt)

    print("--- CONVERT TO BINARY ---")
    # MAKE BINARY ARRAYS:
    # POSITIONS
    position_bytearray, position_bytelen, position_mins, position_maxs, position_count = makeByteArrayFromList(list_VEC3_positions, 'VEC', 'f')
    print('--- POSITIONS ---\n-- ByteLen: ', position_bytelen,'\n-- Min: ', position_mins,'\n-- Max: ', position_maxs,'\n-- Count: ', position_count)

    # FACES / POINT IDs
    faces_bytearray, faces_bytelen, faces_mins, faces_maxs, faces_count =  makeByteArrayFromList(list_SCALAR_faceIndices, "SCALAR", "i")
    print('--- INDICES ---\n-- ByteLen: ', faces_bytelen,'\n-- Min: ', faces_mins,'\n-- Max: ', faces_maxs,'\n-- Count: ', faces_count)

    # Normals
    normals_bytearray, normals_bytelen, normals_mins, normals_maxs, normals_count = makeByteArrayFromList(list_VEC3_normals, 'VEC', 'f')
    print('--- NORMALS ---\n-- ByteLen: ', normals_bytelen,'\n-- Min: ', normals_mins,'\n-- Max: ', normals_maxs,'\n-- Count: ', normals_count)

    # UVs
    uvs_bytearray, uvs_bytelen, uvs_mins, uvs_maxs, uvs_count = makeByteArrayFromList(list_VEC2_uvs, 'VEC', 'f')
    print('--- UVs ---\n--ByteLen: ', uvs_bytelen,'\n--Min: ', uvs_mins,'\n--Max: ', uvs_maxs,'\n--Count: ', uvs_count)

    #TOTAL GEO DATA:
    data_bytearray = position_bytearray + faces_bytearray + normals_bytearray + uvs_bytearray
    print('--- DATA ---\n-- ByteLen: ', len(data_bytearray))

    ### MAKE GLTF FILE ###
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
    nor_ac = AC(name="ac_nor", bufferView=2, componentType=5126, min=normals_mins, max=normals_maxs, count=normals_count, type="VEC3")
    uvs_ac = AC(name="ac_uvs", bufferView=3, componentType=5126, min=uvs_mins, max=uvs_maxs, count=uvs_count, type="VEC2")

    # CONVERT TEXTURE FILES TO IMAGE, SAMPLER, TEXTURES
    img_smp_list, img_src_list, img_tex_list = makeImgFromImgList(model["textures"])

    # MATERIALS -> Currently only Color is embeded, since BF-Specular-Shading model is not supported by GLTF but thats a QOL-Feature
    mat_pbr_def =  { "baseColorTexture" : {"index" : 0}, "metallicFactor" : 0.0, "roughnessFactor" : 1.0 }
    mat = MAT(name='M_Base', alphaMode="MASK", pbrMetallicRoughness=mat_pbr_def)
    # PRIM -> MESH -> NODE -> SCENE
    prim = PM(attributes=ATTB(0,2,TEXCOORD_0=3), indices = 1, material= 0) #<-- ADD NORMALS. UVS, BONES - ACs here!
    mesh = MS(primitives=[prim], name=model['name'])

    # NODES (MESH, JOINTS, SKIN, etc)
    nodes_list, skl_assset, joint_ids_list = makeNodes(list_DATA_bones)

    if skl_assset:
        print(joint_ids_list)
        skin = SK(joints=joint_ids_list, skeleton=1, name="skeleton")
    else:
        skin = None

    # SCENE
    scene = SC(nodes=[0,1])

    # MAKE GLTF STRUCTURE
    gltf_emb = G2(accessors=[pos_ac, ind_ac, nor_ac, uvs_ac], bufferViews=[pos_bw, ind_bw, nor_bw, uvs_bw], buffers=[buffer_geo], images=img_src_list, materials = [mat], meshes=[mesh], nodes=nodes_list, samplers=img_smp_list, scenes=[scene], scene=0, skins=[skin], textures=img_tex_list)

    #OUTPUT GLTF
    postfix = ''
    gltf_emb.convert_buffers(pygltflib.BufferFormat.DATAURI)
    gltf_emb.save_json(abs_path.replace(".drs", postfix + '.gltf'))
    # OUTPUT GLB
    gltf_emb.convert_buffers(pygltflib.BufferFormat.BINARYBLOB)
    gltf_emb.save_binary(abs_path.replace(".drs", postfix + '.glb'))

    print('----- OUT GLTF (EMBEDED) -----> ', abs_path.replace(".drs", postfix + '.gltf'), ' & ', abs_path.replace(".drs", postfix + '.glb'))

    print('------------------------------------------------------------------')
    #break
