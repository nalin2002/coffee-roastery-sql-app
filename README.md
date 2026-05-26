# coffee-roastery-sql-app

A MySQL schema and seed dataset for a specialty-coffee roastery, covering
farms → suppliers → green bean lots → roasting → QC → products → orders →
shipments, with full traceability and live inventory tracking.

## Tables and row counts

| Table | CSV | Rows |
| --- | --- | --- |
| `Farm` | `Farm.csv` | 200 |
| `Supplier` | `Supplier.csv` | 200 |
| `CoffeeBean` | `CoffeeBean.csv` | 200 (B001–B200) |
| `BeanLot` | `BeanLot.csv` | 200 |
| `RoastProfile` | `RoastProfile.csv` | 200 |
| `RoastingBatch` | `RoastingBatch.csv` | 200 (RB0001–RB0200) |
| `BatchLotUsage` | `BatchLotUsage.csv` | 256 (1–2 lots per batch) |
| `QualityControlRecord` | `QualityControlRecord.csv` | 200 (one per batch) |
| `Product` | `product.csv` | 80 |
| `BlendComponent` | `BlendComponent.csv` | 249 |
| `Client` | `Client.csv` | 80 |
| `ClientPrice` | `ClientPrice.csv` | 96 |
| `UserAccount` | `UserAccount.csv` | 80 |
| `SalesOrder` | `SalesOrder.csv` | 90 |
| `OrderLine` | `OrderLine.csv` | 90 |
| `Shipment` | `Shipment.csv` | 90 |
| `FulfilledBy` | `FulfilledBy.csv` | 90 |

## Setup

### 1. Create the schema in MySQL Workbench

- Create a new schema named `coffee_roastery` with charset **`utf8mb4`** and
  collation `utf8mb4_0900_ai_ci`.
- Double-click `coffee_roastery` so it's the default schema (shown **bold**).
- **File → Open SQL Script** → pick `schema.sql` → click **Execute All**
  (lightning bolt). This creates 16 tables, FKs, and 4 inventory triggers.

### 2. Enable LOCAL INFILE (one-time)

On the server, in a new SQL tab:

```sql
SET GLOBAL local_infile = 1;
```

On the client: **Database → Manage Connections → Advanced → Others**, add
`OPT_LOCAL_INFILE=1`, then reconnect.

If your Workbench has **Safe Updates** enabled, also turn it off in
**Preferences → SQL Editor**, since the triggers do unkeyed multi-row updates
in some workflows.

### 3. Load the CSVs (load order matters — FK parents first)

Open a new SQL tab against `coffee_roastery` and run the block below. The
`BatchLotUsage` and `FulfilledBy` loads will fire the inventory triggers,
which automatically initialize `BeanLot.remainingKg` and
`RoastingBatch.remainingKg` to the correct post-activity values.

