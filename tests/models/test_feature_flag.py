"""Tests for FeatureFlag model."""

from src.models.feature_flag import FeatureFlag


class TestFeatureFlag:
    """Test FeatureFlag model."""

    def test_create_feature_flag(self, db_session):
        """建立新的 feature flag"""
        flag = FeatureFlag(key="groups_enabled", value="true")
        db_session.add(flag)
        db_session.commit()

        assert flag.key == "groups_enabled"
        assert flag.value == "true"
        assert flag.updated_at is not None

    def test_feature_flag_repr(self):
        """FeatureFlag __repr__ 格式正確"""
        flag = FeatureFlag(key="groups_enabled", value="true")
        assert repr(flag) == "<FeatureFlag(key=groups_enabled, value=true)>"
