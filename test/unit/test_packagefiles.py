import pathlib as pt

def test_mainscript():
    assert pt.Path('./keyword_count_polmaplib.py').exists()

def test_polmap():
    assert pt.Path('./polmap/polmap.py').exists()
    assert pt.Path('./polmap/__init__.py').exists()

def test_postprocess():
    assert pt.Path('./postprocess/postprocess.py').exists()
    assert pt.Path('./postprocess/goal_target_list_std.xlsx').exists()
    assert pt.Path('./postprocess/__init__.py').exists()

def test_keywords():
    assert pt.Path('./keywords/keywords.xlsx').exists()
