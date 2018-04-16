# Infrastructure of Intel® Media SDK
Product configurations of Intel® Media SDK.  
  
Repository contains only product configuration to build Intel® Media SDK.


# Configuration files naming rules
Pattern:  
`conf_<product type>_<source location>_[<additional tags>].py`

Product types:
- android
- linux
- embedded
- windows

Source locations:
- closed (Gerrit, Intel Inside)
- private (Github, Intel Inside)
- public (Github, Intel Outside)

Additional tags may be various.

Example:

- `conf_linux_closed_open.py`
  Means that configuration file for linux build from Intel inside gerrit repositories without private code

- `conf_embedded_private_api_latest.py`
  Means that configuration file for linux embedded build from Github private repository with latest API.


# License
This project is licensed under MIT license. See [LICENSE](./LICENSE) for details.
