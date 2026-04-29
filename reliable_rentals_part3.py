"""
Reliable Rentals - Project Part 3
Implementation of Logical Database Design using embedded SQL (Python + SQLite)

DSC623 - Database Systems for Data Science | Spring 2026
Prof. Vanessa Aguiar
Authors: Christian Hernandez, Gabriella Escobar Cukier, Anastasiya Drandarov

This script:
  Part A. Creates the entire database schema with all integrity constraints from Part 2.
  Part B. Inserts at least 5 tuples into each relation and displays the contents.
  Part C. Executes the 5 user transactions defined in Part 2 (Section C) as SQL queries.
"""

import sqlite3
import pandas as pd

# ---------------------------------------------------------------------------
# Helper utilities
# ---------------------------------------------------------------------------

DB_FILE = "reliable_rentals.db"


def section(title):
    """Print a clearly delimited section header."""
    line = "=" * 78
    print(f"\n{line}\n{title}\n{line}")


def show_table(conn, table):
    """Print all rows of a table with a clean header."""
    df = pd.read_sql_query(f"SELECT * FROM {table};", conn)
    print(f"\n--- {table} ({len(df)} row{'s' if len(df) != 1 else ''}) ---")
    print(df.to_string(index=False) if len(df) else "(empty)")


def show_query(conn, title, sql):
    """Execute a query and print the result with a header."""
    df = pd.read_sql_query(sql, conn)
    print(f"\n--- {title} ({len(df)} row{'s' if len(df) != 1 else ''}) ---")
    print(df.to_string(index=False) if len(df) else "(no results)")
    return df


# ---------------------------------------------------------------------------
# Part A. Create the database schema
# ---------------------------------------------------------------------------

