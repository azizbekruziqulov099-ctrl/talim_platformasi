"""Run real auth handlers with the existing transactional database fixture.

These cover account identity and one-use behavior, not live Telegram/PostgreSQL.
"""
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace as NS
from unittest import TestCase, main
from unittest.mock import patch
from tests import test_kabutar_auth_rev31 as base
from tests import test_telegram_code_rev53 as code_fixture

A = base.A
PHONE = '+998901234567'

def execute(cur, sql, args=()):
    q = ' '.join(sql.lower().split()); cur.rows = []
    rows = cur.db.state.setdefault('portable_codes', {})
    now = datetime.now(timezone.utc)
    if q.startswith('select *, expires_at>now() as live from kabutar_telegram_codes'):
        row = rows.get(args[0])
        cur.rows = [dict(row,live=row['expires_at']>now)] if row else []
        return
    if q.startswith('insert into kabutar_telegram_codes'):
        phone,tg,request_hash,code_hash,name,role,purpose = args
        rows[phone] = dict(phone=phone,telegram_id=tg,request_hash=request_hash,code_hash=code_hash,
            full_name=name,role=role,purpose=purpose,expires_at=now+timedelta(minutes=5),attempts=0,
            consumed_at=None,redeemer_hash=None,user_id=None)
        return
    if q.startswith('update kabutar_telegram_codes set attempts='):
        rows[args[0]]['attempts'] += 1; return
    if q.startswith('update kabutar_telegram_codes set consumed_at='):
        created,redeemer,uid,phone = args
        rows[phone].update(consumed_at=created,redeemer_hash=redeemer,user_id=uid); return
    return code_fixture.execute(cur,sql,args)

