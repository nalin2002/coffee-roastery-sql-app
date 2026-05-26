"""
MPCS 53001 Databases - Final Project Step 3
Coffee Roastery Database GUI

Team: Nalin Prabhath, Yuanda Gao, Qinyu Li, Disha Janardhan
"""

import os
import sys
from pathlib import Path

import mysql.connector
from dotenv import load_dotenv
from PyQt5.QtCore import QDate
from PyQt5.QtWidgets import (
    QApplication, QComboBox, QDateEdit, QDialog, QDoubleSpinBox,
    QFormLayout, QHBoxLayout, QHeaderView, QLabel, QMainWindow,
    QMessageBox, QPushButton, QSpinBox, QTableWidget, QTableWidgetItem,
    QVBoxLayout, QWidget,
)

load_dotenv(dotenv_path=Path(__file__).with_name(".env"))


def get_conn():
    # opens a new connection to our coffee_roastery MySQL database
    return mysql.connector.connect(
        host=os.environ["DB_HOST"],
        port=int(os.environ.get("DB_PORT", 3306)),
        user=os.environ["DB_USER"],
        password=os.environ["DB_PASSWORD"],
        database=os.environ["DB_NAME"],
        autocommit=False,
        charset="utf8mb4",
        collation="utf8mb4_unicode_ci",
        use_pure=True,
    )


