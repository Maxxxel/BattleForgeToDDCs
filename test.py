import struct
from array import array


with open('files\Mesh_PrimitiveAttribute\Mesh_PrimitiveAttribute_06.bin', 'rb') as f:

    data = f.read()
    print(len(data))
    data_enc = struct.unpack_from('<6i', data, offset=192)
    print(data_enc)
    data_enc = struct.unpack_from('<12f', data, offset=0)
    print(data_enc)
    f.close()


with open('files\ice_barrier\\building_frost_ice_barrier_decal_data.bin', 'rb') as f:
    data = f.read()
    print(len(data))
    data_enc = struct.unpack_from('<6i', data, offset=48)
    print(data_enc)
    data_enc = struct.unpack_from('<12f', data, offset=0)
    print(data_enc)
