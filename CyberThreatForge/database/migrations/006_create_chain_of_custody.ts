import type { Knex } from 'knex';

export async function up(knex: Knex): Promise<void> {
  await knex.schema.createTable('chain_of_custody', (t) => {
    t.uuid('id').primary().defaultTo(knex.raw('gen_random_uuid()'));
    t.uuid('evidence_id').references('id').inTable('case_evidence').onDelete('CASCADE').notNullable();
    t.uuid('actor_id').references('id').inTable('users').notNullable();
    t.string('actor_role').notNullable();
    t.string('action').notNullable(); // acquired, transferred, analyzed, accessed, returned, destroyed
    t.string('from_party').nullable();
    t.string('to_party').nullable();
    t.string('location').nullable();
    t.text('notes').nullable();
    t.string('previous_hash').notNullable();
    t.string('hash').notNullable().unique();
    t.text('signature').notNullable(); // Digital signature
    t.timestamp('timestamp').notNullable().defaultTo(knex.fn.now());

    t.index('evidence_id');
    t.index('actor_id');
    t.index('hash');
    t.index('timestamp');

    // Trigger to prevent mutation
    await knex.raw(`
      CREATE OR REPLACE FUNCTION prevent_custody_mutation()
      RETURNS TRIGGER AS $$
      BEGIN
        RAISE EXCEPTION 'chain_of_custody is append-only. Updates and deletes are forbidden.';
      END;
      $$ LANGUAGE plpgsql;

      CREATE TRIGGER trg_custody_immutable
      BEFORE UPDATE OR DELETE ON chain_of_custody
      FOR EACH ROW EXECUTE FUNCTION prevent_custody_mutation();
    `);
  });

  // Create function to verify chain integrity
  await knex.raw(`
    CREATE OR REPLACE FUNCTION verify_chain_of_custody(p_evidence_id UUID)
    RETURNS TABLE(chain_valid BOOLEAN, break_point TEXT) AS $$
    DECLARE
      rec RECORD;
      expected_hash TEXT;
      prev_hash TEXT := '0000000000000000000000000000000000000000000000000000000000000000';
      hmac_key TEXT := current_setting('app.audit_hmac_key', true);
    BEGIN
      FOR rec IN
        SELECT * FROM chain_of_custody
        WHERE evidence_id = p_evidence_id
        ORDER BY timestamp ASC
      LOOP
        expected_hash := encode(
          hmac(
            prev_hash || rec.id || rec.timestamp || rec.actor_id || rec.action,
            hmac_key,
            'sha256'
          ),
          'hex'
        );

        IF expected_hash != rec.hash THEN
          chain_valid := false;
          break_point := 'Hash mismatch at ' || rec.id;
          RETURN NEXT;
          RETURN;
        END IF;

        prev_hash := rec.hash;
      END LOOP;

      chain_valid := true;
      break_point := NULL;
      RETURN NEXT;
    END;
    $$ LANGUAGE plpgsql;
  `);
}

export async function down(knex: Knex): Promise<void> {
  await knex.raw('DROP FUNCTION IF EXISTS verify_chain_of_custody(UUID)');
  await knex.raw('DROP TRIGGER IF EXISTS trg_custody_immutable ON chain_of_custody');
  await knex.raw('DROP FUNCTION IF EXISTS prevent_custody_mutation');
  await knex.schema.dropTableIfExists('chain_of_custody');
}
