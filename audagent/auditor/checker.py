"""
Runtime policy checker to monitor data handling compliance.
Used in `llm/*_models.py` during graph extraction. The violation info will be attached to edges.
"""
import time
import logging

from pydantic import ValidationError

from audagent.auditor.models import PolicyChecking, PolicyTarget

logger = logging.getLogger(__name__)

class RuntimeChecker:
    def __init__(self, policies) -> None:
        """
        data_type_name as key; PolicyChecking data model as val (where its name mapped back to data_type_name)
        """
        self._data_names: dict[str, PolicyChecking] = {}
        self._target_policies: dict[str, PolicyTarget] = {}
        self._load_target_policies(policies)
        self.issues: list[str] = []

    def _load_target_policies(self, policies: list[PolicyTarget]) -> None:
        try:
            for policy in policies:
                self._target_policies[policy.data_type] = policy
        except ValidationError as e:
            logger.error(f"Error loading target policies into runtime checker: {e}")

    def add_data_name(self, data_name: str, data_type: str) -> None:
        if data_name in self._data_names:
            dt = self._data_names[data_name]
            logger.debug(f"Data name {data_name} already exists in runtime checker, updated retention time.")
            # Update retention time to current time (collected timestamp)
            dt.retention = time.time()
            return
        self.check_collection_allowed(data_type) # Not found violation
        # If it is found and not prohibited, add to runtime checker
        new_data_name = PolicyChecking(
            data_name=data_name,
            data_type=data_type,
            collection="direct",
            processing="irrelevant",
            disclosure=None,
            retention=time.time())
        self._data_names[data_name] = new_data_name
        logger.debug(f"Added data name {data_name} to runtime checker.")

    def check_collection_allowed(self, data_type: str) -> None:
        # Check whether this data type is allowed to be collected
        # For each new data type found in all stages (in addition to the collection), we should check whether it's allowed to be collected
        if data_type not in self._target_policies:
            self.issues.append(f"Data type {data_type} not found in target policies.")
        elif self._target_policies[data_type].prohibited_col: # Prohibited violation
            self.issues.append(f"Data type {data_type} collection is prohibited in the target policy.")
        else:
            logger.debug(f"Data type {data_type} collection is allowed in the target policy.")

    def update_processing_con(self, data_name: str) -> None:
        try:
            self._data_names[data_name].processing = "relevant"
        except KeyError:
            logger.error(f"Data name {data_name} not found in runtime checker for processing update.")
            return
        # Check retention time compliance with target policy
        data_type_for_check = self._data_names[data_name].data_type
        retention_con = self._target_policies[data_type_for_check].retention
        if retention_con and time.time() - self._data_names[data_name].retention > retention_con:
            self.issues.append(f"Data name {data_name} retention time exceeded target policy limit.")

    def update_disclosure(self, data_name: str, disclosure_name: str) -> None:
        try:
            self._data_names[data_name].disclosure = disclosure_name
        except KeyError:
            logger.error(f"Data name {data_name} not found in runtime checker for disclosure update.")
            return
        # Check disclosure compliance with target policy
        data_type_for_check = self._data_names[data_name].data_type
        prohibited_dis = self._target_policies[data_type_for_check].prohibited_dis
        if prohibited_dis:
            self.issues.append(f"Data name {data_name} disclosure is prohibited in the target policy.")
            return
        target_disclosure = self._target_policies[data_type_for_check].disclosure
        if disclosure_name != target_disclosure:
            # Raise issue if disclosure is not allowed; but in fact "service provider" covers all disclosures
            if target_disclosure != "service provider":
                self.issues.append(f"Data name {data_name} disclosure {disclosure_name} is not allowed in the target policy.")
        # Check retention time compliance with target policy
        retention_con = self._target_policies[data_type_for_check].retention
        if retention_con and time.time() - self._data_names[data_name].retention > retention_con:
            self.issues.append(f"Data name {data_name} retention time exceeded target policy limit.")