```sql
USE coffee_roastery;
SET FOREIGN_KEY_CHECKS = 0;

LOAD DATA LOCAL INFILE 'Farm.csv'                 INTO TABLE Farm
  FIELDS TERMINATED BY ',' OPTIONALLY ENCLOSED BY '"' LINES TERMINATED BY '\n' IGNORE 1 LINES;
LOAD DATA LOCAL INFILE 'Supplier.csv'             INTO TABLE Supplier
  FIELDS TERMINATED BY ',' OPTIONALLY ENCLOSED BY '"' LINES TERMINATED BY '\n' IGNORE 1 LINES;
LOAD DATA LOCAL INFILE 'CoffeeBean.csv'           INTO TABLE CoffeeBean
  FIELDS TERMINATED BY ',' OPTIONALLY ENCLOSED BY '"' LINES TERMINATED BY '\n' IGNORE 1 LINES;
LOAD DATA LOCAL INFILE 'RoastProfile.csv'         INTO TABLE RoastProfile
  FIELDS TERMINATED BY ',' OPTIONALLY ENCLOSED BY '"' LINES TERMINATED BY '\n' IGNORE 1 LINES;
LOAD DATA LOCAL INFILE 'product.csv'              INTO TABLE Product
  FIELDS TERMINATED BY ',' OPTIONALLY ENCLOSED BY '"' LINES TERMINATED BY '\n' IGNORE 1 LINES;
LOAD DATA LOCAL INFILE 'Client.csv'               INTO TABLE Client
  FIELDS TERMINATED BY ',' OPTIONALLY ENCLOSED BY '"' LINES TERMINATED BY '\n' IGNORE 1 LINES;

LOAD DATA LOCAL INFILE 'BeanLot.csv'              INTO TABLE BeanLot
  FIELDS TERMINATED BY ',' OPTIONALLY ENCLOSED BY '"' LINES TERMINATED BY '\n' IGNORE 1 LINES;
LOAD DATA LOCAL INFILE 'BlendComponent.csv'       INTO TABLE BlendComponent
  FIELDS TERMINATED BY ',' OPTIONALLY ENCLOSED BY '"' LINES TERMINATED BY '\n' IGNORE 1 LINES;
LOAD DATA LOCAL INFILE 'ClientPrice.csv'          INTO TABLE ClientPrice
  FIELDS TERMINATED BY ',' OPTIONALLY ENCLOSED BY '"' LINES TERMINATED BY '\n' IGNORE 1 LINES;
LOAD DATA LOCAL INFILE 'UserAccount.csv'          INTO TABLE UserAccount
  FIELDS TERMINATED BY ',' OPTIONALLY ENCLOSED BY '"' LINES TERMINATED BY '\n' IGNORE 1 LINES;
LOAD DATA LOCAL INFILE 'SalesOrder.csv'           INTO TABLE SalesOrder
  FIELDS TERMINATED BY ',' OPTIONALLY ENCLOSED BY '"' LINES TERMINATED BY '\n' IGNORE 1 LINES;

LOAD DATA LOCAL INFILE 'RoastingBatch.csv'        INTO TABLE RoastingBatch
  FIELDS TERMINATED BY ',' OPTIONALLY ENCLOSED BY '"' LINES TERMINATED BY '\n' IGNORE 1 LINES;
LOAD DATA LOCAL INFILE 'BatchLotUsage.csv'        INTO TABLE BatchLotUsage
  FIELDS TERMINATED BY ',' OPTIONALLY ENCLOSED BY '"' LINES TERMINATED BY '\n' IGNORE 1 LINES;

LOAD DATA LOCAL INFILE 'OrderLine.csv'            INTO TABLE OrderLine
  FIELDS TERMINATED BY ',' OPTIONALLY ENCLOSED BY '"' LINES TERMINATED BY '\n' IGNORE 1 LINES;
LOAD DATA LOCAL INFILE 'Shipment.csv'             INTO TABLE Shipment
  FIELDS TERMINATED BY ',' OPTIONALLY ENCLOSED BY '"' LINES TERMINATED BY '\n' IGNORE 1 LINES;
LOAD DATA LOCAL INFILE 'QualityControlRecord.csv' INTO TABLE QualityControlRecord
  FIELDS TERMINATED BY ',' OPTIONALLY ENCLOSED BY '"' LINES TERMINATED BY '\n' IGNORE 1 LINES;

LOAD DATA LOCAL INFILE 'FulfilledBy.csv'          INTO TABLE FulfilledBy
  FIELDS TERMINATED BY ',' OPTIONALLY ENCLOSED BY '"' LINES TERMINATED BY '\n' IGNORE 1 LINES;

SET FOREIGN_KEY_CHECKS = 1;
```

Replace `'Farm.csv'` etc. with absolute paths if Workbench can't find the
files relative to its working directory.

### 4. Verify

```sql
SELECT 'Farm' t, COUNT(*) n FROM Farm UNION ALL
SELECT 'BeanLot',        COUNT(*) FROM BeanLot UNION ALL
SELECT 'BatchLotUsage',  COUNT(*) FROM BatchLotUsage UNION ALL
SELECT 'RoastingBatch',  COUNT(*) FROM RoastingBatch UNION ALL
SELECT 'QualityControlRecord', COUNT(*) FROM QualityControlRecord;
```

Expected: 200 / 200 / 256 / 200 / 200.
