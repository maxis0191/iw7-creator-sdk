"""Small original synthetic fixtures only; no native/retail/stock input or run."""
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

SDK = Path(__file__).resolve().parents[1]
ROOT = SDK.parents[1]
PIN = "77e6d4d24e918ee363b3feee3735c3b889dff7d7"
PREPARATION_LIMIT = 8 * 1024 * 1024


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


m = load(SDK / "creator_model_materialize.py", "model_materialize_tested")
sys.path.insert(0, str(ROOT / "ops/model-lab"))
try:
    import rigid_export as rigid
    import prepare_writer
finally:
    sys.path.pop(0)
sys.path.insert(0, str(rigid.BRIDGE))
try:
    fixture = load(rigid.BRIDGE / "test_readback.py", "model_materialize_fixture")
finally:
    sys.path.pop(0)


def encode(value):
    return (json.dumps(value, sort_keys=True, indent=2, ensure_ascii=True, allow_nan=False) + "\n").encode()


def sha(value):
    return hashlib.sha256(value).hexdigest()


class ModelMaterializeTests(unittest.TestCase):
    peak_preparation_bytes = 0

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.addCleanup(self.temp.cleanup)
        self.project, self.source, self.build, self.output = [self.root / p for p in ("project", "source", "build", "candidate")]
        self.project.mkdir(); self.build.mkdir()
        # Five explicit slots, including repeated materials/geometry aliases.
        self.fixture = fixture.SyntheticMulti(surfaces=[(fixture.PYRAMID, fixture.PYRAMID_FACES)] * 5,
            materials=['donor/a', 'donor/b', 'donor/a', 'donor/c', 'donor/b'], alias_geometry=True,
            names=('original/pilot', 'mesh/unrelated', 'root pivot', 'donor/a'))
        export = self.root / 'export'; export.mkdir()
        for role in ('model', 'mesh'):
            path = export / self.fixture.manifest[role]['relative_path']; path.parent.mkdir(parents=True)
            path.write_bytes(self.fixture.outputs[role])
        (export / 'request.json').write_bytes(rigid.json_bytes(self.fixture.request))
        (export / 'manifest.json').write_bytes(rigid.json_bytes(self.fixture.manifest))
        bindings = [dict(slot=i, source=name, target=rigid.MATERIAL)
                    for i, name in enumerate(self.fixture.manifest['material_dependencies'])]
        self.plan = rigid.stage(export, export/'request.json', export/'manifest.json', self.source,
                                lod_distance=1000000, rebinds=bindings)
        for role in ('model', 'mesh'):
            relative = self.fixture.manifest[role]['relative_path']
            dest = self.build / 'roundtrip' / relative; dest.parent.mkdir(parents=True)
            dest.write_bytes((self.source/relative).read_bytes())
        (self.build/'mod.ff').write_bytes(b'SYNTHETIC TEXT ONLY; NOT A FASTFILE OR ENGINE INPUT\n')
        self.proof = rigid.verify_dump(self.source, self.build/'roundtrip', self.build/'mod.ff')
        (self.build/'geometry-roundtrip.json').write_bytes(encode(self.proof))
        (self.build/'reader.stdout.json').write_bytes(encode(self.proof))
        rows = ['material,,'+rigid.MATERIAL, 'xmodel,original/pilot', 'xmodelsurfs,mesh/unrelated',
                'netconststrings,ncs_mdl_paris_model_probe', 'rawfile,paris_model_probe']
        (self.build/'assets.csv').write_text('\n'.join(rows)+'\n')
        log = 'Loading zone "paris_model_probe"\n'
        for row in rows:
            kind, name = row.split(',', 1)
            log += f'Loading asset "{name}" of type {kind}.\n'
        (self.build/'inventory.stdout.log').write_text(log)
        self.state = dict(Schema='iw7.model-ff-build/1', Status='BootstrapInventoryVerified', Restored=True,
            StockPreserved=True, InventoryVerified=True, GeometryRoundtripVerified=True, RestorationStatus='Confirmed',
            RetainedLeaseToken=None, CleanupError=None, Ready=False, SourcePlan=self.plan,
            SourcePlanSHA256=self.proof['source_plan_sha256'], GeometryEvidenceSHA256=sha(encode(self.proof)),
            Build={'ExitCode':0}, Dump={'ExitCode':0}, Offline={'ExitCode':0,'Stdout':str(self.build/'inventory.stdout.log')},
            GeometryReader={'ExitCode':0,'Stdout':str(self.build/'reader.stdout.json')},
            FF={'Path':'mod.ff','Bytes':self.proof['ff']['bytes'],'SHA256':self.proof['ff']['sha256']})
        (self.build/'state.local.json').write_bytes(encode(self.state))
        self.manifest = json.loads((SDK/'examples/beacon/manifest.json').read_bytes())
        # A visibly synthetic authored source fixture; the adapter never creates
        # or infers this lifecycle. Its declaration is not game qualification.
        gsc = b'// SYNTHETIC TEST SOURCE; NEVER COMPILED OR RUN\ninit(){ precachemodel("original/pilot"); level endon("game_ended"); wait 1; model=spawn("script_model",(0,0,0)); model setmodel("original/pilot"); }\n'
        self.gsc_name = 'sdk_model_fixture.gsc'
        (self.project/self.gsc_name).write_bytes(gsc)
        mapping = {'scriptfile:custom_scripts/cp/sdk_beacon.gsc':'scriptfile:custom_scripts/cp/'+self.gsc_name,
                   'xmodel:paris_model_probe':'xmodel:original/pilot',
                   'xsurface:paris_model_probe_lod0':'xsurface:mesh/unrelated', 'rawfile:sdk_beacon':'rawfile:paris_model_probe'}
        self.manifest['namespace'] = 'sdk_model_fixture'
        self.manifest['lifecycle']['entrypoints'][0]['path'] = 'custom_scripts/cp/'+self.gsc_name
        package = self.manifest['package']; package['id'] = 'sdk_model_fixture'
        for node in package['closure']['nodes']:
            node['id'] = mapping.get(node['id'],node['id'])
            node['requires'] = [mapping.get(n,n) for n in node['requires']]
        package['closure']['roots'] = [mapping.get(n,n) for n in package['closure']['roots']]
        for entry in package['files']:
            entry['closure_roots'] = [mapping.get(n,n) for n in entry['closure_roots']]
            if entry['role']=='client': entry['destination']='mods/sdk_model_fixture/mod.ff'
            else: entry.update(source=self.gsc_name,destination='iw7-mod/custom_scripts/cp/'+self.gsc_name)
        self.descriptor = {'schema':'iw7.creator-model-composition/1','assets':{
            'source_root':str(self.source),'source_plan_sha256':sha((self.source/'model-ff-plan.json').read_bytes()),
            'derived_receipt_sha256':sha((self.source/'derived-export.json').read_bytes()),
            'build_receipt_sha256':sha((self.build/'state.local.json').read_bytes()),
            'roundtrip_sha256':sha(encode(self.proof)),'ff_bytes':len((self.build/'mod.ff').read_bytes()),
            'ff_sha256':sha((self.build/'mod.ff').read_bytes())},'script':{
            'path':self.gsc_name,'bytes':len(gsc),'sha256':sha(gsc),
            'review_reference':'SYNTHETIC declaration only; not a source or runtime acceptance',
            'closure_sha256':sha(encode(package['closure']))}}
        self.save()
        self.assertLess(sum(p.stat().st_size for p in self.root.rglob('*') if p.is_file()), PREPARATION_LIMIT)

    def tearDown(self):
        measured = sum(p.stat().st_size for p in self.root.rglob('*') if p.is_file())
        type(self).peak_preparation_bytes = max(type(self).peak_preparation_bytes, measured)
        self.assertLess(measured, PREPARATION_LIMIT)

    def save(self):
        (self.project/'manifest.json').write_bytes(encode(self.manifest))
        (self.project/'composition.json').write_bytes(encode(self.descriptor))

    def repin_state(self):
        raw = encode(self.state); (self.build/'state.local.json').write_bytes(raw)
        self.descriptor['assets']['build_receipt_sha256'] = sha(raw); self.save()

    def invoke(self):
        return m.materialize(self.project,self.build,self.output,ROOT,manifest=self.manifest,client_source=PIN,server_source=PIN)

    def refused(self, pattern=None):
        with self.assertRaisesRegex((ValueError, OSError, KeyError), pattern or '.'):
            self.invoke()
        self.assertFalse(self.output.exists())

    def test_real_verifier_materializes_five_slots_with_false_acceptance(self):
        original = {p:sha(p.read_bytes()) for p in self.root.rglob('*') if p.is_file()}
        result = self.invoke()
        self.assertTrue(result['materialized']); self.assertTrue(result['creator_output_verified'])
        for field in ('closure_complete','package_ready','runtime_ready','owner_accepted'):
            self.assertFalse(result[field])
        self.assertEqual(set(p.name for p in self.output.iterdir()),
                         {'mod.ff',self.gsc_name,'manifest.json','finalization.json','validation-plan.json','validation-package.json'})
        evidence = json.loads((self.output/'finalization.json').read_bytes())
        self.assertEqual(evidence['surface_records'],self.plan['surface_records'])
        self.assertEqual(evidence['material_references'],[rigid.MATERIAL]*5)
        self.assertIn('placeholder',evidence['material_policy'])
        self.assertEqual(evidence['model_name'],'original/pilot'); self.assertEqual(evidence['mesh_name'],'mesh/unrelated')
        self.assertFalse(evidence['native_provenance_verified']); self.assertFalse(evidence['gsc_imports_verified'])
        for p,h in original.items(): self.assertEqual(sha(p.read_bytes()),h)
        manifest = json.loads((self.output/'manifest.json').read_bytes())
        self.assertTrue(all(e['status']=='pending' for e in manifest['package']['evidence']))
        report = json.loads((self.output/'validation-package.json').read_bytes())
        self.assertFalse(report['ready']); self.assertEqual(report['errors'],['package: Dependency closure incomplete'])

    def test_missing_or_unreviewed_gsc_never_writes_candidate(self):
        for key in ('review_reference','closure_sha256','sha256'):
            before=copy.deepcopy(self.descriptor)
            self.descriptor['script'][key]=''; self.save(); self.refused()
            self.descriptor=before
        self.save(); (self.project/self.gsc_name).unlink(); self.refused()

    def test_changed_script_and_reviewed_closure_refused(self):
        (self.project/self.gsc_name).write_bytes(b'changed reviewed script')
        self.refused('Pinned input')

    def test_changed_closure_cannot_reuse_script_review(self):
        self.manifest['package']['closure']['nodes'][0]['requires']=[]
        self.save(); self.refused('closure declaration differs')

    def test_stale_source_build_roundtrip_pins_refused(self):
        for field in ('source_plan_sha256','derived_receipt_sha256','build_receipt_sha256','roundtrip_sha256','ff_sha256'):
            before=copy.deepcopy(self.descriptor)
            self.descriptor['assets'][field]='0'*64; self.save(); self.refused('Pinned input differs')
            self.descriptor=before

    def test_explicit_file_and_aggregate_bounds_precede_writes(self):
        self.descriptor['assets']['ff_bytes']=32*1024*1024+1; self.save()
        self.refused('32 MiB')
        self.descriptor['assets']['ff_bytes']=self.proof['ff']['bytes']; self.save()
        with patch.object(m,'INPUT_LIMIT',32): self.refused('input budget')
        with patch.object(m,'OUTPUT_LIMIT',32): self.refused('output budget')

    def test_shape_extra_fields_promoted_evidence_and_wrong_real_names_refused(self):
        original=copy.deepcopy(self.descriptor)
        self.descriptor['script']['run']='command'; self.save(); self.refused('fields required')
        self.descriptor=original
        self.manifest['package']['evidence'][2].update(status='pass',reference='invented',maps=['cp_zmb'])
        self.save(); self.refused('pending qualification')
        self.manifest['package']['evidence'][2].update(status='pending',reference=None,maps=[])
        self.manifest['package']['closure']['nodes'][1]['requires'] = []
        self.descriptor['script']['closure_sha256']=sha(encode(self.manifest['package']['closure']))
        self.save(); self.refused('real ModelLab names')

    def test_failed_or_unrestored_states_refused_even_when_repinned(self):
        for field,value in (('Restored',False),('StockPreserved',False),('RetainedLeaseToken','held'),
                            ('CleanupError','open'),('Status','Failed'),('Ready',True),('InventoryVerified',False)):
            original=copy.deepcopy(self.state); self.state[field]=value; self.repin_state(); self.refused('Restored successful')
            self.state=original

    def test_phase_failure_and_boolean_exit_refused(self):
        for value in (1,False):
            self.state['Build']['ExitCode']=value; self.repin_state(); self.refused('exit 0')

    def test_ordered_surface_and_ff_proof_cannot_be_forged_by_repin(self):
        self.proof['surface_records'][0]['vertices']+=1
        raw=encode(self.proof); (self.build/'geometry-roundtrip.json').write_bytes(raw)
        (self.build/'reader.stdout.json').write_bytes(raw)
        self.descriptor['assets']['roundtrip_sha256']=sha(raw)
        self.state['GeometryEvidenceSHA256']=sha(raw); self.repin_state()
        self.refused('independent resident revalidation')

    def test_changed_dump_rejected_by_existing_geometry_reader(self):
        path=self.build/'roundtrip/xsurface/mesh/unrelated.xsb'
        raw=bytearray(path.read_bytes()); raw[-1]^=1; path.write_bytes(raw)
        self.refused()

    def test_extra_inventory_and_foreign_phase_path_refused(self):
        self.state['Offline']['Stdout']=str(self.project/'manifest.json'); self.repin_state()
        self.refused('directly under BuildRoot')

    def test_inventory_reference_is_not_a_material_payload(self):
        path=self.build/'assets.csv'; path.write_text(path.read_text().replace('material,,','material,'))
        self.refused('inventory differs')

    def test_v1_and_stale_368_claims_refused(self):
        for field,value in (('schema','iw7.model-ff-plan/1'),('geometry_work_bytes_upper_bound',self.plan['geometry_work_bytes_upper_bound']-80)):
            plan=copy.deepcopy(self.plan); plan[field]=value
            raw=rigid.json_bytes(plan); (self.source/'model-ff-plan.json').write_bytes(raw)
            self.descriptor['assets']['source_plan_sha256']=sha(raw); self.state['SourcePlan']=plan
            self.state['SourcePlanSHA256']=sha(raw); self.repin_state(); self.refused()

    def test_fresh_separate_output_and_redirects_required(self):
        self.output.mkdir(); sentinel=self.output/'preserve.txt'; sentinel.write_text('preserve')
        with self.assertRaisesRegex(ValueError,'Fresh'): self.invoke()
        self.assertEqual(sentinel.read_text(),'preserve')
        self.output=self.source/'nested'; self.refused('overlaps')

    def test_input_changed_during_reader_and_output_tamper_refused(self):
        original_load=m.module
        def altered(path,name):
            mod=original_load(path,name)
            if name=='creator_resident_verifier':
                original=mod.verify_dump
                def verify(*args):
                    result=original(*args)
                    (self.project/self.gsc_name).write_bytes(b'changed after reviewed snapshot')
                    return result
                mod.verify_dump=verify
            return mod
        with patch.object(m,'module',altered): self.refused('Input changed')

    def test_created_payload_is_rechecked_before_success(self):
        original_load=m.module
        def altered(path,name):
            mod=original_load(path,name)
            if name=='model_shared_checks':
                original=mod.sdk.validate
                def validate(*args,**kwargs):
                    result=original(*args,**kwargs)
                    if kwargs.get('stage')=='package':
                        path=self.output/'mod.ff'; raw=bytearray(path.read_bytes()); raw[0]^=1; path.write_bytes(raw)
                    return result
                mod.sdk.validate=validate
            return mod
        with patch.object(m,'module',altered), self.assertRaisesRegex(ValueError,'output changed'):
            self.invoke()
        self.assertTrue(self.output.exists(),'Rejected candidate retained for diagnosis')

    @unittest.skipUnless(shutil.which('pwsh'),'PowerShell required')
    def test_creator_dispatch_and_invalid_modes_do_not_run_builder_or_package(self):
        base=[shutil.which('pwsh'),'-NoProfile','-File',str(SDK/'Creator.ps1'),'-Adapter','ModelLabV2',
              '-Project',str(self.project),'-BuildRoot',str(self.build),'-FinalizeRoot',str(self.output),
              '-ToolsRoot',str(ROOT),'-ClientSource',PIN,'-ServerSource',PIN,'-Protocol','2','-Json']
        for action in ('Plan','Build','Package'):
            run=subprocess.run(base+['-Action',action],capture_output=True,text=True,timeout=20)
            self.assertEqual(run.returncode,1,run.stderr)
            result=json.loads(run.stdout); self.assertIn('only Materialize',' '.join(result['errors']))
            self.assertFalse(self.output.exists()); self.assertFalse(result['build_executed']); self.assertFalse(result['packaged'])
        run=subprocess.run(base+['-Action','Materialize'],capture_output=True,text=True,timeout=20)
        self.assertEqual(run.returncode,0,run.stdout+run.stderr)
        result=json.loads(run.stdout)
        self.assertTrue(result['materialized']); self.assertTrue(result['build_verified'])
        for field in ('build_executed','packaged','runtime_ready','owner_accepted'): self.assertFalse(result[field])
        self.assertTrue(result['pending'])

    @unittest.skipUnless(shutil.which('pwsh'),'PowerShell required')
    def test_creator_refuses_active_collision_and_unrelated_adapter_arguments(self):
        base=[shutil.which('pwsh'),'-NoProfile','-File',str(SDK/'Creator.ps1'),'-Adapter','ModelLabV2',
              '-Action','Materialize','-Project',str(self.project),'-BuildRoot',str(self.build),
              '-FinalizeRoot',str(self.output),'-ToolsRoot',str(ROOT),'-ClientSource',PIN,'-ServerSource',PIN,'-Protocol','2','-Json']
        for extra,reason in [(['-ActiveProject',str(self.project)],'Namespace collision'),
                             (['-RecipientProof','missing.json'],'composition.json'),
                             (['-Output',str(self.root/'not-created.zip')],'does not accept'),
                             (['-BuildParameters','missing.json'],'does not accept')]:
            run=subprocess.run(base+extra,capture_output=True,text=True,timeout=20)
            self.assertEqual(run.returncode,1,run.stdout+run.stderr)
            result=json.loads(run.stdout); self.assertIn(reason,' '.join(result['errors']))
            self.assertFalse(result['materialized']); self.assertFalse(result['build_executed']); self.assertFalse(self.output.exists())


if __name__=='__main__':
    unittest.main()
