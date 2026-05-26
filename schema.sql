-- Coffee Roastery — MySQL DDL (schema v2, ready to use)
-- Charset utf8mb4 everywhere: source CSVs contain em-dashes, curly quotes, arrows.
--
-- Divergences from Schema.txt:
--   * SalesOrder.totalAmount        — in schema, not in CSV (compute via SUM(OrderLine.linePrice))
--   * BlendComponent.componentID    — in schema, not in CSV; PK is (productID, beanID)
--   * BeanLot adds supplierID, farmID, beanID, remainingKg
--   * RoastingBatch uses BatchLotUsage (many lots per batch); adds remainingKg
--   * QualityControlRecord adds batchID (one QC per batch)
--   * BatchLotUsage, ClientPrice, FulfilledBy are association tables
--   * Triggers maintain BeanLot.remainingKg and RoastingBatch.remainingKg

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;
SET SQL_SAFE_UPDATES = 0;

DROP TRIGGER IF EXISTS trg_blu_ai;
DROP TRIGGER IF EXISTS trg_blu_ad;
DROP TRIGGER IF EXISTS trg_fb_ai;
DROP TRIGGER IF EXISTS trg_fb_ad;

DROP TABLE IF EXISTS FulfilledBy;
DROP TABLE IF EXISTS Shipment;
DROP TABLE IF EXISTS OrderLine;
DROP TABLE IF EXISTS SalesOrder;
DROP TABLE IF EXISTS ClientPrice;
DROP TABLE IF EXISTS UserAccount;
DROP TABLE IF EXISTS Client;
DROP TABLE IF EXISTS BlendComponent;
DROP TABLE IF EXISTS QualityControlRecord;
DROP TABLE IF EXISTS BatchLotUsage;
DROP TABLE IF EXISTS RoastingBatch;
DROP TABLE IF EXISTS RoastProfile;
DROP TABLE IF EXISTS BeanLot;
DROP TABLE IF EXISTS CoffeeBean;
DROP TABLE IF EXISTS Supplier;
DROP TABLE IF EXISTS Farm;
DROP TABLE IF EXISTS Product;

-- ---------------------------------------------------------------------------
-- Level 1: parent / lookup tables
-- ---------------------------------------------------------------------------

