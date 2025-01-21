import azure.functions as func
import logging, os, requests
from azpoe.services import AuthService
from azure.mgmt.resource import ResourceManagementClient
from azure.identity import ClientSecretCredential
from azure.core.credentials import TokenCredential
import hashlib
from services.automation_account_service import Automationaccount
from services.blob_service import BlobService
from azure.storage.blob.aio import ContainerClient
import pandas as pd

app = func.FunctionApp(http_auth_level=func.AuthLevel.FUNCTION)
logger = logging.getLogger("azure")
logger.setLevel(logging.WARNING)


def credential_tokenformat(credential_key) -> TokenCredential:
    try:
        spn = os.getenv(credential_key, "").strip()
        if not spn:
            raise KeyError(f"'{spn}' key not found")
        spn_values = spn.split(",")
        cred_dict = {}
        for v in spn_values:
            pair = v.split(":")
            cred_dict[pair[0]] = pair[1]
        credential = ClientSecretCredential(
            tenant_id=cred_dict.get("tenantId"),
            client_id=cred_dict.get("clientId"),
            client_secret=cred_dict.get("clientSecret"),
        )
        return credential
    except Exception as e:
        logging.warning(f"Failed to fetch token credential {e}")
        return None


async def fetch_content_link(runbook_publish_names):
    try:
        content_link_result = []
        for runbook_element in runbook_publish_names:
            blobobj = BlobService(
                storageaccount_endpoint=os.getenv("storageaccountendpoint"),
                conn_str=os.getenv("storage_connection_str"),
            )
            script_content = await blobobj.read_container_file(
                blob_name=runbook_element["blobname"],
                container_name=runbook_element["containername"],
            )
            logging.info(f"Script content is {script_content}")
            content_hash_value = hashlib.sha256(
                script_content.encode("utf-8")
            ).hexdigest()
            content_hash = {"algorithm": "SHA256", "value": content_hash_value}
            container_client = ContainerClient.from_connection_string(
                conn_str=os.getenv("storage_connection_str"),
                container_name=runbook_element["containername"],
            )
            blob_client = container_client.get_blob_client(
                blob=runbook_element["blobname"]
            )
            content_link = {
                "uri": blob_client.url + runbook_element["sastoken"],
                "content_hash": content_hash,
                "version": "v1",
            }
            content_link_result.append(
                {
                    "runbookname": runbook_element["runbookname"],
                    "contentlink": content_link,
                }
            )
        logging.info(f"Generating content link succeeded {content_link_result}")
        return content_link_result
    except Exception as e:
        logging.warning(f"Error fetching content link {e}")


async def __process(new_sub_list):
    try:
        # subscription_list = [["b437f37b-b750-489e-bc55-43044286f6e1", "CredSAPTenant"]]
        tenantName = new_sub_list["tenantName"]
        """subscription_list = [
            {
                "subname": "sap-gcs-az-opseng",
                "subid": "b437f37b-b750-489e-bc55-43044286f6e1",
                "tenantname": "CredSAPTenant",
            }
        ]"""
        resource_group_with_afs = []
        for sub in new_sub_list["data"]:
            credential = credential_tokenformat(credential_key=tenantName)
            logging.info(f"Processing subscription {sub}")
            resource_client = ResourceManagementClient(
                credential=credential,
                subscription_id=sub["subid"],
                base_url="https://management.azure.com",
            )
            rg_list = resource_client.resource_groups.list()
            filter_query = "resourceType eq 'Microsoft.Storage/storageAccounts'"
            for rg in rg_list:
                if rg.name.startswith("HEC"):
                    resources_list = resource_client.resources.list_by_resource_group(
                        resource_group_name=rg.name, filter=filter_query
                    )
                    afs_storage_list = []
                    for resources in resources_list:
                        if resources.kind == "FileStorage":
                            afs_storage_list.append(resources.name)
                    if len(afs_storage_list) > 0:
                        automationaccountname = (
                            "aa"
                            + str(rg.name.split("-")[0].lower())
                            + str(rg.name.split("-")[1].lower())
                            + "backup0001"
                        )
                        resource_group_with_afs.append(
                            {
                                "subscription_id": sub["subid"],
                                "subscription_name": sub["subname"],
                                "rg_name": rg.name,
                                "resource_name": afs_storage_list,
                                "createdTime": sub["createdtime"],
                                "automationaccountname": automationaccountname,
                                "location": rg.location,
                            }
                        )
        result_dict = {"tenantName": tenantName, "data": resource_group_with_afs}
        return result_dict
    except Exception as e:
        logging.warning(f"Error processing for subscription {e}")
        return []


