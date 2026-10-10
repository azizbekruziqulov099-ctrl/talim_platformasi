"""Real auth handlers: code exchange, replay, browser binding and learner roles."""
import json
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace as NS
from unittest import TestCase, main
from unittest.mock import patch
from tests import test_kabutar_auth_rev31 as fixture

A = fixture.A
original_execute = fixture.Cursor.execute

def execute(cur, sql, args=()):
    q = ' '.join(sql.lower().split()); s = cur.db.state; cur.rows = []
    if q.startswith('select to_jsonb(u) as profile from users'):
        user = s['users'].get(args[0]); cur.rows = [{'profile':dict(user)}] if user else []; return
    if q.startswith('select 1 from admin_akkaunt'):
        cur.rows = [{'ok':1}] if args[0] in s.get('admins', set()) else []; return
    if q.startswith('select 1 from talaba_profillari'):
        cur.rows = [{'ok':1}] if args[0] in s.get('students', set()) else []; return
    if q.startswith('select 1 from foydalanuvchi_muassasalari'):
        cur.rows = [{'ok':1}] if args[0] in s.get('memberships', set()) else []; return
    if q.startswith('update users set role='):
        if 'class=%s' in q:
            role, grade, language, subject, learning, uid = args
            s['users'][uid].update(role=role, **{'class':grade}, asosiy_til=language,
                oqituvchi_fani=subject, kabutar_learning_profile=json.loads(learning), kabutar_education_ready=True)
        else:
            role, learning, ready, uid = args
            s['users'][uid].update(role=role, kabutar_learning_profile=json.loads(learning), kabutar_education_ready=ready)
        return
    if q.startswith("update kabutar_auth_challenges set delivery='code'"):
        s['challenges'][args[0]]['delivery']='code'; return
    if q.startswith('update kabutar_auth_challenges set code_hash='):
        code, role, key=args; s['challenges'][key].update(code_hash=code, selected_role=role); return
    if q.startswith('update kabutar_auth_challenges set code_attempts='):
        attempts, _, key = args; s['challenges'][key]['code_attempts']=attempts
        if attempts >= 5: s['challenges'][key]['cancelled_at']=datetime.now(timezone.utc)
        return
    return original_execute(cur, sql, args)