def create_schema(cursor):
    """Drop existing tables and create the schema with all constraints."""

    # Drop in reverse-dependency order so FKs do not block deletion.
    cursor.executescript("""
        DROP TRIGGER IF EXISTS prevent_vehicle_overlap;
        DROP TABLE IF EXISTS HIRE_AGREEMENT;
        DROP TABLE IF EXISTS VEHICLE;
        DROP TABLE IF EXISTS STAFF;
        DROP TABLE IF EXISTS CLIENT;
        DROP TABLE IF EXISTS OUTLET;
    """)

    # OUTLET
    cursor.execute("""
        CREATE TABLE OUTLET (
            outlet_number   INTEGER PRIMARY KEY,
            address         TEXT    NOT NULL UNIQUE,
            phone_number    TEXT    NOT NULL,
            fax_number      TEXT
        );
    """)

    # CLIENT (no FKs — created before tables that reference it)
    cursor.execute("""
        CREATE TABLE CLIENT (
            client_number          INTEGER PRIMARY KEY,
            first_name             TEXT NOT NULL,
            last_name              TEXT NOT NULL,
            home_address           TEXT,
            phone_number           TEXT NOT NULL,
            date_of_birth          TEXT NOT NULL,
            driving_license_number TEXT NOT NULL UNIQUE
        );
    """)

    # STAFF (FK to OUTLET)
    cursor.execute("""
        CREATE TABLE STAFF (
            staff_number        INTEGER PRIMARY KEY,
            first_name          TEXT NOT NULL,
            last_name           TEXT NOT NULL,
            home_address        TEXT,
            home_phone_number   TEXT,
            date_of_birth       TEXT,
            sex                 TEXT CHECK (sex IN ('M', 'F', 'O')),
            date_joined_company TEXT NOT NULL,
            job_title           TEXT NOT NULL,
            salary              REAL NOT NULL CHECK (salary > 0),
            outlet_number       INTEGER NOT NULL,
            FOREIGN KEY (outlet_number) REFERENCES OUTLET(outlet_number)
                ON UPDATE CASCADE
                ON DELETE RESTRICT
        );
    """)

    # VEHICLE (FK to OUTLET)
    cursor.execute("""
        CREATE TABLE VEHICLE (
            registration_number TEXT PRIMARY KEY,
            model               TEXT NOT NULL,
            make                TEXT NOT NULL,
            engine_size         REAL CHECK (engine_size > 0),
            capacity            INTEGER CHECK (capacity > 0),
            current_mileage     INTEGER NOT NULL CHECK (current_mileage >= 0),
            daily_hire_rate     REAL    NOT NULL CHECK (daily_hire_rate > 0),
            outlet_number       INTEGER NOT NULL,
            FOREIGN KEY (outlet_number) REFERENCES OUTLET(outlet_number)
                ON UPDATE CASCADE
                ON DELETE RESTRICT
        );
    """)

    # HIRE_AGREEMENT (FKs to CLIENT, VEHICLE, STAFF)
    cursor.execute("""
        CREATE TABLE HIRE_AGREEMENT (
            hire_number         INTEGER PRIMARY KEY,
            start_date          TEXT NOT NULL,
            expected_end_date   TEXT NOT NULL,
            mileage_before      INTEGER NOT NULL CHECK (mileage_before >= 0),
            mileage_after       INTEGER CHECK (
                                    mileage_after IS NULL OR
                                    mileage_after >= mileage_before
                                ),
            client_number       INTEGER NOT NULL,
            registration_number TEXT    NOT NULL,
            staff_number        INTEGER NOT NULL,

            CHECK (expected_end_date >= start_date),

            FOREIGN KEY (client_number) REFERENCES CLIENT(client_number)
                ON UPDATE CASCADE ON DELETE RESTRICT,

            FOREIGN KEY (registration_number) REFERENCES VEHICLE(registration_number)
                ON UPDATE CASCADE ON DELETE RESTRICT,

            FOREIGN KEY (staff_number) REFERENCES STAFF(staff_number)
                ON UPDATE CASCADE ON DELETE RESTRICT
        );
    """)

    # General constraint from Part 2 D.VI:
    # A vehicle cannot appear in two overlapping active hire agreements.
    cursor.execute("""
        CREATE TRIGGER prevent_vehicle_overlap
        BEFORE INSERT ON HIRE_AGREEMENT
        FOR EACH ROW
        BEGIN
            SELECT
                CASE
                    WHEN EXISTS (
                        SELECT 1 FROM HIRE_AGREEMENT
                        WHERE registration_number = NEW.registration_number
                          AND NOT (
                              NEW.expected_end_date < start_date OR
                              NEW.start_date > expected_end_date
                          )
                    )
                    THEN RAISE(ABORT, 'Vehicle already rented in an overlapping period')
                END;
        END;
    """)

    # Indexes to speed up FK-based joins used in Part C transactions.
    cursor.execute("CREATE INDEX idx_vehicle_outlet ON VEHICLE(outlet_number);")
    cursor.execute("CREATE INDEX idx_staff_outlet  ON STAFF(outlet_number);")
    cursor.execute("CREATE INDEX idx_hire_vehicle  ON HIRE_AGREEMENT(registration_number);")
    cursor.execute("CREATE INDEX idx_hire_client   ON HIRE_AGREEMENT(client_number);")
    cursor.execute("CREATE INDEX idx_hire_staff    ON HIRE_AGREEMENT(staff_number);")


# ---------------------------------------------------------------------------
# Part B. Insert sample data
# ---------------------------------------------------------------------------

