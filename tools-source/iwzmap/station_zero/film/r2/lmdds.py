"""decode an emit's installed lightmap DDS set to npy (A, B top/bottom of secondary; D secondunorm)"""
import sys, os, numpy as np, importlib.util
spec = importlib.util.spec_from_file_location('iw7image', os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', 'bake', 'iw7image.py'))
M = importlib.util.module_from_spec(spec); spec.loader.exec_module(M)
src, out = sys.argv[1], sys.argv[2]; os.makedirs(out, exist_ok=True)
for k in ('primary', 'secondary', 'secondunorm'):
    fmt, w, h, data = M.read_dds(os.path.join(src, k + '.dds'))
    a = M.decode(fmt, w, h, data, os.path.join(out, 'tmp_' + k))
    print(k, fmt, w, h, a.shape, a[..., :3].reshape(-1, 3).mean(0))
    np.save(os.path.join(out, k + '.npy'), a.astype(np.float32))
