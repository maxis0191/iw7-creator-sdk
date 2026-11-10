"""Reader for the dump files the project's asset tool (ZoneTool fork) writes for a game world.

Everything here follows the writer in the asset tool's source (assetmanager::dumper, gfxworld.cpp,
gfxworld_tr.cpp, comworld.cpp): one flat byte stream of typed records, no padding, little endian.

Dump conventions (assetmanager.hpp):
  * array   : 0x08, existing(1 byte); when existing: uint32 count, then count * sizeof(T) raw bytes.
  * string  : 0x06, existing(1 byte); when existing: the characters and a terminating NUL.
  * asset   : 0x07, existing(1 byte); when existing: the asset name and a NUL (only the name is stored).
  * repeat  : 0x09, uint32 entry index, uint32 array index.  Used instead of the record above when the
              same pointer (or a pointer inside an array already written) was written before. The entry
              index counts, in file order, every array, string and asset record written in full; the
              array index is in elements of the referencing type.  A repeat carries no payload.
  * a null pointer or an empty array is written as the record type, existing = 0.
Every array length and offset is bounds checked; a stream that does not end exactly where the layout says
it ends is an error (WorldError), never a partial result.
"""
import struct

try:  # numpy is optional; the pure Python path gives the same results
    import os as _os
    if _os.environ.get('IW7_WORLD_NO_NUMPY'):
        raise ImportError
    import numpy as np
except ImportError:  # pragma: no cover - depends on the environment
    np = None

T_STRING, T_ASSET, T_ARRAY, T_OFFSET = 6, 7, 8, 9


class WorldError(Exception):
    """A file does not parse to its exact end, or a count or offset is not plausible."""


# ---------------------------------------------------------------- C struct layout (x64, natural alignment)

_PRIM = {'u8': (1, 'B'), 'i8': (1, 'b'), 'u16': (2, 'H'), 'i16': (2, 'h'), 'u32': (4, 'I'),
         'i32': (4, 'i'), 'f32': (4, 'f'), 'ptr': (8, 'Q')}
SCHEMAS = {}
_LAYOUTS = {}


class Layout:
    def __init__(self, name):
        off = 0
        align = 1
        self.flat = {}
        for fld in SCHEMAS[name]:
            fname, ftype = fld[0], fld[1]
            cnt = fld[2] if len(fld) > 2 else 1
            if ftype in _PRIM:
                size, ch = _PRIM[ftype]
                al, sub = size, None
            else:
                sub = layout(ftype)
                size, al = sub.size, sub.align
            off = (off + al - 1) // al * al
            for k in range(cnt):
                base = off + k * size
                key = fname + ('[%d]' % k if cnt > 1 else '')
                if sub is None:
                    self.flat[key] = (base, ch)
                else:
                    for path, (o, c) in sub.flat.items():
                        self.flat[key + '.' + path] = (base + o, c)
            off += size * cnt
            align = max(align, al)
        self.align = align
        self.size = (off + align - 1) // align * align
        self.name = name

    def get(self, buf, base, path):
        o, ch = self.flat[path]
        return struct.unpack_from('<' + ch, buf, base + o)[0]

    def off(self, path):
        return self.flat[path][0]

    def compiled(self, paths):
        """struct.Struct reading the named fields (ascending offsets, gaps skipped) from one record."""
        items = sorted((self.flat[p][0], p, self.flat[p][1]) for p in paths)
        fmt = '<'
        pos = 0
        for o, p, ch in items:
            if o < pos:
                raise ValueError('overlapping fields in %s' % self.name)
            fmt += 'x' * (o - pos) + ch
            pos = o + struct.calcsize('<' + ch)
        fmt += 'x' * (self.size - pos)
        return struct.Struct(fmt), [p for _, p, _ in items]


def layout(name):
    if name not in _LAYOUTS:
        _LAYOUTS[name] = Layout(name)
    return _LAYOUTS[name]


def _schema(name, *fields):
    SCHEMAS[name] = fields


# structs.hpp transcription (field order and types as in the asset tool; sizes are asserted below)
_schema('Bounds', ('mid', 'f32', 3), ('half', 'f32', 3))
_schema('GfxSky', ('skySurfCount', 'i32'), ('skyStartSurfs', 'ptr'), ('skyImage', 'ptr'), ('skySamplerState', 'u8'))
_schema('GfxWorldDpvsPlanes', ('cellCount', 'i32'), ('planes', 'ptr'), ('nodes', 'ptr'), ('sceneEntCellBits', 'ptr'))
_schema('GfxCell', ('bounds', 'Bounds'), ('portalCount', 'u16'), ('portals', 'ptr'))
_schema('GfxPortal', ('isQueued', 'u8'), ('isAncestor', 'u8'), ('recursionDepth', 'i8'), ('hullPointCount', 'i8'),
        ('hullPoints', 'ptr'), ('queuedParent', 'ptr'), ('plane', 'f32', 4), ('vertices', 'ptr'),
        ('cellIndex', 'u16'), ('closeDistance', 'u16'), ('vertexCount', 'i8'), ('hullAxis', 'f32', 6))
_schema('GfxReflectionProbe', ('livePath', 'ptr'), ('origin', 'f32', 3), ('angles', 'f32', 3), ('probeInstances', 'ptr'),
        ('probeInstanceCount', 'u32'), ('probeRelightingIndex', 'u32'))
_schema('GfxWorldReflectionProbeData', ('reflectionProbeCount', 'u32'), ('sharedReflectionProbeCount', 'u32'),
        ('reflectionProbes', 'ptr'), ('reflectionProbeArrayImage', 'ptr'), ('probeRelightingCount', 'u32'),
        ('probeRelightingData', 'ptr'), ('reflectionProbeGBufferImageCount', 'u32'),
        ('reflectionProbeGBufferImages', 'ptr'), ('reflectionProbeGBufferTextures', 'ptr'),
        ('reflectionProbeInstanceCount', 'u32'), ('reflectionProbeInstances', 'ptr'),
        ('reflectionProbeLightgridSampleData', 'ptr'), ('buffer', 'ptr'), ('bufferView', 'ptr'), ('bufferRWView', 'ptr'))
_schema('GfxWorldLightmapReindexData', ('imagePixelSize', 'u32'), ('reindexCount', 'u32'), ('reindexElement', 'ptr'),
        ('packedLightmapCount', 'u32'), ('packedLightmap', 'ptr'))
_schema('GfxWorldVolumetrics', ('volumetricCount', 'u32'), ('volumetrics', 'ptr'))
_schema('GfxWorldDraw', ('reflectionProbeData', 'GfxWorldReflectionProbeData'),
        ('lightmapReindexData', 'GfxWorldLightmapReindexData'), ('iesLookupTexture', 'ptr'),
        ('decalVolumeCollectionCount', 'u32'), ('decalVolumeCollections', 'ptr'), ('lightmapOverridePrimary', 'ptr'),
        ('lightmapOverrideSecondary', 'ptr'), ('lightMapCount', 'u32'), ('lightMaps', 'ptr'),
        ('lightmapTextures', 'ptr'), ('unused1', 'ptr'), ('unused2', 'ptr'), ('unused3', 'ptr'),
        ('transientZoneCount', 'u32'), ('transientZones', 'ptr', 32), ('indexCount', 'u32'), ('indices', 'ptr'),
        ('indexBuffer', 'ptr'), ('volumetrics', 'GfxWorldVolumetrics'))