class PortableCodeTests(TestCase):
    def assert_http(self,status,fn,*args,**kwargs):
        with self.assertRaises(base.HTTPException) as caught:
            fn(*args,**kwargs)
        self.assertEqual(caught.exception.status_code,status)
    def setUp(self):
        base.AuthTests.setUp(self)
        self.patch = patch.object(base.Cursor,'execute',execute)
        self.patch.start(); self.addCleanup(self.patch.stop)
        self.issue_handler = self.app.routes['/auth/telegram/code/issue']
        self.redeem_handler = self.app.routes['/auth/telegram/code/redeem']

    def issue(self, **changes):
        fields = dict(challenge='p'*32,telegram_user_id=333,contact_user_id=333,
            phone=PHONE,full_name='Yangi foydalanuvchi',role='talaba')
        fields.update(changes)
        return self.issue_handler(NS(**fields),'s'*32)

    def redeem(self, code, **changes):
        fields = dict(phone=PHONE,code=code,browser_secret='q'*64,mode='login',token=None)
        fields.update(changes)
        return self.redeem_handler(NS(**fields),self.request)

    def test_bot_can_issue_without_any_site_challenge_and_creates_no_account_yet(self):
        result = self.issue()
        self.assertRegex(result['code'],r'^\d{6}$')
        self.assertNotIn(333,self.db.state['users'])
        self.assertFalse(self.db.state['sessions'])
        self.assertNotEqual(self.db.state['portable_codes'][PHONE]['code_hash'],A.digest(result['code']))

    def test_gmail_choice_never_creates_duplicate_even_without_phone_collision(self):
        code = self.issue(purpose='link')['code']
        self.assertEqual(self.redeem(code)['status'], 'link_required')
        self.assertNotIn(333, self.db.state['users'])
        self.assertFalse(self.db.state['portable_codes'][PHONE]['consumed_at'])
        token = self.service.issue_session(222, 'google')
        result = self.redeem(code, mode='link', token=token)
        self.assertEqual(result['user_id'], 222)
        self.assertNotIn(333, self.db.state['users'])

    def test_gmail_choice_cannot_be_reissued_as_new_profile_for_same_request(self):
        self.issue(purpose='link')
        self.assert_http(409, self.issue, purpose='login')
        self.assert_http(422, self.issue, purpose='admin')

    def test_same_challenge_cannot_silently_use_a_previous_role(self):
        code = self.issue(role='talaba')['code']
        self.assert_http(409, self.issue, role='oqituvchi')
        new = self.issue(challenge='r'*32, role='oqituvchi')['code']
        self.assertEqual(self.redeem(new)['user_id'], 333)
        self.assertEqual(self.db.state['users'][333]['role'], 'oqituvchi')

    def test_gmail_choice_still_validates_code_before_telling_browser_to_link(self):
        code = self.issue(purpose='link')['code']
        wrong = '000000' if code != '000000' else '111111'
        self.assertEqual(self.redeem(wrong)['status'], 'invalid_code')
        self.assertFalse(self.db.state['identities'])

    def test_new_user_created_only_on_correct_code_with_selected_role(self):
        result = self.redeem(self.issue()['code'])
        self.assertEqual(self.p._jwt_tekshir(result['token']),333)
        self.assertEqual(self.db.state['users'][333]['kabutar_learning_profile']['role'],'talaba')
        self.assertEqual(self.db.state['identities'][333]['user_id'],333)

    def test_all_new_roles_and_admin_cannot_be_self_selected(self):
        for i,role in enumerate(('oquvchi','talaba','oqituvchi','ota-ona')):
            phone = f'+99890123000{i}'; tg = 800+i
            code = self.issue(telegram_user_id=tg,contact_user_id=tg,phone=phone,role=role)['code']
            result = self.redeem(code,phone=phone)
            self.assertEqual(result['user_id'],tg)
            self.assertEqual(self.db.state['users'][tg]['role'],'oquvchi' if role=='talaba' else role)
        self.assert_http(422,self.issue,role='admin')

    def test_contact_and_bot_secret_are_required(self):
        self.assert_http(403,self.issue,contact_user_id=999)
        self.assert_http(401,self.issue_handler,NS(),'incorrect')
        self.assertFalse(self.db.state.get('portable_codes'))

    def test_leading_zero_code_supported(self):
        with patch.object(self.service,'login_code',return_value='000019'):
            self.assertEqual(self.redeem(self.issue()['code'])['status'],'complete')

    def test_network_retry_same_browser_returns_same_session(self):
        code = self.issue()['code']
        first = self.redeem(code)
        self.assertEqual(self.redeem(code),first)
        self.assertEqual(len(self.db.state['sessions']),1)
        self.assertEqual(self.redeem(code,browser_secret='z'*64)['status'],'used')

    def test_replay_cannot_switch_into_link_mode_or_another_google_account(self):
        code = self.issue()['code']; self.redeem(code)
        token = self.service.issue_session(222,'google')
        self.assertEqual(self.redeem(code,mode='link',token=token)['status'],'used')
        self.assertEqual(self.db.state['identities'][333]['user_id'],333)

    def test_five_wrong_codes_lock_valid_code_and_do_not_create_user(self):
        code = self.issue()['code']; wrong = '000000' if code!='000000' else '111111'
        for _ in range(5): self.assertEqual(self.redeem(wrong)['status'],'invalid_code')
        self.assertEqual(self.redeem(code)['status'],'invalid_code')
        self.assertEqual(self.db.state['portable_codes'][PHONE]['attempts'],5)
        self.assertNotIn(333,self.db.state['users'])

    def test_wrong_phone_cannot_claim_code(self):
        result = self.redeem(self.issue()['code'],phone='+998991234567')
        self.assertEqual(result['status'],'invalid_code')
        self.assertFalse(self.db.state['identities'])

    def test_expired_and_revoked_codes_fail(self):
        code = self.issue()['code']
        self.db.state['portable_codes'][PHONE]['expires_at']=datetime.now(timezone.utc)-timedelta(seconds=1)
        self.assertEqual(self.redeem(code)['status'],'expired')
        self.assert_http(410,self.issue)
        code = self.issue(challenge='n'*32)['code']; self.redeem(code)
        for row in self.db.state['sessions'].values(): row['revoked_at']=datetime.now(timezone.utc)
        self.assertEqual(self.redeem(code)['status'],'expired')

    def test_issue_retry_keeps_code_expiry_and_failed_attempts(self):
        first = self.issue(); row = self.db.state['portable_codes'][PHONE]
        row['attempts']=3; expiry=row['expires_at']
        self.assertEqual(self.issue()['code'],first['code'])
        self.assertEqual(row['attempts'],3); self.assertEqual(row['expires_at'],expiry)

    def test_new_request_invalidates_previous_code(self):
        with patch.object(self.service,'login_code',side_effect=['123450','543210']):
            old = self.issue()['code']; new = self.issue(challenge='n'*32)['code']
        self.assertEqual(self.redeem(old)['status'],'invalid_code')
        self.assertEqual(self.redeem(new)['status'],'complete')

    def test_existing_linked_gmail_user_keeps_original_id_role_and_data(self):
        self.db.state['users'][222].update(role='oqituvchi',class_='11',saved_lessons=['lesson'])
        self.db.state['identities'][333]=dict(telegram_id=333,user_id=222,phone=PHONE)
        self.db.state['phones'][PHONE]=222
        result = self.redeem(self.issue(role='oquvchi')['code'])
        self.assertEqual(result['user_id'],222)
        self.assertEqual(self.db.state['users'][222]['role'],'oqituvchi')
        self.assertEqual(self.db.state['users'][222]['saved_lessons'],['lesson'])
        self.assertNotIn(333,self.db.state['users'])

    def test_google_phone_collision_recovers_by_authenticated_link_same_code(self):
        self.db.state['phones'][PHONE]=222
        self.db.state['users'][222]['role']='oqituvchi'
        code = self.issue()['code']
        self.assert_http(409,self.redeem,code)
        self.assertIsNone(self.db.state['portable_codes'][PHONE]['consumed_at'])
        self.assertNotIn(333,self.db.state['users'])
        token = self.service.issue_session(222,'google')
        result = self.redeem(code,mode='link',token=token)
        self.assertEqual(result['user_id'],222)
        self.assertEqual(self.db.state['users'][222]['role'],'oqituvchi')
        self.assertEqual(self.db.state['identities'][333]['user_id'],222)

    def test_legacy_bot_profile_does_not_block_link_to_authenticated_gmail(self):
        self.db.state['users'][333]=dict(user_id=333,role='oquvchi',results=['keep'])
        self.db.state['users'][222]['role']='oqituvchi'
        self.db.state['phones'][PHONE]=333
        self.db.state['accounts']=[dict(telegram_id=333,uid=333,account_index=0)]
        token = self.service.issue_session(222,'google')
        result = self.redeem(self.issue()['code'],mode='link',token=token)
        self.assertEqual(result['user_id'],222)
        self.assertEqual(self.db.state['phones'][PHONE],222)
        self.assertEqual(self.db.state['users'][333]['results'],['keep'])
        self.assertEqual(self.db.state['users'][222]['role'],'oqituvchi')

    def test_verified_identity_of_another_account_is_not_reassigned(self):
        self.db.state['identities'][333]=dict(telegram_id=333,user_id=111,phone=PHONE)
        token = self.service.issue_session(222,'google')
        self.assert_http(409,self.redeem,self.issue()['code'],mode='link',token=token)
        self.assertEqual(self.db.state['identities'][333]['user_id'],111)

    def test_linking_unconfigured_google_profile_does_not_force_a_student_role(self):
        self.db.state['users'][222]['role']='kabutar'
        token=self.service.issue_session(222,'google')
        result=self.redeem(self.issue(role='oquvchi')['code'],mode='link',token=token)
        self.assertEqual(result['user_id'],222)
        self.assertEqual(self.db.state['users'][222]['role'],'kabutar')

    def test_link_requires_active_authenticated_session_and_allowed_origin(self):
        code = self.issue()['code']
        self.assert_http(401,self.redeem,code,mode='link',token='invalid')
        self.request.headers['origin']='https://attacker.invalid'
        self.assert_http(403,self.redeem,code)
        self.assertFalse(self.db.state['identities'])

    def test_existing_admin_and_student_course_roles_are_preserved(self):
        self.db.state['admins']={111}
        code = self.issue(telegram_user_id=111,contact_user_id=111)['code']
        self.assertEqual(self.redeem(code)['user_id'],111)
        self.assertNotIn('role',self.db.state['users'][111])

