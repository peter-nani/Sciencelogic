from silo.network_tools.client.local_cmd_client import LocalCMDClient
from silo.network_tools.CMD_OPTIONS import Cmd
from silo.network_tools.event_logger import EventLogger
from silo.text_formatter.enrichment_decorators.memory_calculator import calculate_memory


def resolve_host_variable(host_var, em7_values, fallback_var="%X"):
    if host_var is None:
        return fallback_var

    if not isinstance(host_var, str):
        return host_var

    if not host_var.startswith("%"):
        return host_var

    value = em7_values.get(host_var)

    if value is None or str(value).strip().lower() in ("", "none", "null"):
        return fallback_var

    return host_var


@calculate_memory(EM7_LAST_RESULT_LIST, limit_action_memory=50000)
def process(**kwargs):
    available_memory = kwargs["AVAILABLE_MEMORY"]

    try:
        logger = EventLogger(
            logger_name="run_nslookup",
            log_file_path="/tmp/enrichment.log",
            format_type="%(asctime)s %(levelname)-1s %(context)-15s %(uuid)-1s %(message)s",
            logger_enabled=True,
        )

        input_host = globals().get("host")
        input_nameserver = globals().get("nameserver", "")
        input_options = globals().get("options", "")

        logger.log_event(
            "info",
            "Input host variable: [{}]".format(input_host)
        )

        logger.log_event(
            "info",
            "EM7 root name: [{}]".format(
                EM7_VALUES.get("%_root_name")
            )
        )

        logger.log_event(
            "info",
            "EM7 root id: [{}]".format(
                EM7_VALUES.get("%_root_id")
            )
        )

        logger.log_event(
            "info",
            "EM7 parent name: [{}]".format(
                EM7_VALUES.get("%_parent_name")
            )
        )

        logger.log_event(
            "info",
            "EM7 parent id: [{}]".format(
                EM7_VALUES.get("%_parent_id")
            )
        )

        logger.log_event(
            "info",
            "EM7 current entity: [{}]".format(
                EM7_VALUES.get("%X")
            )
        )

        resolved_host = resolve_host_variable(
            host_var=input_host,
            em7_values=EM7_VALUES,
            fallback_var="%X"
        )

        logger.log_event(
            "info",
            "Host value passed to LocalCMDClient: [{}]".format(
                resolved_host
            )
        )

        command_data = {
            "host": resolved_host,
            "nameserver": input_nameserver,
            "options": input_options,
        }

        logger.log_event(
            "info",
            "Command data: {}".format(command_data)
        )

        local_client = LocalCMDClient(
            EM7_VALUES,
            logger,
            command_data,
            EM7_LAST_RESULT_LIST
        )

        logger.log_event(
            "info",
            "Action type [{}] execution started.".format(
                logger.logger_name
            )
        )

        result = local_client.execute_command(
            Cmd.NSLOOKUP.value
        )

        logger.log_event(
            "info",
            "NSLookup result: [{}]".format(result)
        )

        result = {
            "command_list_out": [
                result + (None,)
            ]
        }

    except ValueError as ex:
        result = ex

        logger.log_event(
            "error",
            "Error executing action type: {}".format(ex)
        )

    logger.log_event(
        "info",
        "Action type [{}] execution finished.".format(
            logger.logger_name
        )
    )

    return result


EM7_RESULT = process()