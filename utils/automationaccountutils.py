from azure.mgmt.automation.models import (
    AutomationAccountCreateOrUpdateParameters,
    RunbookCreateOrUpdateParameters,
)
import logging, os


class Automationaccountutils:

    @staticmethod
    def aacreate_or_update_parameters(accountname, location, tags: dict[str, str], sku):
        try:
            parameters = AutomationAccountCreateOrUpdateParameters(
                name=accountname, location=location, tags=tags, sku=sku
            )
            return parameters
        except Exception as e:
            logging.warning(f"Error with util {e}")
            return None

    @staticmethod
    def aacreate_or_update_runbook_parameter(
        name,
        location,
        tags,
        log_verbose,
        log_progress,
        runbook_type,
        publish_content_link,
        description,
        log_activity_trace,
    ):
        try:
            parameters = RunbookCreateOrUpdateParameters(
                runbook_type=runbook_type,
                name=name,
                location=location,
                tags=tags,
                log_verbose=log_verbose,
                log_progress=log_progress,
                publish_content_link=publish_content_link,
                description=description,
                log_activity_trace=log_activity_trace,
            )
            return parameters
        except Exception as e:
            logging.info(f"Error fetching parameter for runbooks {e}")
            return None