def insert_data(cursor):
    """Insert at least 5 tuples into each relation."""

    cursor.executescript("""
        -- OUTLET (5 rows)
        INSERT INTO OUTLET VALUES
            (1, '12 Prairy Ave, Miami, FL, 33137',         '305-305-3333', '305-305-3387'),
            (2, '812 Rosemry Ave, Coral Gables, FL, 33137','305-334-4455', '305-334-4567'),
            (3, '403 Florida St, Miami, FL, 33145',        '305-388-8888', '305-388-8777'),
            (4, '222 Port St, Homestead, FL, 33108',       '786-222-9976', '786-222-9872'),
            (5, 'Sunset Dr, Miami, FL, 33130',             '305-305-5565', '305-305-5531');

        -- STAFF (5 rows)
        INSERT INTO STAFF VALUES
            (237, 'Mary',      'Rosas',    '45 Seaside Rd, Miami, FL 33134',
             '786-837-2776', '1998-07-23', 'F', '2022-01-01', 'Sales Manager',   80000, 1),
            (231, 'Daniel',    'Jackson',  '333 Jefferson Ave, Miami Beach, FL 33139',
             '305-777-1222', '1995-08-22', 'M', '2021-03-01', 'Sales Manager',   81000, 4),
            (112, 'Li',        'Xai',      '1013 Lincoln Ave, Miami, FL 33134',
             '305-888-1115', '2004-05-31', 'M', '2024-01-01', 'Sales Assistant', 55000, 2),
            (76,  'Margarita', 'Diaz',     '3327 Morning Ave, Coral Gables, FL 33133',
             '786-992-3345', '1992-02-20', 'F', '2018-11-18', 'Sales Manager',   85000, 5),
            (45,  'William',   'Bergman',  '20 Pinetree Rd, Miami, FL 33132',
             '305-018-3009', '1993-01-25', 'M', '2024-04-04', 'IT Specialist',   85000, 3);

        -- VEHICLE (5 rows)
        INSERT INTO VEHICLE VALUES
            ('22031', 'Corolla', 'Toyota',  1.5, 5, 12000, 45.00, 4),
            ('11125', 'RAV4',    'Toyota',  2.0, 5, 30000, 55.00, 1),
            ('11329', 'Fusion',  'Ford',    1.8, 5, 22000, 45.00, 3),
            ('16645', 'Rogue',   'Nissan',  2.0, 5, 28000, 60.00, 2),
            ('28834', 'X5',      'BMW',     2.0, 5, 10000, 80.00, 5);

        -- CLIENT (5 rows)
        INSERT INTO CLIENT VALUES
            (1398, 'Jim',      'Thompson',  '504 Pond Ave, Atlanta, GA, 43167',
             '405-277-3331', '1990-03-08', 'DL011784763'),
            (101,  'Allie',    'Rivas',     '430 Stonehill St, Chicago, IL, 21117',
             '205-112-8440', '1982-02-01', 'DL361047299'),
            (281,  'Marianna', 'Prado',     '4490 Roosevelt Rd, Portland, OR, 12352',
             '874-327-3323', '1975-01-29', 'DL837718293'),
            (1882, 'Joye',     'Figueroa',  '2226 Lakeview Ave, Atlanta, GA, 43134',
             '405-232-3422', '2005-04-19', 'DL3892661009'),
            (127,  'Ron',      'Kelly',     '33392 Sunrise St, Birmingham, AL, 35887',
             '509-234-3111', '1977-10-12', 'DL9277771662');

        -- HIRE_AGREEMENT (5 rows; mix of completed and ongoing rentals)
        --   Hires 1227, 399, 1118, 20: completed (mileage_after recorded)
        --   Hire  635:                 ongoing  (mileage_after = NULL)
        INSERT INTO HIRE_AGREEMENT VALUES
            (1227, '2022-02-03', '2022-02-05', 12000, 12065, 1398, '11125', 231),
            (399,  '2024-04-15', '2024-04-21', 18100, 18150, 1882, '11329', 112),
            (635,  '2026-04-03', '2026-04-05', 8210,  NULL,  127,  '28834', 237),
            (1118, '2025-12-15', '2025-12-20', 10350, 10500, 101,  '22031', 76),
            (20,   '2026-01-03', '2026-01-05', 21560, 21600, 101,  '11329', 76);
    """)


# ---------------------------------------------------------------------------
# Part C. Execute the 5 user transactions from Part 2 (Section C)
# ---------------------------------------------------------------------------

