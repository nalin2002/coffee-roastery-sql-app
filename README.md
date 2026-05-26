# coffee-roastery-sql-app

This project currently includes the following generated tables and their total **data rows** (excluding CSV header rows):

- `Product` (`product.csv`): 80 rows ( Picked from specified Source in step2)
- `BlendComponent` (`BlendComponent.csv`): 249 rows
- `Client` (`Client.csv`): 80 rows
- `ClientPrice` (`ClientPrice.csv`): 96 rows
- `UserAccount` (`UserAccount.csv`): 80 rows
- `SalesOrder` (`SalesOrder.csv`): 90 rows
- `OrderLine` (`OrderLine.csv`): 90 rows
- `Shipment` (`Shipment.csv`): 90 rows
- `FulfilledBy` (`FulfilledBy.csv`): 90 rows
- `Farm` (`Farm.csv`): 200 rows
- `Supplier` (`Supplier.csv`): 200 rows
- `CoffeeBean` (`CoffeeBean.csv`): 200 rows (B001–B200; covers B001–B060 referenced by `BlendComponent`)
- `BeanLot` (`BeanLot.csv`): 200 rows
- `RoastProfile` (`RoastProfile.csv`): 200 rows
- `RoastingBatch` (`RoastingBatch.csv`): 200 rows (RB0001–RB0200; covers RB IDs referenced by `FulfilledBy`)
- `QualityControlRecord` (`QualityControlRecord.csv`): 200 rows (one per `RoastingBatch`)