_schema('GfxLightGridColorsHDR', ('rgb', 'f32', 168))
_schema('GfxLightGridTree', ('maxDepth', 'u8'), ('nodeCount', 'i32'), ('leafCount', 'i32'), ('coordMinGridSpace', 'i32', 3),
        ('coordMaxGridSpace', 'i32', 3), ('coordHalfSizeGridSpace', 'i32', 3), ('defaultColorIndexBitCount', 'i32'),
        ('defaultLightIndexBitCount', 'i32'), ('p_nodeTable', 'ptr'), ('leafTableSize', 'i32'), ('p_leafTable', 'ptr'))
_schema('GfxLightGridProbeData', ('gpuVisibleProbesCount', 'u32'), ('gpuVisibleProbePositions', 'ptr'),
        ('gpuVisibleProbesData', 'ptr'), ('gpuVisibleProbesBuffer', 'ptr'), ('gpuVisibleProbesView', 'ptr'),
        ('gpuVisibleProbesRWView', 'ptr'), ('probeCount', 'u32'), ('probes', 'ptr'), ('probesBuffer', 'ptr'),
        ('probesView', 'ptr'), ('probesRWView', 'ptr'), ('probePositions', 'ptr'), ('probePositionsBuffer', 'ptr'),
        ('probePositionsView', 'ptr'), ('zoneCount', 'u32'), ('zones', 'ptr'), ('tetrahedronCount', 'u32'),
        ('tetrahedronCountVisible', 'u32'), ('tetrahedrons', 'ptr'), ('tetrahedronBuffer', 'ptr'),
        ('tetrahedronView', 'ptr'), ('tetrahedronNeighbors', 'ptr'), ('tetrahedronNeighborsBuffer', 'ptr'),
        ('tetrahedronNeighborsView', 'ptr'), ('tetrahedronVisibility', 'ptr'), ('tetrahedronVisibilityBuffer', 'ptr'),
        ('tetrahedronVisibilityView', 'ptr'), ('voxelStartTetrahedronCount', 'u32'), ('voxelStartTetrahedron', 'ptr'),
        ('voxelStartTetrahedronBuffer', 'ptr'), ('voxelStartTetrahedronView', 'ptr'))
_schema('GfxLightGrid', ('unk', 'i32', 9), ('tableVersion', 'i32'), ('paletteVersion', 'i32'),
        ('rangeExponent8BitsEncoding', 'i8'), ('rangeExponent12BitsEncoding', 'i8'), ('rangeExponent16BitsEncoding', 'i8'),
        ('stageCount', 'u8'), ('stageLightingContrastGain', 'ptr'), ('paletteEntryCount', 'u32'),
        ('paletteEntryAddress', 'ptr'), ('paletteBitstreamSize', 'u32'), ('paletteBitstream', 'ptr'),
        ('skyLightGridColors', 'GfxLightGridColorsHDR'), ('defaultLightGridColors', 'GfxLightGridColorsHDR'),
        ('tree', 'GfxLightGridTree'), ('probeData', 'GfxLightGridProbeData'))
_schema('GfxWorldLightLists', ('surfaceListOffsetCount', 'u32'), ('surfaceListOffsets', 'ptr'),
        ('smodelListOffsetCount', 'u32'), ('smodelListOffsets', 'ptr'), ('listsSize', 'u32'), ('lists', 'ptr'))
_schema('sunflare_t', ('hasValidData', 'u8'), ('spriteMaterial', 'ptr'), ('flareMaterial', 'ptr'),
        ('spriteSize', 'f32'), ('flareMinSize', 'f32'), ('flareMinDot', 'f32'), ('flareMaxSize', 'f32'),
        ('flareMaxDot', 'f32'), ('flareMaxAlpha', 'f32'), ('flareFadeInTime', 'i32'), ('flareFadeOutTime', 'i32'),
        ('blindMinDot', 'f32'), ('blindMaxDot', 'f32'), ('blindMaxDarken', 'f32'), ('blindFadeInTime', 'i32'),
        ('blindFadeOutTime', 'i32'), ('glareMinDot', 'f32'), ('glareMaxDot', 'f32'), ('glareMaxLighten', 'f32'),
        ('glareFadeInTime', 'i32'), ('glareFadeOutTime', 'i32'), ('sunFxPosition', 'f32', 3))
_schema('GfxLightAABB', ('nodeCount', 'u16'), ('lightCount', 'u16'), ('nodeArray', 'ptr'), ('lightArray', 'ptr'))
_schema('GfxWorldDpvsStatic', ('smodelCount', 'u32'), ('staticSurfaceCount', 'u32'), ('litOpaqueSurfsBegin', 'u32'),
        ('litOpaqueSurfsEnd', 'u32'), ('litDecalSurfsBegin', 'u32'), ('litDecalSurfsEnd', 'u32'),
        ('litTransSurfsBegin', 'u32'), ('litTransSurfsEnd', 'u32'), ('emissiveSurfsBegin', 'u32'),
        ('emissiveSurfsEnd', 'u32'), ('smodelVisDataCount', 'u32'), ('surfaceVisDataCount', 'u32'),
        ('primaryLightVisDataCount', 'u32'), ('reflectionProbeVisDataCount', 'u32'), ('volumetricVisDataCount', 'u32'),
        ('decalVisDataCount', 'u32'), ('smodelVisData', 'ptr', 30), ('surfaceVisData', 'ptr', 30), ('lodData', 'ptr'),
        ('primaryLightVisData', 'ptr'), ('reflectionProbeVisData', 'ptr'), ('volumetricVisData', 'ptr'),
        ('decalVisData', 'ptr'), ('tessellationCutoffVisData', 'ptr', 30), ('sortedSurfIndex', 'ptr'),
        ('smodelInsts', 'ptr'), ('surfaces', 'ptr'), ('surfacesBounds', 'ptr'), ('smodelDrawInsts', 'ptr'),
        ('surfaceMaterials', 'ptr'), ('surfaceCastsSunShadow', 'ptr'), ('sortedSmodelIndices', 'ptr'),
        ('sunShadowOptCount', 'u32'), ('sunSurfVisDataCount', 'u32'), ('surfaceCastsSunShadowOpt', 'ptr'),
        ('constantBuffers', 'ptr'), ('usageCount', 'i32'))
_schema('GfxWorldDpvsDynamic', ('dynEntClientWordCount', 'u32', 2), ('dynEntClientCount', 'u32', 2),
        ('dynEntCellBits', 'ptr', 2), ('dynEntVisData', 'ptr', 60))