def run_transactions(conn):
    """Execute the five Part 2 transactions as SQL queries."""

    # Transaction 1 -----------------------------------------------------------
    # Which vehicles are currently stored at Outlet 3, and what is their daily
    # hire rate? — entities: Outlet -> Vehicle
    show_query(conn, "Transaction 1 - Vehicles at Outlet 3", """
        SELECT
            v.registration_number,
            v.make,
            v.model,
            v.daily_hire_rate
        FROM VEHICLE v
        WHERE v.outlet_number = 3
        ORDER BY v.registration_number;
    """)

    # Transaction 2 -----------------------------------------------------------
    # Show all hire agreements signed by client 101, including the vehicle
    # rented and the hire dates. — entities: Client -> HireAgreement -> Vehicle
    show_query(conn, "Transaction 2 - Hire history for client 101", """
        SELECT
            h.hire_number,
            c.first_name || ' ' || c.last_name AS client_name,
            h.start_date,
            h.expected_end_date,
            h.registration_number,
            v.make,
            v.model,
            h.mileage_before,
            h.mileage_after
        FROM HIRE_AGREEMENT h
        JOIN CLIENT  c ON h.client_number       = c.client_number
        JOIN VEHICLE v ON h.registration_number = v.registration_number
        WHERE h.client_number = 101
        ORDER BY h.start_date;
    """)

    # Transaction 3 -----------------------------------------------------------
    # List all ongoing hires (not yet returned), with the client's name and
    # the outlet where the vehicle is based.
    # — entities: HireAgreement -> Client, HireAgreement -> Vehicle -> Outlet
    show_query(conn, "Transaction 3 - Ongoing hires (not yet returned)", """
        SELECT
            h.hire_number,
            c.first_name || ' ' || c.last_name AS client_name,
            h.start_date,
            h.expected_end_date,
            v.registration_number,
            v.make,
            v.model,
            o.outlet_number,
            o.address AS outlet_address
        FROM HIRE_AGREEMENT h
        JOIN CLIENT  c ON h.client_number       = c.client_number
        JOIN VEHICLE v ON h.registration_number = v.registration_number
        JOIN OUTLET  o ON v.outlet_number       = o.outlet_number
        WHERE h.mileage_after IS NULL
        ORDER BY h.start_date;
    """)

    # Transaction 4 -----------------------------------------------------------
    # List all clients who have ever rented a vehicle belonging to Outlet 5,
    # along with the vehicle they rented and the hire dates.
    # — entities: Outlet -> Vehicle -> HireAgreement -> Client
    show_query(conn, "Transaction 4 - Clients who rented vehicles from Outlet 5", """
        SELECT
            c.client_number,
            c.first_name || ' ' || c.last_name AS client_name,
            c.phone_number,
            v.registration_number,
            v.make,
            v.model,
            h.start_date,
            h.expected_end_date,
            h.mileage_before,
            h.mileage_after
        FROM HIRE_AGREEMENT h
        JOIN CLIENT  c ON h.client_number       = c.client_number
        JOIN VEHICLE v ON h.registration_number = v.registration_number
        WHERE v.outlet_number = 5
        ORDER BY h.start_date;
    """)

    # Transaction 5 -----------------------------------------------------------
    # What is the total charge for hire agreement 20, based on the number of
    # days and the vehicle's daily hire rate? — entities: HireAgreement -> Vehicle
    show_query(conn, "Transaction 5 - Total charge for hire agreement 20", """
        SELECT
            h.hire_number,
            v.registration_number,
            v.make,
            v.model,
            h.start_date,
            h.expected_end_date,
            v.daily_hire_rate,
            (julianday(h.expected_end_date) - julianday(h.start_date) + 1)
                AS number_of_days,
            (julianday(h.expected_end_date) - julianday(h.start_date) + 1)
                * v.daily_hire_rate AS total_charge,
            (h.mileage_after - h.mileage_before) AS distance_driven
        FROM HIRE_AGREEMENT h
        JOIN VEHICLE v ON h.registration_number = v.registration_number
        WHERE h.hire_number = 20;
    """)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    conn = sqlite3.connect(DB_FILE)
    conn.execute("PRAGMA foreign_keys = ON;")
    cursor = conn.cursor()

    section("PART A. CREATE SCHEMA")
    create_schema(cursor)
    conn.commit()
    print("Schema created successfully with 5 tables, 1 trigger, and 5 indexes.")

    section("PART B. INSERT DATA AND DISPLAY TABLES")
    insert_data(cursor)
    conn.commit()
    for table in ("OUTLET", "STAFF", "VEHICLE", "CLIENT", "HIRE_AGREEMENT"):
        show_table(conn, table)

    section("PART C. USER TRANSACTIONS (queries from Part 2.C)")
    run_transactions(conn)

    conn.close()
    print("\nDatabase connection closed successfully.")


if __name__ == "__main__":
    main()
