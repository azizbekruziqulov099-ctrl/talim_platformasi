"""Regression coverage for editable canvas geometry and native PPTX output.

Run without an application server or database:
    python -m unittest discover -s tests -p test_presentation_geometry_rev51.py
"""
import base64
from copy import deepcopy
from io import BytesIO
import unittest
import zipfile

from lxml import etree as E
from PIL import Image

from modules.presentation_export import EMU, LAYOUTS, NS, TEMPLATE_DEFAULTS, export_pptx, get_layout_spec
from modules.presentation_layout_validation import validate_slide_geometry


NEW_FAMILIES = ("pencil", "arc", "spiral", "bands")


def tiny_png():
    image = Image.new("RGB", (2, 2), (23, 114, 189))
    output = BytesIO()
    image.save(output, format="PNG")
    return "data:image/png;base64," + base64.b64encode(output.getvalue()).decode("ascii")


PNG = tiny_png()


def box(x=100, y=100, w=200, h=100):
    return {"x": x, "y": y, "w": w, "h": h}


def element(kind="rect", identity="extra", **values):
    return {"id": identity, "kind": kind, **box(), **values}


def document(slides, template="glass"):
    return {
        "schema": 2,
        "title": "Geometry regression",
        "subject": "Math",
        "design": {"template": template, "background": "solid", "overlay": 0, "transition": "none"},
        "slides": slides,
    }


def xml_slides(payload):
    with zipfile.ZipFile(BytesIO(payload)) as archive:
        names = sorted(
            (name for name in archive.namelist() if name.startswith("ppt/slides/slide") and name.endswith(".xml")),
            key=lambda name: int(name.rsplit("slide", 1)[1].split(".")[0]),
        )
        return [E.fromstring(archive.read(name)) for name in names]


def named_shape(root, name):
    matches = root.xpath(".//p:sp[p:nvSpPr/p:cNvPr/@name=$name] | .//p:pic[p:nvPicPr/p:cNvPr/@name=$name]", namespaces=NS, name=name)
    if len(matches) != 1:
        raise AssertionError(f"Expected one native shape named {name!r}; found {len(matches)}")
    return matches[0]


def coordinates(shape):
    transform = shape.find("p:spPr/a:xfrm", NS)
    off, extent = transform.find("a:off", NS), transform.find("a:ext", NS)
    return tuple(int(value) for value in (off.get("x"), off.get("y"), extent.get("cx"), extent.get("cy")))


def emu(rect):
    return tuple(round(rect[field] * EMU) for field in ("x", "y", "w", "h"))