_schema('GfxWorld', ('name', 'ptr'), ('baseName', 'ptr'), ('bspVersion', 'u32'), ('planeCount', 'i32'),
        ('nodeCount', 'i32'), ('surfaceCount', 'u32'), ('skyCount', 'i32'), ('skies', 'ptr'),
        ('lastSunPrimaryLightIndex', 'u32'), ('primaryLightCount', 'u32'), ('movingScriptablePrimaryLightCount', 'u32'),
        ('sortKeys', 'u32', 15), ('dpvsPlanes', 'GfxWorldDpvsPlanes'), ('cellTransientInfos', 'ptr'), ('cells', 'ptr'),
        ('draw', 'GfxWorldDraw'), ('lightGrid', 'GfxLightGrid'), ('frustumLights', 'ptr'), ('lightViewFrustums', 'ptr'),
        ('voxelTreeCount', 'i32'), ('voxelTree', 'ptr'), ('heightfieldCount', 'i32'), ('heightfields', 'ptr'),
        ('lightLists', 'GfxWorldLightLists'), ('modelCount', 'i32'), ('models', 'ptr'), ('bounds', 'Bounds'),
        ('checksum', 'u32'), ('materialMemoryCount', 'i32'), ('materialMemory', 'ptr'), ('sun', 'sunflare_t'),
        ('outdoorLookupMatrix', 'f32', 16), ('outdoorImage', 'ptr'), ('dustMaterial', 'ptr'),
        ('materialLod0SizeThreshold', 'f32'), ('cellCasterBits', 'ptr'), ('cellHasSunLitSurfsBits', 'ptr'),
        ('sceneDynModel', 'ptr'), ('sceneDynBrush', 'ptr'), ('primaryLightMotionDetectBitsEntries', 'u32'),
        ('primaryLightMotionDetectBits', 'ptr'), ('entityMotionBitsEntries', 'u32'), ('entityMotionBits', 'ptr'),
        ('staticSpotOmniPrimaryLightCountAligned', 'u32'), ('numPrimaryLightEntityShadowVisEntries', 'u32'),
        ('primaryLightEntityShadowVis', 'ptr'), ('dynEntMotionBitsEntries', 'u32', 2), ('dynEntMotionBits', 'ptr', 2),
        ('numPrimaryLightDynEntShadowVisEntries', 'u32', 2), ('primaryLightDynEntShadowVis', 'ptr', 2),
        ('shadowGeomOptimized', 'ptr'), ('lightRegion', 'ptr'), ('lightAABB', 'GfxLightAABB'),
        ('dpvs', 'GfxWorldDpvsStatic'), ('dpvsDyn', 'GfxWorldDpvsDynamic'), ('mapVtxChecksum', 'u32'),
        ('heroOnlyLightCount', 'u32'), ('heroOnlyLights', 'ptr'), ('numUmbraGates', 'u32'), ('umbraGates', 'ptr'),
        ('umbraTomeSize', 'u32'), ('umbraTomeData', 'ptr'), ('umbraTomePtr', 'ptr'), ('numUmbraGates2', 'u32'),
        ('umbraGates2', 'ptr'), ('umbraTomeSize2', 'u32'), ('umbraTomeData2', 'ptr'), ('umbraTomePtr2', 'ptr'),
        ('umbraUnkSize', 'u32'), ('umbraUnkData', 'ptr'))
_schema('srfTriangles_t', ('vertexLayerData', 'u32'), ('firstVertex', 'u32'), ('maxEdgeLength', 'f32'),
        ('vertexCount', 'u16'), ('triCount', 'u16'), ('baseIndex', 'u32'))
_schema('GfxSurface', ('tris', 'srfTriangles_t'), ('material', 'ptr'), ('lightmapIndex', 'u8'), ('flags', 'u8'),
        ('sortKey', 'u16'), ('unk1', 'u8'), ('unk2', 'u8'), ('unk3', 'u8'), ('unk4', 'u8'), ('transientZone', 'u8'))
_schema('GfxStaticModelInst', ('bounds', 'Bounds'), ('lightingOrigin', 'f32', 3))
_schema('GfxStaticModelVertexLightingInfo', ('lightingValues', 'ptr'), ('smodelLightingVb', 'ptr'),
        ('lightingValuesVb', 'ptr'), ('cacheSize', 'u32'), ('cacheBuffer', 'ptr'), ('cacheView', 'ptr'), ('flags', 'i32'),
        ('numLightingValues', 'u32'))
_schema('GfxStaticModelDrawInst', ('origin', 'f32', 3), ('axis', 'f32', 9), ('scale', 'f32'), ('model', 'ptr'),
        ('vertexLightingInfo', 'GfxStaticModelVertexLightingInfo'), ('lmOffset', 'f32', 2), ('lmScale', 'f32', 2),
        ('lmIndex', 'i32'), ('unk0', 'u16'), ('unk1', 'u16'), ('unk2', 'u16'), ('unk3', 'u16'),
        ('lightingHandle', 'u16'), ('unk5', 'u16'), ('unk6', 'u16', 4), ('cullDist', 'u16'), ('flags', 'u16'),
        ('unk9', 'u16'), ('unk10', 'u16'), ('unk11', 'u16'), ('unk13', 'u8'), ('unk14', 'u8'), ('unk15', 'u8', 4),
        ('primaryLightEnvIndex', 'u16'), ('reflectionProbeIndex', 'u8'), ('firstMtlSkinIndex', 'u8'),
        ('sunShadowFlags', 'u8'), ('transientZone', 'u8'), ('unk21', 'u8'))
_schema('GfxSurfaceBounds', ('bounds', 'Bounds'), ('unk', 'u32', 3))
_schema('GfxBrushModel', ('writableBounds', 'Bounds'), ('bounds', 'Bounds'), ('radius', 'f32'),
        ('startSurfIndex', 'u32'), ('surfaceCount', 'u16'))
_schema('GfxVoxelTree', ('zoneBound', 'Bounds'), ('voxelTopDownViewNodeCount', 'i32'), ('voxelInternalNodeCount', 'i32'),
        ('voxelLeafNodeCount', 'i32'), ('lightListArraySize', 'i32'), ('voxelTreeHeader', 'ptr'),
        ('voxelTopDownViewNodeArray', 'ptr'), ('voxelInternalNodeArray', 'ptr'), ('voxelLeafNodeArray', 'ptr'),
        ('lightListArray', 'ptr'), ('voxelInternalNodeDynamicLightList', 'ptr'), ('pad', 'u8', 24))
_schema('GfxFrustumLights', ('indexCount', 'u32'), ('indices', 'ptr'), ('vertexCount', 'u32'), ('vertices', 'ptr'),
        ('indexBuffer', 'ptr'), ('vertexBuffer', 'ptr'))
_schema('GfxLightViewFrustum', ('planeCount', 'u32'), ('planes', 'ptr'), ('indexCount', 'u32'), ('indices', 'ptr'),
        ('vertexCount', 'u32'), ('vertices', 'ptr'))
