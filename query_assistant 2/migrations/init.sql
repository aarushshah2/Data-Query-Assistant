-- ============================================================
-- Intelligent Query Assistant - Database Initialization
-- Run: psql -U <user> -d <db> -f migrations/init.sql
-- ============================================================

-- ── Leads ────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS leads (
    id          SERIAL PRIMARY KEY,
    first_name  VARCHAR(100),
    last_name   VARCHAR(100),
    email       VARCHAR(255),
    phone       VARCHAR(30),
    state       VARCHAR(50),
    city        VARCHAR(100),
    status      VARCHAR(50) DEFAULT 'new',   -- new | contacted | qualified | lost
    source      VARCHAR(100),                -- web | referral | ad | cold_call
    assigned_to VARCHAR(100),
    created_at  TIMESTAMPTZ DEFAULT NOW(),
    updated_at  TIMESTAMPTZ DEFAULT NOW()
);

-- ── Customers ─────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS customers (
    id              SERIAL PRIMARY KEY,
    first_name      VARCHAR(100),
    last_name       VARCHAR(100),
    email           VARCHAR(255) UNIQUE,
    phone           VARCHAR(30),
    state           VARCHAR(50),
    city            VARCHAR(100),
    plan            VARCHAR(50),             -- basic | pro | enterprise
    monthly_value   NUMERIC(10,2),
    signup_date     DATE,
    is_active       BOOLEAN DEFAULT TRUE,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

-- ── Vehicles ──────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS vehicles (
    id              SERIAL PRIMARY KEY,
    vin             VARCHAR(17) UNIQUE,
    make            VARCHAR(100),
    model           VARCHAR(100),
    year            INTEGER,
    color           VARCHAR(50),
    status          VARCHAR(50),             -- running | not_running | maintenance | sold
    mileage         INTEGER,
    customer_id     INTEGER REFERENCES customers(id),
    last_service    DATE,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

-- ── Deals ─────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS deals (
    id              SERIAL PRIMARY KEY,
    lead_id         INTEGER REFERENCES leads(id),
    customer_id     INTEGER REFERENCES customers(id),
    sales_rep       VARCHAR(100),
    deal_value      NUMERIC(12,2),
    stage           VARCHAR(50),             -- prospecting | proposal | negotiation | closed_won | closed_lost
    close_date      DATE,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

-- ── Audit Log (restricted - blocked from user queries) ────────
CREATE TABLE IF NOT EXISTS query_logs (
    id              SERIAL PRIMARY KEY,
    user_question   TEXT,
    generated_sql   TEXT,
    validation_passed BOOLEAN,
    execution_time_ms NUMERIC(10,2),
    row_count       INTEGER,
    error_message   TEXT,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

-- ── Indexes ───────────────────────────────────────────────────
CREATE INDEX IF NOT EXISTS idx_leads_state       ON leads(state);
CREATE INDEX IF NOT EXISTS idx_leads_created     ON leads(created_at);
CREATE INDEX IF NOT EXISTS idx_leads_status      ON leads(status);
CREATE INDEX IF NOT EXISTS idx_customers_signup  ON customers(signup_date);
CREATE INDEX IF NOT EXISTS idx_vehicles_status   ON vehicles(status);
CREATE INDEX IF NOT EXISTS idx_deals_sales_rep   ON deals(sales_rep);

-- ── Sample Data ───────────────────────────────────────────────

INSERT INTO leads (first_name, last_name, email, state, city, status, source, assigned_to, created_at) VALUES
('Alice',   'Johnson',  'alice@email.com',   'Texas',      'Austin',      'qualified',  'web',       'Bob Smith',   NOW() - INTERVAL '2 days'),
('Carlos',  'Martinez', 'carlos@email.com',  'Texas',      'Houston',     'new',        'referral',  'Jane Doe',    NOW() - INTERVAL '1 day'),
('Diana',   'Park',     'diana@email.com',   'California', 'Los Angeles', 'contacted',  'ad',        'Bob Smith',   NOW() - INTERVAL '5 days'),
('Ethan',   'Brown',    'ethan@email.com',   'Texas',      'Dallas',      'lost',       'cold_call', 'Jane Doe',    NOW() - INTERVAL '10 days'),
('Fiona',   'Chen',     'fiona@email.com',   'New York',   'New York',    'new',        'web',       'Bob Smith',   NOW() - INTERVAL '3 days'),
('George',  'Wilson',   'george@email.com',  'Florida',    'Miami',       'qualified',  'referral',  'Jane Doe',    NOW() - INTERVAL '6 days'),
('Hannah',  'Lee',      'hannah@email.com',  'Texas',      'San Antonio', 'new',        'web',       'Bob Smith',   NOW() - INTERVAL '4 days'),
('Ivan',    'Petrov',   'ivan@email.com',    'Illinois',   'Chicago',     'contacted',  'ad',        'Jane Doe',    NOW() - INTERVAL '8 days'),
('Julia',   'Adams',    'julia@email.com',   'Texas',      'Austin',      'qualified',  'referral',  'Bob Smith',   NOW() - INTERVAL '1 day'),
('Kevin',   'Scott',    'kevin@email.com',   'California', 'San Diego',   'new',        'web',       'Jane Doe',    NOW() - INTERVAL '2 days'),
('Laura',   'White',    'laura@email.com',   'Texas',      'Houston',     'contacted',  'cold_call', 'Bob Smith',   NOW() - INTERVAL '7 days'),
('Mike',    'Taylor',   'mike@email.com',    'Ohio',       'Columbus',    'lost',       'ad',        'Jane Doe',    NOW() - INTERVAL '15 days'),
('Nina',    'Garcia',   'nina@email.com',    'Texas',      'Dallas',      'new',        'web',       'Bob Smith',   NOW() - INTERVAL '3 days'),
('Oscar',   'Harris',   'oscar@email.com',   'Washington', 'Seattle',     'qualified',  'referral',  'Jane Doe',    NOW() - INTERVAL '9 days'),
('Paula',   'Clark',    'paula@email.com',   'Florida',    'Orlando',     'new',        'web',       'Bob Smith',   NOW() - INTERVAL '2 days')
ON CONFLICT DO NOTHING;

INSERT INTO customers (first_name, last_name, email, state, city, plan, monthly_value, signup_date, is_active) VALUES
('Alice',  'Johnson',  'alice.c@email.com',  'Texas',      'Austin',      'pro',        299.00, DATE_TRUNC('month', NOW())::DATE,              TRUE),
('Bob',    'Smith',    'bob.c@email.com',    'California', 'Los Angeles', 'enterprise', 999.00, (DATE_TRUNC('month', NOW()) - INTERVAL '1 month')::DATE, TRUE),
('Carol',  'Davis',    'carol.c@email.com',  'New York',   'New York',    'basic',      49.00,  (NOW() - INTERVAL '5 days')::DATE,             TRUE),
('Dan',    'Moore',    'dan.c@email.com',    'Texas',      'Houston',     'pro',        299.00, (DATE_TRUNC('month', NOW()) - INTERVAL '2 months')::DATE, FALSE),
('Eva',    'Taylor',   'eva.c@email.com',    'Florida',    'Miami',       'basic',      49.00,  (NOW() - INTERVAL '2 days')::DATE,             TRUE),
('Frank',  'Anderson', 'frank.c@email.com',  'Illinois',   'Chicago',     'enterprise', 999.00, DATE_TRUNC('month', NOW())::DATE,              TRUE),
('Grace',  'Thomas',   'grace.c@email.com',  'Texas',      'Dallas',      'pro',        299.00, (NOW() - INTERVAL '10 days')::DATE,            TRUE),
('Henry',  'Jackson',  'henry.c@email.com',  'Ohio',       'Columbus',    'basic',      49.00,  (DATE_TRUNC('month', NOW()) - INTERVAL '3 months')::DATE, TRUE)
ON CONFLICT DO NOTHING;

INSERT INTO vehicles (vin, make, model, year, color, status, mileage, customer_id, last_service) VALUES
('1HGCM82633A123456', 'Honda',      'Accord',    2020, 'Blue',   'running',      45000, 1, '2024-11-01'),
('2T1BURHE0JC987654', 'Toyota',     'Corolla',   2019, 'White',  'not_running',  78000, 2, '2024-08-15'),
('3VWFE21C04M000111', 'Volkswagen', 'Jetta',     2021, 'Black',  'maintenance',  30000, 3, '2025-01-10'),
('1FTFW1ET5DKE22222', 'Ford',       'F-150',     2018, 'Red',    'running',      92000, 4, '2024-12-01'),
('5NPE24AF6FH333333', 'Hyundai',    'Sonata',    2022, 'Silver', 'running',      18000, 5, '2025-02-01'),
('WBAEV53402KM44444', 'BMW',        '3 Series',  2023, 'Gray',   'not_running',  5000,  6, '2024-07-20'),
('JN1AZ4EH2FM555555', 'Nissan',     'Maxima',    2017, 'Green',  'sold',         110000,7, '2024-06-15'),
('1G1ZT53806F666666', 'Chevrolet',  'Malibu',    2020, 'Blue',   'running',      55000, 8, '2025-01-25'),
('3GNFK16307G777777', 'Chevrolet',  'Tahoe',     2016, 'White',  'not_running',  140000,1, '2023-12-01'),
('2FMDK3GC6BB888888', 'Ford',       'Edge',      2021, 'Black',  'maintenance',  40000, 2, '2025-02-10')
ON CONFLICT DO NOTHING;

INSERT INTO deals (lead_id, customer_id, sales_rep, deal_value, stage, close_date, created_at) VALUES
(1, 1, 'Bob Smith',  12000.00, 'closed_won',  '2025-01-15', NOW() - INTERVAL '30 days'),
(3, 2, 'Jane Doe',   45000.00, 'closed_won',  '2025-01-20', NOW() - INTERVAL '25 days'),
(6, 3, 'Bob Smith',   2500.00, 'closed_won',  '2025-02-01', NOW() - INTERVAL '15 days'),
(2, NULL,'Jane Doe',  8000.00, 'proposal',    NULL,          NOW() - INTERVAL '5 days'),
(5, NULL,'Bob Smith', 15000.00,'negotiation', NULL,          NOW() - INTERVAL '3 days'),
(7, 4, 'Jane Doe',   18000.00, 'closed_won',  '2025-01-30', NOW() - INTERVAL '20 days'),
(9, 5, 'Bob Smith',   3500.00, 'closed_lost', '2025-02-05', NOW() - INTERVAL '10 days'),
(10,6, 'Jane Doe',   75000.00, 'closed_won',  '2025-02-10', NOW() - INTERVAL '8 days')
ON CONFLICT DO NOTHING;
