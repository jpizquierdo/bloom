"""Pure OIDC rules: nested claims, group → role mapping, username derivation."""

from bloom.domain.oidc import claim_at, groups_from, resolve_role, username_from_claims, with_suffix


def test_claim_at_reads_nested_paths():
    claims = {"realm_access": {"roles": ["bloom-admin"]}, "groups": ["a"]}
    assert claim_at(claims, "realm_access.roles") == ["bloom-admin"]
    assert claim_at(claims, "groups") == ["a"]
    # Missing segments, or walking into a non-dict, give None rather than raising.
    assert claim_at(claims, "realm_access.missing") is None
    assert claim_at(claims, "groups.nested") is None


def test_groups_from_accepts_list_or_single_string():
    assert groups_from({"groups": ["a", "b"]}, "groups") == {"a", "b"}
    assert groups_from({"groups": "a"}, "groups") == {"a"}
    assert groups_from({}, "groups") == set()


def test_resolve_role_without_any_group_settings_keeps_stored_role():
    assert resolve_role(set(), set(), set(), "user") == "user"
    assert resolve_role(set(), set(), set(), "admin") == "admin"


def test_resolve_role_syncs_with_admin_groups():
    admins = {"bloom-admin"}
    # Membership promotes, absence demotes: the IdP is authoritative.
    assert resolve_role({"bloom-admin"}, admins, set(), "user") == "admin"
    assert resolve_role({"other"}, admins, set(), "admin") == "user"


def test_resolve_role_allowed_groups_gate():
    allowed = {"bloom-users"}
    assert resolve_role({"bloom-users"}, set(), allowed, "user") == "user"
    assert resolve_role({"other"}, set(), allowed, "user") is None
    # Admins pass the gate whether the role comes from groups or from the DB.
    assert resolve_role({"bloom-admin"}, {"bloom-admin"}, allowed, "user") == "admin"
    assert resolve_role(set(), set(), allowed, "admin") == "admin"


def test_username_from_claims():
    assert username_from_claims("Jane.Doe", "x@example.com") == "jane.doe"
    # Invalid characters collapse to "-"; too-short handles fall back to the email local part.
    assert username_from_claims("Jane Doe!", None) == "jane-doe"
    assert username_from_claims("jd", "jane.doe@example.com") == "jane.doe"
    assert username_from_claims(None, None) == "user"
    assert len(username_from_claims("x" * 50, None)) == 32


def test_with_suffix_stays_within_limit():
    assert with_suffix("jane", 2) == "jane-2"
    assert with_suffix("x" * 32, 12) == "x" * 29 + "-12"
