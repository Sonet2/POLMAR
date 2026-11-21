# POLMAR

**A Python CLI for timber orders, roof-material calculations, and delivery cost estimates.**

Preparing a timber order involves material prices, dimensions, volumes, customer details, and transport costs. POLMAR addresses this real business problem by bringing those steps into one workflow backed by SQLite.

This is my individual project. I wrote all application code myself and I am responsible for its design, implementation, debugging, and ongoing development. I use AI tools to support my learning, code reviews, and occasionally to help find bugs.

The application has a Polish terminal interface.

## Features

- Manage individual and company customers, delivery locations, and warehouse records.
- Reserve available warehouse stock for orders and display reserved quantities. Prevent deletion of orders and warehouse entries with active reservations.
- Create orders from individual timber selections or roof-material calculations based on dimensions, quantities, and spacing.
- Estimate fuel consumption and cost using driving distances obtained through OpenRouteService.
- Search orders by customer name, display their items and final price, and update their status.
- Cancel forms with `/wstecz`. Press Enter in search fields to show all records.

Warehouse stock is reduced when materials are reserved. Cancelling an order returns the reserved quantities to the warehouse; completing an order clears its reservations without restoring the stock. Customers and delivery locations are saved separately and remain available if a subsequent order is cancelled.

## Technical decisions

The project evolved from JSON storage to a relational SQLite database.

- Monetary amounts use integer grosze. Each order item stores its original unit price.
- Orders, their items, and stock reservations are saved in one transaction, with rollback on failure.
- SQLite triggers calculate totals including fuel and enforce customer/address matching. Foreign keys protect related records.
- Repository classes handle SQL, managers coordinate operations, and the menu handles navigation. Dependencies are passed through constructors.

## Run locally

Tested with Python 3.14. These commands use a macOS/Linux shell and the SQLite command-line tool. Adding delivery locations requires internet access and an OpenRouteService API key.

### 1. Install dependencies

```bash
git clone https://github.com/Sonet2/POLMAR.git
cd POLMAR
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r requirements.txt
```

### 2. Configure the application

Create `.env` in the project root. Supply your API key and a complete dispatch address in Poland. Obtain a key through the [OpenRouteService developer portal](https://openrouteservice.org/dev/).

```dotenv
DATABASE=POLMAR.db
ORS_API_KEY=your_openrouteservice_api_key
START_ADDRESS="Your dispatch address in Poland"
```

The application loads `.env` automatically. This file is excluded from version control.

### 3. Create a database and sample catalog

For a new database, run the following command from the project root.

```bash
sqlite3 POLMAR.db < schema.sql
```

The following sample catalog supports both order types. Prices are demonstration values in grosze per cubic metre.

```bash
sqlite3 POLMAR.db <<'SQL'
PRAGMA foreign_keys = ON;
BEGIN;

INSERT INTO wood_species (id, name)
VALUES (1, 'sosna');

INSERT INTO materials (
    category, subcategory, wood_species_id, price_per_m3_grosze
)
VALUES
    ('deska', NULL, 1, 100000),
    ('kantowka', NULL, 1, 150000),
    ('belka', NULL, 1, 160000),
    ('lata', NULL, NULL, 120000),
    ('kontrlata', NULL, NULL, 120000);

COMMIT;
SQL
```

### 4. Start the application

```bash
python3 app.py
```

Select a section from the main menu to manage the warehouse, orders, or customers and deliveries. Select `0` to go back or exit.
