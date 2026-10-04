from listkit_page import paginate


def test_empty_list():
    assert paginate([], 1, 3) == []


def test_page_past_the_end_is_empty():
    assert paginate(list(range(4)), 9, 3) == []