QUERIES = [
    {
        "id": 1,
        "title": "Which farms and suppliers provided the bean lots used in a specific roasting batch?",
        "params": [{"name": "batchID", "kind": "select_batch", "label": "Batch ID"}],
        "sql": """
            SELECT DISTINCT
                f.farmID, f.farmName, f.country,
                s.supplierID, s.supplierName,
                bl.lotID, blu.quantityUsedKg
            FROM BatchLotUsage blu
            JOIN BeanLot bl ON bl.lotID = blu.lotID
            JOIN Farm f ON f.farmID = bl.farmID
            JOIN Supplier s ON s.supplierID = bl.supplierID
            WHERE blu.batchID = %s
            ORDER BY f.farmName, s.supplierName, bl.lotID
        """,
    },
    {
        "id": 2,
        "title": "For a given customer order, which roasting batches, bean lots, and farms were involved in fulfilling it?",
        "params": [{"name": "orderID", "kind": "select_order", "label": "Order ID"}],
        "sql": """
            SELECT
                ol.lineID, p.productName,
                rb.batchID, rb.roastDate, fb.quantityFromBatchKg,
                bl.lotID, blu.quantityUsedKg,
                f.farmName, f.country
            FROM OrderLine ol
            JOIN Product p ON p.productID = ol.productID
            JOIN FulfilledBy fb ON fb.lineID = ol.lineID
            JOIN RoastingBatch rb ON rb.batchID = fb.batchID
            JOIN BatchLotUsage blu ON blu.batchID = rb.batchID
            JOIN BeanLot bl ON bl.lotID = blu.lotID
            JOIN Farm f ON f.farmID = bl.farmID
            WHERE ol.orderID = %s
            ORDER BY ol.lineID, rb.batchID, bl.lotID
        """,
    },
    {
        "id": 3,
        "title": "Which roast profiles have been used most often across all roasting batches?",
        "params": [{"name": "limit", "kind": "limit", "label": "Show top"}],
        "sql": """
            SELECT
                rp.profileID, rp.profileName, rp.roastLevel,
                COUNT(*) AS batches_count,
                SUM(rb.quantityProducedKg) AS total_produced_kg
            FROM RoastingBatch rb
            JOIN RoastProfile rp ON rp.profileID = rb.profileID
            GROUP BY rp.profileID, rp.profileName, rp.roastLevel
            ORDER BY batches_count DESC
            LIMIT %s
        """,
    },
    {
        "id": 4,
        "title": "What is the current green coffee inventory remaining for each bean lot after all recorded roasting activity?",
        "params": [],
        "sql": """
            SELECT
                bl.lotID, b.beanName, b.variety,
                f.farmName, f.country,
                bl.arrivalDate,
                bl.quantityKg AS arrived_kg,
                bl.remainingKg AS remaining_kg
            FROM BeanLot bl
            JOIN CoffeeBean b ON b.beanID = bl.beanID
            JOIN Farm f ON f.farmID = bl.farmID
            ORDER BY bl.remainingKg DESC
        """,
    },
    {
        "id": 5,
        "title": "Which products are blends, and which beans make up each blend with what proportions?",
        "params": [],
        "sql": """
            SELECT
                p.productID, p.productName, p.productType,
                b.beanID, b.beanName, b.variety, b.origin,
                bc.proportion
            FROM Product p
            JOIN BlendComponent bc ON bc.productID = p.productID
            JOIN CoffeeBean b ON b.beanID = bc.beanID
            WHERE p.productID IN (
                SELECT productID FROM BlendComponent
                GROUP BY productID HAVING COUNT(*) > 1
            )
            ORDER BY p.productName, bc.proportion DESC
        """,
    },
    {
        "id": 6,
        "title": "Which batches of coffee were used to fulfill a specific client's orders?",
        "params": [{"name": "clientID", "kind": "select_client", "label": "Client"}],
        "sql": """
            SELECT
                so.orderID, so.orderDate, p.productName,
                rb.batchID, rb.roastDate, fb.quantityFromBatchKg
            FROM Client c
            JOIN SalesOrder so ON so.clientID = c.clientID
            JOIN OrderLine ol ON ol.orderID = so.orderID
            JOIN Product p ON p.productID = ol.productID
            JOIN FulfilledBy fb ON fb.lineID = ol.lineID
            JOIN RoastingBatch rb ON rb.batchID = fb.batchID
            WHERE c.clientID = %s
            ORDER BY so.orderDate DESC, so.orderID, rb.batchID
        """,
    },
    {
        "id": 7,
        "title": "What are the average quality scores for each roast profile?",
        "params": [],
        "sql": """
            SELECT
                rp.profileID, rp.profileName, rp.roastLevel,
                COUNT(qc.qcID) AS n_batches,
                ROUND(AVG(qc.cuppingScore), 2) AS avg_score,
                ROUND(MIN(qc.cuppingScore), 2) AS min_score,
                ROUND(MAX(qc.cuppingScore), 2) AS max_score
            FROM RoastProfile rp
            JOIN RoastingBatch rb ON rb.profileID = rp.profileID
            JOIN QualityControlRecord qc ON qc.batchID = rb.batchID
            GROUP BY rp.profileID, rp.profileName, rp.roastLevel
            ORDER BY avg_score DESC
        """,
    },
    {
        "id": 8,
        "title": "Which clients purchased the highest volume of each product over a selected time period?",
        "params": [
            {"name": "start_date", "kind": "date", "label": "Start date"},
            {"name": "end_date", "kind": "date", "label": "End date"},
        ],
        "sql": """
            SELECT
                p.productID, p.productName,
                c.clientID, c.clientName,
                SUM(ol.quantity) AS total_kg,
                SUM(ol.linePrice) AS total_revenue
            FROM SalesOrder so
            JOIN Client c ON c.clientID = so.clientID
            JOIN OrderLine ol ON ol.orderID = so.orderID
            JOIN Product p ON p.productID = ol.productID
            WHERE so.orderDate BETWEEN %s AND %s
            GROUP BY p.productID, p.productName, c.clientID, c.clientName
            ORDER BY p.productID, total_kg DESC
        """,
    },
    {
        "id": 9,
        "title": "Which orders are still pending, and are there enough completed roasting batches available to fulfill them?",
        "params": [],
        "sql": """
            SELECT
                so.orderID, so.orderDate, c.clientName,
                SUM(ol.quantity) AS total_ordered_kg,
                (SELECT COALESCE(SUM(rb.remainingKg), 0) FROM RoastingBatch rb)
                    AS total_available_roasted_kg
            FROM SalesOrder so
            JOIN Client c ON c.clientID = so.clientID
            JOIN OrderLine ol ON ol.orderID = so.orderID
            WHERE so.status = 'Pending'
            GROUP BY so.orderID, so.orderDate, c.clientName
            ORDER BY so.orderDate
        """,
    },
    {
        "id": 10,
        "title": "What shipment information, including shipment date and tracking number, is associated with each fulfilled order?",
        "params": [],
        "sql": """
            SELECT
                so.orderID, so.orderDate, so.status, c.clientName,
                sh.shipmentID, sh.shipmentDate, sh.carrier, sh.trackingNumber
            FROM SalesOrder so
            JOIN Shipment sh ON sh.orderID = so.orderID
            JOIN Client c ON c.clientID = so.clientID
            ORDER BY sh.shipmentDate DESC
        """,
    },
    {
        "id": 11,
        "title": "Which bean lots have been used most frequently across roasting batches, and in what total quantities?",
        "params": [{"name": "limit", "kind": "limit", "label": "Show top"}],
        "sql": """
            SELECT
                bl.lotID, b.beanName, f.farmName,
                COUNT(DISTINCT blu.batchID) AS batches_used_in,
                SUM(blu.quantityUsedKg) AS total_used_kg,
                bl.quantityKg AS original_kg,
                bl.remainingKg AS remaining_kg
            FROM BatchLotUsage blu
            JOIN BeanLot bl ON bl.lotID = blu.lotID
            JOIN CoffeeBean b ON b.beanID = bl.beanID
            JOIN Farm f ON f.farmID = bl.farmID
            GROUP BY bl.lotID, b.beanName, f.farmName, bl.quantityKg, bl.remainingKg
            ORDER BY batches_used_in DESC, total_used_kg DESC
            LIMIT %s
        """,
    },
    {
        "id": 12,
        "title": "Which products are the best-selling products by month, and which clients buy them most often?",
        "params": [
            {"name": "start_date", "kind": "date", "label": "Start date"},
            {"name": "end_date", "kind": "date", "label": "End date"},
        ],
        "sql": """
            SELECT
                monthly.month,
                monthly.productID,
                monthly.productName,
                monthly.total_kg,
                (
                    SELECT c2.clientName
                    FROM SalesOrder so2
                    JOIN Client c2 ON c2.clientID = so2.clientID
                    JOIN OrderLine ol2 ON ol2.orderID = so2.orderID
                    WHERE ol2.productID = monthly.productID
                      AND DATE_FORMAT(so2.orderDate, '%%Y-%%m') = monthly.month
                    GROUP BY c2.clientID, c2.clientName
                    ORDER BY SUM(ol2.quantity) DESC
                    LIMIT 1
                ) AS top_client
            FROM (
                SELECT
                    DATE_FORMAT(so.orderDate, '%%Y-%%m') AS month,
                    p.productID, p.productName,
                    SUM(ol.quantity) AS total_kg
                FROM SalesOrder so
                JOIN OrderLine ol ON ol.orderID = so.orderID
                JOIN Product p ON p.productID = ol.productID
                WHERE so.orderDate BETWEEN %s AND %s
                GROUP BY month, p.productID, p.productName
            ) AS monthly
            ORDER BY monthly.month, monthly.total_kg DESC
        """,
    },
]