class GeometryValidationTests(unittest.TestCase):
    def test_normalization_is_non_mutating_and_allows_exact_slide_edges(self):
        slide = {
            "placements": {"body2": box(0, 0, 1280, 720)},
            "elements": [element("text", "note", text="First\r\nSecond", color="#AABBCC"),
                         element("rect", "edge", x=1279, y=719, w=1, h=1, fill="#DDEEFF")],
        }
        original = deepcopy(slide)
        normalized = validate_slide_geometry(slide)
        self.assertEqual(slide, original)
        self.assertEqual(normalized["placements"]["body2"], box(0, 0, 1280, 720))
        self.assertEqual(normalized["elements"][0]["text"], "First\nSecond")
        self.assertEqual(normalized["elements"][0]["fontSize"], 28)
        self.assertEqual(normalized["elements"][0]["color"], "#aabbcc")
        self.assertEqual(normalized["elements"][1]["fill"], "#ddeeff")

    def test_rejects_nonfinite_boolean_negative_zero_and_off_slide_coordinates(self):
        invalid = [box(x=float("nan")), box(y=float("inf")), box(w=float("-inf")),
                   box(x=True), box(x="100"), box(x=-1), box(x=10 ** 1000), box(w=0), box(h=-1),
                   box(x=1200, w=81), box(y=700, h=21), box(w=1281), box(h=721)]
        for rect in invalid:
            with self.subTest(rect=rect):
                with self.assertRaises(ValueError):
                    validate_slide_geometry({"placements": {"title": rect}})
                with self.assertRaises(ValueError):
                    export_pptx(document([{"elements": [element(**rect)]}]))

    def test_rejects_unknown_fields_duplicate_ids_and_element_limits(self):
        invalid = [
            {"placements": {"footer": box()}},
            {"placements": {"title": {**box(), "rotation": 10}}},
            {"placements": []},
            {"elements": {}},
            {"elements": [element(rotation=10)]},
            {"elements": [element("video")]},
            {"elements": [element(identity="same"), element(identity="same")]},
            {"elements": [element(identity=str(index)) for index in range(13)]},
            {"elements": [element("text", text="x" * 601)]},
            {"elements": [element("text", text="bad\x00text")]},
            {"elements": [element("text", fontSize=float("nan"))]},
            {"elements": [element("text", fontSize=73)]},
            {"elements": [element("text", color="red")]},
            {"elements": [element(fill="#fff")]},
        ]
        for slide in invalid:
            with self.subTest(slide=slide):
                with self.assertRaises(ValueError):
                    validate_slide_geometry(slide)

    def test_caption_and_example_labels_must_fit_with_their_parent(self):
        for field, caption_field in (("image", "image_caption"), ("image2", "image2_caption")):
            valid = {field: PNG, caption_field: "Caption", "placements": {field: box(100, 500, 150, 182)}}
            self.assertEqual(validate_slide_geometry(valid)["placements"][field]["h"], 182)
            valid["placements"][field]["h"] = 183
            with self.subTest(field=field), self.assertRaises(ValueError):
                validate_slide_geometry(valid)
        self.assertEqual(validate_slide_geometry({"example": "Example", "placements": {"example": box(y=28)}})["placements"]["example"]["y"], 28)
        with self.assertRaises(ValueError):
            validate_slide_geometry({"example": "Example", "placements": {"example": box(y=27)}})

    def test_image_transport_and_real_decode_are_both_checked(self):
        for source in ("https://example.test/image.png", "data:image/svg+xml;base64,PHN2Zy8+", "data:image/png;base64,AAAA", "data:image/png;base64,%%%"):
            with self.subTest(source=source), self.assertRaises(ValueError):
                validate_slide_geometry({"elements": [element("image", image=source)]})
        # A valid transport signature alone must not bypass the image decoder.
        corrupt = "data:image/png;base64," + base64.b64encode(b"\x89PNG\r\n\x1a\nnot-a-png").decode("ascii")
        with self.assertRaises(ValueError):
            export_pptx(document([{"layout": "text", "elements": [element("image", image=corrupt)]}]))
        self.assertEqual(validate_slide_geometry({"elements": [element("image", image=PNG)]})["elements"][0]["image"], PNG)


