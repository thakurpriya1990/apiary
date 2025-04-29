# CREATE DB EXPORT
### EXCLUDE Reversion and add schema only for reversion
NOTE: normally for PROD you would not exclude the reversion tables as in the command below. But for DEV work, these can be excluded to speed up DB backup and restore.
```
pg_dump -U ledger_prod -W --exclude-table='django_cron*' --exclude-table='reversion_revision' --exclude-table='reversion_version' -t 'disturbance_*' -t 'accounts_*' -t 'address_*' -t 'analytics_*' -t 'auth_*' -t 'django_*' -t 'taggit_*' -Fc ledger_prod -h <db_hostname> -p 5432 > /dbdumps/dumps/das_seg_tables_18March2025.sql

### Append empty reversion tables
pg_dump -U ledger_prod -W --schema-only -t reversion_revision -t reversion_version ledger_prod -h <db_hostname> -p 5432 >> /dbdumps/dumps/das_seg_tables_26Feb2025.sql
```
# TO RESTORE to DB  das_seg_dev_orig
```
psql -U das_dev das_seg_dev_orig -h localhost -W <  das_seg_tables_26Feb2025.sql
```

# Create a working copy DB (or use the orig)
``` 
psql
> create database das_seg_dev template das_seg_dev_orig owner das_dev;
```

# Update disturbance.env DATABASE_URL with DB das_seg_dev2
```
...
DATABASE_URL=postgis://das_dev:<passwd>@172.17.0.1:25432/das_seg_dev
...

```

# Update pip version to 24.0

# Run migrations
```
./manage_ds.py migrate disturbance
```

# Delete the Apiary Proposal Types
deleted the Apiary proposal type in Admin (via Django Admin) - those with blank application_name (and v1)





# Segregation Steps for Disturbance

# Step 1: export disturbance tables and reversion schema from ledger
### EXCLUDE Reversion and add schema only for reversion
NOTE: normally for PROD you would not exclude the reversion tables as in the command below. But for DEV work, these can be excluded to speed up DB backup and restore.
```

Run pg_dump on the ledger database.

`pg_dump -U ledger_prod -W --exclude-table='django_cron*' --exclude-table='reversion_revision' --exclude-table='reversion_version' -t 'disturbance_*' -t 'accounts_*' -t 'address_*' -t 'analytics_*' -t 'auth_*' -t 'django_*' -t 'taggit_*' -Fc ledger_prod -h <db_hostname> -p 5432 > /dbdumps/dumps/das_seg_tables_DDMMYYYY.sql

### Append empty reversion tables
`pg_dump -U ledger_prod -W --schema-only -t reversion_revision -t reversion_version ledger_prod -h <db_hostname> -p 5432 >> /dbdumps/dumps/reversion_schema_das_seg_tables_DDMMYYYY.sql
```

# Step 2: create new disturbance database

As a postgres admin user (`su postgres` then `psql`) create the new disturbance database.
```

`CREATE DATABASE das_dev;`

`CREATE USER das_dev WITH PASSWORD 'password';`

`GRANT ALL ON DATABASE das_dev to das_dev;`

`\c das_dev`

`create extension postgis;`

`GRANT ALL ON ALL TABLES IN SCHEMA public TO das_dev;`

`GRANT ALL ON SCHEMA public TO das_dev;`
```

# Step 3: to restore exported tables in to new DB disturbance
```
psql -U das_dev das_dev -h localhost -W <  das_seg_tables_DDMMYYYY.sql

psql -U das_dev das_dev -h localhost -W <  reversion_schema_das_seg_tables_DDMMYYYY.sql
```

# Step 4: Create a working copy DB (or use the orig)
``` 
psql
> create database das_seg_dev template das_dev owner das_dev;
```

# Step 5: Update environment variable with new database url (and other variables)

Update the environment variables:

- DATABASE_URL=postgis://das_dev:<passwd>@172.17.0.1:15432/das_seg_dev
- ENABLE_DJANGO_LOGIN=True

# Step 6: Update python version to 3.12.3

# Step 7: Update pip version to 24.0

# Step 8: Install pip modules:
```
pip install -r requirements.txt
```

# Step 8: Run all other migrations
```
./manage_ds.py migrate disturbance
```

# Step 9: Delete the Apiary Proposal Types

delete the Apiary proposal type in Admin (via Django Admin) - those with blank application_name (and v1)

# Step 10: Follow the steps for django-cron missing table if gives error

# Step 11: Follow the steps to dump the scheme questions data if necessary

# Step 12: Change the env variables for kmi to kb


