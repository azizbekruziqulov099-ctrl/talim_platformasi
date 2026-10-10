"""Bounded upload and actual route failure-path tests without a database.
Run: python -m unittest tests.test_kabutar_uploads -v
"""
import ast
import asyncio
import re
import types
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import Mock
from kabutar_uploads import MIB, KABUTAR_UPLOAD_LIMITS_MB, UploadTooLarge, read_bounded_upload

ROOT = Path(__file__).resolve().parents[1]


class Upload:
    def __init__(self, data=b'PNG sample', size=None, fail=None):
        self.data, self.size, self.fail = data, size, fail
        self.offset = 0
        self.closed = 0
        self.read_sizes = []
        self.filename, self.content_type = 'rasm.png', 'image/png'
    async def read(self, count):
        self.read_sizes.append(count)
        if self.fail:
            raise self.fail
        block = self.data[self.offset:self.offset+count]
        self.offset += len(block)
        return block
    async def close(self):
        self.closed += 1


class HTTPError(Exception):
    def __init__(self, status_code, detail):
        self.status_code, self.detail = status_code, detail


def route_function(filename, name, conn):
    """Execute the actual selected endpoint, stubbing unrelated infrastructure."""
    tree = ast.parse((ROOT / filename).read_text())
    node = next(n for n in tree.body if isinstance(n, ast.AsyncFunctionDef) and n.name == name)
    node.decorator_list = []
    node.args.defaults = [ast.Constant(None) for _ in node.args.defaults]
    for arg in node.args.args:
        arg.annotation = None
    env = {
        '__name__':'kabutar_upload_route_test', 'HTTPException':HTTPError,
        '_jwt_tekshir':lambda token:11, '_db':lambda:conn, 're':re,
        'psycopg2':types.SimpleNamespace(Binary=lambda data:data),
        '_SOKINISH_SOZLARI_BOSHLANGICH':[], '_XAVFLI_SOZLAR_BOSHLANGICH':[],
        '_matnda_royxat_sozi_bormi':lambda *args:False,
        '_fayl_turi_ruxsat_etilganmi':lambda *args:True,
        '_faylda_virus_bormi':lambda data:False, '_rasm_uyatsizmi':lambda data:False,
        '_kabutar_ruxsat':lambda *args:True,
    }
    for helper in ['_chat_jadvallari','_chat_suhbat_ruxsat','_moderatsiya_jadvallari','_kabutar_jadval']:
        env[helper] = lambda *args:None
    if filename == 'samtm_school.py':
        assignment = next(n for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='_KABUTAR_FAYL_TURLARI' for t in n.targets))
        env['_KABUTAR_FAYL_TURLARI'] = ast.literal_eval(assignment.value)
    exec(compile(ast.fix_missing_locations(ast.Module(body=[node],type_ignores=[])),filename,'exec'),env)
    return env[name]


class UploadTests(unittest.IsolatedAsyncioTestCase):
    async def test_exact_limit_is_accepted(self):
        upload = Upload(b'x' * 100)
        self.assertEqual(await read_bounded_upload(upload,100), b'x'*100)
        self.assertEqual(upload.closed,1)

    async def test_unknown_size_reads_at_most_limit_plus_one_then_rejects(self):
        upload = Upload(b'x' * 10000)
        with self.assertRaises(UploadTooLarge):
            await read_bounded_upload(upload,100)
        self.assertEqual(upload.offset,101)
        self.assertEqual(upload.closed,1)

    async def test_measured_oversize_is_rejected_without_loading_bytes(self):
        upload = Upload(size=16*MIB)
        with self.assertRaises(UploadTooLarge):
            await read_bounded_upload(upload,15*MIB)
        self.assertEqual(upload.read_sizes,[])
        self.assertEqual(upload.closed,1)

    async def test_chunks_stay_bounded(self):
        upload = Upload(b'x'*(130*1024))
        self.assertEqual(len(await read_bounded_upload(upload,140*1024)),130*1024)
        self.assertLessEqual(max(upload.read_sizes),64*1024)

    async def test_read_error_and_cancel_close_temp_file(self):
        for error in [OSError('read failed'),asyncio.CancelledError()]:
            upload = Upload(fail=error)
            with self.assertRaises(type(error)):
                await read_bounded_upload(upload,100)
            self.assertEqual(upload.closed,1)

    async def test_empty_returns_empty_and_closes(self):
        upload = Upload(b'')
        self.assertEqual(await read_bounded_upload(upload,100),b'')
        self.assertEqual(upload.closed,1)

    async def test_legacy_route_rejects_cap_and_returns_db_connection(self):
        conn=Mock(); upload=Upload(size=16*MIB)
        send=route_function('samtm_platform.py','chat_xabar_yubor',conn)
        with self.assertRaises(HTTPError) as exc:
            await send(token='token',guruh_id=5,fayl_turi='hujjat',fayl=upload)
        self.assertEqual(exc.exception.status_code,413)
        conn.rollback.assert_called_once();conn.cursor.return_value.close.assert_called_once();conn.close.assert_called_once()
        self.assertEqual(upload.closed,1)
        conn.cursor.return_value.execute.assert_not_called()

    async def test_legacy_route_cancellation_also_returns_db_connection(self):
        conn=Mock(); upload=Upload(fail=asyncio.CancelledError())
        send=route_function('samtm_platform.py','chat_xabar_yubor',conn)
        with self.assertRaises(asyncio.CancelledError):
            await send(token='token',guruh_id=5,fayl_turi='hujjat',fayl=upload)
        conn.rollback.assert_called_once();conn.close.assert_called_once()
        self.assertEqual(upload.closed,1)

    async def test_school_route_rejects_before_opening_db(self):
        conn=Mock(); upload=Upload(size=16*MIB)
        send=route_function('samtm_school.py','v2257_kabutar_yubor',conn)
        with self.assertRaises(HTTPError) as exc:
            await send(token='token',qabul_qiluvchi_user_id=2,fayl_turi='hujjat',fayl=upload)
        self.assertEqual(exc.exception.status_code,413)
        conn.cursor.assert_not_called()
        self.assertEqual(upload.closed,1)

    async def test_image_hujjat_filename_mime_caption_protocol_still_works(self):
        for filename,name,kwargs in [
            ('samtm_platform.py','chat_xabar_yubor',{'guruh_id':5}),
            ('samtm_school.py','v2257_kabutar_yubor',{'qabul_qiluvchi_user_id':2}),
        ]:
            conn=Mock(); upload=Upload()
            inserted={'id':25,'yaratilgan_at':datetime.now(timezone.utc)}
            conn.cursor.return_value.fetchone.side_effect = ([{'jami':0},inserted] if filename=='samtm_platform.py' else [inserted])
            send=route_function(filename,name,conn)
            result=await send(token='token',matn='Rasm izohi',fayl_turi='hujjat',fayl=upload,**kwargs)
            self.assertEqual(result['id'],25)
            parameters=conn.cursor.return_value.execute.call_args.args[1]
            self.assertIn('image/png',parameters);self.assertIn('rasm.png',parameters);self.assertIn('Rasm izohi',parameters)
            conn.commit.assert_called_once();conn.close.assert_called_once();self.assertEqual(upload.closed,1)

    def test_existing_frontend_limits_align(self):
        self.assertEqual(KABUTAR_UPLOAD_LIMITS_MB,{'audio':15,'video':40,'video_doira':40,'hujjat':15})


if __name__=='__main__':unittest.main()
