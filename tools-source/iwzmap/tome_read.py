"""Read an IW7 Umbra (format 20) tome header and the blocks it points at. usage: tome_read.py <tome>"""
import struct, sys, zlib

FIELDS = [  # (name, offset, fmt)
    ('versionMagic', 0x00, 'I'), ('crc32', 0x04, 'I'), ('size', 0x08, 'I'), ('lodBaseDistance', 0x0C, 'f'),
    ('flags', 0x10, 'I'), ('treeMin', 0x14, '3f'), ('treeMax', 0x20, '3f'),
    ('tileTree.nodeCount_mapWidth', 0x2C, 'I'), ('tileTree.treeData', 0x30, 'I'), ('tileTree.map', 0x34, 'I'),
    ('tileTree.numSplitValues', 0x38, 'I'), ('tileTree.splitValues', 0x3C, 'I'),
    ('numObjects', 0x40, 'i'), ('objBounds', 0x44, 'I'), ('objDistances', 0x48, 'I'), ('userIDStarts', 0x4C, 'I'),
    ('userIDs', 0x50, 'I'), ('listWidths', 0x54, 'I'), ('objectLists', 0x58, 'I'), ('objectListSize', 0x5C, 'i'),
    ('clusterLists', 0x60, 'I'), ('clusterListSize', 0x64, 'i'), ('numGates', 0x68, 'i'), ('gateIndexMap', 0x6C, 'I'),
    ('gateVertices', 0x70, 'I'), ('numGateVertices', 0x74, 'i'), ('gateIndices', 0x78, 'I'), ('numClusters', 0x7C, 'i'),
    ('clusters', 0x80, 'I'), ('clusterPortals', 0x84, 'I'), ('cellStarts', 0x88, 'I'), ('numLeafTiles', 0x8C, 'i'),
    ('numTiles', 0x90, 'i'), ('bitsPerSlotPath', 0x94, 'i'), ('slotPaths', 0x98, 'I'), ('tileLodLevels', 0x9C, 'I'),
    ('tiles', 0xA0, 'I'), ('tileMatchingData', 0xA4, 'I'), ('matchingTrees', 0xA8, 'I'), ('numMatchingTrees', 0xAC, 'i'),
    ('numTomes', 0xB0, 'i'), ('tomeClusterStarts', 0xB4, 'I'), ('tomeClusterPortalStarts', 0xB8, 'I'),
    ('objectDepthmaps', 0x13C, 'I'), ('depthmapFaces', 0x140, 'I'), ('depthmapPalettes', 0x144, 'I'),
    ('numFaces', 0x148, 'i'), ('tilePortalExpands', 0x14C, 'I'), ('boundsMin', 0x150, '3f'), ('boundsMax', 0x15C, '3f'),
    ('clusterCoordScale', 0x168, 'f'),
]

d = open(sys.argv[1], 'rb').read()
h = {}
for name, off, fmt in FIELDS:
    v = struct.unpack_from('<' + fmt, d, off)
    h[name] = v[0] if len(v) == 1 else v
    print('%-28s %-6s %s' % (name, hex(off), (hex(h[name]) if isinstance(h[name], int) and h[name] > 9 else h[name])))
crc = zlib.crc32(d[8:]) & 0xffffffff
print('size ok', h['size'] == len(d), 'crc32(zlib)', hex(crc))
print('computation string', d[0xBC:0x13C].split(b'\0')[0])
