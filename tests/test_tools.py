import contextlib, io, json, os, shutil, subprocess, sys, tempfile, unittest
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
import audit_pdf, pagination_audit, review_queue, build_public, privacy_check

def tiny_pdf(path, boxes=((200, 100, 0), (100, 200, 90))):
    objs, kids = [], " ".join(f"{3 + i} 0 R" for i in range(len(boxes)))
    objs.append("<< /Type /Catalog /Pages 2 0 R >>")
    objs.append(f"<< /Type /Pages /Kids [{kids}] /Count {len(boxes)} >>")
    for w, h, r in boxes:
        objs.append(f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 {w} {h}] /Rotate {r} >>")
    out, offs = b"%PDF-1.4\n", []
    for i, o in enumerate(objs, 1):
        offs.append(len(out)); out += f"{i} 0 obj\n{o}\nendobj\n".encode()
    x = len(out)
    out += f"xref\n0 {len(objs)+1}\n0000000000 65535 f \n".encode()
    out += b"".join(f"{o:010d} 00000 n \n".encode() for o in offs)
    out += f"trailer\n<< /Size {len(objs)+1} /Root 1 0 R >>\nstartxref\n{x}\n%%EOF\n".encode()
    with open(path, "wb") as f: f.write(out)

def make_repo(d):
    os.makedirs(os.path.join(d, "data", "contributions")); os.makedirs(os.path.join(d, "reader"))
    json.dump({"pages": [], "chapters": []}, open(os.path.join(d, "data", "manuscript.json"), "w"))
    open(os.path.join(d, "reader", "index.html"), "w").write("<html></html>")
    for cid, st in (("c1", "pending"), ("c2", "approved"), ("c3", "rejected")):
        json.dump({"id": cid, "status": st, "title": f"Title {cid} zz", "body": f"Body {cid} qq", "audience": "family",
                   "kind": "memory", "reviewed_by": None, "reviewed_at": None},
                  open(os.path.join(d, "data", "contributions", cid + ".json"), "w"))
    open(os.path.join(d, "data", "review_log.jsonl"), "w").close()

class Base(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.mkdtemp(); self.addCleanup(shutil.rmtree, self.d)

class PdfTests(Base):
    def test_audit(self):
        p = os.path.join(self.d, "t.pdf"); tiny_pdf(p)
        before = open(p, "rb").read()
        r = audit_pdf.audit(p)
        self.assertEqual(r["page_count"], 2)
        self.assertEqual([x["orientation"] for x in r["pages"]], ["landscape", "landscape"])  # 2nd rotated 90
        self.assertEqual(r["pages"][1]["rotation"], 90)
        self.assertEqual(len(r["sha256"]), 64)
        self.assertEqual(open(p, "rb").read(), before)
        self.assertEqual(os.listdir(self.d), ["t.pdf"])
    def test_cli_does_not_print_path(self):
        p = os.path.join(self.d, "secretname.pdf"); tiny_pdf(p)
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf): self.assertEqual(audit_pdf.main([p]), 0)
        self.assertNotIn("secretname", buf.getvalue())
    def test_rejects_non_pdf(self):
        p = os.path.join(self.d, "x.pdf"); open(p, "w").write("hello")
        with contextlib.redirect_stderr(io.StringIO()): self.assertEqual(audit_pdf.main([p]), 2)

class PaginationTests(unittest.TestCase):
    def test_real_manuscript_stays_open(self):
        m = json.load(open(os.path.join(ROOT, "data", "manuscript.json")))
        r = pagination_audit.audit(m)
        self.assertEqual(r["completeness"], "OPEN")
        self.assertNotIn("complete.", r["statement"].replace("NOT established", ""))
        self.assertIn(2, r["unaccounted_numbers_in_range"])
    def test_dups_and_toc(self):
        m = {"pages": [{"id": "a", "printed_number": 1, "transcription_status": "none", "kind": "text"},
                       {"id": "b", "printed_number": 1, "transcription_status": "verified", "kind": "text"},
                       {"id": "c", "printed_number": 4, "transcription_status": "verified", "kind": "text"}],
             "chapters": [{"pages": ["a", "zz", "a"]}]}
        r = pagination_audit.audit(m)
        self.assertEqual(r["duplicate_printed_numbers"], [1]); self.assertEqual(r["unaccounted_numbers_in_range"], [2, 3])
        self.assertEqual(r["blank_pages"], ["a"]); self.assertEqual(r["toc_unknown_page_ids"], ["zz"])
        self.assertEqual(r["toc_duplicate_page_ids"], ["a"]); self.assertEqual(r["pages_not_in_toc"], ["b", "c"])

