from azure.mgmt.automation.aio.operations import RunbookOperations
from azure.mgmt.automation.operations import AutomationAccountOperations
from azure.mgmt.automation.aio import AutomationClient
from azpoe.services import AuthService
from utils.automationaccountutils import Automationaccountutils
import logging, os, json


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
                            if creation_aa_result is not None:
                                account["automationaccountid"] = creation_aa_result.id

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
                                if runbook_creation is not None:
                                    logging.info(
                                        f"Runbook creation succeeded {runbook_creation}"
                                    )
                    except Exception as e:
                        logging.warning(f"Failed to publish runbook for aa {e}")

        except Exception as e:
            logging.warning(f"Error while creating or updating runbook in aa {e} ")
