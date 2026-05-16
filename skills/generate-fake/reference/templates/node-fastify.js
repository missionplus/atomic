// Template: Node / Fastify fake server.
//
// Same shape as the Python template — adapt to the surfaces you discovered.

import Fastify from "fastify";
import * as state from "./state.js";

const fastify = Fastify({ logger: true });

// --- Health & admin --------------------------------------------------------

fastify.get("/health", async () => ({ status: "ok", fake: true }));

fastify.post("/__reset", async (_req, reply) => {
  state.reset();
  reply.code(204).send();
});

// --- Example: canned response ---------------------------------------------

fastify.get("/version", async () => ({ version: "1.0.0-fake" }));

// --- Example: transform (echo + synthesise) -------------------------------

fastify.get("/users/:userId", async (req) => {
  const { userId } = req.params;
  return {
    id: userId,
    email: `${userId}@example.com`,
    created_at: "2026-01-01T00:00:00Z",
  };
});

// --- Example: stateful-lite -----------------------------------------------

fastify.post("/orders", async (req) => {
  const body = req.body ?? {};
  const orderId = `ord_${String(state.nextSeq("orders")).padStart(6, "0")}`;
  const record = {
    ...body,
    id: orderId,
    status: "accepted",
    created_at: "2026-01-01T00:00:00Z",
  };
  state.put("orders", orderId, record);
  return record;
});

fastify.get("/orders/:orderId", async (req, reply) => {
  const found = state.get("orders", req.params.orderId);
  if (!found) {
    reply.code(404);
    return { error: "not_found" };
  }
  return found;
});

// --- Error envelope -------------------------------------------------------

fastify.setErrorHandler((err, _req, reply) => {
  reply.code(500).send({ error: "internal_error", message: err.message });
});

const port = Number(process.env.FAKE_PORT ?? 8000);
fastify.listen({ host: "0.0.0.0", port }).catch((err) => {
  fastify.log.error(err);
  process.exit(1);
});
