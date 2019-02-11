# pyclinchpad
Python api for Clinchpad CRM.

### About Clinchpad
Very easy to use online CRM. Free up to 100 leads.

Simpler than a traditional CRM. Better than using spreadsheets.

Get it at https://clinchpad.com

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

### Missing features?

Of course. But feel free so send a PR.

### Only Python3?

Dude! It's 2019.