_schema('GfxShadowGeometry', ('surfaceCount', 'u16'), ('smodelCount', 'u16'), ('sortedSurfIndex', 'ptr'),
        ('smodelIndex', 'ptr'))
_schema('GfxLightRegion', ('hullCount', 'u32'), ('hulls', 'ptr'))
_schema('GfxLightRegionHull', ('kdopMidPoint', 'f32', 9), ('kdopHalfSize', 'f32', 9), ('axisCount', 'u32'), ('axis', 'ptr'))
_schema('GfxWorldVertex', ('xyz', 'f32', 3), ('binormalSign', 'f32'), ('color', 'u32'), ('texCoord', 'f32', 2),
        ('lmapCoord', 'f32', 2), ('normal', 'u32'), ('tangent', 'u32'))
_schema('GfxAabbTree', ('bounds', 'Bounds'), ('childCount', 'u16'), ('surfaceCount', 'u16'), ('startSurfIndex', 'u32'),
        ('smodelIndexCount', 'u16'), ('smodelIndexes', 'ptr'), ('childrenOffset', 'i32'))
_schema('GfxWorldTransientZone', ('name', 'ptr'), ('transientZoneIndex', 'u32'), ('vertexCount', 'u32'),
        ('vertices', 'ptr'), ('worldVb', 'ptr'), ('vertexLayerDataSize', 'u32'), ('vldData', 'ptr'), ('layerVb', 'ptr'),
        ('cellCount', 'u32'), ('aabbTreeCounts', 'ptr'), ('aabbTrees', 'ptr'))
_schema('ComPrimaryLight', ('type', 'u8'), ('canUseShadowMap', 'u8'), ('needsDynamicShadows', 'u8'),
        ('isVolumetric', 'u8'), ('exponent', 'u8'), ('unused', 'u8', 3), ('transientZoneList', 'u32'),
        ('entityId', 'u32'), ('uvIntensity', 'f32'), ('irIntensity', 'f32'), ('color', 'f32', 3), ('dir', 'f32', 3),
        ('up', 'f32', 3), ('origin', 'f32', 3), ('radius', 'f32'), ('fadeOffsetRt', 'f32', 2), ('bulbRadius', 'f32'),
        ('bulbLength', 'f32', 3), ('cosHalfFovOuter', 'f32'), ('cosHalfFovInner', 'f32'), ('shadowSoftness', 'f32'),
        ('shadowBias', 'f32'), ('shadowArea', 'f32'), ('distanceFalloff', 'f32'), ('rotationLimit', 'f32'),
        ('translationLimit', 'f32'), ('defName', 'ptr'))
_schema('ComPrimaryLightEnv', ('primaryLightIndices', 'u16', 4), ('numIndices', 'u8'))
_schema('ComWorld', ('name', 'ptr'), ('isInUse', 'i32'), ('useForwardPlus', 'i32'), ('bakeQuality', 'u32'),
        ('primaryLightCount', 'u32'), ('primaryLights', 'ptr'), ('scriptablePrimaryLightCount', 'u32'),
        ('firstScriptablePrimaryLight', 'u32'), ('primaryLightEnvCount', 'u32'), ('primaryLightEnvs', 'ptr'),
        ('changeListNumber', 'u32'), ('changeListTime', 'i32'), ('changeListUserName', 'ptr'),
        ('numUmbraGates', 'u32'), ('umbraGateNames', 'ptr'), ('umbraGateInitialStates', 'i32', 4))

# sizes and offsets that structs.hpp asserts: a wrong transcription fails here, at import
_ASSERTED = {'GfxWorld': 0x11A8, 'GfxSky': 32, 'GfxWorldDpvsPlanes': 32, 'GfxReflectionProbe': 48,
             'GfxWorldReflectionProbeData': 112, 'GfxWorldLightmapReindexData': 32, 'GfxWorldDraw': 536,
             'GfxLightGrid': 0x6D8, 'GfxLightGridProbeData': 240, 'GfxVoxelTree': 112, 'GfxFrustumLights': 48,
             'GfxLightViewFrustum': 48, 'GfxWorldLightLists': 48, 'GfxBrushModel': 60, 'sunflare_t': 112,
             'GfxShadowGeometry': 24, 'GfxLightAABB': 24, 'GfxSurface': 48, 'GfxStaticModelDrawInst': 184,
             'GfxSurfaceBounds': 36, 'GfxWorldDpvsStatic': 920, 'GfxWorldDpvsDynamic': 512, 'GfxWorldVertex': 44,
             'GfxAabbTree': 56, 'GfxWorldTransientZone': 0x50, 'ComPrimaryLight': 144, 'ComWorld': 0x68,
             'GfxStaticModelVertexLightingInfo': 56}
_ASSERTED_OFFSETS = {('GfxWorld', 'dpvsPlanes.cellCount'): 120, ('GfxWorld', 'voxelTreeCount'): 2472,
                     ('GfxWorld', 'models'): 2560, ('GfxWorld', 'materialMemory'): 2600,
                     ('GfxWorld', 'outdoorImage'): 2784, ('GfxWorld', 'cellHasSunLitSurfsBits'): 2816,
                     ('GfxWorld', 'sceneDynModel'): 2824, ('GfxWorld', 'shadowGeomOptimized'): 2936,
                     ('GfxWorld', 'lightAABB.nodeCount'): 2952, ('GfxWorld', 'heroOnlyLights'): 4416,
                     ('GfxWorld', 'numUmbraGates'): 4424, ('GfxWorld', 'numUmbraGates2'): 4464,
                     ('GfxWorld', 'umbraUnkData'): 4512, ('GfxWorldDraw', 'iesLookupTexture'): 144,
                     ('GfxWorldDraw', 'decalVolumeCollectionCount'): 152, ('GfxWorldDraw', 'transientZones[0]'): 240,
                     ('GfxWorldDraw', 'indices'): 504, ('GfxWorldDraw', 'indexBuffer'): 512,
                     ('GfxWorldDraw', 'volumetrics.volumetricCount'): 520, ('GfxLightGrid', 'stageCount'): 47,
                     ('GfxVoxelTree', 'voxelTreeHeader'): 40, ('GfxVoxelTree', 'voxelInternalNodeDynamicLightList'): 80,
                     ('GfxSurface', 'material'): 24, ('GfxStaticModelDrawInst', 'model'): 56,
                     ('GfxStaticModelDrawInst', 'vertexLightingInfo.lightingValues'): 64,
                     ('GfxStaticModelDrawInst', 'cullDist'): 160}
for _n, _s in _ASSERTED.items():
    assert layout(_n).size == _s, ('layout', _n, layout(_n).size, _s)
for (_n, _p), _o in _ASSERTED_OFFSETS.items():
    assert layout(_n).off(_p) == _o, ('offset', _n, _p, layout(_n).off(_p), _o)

