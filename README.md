# BattleForgeToDDCs
### About
This is a simple mass-converter for Battle Forges .DRS Models. Goal is to create a universal file (GLTF) for use in multiple DDCs like Blender, Maya, Houdini, 3dsMax, etc...

<img src="https://i.gyazo.com/51a830c1b9aaefcafeedaf3ecd8edee8.png" alt="ice_barrier_gltf" width="400" height="400">

> Ice Barrier in GLTF


### How to use
- Renamve the dev_env.json.example to dev_env.json
- Edit the Path to the master folder of all DRS/DDS Files (It will search all subfolders for .drs and .dds files)

### Dependencies
- [pfp](https://github.com/d0c-s4vage/pfpu)
- [pygltflib](https://gitlab.com/dodgyville/pygltflib)
- [Pillow](https://github.com/python-pillow/Pillow)

### To-Do
- [x] DRS Parsing & Reading
- [X] Convert DRS Geometry (Points, Faces) to GLTF
- [x] Convert Normals, UVs to GLTF
- [ ] ~Add Decal, Damage Model and Model into one GLTF File~ does not make a whole lot of sense. might at as a QOL-feature later.
- [x] Redo Search Algorithm. (Take into account: "Model Groups", shared decal textures in different location)
- [ ] Embed Textures, Materials and Gemetry into single GLTF
- [ ] Joints, Animations (from SKA)

### Credit
- CrazyCockerell (QuickBMS Script for mass-exporting of Battle Forges PAK-Files!)
- bobfrog (pfp-DRS-Template & awseome prework!)
- solcrow (Help + Awesome Unity Viewer and Exporter - Shown that its possible + Animation pfp-SKA-parse templates)
- Kubik & LPeter1997 for their help!
- [Skylords Reborn Team](https://forum.skylords.eu/) (In general for keeping the Game alive!)
