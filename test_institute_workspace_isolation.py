"""Regression contracts for institute/workspace isolation.

These tests intentionally inspect the deploy sources.  The bug they protect
against crossed two otherwise valid systems: an institute workspace was
initially rendered from the user's legacy profile, then an asynchronous
multi-organization response replaced index zero with a school.  A stale or
archived V17 context could also be re-provisioned by the institute bootstrap.
"""

from __future__ import annotations

import ast
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def _first_existing(*paths: Path) -> Path:
    for path in paths:
        if path.exists():
            return path
    raise FileNotFoundError("Deploy source topilmadi: " + ", ".join(map(str, paths)))


def _read(*paths: Path) -> str:
    return _first_existing(*paths).read_text(encoding="utf-8")


def _python_function(source: str, name: str) -> str:
    tree = ast.parse(source)
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == name:
            return ast.get_source_segment(source, node) or ""
    raise AssertionError(f"{name} funksiyasi topilmadi")


def _javascript_window(source: str, name: str, length: int = 2400) -> str:
    """Return a deterministic window around a named top-level JS helper."""
    match = re.search(
        rf"(?:function\s+{re.escape(name)}\s*\(|const\s+{re.escape(name)}\s*=)",
        source,
    )
    if not match:
        raise AssertionError(f"{name} yordamchi funksiyasi topilmadi")
    return source[match.start() : match.start() + length]


class InstituteBackendArchiveIsolationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.backend = _read(
            ROOT / "institute_work/backend/samtm_institute.py",
            ROOT / "upload/Pasted text(20260902-090331).txt",
        )
        cls.platform = _read(
            ROOT / "institute_work/backend/samtm_platform.py",
            ROOT / "institute_work/backend/main.py",
            ROOT / "institute_base/backend/main.py",
        )

    def test_resolver_validates_type_activity_and_lifecycle_before_using_map(self):
        resolver = _python_function(self.backend, "_resolve_university")
        normalized = re.sub(r"\s+", " ", resolver).lower()

        self.assertIn("organization_type='institute'", normalized)
        self.assertRegex(normalized, r"(?:c|context)\.active\s*=\s*true")
        self.assertIn("lifecycle_status", normalized)
        self.assertRegex(
            normalized,
            r"lifecycle_status[^\n]*(?:trial|active|read_only)",
            "Only live V17 lifecycle states may resolve an institute",
        )

        validation_at = min(
            normalized.index("organization_type='institute'"),
            normalized.index("lifecycle_status"),
        )
        mapped_return = re.search(r"if\s+mapped\s*:[^\n]*\n?\s*return", normalized)
        if mapped_return:
            self.assertLess(
                validation_at,
                mapped_return.start(),
                "A stale existing map must not bypass type/lifecycle validation",
            )

    def test_archived_workspace_is_rejected_before_any_reprovision_insert(self):
        resolver = _python_function(self.backend, "_resolve_university")
        lowered = resolver.lower()
        self.assertIn(
            "lifecycle_status",
            lowered,
            "Resolver must inspect lifecycle before it may provision a university",
        )
        lifecycle_at = lowered.index("lifecycle_status")
        insert_at = lowered.index("insert into universitetlar")
        self.assertLess(lifecycle_at, insert_at)
        self.assertTrue(
            "archiv" in lowered or all(state in lowered for state in ("trial", "active", "read_only")),
            "Archived/deleted lifecycle states must be excluded with a positive allow-list",
        )

    def test_my_organizations_does_not_return_inactive_or_archived_contexts(self):
        endpoint = _python_function(self.platform, "muassasalarim")
        normalized = re.sub(r"\s+", " ", endpoint).lower()
        self.assertRegex(normalized, r"(?:c|context)\.active\s*=\s*true")
        self.assertIn("lifecycle_status", normalized)
        self.assertTrue(
            "archiv" in normalized or all(state in normalized for state in ("trial", "active", "read_only")),
            "The membership list must exclude archived/deleted V17 organizations",
        )

    def test_wrong_type_workspace_map_cannot_revive_a_legacy_university(self):
        endpoint = _python_function(self.platform, "muassasalarim")
        normalized = re.sub(r"\s+", " ", endpoint).lower()
        self.assertIn("uwm.universitet_id=%s", normalized)
        self.assertRegex(
            normalized,
            r"bool_or\s*\([^)]*organization_type='institute'[^)]*context_type='university'",
            "Noto'g'ri school->universitet xaritasi mavjud deb topilib, faol institut deb qabul qilinmasligi kerak",
        )

    def test_v17_institute_dto_uses_mapped_university_id(self):
        endpoint = _python_function(self.platform, "muassasalarim")
        normalized = re.sub(r"\s+", " ", endpoint).lower()
        self.assertIn(
            "then uwm.universitet_id else c.external_id end",
            normalized,
        )

    def test_explicit_legacy_id_cannot_bypass_active_workspace_check(self):
        bootstrap = _python_function(self.backend, "bootstrap")
        self.assertIn(
            "_require_active_university_source(cur, uid)",
            bootstrap,
            "universitet_id bilan ochish ham arxivlangan V17 manbasini qayta tekshirishi kerak",
        )

    def test_every_direct_institute_route_membership_checks_active_source(self):
        endpoint = _python_function(self.backend, "_require_member")
        self.assertIn("_require_active_university_source(cur, university_id)", endpoint)

    def test_super_admin_list_filters_archived_or_wrong_type_mappings(self):
        endpoint = _python_function(self.backend, "super_admin_institutes")
        normalized = re.sub(r"\s+", " ", endpoint).lower()
        self.assertIn("universitet_workspace_map", normalized)
        self.assertIn("organization_type='institute'", normalized)
        self.assertRegex(normalized, r"(?:c|context)\.active\s*=\s*true")
        self.assertIn("lifecycle_status", normalized)

    def test_legacy_admin_list_uses_the_same_archive_filter(self):
        endpoint = _python_function(self.platform, "universitetlar_royxati")
        normalized = re.sub(r"\s+", " ", endpoint).lower()
        self.assertIn("universitet_workspace_map", normalized)
        self.assertIn("organization_type='institute'", normalized)
        self.assertIn("lifecycle_status", normalized)


class InstituteFrontendStableSelectionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = _read(
            ROOT / "institute_work/frontend/src/App.jsx",
            ROOT / "institute_base/frontend/src/App.jsx",
        )
        cls.workspace = _read(
            ROOT / "institute_work/frontend/src/institute/InstituteWorkspace.jsx",
            ROOT / "upload/Pasted text(20260902-084059).txt",
        )

    def test_membership_identity_is_stable_and_not_an_array_index(self):
        key_helper = _javascript_window(self.app, "muassasaBarqarorKaliti", 900)
        selection_helper = _javascript_window(self.app, "faolMuassasaniTanla", 2400)

        self.assertIn("turi", key_helper)
        self.assertRegex(key_helper, r"context_id|muassasa_id|organization_v17_id")
        self.assertLess(
            key_helper.index("item.muassasa_id"),
            key_helper.index("item.context_id"),
            "Profil IDsi V17 DTOdagi external ID bilan bir xil tanlov kalitini berishi kerak",
        )
        self.assertIn("tanlanganKalit", selection_helper)
        self.assertIn("kerakliTuri", selection_helper)
        self.assertRegex(selection_helper, r"\.find\s*\(")
        same_key_at = selection_helper.index("tanlanganKalit")
        wanted_type_at = selection_helper.index("kerakliTuri", same_key_at + 1)
        self.assertLess(
            same_key_at,
            wanted_type_at,
            "Existing Pedagogika selection must win before a type fallback",
        )

    def test_institute_route_explicitly_selects_university_membership(self):
        route_at = self.app.index('korinish === "institut_workspace"')
        route = self.app[route_at : route_at + 3000]
        self.assertRegex(self.app, r"kerakliTuri[^\n]{0,160}(?:universitet|university)")
        self.assertNotRegex(route, r"muassasalar(?:im)?\s*\[\s*0\s*\]")
        self.assertRegex(route, r"initialWorkspace=.*(?:faol|aktiv|tanlangan).*Muassasa")

    def test_institute_component_never_receives_a_school_workspace(self):
        route_at = self.app.index("<InstituteWorkspace")
        route = self.app[route_at : route_at + 1000]
        self.assertIn('turi === "universitet"', route)
        self.assertNotIn('turi === "maktab"', route)

    def test_workspace_bootstrap_prefers_explicit_context_over_legacy_fallback(self):
        self.assertIn("initialWorkspace?.context_id", self.workspace)
        self.assertIn('qs.set("workspace_id", workspaceId)', self.workspace)
        self.assertIn('qs.set("universitet_id"', self.workspace)

    def test_authoritative_empty_or_failed_membership_never_uses_stale_profile(self):
        self.assertIn(
            "muassasalarJavobiOlindi ? muassasalar : profilMuassasalar",
            self.app,
        )
        fetch_at = self.app.index("/api/auth/muassasalarim")
        fetch_flow = self.app[fetch_at : fetch_at + 1800]
        self.assertGreaterEqual(fetch_flow.count("setMuassasalarJavobiOlindi(true)"), 2)
        self.assertIn("setMuassasalar([])", fetch_flow)
        self.assertIn("setMuassasalarXato", fetch_flow)

    def test_admission_buttons_call_the_existing_generic_stage_route(self):
        panel = _javascript_window(self.workspace, "AdmissionsPanel", 18000)
        self.assertIn("const markStage", panel)
        self.assertIn("/bosqich", panel)
        self.assertIn("JSON.stringify({ token, bosqich })", panel)
        self.assertNotIn("/${id}/hujjat", panel)
        self.assertNotIn("/${id}/hemis", panel)


