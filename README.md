# pyclinchpad
Python api for Clinchpad CRM


### Usage:

```python
from pyclinchpad import Clinchpad
cp = Clinchpad()
hotleads = cp.leads('Salespipeline', 'In negotiation')
```

Make sure you add a clinchpad.ini file with the followin content:

```
[api]
key = your-api-key-here
```

You can find your api key in the clinchad settings panel.