# element sizes of arrays that are only walked over (structs.hpp assert_sizeof or sum of the members)
SZ = {'ptr': 8, 'u8': 1, 'u16': 2, 'u32': 4, 'i32': 4, 'vec3': 12, 'vec4': 16, 'cplane': 20, 'GfxCellTransientInfo': 4,
      'probeRelighting': 20, 'GfxReflectionProbeInstance': 152, 'GfxReflectionProbeSampleData': 32,
      'reindexElement': 20, 'packedLightmap': 8, 'decalVolume': 388, 'GfxVolumetric': 240, 'GfxSHProbeData': 64,
      'GfxGpuLightGridProbePosition': 12, 'GfxGpuLightGridZone': 88, 'tetrahedron': 16, 'tetrahedronNeighbors': 16,
      'tetrahedronVisibility': 64, 'GfxVoxelTreeHeader': 64, 'GfxVoxelTopDownViewNode': 12,
      'GfxVoxelInternalNode': 16, 'GfxVoxelLeafNode': 2, 'GfxHeightfield': 96, 'MaterialMemory': 16,
      'GfxLightRegionAxis': 20, 'GfxLightAABBNode': 28, 'GfxStaticModelVertexLighting': 20, 'GfxHeroOnlyLight': 68,
      'UmbraGate': 32, 'UmbraGate2': 40, 'GfxCellTreeCount': 4, 'GfxCellTree': 8}


# ---------------------------------------------------------------- the record stream

class Arr:
    """A located array: byte offset of the first element and the element count."""
    __slots__ = ('off', 'count')

    def __init__(self, off, count):
        self.off, self.count = off, count


class Stream:
    def __init__(self, buf, label):
        self.b = buf
        self.p = 0
        self.label = label
        self.entries = []  # ('array', offset, count, elem) | ('string', text) | ('asset', name)

    def fail(self, msg, at=None):
        at = self.p if at is None else at
        raise WorldError('%s: offset %d (0x%x): %s' % (self.label, at, at, msg))

    def need(self, n, what=''):
        if n < 0 or self.p + n > len(self.b):
            self.fail('need %d bytes%s but only %d remain' % (n, (' for ' + what) if what else '', len(self.b) - self.p))

    def u8(self):
        self.need(1)
        v = self.b[self.p]
        self.p += 1
        return v

    def u32(self):
        self.need(4)
        v = struct.unpack_from('<I', self.b, self.p)[0]
        self.p += 4
        return v

    def _repeat(self, what):
        idx, aidx = self.u32(), self.u32()
        if idx >= len(self.entries):
            self.fail('%s repeat refers to entry %d but only %d entries exist' % (what, idx, len(self.entries)))
        return self.entries[idx], aidx

    def _cstr(self, what):
        end = self.b.find(b'\0', self.p)
        if end < 0:
            self.fail('unterminated %s' % what)
        text = self.b[self.p:end].decode('latin-1')
        self.p = end + 1
        return text

    def array(self, elem, expected, what, required=False):
        """One dump_array record. Returns Arr, or None for a null/empty array. `expected` is the element
        count the owning structure declares; the file count must equal it."""
        start = self.p
        t = self.u8()
        if t == T_ARRAY:
            if self.u8() == 0:
                if required and expected:
                    self.fail('%s: %d elements declared but the array is absent' % (what, expected), start)
                return None
            n = self.u32()
            if n != expected:
                self.fail('%s: file holds %d elements but the structure declares %d' % (what, n, expected), start)
            self.need(n * elem, what)
            off = self.p
            self.p += n * elem
            self.entries.append(('array', off, n, elem))
            return Arr(off, n)
        if t == T_OFFSET:
            e, aidx = self._repeat(what)
            if e[0] != 'array':
                self.fail('%s: repeat refers to a %s entry' % (what, e[0]), start)
            off = e[1] + aidx * elem
            if off + expected * elem > e[1] + e[2] * e[3]:
                self.fail('%s: repeat runs past the end of entry (%d elements from index %d)' % (what, expected, aidx), start)
            return Arr(off, expected)
        self.fail('%s: expected an array record (8) or a repeat (9), found %d' % (what, t), start)

    def string(self, what='string'):
        start = self.p
        t = self.u8()
        if t == T_STRING:
            if self.u8() == 0:
                return None
            text = self._cstr(what)
            self.entries.append(('string', text))
            return text
        if t == T_OFFSET:
            e, aidx = self._repeat(what)
            if e[0] == 'string':
                return e[1][aidx:]
            if e[0] == 'array':
                end = self.b.find(b'\0', e[1] + aidx)
                return self.b[e[1] + aidx:end].decode('latin-1')
            self.fail('%s: repeat refers to a %s entry' % (what, e[0]), start)
        self.fail('%s: expected a string record (6) or a repeat (9), found %d' % (what, t), start)

    def asset(self, what='asset'):
        start = self.p
        t = self.u8()
        if t == T_ASSET:
            if self.u8() == 0:
                return None
            name = self._cstr(what)
            self.entries.append(('asset', name))
            return name
        if t == T_OFFSET:
            e, aidx = self._repeat(what)
            if e[0] != 'asset' or aidx != 0:
                self.fail('%s: repeat refers to a %s entry (array index %d)' % (what, e[0], aidx), start)
            return e[1]
        self.fail('%s: expected an asset record (7) or a repeat (9), found %d' % (what, t), start)

    def finish(self):
        if self.p != len(self.b):
            self.fail('parsed to offset %d but the file is %d bytes: %d trailing bytes' % (self.p, len(self.b), len(self.b) - self.p), self.p)


# ---------------------------------------------------------------- gfxmap

class GfxWorldData:
    """Everything kept from a .gfxmap; the arrays that are only walked over are not retained."""


# a count above this is not a plausible world; it stops a misread count from allocating the machine away
_LIMITS = {'surfaceCount': 2_000_000, 'smodelCount': 2_000_000, 'primaryLightCount': 200_000, 'indexCount': 200_000_000,
           'reflectionProbeCount': 100_000, 'cellCount': 1_000_000}


