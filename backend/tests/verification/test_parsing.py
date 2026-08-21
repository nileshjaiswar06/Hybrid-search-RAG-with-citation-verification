from app.verification.parsing import extract_cited_claims


def test_extract_cited_claims():
    claims = extract_cited_claims(
        "Passwords must be strong. [1] "
        "Confidential data must be protected. [2][3]"
    )

    assert len(claims) == 2
    assert claims[0].text == "Passwords must be strong."
    assert claims[0].citation_labels == (1,)
    assert claims[1].text == "Confidential data must be protected."
    assert claims[1].citation_labels == (2, 3)