CREATE TABLE Farm (
  farmID            VARCHAR(8)   NOT NULL,
  farmName          VARCHAR(255) NOT NULL,
  country           VARCHAR(100) NOT NULL,
  region            VARCHAR(150) NOT NULL,
  altitude          INT          NULL,
  processingMethod  VARCHAR(100) NULL,
  PRIMARY KEY (farmID)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE Supplier (
  supplierID    VARCHAR(8)   NOT NULL,
  supplierName  VARCHAR(255) NOT NULL,
  contactEmail  VARCHAR(255) NULL,
  phone         VARCHAR(40)  NULL,
  PRIMARY KEY (supplierID)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE CoffeeBean (
  beanID   VARCHAR(8)   NOT NULL,
  beanName VARCHAR(255) NOT NULL,
  variety  VARCHAR(150) NULL,
  origin   VARCHAR(100) NULL,
  PRIMARY KEY (beanID)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE RoastProfile (
  profileID         VARCHAR(8)   NOT NULL,
  profileName       VARCHAR(255) NOT NULL,
  roastLevel        VARCHAR(40)  NOT NULL,
  durationMinutes   DECIMAL(5,2) NOT NULL,
  temperatureCurve  VARCHAR(255) NULL,
  PRIMARY KEY (profileID)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE Product (
  productID    INT            NOT NULL,
  productName  VARCHAR(255)   NOT NULL,
  productType  VARCHAR(80)    NULL,
  description  TEXT           NULL,
  pricePerKg   DECIMAL(10,2)  NOT NULL,
  PRIMARY KEY (productID)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE Client (
  clientID       VARCHAR(8)   NOT NULL,
  clientName     VARCHAR(255) NOT NULL,
  contactPerson  VARCHAR(150) NULL,
  email          VARCHAR(255) NULL,
  phone          VARCHAR(40)  NULL,
  address        VARCHAR(255) NULL,
  PRIMARY KEY (clientID)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ---------------------------------------------------------------------------
-- Level 2
-- ---------------------------------------------------------------------------

CREATE TABLE BeanLot (
  lotID        VARCHAR(10)    NOT NULL,
  supplierID   VARCHAR(8)     NOT NULL,
  farmID       VARCHAR(8)     NOT NULL,
  beanID       VARCHAR(8)     NOT NULL,
  arrivalDate  DATE           NOT NULL,
  quantityKg   DECIMAL(12,2)  NOT NULL,
  costPerKg    DECIMAL(10,2)  NOT NULL,
  remainingKg  DECIMAL(12,2)  NOT NULL,
  PRIMARY KEY (lotID),
  KEY ix_beanlot_supplier (supplierID),
  KEY ix_beanlot_farm (farmID),
  KEY ix_beanlot_bean (beanID),
  CONSTRAINT fk_beanlot_supplier FOREIGN KEY (supplierID) REFERENCES Supplier(supplierID),
  CONSTRAINT fk_beanlot_farm     FOREIGN KEY (farmID)     REFERENCES Farm(farmID),
  CONSTRAINT fk_beanlot_bean     FOREIGN KEY (beanID)     REFERENCES CoffeeBean(beanID)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE BlendComponent (
  productID   INT            NOT NULL,
  beanID      VARCHAR(8)     NOT NULL,
  proportion  DECIMAL(6,4)   NOT NULL,
  PRIMARY KEY (productID, beanID),
  KEY ix_blend_bean (beanID),
  CONSTRAINT fk_blend_product FOREIGN KEY (productID) REFERENCES Product(productID),
  CONSTRAINT fk_blend_bean    FOREIGN KEY (beanID)    REFERENCES CoffeeBean(beanID)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE ClientPrice (
  clientID              VARCHAR(8)    NOT NULL,
  productID             INT           NOT NULL,
  specialUnitPricePerKg DECIMAL(10,2) NOT NULL,
  discount              DECIMAL(5,4)  NOT NULL,
  PRIMARY KEY (clientID, productID),
  KEY ix_cp_product (productID),
  CONSTRAINT fk_cp_client  FOREIGN KEY (clientID)  REFERENCES Client(clientID),
  CONSTRAINT fk_cp_product FOREIGN KEY (productID) REFERENCES Product(productID)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE UserAccount (
  userID        VARCHAR(8)   NOT NULL,
  clientID      VARCHAR(8)   NULL,
  username      VARCHAR(80)  NOT NULL,
  passwordHash  VARCHAR(255) NOT NULL,
  role          VARCHAR(40)  NOT NULL,
  PRIMARY KEY (userID),
  UNIQUE KEY uq_user_username (username),
  KEY ix_user_client (clientID),
  CONSTRAINT fk_user_client FOREIGN KEY (clientID) REFERENCES Client(clientID)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE SalesOrder (
  orderID    VARCHAR(8)  NOT NULL,
  clientID   VARCHAR(8)  NOT NULL,
  orderDate  DATE        NOT NULL,
  status     VARCHAR(40) NOT NULL,
  PRIMARY KEY (orderID),
  KEY ix_so_client (clientID),
  CONSTRAINT fk_so_client FOREIGN KEY (clientID) REFERENCES Client(clientID)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ---------------------------------------------------------------------------
-- Level 3
-- ---------------------------------------------------------------------------

CREATE TABLE RoastingBatch (
  batchID             VARCHAR(8)    NOT NULL,
  profileID           VARCHAR(8)    NOT NULL,
  roastDate           DATE          NOT NULL,
  quantityProducedKg  DECIMAL(10,2) NOT NULL,
  remainingKg         DECIMAL(10,2) NOT NULL,
  notes               TEXT          NULL,
  PRIMARY KEY (batchID),
  KEY ix_rb_profile (profileID),
  CONSTRAINT fk_rb_profile FOREIGN KEY (profileID) REFERENCES RoastProfile(profileID)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE BatchLotUsage (
  batchID         VARCHAR(8)    NOT NULL,
  lotID           VARCHAR(10)   NOT NULL,
  quantityUsedKg  DECIMAL(10,2) NOT NULL,
  PRIMARY KEY (batchID, lotID),
  KEY ix_blu_lot (lotID),
  CONSTRAINT fk_blu_batch FOREIGN KEY (batchID) REFERENCES RoastingBatch(batchID),
  CONSTRAINT fk_blu_lot   FOREIGN KEY (lotID)   REFERENCES BeanLot(lotID)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE OrderLine (
  lineID     VARCHAR(8)    NOT NULL,
  orderID    VARCHAR(8)    NOT NULL,
  productID  INT           NOT NULL,
  quantity   DECIMAL(10,2) NOT NULL,
  linePrice  DECIMAL(12,2) NOT NULL,
  PRIMARY KEY (lineID),
  KEY ix_ol_order (orderID),
  KEY ix_ol_product (productID),
  CONSTRAINT fk_ol_order   FOREIGN KEY (orderID)   REFERENCES SalesOrder(orderID),
  CONSTRAINT fk_ol_product FOREIGN KEY (productID) REFERENCES Product(productID)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE Shipment (
  shipmentID      VARCHAR(8)   NOT NULL,
  orderID         VARCHAR(8)   NOT NULL,
  shipmentDate    DATE         NOT NULL,
  carrier         VARCHAR(80)  NOT NULL,
  trackingNumber  VARCHAR(80)  NOT NULL,
  PRIMARY KEY (shipmentID),
  KEY ix_sh_order (orderID),
  CONSTRAINT fk_sh_order FOREIGN KEY (orderID) REFERENCES SalesOrder(orderID)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ---------------------------------------------------------------------------
-- Level 4
-- ---------------------------------------------------------------------------

CREATE TABLE QualityControlRecord (
  qcID          VARCHAR(8)    NOT NULL,
  batchID       VARCHAR(8)    NOT NULL,
  cuppingScore  DECIMAL(5,2)  NOT NULL,
  tastingNotes  TEXT          NULL,
  defectNotes   VARCHAR(255)  NULL,
  PRIMARY KEY (qcID),
  UNIQUE KEY uq_qc_batch (batchID),
  CONSTRAINT fk_qc_batch FOREIGN KEY (batchID) REFERENCES RoastingBatch(batchID)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE FulfilledBy (
  lineID              VARCHAR(8)    NOT NULL,
  batchID             VARCHAR(8)    NOT NULL,
  quantityFromBatchKg DECIMAL(10,2) NOT NULL,
  PRIMARY KEY (lineID, batchID),
  KEY ix_fb_batch (batchID),
  CONSTRAINT fk_fb_line  FOREIGN KEY (lineID)  REFERENCES OrderLine(lineID),
  CONSTRAINT fk_fb_batch FOREIGN KEY (batchID) REFERENCES RoastingBatch(batchID)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

SET FOREIGN_KEY_CHECKS = 1;

-- ---------------------------------------------------------------------------
-- Triggers — keep remainingKg in sync as BatchLotUsage and FulfilledBy change
-- ---------------------------------------------------------------------------

DELIMITER //

CREATE TRIGGER trg_blu_ai AFTER INSERT ON BatchLotUsage
FOR EACH ROW
BEGIN
  UPDATE BeanLot SET remainingKg = remainingKg - NEW.quantityUsedKg WHERE lotID = NEW.lotID;
END//

CREATE TRIGGER trg_blu_ad AFTER DELETE ON BatchLotUsage
FOR EACH ROW
BEGIN
  UPDATE BeanLot SET remainingKg = remainingKg + OLD.quantityUsedKg WHERE lotID = OLD.lotID;
END//

CREATE TRIGGER trg_fb_ai AFTER INSERT ON FulfilledBy
FOR EACH ROW
BEGIN
  UPDATE RoastingBatch SET remainingKg = remainingKg - NEW.quantityFromBatchKg WHERE batchID = NEW.batchID;
END//

CREATE TRIGGER trg_fb_ad AFTER DELETE ON FulfilledBy
FOR EACH ROW
BEGIN
  UPDATE RoastingBatch SET remainingKg = remainingKg + OLD.quantityFromBatchKg WHERE batchID = OLD.batchID;
END//

DELIMITER ;
