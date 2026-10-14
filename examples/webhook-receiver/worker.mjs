import pg from 'pg';
import { setTimeout as sleep } from 'node:timers/promises';

if (!process.env.DATABASE_URL) throw new Error('DATABASE_URL is required');
const db = new pg.Pool({ connectionString: process.env.DATABASE_URL });
let stopping = false;
for (const signal of ['SIGTERM', 'SIGINT']) process.once(signal, () => { stopping = true; });

// Multiple workers coordinate with PostgreSQL row locks. Recording the
// audit effect and marking the inbox row are one atomic transaction.
async function processNext() {
  const connection = await db.connect();
  let delivery;
  try {
    await connection.query('BEGIN');
    const pending = await connection.query(
      `SELECT delivery_id, payload FROM bastion_webhook_inbox
       WHERE processed_at IS NULL AND next_attempt_at <= now()
       ORDER BY received_at LIMIT 1 FOR UPDATE SKIP LOCKED`,
    );
    delivery = pending.rows[0];
    if (!delivery) { await connection.query('COMMIT'); return false; }
    const event = delivery.payload.data;
    await connection.query(
      `INSERT INTO bastion_decision_audit
       (event_id, site_id, account_id, action, risk_score, evidence)
       VALUES ($1, $2, $3, $4, $5, $6) ON CONFLICT (event_id) DO NOTHING`,
      [event.id, event.siteId, event.accountId, event.metadata?.action || 'review',
        event.riskScore, JSON.stringify(event.metadata?.signalEvidence || [])],
    );
    await connection.query(
      'UPDATE bastion_webhook_inbox SET processed_at=now(), last_error=NULL WHERE delivery_id=$1',
      [delivery.delivery_id],
    );
    await connection.query('COMMIT');
    return true;
  } catch (error) {
    await connection.query('ROLLBACK');
    if (delivery) {
      await connection.query(
        `UPDATE bastion_webhook_inbox SET attempts=attempts+1,
         last_error=$2, next_attempt_at=now()+interval '30 seconds'
         WHERE delivery_id=$1 AND processed_at IS NULL`,
        [delivery.delivery_id, error.message.slice(0, 500)],
      );
    }
    throw error;
  } finally {
    connection.release();
  }
}

try {
  while (!stopping) {
    try { if (await processNext()) continue; }
    catch (error) { console.error('Webhook processing failed:', error.message); }
    await sleep(500);
  }
} finally {
  await db.end();
}
