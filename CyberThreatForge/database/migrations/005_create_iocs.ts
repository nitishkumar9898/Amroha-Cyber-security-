import type { Knex } from 'knex';

export async function up(knex: Knex): Promise<void> {
  await knex.schema.createTable('iocs', (t) => {
    t.uuid('id').primary().defaultTo(knex.raw('gen_random_uuid()'));
    t.string('type').notNullable(); // ip, domain, url, hash, email, cve
    t.string('value').notNullable().unique();
    t.string('severity').defaultTo('medium'); // low, medium, high, critical
    t.text('description').nullable();
    t.string('source').notNullable(); // darkweb, feed, analysis, manual
    t.uuid('case_id').references('id').inTable('cases').nullable();
    t.jsonb('tags').defaultTo('[]');
    t.timestamps(true, true);

    t.index('type');
    t.index('severity');
    t.index('source');
    t.index('value');
  });

  await knex.schema.createTable('threat_feeds', (t) => {
    t.uuid('id').primary().defaultTo(knex.raw('gen_random_uuid()'));
    t.string('name').notNullable();
    t.string('url').notNullable();
    t.string('provider').notNullable();
    t.string('format').defaultTo('stix'); // stix, json, csv, txt
    t.boolean('active').defaultTo(true);
    t.integer('poll_interval_seconds').defaultTo(3600);
    t.timestamps(true, true);
  });
}

export async function down(knex: Knex): Promise<void> {
  await knex.schema.dropTableIfExists('threat_feeds');
  await knex.schema.dropTableIfExists('iocs');
}
