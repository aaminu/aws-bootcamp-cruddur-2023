# Week 4 — Postgres and RDS
```bash
$ aws rds create-db-instance \
  --db-instance-identifier cruddur-db-instance \
  --db-instance-class db.t3.micro \
  --engine postgres \
  --engine-version  14.6 \
  --master-username ${POSTGRES_MASTER_USERNAME} \
  --master-user-password ${POSTGRES_MASTER_PASSWORD} \
  --allocated-storage 20 \
  --availability-zone "${AWS_DEFAULT_REGION}a" \
  --backup-retention-period 0 \
  --port ${POSTGRES_PORT} \
  --no-multi-az \
  --db-name cruddur \
  --storage-type gp2 \
  --publicly-accessible \
  --storage-encrypted \
  --enable-performance-insights \
  --performance-insights-retention-period 7 \
  --no-deletion-protection
```

```bash
psql cruddur < db/schema.sql -h localhost -U postgres
```

postgresql://[username[:password]@][netloc][:port][/dbname][?param1=value1&...]

export CONNECTION_URL="postgresql://postgres:password@localhost:5432/cruddur"
gp env CONNECTION_URL=$CONNECTION_URL

export PROD_DB_ENDPOINT = <my-endpoint>
gp env PROD_DB_ENDPOINT=$PROD_DB_ENDPOINT 
export PROD_CONNECTION_URL = "postgresql://${POSTGRES_MASTER_USERNAME}:${POSTGRES_MASTER_PASSWORD}@${PROD_DB_ENDPOINT}:${POSTGRES_PORT}/cruddur"
 