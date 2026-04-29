# Reliable Rentals — Database Project

**DSC623 — Database Systems for Data Science | Spring 2026**
University of Miami | Prof. Vanessa Aguiar

**Group members:** Christian Hernandez, Gabriella Escobar Cukier, Anastasiya Drandarov

---

## About the project

Reliable Rentals is a fictional vehicle-rental company. This repository contains the full database design and implementation for the company, developed in three parts:

| Part | Deliverable | Description |
|------|-------------|-------------|
| 1 | Conceptual Design | Identified entities, relationships, multiplicity constraints, attributes, and primary keys. Produced the conceptual E-R diagram. |
| 2 | Logical Design | Derived the relational schema with foreign keys, validated it through 3NF normalization, defined integrity constraints, and produced the logical E-R diagram. |
| 3 | Implementation | Built the database in Python + SQLite using embedded SQL. Created the schema, populated it with sample data, and implemented the five user transactions defined in Part 2. |

---

## Repository structure

```
reliable-rentals/
├─ README.md                    This file
├─ part1_conceptual_design/     Part 1 report and conceptual ER diagram
├─ part2_logical_design/        Part 2 report and logical ER diagram (Word + PowerPoint)
└─ part3_implementation/        reliable_rentals_part3.py and Part 3 report
```

---

## How to run the implementation (Part 3)

### Requirements

- Python 3.8 or higher
- `sqlite3` (included with Python)
- `pandas`

Install pandas if needed:

```
pip install pandas
```

### Run

```
cd part3_implementation
python reliable_rentals_part3.py
```

The script is self-contained and idempotent — each run drops existing tables and recreates `reliable_rentals.db` from scratch in the working directory.

### What the script does

- **Part A.** Creates 5 tables (OUTLET, CLIENT, STAFF, VEHICLE, HIRE_AGREEMENT) with all integrity constraints from Part 2.D: primary keys, foreign keys (with `ON DELETE RESTRICT` and `ON UPDATE CASCADE`), unique constraints on alternate keys, NOT NULL constraints on required fields, CHECK constraints on attribute domains, and a BEFORE INSERT trigger that prevents overlapping rentals on the same vehicle.
- **Part B.** Inserts 5 sample rows into each table and prints the contents.
- **Part C.** Executes the 5 user transactions defined in Part 2.C as SQL queries and prints the results.

---

## Design notes

- **Normalization:** All five tables are in 3NF. Full normalization steps and functional dependencies are documented in the Part 2 report.
- **Multiplicity:** Notation `1..1`, `1..*`, `0..*` consistent with Part 1. See the logical E-R diagram in `part2_logical_design/`.
- **Trigger for general constraint:** The rule "a vehicle cannot appear in two overlapping active hire agreements" cannot be expressed as a CHECK clause because it spans rows. It is implemented as the trigger `prevent_vehicle_overlap`.
- **Indexes:** Created on every foreign key column to speed up the JOIN-heavy transactions in Part C.
