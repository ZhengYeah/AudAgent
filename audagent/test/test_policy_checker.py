import time

from audagent.auditor.models import PolicyTarget, PolicyChecking
from audagent.auditor.checker import RuntimeChecker


def make_checker_with_policy(data_type: str, *, prohibited_col=False, prohibited_dis=False,
                             disclosure=None, retention=None):
    tgt = PolicyTarget(
        data_type=data_type,
        prohibited_col=prohibited_col,
        prohibited_dis=prohibited_dis,
        collection="direct",
        processing="irrelevant",
        disclosure=disclosure,
        retention=retention,
    )
    return RuntimeChecker({data_type: tgt})

def test_add_data_name_updates_existing_retention():
    checker = make_checker_with_policy("email", retention=60.0)
    old_ret = 1.0
    checker._data_names["user_email"] = PolicyChecking(
        data_name="user_email",
        data_type="email",
        collection="direct",
        processing="irrelevant",
        disclosure=None,
        retention=old_ret,
    )
    checker.add_data_name("user_email", "email")
    assert "user_email" in checker._data_names
    assert checker._data_names["user_email"].retention > old_ret

def test_check_collection_con_missing_type_reports_issue():
    checker = RuntimeChecker({})
    # create an entry with a data_type that is not present in target policies
    checker._data_names["foo"] = PolicyChecking(
        data_name="foo",
        data_type="unknown_type",
        collection="direct",
        processing="irrelevant",
        disclosure=None,
        retention=time.time(),
    )
    checker.check_collection_con("foo")
    assert any("Data type foo not found in target policies." in i for i in checker.issues)

def test_update_processing_con_missing_name_reports_issue():
    checker = make_checker_with_policy("phone", retention=10.0)
    checker.update_processing_con("missing_name")
    assert any("Data name missing_name not found in runtime checker for processing update." in i
               for i in checker.issues)

def test_update_processing_con_retention_exceeded_reports_issue():
    checker = make_checker_with_policy("ssn", retention=0.5)
    # set an old retention timestamp to force exceed
    checker._data_names["my_ssn"] = PolicyChecking(
        data_name="my_ssn",
        data_type="ssn",
        collection="direct",
        processing="irrelevant",
        disclosure=None,
        retention=time.time() - 10.0,
    )
    checker.update_processing_con("my_ssn")
    assert any("Data name my_ssn retention time exceeded target policy limit." in i
               for i in checker.issues)

def test_update_disclosure_prohibited_reports_issue_and_returns():
    checker = make_checker_with_policy("location", prohibited_dis=True, disclosure="partner")
    checker._data_names["loc"] = PolicyChecking(
        data_name="loc",
        data_type="location",
        collection="direct",
        processing="irrelevant",
        disclosure=None,
        retention=time.time(),
    )
    checker.update_disclosure("loc", "partner")
    assert any("Data name loc disclosure is prohibited in the target policy." in i
               for i in checker.issues)

def test_update_disclosure_mismatch_reports_issue_when_not_service_provider():
    checker = make_checker_with_policy("profile", disclosure="partner", prohibited_dis=False, retention=60.0)
    checker._data_names["profile_1"] = PolicyChecking(
        data_name="profile_1",
        data_type="profile",
        collection="direct",
        processing="irrelevant",
        disclosure=None,
        retention=time.time() - 100.0,  # also triggers retention exceeded
    )
    checker.update_disclosure("profile_1", "other")
    assert any("Data name profile_1 disclosure other is not allowed in the target policy." in i
               for i in checker.issues)
    # retention should also have been checked and reported
    assert any("Data name profile_1 retention time exceeded target policy limit." in i
               for i in checker.issues)