class ReviewTests(Base):
    def setUp(self):
        super().setUp(); make_repo(self.d)
    def test_approve_chain(self):
        r1 = review_queue.decide(self.d, "c1", "approved", "Rev", today="2026-01-01")
        self.assertEqual(r1["prev_hash"], "0" * 64)
        log = review_queue.read_log(self.d); self.assertTrue(review_queue.verify_log(log))
        c = json.load(open(os.path.join(self.d, "data", "contributions", "c1.json")))
        self.assertEqual((c["status"], c["reviewed_by"]), ("approved", "Rev"))
    def test_tamper_detected_and_refused(self):
        review_queue.decide(self.d, "c1", "rejected", "Rev")
        lp = os.path.join(self.d, "data", "review_log.jsonl")
        t = open(lp).read().replace("rejected", "approved"); open(lp, "w").write(t)
        self.assertFalse(review_queue.verify_log(review_queue.read_log(self.d)))
    def test_requires_reviewer_and_pending(self):
        with self.assertRaises(SystemExit): review_queue.decide(self.d, "c1", "approved", " ")
        with self.assertRaises(SystemExit): review_queue.decide(self.d, "c2", "rejected", "Rev")
        with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
            review_queue.main(["approve", "c1"], root=self.d)
    def test_matches_existing_log_format(self):
        self.assertTrue(review_queue.verify_log(review_queue.read_log(ROOT)))

class BuildTests(Base):
    def setUp(self):
        super().setUp(); make_repo(self.d)
    def test_only_approved(self):
        out = os.path.join(self.d, "dist")
        self.assertEqual(build_public.build(self.d, out), ["c2"])
        self.assertEqual(sorted(os.listdir(os.path.join(out, "data", "contributions"))), ["c2.json", "index.json"])
    def test_leak_fails(self):
        open(os.path.join(self.d, "reader", "index.html"), "w").write("see Body c1 qq")
        with contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(build_public.main(["--out", os.path.join(self.d, "dist")], root=self.d), 1)
        self.assertFalse(os.path.exists(os.path.join(self.d, "dist")))

    def test_index_matches_reader_parsing(self):
        out = os.path.join(self.d, "dist"); build_public.build(self.d, out)
        cdir = os.path.join(out, "data", "contributions")
        idx = json.load(open(os.path.join(cdir, "index.json")))
        self.assertEqual(idx, ["c2.json"])
        # run the reader's real contribNames() (extracted from reader.js) when node is available
        node = shutil.which("node")
        if node:
            src = open(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "reader", "reader.js"), encoding="utf-8").read()
            a = src.index("function contribNames"); b = src.index("async function loadContribs")
            code = src[a:b] + "console.log(JSON.stringify(contribNames(" + json.dumps(idx) + ")))"
            res = subprocess.run([node, "-e", code], capture_output=True, text=True, check=True)
            names = json.loads(res.stdout)
            self.assertEqual(names, idx)
            for n in names: self.assertTrue(os.path.isfile(os.path.join(cdir, n)), n)
    def test_decision_regenerates_dev_index(self):
        review_queue.write_index(self.d)
        review_queue.decide(self.d, "c1", "approved", "Rev", today="2026-01-01")
        idx = json.load(open(os.path.join(self.d, "data", "contributions", "index.json")))
        self.assertEqual(idx, ["c1.json", "c2.json", "c3.json"])
        self.assertEqual(sorted(c["id"] for _, c in review_queue.load_all(self.d)), ["c1", "c2", "c3"])

class PrivacyTests(Base):
    def run_check(self):
        with contextlib.redirect_stdout(io.StringIO()): return privacy_check.main([], root=self.d)
    def test_clean_and_svg_ok(self):
        open(os.path.join(self.d, "a.svg"), "w").write("<svg/>"); open(os.path.join(self.d, "a.txt"), "w").write("hi a" + "@example.com")
        self.assertEqual(self.run_check(), 0)
    def test_flags(self):
        for name, body in (("x.pdf", "%PDF"), ("y.png", "x"), ("z.ged", "0 HEAD"), ("e.txt", "me" + "@" + "real-mail.com"), ("p.txt", "call 555" + "-123-" + "4567 now")):
            with self.subTest(name):
                p = os.path.join(self.d, name); open(p, "w").write(body)
                self.assertEqual(self.run_check(), 1); os.remove(p)
    def test_gitignored_skipped(self):
        subprocess.run(["git", "init", "-q"], cwd=self.d, check=True)
        open(os.path.join(self.d, ".gitignore"), "w").write("*.pdf\n"); open(os.path.join(self.d, "x.pdf"), "w").write("%PDF")
        self.assertEqual(self.run_check(), 0)
    def test_repo_is_clean(self):
        with contextlib.redirect_stdout(io.StringIO()): self.assertEqual(privacy_check.main([], root=ROOT), 0)

if __name__ == "__main__":
    unittest.main()
