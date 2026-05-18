import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), 'scripts'))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__))))

from scripts.ingest_corpus import normalize_text, split_oversized_paragraph, clean_html_text


def test_remove_extra_spaces():
    assert normalize_text("Hello   World") == "Hello World"


def test_remove_control_chars():
    assert normalize_text("Hello\x00World") == "HelloWorld"


def test_normalize_quotes():
    result = normalize_text('\u201cHello\u201d \u2018World\u2019')
    assert result == '"Hello" \'World\'', repr(result)


def test_strip_whitespace():
    assert normalize_text("  Hello World  ") == "Hello World"


def test_empty_text():
    assert normalize_text("") == ""
    assert normalize_text(None) == ""


def test_ligature_expansion():
    text = '\ufb01'  # fi ligature
    result = normalize_text(text)
    assert 'fi' in result, repr(result)


def test_html_tag_removal():
    result = normalize_text("Hello <b>World</b>")
    assert "<b>" not in result
    assert "World" in result


def test_split_oversized_paragraph():
    text = "Sentence one. Sentence two. Sentence three. " * 100
    fragments = split_oversized_paragraph(text, max_tokens=200)
    assert len(fragments) >= 2


def test_split_small_paragraph():
    text = "Short text."
    fragments = split_oversized_paragraph(text, max_tokens=1000)
    assert fragments == [text]


def test_split_empty_text():
    assert split_oversized_paragraph("", 100) == [""]
