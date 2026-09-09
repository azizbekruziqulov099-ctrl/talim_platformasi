"""Isolated auth regression tests; real PostgreSQL/Telegram staging still required.

FastAPI declarations are stubbed where unavailable. The production service code
runs unchanged against a transactional in-memory cursor implementing its queries.
Cryptographic token encoding is isolated from identity/session authorization.
"""
import ast
import copy
import hashlib
import hmac
import json
import os
from pathlib import Path
import sys
import types
import unittest
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
class HTTPException(Exception):
    def __init__(self,status_code,detail,headers=None):
        self.status_code=status_code; self.detail=detail
class FakeJWT:
    @staticmethod
    def encode(claims,key,algorithm='HS256'):
        plain=json.dumps(claims,default=lambda x:x.timestamp(),sort_keys=True)
        return plain+'|'+hmac.new(key.encode(),plain.encode(),hashlib.sha256).hexdigest()
    @staticmethod
    def decode(token,key,**kwargs):
        plain,signature=token.rsplit('|',1)
        if not hmac.compare_digest(signature,hmac.new(key.encode(),plain.encode(),hashlib.sha256).hexdigest()):
            raise ValueError('signature')
        claims=json.loads(plain)
        if claims['exp']<datetime.now(timezone.utc).timestamp(): raise ValueError('expired')
        return claims
class FakeModel:
    pass
class FakeApp:
    def __init__(self):self.routes={}
    def get(self,path):return self.post(path)
    def post(self,path):
        def add(fn):self.routes[path]=fn;return fn
        return add
    def middleware(self,*args):return lambda fn:fn
    def add_event_handler(self,*args):pass

def load_auth():
    tree=ast.parse((ROOT/'kabutar_auth.py').read_text())
    tree.body=[n for n in tree.body if not isinstance(n,ast.ImportFrom) or n.module not in ('fastapi','fastapi.responses','jose','pydantic')]
    ns={'__name__':'auth_regression','HTTPException':HTTPException,'Request':object,'Header':lambda x:x,
        'JSONResponse':dict,'jwt':FakeJWT,'JWTError':ValueError,'BaseModel':FakeModel,'Field':lambda *a,**kw:None}
    exec(compile(tree,str(ROOT/'kabutar_auth.py'),'exec'),ns)
    return types.SimpleNamespace(**ns)
A=load_auth()

class MemoryDB:
    def __init__(self):
        self.state={'users':{111:{'user_id':111},222:{'user_id':222}},'identities':{},'phones':{},'sessions':{},'challenges':{},'consumed':{},'rates':{},'accounts':None,'security':{},'passwords':{},'google':{'person@example.com':111},'invites':{}}
    def connect(self):return Connection(self)
class Connection:
    def __init__(self,db):self.db=db;self.snapshot=copy.deepcopy(db.state)
    def cursor(self):return Cursor(self.db)
    def commit(self):self.snapshot=copy.deepcopy(self.db.state)
    def rollback(self):self.db.state=self.snapshot
    def close(self):pass
