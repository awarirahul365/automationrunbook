from azure.mgmt.automation.aio import AutomationClient
from azpoe.services import AuthService
from utils.automationaccountutils import Automationaccountutils
import logging, os, json, random, uuid


class Automationaccount:

    @staticmethod
    async def create_automation_account(rg_afslist: list[dict]):

        try:
            logging.info(f"Processing creation of account {rg_afslist}")
            credential, cloud = AuthService.get_credential(rg_afslist["tenantName"])
            async with credential:
                for account in rg_afslist["data"]:
                    try:
                        automation_client = AutomationClient(
                            credential=credential,
                            subscription_id=account["subscription_id"],
                        )
                        async with automation_client:
                            creation_aa_result = None
                            creation_aa_result = await automation_client.automation_account.create_or_update(
                                resource_group_name=account["rg_name"],
                                automation_account_name=account[
                                    "automationaccountname"
                                ],
                                parameters=Automationaccountutils.aacreate_or_update_parameters(
                                    accountname=account["automationaccountname"],
                                    location=account["location"],
                                    tags={
                                        "accounttype": os.getenv(
                                            "automationaccounttags"
                                        )
                                    },
                                    sku={"name": os.getenv("automationaccountsku")},
                                ),
                            )
                            account["automationaccountid"] = (
                                creation_aa_result.id if creation_aa_result else None
                            )
                            logging.info(
                                f"Automation Account creation result {creation_aa_result}"
                            )
                    except Exception as e:
                        logging.warning(
                            f"Error creating account for automation {account['subscription_id']} {e}"
                        )

        except Exception as e:
            logging.warning(f"Error creating the automation account {e}")

    @staticmethod
    async def create_runbook_to_automation_account(
        rg_automationaccount_list: list[dict], runbook_with_contentlink
    ):
        try:
            logging.info(f"Processing Runbook creation for {rg_automationaccount_list}")
            logging.info(f"Processing Runbook creation for {runbook_with_contentlink}")
            credential, cloud = AuthService.get_credential(
                rg_automationaccount_list["tenantName"]
            )
            async with credential:
                for account in rg_automationaccount_list["data"]:
                    try:
                        automation_client = AutomationClient(
                            credential=credential,
                            subscription_id=account["subscription_id"],
                        )
                        async with automation_client:
                            for runbooks in runbook_with_contentlink:
                                runbookname = runbooks["runbookname"]
                                runbookcontentlink = runbooks["contentlink"]
                                runbook_creation = None
                                runbook_creation = await automation_client.runbook.create_or_update(
                                    resource_group_name=account["rg_name"],
                                    automation_account_name=account[
                                        "automationaccountname"
                                    ],
                                    runbook_name=runbookname,
                                    parameters=Automationaccountutils.aacreate_or_update_runbook_parameter(
                                        name=runbookname,
                                        location=account["location"],
                                        tags={"servicenow_instance": "itsm.sap.com"},
                                        log_verbose="true",
                                        log_progress="true",
                                        runbook_type="Python3",
                                        publish_content_link=runbookcontentlink,
                                        description="publishing runbook",
                                        log_activity_trace=0,
                                    ),
                                )
                                account["published_runbooks"] = {
                                    "runbookname": runbookname,
                                    "runbookid": (
                                        runbook_creation.id
                                        if runbook_creation
                                        else None
                                    ),
                                }
                                if runbook_creation is not None:
                                    logging.info(
                                        f"Runbook creation succeeded {runbook_creation}"
                                    )
                    except Exception as e:
                        logging.warning(f"Failed to publish runbook for aa {e}")

        except Exception as e:
            logging.warning(f"Error while creating or updating runbook in aa {e} ")

    @staticmethod
    async def update_variables_to_automation_account(
        rg_aa_account_list, variables_names_list
    ):
        logging.info(f"Adding variables to automation account {rg_aa_account_list}")
        try:
            credential, cloud = AuthService.get_credential(
                rg_aa_account_list["tenantName"]
            )
            async with credential:
                for account in rg_aa_account_list["data"]:
                    try:
                        automation_client = AutomationClient(
                            credential=credential,
                            subscription_id=account["subscription_id"],
                        )
                        logging.info(f"Created Automation client {automation_client}")
                        async with automation_client:
                            variable_addition_list = []
                            for var in variables_names_list:
                                logging.info(f"Adding variable {var}")
                                variable_addition_result = None
                                if var == "EXCLUDE_AFS":
                                    variable_addition_result = await automation_client.variable.create_or_update(
                                        resource_group_name=account["rg_name"],
                                        automation_account_name=account[
                                            "automationaccountname"
                                        ],
                                        variable_name=var,
                                        parameters=Automationaccountutils.aaupdate_runbook_variables(
                                            variable_name=var,
                                            variable_value=json.dumps(
                                                "vol-install-xsc"
                                            ),
                                            description="runbook_variable",
                                            is_encrypted=False,
                                        ),
                                    )
                                    variable_addition_list.append(
                                        {
                                            f"{variable_addition_result.name}": {
                                                variable_addition_result.value
                                            }
                                        }
                                    )
                                    logging.info(
                                        f"Variable added {var} {variable_addition_result}"
                                    )
                                elif var == "OBJECT_STORAGE":
                                    variable_addition_result = await automation_client.variable.create_or_update(
                                        resource_group_name=account["rg_name"],
                                        automation_account_name=account[
                                            "automationaccountname"
                                        ],
                                        variable_name=var,
                                        parameters=Automationaccountutils.aaupdate_runbook_variables(
                                            variable_name=var,
                                            variable_value=json.dumps(
                                                random.choice(account["resource_name"])
                                            ),
                                            description="runbook_variable",
                                            is_encrypted=False,
                                        ),
                                    )
                                    variable_addition_list.append(
                                        {
                                            f"{variable_addition_result.name}": {
                                                variable_addition_result.value
                                            }
                                        }
                                    )
                                    logging.info(
                                        f"Variable added {var} {variable_addition_result}"
                                    )
                                elif var == "RESOURCE_GROUP":
                                    variable_addition_result = await automation_client.variable.create_or_update(
                                        resource_group_name=account["rg_name"],
                                        automation_account_name=account[
                                            "automationaccountname"
                                        ],
                                        variable_name=var,
                                        parameters=Automationaccountutils.aaupdate_runbook_variables(
                                            variable_name=var,
                                            variable_value=json.dumps(
                                                account["rg_name"]
                                            ),
                                            description="runbook_variable",
                                            is_encrypted=False,
                                        ),
                                    )
                                    variable_addition_list.append(
                                        {
                                            f"{variable_addition_result.name}": {
                                                variable_addition_result.value
                                            }
                                        }
                                    )
                                    logging.info(
                                        f"Variable added {var} {variable_addition_result}"
                                    )
                                elif var == "RetentionDays":
                                    variable_addition_result = await automation_client.variable.create_or_update(
                                        resource_group_name=account["rg_name"],
                                        automation_account_name=account[
                                            "automationaccountname"
                                        ],
                                        variable_name=var,
                                        parameters=Automationaccountutils.aaupdate_runbook_variables(
                                            variable_name=var,
                                            variable_value=json.dumps(
                                                os.getenv("RetentionDays")
                                            ),
                                            description="runbook_variable",
                                            is_encrypted=False,
                                        ),
                                    )
                                    variable_addition_list.append(
                                        {
                                            f"{variable_addition_result.name}": {
                                                variable_addition_result.value
                                            }
                                        }
                                    )
                                    logging.info(
                                        f"Variable added {var} {variable_addition_result}"
                                    )
                                elif var == "SUBSCRIPTION_ID":
                                    variable_addition_result = await automation_client.variable.create_or_update(
                                        resource_group_name=account["rg_name"],
                                        automation_account_name=account[
                                            "automationaccountname"
                                        ],
                                        variable_name=var,
                                        parameters=Automationaccountutils.aaupdate_runbook_variables(
                                            variable_name=var,
                                            variable_value=json.dumps(
                                                account["subscription_id"]
                                            ),
                                            description="runbook_variable",
                                            is_encrypted=False,
                                        ),
                                    )
                                    variable_addition_list.append(
                                        {
                                            f"{variable_addition_result.name}": {
                                                variable_addition_result.value
                                            }
                                        }
                                    )
                                    logging.info(
                                        f"Variable added {var} {variable_addition_result}"
                                    )
                            account["variableadditionlist"] = variable_addition_list
                    except Exception as e:
                        logging.warning(
                            f"Error with adding of variables for {account} {e}"
                        )
                        logging.error(f"Error with adding variables {e}", exc_info=True)
                        raise
        except Exception as e:
            logging.warning(f"Error updating variables to automation account {e}")

    @staticmethod
    async def create_automation_account_schedule(
        automationaccountlist, automation_schedule_list
    ):
        try:
            logging.info(f"Automation account list {automationaccountlist}")
            credential, cloud = AuthService.get_credential(
                automationaccountlist["tenantName"]
            )
            async with credential:
                for account in automationaccountlist["data"]:
                    try:
                        automation_client = AutomationClient(
                            credential=credential,
                            subscription_id=account["subscription_id"],
                        )
                        async with automation_client:
                            schedule_id_list = []
                            for sch in automation_schedule_list:
                                try:
                                    create_schedule = None
                                    create_schedule = await automation_client.schedule.create_or_update(
                                        resource_group_name=account["rg_name"],
                                        automation_account_name=account[
                                            "automationaccountname"
                                        ],
                                        schedule_name=os.getenv("schedule_name"),
                                        parameters=Automationaccountutils.aacreate_or_update_schedule_parameter(
                                            schedule_name=sch["name"],
                                            start_time=sch["start_time"],
                                            expiry_time=sch["expiry_time"],
                                            frequency=sch["frequency"],
                                            description=sch["description"],
                                            interval=sch["interval"],
                                            time_zone=sch["time_zone"],
                                            advanced_schedule=sch["advanced_schedule"],
                                        ),
                                    )
                                    schedule_id_list.append(
                                        {
                                            "schedule_name": create_schedule.name,
                                            "schedule_id": create_schedule.id,
                                        }
                                    )
                                    if create_schedule is not None:
                                        logging.info(
                                            f"Schedule created with {create_schedule}"
                                        )

                                except Exception as e:
                                    logging.warning(
                                        f"Error creating schedule {sch} {e}"
                                    )
                            account["schedule_id"] = schedule_id_list
                    except Exception as e:
                        logging.warning(f"Error with automation client {account}")

        except Exception as e:
            logging.warning(f"Error creating a Automation account schedule {e}")

    @staticmethod
    async def link_runbook_to_schedule(
        automationaccountlist, link_runbook_relation_list
    ):
        try:
            logging.info(
                f"Automation account currently being used {automationaccountlist}"
            )
            credential, cloud = AuthService.get_credential(
                automationaccountlist["tenantName"]
            )
            async with credential:
                for account in automationaccountlist["data"]:
                    try:
                        automation_client = AutomationClient(
                            credential=credential,
                            subscription_id=account["subscription_id"],
                        )
                        async with automation_client:
                            for runbook in link_runbook_relation_list:
                                logging.info(
                                    f"Processing Current runbook now is {runbook}"
                                )
                                runbookname = runbook["runbookname"]
                                schedulename = runbook["schedulename"]
                                try:
                                    link_runbook_result = await automation_client.job_schedule.create(
                                        resource_group_name=account["rg_name"],
                                        automation_account_name=account[
                                            "automationaccountname"
                                        ],
                                        job_schedule_id=str(uuid.uuid4()),
                                        parameters=Automationaccountutils.aalink_runbook_to_aa(
                                            schedule_name=schedulename,
                                            runbook_name=runbookname,
                                            run_on=None,
                                            addparameters=None,
                                        ),
                                    )
                                    if link_runbook_result is not None:
                                        logging.info(
                                            f"Runbook linked to schedule {link_runbook_result}"
                                        )
                                except Exception as e:
                                    logging.warning(f"Error Linking runbook {e}")

                    except Exception as e:
                        logging.warning(f"Error Linking schedule for runbook {e}")

        except Exception as e:
            logging.warning(f"Error linking the storage account for {e}")
