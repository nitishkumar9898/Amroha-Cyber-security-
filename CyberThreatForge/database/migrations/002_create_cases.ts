import type { Knex } from 'knex';

export async function up(knex: Knex): Promise<void> {
  await knex.schema.createTable('cases', (t) => {
    t.uuid('id').primary().defaultTo(knex.raw('gen_random_uuid()'));
    t.string('title').notNullable();
    t.text('description').notNullable();
    t.string('classification').notNullable(); // CRITICAL, HIGH, MEDIUM, LOW
    t.string('type').notNullable(); // cyber_crime, digital_forensics, threat_intel, incident_response
    t.string('status').notNullable().defaultTo('open'); // open, under_investigation, closed, archived
    t.string('jurisdiction').notNullable();
    t.string('fir_number').nullable();
    t.uuid('created_by').references('id').inTable('users').notNullable();
    t.uuid('assigned_to').references('id').inTable('users').nullable();
    t.timestamps(true, true);
    t.timestamp('closed_at').nullable();

    t.index('status');
    t.index('classification');
    t.index('created_by');
    t.index('assigned_to');
  });

  await knex.schema.createTable('case_evidence', (t) => {
    t.uuid('id').primary().defaultTo(knex.raw('gen_random_uuid()'));
    t.uuid('case_id').references('id').inTable('cases').onDelete('CASCADE').notNullable();
    t.string('evidence_type').notNullable();
    t.text('description').nullable();
    t.string('file_path').notNullable();
    t.string('file_hash').notNullable();
    t.bigInteger('file_size').notNullable();
    t.string('mime_type').notNullable();
    t.jsonb('metadata').defaultTo('{}');
    t.timestamps(true, true);
    t.timestamp('deleted_at').nullable();

    t.index('case_id');
    t.index('evidence_type');
  });
}

export async function down(knex: Knex): Promise<void> {
  await knex.schema.dropTableIfExists('case_evidence');
  await knex.schema.dropTableIfExists('cases');
}