class Cursor:
    def __init__(self,db):self.db=db;self.rows=[]
    def close(self):pass
    def fetchone(self):return self.rows.pop(0) if self.rows else None
    def fetchall(self):rows=self.rows;self.rows=[];return rows
    def execute(self,sql,args=()):
        q=' '.join(sql.lower().split());s=self.db.state;self.rows=[];now=datetime.now(timezone.utc)
        if q.startswith('select pg_advisory'):return
        if q.startswith('select kod as stored_code,user_id,ishlatildi'):
            rows=[r.copy() for code,r in s['invites'].items() if code in args[:2]];self.rows=rows[:1];return
        if q.startswith('select 1 from google_hisob where user_id='):
            uid=args[0]
            claimed=uid in s['google'].values() or any(r['user_id']==uid for r in s['identities'].values()) or uid in s['passwords'] or any(r['user_id']==uid for r in s['sessions'].values()) or uid in s['phones'].values() or uid in s['security']
            self.rows=[{'exists':1}] if claimed else [];return
        if q.startswith('insert into google_hisob'):
            s['google'][args[0]]=args[1];return
        if q.startswith('update xodim_kod set ishlatildi='):
            s['invites'][args[0]]['ishlatildi']=True;return
        if q.startswith('update users set kabutar_education_ready='):
            s['users'][args[0]]['kabutar_education_ready']=True;return
        if q.startswith('update users set phone_discoverable=false'):
            s['users'][args[0]]['phone_discoverable']=False;return
        if q.startswith('select user_id from google_hisob'):
            uid=s['google'].get(args[0]);self.rows=[{'user_id':uid}] if uid is not None else [];return
        if q.startswith('select password_hash from kabutar_auth_password'):
            value=s['passwords'].get(args[0]);self.rows=[{'password_hash':value}] if value else [];return
        if q.startswith('insert into kabutar_auth_password'):
            s['passwords'][args[0]]=args[1];return
        if q.startswith('select disable_legacy from kabutar_auth_security'):
            self.rows=[{'disable_legacy':True}] if s['security'].get(args[0]) else [];return
        if q.startswith('insert into kabutar_auth_security'):
            if 'disable_legacy' in q:s['security'][args[0]]=True
            else:s['security'].setdefault(args[0],False)
            return
        if q.startswith('select target_user_id from kabutar_auth_challenges'):
            row=s['challenges'].get(args[0]);self.rows=[{'target_user_id':row.get('target_user_id')}] if row else [];return
        if q.startswith('insert into kabutar_auth_rate'):
            b=args[0];s['rates'][b]=s['rates'].get(b,0)+1;self.rows=[{'hits':s['rates'][b]}];return
        if q.startswith('insert into kabutar_auth_sessions'):
            if 'to_timestamp' in q:
                key,uid,exp=args;row={'user_id':uid,'expires_at':datetime.fromtimestamp(exp,timezone.utc),'created_at':now,'revoked_at':None,'method':'legacy'}
            else:
                key,uid,created,exp,method=args;row={'user_id':uid,'expires_at':exp,'created_at':created,'revoked_at':None,'method':method}
            s['sessions'].setdefault(key,row);return
        if 'from kabutar_auth_sessions where session_hash=' in q:
            row=s['sessions'].get(args[0])
            if row and not row['revoked_at'] and row['expires_at']>now:
                copied=row.copy()
                if 'as recent' in q:copied['recent']=row['created_at']>now-timedelta(minutes=10)
                if 'user_id=%s' not in q or row['user_id']==args[1]:self.rows=[copied]
            return
        if q.startswith('update kabutar_auth_sessions set revoked_at=now()'):
            for key,row in s['sessions'].items():
                matches=row['user_id']==args[0] if 'where user_id=' in q else key==args[0]
                if matches and 'session_hash<>%s' in q:matches=key!=args[1]
                if matches:row['revoked_at']=now
            return
        if q.startswith('insert into kabutar_auth_consumed'):
            key,exp=args
            if key not in s['consumed']:
                s['consumed'][key]=exp;self.rows=[{'token_hash':key}]
            return
        if q.startswith('select *, expires_at>now()'):
            row=s['challenges'].get(args[0])
            if row:self.rows=[dict(row,live=row['expires_at']>now)]
            return
        if q.startswith('update kabutar_auth_challenges set consumed_at='):
            s['challenges'][args[1]]['consumed_at']=args[0];return
        if q.startswith('update kabutar_auth_challenges set cancelled_at='):
            for key,row in s['challenges'].items():
                if 'where challenge_hash=' in q:matches=key==args[0]
                elif 'where target_user_id=' in q:matches=row['target_user_id']==args[0] and row['consumed_at'] is None
                else:matches=row.get('link_session_hash')==args[0] and row['consumed_at'] is None
                if matches:row['cancelled_at']=now
            return
        if q.startswith('update kabutar_auth_challenges set user_id='):
            uid,tg,phone,key=args;s['challenges'][key].update(user_id=uid,telegram_id=tg,phone=phone,confirmed_at=now);return
        if q.startswith('select user_id,phone from kabutar_telegram_identity'):
            row=s['identities'].get(args[0]);self.rows=[row.copy()] if row else [];return
        if q.startswith("select to_regclass('public.user_accounts')"):
            self.rows=[{'t':'user_accounts' if s['accounts'] is not None else None}];return
        if q.startswith('select uid from user_accounts'):
            rows=[r for r in s['accounts'] if r['telegram_id']==args[0] and r['account_index']==0];self.rows=rows;return
        if q.startswith('select 1 from user_accounts'):
            self.rows=[r for r in s['accounts'] if r['uid']==args[0] and r['telegram_id']!=args[1]];return
        if q.startswith('select user_id from users where user_id='):
            row=s['users'].get(args[0]);self.rows=[row.copy()] if row else [];return
        if q.startswith('select user_id from telefon_hisob'):
            uid=s['phones'].get(args[0]);self.rows=[{'user_id':uid}] if uid is not None else [];return
        if q.startswith('select telegram_id,user_id from kabutar_telegram_identity'):
            self.rows=[r.copy() for r in s['identities'].values() if r['phone']==args[0] or r['user_id']==args[1]];return
        if q.startswith('insert into users'):
            uid,name=args;s['users'].setdefault(uid,{'user_id':uid,'full_name':name,'role':'kabutar'});return
        if q.startswith('insert into kabutar_telegram_identity'):
            tg,uid,phone=args;s['identities'][tg]={'telegram_id':tg,'user_id':uid,'phone':phone};return
        if q.startswith('insert into telefon_hisob'):
            phone,uid=args;s['phones'].setdefault(phone,uid);return
        if q.startswith('delete from telefon_hisob'):
            phone,uid=args
            if s['phones'].get(phone)==uid:del s['phones'][phone]
            return
        raise AssertionError('Query fixture missing: '+q)

