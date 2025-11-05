import time
from typing import Any, Type, Optional
import logging

from pydantic import BaseModel

from audagent.auditing.models import PolicyChecking

logger = logging.getLogger(__name__)

class RuntimeChecker:
    def __init__(self) -> None:
        self.data_types: list[PolicyChecking] = []

    def add_data_type(self, data_type: str) -> None:
        data_type = PolicyChecking(data_type=data_type, collection=None, processing=None, disclosure=None, retention=time.time())
        self.data_types.append(data_type)
        logger.debug(f"Added data type {data_type.data_type} to runtime checker.")

    def update_collection_con(self, data_type: str) -> None:
        for dt in self.data_types:
            if dt.data_type == data_type:
                dt.collection = "direct"

    def update_processing_con(self, data_type: str) -> None:
        # Update processing constraint to "relevant" when this data type used in response or tool call
        for dt in self.data_types:
            if dt.data_type == data_type:
                dt.processing = "relevant"
                logger.debug(f"Updated processing constraint for data type {data_type} to 'relevant'.")

    def update_disclosure(self, data_type: str, disclosure: str) -> None:
        for dt in self.data_types:
            if dt.data_type == data_type:
                dt.disclosure = disclosure
                logger.debug(f"Updated disclosure for data type {data_type} to '{disclosure}'.")

    def update_retention(self, data_type: str) -> None:
        for dt in self.data_types:
            if dt.data_type == data_type:
                dt.retention = time.time() - dt.retention


    def instant_checker(self, target_policy: Type[BaseModel], data_type:str) -> bool:
        for dt in self.data_types:
            if dt.data_type == data_type:
                target = target_policy.model_validate({'data_type': dt.data_type,
                                                      'collection': dt.collection,
                                                      'processing': dt.processing,
                                                      'disclosure': dt.disclosure,
                                                      'retention': dt.retention})
                if dt == target:
                    logger.debug(f"Data type {data_type} complies with the target policy.")
                    return True
                else:
                    logger.warning(f"Data type {data_type} does not comply with the target policy.")
                    return False
        logger.warning(f"Data type {data_type} not found in runtime checker.")
        return False