class InstituteHierarchyIsolationTests(unittest.TestCase):
    """Keep identically named directions inside their own department."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.backend = _read(
            ROOT / "institute_work/backend/samtm_institute.py",
            ROOT / "upload/Pasted text(20260902-090331).txt",
        )
        cls.workspace = _read(
            ROOT / "institute_work/frontend/src/institute/InstituteWorkspace.jsx",
            ROOT / "upload/Pasted text(20260902-084059).txt",
        )

    @staticmethod
    def _assert_department_scoped_group_key(function_source: str) -> None:
        """Every program grouping key must carry its department scope.

        A direction name is not globally unique within a faculty.  For example,
        two departments may both own a direction called ``Pedagogika``.  Such
        rows may be canonicalised only when both their department and direction
        identities match.
        """

        tree = ast.parse(function_source)
        group_calls = [
            node
            for node in ast.walk(tree)
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr == "setdefault"
            and isinstance(node.func.value, ast.Name)
            and node.func.value.id == "grouped"
        ]
        # The safest implementation does not canonicalise program rows at all;
        # in that case each row remains under the department query that loaded it.
        for call in group_calls:
            key_source = (
                ast.get_source_segment(function_source, call.args[0])
                if call.args
                else ""
            ) or ""
            if not re.search(r"department|kafedra", key_source, flags=re.IGNORECASE):
                raise AssertionError(
                    "Bir xil nomli yo'nalishlar boshqa kafedradan qo'shilib ketmasligi "
                    "uchun grouped kalitida kafedra id/nomi bo'lishi shart"
                )

    def test_structure_program_canonicalization_is_department_scoped(self):
        endpoint = _python_function(self.backend, "structure")
        normalized = re.sub(r"\s+", " ", endpoint).lower()
        self.assertIn(
            "where y.kafedra_id=%s and y.faol=true",
            normalized,
            "Har bir kafedraning yo'nalishlari o'z parent IDsi bilan yuklanishi kerak",
        )
        self._assert_department_scoped_group_key(endpoint)

    def test_faculty_program_list_does_not_merge_across_departments(self):
        endpoint = _python_function(self.backend, "faculty_programs")
        normalized = re.sub(r"\s+", " ", endpoint).lower()

        self.assertIn("y.kafedra_id", normalized)
        self.assertIn("k.nomi kafedra_nomi", normalized)
        # Keeping every DB row is valid. If legacy aliases are deduplicated,
        # however, their key must include the department.
        self._assert_department_scoped_group_key(endpoint)

    def test_structure_import_program_identity_includes_department(self):
        commit = _python_function(self.backend, "structure_commit")
        normalized = re.sub(r"\s+", " ", commit)
        self.assertRegex(
            normalized,
            r"pk\s*=\s*\(\s*dk\s*,\s*_key\s*\(\s*item\s*\[\s*[\"']yonalish[\"']\s*\]",
            "Import xaritasida yo'nalish kaliti fakultet+kafedra (dk) doirasida bo'lishi kerak",
        )

    def test_frontend_canonicalization_is_department_scoped(self):
        helper = _javascript_window(
            self.workspace,
            "canonicalizeInstituteStructure",
            7000,
        )
        self.assertRegex(
            helper,
            r"faculty\.kafedralar\s*\|\|\s*\[\]\)\.map\s*\(\s*department",
            "Frontend kafedra daraxtini parent-child tartibida saqlashi kerak",
        )
        if "programGroups" in helper:
            key_lines = re.findall(r"const\s+key\s*=\s*([^;]+);", helper)
            program_key = next(
                (line for line in key_lines if "program" in line.lower()),
                "",
            )
            self.assertRegex(
                program_key,
                r"department|kafedra",
                "Frontend bir xil nomli yo'nalishlarni faqat o'z kafedrasi ichida birlashtirishi kerak",
            )

    def test_frontend_requires_department_selection_before_programs(self):
        panel = _javascript_window(self.workspace, "StructurePanel", 22000)
        self.assertIn("selectedDepartment", panel)
        self.assertRegex(panel, r"selectedDepartment\.yonalishlar\s*\|\|\s*\[\]")
        self.assertNotIn("selectedFaculty.kafedralar.flatMap", panel)


class InstituteAdmissionCommitIsolationTests(unittest.TestCase):
    """Admission imports consume structure; they must never mutate it."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.backend = _read(
            ROOT / "institute_work/backend/samtm_institute.py",
            ROOT / "upload/Pasted text(20260902-090331).txt",
        )
        cls.commit = _python_function(cls.backend, "admission_commit")
        cls.normalized = re.sub(r"\s+", " ", cls.commit).lower()

    def test_admission_commit_does_not_create_departments_or_directions(self):
        self.assertNotIn(
            "insert into kafedralar",
            self.normalized,
            "Qabul importi yangi kafedra yaratmasligi kerak; tuzilma alohida bosqichda yaratiladi",
        )
        self.assertNotIn(
            "insert into universitet_yonalishlari",
            self.normalized,
            "Qabul importi yangi yo'nalish yaratmasligi kerak; faqat mavjud faol yo'nalishga bog'laydi",
        )

    def test_admission_commit_never_reactivates_archived_structure(self):
        structure_prefix = self.normalized.split(
            "insert into universitet_qabul_talabalari",
            1,
        )[0]
        self.assertNotRegex(
            structure_prefix,
            r"do\s+update\s+set\s+(?:\w+\.)?faol\s*=\s*true",
            "Qabul commit arxivlangan kafedra/yo'nalishni qayta faollashtirmasligi kerak",
        )

    def test_all_directions_are_resolved_as_active_before_student_write(self):
        student_insert_at = self.normalized.find(
            "insert into universitet_qabul_talabalari"
        )
        self.assertGreater(student_insert_at, 0, "Talaba import SQL topilmadi")
        resolution = self.normalized[:student_insert_at]

        self.assertRegex(
            resolution,
            r"universitet_yonalishlari[^;]{0,900}faol\s*=\s*true",
            "Qabul faqat mavjud faol yo'nalishni resolve qilishi kerak",
        )
        self.assertRegex(
            resolution,
            r"if\s+not\s+(?:existing_program|program_id|resolved[^:]*)\s*:\s*raise\s+httpexception",
            "Mos faol yo'nalish topilmasa commit talaba yozishdan oldin aniq xato bilan to'xtashi kerak",
        )

    def test_name_only_fallback_cannot_pick_an_arbitrary_department(self):
        student_insert_at = self.normalized.find(
            "insert into universitet_qabul_talabalari"
        )
        resolution = self.normalized[:student_insert_at]
        ambiguous_fallback = re.search(
            r"lower\s*\(\s*trim\s*\(\s*y\.nomi\s*\)\s*\)"
            r".{0,500}?group\s+by\s+y\.id"
            r".{0,240}?limit\s+1",
            resolution,
        )
        self.assertIsNone(
            ambiguous_fallback,
            "Bir xil nomli yo'nalish bo'lsa qabul importi kafedrasiz LIMIT 1 bilan tasodifiy tanlamasligi kerak",
        )


class InstituteAdmissionRoleContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.backend = _read(ROOT / "institute_work/backend/samtm_institute.py")

    def test_document_and_hemis_stage_roles_are_separate(self):
        endpoint = _python_function(self.backend, "update_stage")
        normalized = re.sub(r"\s+", " ", endpoint)
        self.assertRegex(normalized, r"req\.bosqich\s*==\s*2.{0,500}MARK_DOCUMENT_ROLES")
        self.assertRegex(normalized, r"else:.{0,700}MARK_HEMIS_ROLES")

    def test_reports_have_json_and_xlsx_routes(self):
        for path in (
            '/qabul/kunlik_hisobot',
            '/qabul/kunlik_hisobot.xlsx',
            '/qabul/umumiy_hisobot',
            '/qabul/umumiy_hisobot.xlsx',
        ):
            self.assertEqual(
                self.backend.count(f'@router.get("{path}")'),
                1,
                f"{path} aynan bir marta ro'yxatdan o'tishi kerak",
            )

    def test_admission_template_has_a_real_authenticated_route(self):
        self.assertEqual(self.backend.count('@router.get("/qabul/shablon")'), 1)
        endpoint = _python_function(self.backend, "admission_template")
        self.assertIn("_require_member", endpoint)
        self.assertIn("_admission_template_xlsx", endpoint)


if __name__ == "__main__":
    unittest.main()
