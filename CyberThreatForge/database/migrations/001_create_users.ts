import type { Knex } from 'knex';

export async function up(knex: Knex): Promise<void> {
  await knex.schema.createTable('users', (t) => {
    t.uuid('id').primary().defaultTo(knex.raw('gen_random_uuid()'));
    t.string('email').unique().notNullable();
    t.string('name').notNullable();
    t.string('password_hash').notNullable();
    t.string('role').notNullable().defaultTo('researcher'); // police, nia, cbi, researcher, admin
    t.string('department').notNullable();
    t.string('station').nullable();
    t.string('mfa_secret').nullable();
    t.boolean('mfa_enabled').defaultTo(false);
    t.timestamp('last_login_at').nullable();
    t.timestamps(true, true);
    t.timestamp('deleted_at').nullable();

    t.index(['role', 'department']);
  });
}

export async function down(knex: Knex): Promise<void> {
  await knex.schema.dropTableIfExists('users');
}