class GoogleContinuationTests(TestCase):
    """Execute the real OAuth routes; mock Google HTTP and token transport only."""
    def setUp(self):
        import ast,asyncio,base64,hashlib,secrets
        from pathlib import Path
        from typing import Optional
        from urllib.parse import urlencode
        self.asyncio=asyncio;self.user_id=222;self.google_calls=0
        owner=self
        class Response:
            def __init__(self,content=None,status_code=200):
                self.content=content;self.status_code=status_code;self.headers={}
        class Cursor:
            def execute(self,*args):pass
            def fetchone(self):return {'user_id':owner.user_id} if owner.user_id else None
            def close(self):pass
        class Google:
            def __init__(self,*args,**kwargs):pass
            async def __aenter__(self):return self
            async def __aexit__(self,*args):pass
            async def post(self,*args,**kwargs):
                owner.google_calls+=1
                return NS(raise_for_status=lambda:None,json=lambda:{'access_token':'fixture-google'})
            async def get(self,*args,**kwargs):
                return NS(raise_for_status=lambda:None,json=lambda:{'email':'teacher@example.test','email_verified':True,'name':'Teacher'})
        def cookie(response,name,value,*args):self.cookie=value
        self.ns=dict(Optional=Optional,Request=object,GoogleTicketExchange=object,HTTPException=base.HTTPException,
            base64=base64,hashlib=hashlib,secrets=secrets,urlencode=urlencode,
            GOOGLE_CLIENT_ID='fixture',GOOGLE_CLIENT_SECRET='fixture',REDIRECT_URI='https://api.test/callback',
            OAUTH_STATE_SECONDS=600,OAUTH_STATE_COOKIE='state',OAUTH_TICKET_SECONDS=60,OAUTH_REGISTRATION_GRANT_SECONDS=600,
            FRONTEND_ORIGINS=['https://talimkabutar.uz'],RedirectResponse=Response,JSONResponse=Response,
            httpx=NS(AsyncClient=Google,HTTPError=RuntimeError),
            _oauth_cookie_qoy=cookie,_oauth_frontend_redirect=lambda **values:values,
            _oauth_imzolangan_token=lambda purpose,seconds,**values:dict(purpose=purpose,**values),
            _oauth_token_och=lambda value,purpose:value if isinstance(value,dict) and value.get('purpose')==purpose else None,
            _auth_ticket_consume=lambda payload:None,_jwt_yarat=lambda uid:f'fixture-session-{uid}',
            _db=lambda:NS(cursor=lambda:Cursor(),close=lambda:None))
        tree=ast.parse((Path(__file__).resolve().parents[1]/'samtm_platform.py').read_text())
        names={'google_login','google_callback','google_ticket_exchange'}
        tree.body=[node for node in tree.body if isinstance(node,(ast.FunctionDef,ast.AsyncFunctionDef)) and node.name in names]
        for node in tree.body:node.decorator_list=[]
        exec(compile(tree,'oauth_routes','exec'),self.ns)

    def exchange(self,intent):
        self.ns['google_login'](intent)
        self.assertEqual(self.cookie['intent'],intent)
        callback=self.asyncio.run(self.ns['google_callback'](NS(cookies={'state':self.cookie}),code='code',state=self.cookie['state']))
        return self.ns['google_ticket_exchange'](NS(ticket=callback['ticket']),NS(headers={'origin':'https://talimkabutar.uz'})).content

    def test_existing_gmail_login_carries_telegram_intent_through_server(self):
        result=self.exchange('telegram')
        self.assertEqual(result,{'holat':'kirdi','token':'fixture-session-222','intent':'telegram'})

    def test_new_google_registration_also_preserves_telegram_continuation(self):
        self.user_id=None
        result=self.exchange('telegram')
        self.assertEqual(result['holat'],'ulash')
        self.assertEqual(result['intent'],'telegram')
        self.assertEqual(result['oauth_grant']['intent'],'telegram')

    def test_existing_google_identity_link_flow_remains_separate(self):
        result=self.exchange('link')
        self.assertEqual(result['holat'],'ulash')
        self.assertEqual(result['intent'],'link')

    def test_telegram_intent_still_requires_matching_oauth_state(self):
        self.ns['google_login']('telegram')
        result=self.asyncio.run(self.ns['google_callback'](NS(cookies={'state':self.cookie}),code='code',state='wrong'))
        self.assertEqual(result,{'xato':'state'})
        self.assertEqual(self.google_calls,0)

if __name__ == '__main__': main()