def parse_gfxmap(buf, label='gfxmap'):
    s = Stream(buf, label)
    W = layout('GfxWorld')
    wa = s.array(W.size, 1, 'GfxWorld', required=True)
    wb = wa.off

    def g(path):
        return W.get(buf, wb, path)

    d = GfxWorldData()
    d.header = {k: g(k) for k in ('bspVersion', 'planeCount', 'nodeCount', 'surfaceCount', 'skyCount',
                                  'lastSunPrimaryLightIndex', 'primaryLightCount', 'movingScriptablePrimaryLightCount',
                                  'checksum', 'mapVtxChecksum', 'modelCount', 'materialMemoryCount',
                                  'heroOnlyLightCount', 'numUmbraGates', 'umbraTomeSize', 'numUmbraGates2',
                                  'umbraTomeSize2', 'umbraUnkSize', 'voxelTreeCount', 'heightfieldCount')}
    for k in ('smodelCount', 'staticSurfaceCount', 'surfaceVisDataCount'):
        d.header['dpvs.' + k] = g('dpvs.' + k)
    for k in ('indexCount', 'lightMapCount', 'transientZoneCount'):
        d.header['draw.' + k] = g('draw.' + k)
    for k in ('reflectionProbeCount', 'sharedReflectionProbeCount', 'reflectionProbeInstanceCount'):
        d.header['draw.' + k] = g('draw.reflectionProbeData.' + k)
    d.header['bounds'] = [g('bounds.mid[%d]' % i) for i in range(3)] + [g('bounds.half[%d]' % i) for i in range(3)]
    for k, lim in (('surfaceCount', 'surfaceCount'), ('primaryLightCount', 'primaryLightCount')):
        if d.header[k] > _LIMITS[lim]:
            s.fail('%s = %d is not plausible' % (k, d.header[k]), wa.off)
    if d.header['dpvs.smodelCount'] > _LIMITS['smodelCount']:
        s.fail('smodelCount = %d is not plausible' % d.header['dpvs.smodelCount'], wa.off)
    if d.header['draw.indexCount'] > _LIMITS['indexCount']:
        s.fail('indexCount = %d is not plausible' % d.header['draw.indexCount'], wa.off)
    for k in ('planeCount', 'nodeCount', 'skyCount', 'modelCount', 'materialMemoryCount', 'voxelTreeCount', 'heightfieldCount'):
        if d.header[k] < 0:
            s.fail('%s = %d is negative' % (k, d.header[k]), wa.off)

    d.name = s.string('GfxWorld.name')
    d.base_name = s.string('GfxWorld.baseName')
    names = []  # (kind, index, name) for every named asset the world references besides models/materials

    def named(kind, idx, name):
        if name:
            names.append((kind, idx, name))

    # skies
    sky_count = g('skyCount')
    skies = s.array(layout('GfxSky').size, sky_count, 'skies')
    for i in range(sky_count):
        if skies is None:
            break
        n = struct.unpack_from('<i', buf, skies.off + 32 * i)[0]
        s.array(4, n, 'skyStartSurfs')
        named('sky_image', i, s.asset('skyImage'))
    # dpvs planes, nodes, cells
    s.array(SZ['cplane'], g('planeCount'), 'planes')
    s.array(2, g('nodeCount'), 'nodes')
    cell_count = g('dpvsPlanes.cellCount')
    if cell_count < 0 or cell_count > _LIMITS['cellCount']:
        s.fail('cellCount = %d is not plausible' % cell_count, wa.off)
    s.array(SZ['GfxCellTransientInfo'], cell_count, 'cellTransientInfos')
    CL, PL = layout('GfxCell'), layout('GfxPortal')
    cells = s.array(CL.size, cell_count, 'cells')
    for i in range(cell_count):
        if cells is None:
            break
        pc = CL.get(buf, cells.off + CL.size * i, 'portalCount')
        portals = s.array(PL.size, pc, 'portals')
        for j in range(pc):
            if portals is None:
                break
            vc = PL.get(buf, portals.off + PL.size * j, 'vertexCount')
            s.array(SZ['vec3'], vc if vc > 0 else 0, 'portal vertices')
    # reflection probes
    RP = layout('GfxReflectionProbe')
    rpc = g('draw.reflectionProbeData.reflectionProbeCount')
    if rpc > _LIMITS['reflectionProbeCount']:
        s.fail('reflectionProbeCount = %d is not plausible' % rpc, wa.off)
    probes = s.array(RP.size, rpc, 'reflectionProbes')
    d.probes = []
    for i in range(rpc):
        if probes is None:
            break
        base = probes.off + RP.size * i
        live = s.string('probe livePath')
        s.array(4, RP.get(buf, base, 'probeInstanceCount'), 'probeInstances')
        d.probes.append((i, live, tuple(RP.get(buf, base, 'origin[%d]' % k) for k in range(3)),
                         tuple(RP.get(buf, base, 'angles[%d]' % k) for k in range(3)), RP.get(buf, base, 'probeInstanceCount')))
    named('reflection_probe_array_image', 0, s.asset('reflectionProbeArrayImage'))
    s.array(SZ['probeRelighting'], g('draw.reflectionProbeData.probeRelightingCount'), 'probeRelightingData')
    gbc = g('draw.reflectionProbeData.reflectionProbeGBufferImageCount')
    s.array(8, gbc, 'reflectionProbeGBufferImages')
    for i in range(gbc):
        named('probe_gbuffer_image', i, s.asset('gbuffer image'))
    ric = g('draw.reflectionProbeData.reflectionProbeInstanceCount')
    s.array(SZ['GfxReflectionProbeInstance'], ric, 'reflectionProbeInstances')
    d.probe_instances = []
    for i in range(ric):
        a, b = s.string('probe instance livePath'), s.string('probe instance livePath2')
        d.probe_instances.append((i, a, b))
    s.array(SZ['GfxReflectionProbeSampleData'], rpc, 'reflectionProbeLightgridSampleData')
    s.array(SZ['reindexElement'], g('draw.lightmapReindexData.reindexCount'), 'reindexElement')
    s.array(SZ['packedLightmap'], g('draw.lightmapReindexData.packedLightmapCount'), 'packedLightmap')
    named('ies_lookup_texture', 0, s.asset('iesLookupTexture'))
    s.array(SZ['decalVolume'], g('draw.decalVolumeCollectionCount'), 'decalVolumeCollections')
    named('lightmap_override_primary', 0, s.asset('lightmapOverridePrimary'))
    named('lightmap_override_secondary', 0, s.asset('lightmapOverrideSecondary'))
    lmc = g('draw.lightMapCount')
    s.array(8, lmc, 'lightMaps')
    for i in range(lmc):
        named('lightmap', i, s.asset('lightmap'))
    d.transient_zones = []
    for i in range(32):
        z = s.asset('transientZone')
        d.transient_zones.append(z)
        named('transient_zone', i, z)
    index_count = g('draw.indexCount')
    d.indices = s.array(2, index_count, 'draw.indices', required=True)
    vc = g('draw.volumetrics.volumetricCount')
    s.array(SZ['GfxVolumetric'], vc, 'volumetrics')
    for i in range(vc):
        s.string('volumetric livePath')
        for m in range(4):
            named('volumetric_mask_image', i * 4 + m, s.asset('volumetric mask image'))
    # light grid
    s.array(4, g('lightGrid.stageCount'), 'stageLightingContrastGain')
    s.array(4, g('lightGrid.paletteEntryCount'), 'paletteEntryAddress')
    s.array(1, g('lightGrid.paletteBitstreamSize'), 'paletteBitstream')
    nc = g('lightGrid.tree.nodeCount')
    s.array(4, nc if nc > 0 else 0, 'lightGrid p_nodeTable')
    ls = g('lightGrid.tree.leafTableSize')
    s.array(1, ls if ls > 0 else 0, 'lightGrid p_leafTable')
    pd = 'lightGrid.probeData.'
    gvc = g(pd + 'gpuVisibleProbesCount')
    s.array(SZ['GfxGpuLightGridProbePosition'], gvc, 'gpuVisibleProbePositions')
    s.array(SZ['GfxSHProbeData'], (gvc + 0x2000) & 0xFFFFFFFF, 'gpuVisibleProbesData')
    pcount = g(pd + 'probeCount')
    s.array(SZ['GfxSHProbeData'], pcount, 'light grid probes')
    s.array(SZ['GfxGpuLightGridProbePosition'], pcount, 'probePositions')
    s.array(SZ['GfxGpuLightGridZone'], g(pd + 'zoneCount'), 'light grid zones')
    tc = g(pd + 'tetrahedronCount')
    s.array(SZ['tetrahedron'], tc, 'tetrahedrons')
    s.array(SZ['tetrahedronNeighbors'], tc, 'tetrahedronNeighbors')
    s.array(SZ['tetrahedronVisibility'], g(pd + 'tetrahedronCountVisible'), 'tetrahedronVisibility')
    s.array(4, g(pd + 'voxelStartTetrahedronCount'), 'voxelStartTetrahedron')
    plc = g('primaryLightCount')
    # per-light frustum data
    FL, LV = layout('GfxFrustumLights'), layout('GfxLightViewFrustum')
    fl = s.array(FL.size, plc, 'frustumLights')
    for i in range(plc if fl else 0):
        base = fl.off + FL.size * i
        s.array(2, FL.get(buf, base, 'indexCount'), 'frustumLights indices')
        s.array(1, 32 * FL.get(buf, base, 'vertexCount'), 'frustumLights vertices')
    lv = s.array(LV.size, plc, 'lightViewFrustums')
    for i in range(plc if lv else 0):
        base = lv.off + LV.size * i
        s.array(SZ['vec4'], LV.get(buf, base, 'planeCount'), 'lightViewFrustum planes')
        s.array(2, LV.get(buf, base, 'indexCount'), 'lightViewFrustum indices')
        s.array(SZ['vec3'], LV.get(buf, base, 'vertexCount'), 'lightViewFrustum vertices')
    VT = layout('GfxVoxelTree')
    vtc = g('voxelTreeCount')
    vt = s.array(VT.size, vtc, 'voxelTree')
    for i in range(vtc if vt else 0):
        base = vt.off + VT.size * i
        s.array(SZ['GfxVoxelTreeHeader'], 1, 'voxelTreeHeader')
        s.array(SZ['GfxVoxelTopDownViewNode'], VT.get(buf, base, 'voxelTopDownViewNodeCount'), 'voxelTopDownViewNodeArray')
        s.array(SZ['GfxVoxelInternalNode'], VT.get(buf, base, 'voxelInternalNodeCount'), 'voxelInternalNodeArray')
        s.array(SZ['GfxVoxelLeafNode'], VT.get(buf, base, 'voxelLeafNodeCount'), 'voxelLeafNodeArray')
        s.array(2, VT.get(buf, base, 'lightListArraySize'), 'lightListArray')
    hfc = g('heightfieldCount')
    s.array(SZ['GfxHeightfield'], hfc, 'heightfields')
    for i in range(hfc):
        named('heightfield_image', i, s.asset('heightfield image'))
    s.array(2, g('lightLists.listsSize'), 'lightLists.lists')
    BM = layout('GfxBrushModel')
    mc = g('modelCount')
    models = s.array(BM.size, mc, 'brush models')
    d.brush_models = []
    for i in range(mc if models else 0):
        base = models.off + BM.size * i
        d.brush_models.append((i, tuple(BM.get(buf, base, 'bounds.mid[%d]' % k) for k in range(3)),
                               tuple(BM.get(buf, base, 'bounds.half[%d]' % k) for k in range(3)),
                               BM.get(buf, base, 'radius'), BM.get(buf, base, 'startSurfIndex'),
                               BM.get(buf, base, 'surfaceCount')))
    mmc = g('materialMemoryCount')
    s.array(SZ['MaterialMemory'], mmc, 'materialMemory')
    for i in range(mmc):
        s.asset('materialMemory material')
    named('sun_sprite_material', 0, s.asset('sun.spriteMaterial'))
    named('sun_flare_material', 0, s.asset('sun.flareMaterial'))
    named('outdoor_image', 0, s.asset('outdoorImage'))
    named('dust_material', 0, s.asset('dustMaterial'))
    SG = layout('GfxShadowGeometry')
    sg = s.array(SG.size, plc, 'shadowGeomOptimized')
    for i in range(plc if sg else 0):
        base = sg.off + SG.size * i
        s.array(4, SG.get(buf, base, 'surfaceCount'), 'shadow sortedSurfIndex')
        s.array(2, SG.get(buf, base, 'smodelCount'), 'shadow smodelIndex')
    LR, LH = layout('GfxLightRegion'), layout('GfxLightRegionHull')
    lr = s.array(LR.size, plc, 'lightRegion')
    for i in range(plc if lr else 0):
        base = lr.off + LR.size * i
        hc = LR.get(buf, base, 'hullCount')
        hulls = s.array(LH.size, hc, 'lightRegion hulls')
        for j in range(hc if hulls else 0):
            s.array(SZ['GfxLightRegionAxis'], LH.get(buf, hulls.off + LH.size * j, 'axisCount'), 'lightRegion axis')
    s.array(SZ['GfxLightAABBNode'], g('lightAABB.nodeCount'), 'lightAABB nodeArray')
    s.array(2, g('lightAABB.lightCount'), 'lightAABB lightArray')

    # static world: the part this tool exists for
    smc, ssc, sfc = g('dpvs.smodelCount'), g('dpvs.staticSurfaceCount'), g('surfaceCount')
    d.lod_data = s.array(4, smc + 1, 'dpvs.lodData')
    s.array(4, ssc, 'dpvs.sortedSurfIndex')
    SI, SF, SD = layout('GfxStaticModelInst'), layout('GfxSurface'), layout('GfxStaticModelDrawInst')
    d.smodel_insts = s.array(SI.size, smc, 'dpvs.smodelInsts', required=True)
    d.surfaces = s.array(SF.size, sfc, 'dpvs.surfaces', required=True)
    d.surface_materials = [s.asset('surface material') for _ in range(sfc if d.surfaces else 0)]
    d.surface_bounds = s.array(layout('GfxSurfaceBounds').size, sfc, 'dpvs.surfacesBounds')
    d.draw_insts = s.array(SD.size, smc, 'dpvs.smodelDrawInsts', required=True)
    d.smodel_models = []
    d.smodel_lighting_values = []
    for i in range(smc if d.draw_insts else 0):
        d.smodel_models.append(s.asset('smodel model'))
        nlv = SD.get(buf, d.draw_insts.off + SD.size * i, 'vertexLightingInfo.numLightingValues')
        s.array(SZ['GfxStaticModelVertexLighting'], nlv, 'smodel lightingValues')
    s.array(4, g('dpvs.surfaceVisDataCount'), 'surfaceCastsSunShadow')
    d.sorted_smodel_indices = s.array(2, smc, 'dpvs.sortedSmodelIndices')
    s.array(SZ['GfxHeroOnlyLight'], g('heroOnlyLightCount'), 'heroOnlyLights')
    s.array(SZ['UmbraGate'], g('numUmbraGates'), 'umbraGates')
    s.array(1, g('umbraTomeSize'), 'umbraTomeData')
    s.array(SZ['UmbraGate2'], g('numUmbraGates2'), 'umbraGates2')
    s.array(1, g('umbraTomeSize2'), 'umbraTomeData2')
    s.array(1, g('umbraUnkSize'), 'umbraUnkData')
    s.finish()
    d.named_assets = names
    d.end = s.p
    d.entries = len(s.entries)
    d.layout = (W, SI, SF, SD)
    d.buf = buf
    return d