PICKER_SQL = {
    "select_batch":  "SELECT batchID, batchID FROM RoastingBatch ORDER BY batchID",
    "select_order":  "SELECT orderID, CONCAT(orderID, ' — ', orderDate) FROM SalesOrder ORDER BY orderID",
    "select_client": "SELECT clientID, clientName FROM Client ORDER BY clientName",
}


def fetch_picker_options(kind):
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute(PICKER_SQL[kind])
        return cur.fetchall()


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Coffee Roastery Database")
        self.resize(1100, 750)

        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)

        layout.addWidget(QLabel("<h1>Coffee Roastery Database</h1>"))
        welcome = QLabel(
            "This is our final project for Databases. The database "
            "keeps track of a specialty coffee roastery: from the farms where "
            "the beans are grown, all the way to the wholesale orders we ship "
            "out. Pick one of the 12 questions below, fill in the inputs if any, "
            "and click Run query to see the results. You can also add a new "
            "sales order using the button on the right."
        )
        welcome.setWordWrap(True)
        layout.addWidget(welcome)
        layout.addSpacing(8)

        # the dropdown that shows all 12 of our queries
        layout.addWidget(QLabel("<b>Question:</b>"))
        self.query_box = QComboBox()
        for q in QUERIES:
            self.query_box.addItem(f"#{q['id']}  {q['title']}", q)
        self.query_box.currentIndexChanged.connect(self.rebuild_params)
        layout.addWidget(self.query_box)
        self.param_widget = QWidget()
        self.param_layout = QFormLayout(self.param_widget)
        layout.addWidget(self.param_widget)
        self.param_widgets = {}
        btn_row = QHBoxLayout()
        run_btn = QPushButton("Run query")
        run_btn.clicked.connect(self.run_query)
        new_order_btn = QPushButton("New sales order…")
        new_order_btn.clicked.connect(self.open_new_order)
        btn_row.addWidget(run_btn)
        btn_row.addStretch()
        btn_row.addWidget(new_order_btn)
        layout.addLayout(btn_row)
        layout.addWidget(QLabel("<b>Results:</b>"))
        self.status_label = QLabel("No query run yet.")
        layout.addWidget(self.status_label)
        self.results = QTableWidget()
        self.results.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        layout.addWidget(self.results, stretch=1)
        self.rebuild_params()

    def rebuild_params(self):
        # whenever the user picks a different question, we rebuild the
        # input row to match what that question needs (dropdown, date, etc.)
        while self.param_layout.rowCount() > 0:
            self.param_layout.removeRow(0)
        self.param_widgets = {}

        q = self.query_box.currentData()
        if not q:
            return

        for p in q["params"]:
            kind = p["kind"]
            if kind in PICKER_SQL:
                widget = QComboBox()
                try:
                    for row in fetch_picker_options(kind):
                        widget.addItem(str(row[1]), row[0])
                except mysql.connector.Error as e:
                    QMessageBox.warning(self, "Database error", f"Could not load options: {e}")
            elif kind == "date":
                widget = QDateEdit()
                widget.setCalendarPopup(True)
                widget.setDisplayFormat("yyyy-MM-dd")
                if "start" in p["name"]:
                    widget.setDate(QDate(2025, 1, 1))
                else:
                    widget.setDate(QDate(2025, 12, 31))
            elif kind == "limit":
                widget = QSpinBox()
                widget.setRange(1, 100)
                widget.setValue(10)
            else:
                widget = QLabel("(unsupported)")
            self.param_widgets[p["name"]] = widget
            self.param_layout.addRow(p["label"] + ":", widget)

    def collect_params(self):
        q = self.query_box.currentData()
        values = []
        for p in q["params"]:
            w = self.param_widgets[p["name"]]
            if isinstance(w, QComboBox):
                values.append(w.currentData())
            elif isinstance(w, QDateEdit):
                values.append(w.date().toString("yyyy-MM-dd"))
            elif isinstance(w, QSpinBox):
                values.append(w.value())
        return values

    def run_query(self):
        # gets called when the user clicks Run query.
        # we always open a fresh connection so the results are not cached.
        q = self.query_box.currentData()
        params = self.collect_params()
        try:
            with get_conn() as conn:
                cur = conn.cursor()
                cur.execute(q["sql"], tuple(params))
                rows = cur.fetchall()
                columns = [d[0] for d in cur.description]
        except mysql.connector.Error as e:
            QMessageBox.warning(self, "Query error", str(e))
            return

        # put the rows into the results table
        self.results.clear()
        self.results.setColumnCount(len(columns))
        self.results.setRowCount(len(rows))
        self.results.setHorizontalHeaderLabels(columns)
        for r, row in enumerate(rows):
            for c, val in enumerate(row):
                self.results.setItem(r, c, QTableWidgetItem("" if val is None else str(val)))
        self.results.resizeColumnsToContents()
        self.status_label.setText(f"Query #{q['id']} returned {len(rows)} row(s).")

    def open_new_order(self):
        NewOrderDialog(self).exec()


