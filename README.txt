Configuration files naming rules:

conf_<product type>_<source location>_[<additional tags>].py

product types:
- android
- linux
- embedded
- windows

source locations:
 - closed (Gerrit, Intel Inside)
 - private (Github, Intel Inside)
 - public (Github, Intel Outside)

additional tags may be various.

Example:

- conf_linux_closed_open.py
  means configuration file for linux build from Intel inside gerrit repositories without private code

- conf_embedded_private_api_latest.py
  means configuration file for linux embedded build from Github private repository with latest API.
  