class CodeFlowTests(TestCase):
    assert_http = fixture.AuthTests.assert_http
    confirm_body = fixture.AuthTests.confirm_body
    def setUp(self):
        fixture.AuthTests.setUp(self)
        self.addCleanup(patch.stopall)
        patch.object(fixture.Cursor, 'execute', execute).start()
        self.p.joriy_foydalanuvchi = lambda token: dict(self.db.state['users'][self.p._jwt_tekshir(token)])
        self.start_code()
    def start_code(self):
        self.start = self.app.routes['/auth/telegram/start'](NS(mode='login', token=None, delivery='code'), self.request)
        self.challenge=self.start['challenge']
        self.body=NS(challenge=self.challenge,browser_secret=self.start['browser_secret'])
    def approve(self, role='talaba'):
        body=self.confirm_body(); body.role=role
        return self.app.routes['/auth/telegram/confirm'](body,'s'*32)
    def verify(self, code, **changes):
        return self.app.routes['/auth/telegram/verify'](NS(**{**vars(self.body),'code':code,**changes}),self.request)
    def test_code_is_bot_only_and_poll_never_issues_session(self):
        result=self.approve()
        self.assertNotIn('code',self.start)
        self.assertEqual(len(result['code']),6)
        self.assertEqual(self.app.routes['/auth/telegram/poll'](self.body,self.request),{'status':'code_required'})
        self.assertFalse(self.db.state['sessions'])
        inspected=self.app.routes['/auth/telegram/inspect'](NS(challenge=self.challenge),'s'*32)
        self.assertNotIn('code',inspected)
        self.assertNotIn('code_hash',inspected)
    def test_code_creates_one_session_and_network_retry_is_idempotent(self):
        code=self.approve()['code']; first=self.verify(code); second=self.verify(code)
        self.assertEqual(first,second)
        self.assertEqual(self.p._jwt_tekshir(first['token']),111)
        self.assertEqual(len(self.db.state['sessions']),1)
    def test_code_cannot_be_used_in_other_browser(self):
        code=self.approve()['code']
        self.assert_http(401,lambda: self.verify(code,browser_secret='x'*43))
        self.assertFalse(self.db.state['sessions'])
    def test_five_wrong_attempts_persist_and_lock_even_correct_code(self):
        code=self.approve()['code']; wrong='000000' if code!='000000' else '111111'
        for left in range(4,-1,-1):
            result=self.verify(wrong)
            self.assertEqual(result['attempts_left'],left)
        self.assertEqual(self.verify(code)['status'],'cancelled')
        self.assertFalse(self.db.state['sessions'])
    def test_expired_code_is_rejected(self):
        code=self.approve()['code']
        self.db.state['challenges'][A.digest(self.challenge)]['expires_at']=datetime.now(timezone.utc)-timedelta(seconds=1)
        self.assertEqual(self.verify(code)['status'],'expired')
    def test_cancelled_request_cannot_sign_in(self):
        code=self.approve()['code']
        self.app.routes['/auth/telegram/cancel'](self.body,self.request)
        self.assertEqual(self.verify(code)['status'],'cancelled')
    def test_repeated_bot_confirmation_recovers_same_code(self):
        self.assertEqual(self.approve(),self.approve())
    def test_all_four_roles_keep_correct_legacy_role_without_membership(self):
        for role in ('oquvchi','talaba','oqituvchi','ota-ona'):
            with self.subTest(role=role):
                self.db.state['users'][111]={'user_id':111,'role':'kabutar'}; self.start_code()
                self.assertEqual(self.approve(role)['role'],role)
                user=self.db.state['users'][111]
                self.assertEqual(user['role'],'oquvchi' if role=='talaba' else role)
                self.assertEqual(user['kabutar_learning_profile']['role'],role)
                self.assertNotIn('universitet_id',user)
    def test_existing_teacher_cannot_silently_become_student(self):
        self.db.state['users'][111].update(role='oqituvchi',universitet_id=17)
        self.assert_http(409,self.approve,'talaba')
        self.assertEqual(self.db.state['users'][111]['role'],'oqituvchi')
        self.assertFalse(self.db.state['identities'])
    def test_admin_role_is_not_self_selectable(self):
        self.assert_http(422,self.approve,'admin')
        self.assertFalse(self.db.state['identities'])
    def test_student_profile_needs_no_institution_password(self):
        token=self.verify(self.approve()['code'])['token']
        body=NS(token=token,role='talaba',class_=None,grade=None,language='ru',subject=None,
            course=2,degree='bakalavr',study_form='kechki')
        result=self.app.routes['/auth/profile/education'](body,self.request)
        profile=result['profile']
        self.assertEqual(profile['class'],'2 kurs')
        self.assertEqual(profile['kabutar_learning_profile']['talim_shakli'],'kechki')
        self.assertTrue(profile['kabutar_education_ready'])
        self.assertNotIn('universitet_id',profile)
    def test_enrolled_student_cannot_replace_authoritative_profile(self):
        token=self.verify(self.approve()['code'])['token']
        self.db.state['students']={111}
        body=NS(token=token,role='talaba',class_=None,grade=None,language='uz',subject=None,
            course=2,degree='bakalavr',study_form='kunduzgi')
        self.assert_http(409,self.app.routes['/auth/profile/education'],body,self.request)
    def test_invalid_course_is_rejected_before_write(self):
        token=self.verify(self.approve()['code'])['token']
        body=NS(token=token,role='talaba',class_=None,grade=None,language='uz',subject=None,
            course=4,degree='magistr',study_form='kunduzgi')
        self.assert_http(422,self.app.routes['/auth/profile/education'],body,self.request)

if __name__=='__main__': main()
