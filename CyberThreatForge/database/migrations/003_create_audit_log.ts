import type { Knex } from 'knex';

export async function up(knex: Knex): Promise<void> {
  await knex.schema.createTable('audit_log_immutable', (t) => {
    t.uuid('id').primary();
    t.timestamp('timestamp').notNullable().defaultTo(knex.fn.now());
    t.string('actor_id').notNullable();
    t.string('actor_role').notNullable();
    t.string('action').notNullable();
    t.string('resource').notNullable();
    t.string('resource_id').nullable();
    t.jsonb('metadata').defaultTo('{}');
    t.string('previous_hash').notNullable();
    t.string('hash').notNullable().unique();

    t.index('actor_id');
    t.index('action');
    t.index('timestamp');
    t.index('resource');

    // Trigger to prevent updates/deletes (immutable guarantee)
    await knex.raw(`
      CREATE OR REPLACE FUNCTION prevent_audit_mutation()
      RETURNS TRIGGER AS $$
      BEGIN
        RAISE EXCEPTION 'audit_log_immutable is append-only. Updates and deletes are forbidden.';
      END;
      $$ LANGUAGE plpgsql;

      CREATE TRIGGER trg_audit_immutable
      BEFORE UPDATE OR DELETE ON audit_log_immutable
      FOR EACH ROW EXECUTE FUNCTION prevent_audit_mutation();
    `);
  });
}

export async function down(knex: Knex): Promise<void> {
  await knex.raw('DROP TRIGGER IF EXISTS trg_audit_immutable ON audit_log_immutable');
  await knex.raw('DROP FUNCTION IF EXISTS prevent_audit_mutation');
  await knex.schema.dropTableIfExists('audit_log_immutable');
}
