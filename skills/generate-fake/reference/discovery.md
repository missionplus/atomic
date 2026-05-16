# Discovery — finding every integration surface

This document defines the search order. Follow it top to bottom; stop early only when you are confident you've enumerated every external touchpoint.

## Order of precedence

```
1. Specifications      (highest signal, most reliable)
2. Handler / routing source code
3. Data-access layer (models, repositories, migrations)
4. Outbound clients   (HTTP clients, queue publishers, gRPC stubs)
5. Infra-as-code      (docker-compose, k8s, terraform, helm)
6. Integration tests
7. Config / env loading
```

Cross-reference between sources — a surface mentioned in *any* of these counts.

## 1. Specifications

Look for, in order:

| File pattern | What it tells you |
|---|---|
| `openapi.{yaml,yml,json}`, `swagger.{yaml,json}`, `api.{yaml,yml}` | Inbound HTTP API |
| `asyncapi.{yaml,json}` | Inbound/outbound queue messages with schemas |
| `*.proto` | gRPC services & messages |
| `*.graphql`, `schema.gql`, `schema.graphql` | GraphQL surface |
| `*.avsc`, `*.avro`, `*.thrift` | Message schemas |
| Postman collections, Insomnia exports | Quasi-specs; useful but treat as hints |

If multiple specs exist, parse all of them. Record each spec path + SHA-256 in the manifest.

## 2. Handler / routing source

Match by language:

**Python**
- FastAPI: `@app.get(...)`, `@router.post(...)`, `APIRouter`, `include_router`.
- Flask: `@app.route(...)`, `@blueprint.route(...)`.
- Django: `urls.py`, `urlpatterns`, `path(...)`, `re_path(...)`, viewsets.

**Node / TS**
- Express: `app.get/post/put/delete/patch/use`, `router.METHOD`.
- Fastify: `fastify.get/post/...`, `fastify.register`.
- NestJS: `@Controller`, `@Get`, `@Post`, etc.
- Koa, Hapi, Hono — similar patterns.

**Java**
- Spring: `@RestController`, `@RequestMapping`, `@GetMapping`, etc.
- JAX-RS: `@Path`, `@GET`, `@POST`.

**Go**
- `net/http`: `http.HandleFunc`, mux registrations.
- `gin.Engine.GET/POST/...`, `chi.Router`, `echo.Echo.GET/...`.

**C# / .NET**
- `[HttpGet]`, `[HttpPost]`, `[Route]`, minimal-API `app.MapGet`.

**Ruby on Rails**
- `config/routes.rb` — `resources`, `get`, `post`.

For each handler, record: method, path, request schema (if typed), response schema (if typed), and the file:line.

## 3. Data-access layer

- ORM models: SQLAlchemy `Base` subclasses, TypeORM/Prisma schemas, GORM structs, ActiveRecord models, Entity Framework `DbContext`, JPA `@Entity`.
- Raw SQL: migration files (`migrations/`, `alembic/`, `db/migrate/`, `prisma/migrations/`, `*.sql`).
- NoSQL: collection names in code (`db.collection("users")`), DynamoDB table refs, Firestore paths.

You don't usually fake the database directly (apps connect via env-supplied DSN). But you *do* record:

- Which tables/collections exist.
- Which the app reads vs writes.

That informs whether the fake needs SQLite stand-in tables or can ignore the DB entirely.

## 4. Outbound clients

These are surfaces the app *calls* — you'll generally *not* fake these (the consuming app's tests should), but you must enumerate them so the fragility report is complete.

- HTTP clients: `requests`, `httpx`, `aiohttp`, `axios`, `node-fetch`, `RestTemplate`, `WebClient`, `OkHttpClient`.
- SDKs: `boto3`, AWS SDK v3, `google-cloud-*`, `stripe`, `twilio`, etc.
- Message producers: `KafkaProducer`, `kafkajs.producer`, `pika.BasicPublish`, `@aws-sdk/client-sqs.SendMessageCommand`.
- gRPC stubs.

Record each outbound call: target (host/topic), method, schema if known, source file:line.

## 5. Infra-as-code

Tells you which queues, topics, brokers, buckets, and external services are actually wired up in deployment.

- `docker-compose*.yml` — service names give you queues, DBs, caches.
- `k8s/`, `helm/`, `kustomize/` — env vars and Services reveal endpoints.
- `terraform/`, `pulumi/`, `cdk/` — managed resources (SQS queues, S3 buckets, RDS, etc.).
- `.env`, `.env.example`, `config/*.yaml` — every URL and broker the app reads at startup.

Cross-check this against what you found in step 2/3/4. Anything wired up in infra but not present in code is suspicious — flag it.

## 6. Integration tests

`tests/integration/`, `*.test.ts`, `*.spec.py`, etc. Tests often instantiate exactly the inbound and outbound calls you care about. Use them as ground truth and as example payloads.

## 7. Config / env loading

The `Settings`/`Config` class (e.g. `pydantic_settings.BaseSettings`, NestJS `ConfigModule`, Spring `@ConfigurationProperties`) lists every external URL/broker/key the app uses. Treat it as a checklist.

## Output of discovery

When you finish, you should have a single in-memory table like this, ready to feed into the manifest:

| id | kind | direction | path/topic/table | request_schema | response_schema | source_files | confidence |
|---|---|---|---|---|---|---|---|
| h1 | http | inbound | `GET /users/{id}` | — | `User` | `routes/users.py:14` | spec |
| h2 | http | inbound | `POST /orders` | `CreateOrder` | `Order` | `routes/orders.py:22` | code |
| q1 | queue | inbound | topic `payments.received` | `PaymentReceived` | — | `consumers/payments.py:9` | code |
| q2 | queue | outbound | topic `notifications.email` | `EmailEvent` | — | `services/notify.py:30` | code |
| g1 | grpc | inbound | `Inventory.GetItem` | `GetItemRequest` | `Item` | `proto/inventory.proto` | spec |
| db1 | db | — | table `users` | — | — | `models/user.py:5` | code |
| out1 | external_http | outbound | `https://api.stripe.com/v1/charges` | — | — | `payments/stripe_client.py:8` | code |

`confidence` is `spec` (came from a spec file), `code` (inferred from source), or `infer` (assembled from multiple weak signals — flag these in the fragility report).
