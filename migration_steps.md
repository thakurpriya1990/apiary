## Step 1: Create a new database
```
CREATE DATABASE apiary_dev;
CREATE USER apiary_dev WITH PASSWORD '<password>';
GRANT ALL PRIVILEGES ON DATABASE "apiary_dev" to apiary_dev;
\c apiary_dev
create extension postgis;
GRANT ALL ON ALL TABLES IN SCHEMA public TO apiary_dev;
GRANT ALL ON SCHEMA public TO apiary_dev;
```

## Step 2: Dump data and reversion schema from the ledger_prod
```
pg_dump -U ledger_prod -W --exclude-table='django_cron*' -t 'disturbance_*' -t 'django_*' -t 'taggit_*' -t 'auth_group' -t 'auth_permission' -t 'accounts_document' ledger_prod -h <host> > /tmp/apiary_ledger_tables_YYYYMMDD.sql
pg_dump --schema-only -U ledger_prod -W -t 'reversion_*' -h <host> > /tmp/reversion_schema_apiary_ledger_tables.sql
```
Enter password for the ledger_prod database

## Step 3: Import dumped data and reversion schema into newly created database
```
psql -U apiary_dev apiary_dev -W -h <host> < /tmp/apiary_ledger_tables_YYYYMMDD.sql
psql -U apiary_dev apiary_dev -W -h <host> < /tmp/reversion_schema_apiary_ledger_tables.sql
```
Enter password for the apiary_dev database

## Step 4: Fix and Apply migrations
### 1. Create copy of table: django_migrations
```
CREATE TABLE django_migrations_temp AS SELECT * from django_migrations;
```
### 2. Delete migrations in order to apply ledger_api_client migrations
```
delete from django_migrations where id > 11;
```
### 3. Apply ledger_api_client migrations
```
python manage_ds.py migrate ledger_api_client
```
### 4. Reinsert the migrations that were deleted in the Step 4-2
```
insert into django_migrations (id,app,name,applied) select * from  django_migrations_temp  where id > 11;
```
### 5. Delete django cron migrations so they can be created from initial migration
```
delete from django_migrations where app = 'django_cron';
```
### 6. Apply other migrations
```
./manage_ds.py migrate admin
./manage_ds.py migrate django_cron
./manage_ds.py migrate disturbance
./manage_ds.py migrate
```

### 7.  Fake migrations
```
./manage_ds.py migrate 0295_proposal_prefill_requested --fake
./manage_ds.py migrate disturbance 
(To apply 0296 migration)
./manage_ds.py migrate disturbance 0297_apiarysite_exempt_from_radius_restriction --fake
```



