import express from 'express';
import pg from 'pg';
import { verifyWebhook } from '@bastionsecurity/sdk';

const secret = process.env.BASTION_WEBHOOK_SECRET;
if (!secret || !process.env.DATABASE_URL) {
  throw new Error('BASTION_WEBHOOK_SECRET and DATABASE_URL are required');
}
const db = new pg.Pool({ connectionString: process.env.DATABASE_URL });
const app = express();

// Register the raw-body route BEFORE any express.json() middleware.
app.post('/webhooks/bastion', express.raw({ type: 'application/json', limit: '256kb' }),
  async (req, res) => {
    try {
      if (!Buffer.isBuffer(req.body) ||
          !await verifyWebhook(secret, req.body, req.get('Bastion-Signature') || '')) {
        res.sendStatus(401);
        return;
      }
      let event;
      try { event = JSON.parse(req.body.toString('utf8')); }
      catch { res.sendStatus(400); return; }
      const data = event?.data;
      if (event?.type !== 'decision.created' ||
          typeof event.id !== 'string' ||
          event.id !== req.get('Bastion-Delivery') ||
          !/^[0-9a-f-]{36}$/i.test(event.id) ||
          !data || typeof data.id !== 'string' || !data.id ||
          typeof data.siteId !== 'string' || !data.siteId ||
          typeof data.accountId !== 'string' || !data.accountId ||
          (data.metadata?.action !== undefined &&
           !['allow', 'review', 'challenge', 'block'].includes(data.metadata.action)) ||
          !Number.isFinite(data.riskScore) || data.riskScore < 0 || data.riskScore > 100) {
        res.sendStatus(400);
        return;
      }
      const inserted = await db.query(
        'INSERT INTO bastion_webhook_inbox (delivery_id, payload) VALUES ($1, $2) ON CONFLICT DO NOTHING RETURNING delivery_id',
        [event.id, event],
      );
      res.sendStatus(inserted.rowCount ? 202 : 200);
    } catch (error) {
      console.error('Webhook acceptance failed:', error.message);
      res.sendStatus(500); // No acknowledgement when durable storage fails.
    }
  });

app.use(express.json());
const server = app.listen(Number(process.env.PORT || 3000), process.env.HOST || '127.0.0.1',
  () => console.log('Bastion webhook receiver listening.'));
for (const signal of ['SIGTERM', 'SIGINT']) {
  process.once(signal, () => server.close(() => void db.end()));
}