class NewOrderDialog(QDialog):
    STATUSES = ["Pending", "Confirmed", "Packed", "Shipped", "Delivered"]

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("New sales order")
        self.resize(750, 520)

        try:
            with get_conn() as conn:
                cur = conn.cursor()
                cur.execute("SELECT clientID, clientName FROM Client ORDER BY clientName")
                self.client_rows = cur.fetchall()
                cur.execute("SELECT productID, productName, pricePerKg FROM Product ORDER BY productName")
                self.product_rows = cur.fetchall()
                cur.execute("SELECT clientID, productID, specialUnitPricePerKg FROM ClientPrice")
                self.client_prices = {(r[0], r[1]): float(r[2]) for r in cur.fetchall()}
        except mysql.connector.Error as e:
            QMessageBox.critical(self, "Database error", f"Could not load reference data: {e}")
            self.client_rows, self.product_rows, self.client_prices = [], [], {}

        layout = QVBoxLayout(self)
        form = QFormLayout()

        self.client_box = QComboBox()
        for cid, name in self.client_rows:
            self.client_box.addItem(name, cid)
        self.client_box.currentIndexChanged.connect(self.recompute_all_lines)

        self.date_edit = QDateEdit()
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setDisplayFormat("yyyy-MM-dd")
        self.date_edit.setDate(QDate.currentDate())

        self.status_box = QComboBox()
        self.status_box.addItems(self.STATUSES)

        form.addRow("Client:", self.client_box)
        form.addRow("Order date:", self.date_edit)
        form.addRow("Status:", self.status_box)
        layout.addLayout(form)

        layout.addSpacing(6)
        layout.addWidget(QLabel("<b>Order lines:</b>"))
        self.lines = QTableWidget(0, 4)
        self.lines.setHorizontalHeaderLabels(["Product", "Quantity (kg)", "Unit price", "Line total"])
        self.lines.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.lines, stretch=1)

        line_btns = QHBoxLayout()
        add_btn = QPushButton("+ Add line")
        add_btn.clicked.connect(self.add_line)
        line_btns.addWidget(add_btn)
        line_btns.addStretch()
        layout.addLayout(line_btns)

        bottom = QHBoxLayout()
        bottom.addStretch()
        cancel = QPushButton("Cancel")
        cancel.clicked.connect(self.reject)
        save = QPushButton("Save")
        save.setDefault(True)
        save.clicked.connect(self.save)
        bottom.addWidget(cancel)
        bottom.addWidget(save)
        layout.addLayout(bottom)

        self.add_line()

    def add_line(self):
        r = self.lines.rowCount()
        self.lines.insertRow(r)

        prod_box = QComboBox()
        for pid, name, price in self.product_rows:
            prod_box.addItem(name, (pid, float(price)))
        prod_box.currentIndexChanged.connect(lambda _i, row=r: self.recompute_line(row))
        self.lines.setCellWidget(r, 0, prod_box)

        qty = QDoubleSpinBox()
        qty.setRange(0.01, 100000)
        qty.setDecimals(2)
        qty.setValue(1.0)
        qty.valueChanged.connect(lambda _v, row=r: self.recompute_line(row))
        self.lines.setCellWidget(r, 1, qty)

        self.lines.setCellWidget(r, 2, QLabel("0.00"))
        self.lines.setCellWidget(r, 3, QLabel("0.00"))
        self.recompute_line(r)

    def recompute_line(self, row):
        prod_box = self.lines.cellWidget(row, 0)
        qty = self.lines.cellWidget(row, 1)
        prod_data = prod_box.currentData()
        if prod_data is None:
            return
        pid, default_price = prod_data
        price = self.client_prices.get((self.client_box.currentData(), pid), default_price)
        self.lines.cellWidget(row, 2).setText(f"{price:.2f}")
        self.lines.cellWidget(row, 3).setText(f"{price * qty.value():.2f}")

    def recompute_all_lines(self):
        for r in range(self.lines.rowCount()):
            self.recompute_line(r)

    def save(self):
        # collects the info the user entered and inserts a new SalesOrder
        # plus its OrderLines into the database in one transaction.
        client_id = self.client_box.currentData()
        if not client_id:
            QMessageBox.warning(self, "Missing client", "Please pick a client.")
            return

        # gather each row's product, quantity, and price into a list
        line_data = []
        for r in range(self.lines.rowCount()):
            prod_data = self.lines.cellWidget(r, 0).currentData()
            if prod_data is None:
                continue
            pid, _ = prod_data
            qty = self.lines.cellWidget(r, 1).value()
            unit = float(self.lines.cellWidget(r, 2).text())
            line_data.append((pid, qty, round(unit * qty, 2)))

        if not line_data:
            QMessageBox.warning(self, "No lines", "Please add at least one order line.")
            return

        order_date = self.date_edit.date().toString("yyyy-MM-dd")
        status = self.status_box.currentText()

        try:
            with get_conn() as conn:
                cur = conn.cursor()
                # figure out the next orderID by looking at the biggest one so far
                cur.execute("SELECT COALESCE(MAX(CAST(SUBSTRING(orderID, 2) AS UNSIGNED)), 0) FROM SalesOrder")
                order_id = f"O{int(cur.fetchone()[0]) + 1:04d}"
                cur.execute(
                    "INSERT INTO SalesOrder (orderID, clientID, orderDate, status) VALUES (%s, %s, %s, %s)",
                    (order_id, client_id, order_date, status),
                )
                # same idea for the next lineID
                cur.execute("SELECT COALESCE(MAX(CAST(SUBSTRING(lineID, 2) AS UNSIGNED)), 0) FROM OrderLine")
                next_line_num = int(cur.fetchone()[0]) + 1
                for i, (pid, qty, line_price) in enumerate(line_data):
                    cur.execute(
                        "INSERT INTO OrderLine (lineID, orderID, productID, quantity, linePrice) "
                        "VALUES (%s, %s, %s, %s, %s)",
                        (f"L{next_line_num + i:05d}", order_id, pid, qty, line_price),
                    )
                conn.commit()
        except mysql.connector.Error as e:
            QMessageBox.critical(self, "Database error", f"Could not save order: {e}")
            return

        QMessageBox.information(
            self, "Order created",
            f"Sales order {order_id} created with {len(line_data)} line(s)."
        )
        self.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
