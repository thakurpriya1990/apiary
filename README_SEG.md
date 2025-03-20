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


