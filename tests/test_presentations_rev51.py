"""Boundary and shared AI gate tests. Framework imports are isolated here;
PostgreSQL SQL/runtime behavior and real provider calls require staging.
"""
import ast
from contextlib import contextmanager
from copy import deepcopy
import json
from pathlib import Path
import sys
import types
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from modules.presentation_ai import PresentationAIError
from modules import presentation_ai_jobs as jobs


class HTTPException(Exception):
    def __init__(self, status_code, detail, headers=None):
        self.status_code, self.detail, self.headers = status_code, detail, headers
        super().__init__(detail)


def service_module():
    source = ROOT / 'modules/presentations.py'
    tree = ast.parse(source.read_text())
    tree.body = [node for node in tree.body if not (isinstance(node, ast.ImportFrom)
        and node.module in ('fastapi', 'fastapi.responses', 'starlette.concurrency'))]
    mod = types.ModuleType('modules.presentations')
    mod.__dict__.update(__package__='modules', HTTPException=HTTPException, Header=lambda x:x,
                        Query=lambda *a,**k:None, Request=object, Response=object)
    exec(compile(tree, str(source), 'exec'), mod.__dict__)
    return mod


S = service_module()


def document():
    return {'schema':2,'title':'Kvadrat tenglamalar','subject':'Matematika','lesson_type':'lecture',
            'design':{'template':'glass','transition':'fade','background':'paper','color':'#ffffff',
                      'image':None,'overlay':0,'panel':'solid','accent':'blue','text':'dark','font':'sans',
                      'size':'normal','radius':'round'},
            'slides':[{'id':'s1','title':'Tenglama','section':'Kirish','body':'Asosiy tushuncha',
                       'formula':'','example':'','image':None,'layout':'text','design':None}]}


class Boundaries(unittest.TestCase):
    def test_legacy_and_canvas_roundtrip(self):
        old = document(); old['schema']=1
        normalized = S.validate_document(old)
        self.assertEqual(normalized['audience'],'')
        self.assertEqual(normalized['slides'][0]['elements'], [])
        normalized['audience']='8-sinf'
        normalized['slides'][0]['placements']={'title':{'x':100,'y':120,'w':900,'h':100}}
        normalized['slides'][0]['elements']=[{'id':'e1','kind':'text','x':120,'y':450,'w':500,'h':70,'text':'Izoh','fontSize':28,'color':'#17394b'}]
        for family in ['glass','ribbon','split','gallery','steps','pencil','arc','spiral','bands']:
            normalized['design']['template']=family
            self.assertEqual(S.validate_document(normalized),normalized)

    def test_api_rejects_bad_geometry_audience_and_unknown_fields(self):
        for mutate in [lambda d:d.update(audience='a'*121), lambda d:d.update(role='admin'),
                       lambda d:d['slides'][0].update(placements={'body':{'x':1200,'y':0,'w':200,'h':100}}),
                       lambda d:d['slides'][0].update(elements=[{'id':'e','kind':'script','x':0,'y':0,'w':10,'h':10}])]:
            d=document();mutate(d)
            with self.assertRaises(HTTPException):S.validate_document(d)

    def test_cache_media_does_not_leak_and_layout_change_invalidates(self):
        d=S.validate_document(document()); brief={'audience':'8-sinf','instructions':''}
        first=jobs.cache_key(d,brief,['s1'],'model')
        d['slides'][0]['placements']={'body':{'x':0,'y':0,'w':100,'h':100}}
        self.assertNotEqual(first,jobs.cache_key(d,brief,['s1'],'model'))
        result={'document':d,'warnings':[]};d['slides'][0]['image']='SECRET-IMAGE'
        cached=jobs.text_result(result,['s1'])
        self.assertNotIn('SECRET-IMAGE',json.dumps(cached))
        cached['slides'][0]['body']='Yangi tushuntirish'
        restored=jobs.restore_result(d,cached)
        self.assertEqual(restored['document']['slides'][0]['image'],'SECRET-IMAGE')
        self.assertEqual(restored['document']['slides'][0]['placements'],d['slides'][0]['placements'])
        self.assertEqual(d['slides'][0]['body'],'Asosiy tushuncha')


class FakeCursor:
    def __init__(self, responses):self.responses=list(responses);self.calls=[]
    def execute(self, sql, args=()):self.calls.append((' '.join(sql.split()),args))
    def fetchone(self):return self.responses.pop(0)


class SharedGate(unittest.TestCase):
    def setup_gate(self,responses):
        cur=FakeCursor(responses);self.events=[]
        @contextmanager
        def db():
            self.events.append('open')
            try:yield cur
            finally:self.events.append('close')
        def require(cur,uid):self.events.append(('require',uid))
        self.cur=cur
        return jobs.PresentationAIJobs(db,require)

    def test_cache_read_is_owner_scoped_and_rechecks_eligibility(self):
        gate=self.setup_gate([{'result':{'slides':[],'warnings':[]}}])
        job,cached=gate._reserve(71,'a'*64)
        self.assertIsNone(job)
        self.assertIn(('require',71),self.events)
        self.assertTrue(any('WHERE owner_id=%s AND request_hash=%s' in q and args==(71,'a'*64) for q,args in self.cur.calls))

    def test_running_user_global_daily_and_minute_limits(self):
        attempts=[
            [None,{'total':1,'own':1}],
            [None,{'total':2,'own':0}],
            [None,{'total':0,'own':0},{'total':5,'own':5}],
            [None,{'total':0,'own':0},{'total':20,'own':0}],
            [None,{'total':0,'own':0},{'total':0,'own':0},{'total':2}],
        ]
        with patch.dict('os.environ',{'PRESENTATION_AI_USER_DAILY':'5','PRESENTATION_AI_GLOBAL_DAILY':'20'}):
            for responses in attempts:
                gate=self.setup_gate(responses)
                with self.assertRaises(PresentationAIError):gate._reserve(7,'k'*64)
                self.assertFalse(any(q.startswith('INSERT') for q,args in self.cur.calls))

    def test_unconfigured_service_consumes_no_quota(self):
        gate=self.setup_gate([])
        with patch.object(jobs,'get_ai_capabilities',return_value={'enabled':True,'available':False,'reason':'Kalit kerak'}):
            with self.assertRaises(PresentationAIError):gate.generate(7,document(),{},['s1'])
        self.assertEqual(self.events,[])

    def test_provider_runs_outside_db_and_failure_releases_lease(self):
        gate=self.setup_gate([None,{'total':0,'own':0},{'total':0,'own':0},{'total':0}])
        def fail_provider(*args):
            self.assertEqual(self.events[-1],'close')
            raise PresentationAIError('Xizmat band',429)
        caps={'enabled':True,'available':True,'model':'model'}
        with patch.object(jobs,'get_ai_capabilities',return_value=caps), patch.object(jobs,'generate_content',side_effect=fail_provider):
            with self.assertRaises(PresentationAIError):gate.generate(7,document(),{},['s1'])
        self.assertTrue(any("SET status='failed'" in q for q,args in self.cur.calls))


if __name__=='__main__':unittest.main()