def parse_transient_zone(buf, label='gfxmap_tr'):
    s = Stream(buf, label)
    Z = layout('GfxWorldTransientZone')
    za = s.array(Z.size, 1, 'GfxWorldTransientZone', required=True)

    def g(path):
        return Z.get(buf, za.off, path)

    zone = type('Zone', (), {})()
    zone.name = s.string('zone name')
    vc, vls, cc = g('vertexCount'), g('vertexLayerDataSize'), g('cellCount')
    zone.index = g('transientZoneIndex')
    zone.vertex_count = vc
    zone.vertices = s.array(layout('GfxWorldVertex').size, vc, 'zone vertices', required=True)
    zone.layer_data = s.array(1, vls, 'zone vertex layer data')
    zone.cell_count = cc
    counts = s.array(4, cc, 'aabbTreeCounts')
    trees = s.array(8, cc, 'aabbTrees')
    AT = layout('GfxAabbTree')
    tree_total = 0
    for i in range(cc if trees else 0):
        n = struct.unpack_from('<i', buf, counts.off + 4 * i)[0] if counts else 0
        arr = s.array(AT.size, n if n > 0 else 0, 'aabbTree')
        for j in range(n if arr else 0):
            s.array(2, AT.get(buf, arr.off + AT.size * j, 'smodelIndexCount'), 'aabb smodelIndexes')
            tree_total += 1
    zone.tree_nodes = tree_total
    s.finish()
    zone.end = s.p
    return zone


