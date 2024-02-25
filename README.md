# ![WMGZON](/static/assets/Logo.png)

## General Description

WMGZON is an online shopping tool allowing users to browse and purchase a wide range of products split into various product categories. The tool operates through a website that allows users to browse products, create accounts, store interesting products to their ‘Wishlist’ to view later, and places orders. The site also provides a platform for adding & managing the listed products via certain management pages only available to administrator accounts.

## Prerequisites

Before running the app, you must have Python 3.9.4 or later installed.
Following this, ensure you have the relevant packages installed.
These can be installed through the pip package manager with the following command:

```bash
$ pip install -r requirements.txt
```

## Running

If all prerequisites have been met, the app can be started by running the 'app.py' file. Either run the file through your IDE or enter the following command into a terminal window under the WMGZON directory:

```bash
$ python app.py
```

This will launch a development server and share the address in the terminal.
Navigate to this address in a web browser to view the app.

### Good to Know

User accounts can be created through the '/signup' page.
An administrator account is already configured with the following details:

> Email: admin@wmgzon.com <br>
> Password: Admin123

The basket clears of products each time the app is re-run.

## Testing

A series of tests have been created with Pytest. To run these, enter the following command into a terminal window under the WMGZON directory:

```bash
$ python -m pytest
```
