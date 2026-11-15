# Database Backup and Restore

## Backup

pg_dump -U aquamedi -d aquamedi_db > backup.sql

## Restore

psql -U aquamedi -d aquamedi_db < backup.sql

## Notes

Test in disposable database only. Never run against production without approval.