class AuthTests(unittest.TestCase):
    def setUp(self):
        self.db=MemoryDB();self.app=FakeApp()
        self.p=types.SimpleNamespace(_db=self.db.connect,JWT_MAXFIY_KALIT='test-key-'+'a'*32,FRONTEND_ORIGINS=['https://talimkabutar.uz'],FRONTEND_URL='https://talimkabutar.uz',GOOGLE_CLIENT_ID='test',GOOGLE_CLIENT_SECRET='test')
        self.p._jwt_header_yoki_query=lambda token,header:header.removeprefix('Bearer ') if header else token
        self.p._xodim_kod_variantlari=lambda code:(code,'sha256:'+A.digest(code))
        def check_grant(token,email):
            if token!='valid-grant':raise HTTPException(401,'invalid')
            return {'jti':'invite-grant','email':email,'exp':(datetime.now(timezone.utc)+timedelta(minutes=15)).timestamp()}
        self.p._google_registration_tekshir=check_grant
        with patch.dict(os.environ,{'KABUTAR_BOT_AUTH_SECRET':'s'*32,'KABUTAR_BOT_USERNAME':'kabutar_test_bot'}):
            self.service=A.register_auth(self.app,self.p)
        self.p._jwt_tekshir=lambda token:self.service.verify_session(token,self.service.claims(token))
        self.request=types.SimpleNamespace(headers={'origin':'https://talimkabutar.uz'},client=types.SimpleNamespace(host='127.0.0.1'))
        self.challenge='c'*32;self.secret='b'*43
        self.body=types.SimpleNamespace(challenge=self.challenge,browser_secret=self.secret)
        self.db.state['challenges'][A.digest(self.challenge)]={'browser_hash':A.digest(self.secret),'verification_code':'123456','mode':'login','target_user_id':None,'user_id':None,'telegram_id':None,'phone':None,'confirmed_at':None,'consumed_at':None,'cancelled_at':None,'expires_at':datetime.now(timezone.utc)+timedelta(minutes=5)}
    def confirm_body(self,**kwargs):
        return types.SimpleNamespace(challenge=self.challenge,telegram_user_id=kwargs.get('tg',111),contact_user_id=kwargs.get('contact',111),phone=kwargs.get('phone','+998901234567'),full_name='Person')
    def assert_http(self,code,fn,*args):
        with self.assertRaises(HTTPException) as caught:fn(*args)
        self.assertEqual(caught.exception.status_code,code)
    def test_contact_must_belong_to_sender(self):
        self.assert_http(403,self.app.routes['/auth/telegram/confirm'],self.confirm_body(contact=222),'s'*32)
        self.assertEqual(self.db.state['identities'],{})
    def test_bot_secret_required_before_lookup(self):
        self.assert_http(401,self.app.routes['/auth/telegram/confirm'],self.confirm_body(),'bad')
    def test_confirm_idempotent_no_duplicate_identity(self):
        for _ in range(2):self.assertEqual(self.app.routes['/auth/telegram/confirm'](self.confirm_body(),'s'*32),{'status':'confirmed'})
        self.assertEqual(len(self.db.state['identities']),1)
        self.assertEqual(len(self.db.state['sessions']),0)
    def test_browser_secret_required_even_after_bot_confirms(self):
        self.app.routes['/auth/telegram/confirm'](self.confirm_body(),'s'*32)
        wrong=types.SimpleNamespace(challenge=self.challenge,browser_secret='x'*43)
        self.assert_http(401,self.app.routes['/auth/telegram/poll'],wrong,self.request)
        self.assertEqual(len(self.db.state['sessions']),0)
    def test_poll_network_retry_returns_same_token_one_session(self):
        self.app.routes['/auth/telegram/confirm'](self.confirm_body(),'s'*32)
        first=self.app.routes['/auth/telegram/poll'](self.body,self.request)
        retry=self.app.routes['/auth/telegram/poll'](self.body,self.request)
        self.assertEqual(first,retry);self.assertEqual(first['user_id'],111)
        self.assertEqual(len(self.db.state['sessions']),1)
        self.assertEqual(self.p._jwt_tekshir(first['token']),111)
    def test_phone_conflict_does_not_move_accounts(self):
        self.db.state['phones']['+998901234567']=222
        self.assert_http(409,self.app.routes['/auth/telegram/confirm'],self.confirm_body(),'s'*32)
        self.assertEqual(self.db.state['phones']['+998901234567'],222)
        self.assertFalse(self.db.state['identities'])
    def test_link_other_existing_account_is_denied(self):
        token=self.service.issue_session(222,'google')
        sid=self.service.claims(token)['sid']
        row=self.db.state['challenges'][A.digest(self.challenge)];row.update(mode='link',target_user_id=222,link_session_hash=A.digest(sid))
        self.assert_http(409,self.app.routes['/auth/telegram/confirm'],self.confirm_body(),'s'*32)
        self.assertIsNone(self.db.state['challenges'][A.digest(self.challenge)]['confirmed_at'])
    def test_bot_virtual_selected_account_never_used(self):
        self.db.state['accounts']=[{'telegram_id':111,'account_index':0,'uid':111},{'telegram_id':111,'account_index':1,'uid':222,'is_active':True}]
        self.app.routes['/auth/telegram/confirm'](self.confirm_body(),'s'*32)
        self.assertEqual(self.db.state['identities'][111]['user_id'],111)
    def test_moved_raw_telegram_user_is_not_reclaimed(self):
        self.db.state['accounts']=[{'telegram_id':222,'account_index':0,'uid':111}]
        self.assert_http(409,self.app.routes['/auth/telegram/confirm'],self.confirm_body(),'s'*32)
    def test_expiry_and_cancellation_issue_no_token(self):
        row=self.db.state['challenges'][A.digest(self.challenge)];row['expires_at']=datetime.now(timezone.utc)-timedelta(seconds=1)
        self.assertEqual(self.app.routes['/auth/telegram/poll'](self.body,self.request),{'status':'expired'})
        self.assert_http(410,self.app.routes['/auth/telegram/confirm'],self.confirm_body(),'s'*32)
        row['expires_at']=datetime.now(timezone.utc)+timedelta(minutes=1)
        self.app.routes['/auth/telegram/cancel'](self.body,self.request)
        self.assertEqual(self.app.routes['/auth/telegram/poll'](self.body,self.request),{'status':'cancelled'})
    def test_logout_revokes_one_device_and_not_other(self):
        one=self.service.issue_session(111,'google');two=self.service.issue_session(111,'google')
        self.app.routes['/auth/logout'](types.SimpleNamespace(token=one,all_devices=False),self.request)
        self.assert_http(401,self.p._jwt_tekshir,one);self.assertEqual(self.p._jwt_tekshir(two),111)
    def test_logout_all_revokes_other_sessions(self):
        one=self.service.issue_session(111,'google');two=self.service.issue_session(111,'telegram')
        self.app.routes['/auth/logout'](types.SimpleNamespace(token=one,all_devices=True),self.request)
        self.assert_http(401,self.p._jwt_tekshir,one);self.assert_http(401,self.p._jwt_tekshir,two)
    def test_google_ticket_is_not_access_token(self):
        claims={'purpose':'google_login_ticket','user_id':111,'jti':'ticket','exp':(datetime.now(timezone.utc)+timedelta(minutes=1)).timestamp()}
        self.assert_http(401,self.service.verify_session,'ticket',claims)
        self.assertFalse(self.db.state['sessions'])
    def test_google_exchange_grant_one_use(self):
        grant={'jti':'random-token','exp':(datetime.now(timezone.utc)+timedelta(minutes=1)).timestamp()}
        self.service.consume(grant);self.assert_http(401,self.service.consume,grant)
    def test_legacy_session_revocation_cannot_recreate_session(self):
        token=FakeJWT.encode({'user_id':111,'exp':(datetime.now(timezone.utc)+timedelta(days=1)).timestamp()},self.p.JWT_MAXFIY_KALIT)
        self.assertEqual(self.p._jwt_tekshir(token),111)
        self.app.routes['/auth/logout'](types.SimpleNamespace(token=token,all_devices=False),self.request)
        self.assert_http(401,self.p._jwt_tekshir,token)
    def test_logout_all_disables_not_yet_seen_legacy_token(self):
        old=FakeJWT.encode({'user_id':111,'exp':(datetime.now(timezone.utc)+timedelta(days=1)).timestamp()},self.p.JWT_MAXFIY_KALIT)
        current=self.service.issue_session(111,'google')
        self.app.routes['/auth/logout'](types.SimpleNamespace(token=current,all_devices=True),self.request)
        self.assert_http(401,self.p._jwt_tekshir,old)
        self.assertNotIn(A.digest(old),self.db.state['sessions'])
    def test_revoked_link_session_cannot_approve(self):
        token=self.service.issue_session(111,'google')
        sid=self.service.claims(token)['sid']
        self.db.state['challenges'][A.digest(self.challenge)].update(mode='link',target_user_id=111,link_session_hash=A.digest(sid))
        self.app.routes['/auth/logout'](types.SimpleNamespace(token=token,all_devices=False),self.request)
        self.assert_http(410,self.app.routes['/auth/telegram/confirm'],self.confirm_body(),'s'*32)
        self.assertFalse(self.db.state['identities'])
    def password_body(self,token,**kwargs):
        return types.SimpleNamespace(token=token,password=kwargs.get('password','new-password-12345'),current_password=kwargs.get('current_password'),reset=kwargs.get('reset',False))
    def test_set_password_requires_recent_trusted_identity(self):
        token=self.service.issue_session(111,'password')
        self.assert_http(403,self.app.routes['/auth/password/set'],self.password_body(token),self.request)
        self.assertFalse(self.db.state['passwords'])
    def test_password_set_keeps_current_revokes_other_and_unseen_legacy(self):
        token=self.service.issue_session(111,'google');other=self.service.issue_session(111,'google')
        self.app.routes['/auth/password/set'](self.password_body(token),self.request)
        self.assertEqual(self.p._jwt_tekshir(token),111)
        self.assert_http(401,self.p._jwt_tekshir,other)
        self.assertTrue(self.db.state['security'][111])
        self.assertTrue(A.password_matches('new-password-12345',self.db.state['passwords'][111]))
    def test_existing_password_wrong_current_is_rejected(self):
        token=self.service.issue_session(111,'password')
        self.db.state['passwords'][111]=A.password_hash('old-password-12345')
        before=self.db.state['passwords'][111]
        self.assert_http(403,self.app.routes['/auth/password/set'],self.password_body(token,current_password='wrong-password-12345'),self.request)
        self.assertEqual(self.db.state['passwords'][111],before)
    def test_password_change_during_login_cannot_issue_old_password_session(self):
        self.db.state['passwords'][111]=A.password_hash('old-password-12345')
        original_matches=self.app.routes['/auth/password/login'].__globals__['password_matches']
        def concurrent_change(password,stored):
            result=original_matches(password,stored)
            self.db.state['passwords'][111]=A.password_hash('replacement-password-12345')
            return result
        with patch.dict(self.app.routes['/auth/password/login'].__globals__,{'password_matches':concurrent_change}):
            self.assert_http(401,self.app.routes['/auth/password/login'],types.SimpleNamespace(identifier='person@example.com',password='old-password-12345'),self.request)
        self.assertFalse(self.db.state['sessions'])
    def test_password_signin_succeeds_for_existing_identity(self):
        self.db.state['passwords'][111]=A.password_hash('correct-password-12345')
        result=self.app.routes['/auth/password/login'](types.SimpleNamespace(identifier='person@example.com',password='correct-password-12345'),self.request)
        self.assertEqual(result['status'],'complete');self.assertEqual(self.p._jwt_tekshir(result['token']),111)
    def invite_body(self,**kwargs):
        code='ABCD1234WXYZ';key='sha256:'+A.digest(code)
        self.db.state['invites'].setdefault(key,{'stored_code':key,'user_id':222,'ishlatildi':False,'live':True})
        return types.SimpleNamespace(kod=kwargs.get('kod',code),email=kwargs.get('email','new@example.com'),oauth_grant=kwargs.get('grant','valid-grant'))
    def test_imported_employee_claims_one_strong_invite_preserves_id(self):
        body=self.invite_body()
        result=self.app.routes['/auth/invite/claim'](body,self.request)
        self.assertEqual(result['user_id'],222);self.assertEqual(self.p._jwt_tekshir(result['token']),222)
        self.assertEqual(self.db.state['google']['new@example.com'],222)
        self.assertEqual(set(self.db.state['users']),{111,222})
        self.assert_http(400,self.app.routes['/auth/invite/claim'],body,self.request)
        self.assertEqual(len(self.db.state['sessions']),1)
    def test_employee_invite_does_not_reassign_existing_google(self):
        body=self.invite_body(email='person@example.com')
        self.assert_http(409,self.app.routes['/auth/invite/claim'],body,self.request)
        self.assertEqual(self.db.state['google']['person@example.com'],111)
        self.assertFalse(self.db.state['consumed'])
    def test_employee_invite_does_not_claim_password_owned_account(self):
        body=self.invite_body();self.db.state['passwords'][222]=A.password_hash('existing-password-123')
        self.assert_http(409,self.app.routes['/auth/invite/claim'],body,self.request)
        self.assertNotIn('new@example.com',self.db.state['google'])
    def test_invite_rejects_legacy_six_character_codes(self):
        self.assert_http(422,self.app.routes['/auth/invite/claim'],self.invite_body(kod='ABC123'),self.request)
        self.assertFalse(self.db.state['consumed'])
    def test_invite_rejects_expired_and_unverified_grant(self):
        body=self.invite_body(grant='invalid')
        self.assert_http(401,self.app.routes['/auth/invite/claim'],body,self.request)
        body=self.invite_body()
        self.db.state['invites']['sha256:'+A.digest(body.kod)]['live']=False
        self.assert_http(400,self.app.routes['/auth/invite/claim'],body,self.request)
    def test_phone_change_resets_search_permission(self):
        self.app.routes['/auth/telegram/confirm'](self.confirm_body(),'s'*32)
        self.db.state['users'][111]['phone_discoverable']=True
        with self.service.transaction() as cur:
            self.service._resolve_telegram(cur,111,'+998909999999','Same person')
        self.assertFalse(self.db.state['users'][111]['phone_discoverable'])
        self.assertNotIn('+998901234567',self.db.state['phones'])
    def test_password_hash_salted_and_checks_correct_password(self):
        first=A.password_hash('correct-password-123');second=A.password_hash('correct-password-123')
        self.assertNotEqual(first,second);self.assertNotIn('correct-password',first)
        self.assertTrue(A.password_matches('correct-password-123',first));self.assertFalse(A.password_matches('wrong-password-123',first))
    def test_origin_rejects_unrelated_site(self):
        self.assert_http(403,self.service.origin,types.SimpleNamespace(headers={'origin':'https://attacker.example'}))
    def test_no_legacy_sms_side_effects(self):
        tree=ast.parse((ROOT/'samtm_platform.py').read_text())
        for name in ['telefon_kod_sorash','telefon_kod_tasdiqla','telefon_royxat','hisob_ulash','sayt_kod_yarat']:
            fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name==name)
            ns={'HTTPException':HTTPException}
            fn.args.args[0].annotation=None
            fn.decorator_list=[]
            exec(compile(ast.Module(body=[fn],type_ignores=[]),'<legacy>','exec'),ns)
            self.assert_http(410,ns[name],types.SimpleNamespace())

if __name__=='__main__':unittest.main()