# ---------------------------------------------------------------- com world (lights)

LIGHT_FIELDS = ['type', 'canUseShadowMap', 'needsDynamicShadows', 'isVolumetric', 'exponent', 'transientZoneList',
                'entityId', 'uvIntensity', 'irIntensity', 'color', 'dir', 'up', 'origin', 'radius', 'fadeOffsetRt',
                'bulbRadius', 'bulbLength', 'cosHalfFovOuter', 'cosHalfFovInner', 'shadowSoftness', 'shadowBias',
                'shadowArea', 'distanceFalloff', 'rotationLimit', 'translationLimit', 'defName']
LIGHT_ARRAYS = {'color': 3, 'dir': 3, 'up': 3, 'origin': 3, 'fadeOffsetRt': 2, 'bulbLength': 3}


def parse_commap_binary(buf, label='commap'):
    """The binary .commap (the asset tool writes JSON instead; both are accepted)."""
    s = Stream(buf, label)
    C = layout('ComWorld')
    ca = s.array(C.size, 1, 'ComWorld', required=True)
    out = {k: C.get(buf, ca.off, k) for k in ('isInUse', 'useForwardPlus', 'bakeQuality', 'scriptablePrimaryLightCount',
                                              'firstScriptablePrimaryLight', 'changeListNumber', 'changeListTime')}
    out['name'] = s.string('ComWorld.name')
    n = C.get(buf, ca.off, 'primaryLightCount')
    L = layout('ComPrimaryLight')
    arr = s.array(L.size, n, 'primaryLights', required=True)
    lights = []
    for i in range(n if arr else 0):
        base = arr.off + L.size * i
        light = {'primaryLightIndex': i}
        for f in LIGHT_FIELDS[:-1]:
            if f in LIGHT_ARRAYS:
                light[f] = [L.get(buf, base, '%s[%d]' % (f, k)) for k in range(LIGHT_ARRAYS[f])]
            else:
                light[f] = L.get(buf, base, f)
        light['defName'] = s.string('light defName')
        lights.append(light)
    out['primaryLight'] = lights
    envn = C.get(buf, ca.off, 'primaryLightEnvCount')
    E = layout('ComPrimaryLightEnv')
    s.array(E.size, envn, 'primaryLightEnvs')
    out['changeListUserName'] = s.string('changeList userName')
    out['umbraGateNames'] = [s.string('umbra gate name') for _ in range(C.get(buf, ca.off, 'numUmbraGates'))]
    s.finish()
    return out


# ---------------------------------------------------------------- vertices

def decode_unit(packed):
    """10:10:10:2 packed unit vector (x bits 0-9, y 10-19, z 20-29), as the project's generator packs them."""
    return ((packed & 1023) / 511.5 - 1.0, ((packed >> 10) & 1023) / 511.5 - 1.0, ((packed >> 20) & 1023) / 511.5 - 1.0)


VERTEX_SIZE = layout('GfxWorldVertex').size


def decode_vertices(raw, count):
    """positions, normals, texcoords, lightmap coords of `count` 44-byte world vertices, as lists of tuples."""
    if np is not None:
        fl = np.frombuffer(raw, dtype='<f4', count=count * 11).reshape(count, 11)
        u = np.frombuffer(raw, dtype='<u4', count=count * 11).reshape(count, 11)
        pos = [tuple(map(float, r)) for r in fl[:, 0:3]]
        uv = [tuple(map(float, r)) for r in fl[:, 5:7]]
        lm = [tuple(map(float, r)) for r in fl[:, 7:9]]
        nrm = [decode_unit(int(p)) for p in u[:, 9]]
        return pos, nrm, uv, lm
    pos, nrm, uv, lm = [], [], [], []
    for rec in struct.iter_unpack('<3ffI2f2fII', raw[:count * VERTEX_SIZE]):
        pos.append(rec[0:3])
        uv.append(rec[5:7])
        lm.append(rec[7:9])
        nrm.append(decode_unit(rec[9]))
    return pos, nrm, uv, lm


def decode_vertex_extras(raw, count):
    """The vertex fields decode_vertices leaves out, as lists: tangents (decoded like the normals), the raw fourth
    float of the vertex (named binormalSign in the asset tool; kept as stored) and the vertex colour (u32)."""
    tan, sign, col = [], [], []
    for rec in struct.iter_unpack('<3ffI2f2fII', raw[:count * VERTEX_SIZE]):
        tan.append(decode_unit(rec[10]))
        sign.append(rec[3])
        col.append(rec[4])
    return tan, sign, col