@app.route(route="http_trigger_automation_account")
async def http_trigger_automation_account(req: func.HttpRequest) -> func.HttpResponse:
    logging.info("Python HTTP trigger function processed a request.")
    try:
        new_subscription_list = [
            {
                "tenantName": "CredSAPTenant",
                "data": [
                    {
                        "subname": "sap-gcs-az-opseng",
                        "subid": "b437f37b-b750-489e-bc55-43044286f6e1",
                        "createdtime": "createdtime",
                    }
                ],
            },
            {
                "tenantName": "CredSharedTenant",
                "data": [
                    {
                        "subname": "sap-gcs-azpoe",
                        "subid": "2bb552a1-0927-4732-a475-30f97da346b7",
                        "createdtime": "createdtime",
                    }
                ],
            },
        ]
        rg_with_afs_storage = []
        # fetch resource groups and subscription with AFS account
        for tenant in new_subscription_list:
            ans = await __process(tenant)
            rg_with_afs_storage.append(ans)
        # Create or update automation account
        for acc in rg_with_afs_storage:
            await Automationaccount.create_automation_account(rg_afslist=acc)

        # Onboard variables to the automation accounts
        variables_names_list = [
            "EXCLUDE_AFS",
            "OBJECT_STORAGE",
            "RESOURCE_GROUP",
            "RetentionDays",
            "SUBSCRIPTION_ID",
        ]
        for acc in rg_with_afs_storage:
            await Automationaccount.update_variables_to_automation_account(
                rg_aa_account_list=acc,
                variables_names_list=variables_names_list,
            )
        # Add Runbook to automation account created information
        runbook_publish_names = [
            {
                "runbookname": "afs_backuprunbook",
                "storagename": os.getenv("scriptstoragename"),
                "containername": os.getenv("containername"),
                "blobname": os.getenv("backuprunbookblob"),
                "sastoken": os.getenv("backupsastoken"),
            },
            {
                "runbookname": "afs_deletionrunbook",
                "storagename": os.getenv("scriptstoragename"),
                "containername": os.getenv("containername"),
                "blobname": os.getenv("deletionrunbookblob"),
                "sastoken": os.getenv("deletionsastoken"),
            },
        ]
        # fetch content link for runbook
        runbook_with_contentlink = await fetch_content_link(runbook_publish_names)

        # publish runbook to the automation accounts
        for acc in rg_with_afs_storage:
            await Automationaccount.create_runbook_to_automation_account(
                rg_automationaccount_list=acc,
                runbook_with_contentlink=runbook_with_contentlink,
            )
        # Schedule Automation runbook variables
        automation_schedule_variables = [
            {
                "name": os.getenv("schedule_name"),
                "start_time": "2025-01-23T00:00:00Z",
                "expiry_time": None,
                "frequency": "Day",
                "description": None,
                "interval": "1",
                "time_zone": "UTC",
                "advanced_schedule": None,
            }
        ]
        # Create schedules for automation runbooks
        for acc in rg_with_afs_storage:
            await Automationaccount.create_automation_account_schedule(
                automationaccountlist=acc,
                automation_schedule_list=automation_schedule_variables,
            )
        # Link Runbooks to schedules created
        link_runbook_relation_list = [
            {
                "runbookname": "afs_backuprunbook",
                "schedulename": os.getenv("schedule_name"),
            },
            {
                "runbookname": "afs_deletionrunbook",
                "schedulename": os.getenv("schedule_name"),
            },
        ]
        for acc in rg_with_afs_storage:
            await Automationaccount.link_runbook_to_schedule(
                automationaccountlist=acc,
                link_runbook_relation_list=link_runbook_relation_list,
            )
        # import python packages for automation account
        python_package_list = [
            {
                "packagename": "azure-identity",
                "version": "23.2.0",
                "packageuri": "https://files.pythonhosted.org/packages/05/ed/85b5e33b2d5ee8ae12228a77f74a484cd6bf58d3288d8524498a02cf0c8c/azure_mgmt_resource-23.2.0-py3-none-any.whl",
            }
        ]
        for acc in rg_with_afs_storage:
            await Automationaccount.install_python_package(
                automationaccountlist=acc,
                python_package_list=python_package_list,
            )
        # Report the accounts created
        with pd.ExcelWriter("automationoutput.xlsx", engine="openpyxl") as writer:
            for element in rg_with_afs_storage:
                tenantname = element["tenantName"]
                data = element["data"]
                if data:
                    df = pd.json_normalize(data)
                    df.to_excel(writer, sheet_name=tenantname[:31], index=False)
                else:
                    pd.DataFrame().to_excel(
                        writer, sheet_name=tenantname[:31], index=False
                    )

    except Exception as e:
        logging.warning(f"Error processing {e}")
    return func.HttpResponse(
        str(rg_with_afs_storage),
        status_code=200,
    )
