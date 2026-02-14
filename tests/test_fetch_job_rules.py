"""Unit tests for crawler.fetch_job_rules."""
from crawler.fetch_job_rules import is_under_100, is_target_software_role


class TestIsUnder100:
    def test_none_returns_true(self):
        assert is_under_100(None) is True

    def test_zero_returns_true(self):
        assert is_under_100(0) is True

    def test_99_returns_true(self):
        assert is_under_100(99) is True

    def test_100_returns_false(self):
        assert is_under_100(100) is False

    def test_above_100_returns_false(self):
        assert is_under_100(150) is False


class TestIsTargetSoftwareRole:
    def test_software_engineer_true(self):
        assert is_target_software_role("Software Engineer") is True

    def test_backend_developer_true(self):
        assert is_target_software_role("Backend Developer") is True

    def test_sde_true(self):
        assert is_target_software_role("SDE 2") is True

    def test_fullstack_true(self):
        assert is_target_software_role("Full Stack Engineer") is True

    def test_staff_excluded(self):
        assert is_target_software_role("Staff Software Engineer") is False

    def test_principal_excluded(self):
        assert is_target_software_role("Principal Engineer") is False

    def test_lead_excluded(self):
        assert is_target_software_role("Lead Developer") is False

    def test_manager_excluded(self):
        assert is_target_software_role("Engineering Manager") is False

    def test_director_excluded(self):
        assert is_target_software_role("Director of Engineering") is False

    def test_non_software_false(self):
        assert is_target_software_role("Product Manager") is False

    def test_empty_false(self):
        assert is_target_software_role("") is False
