from azure.mgmt.automation.models import (
    AutomationAccountCreateOrUpdateParameters,
    RunbookCreateOrUpdateParameters,
    VariableCreateOrUpdateParameters,
    ScheduleCreateOrUpdateParameters,
    JobScheduleCreateParameters,
    ScheduleAssociationProperty,
    RunbookAssociationProperty,
)
import logging, os, json


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

    @staticmethod
    def aaupdate_runbook_variables(
        variable_name, variable_value, description, is_encrypted
    ):
        try:
            parameters = VariableCreateOrUpdateParameters(
                name=variable_name,
                value=variable_value,
                description=description,
                is_encrypted=is_encrypted,
            )
            logging.info(f"Fetching variable parameters {parameters}")
            return parameters
        except Exception as e:
            logging.warning(f"Error with updating runbook variables utils {e}")
            return None

    @staticmethod
    def aacreate_or_update_schedule_parameter(
        schedule_name,
        start_time,
        frequency,
        description,
        expiry_time,
        interval,
        time_zone,
        advanced_schedule,
    ):
        try:
            parameters = ScheduleCreateOrUpdateParameters(
                name=schedule_name,
                start_time=start_time,
                expiry_time=expiry_time,
                frequency=frequency,
                description=description,
                advanced_schedule=advanced_schedule,
                time_zone=time_zone,
                interval=interval,
            )
            return parameters
        except Exception as e:
            logging.info(f"Error assigning parameter for schedule {e}")
            return None

    @staticmethod
    def aalink_runbook_to_aa(schedule_name, runbook_name, run_on, addparameters):
        try:
            parameters = JobScheduleCreateParameters(
                schedule=ScheduleAssociationProperty(name=schedule_name),
                runbook=RunbookAssociationProperty(name=runbook_name),
                run_on=run_on,
                parameters=addparameters,
            )
            return parameters
        except Exception as e:
            logging.warning(f"Error creating parameters for Automation account {e}")
            return None
