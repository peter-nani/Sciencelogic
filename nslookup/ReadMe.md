Network Connectivity – Root Device NSLookup
Problem Statement

The SFTY:SQL: Network Connectivity: Run Nslookup (IPv4) Automation Policy uses the ScienceLogic LocalCMDClient to execute an nslookup command.

The original PowerPack snippet expects the following input parameters:

[
  {
    "name": "host",
    "type": "string"
  },
  {
    "name": "nameserver",
    "type": "string"
  },
  {
    "name": "options",
    "type": "string"
  }
]

The Action was configured with:

{
  "host": "%_root_name",
  "nameserver": "",
  "options": ""
}

The requirement was:

If the event occurs on a component device, perform NSLookup against the root device.
If the event occurs directly on a root device, perform NSLookup against the root/event device itself.
Initial Problem

ScienceLogic provides the following Run Book variables for component events:

%_root_name
%_root_id
%_parent_name
%_parent_id

However, %_root_name is only populated when the event is associated with a component device. For a root-device event, %_root_name can be None.

For example, for an event on:

MSSQLSERVER

the EM7 hierarchy was:

MTTstr_sdYYp_R.org
    |
    +-- Microsoft SQL Server
            |
            +-- MSSQLSERVER

The EM7 values confirmed:

%X              = MSSQLSERVER
%x              = 1714

%_parent_name   = Microsoft SQL Server
%_parent_id     = 1710

%_root_name     = MTTstr_sdYYp_R.org
%_root_id       = 1681

The EM7 runtime therefore had the root information available for the component event.

Investigation
1. Understanding EM7 Variable Translation

LocalCMDClient inherits from the ScienceLogic Client class.

The existing implementation uses:

self.format_command(...)

to translate EM7 variables using EM7_VALUES.

The flow is:

Action Input
      |
      v
host = "%_root_name"
      |
      v
LocalCMDClient
      |
      v
Client.format_command()
      |
      v
EM7_VALUES["%_root_name"]
      |
      v
Actual root device name

Therefore, there was no need to implement a separate EM7 variable translation mechanism.

2. Incorrect Use of kwargs

An attempt was made to retrieve the PowerPack input using:

host = kwargs.get("host")

This resulted in:

Input hostname variable: [None]

even though %_root_name was present in EM7_VALUES.

The reason was that the PowerPack input parameters are exposed as snippet variables:

host
nameserver
options

and are not necessarily stored inside the kwargs dictionary.

The original PowerPack code confirms this pattern because it directly uses:

command_data = {
    "host": host,
    "nameserver": nameserver,
    "options": options,
}

rather than:

kwargs.get("host")
Solution Implemented

The solution preserves the existing ScienceLogic PowerPack architecture.

The Action continues to provide:

{
  "host": "%_root_name",
  "nameserver": "",
  "options": ""
}

The snippet receives host as the PowerPack input variable and passes it to LocalCMDClient.

When %_root_name is available:

host
 |
 +-- %_root_name
          |
          v
    LocalCMDClient
          |
          v
    format_command()
          |
          v
MTTstr_sdYYp_R.org

The final command becomes:

nslookup MTTstr_sdYYp_R.org
Root Device Resolution

The implemented logic also supports a fallback when %_root_name is unavailable.

The intended logic is:

                    Event
                      |
                      v
               %_root_name
                      |
              +-------+-------+
              |               |
            Value           None
              |               |
              v               v
       Use %_root_name       %X
              |               |
              +-------+-------+
                      |
                      v
               LocalCMDClient
                      |
                      v
                 NSLOOKUP

For a component event:

%_root_name
    |
    v
MTTstr_sdYYp_R.org

For a root-device event:

%_root_name
    |
    v
None
    |
    v
%X
    |
    v
Current/root device name

This allows the same Action to handle both component and root-device events.

Implementation

The host-resolution helper:

def resolve_host_variable(host_var, em7_values, fallback_var="%X"):
    value = em7_values.get(host_var)

    if value is None or str(value).strip().lower() in ("", "none", "null"):
        return fallback_var

    return value

The important design decision is that the helper returns the EM7 variable token such as:

%_root_name

or:

%X

rather than attempting to translate it itself.

LocalCMDClient remains responsible for the actual EM7 variable translation.

Validation

The final test confirmed the complete flow.

The snippet received:

Input host variable: [%_root_name]

and EM7 provided:

EM7 root name: [MTTstr_sdYYp_R.org]
EM7 root id: [1681]
EM7 parent name: [Microsoft SQL Server]
EM7 current entity: [MSSQLSERVER]

The command data remained:

{
    'host': '%_root_name',
    'nameserver': '',
    'options': ''
}

LocalCMDClient then translated %_root_name and executed:

nslookup MTTstr_sdYYp_R.org

The DNS lookup successfully returned:

Name:    MTTstr_sdYYp_R.org
Address: 10.15.20.22

Current Architecture
ScienceLogic Event
        |
        v
Determine event entity
        |
        v
PowerPack Input
host = "%_root_name"
        |
        v
Python Snippet
        |
        v
LocalCMDClient
        |
        v
Client.format_command()
        |
        v
EM7_VALUES
        |
        +----------------------+
        |                      |
 Component Event          Root Event
        |                      |
 %_root_name              %_root_name=None
        |                      |
        v                      v
 Root Device Name              %X
        |                      |
        +----------+-----------+
                   |
                   v
              NSLOOKUP
Future Enhancement: Root Device IP Lookup

The next requirement is to perform a reverse NSLookup using the root device IP, regardless of where the event occurs.

For example:

Component Event
      |
      v
%_root_id = 1681
      |
      v
Find root device IP
      |
      v
10.15.20.22
      |
      v
nslookup 10.15.20.22
      |
      v
MTTstr_sdYYp_R.org

For a root-device event:

Root Event
      |
      v
%x = Root Device ID
      |
      v
Find root device IP
      |
      v
10.15.20.22
      |
      v
nslookup 10.15.20.22

Potential approaches identified for this enhancement are:

Find an existing EM7 Run Book variable that directly provides the root device IP.
Use %_root_id for component events and %x for root events, then retrieve the device IP through a supported EM7 API/client mechanism.
Retrieve the IP from the EM7 database if no supported API mechanism is available.
As a fallback, resolve %_root_name to an IP first and then perform the reverse lookup.

The preferred approach is to use the root device ID → supported EM7 device lookup → root IP → reverse NSLookup path, avoiding hard-coded IP addresses or dependence on DNS forward resolution.