class NativePptxGeometryTests(unittest.TestCase):
    def test_title_and_all_body_slots_export_at_requested_coordinates(self):
        placements = {"title": box(120, 120, 880, 80), "body": box(80, 280, 300, 130),
                      "body2": box(460, 310, 300, 100), "body3": box(840, 340, 300, 160)}
        slide = {"layout": "three_cards", "title": "Moved title", "body": "One", "body2": "Two", "body3": "Three", "placements": placements}
        root = xml_slides(export_pptx(document([slide])))[0]
        for field, name in (("title", "Sarlavha"), ("body", "Asosiy matn"), ("body2", "2-matn"), ("body3", "3-matn")):
            with self.subTest(field=field):
                shape = named_shape(root, name)
                self.assertEqual(coordinates(shape), emu(placements[field]))
                self.assertIsNotNone(shape.find("p:txBody/a:p/a:r/a:t", NS))

    def test_formula_stays_native_omml_and_example_label_moves_with_example(self):
        placements = {"formula": box(160, 320, 540, 170), "example": box(700, 540, 400, 80)}
        slide = {"layout": "formula", "title": "Formula", "body": "Details", "formula": r"\frac{a}{b}", "example": "Example", "placements": placements}
        root = xml_slides(export_pptx(document([slide])))[0]
        native = named_shape(root, "Formula")
        self.assertEqual(coordinates(native), emu(placements["formula"]))
        self.assertEqual(len(native.xpath(".//m:oMath/m:f", namespaces=NS)), 1)
        self.assertEqual(native.getparent().tag, "{" + NS["mc"] + "}Choice")
        self.assertEqual(len(root.xpath(".//mc:AlternateContent/mc:Fallback/p:pic", namespaces=NS)), 1)
        self.assertEqual(coordinates(named_shape(root, "Misol")), emu(placements["example"]))
        self.assertEqual(coordinates(named_shape(root, "Misol belgisi")), emu(box(700, 512, 400, 20)))

    def test_two_image_captions_move_with_the_image_boxes(self):
        placements = {"image": box(100, 250, 180, 180), "image2": box(750, 300, 200, 200)}
        slide = {"layout": "two_images", "title": "Images", "body": "One", "body2": "Two", "image": PNG, "image2": PNG,
                 "image_caption": "First", "image2_caption": "Second", "placements": placements}
        root = xml_slides(export_pptx(document([slide])))[0]
        for field, name, caption_name in (("image", "Slayd rasmi", "1-rasm izohi"), ("image2", "Slayd 2-rasmi", "2-rasm izohi")):
            with self.subTest(field=field):
                picture = named_shape(root, name)
                self.assertEqual(picture.tag, "{" + NS["p"] + "}pic")
                self.assertEqual(coordinates(picture), emu(placements[field]))
                rect = placements[field]
                self.assertEqual(coordinates(named_shape(root, caption_name)), emu(box(rect["x"], rect["y"] + rect["h"] + 8, rect["w"], 30)))

    def test_custom_text_image_and_rectangle_are_native_and_retain_style_and_order(self):
        elements = [element("rect", "block", x=45, y=450, w=220, h=100, fill="#Aa11Cc"),
                    element("text", "note", x=300, y=480, w=360, h=100, text="Editable note", fontSize=32, color="#12ABef"),
                    element("image", "photo", x=1000, y=470, w=120, h=120, image=PNG)]
        root = xml_slides(export_pptx(document([{"title": "Extras", "elements": elements}])))[0]
        shapes = [named_shape(root, "Qo‘shimcha element: " + item["id"]) for item in elements]
        self.assertEqual([coordinates(shape) for shape in shapes], [emu(item) for item in elements])
        self.assertEqual([E.QName(shape).localname for shape in shapes], ["sp", "sp", "pic"])
        self.assertEqual(shapes[0].find("p:spPr/a:solidFill/a:srgbClr", NS).get("val"), "aa11cc")
        self.assertEqual(shapes[0].find("p:spPr/a:prstGeom", NS).get("prst"), "rect")
        run = shapes[1].find("p:txBody/a:p/a:r", NS)
        self.assertEqual(run.find("a:t", NS).text, "Editable note")
        self.assertEqual(run.find("a:rPr", NS).get("sz"), "2400")
        self.assertEqual(run.find("a:rPr/a:solidFill/a:srgbClr", NS).get("val"), "12abef")
        names = root.xpath("p:cSld/p:spTree/*/p:nvSpPr/p:cNvPr/@name | p:cSld/p:spTree/*/p:nvPicPr/p:cNvPr/@name", namespaces=NS)
        self.assertEqual([name for name in names if name.startswith("Qo‘shimcha element: ")], ["Qo‘shimcha element: " + item["id"] for item in elements])
        self.assertIsNotNone(shapes[2].find("p:blipFill/a:blip", NS).get("{" + NS["r"] + "}embed"))

    def test_measured_native_overflow_is_rejected_after_a_resize(self):
        invalid = [
            {"title": "Cannot fit", "placements": {"title": box(w=1, h=1)}},
            {"elements": [element("text", text="Too big", fontSize=72, w=10, h=10)]},
            {"layout": "formula", "formula": "x+1", "placements": {"formula": box(w=20, h=20)}},
        ]
        for slide in invalid:
            with self.subTest(slide=slide), self.assertRaisesRegex(ValueError, "sig‘madi"):
                export_pptx(document([slide]))

    def test_legacy_five_template_geometry_baselines_are_unchanged(self):
        # Frozen pre-rev51 text geometry; do not derive these values from layouts.
        expected = {
            "glass": ((96, 146, 1088, 96), (96, 254, 1088, 346), (64, 116, 1152, 522)),
            "ribbon": ((96, 146, 1088, 96), (96, 254, 1088, 346), (64, 108, 1152, 530)),
            "split": ((144, 144, 1016, 100), (144, 264, 1016, 336), (112, 114, 1104, 524)),
            "gallery": ((80, 118, 1120, 92), (80, 226, 1120, 382), (48, 98, 1184, 540)),
            "steps": ((116, 145, 1068, 96), (116, 272, 1068, 328), (64, 116, 1152, 522)),
        }
        for family, (title, body, panel) in expected.items():
            with self.subTest(family=family):
                slide = {"layout": "text", "title": "Legacy", "body": "Text"}
                spec = get_layout_spec(slide, {"template": family})
                self.assertEqual(tuple(spec["title"][key] for key in ("x", "y", "w", "h")), title)
                self.assertEqual(tuple(spec["bodySlots"][0][key] for key in ("x", "y", "w", "h")), body)
                self.assertEqual(tuple(spec["panel"][key] for key in ("x", "y", "w", "h")), panel)
                self.assertEqual(spec, get_layout_spec({**slide, "placements": {}, "elements": []}, {"template": family}))
                root = xml_slides(export_pptx(document([slide], family)))[0]
                self.assertEqual(coordinates(named_shape(root, "Sarlavha")), tuple(round(value * EMU) for value in title))

    def test_four_new_families_export_all_eight_layouts_as_native_shapes(self):
        seen_polygon = False
        for family in NEW_FAMILIES:
            with self.subTest(family=family):
                self.assertIn(family, TEMPLATE_DEFAULTS)
                slides = []
                for layout in LAYOUTS:
                    slide = {"layout": layout, "title": "Title", "body": "One"}
                    if layout in ("two_columns", "two_images", "three_cards", "steps"):
                        slide["body2"] = "Two"
                    if layout in ("three_cards", "steps"):
                        slide["body3"] = "Three"
                    if layout == "formula":
                        slide["formula"] = "x+1"
                    if layout in ("image", "cover", "two_images"):
                        slide["image"] = PNG
                    if layout == "two_images":
                        slide["image2"] = PNG
                    slides.append(slide)
                payload = export_pptx(document(slides, family))
                roots = xml_slides(payload)
                self.assertEqual(len(roots), 8)
                for slide, root in zip(slides, roots):
                    with self.subTest(family=family, layout=slide["layout"]):
                        spec = get_layout_spec(slide, {"template": family})
                        self.assertEqual(spec["template"], family)
                        self.assertEqual(coordinates(named_shape(root, "Sarlavha")), emu(spec["title"]))
                        self.assertEqual(named_shape(root, "Sarlavha").tag, "{" + NS["p"] + "}sp")
                        expected_body_count = 3 if slide["layout"] in ("three_cards", "steps") else 2 if slide["layout"] in ("two_columns", "two_images") else 1
                        self.assertEqual(len(spec["bodySlots"]), expected_body_count)
                        for shape in root.xpath(".//p:sp | .//p:pic", namespaces=NS):
                            x, y, w, h = coordinates(shape)
                            self.assertGreater(w, 0)
                            self.assertGreater(h, 0)
                            self.assertGreaterEqual(x, 0)
                            self.assertGreaterEqual(y, 0)
                            self.assertLessEqual(x + w, 1280 * EMU + 1)
                            self.assertLessEqual(y + h, 720 * EMU + 1)
                        polygons = root.xpath(".//p:sp/p:spPr/a:custGeom/a:pathLst/a:path", namespaces=NS)
                        seen_polygon = seen_polygon or bool(polygons)
                        for path in polygons:
                            self.assertEqual(len(path.findall("a:moveTo", NS)), 1)
                            self.assertGreaterEqual(len(path.findall("a:lnTo", NS)), 2)
                            self.assertIsNotNone(path.find("a:close", NS))
                with zipfile.ZipFile(BytesIO(payload)) as archive:
                    for name in archive.namelist():
                        if name.startswith("ppt/slides/_rels/"):
                            relations = E.fromstring(archive.read(name))
                            for relation in relations:
                                self.assertNotEqual(relation.get("TargetMode"), "External")
                                if relation.get("Type", "").endswith("/image"):
                                    self.assertIn("ppt/" + relation.get("Target").removeprefix("../"), archive.namelist())
        self.assertTrue(seen_polygon, "New family motifs must include native polygon geometry")

    def test_infographic_body_positions_are_distinct_native_compositions(self):
        expected = {
            "pencil": [(96, 282, 424, 108), (760, 374, 424, 108), (96, 484, 424, 108)],
            "arc": [(414, 244, 714, 96), (414, 364, 714, 96), (414, 484, 714, 96)],
            "spiral": [(96, 230, 320, 96), (480, 526, 320, 96), (864, 230, 320, 96)],
            "bands": [(354, 244, 670, 96), (354, 364, 670, 96), (354, 484, 670, 96)],
        }
        slide = {"layout": "steps", "title": "Reference", "body": "One", "body2": "Two", "body3": "Three"}
        for family, positions in expected.items():
            with self.subTest(family=family):
                spec = get_layout_spec(slide, {"template": family})
                self.assertEqual([tuple(slot[key] for key in ("x", "y", "w", "h")) for slot in spec["bodySlots"]], positions)
                root = xml_slides(export_pptx(document([slide], family)))[0]
                for name, position in zip(("Asosiy matn", "2-matn", "3-matn"), positions):
                    self.assertEqual(coordinates(named_shape(root, name)), tuple(round(value * EMU) for value in position))

    def test_empty_custom_text_keeps_an_editable_native_box(self):
        extra = element("text", "empty", text="")
        root = xml_slides(export_pptx(document([{"elements": [extra]}])))[0]
        shape = named_shape(root, "Qo‘shimcha element: empty")
        self.assertEqual(coordinates(shape), emu(extra))
        self.assertIsNotNone(shape.find("p:txBody/a:p", NS))

    def test_reference_callouts_fit_three_native_lines_at_large_size(self):
        text = "Birinchi fikr\nIkkinchi fikr\nUchinchi fikr"
        slide = {"layout": "steps", "title": "Reference", "body": text, "body2": text, "body3": text}
        for family in NEW_FAMILIES:
            with self.subTest(family=family):
                source = document([slide], family)
                source["design"]["size"] = "large"
                root = xml_slides(export_pptx(source))[0]
                for name in ("Asosiy matn", "2-matn", "3-matn"):
                    shape = named_shape(root, name)
                    self.assertEqual(len(shape.findall("p:txBody/a:p", NS)), 3)
                    self.assertEqual(shape.find("p:txBody/a:p/a:r/a:rPr", NS).get("sz"), "1800")

    def test_selected_palette_changes_native_motif_fill_without_changing_geometry(self):
        slide = {"layout": "steps", "title": "Palette", "body": "One", "body2": "Two", "body3": "Three"}
        for family in NEW_FAMILIES:
            with self.subTest(family=family):
                original = get_layout_spec(slide, {"template": family})
                changed = get_layout_spec(slide, {"template": family, "accent": "blue"})
                self.assertEqual(original["bodySlots"], changed["bodySlots"])
                self.assertEqual([{key: shape[key] for key in ("x", "y", "w", "h")} for shape in original["decorations"]],
                                 [{key: shape[key] for key in ("x", "y", "w", "h")} for shape in changed["decorations"]])
                self.assertNotEqual([shape["fill"] for shape in original["decorations"]], [shape["fill"] for shape in changed["decorations"]])
                source = document([slide], family)
                source["design"]["accent"] = "blue"
                root = xml_slides(export_pptx(source))[0]
                colors = root.xpath(".//p:sp[p:nvSpPr/p:cNvPr[starts-with(@name, 'Bezak ')]]/p:spPr/a:solidFill/a:srgbClr/@val", namespaces=NS)
                self.assertTrue(set(colors) & {"c7d8ed", "799abf", "45658e"})


if __name__ == "__main__":
    unittest.main()
