from datetime import tzinfo, timedelta, datetime
import sys, os
import_path = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, import_path + '/../')
import snapshots


def test_tag_found():
    """The correct value is returned for the given existing key"""
    tags = [{'Key': 'Test', 'Value': 'test_value'}]
    assert snapshots.tag('Test', tags) == 'test_value'

def test_tag_not_found():
    """An empty string is returned for the given missing key"""
    tags = [{'Key': 'X', 'Value': 'x'}]
    assert snapshots.tag('Test', tags) == ''

def test_older_than_true():
    """The given date is really older than the given number of days"""
    old = datetime.now(snapshots.UTC()) - timedelta(days=2)
    assert snapshots.older_than(old, 1)

def test_older_than_false():
    """A date that's less than the given number of days is not
    declared older"""
    old = datetime.now(snapshots.UTC()) - timedelta(days=1)
    assert not snapshots.older_than(old, 2)

def test_has_true_tag_true():
    """Truth is declared for a record that has the tag's value == 'true'"""
    r = {'Tags': [{'Key': 'Test', 'Value': 'true'}]}
    assert snapshots.has_true_tag('Test', r)

def test_has_true_tag_false():
    """False is returned for a record that has no given tag or has the tag's
    value not == 'true'"""
    recs = [{'Tags': [{'Key': 'X', 'Value': 'true'},
                      {'Key': 'Test', 'Value': 'false'}]},
            {'Tags': []},
            {}]
    for r in recs:
        assert not snapshots.has_true_tag('Test', r)
